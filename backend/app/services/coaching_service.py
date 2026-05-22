from __future__ import annotations

from collections import Counter
from typing import Any


class CoachingService:
    def personalize(
        self,
        *,
        mode: str,
        strengths: list[str],
        weaknesses: list[str],
        current_focus_topics: list[str],
        memory_context: list[dict[str, Any]],
    ) -> list[str]:
        tips: list[str] = []
        recurring_topics = Counter()
        for memory in memory_context:
            metadata = memory.get("metadata", {})
            for topic in metadata.get("weak_topics", []) or []:
                recurring_topics[str(topic)] += 1

        for topic in current_focus_topics[:3]:
            if recurring_topics[topic] > 0:
                tips.append(
                    f"{topic} has appeared across multiple {mode} sessions, so make it part of your deliberate weekly practice plan."
                )

        if weaknesses:
            tips.append(f"Prioritize fixing this next: {weaknesses[0]}")
        if strengths:
            tips.append(f"Keep reinforcing this habit: {strengths[0]}")
        return tips[:5]


coaching_service = CoachingService()
