from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings
from app.schemas.analysis import GrammarIssue


class _GrammarIssuePayload(BaseModel):
    excerpt: str = Field(description="Exact excerpt copied from the transcript.")
    message: str = Field(description="Short explanation of the grammar issue.")
    category: str | None = Field(default=None, description="grammar, punctuation, tense, or clarity")
    suggestions: list[str] = Field(default_factory=list, description="Up to 3 concise fixes.")


class _GrammarReviewPayload(BaseModel):
    grammar_score: int = Field(description="Grammar score from 0 to 100.")
    issues: list[_GrammarIssuePayload] = Field(default_factory=list)
    summary: str = Field(description="Short grammar summary.")


class GrammarLLMService:
    def provider_available(self) -> bool:
        return bool(settings.groq_api_key)

    def evaluate(self, transcript: str) -> tuple[list[GrammarIssue], int | None, list[str]]:
        warnings: list[str] = []
        if not self.provider_available():
            warnings.append("Groq grammar model is not configured, so grammar scoring was skipped.")
            return [], None, warnings

        messages = self._build_messages(transcript)

        try:
            response = self._build_model().invoke(messages)
            parsed = self._parse_response(response.content)
        except Exception as exc:
            warnings.append(f"Groq grammar analysis failed: {exc}")
            return [], None, warnings

        issues = self._map_issues(transcript, parsed.issues)
        grammar_score = max(0, min(parsed.grammar_score, 100))
        return issues[:10], grammar_score, warnings

    def _build_model(self) -> ChatOpenAI:
        return ChatOpenAI(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
            temperature=0.0,
            timeout=settings.grammar_llm_timeout_seconds,
            max_retries=1,
        )

    @staticmethod
    def _build_messages(transcript: str) -> list:
        system_message = (
            "You are a grammar reviewer for spoken communication coaching. "
            "Review only grammar, punctuation, tense consistency, and sentence clarity. "
            "Be conservative because this is speech transcription, not polished writing. "
            "Do not penalize missing commas or punctuation unless it clearly harms professional clarity. "
            "Ignore technical correctness and focus only on language quality. "
            "Return only valid JSON with the exact top-level fields requested and no schema wrapper."
        )
        human_payload: dict[str, Any] = {
            "transcript": transcript,
            "required_schema": {
                "grammar_score": "integer 0-100",
                "issues": [
                    {
                        "excerpt": "string copied from transcript",
                        "message": "string",
                        "category": "grammar | punctuation | tense | clarity | null",
                        "suggestions": ["string"],
                    }
                ],
                "summary": "string",
            },
        }
        return [
            SystemMessage(content=system_message),
            HumanMessage(
                content=(
                    "Analyze the following transcript and return a JSON response.\n\n"
                    f"{json.dumps(human_payload, indent=2)}"
                )
            ),
        ]

    @staticmethod
    def _parse_response(text: str) -> _GrammarReviewPayload:
        payload = GrammarLLMService._extract_json_payload(text)
        payload = GrammarLLMService._normalize_payload(payload)
        return _GrammarReviewPayload.model_validate(payload)

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

        for candidate in GrammarLLMService._candidate_variants(candidates):
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
    def _map_issues(
        transcript: str,
        issues: list[_GrammarIssuePayload],
    ) -> list[GrammarIssue]:
        lowered_transcript = transcript.lower()
        search_cursor = 0
        mapped_issues: list[GrammarIssue] = []

        for issue in issues:
            excerpt = issue.excerpt.strip()
            offset = 0
            error_length = len(excerpt)

            if excerpt:
                lower_excerpt = excerpt.lower()
                match_index = lowered_transcript.find(lower_excerpt, search_cursor)
                if match_index == -1:
                    match_index = lowered_transcript.find(lower_excerpt)
                if match_index >= 0:
                    offset = match_index
                    error_length = len(excerpt)
                    search_cursor = match_index + max(len(excerpt), 1)

            mapped_issues.append(
                GrammarIssue(
                    message=issue.message.strip(),
                    offset=offset,
                    error_length=error_length,
                    category=issue.category,
                    suggestions=[item.strip() for item in issue.suggestions[:3] if item.strip()],
                )
            )

        return mapped_issues


grammar_llm_service = GrammarLLMService()
