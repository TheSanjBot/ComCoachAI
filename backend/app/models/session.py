from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class SessionMode(str, Enum):
    INTERVIEW = "interview"
    PUBLIC_SPEAKING = "public_speaking"
    RESUME_ANALYSIS = "resume_analysis"


class SessionStatus(str, Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    COMPLETED = "completed"


class CoachingSession(Base):
    __tablename__ = "coaching_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    mode: Mapped[SessionMode] = mapped_column(SqlEnum(SessionMode), index=True)
    status: Mapped[SessionStatus] = mapped_column(
        SqlEnum(SessionStatus),
        default=SessionStatus.DRAFT,
    )
    role: Mapped[str | None] = mapped_column(String(120), nullable=True)
    experience_level: Mapped[str | None] = mapped_column(String(80), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prompt_context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript_segments: Mapped[list | None] = mapped_column(JSON, nullable=True)
    video_metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("User", back_populates="sessions")
    report = relationship("SessionReport", back_populates="session", uselist=False)

