from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings


class FactualAccuracyReview(BaseModel):
    factual_accuracy_score: int = Field(description="0-100 factual accuracy score for the talk.")
    factual_accuracy_summary: str = Field(
        description="Short summary of whether the talk was factually reliable for the chosen topic."
    )
    factual_highlights: list[str] = Field(
        default_factory=list,
        description="Claims or sections that were broadly accurate or well-grounded.",
    )
    factual_corrections: list[str] = Field(
        default_factory=list,
        description="Corrections for questionable, unsupported, or inaccurate claims.",
    )


class ContentAccuracyService:
    def provider_available(self) -> bool:
        return bool(settings.groq_api_key)

    def review_public_speaking_transcript(self, topic: str, transcript: str) -> FactualAccuracyReview:
        if not self.provider_available():
            return FactualAccuracyReview(
                factual_accuracy_score=0,
                factual_accuracy_summary="Factual review is unavailable because the Groq key is not configured.",
                factual_highlights=[],
                factual_corrections=[],
            )

        if not transcript.strip():
            return FactualAccuracyReview(
                factual_accuracy_score=0,
                factual_accuracy_summary="Factual review could not run because the transcript was empty.",
                factual_highlights=[],
                factual_corrections=[],
            )

        response = self._build_model().invoke(self._build_messages(topic, transcript))
        payload = self._extract_json_payload(response.content)
        payload = self._normalize_payload(payload)
        parsed = FactualAccuracyReview.model_validate(payload)
        parsed.factual_accuracy_score = max(0, min(parsed.factual_accuracy_score, 100))
        parsed.factual_highlights = parsed.factual_highlights[:4]
        parsed.factual_corrections = parsed.factual_corrections[:4]
        return parsed

    def _build_model(self) -> ChatOpenAI:
        return ChatOpenAI(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
            temperature=0.0,
            timeout=settings.interview_llm_timeout_seconds,
            max_retries=1,
        )

    @staticmethod
    def _build_messages(topic: str, transcript: str) -> list:
        system_message = (
            "You are a factual reviewer for public speaking coaching. "
            "Evaluate whether the speech is factually reliable for the stated topic. "
            "Be careful with nuance: if the topic is opinion-heavy or partially interpretive, do not over-penalize. "
            "When the speaker makes unsupported or incorrect claims, explain them clearly and briefly. "
            "Return only valid JSON with the exact top-level fields requested."
        )
        human_payload: dict[str, Any] = {
            "topic": topic,
            "transcript": transcript,
            "required_schema": {
                "factual_accuracy_score": "integer 0-100",
                "factual_accuracy_summary": "string",
                "factual_highlights": ["string"],
                "factual_corrections": ["string"],
            },
        }
        return [
            SystemMessage(content=system_message),
            HumanMessage(
                content=(
                    "Review the factual quality of this speech and respond in JSON only.\n\n"
                    f"{json.dumps(human_payload, indent=2)}"
                )
            ),
        ]

    @staticmethod
    def _extract_json_payload(text: str) -> dict[str, Any]:
        if not text:
            raise ValueError("Model returned an empty response.")

        candidates = [text]
        fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fenced_match:
            candidates.insert(0, fenced_match.group(1))

        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            candidates.append(brace_match.group(0))

        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue

        raise ValueError(f"Model did not return valid JSON: {text}")

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


content_accuracy_service = ContentAccuracyService()
