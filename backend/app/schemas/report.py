from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ResourceRecommendation(BaseModel):
    topic: str
    title: str
    platform: str
    price: str
    url: str


class LearningRoadmapItem(BaseModel):
    skill: str
    next_step: str
    resource_title: str | None = None
    resource_url: str | None = None


class ReportResponse(BaseModel):
    report_id: str
    mode: str
    title: str
    role: str | None = None
    experience_level: str | None = None
    topic: str | None = None
    summary: str
    communication_score: float
    technical_score: float | None = None
    confidence_score: float
    posture_score: float
    eye_contact_score: float
    malpractice_score: float
    overall_score: float
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    coaching_tips: list[str] = Field(default_factory=list)
    learning_roadmap: list[LearningRoadmapItem] = Field(default_factory=list)
    recommendations: list[ResourceRecommendation] = Field(default_factory=list)
    analytics: dict[str, Any] = Field(default_factory=dict)
    artifact_relative_path: str | None = None
    created_at: datetime


class ReportListResponse(BaseModel):
    reports: list[ReportResponse]
