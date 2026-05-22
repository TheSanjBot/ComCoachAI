from __future__ import annotations

from typing import Any

from backend.app.core.config import get_settings


class LLMOrchestrator:
    """Explicit provider boundary for later LangChain-backed model calls."""

    def __init__(self) -> None:
        settings = get_settings()
        self.provider = settings.llm_provider
        self.model = settings.llm_model

    def build_followup_prompt(
        self,
        role: str,
        transcript: str,
        missing_concepts: list[str],
        memory_context: list[dict[str, Any]],
    ) -> str:
        prior_context = memory_context[0]["metadata"]["weak_topic"] if memory_context else "none"
        missing = ", ".join(missing_concepts) if missing_concepts else "depth and tradeoffs"
        return (
            f"Role: {role}. Prior weakness context: {prior_context}. "
            f"Current answer: {transcript[:400]}. Probe missing areas around {missing}."
        )


llm_orchestrator = LLMOrchestrator()

