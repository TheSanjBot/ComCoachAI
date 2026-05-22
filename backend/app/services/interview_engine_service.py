from __future__ import annotations

from typing import Any

from backend.app.services.question_bank_service import question_bank_service


class InterviewEngineService:
    def open_interview(
        self,
        role: str,
        experience_level: str | None = None,
        weak_topics: list[str] | None = None,
    ) -> dict[str, Any]:
        weak_topics = weak_topics or []
        preferred_topic = weak_topics[0] if weak_topics else None
        question = question_bank_service.find_question(
            role=role,
            difficulty=(experience_level or "medium"),
            topic=preferred_topic,
        )
        return question

    def generate_followup(
        self,
        question_context: dict[str, Any],
        evaluation: dict[str, Any],
        memory_context: list[dict[str, Any]] | None = None,
    ) -> str:
        memory_context = memory_context or []
        if evaluation.get("missing_concepts"):
            concept = evaluation["missing_concepts"][0]
            return f"Let's go one layer deeper. How would you explain {concept} in a practical production scenario?"
        if question_context.get("followups"):
            return question_context["followups"][0]
        if memory_context:
            focus = memory_context[0].get("metadata", {}).get("weak_topic")
            if focus:
                return f"Previously {focus} looked shaky. Can you connect it to this answer with a real example?"
        return "Can you walk me through a tradeoff or production example related to your answer?"


interview_engine_service = InterviewEngineService()

