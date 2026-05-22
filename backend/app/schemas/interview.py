from typing import Any

from pydantic import BaseModel


class InterviewQuestionResponse(BaseModel):
    question: str
    topic: str
    difficulty: str
    followups: list[str]
    context: dict[str, Any] = {}

