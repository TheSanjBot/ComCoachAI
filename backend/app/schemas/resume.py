from pydantic import BaseModel, Field

from app.schemas.report import LearningRoadmapItem, ResourceRecommendation


class ResumeAnalysisTextRequest(BaseModel):
    resume_text: str
    target_role: str


class ResumeAnalysisResponse(BaseModel):
    target_role: str
    matching_score: float
    ats_readiness_score: float = 0
    role_fit_summary: str = ""
    detected_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    priority_gaps: list[str] = Field(default_factory=list)
    evidence_highlights: list[str] = Field(default_factory=list)
    extracted_text_preview: str = ""
    learning_roadmap: list[LearningRoadmapItem] = Field(default_factory=list)
    recommendations: list[ResourceRecommendation] = Field(default_factory=list)
    personalized_coaching: list[str] = Field(default_factory=list)
    report_id: str | None = None
    artifact_relative_path: str | None = None
