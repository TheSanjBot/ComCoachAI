from datetime import datetime, timezone
import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings
from app.schemas.analysis import RecordingAnalysisResponse
from app.schemas.coaching import InterviewQuestionPrompt, TechnicalEvaluationResult
from app.services.question_bank_service import QuestionBankService


class _LLMTechnicalEvaluation(BaseModel):
    technical_score: int = Field(description="Overall technical answer score from 0 to 100.")
    correctness_score: int = Field(description="Correctness score from 0 to 100.")
    explanation_depth_score: int = Field(description="Depth score from 0 to 100.")
    technical_clarity_score: int = Field(description="Technical clarity score from 0 to 100.")
    strengths: list[str] = Field(description="Concrete technical strengths in the answer.")
    weaknesses: list[str] = Field(description="Concrete technical weaknesses in the answer.")
    missing_concepts: list[str] = Field(description="Important concepts the answer missed.")
    evidence_found: list[str] = Field(
        description="Concepts or terms that clearly appeared in the answer."
    )
    suggested_followup_topics: list[str] = Field(
        description="Topics that should be probed next."
    )
    summary: str = Field(description="Short technical evaluation summary.")


class _LLMFollowUpQuestion(BaseModel):
    topic: str = Field(description="Topic focus for the next interview question.")
    difficulty: str = Field(description="Difficulty label for the next question.")
    question: str = Field(description="A focused next interview question.")
    expected_concepts: list[str] = Field(
        description="Concepts a strong answer should cover."
    )
    rationale: str = Field(
        description="Why this next question follows from the candidate's previous answer."
    )


