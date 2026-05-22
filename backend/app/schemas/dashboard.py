from pydantic import BaseModel
from app.schemas.report import ResourceRecommendation


class ModeCard(BaseModel):
    slug: str
    title: str
    description: str
    status: str
    estimated_duration_minutes: int
    primary_focus: str
    next_milestone: str


class ScoreSummary(BaseModel):
    label: str
    score: int
    delta: int
    note: str


class ConfidenceTrendPoint(BaseModel):
    label: str
    confidence_score: int
    communication_score: int


class ModePerformancePoint(BaseModel):
    slug: str
    title: str
    average_overall_score: float
    average_confidence_score: float
    session_count: int


class FeaturedRecommendation(ResourceRecommendation):
    source_mode: str


class RecentReport(BaseModel):
    id: str
    title: str
    mode: str
    completed_at: str
    communication_score: int
    confidence_score: int
    summary: str


class InterviewHistoryItem(BaseModel):
    id: str
    role: str
    level: str
    completed_at: str
    technical_score: int
    communication_score: int
    trend: str


class DashboardOverview(BaseModel):
    welcome_name: str
    streak_days: int
    total_sessions: int
    average_confidence_score: int
    focus_area: str
    recommended_mode_slug: str
    mode_cards: list[ModeCard]
    score_summaries: list[ScoreSummary]
    confidence_trend: list[ConfidenceTrendPoint]
    mode_performance: list[ModePerformancePoint]
    recent_reports: list[RecentReport]
    interview_history: list[InterviewHistoryItem]
    featured_recommendations: list[FeaturedRecommendation]
    priority_actions: list[str]
