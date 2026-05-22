from typing import Any

from pydantic import BaseModel, Field

from backend.app.models.session import SessionMode, SessionStatus


class SessionCreate(BaseModel):
    mode: SessionMode
    role: str | None = None
    experience_level: str | None = None
    topic: str | None = None
    prompt_context: dict[str, Any] | None = None


class RecordingSubmission(BaseModel):
    transcript: str | None = None
    transcript_segments: list[dict[str, Any]] = Field(default_factory=list)
    video_metrics: dict[str, Any] = Field(default_factory=dict)
    video_path: str | None = None
    audio_path: str | None = None
    resume_text: str | None = None
    target_role: str | None = None


class SessionResponse(BaseModel):
    id: int
    mode: SessionMode
    status: SessionStatus
    role: str | None
    experience_level: str | None
    topic: str | None
    transcript: str | None

    class Config:
        from_attributes = True
