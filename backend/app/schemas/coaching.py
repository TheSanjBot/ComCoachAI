from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.report import LearningRoadmapItem, ResourceRecommendation


SUPPORTED_INTERVIEW_ROLES = [
    "SDE",
    "Frontend Engineer",
    "Backend Engineer",
    "Cloud Engineer",
    "DevOps Engineer",
    "SRE",
    "Testing Engineer",
    "AI/ML Engineer",
    "Data Analyst",
]


class ExperienceLevel(str, Enum):
    ENTRY = "entry-level"
    MID = "mid-level"
    SENIOR = "senior"


class InterviewSessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"


class InterviewQuestionPrompt(BaseModel):
    question_id: str
    role: str
    topic: str
    difficulty: str
    question: str
    followups: list[str] = Field(default_factory=list)
    expected_concepts: list[str] = Field(default_factory=list)
    source: str = "question-bank"


class InterviewSessionCreateRequest(BaseModel):
    role: str
    experience_level: ExperienceLevel
    target_question_count: int = 3
    resume_filename: str | None = None
    resume_notes: str | None = None


class InterviewSessionResponse(BaseModel):
    session_id: str
    role: str
    experience_level: ExperienceLevel
    target_question_count: int
    answered_question_count: int
    status: InterviewSessionStatus
    created_at: datetime
    updated_at: datetime
    current_question: InterviewQuestionPrompt | None = None
    supported_roles: list[str] = Field(default_factory=lambda: SUPPORTED_INTERVIEW_ROLES.copy())
    resume_filename: str | None = None
    resume_notes: str | None = None


class TechnicalEvaluationResult(BaseModel):
    technical_score: int
    correctness_score: int
    explanation_depth_score: int
    technical_clarity_score: int
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    missing_concepts: list[str] = Field(default_factory=list)
    evidence_found: list[str] = Field(default_factory=list)
    suggested_followup_topics: list[str] = Field(default_factory=list)
    summary: str
    strategy: str
    warnings: list[str] = Field(default_factory=list)


class InterviewTurnResult(BaseModel):
    session: InterviewSessionResponse
    question: InterviewQuestionPrompt
    technical_evaluation: TechnicalEvaluationResult
    communication_score: int
    coaching_feedback: list[str] = Field(default_factory=list)
    next_question: InterviewQuestionPrompt | None = None
    final_report: "InterviewFinalReport | None" = None


class InterviewSubmitAnswerRequest(BaseModel):
    recording_id: str


class InterviewFinalReport(BaseModel):
    session_id: str
    role: str
    experience_level: ExperienceLevel
    completed_at: datetime
    question_count: int
    average_technical_score: float
    average_communication_score: float
    average_words_per_minute: float = 0
    average_filler_words: float = 0
    average_posture_score: float = 0
    average_eye_contact_score: float = 0
    average_malpractice_score: float = 0
    strongest_topics: list[str] = Field(default_factory=list)
    weakest_topics: list[str] = Field(default_factory=list)
    recurring_missing_concepts: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    final_coaching_summary: str
    personalized_coaching: list[str] = Field(default_factory=list)
    learning_roadmap: list[LearningRoadmapItem] = Field(default_factory=list)
    recommendations: list[ResourceRecommendation] = Field(default_factory=list)
    report_id: str | None = None


class PublicSpeakingSessionCreateRequest(BaseModel):
    topic: str
    audience: str | None = None


class PublicSpeakingSessionResponse(BaseModel):
    session_id: str
    topic: str
    audience: str | None = None
    created_at: datetime
    updated_at: datetime
    status: str


class PublicSpeakingCoachingResult(BaseModel):
    session: PublicSpeakingSessionResponse
    recording_id: str
    confidence_score: int
    communication_score: int = 0
    factual_accuracy_score: int = 0
    words_per_minute: float = 0
    filler_word_total: int = 0
    posture_score: int = 0
    eye_contact_score: int = 0
    malpractice_score: int = 0
    pacing_suggestions: list[str] = Field(default_factory=list)
    posture_coaching: list[str] = Field(default_factory=list)
    eye_contact_coaching: list[str] = Field(default_factory=list)
    communication_advice: list[str] = Field(default_factory=list)
    storytelling_feedback: list[str] = Field(default_factory=list)
    factual_highlights: list[str] = Field(default_factory=list)
    factual_corrections: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    summary: str
    factual_accuracy_summary: str = ""
    personalized_coaching: list[str] = Field(default_factory=list)
    learning_roadmap: list[LearningRoadmapItem] = Field(default_factory=list)
    recommendations: list[ResourceRecommendation] = Field(default_factory=list)
    report_id: str | None = None


class PublicSpeakingSubmitRequest(BaseModel):
    recording_id: str


InterviewTurnResult.model_rebuild()
