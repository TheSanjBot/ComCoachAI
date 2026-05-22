from functools import lru_cache
import json
from pathlib import Path
import random

from app.core.config import PROJECT_ROOT
from app.schemas.coaching import InterviewQuestionPrompt

QUESTION_BANK_PATH = PROJECT_ROOT / "backend" / "app" / "ai" / "question_banks" / "interview_questions.json"

ROLE_DEFAULT_TOPIC = {
    "SDE": "Arrays",
    "Frontend Engineer": "React Performance",
    "Backend Engineer": "Docker",
    "Cloud Engineer": "Kubernetes",
    "DevOps Engineer": "CI/CD",
    "SRE": "Observability",
    "Testing Engineer": "Test Strategy",
    "AI/ML Engineer": "Model Deployment",
    "Data Analyst": "SQL",
}


class QuestionBankService:
    def __init__(self) -> None:
        self._random = random.Random()

    @staticmethod
    @lru_cache(maxsize=1)
    def load_bank() -> list[dict]:
        payload = json.loads(QUESTION_BANK_PATH.read_text(encoding="utf-8"))
        return payload if isinstance(payload, list) else []

    def list_questions_for_role(self, role: str) -> list[InterviewQuestionPrompt]:
        return [
            self._to_prompt(item)
            for item in self.load_bank()
            if item.get("role") == role
        ]

    def select_initial_question(
        self,
        role: str,
        difficulty: str,
        used_question_ids: set[str] | None = None,
    ) -> InterviewQuestionPrompt:
        used_ids = used_question_ids or set()
        candidates = [
            item
            for item in self.load_bank()
            if item.get("role") == role
            and item.get("difficulty") == difficulty
            and item.get("id") not in used_ids
        ]
        if not candidates:
            candidates = [
                item
                for item in self.load_bank()
                if item.get("role") == role and item.get("id") not in used_ids
            ]
        if not candidates:
            candidates = [item for item in self.load_bank() if item.get("id") not in used_ids]
        return self._to_prompt(candidates[0])

    def select_follow_up_question(
        self,
        role: str,
        missing_concepts: list[str],
        used_question_ids: set[str],
        fallback_difficulty: str,
    ) -> InterviewQuestionPrompt | None:
        lowered_missing = {concept.lower() for concept in missing_concepts}
        ranked_candidates: list[dict] = []
        for item in self.load_bank():
            if item.get("role") != role or item.get("id") in used_question_ids:
                continue
            expected = {concept.lower() for concept in item.get("expected_concepts", [])}
            topic = str(item.get("topic", "")).lower()
            overlap = len(lowered_missing & expected)
            if overlap or any(concept in topic for concept in lowered_missing):
                ranked_candidates.append(item)

        if ranked_candidates:
            ranked_candidates.sort(
                key=lambda item: (
                    -len(lowered_missing & {concept.lower() for concept in item.get("expected_concepts", [])}),
                    item.get("difficulty") != fallback_difficulty,
                )
            )
            return self._to_prompt(ranked_candidates[0])

        remaining_role_questions = [
            item
            for item in self.load_bank()
            if item.get("role") == role and item.get("id") not in used_question_ids
        ]
        if remaining_role_questions:
            return self._to_prompt(remaining_role_questions[0])
        return None

    @staticmethod
    def default_topic_for_role(role: str) -> str:
        return ROLE_DEFAULT_TOPIC.get(role, "Core concepts")

    @staticmethod
    def build_inline_follow_up(
        base_question: InterviewQuestionPrompt,
        followup_text: str,
        suffix: int,
    ) -> InterviewQuestionPrompt:
        return InterviewQuestionPrompt(
            question_id=f"{base_question.question_id}-followup-{suffix}",
            role=base_question.role,
            topic=base_question.topic,
            difficulty=base_question.difficulty,
            question=followup_text,
            followups=[],
            expected_concepts=base_question.expected_concepts,
            source="follow-up",
        )

    @staticmethod
    def _to_prompt(item: dict) -> InterviewQuestionPrompt:
        return InterviewQuestionPrompt(
            question_id=str(item["id"]),
            role=str(item["role"]),
            topic=str(item["topic"]),
            difficulty=str(item["difficulty"]),
            question=str(item["question"]),
            followups=[str(entry) for entry in item.get("followups", [])],
            expected_concepts=[str(entry) for entry in item.get("expected_concepts", [])],
            source="question-bank",
        )