class InterviewLLMService:
    def __init__(self) -> None:
        self.question_bank = QuestionBankService()

    def provider_ready(self) -> bool:
        return bool(settings.groq_api_key)

    def evaluate_answer(
        self,
        question: InterviewQuestionPrompt,
        analysis: RecordingAnalysisResponse,
        conversation_history: list[dict[str, Any]] | None = None,
        memory_context: list[dict[str, Any]] | None = None,
    ) -> TechnicalEvaluationResult:
        model = self._build_model()
        prompt = self._build_messages(
            system_message=(
                "You are a technical interviewer evaluating a candidate response. "
                "Be strict, concrete, and evidence-driven. Score only the answer that was provided. "
                "Use the transcript as the main source of truth, but you may use communication analysis "
                "to judge technical clarity. Return only valid JSON with the exact top-level fields requested."
            ),
            human_payload={
                "question": question.model_dump(mode="json"),
                "transcript": analysis.transcript.transcript,
                "communication_summary": {
                    "fluency_score": analysis.communication_analysis.fluency_score,
                    "sentence_quality_score": analysis.communication_analysis.sentence_quality_score,
                    "pace_classification": analysis.communication_analysis.pace_classification,
                    "filler_word_total": analysis.communication_analysis.filler_word_total,
                },
                "previous_turns": conversation_history or [],
                "memory_context": memory_context or [],
                "required_schema": self._schema_requirements("technical_evaluation"),
            },
        )
        parsed = self._invoke_model(_LLMTechnicalEvaluation, model, prompt)

        return TechnicalEvaluationResult(
            technical_score=max(0, min(parsed.technical_score, 100)),
            correctness_score=max(0, min(parsed.correctness_score, 100)),
            explanation_depth_score=max(0, min(parsed.explanation_depth_score, 100)),
            technical_clarity_score=max(0, min(parsed.technical_clarity_score, 100)),
            strengths=parsed.strengths,
            weaknesses=parsed.weaknesses,
            missing_concepts=parsed.missing_concepts,
            evidence_found=parsed.evidence_found,
            suggested_followup_topics=parsed.suggested_followup_topics,
            summary=parsed.summary,
            strategy="langchain-groq",
            warnings=[],
        )

    def generate_follow_up_question(
        self,
        *,
        current_question: InterviewQuestionPrompt,
        role: str,
        difficulty: str,
        analysis: RecordingAnalysisResponse,
        technical_evaluation: TechnicalEvaluationResult,
        conversation_history: list[dict[str, Any]],
        memory_context: list[dict[str, Any]],
        used_question_ids: set[str],
    ) -> InterviewQuestionPrompt | None:
        model = self._build_model()
        question_bank_context = [
            item.model_dump(mode="json")
            for item in self.question_bank.list_questions_for_role(role)
            if item.question_id not in used_question_ids
        ][:4]
        prompt = self._build_messages(
            system_message=(
                "You are generating the next technical interview question in a staged mock interview. "
                "Use the prior question, the candidate transcript, the technical evaluation, and the "
                "available question-bank context to ask one focused follow-up question. Prefer probing "
                "missing concepts or weak explanations. Return only the requested JSON structure."
            ),
            human_payload={
                "role": role,
                "difficulty": difficulty,
                "current_question": current_question.model_dump(mode="json"),
                "transcript": analysis.transcript.transcript,
                "technical_evaluation": technical_evaluation.model_dump(mode="json"),
                "available_question_bank_context": question_bank_context,
                "previous_turns": conversation_history,
                "memory_context": memory_context,
                "required_schema": self._schema_requirements("follow_up_question"),
            },
        )
        parsed = self._invoke_model(_LLMFollowUpQuestion, model, prompt)

        return InterviewQuestionPrompt(
            question_id=f"llm-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
            role=role,
            topic=parsed.topic,
            difficulty=parsed.difficulty or difficulty,
            question=parsed.question,
            followups=[],
            expected_concepts=parsed.expected_concepts,
            source="langchain-groq",
        )

    def _build_model(self) -> ChatOpenAI:
        if not self.provider_ready():
            raise RuntimeError("Groq API key is not configured.")
        return ChatOpenAI(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
            temperature=settings.interview_llm_temperature,
            timeout=settings.interview_llm_timeout_seconds,
            max_retries=1,
        )

    @staticmethod
    def _build_messages(*, system_message: str, human_payload: dict[str, Any]) -> list:
        human_message = (
            "Use the following context to produce a valid JSON response.\n\n"
            f"{json.dumps(human_payload, indent=2)}"
        )
        return [
            SystemMessage(content=system_message),
            HumanMessage(content=human_message),
        ]

    @staticmethod
    def _invoke_model(schema: type[BaseModel], model: ChatOpenAI, prompt: list):
        response = model.invoke(prompt)
        payload = InterviewLLMService._extract_json_payload(response.content)
        payload = InterviewLLMService._normalize_payload(payload)
        return schema.model_validate(payload)

    @staticmethod
    def _extract_json_payload(text: str) -> dict[str, Any]:
        if not text:
            raise ValueError("Model returned an empty response.")

        candidates = [text]
        fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fenced_match:
            candidates.insert(0, fenced_match.group(1))

        brace_start = text.find("{")
        if brace_start != -1:
            candidates.append(text[brace_start:])

        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            candidates.append(brace_match.group(0))

        for candidate in InterviewLLMService._candidate_variants(candidates):
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue

        raise ValueError(f"Model did not return valid JSON: {text}")

    @staticmethod
    def _candidate_variants(candidates: list[str]) -> list[str]:
        variants: list[str] = []
        seen: set[str] = set()

        for candidate in candidates:
            normalized = candidate.strip()
            if not normalized:
                continue

            repair_candidates = [normalized]
            brace_delta = normalized.count("{") - normalized.count("}")
            if brace_delta > 0:
                repair_candidates.append(f"{normalized}{'}' * brace_delta}")
            if not normalized.endswith("}"):
                repair_candidates.append(f"{normalized}}}")

            for repair in repair_candidates:
                cleaned = re.sub(r",(\s*[}\]])", r"\1", repair.strip())
                if cleaned and cleaned not in seen:
                    variants.append(cleaned)
                    seen.add(cleaned)

        return variants

    @staticmethod
    def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
        current = payload
        while isinstance(current, dict):
            if "properties" in current and isinstance(current["properties"], dict):
                current = current["properties"]
                continue
            if "result" in current and isinstance(current["result"], dict):
                current = current["result"]
                continue
            if "output" in current and isinstance(current["output"], dict):
                current = current["output"]
                continue
            if "data" in current and isinstance(current["data"], dict):
                current = current["data"]
                continue
            break
        return current

    @staticmethod
    def _schema_requirements(schema_name: str) -> dict[str, Any]:
        if schema_name == "technical_evaluation":
            return {
                "technical_score": "integer 0-100",
                "correctness_score": "integer 0-100",
                "explanation_depth_score": "integer 0-100",
                "technical_clarity_score": "integer 0-100",
                "strengths": ["string"],
                "weaknesses": ["string"],
                "missing_concepts": ["string"],
                "evidence_found": ["string"],
                "suggested_followup_topics": ["string"],
                "summary": "string",
            }
        return {
            "topic": "string",
            "difficulty": "string",
            "question": "string",
            "expected_concepts": ["string"],
            "rationale": "string",
        }
