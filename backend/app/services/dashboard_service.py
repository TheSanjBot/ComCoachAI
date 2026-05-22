from __future__ import annotations

from collections import Counter
from datetime import UTC, date, datetime, timedelta
from statistics import mean

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.dashboard import (
    ConfidenceTrendPoint,
    DashboardOverview,
    FeaturedRecommendation,
    InterviewHistoryItem,
    ModeCard,
    ModePerformancePoint,
    RecentReport,
    ScoreSummary,
)
from app.schemas.report import ReportResponse
from app.services.report_service import GeneratedReportService


class DashboardService:
    def __init__(self, user: User, db: AsyncSession):
        self.user = user
        self.db = db

    async def build_overview(self) -> DashboardOverview:
        reports = await GeneratedReportService(self.db).list_reports(self.user)
        first_name = self.user.full_name.split()[0] if self.user.full_name else "Coach"
        confidence_scores = [report.confidence_score for report in reports if report.confidence_score > 0]
        communication_scores = [report.communication_score for report in reports if report.communication_score > 0]
        technical_scores = [
            report.technical_score
            for report in reports
            if report.technical_score is not None and report.technical_score > 0
        ]
        focus_area = self._focus_area(reports)

        return DashboardOverview(
            welcome_name=first_name,
            streak_days=self._streak_days(reports),
            total_sessions=len(reports),
            average_confidence_score=round(mean(confidence_scores)) if confidence_scores else 0,
            focus_area=focus_area,
            recommended_mode_slug=self._recommended_mode(reports),
            mode_cards=self._mode_cards(reports),
            score_summaries=[
                ScoreSummary(
                    label="Confidence",
                    score=round(mean(confidence_scores)) if confidence_scores else 0,
                    delta=self._delta(confidence_scores),
                    note="Tracks overall delivery confidence across completed sessions.",
                ),
                ScoreSummary(
                    label="Communication",
                    score=round(mean(communication_scores)) if communication_scores else 0,
                    delta=self._delta(communication_scores),
                    note="Blends fluency, clarity, pacing, and speaking consistency.",
                ),
                ScoreSummary(
                    label="Technical / Match",
                    score=round(mean(technical_scores)) if technical_scores else 0,
                    delta=self._delta(technical_scores),
                    note="Reflects technical interview performance or resume-role alignment.",
                ),
            ],
            confidence_trend=self._confidence_trend(reports),
            mode_performance=self._mode_performance(reports),
            recent_reports=self._recent_reports(reports),
            interview_history=self._interview_history(reports),
            featured_recommendations=self._featured_recommendations(reports),
            priority_actions=self._priority_actions(reports),
        )

    def _mode_cards(self, reports: list[ReportResponse]) -> list[ModeCard]:
        completed_modes = {report.mode for report in reports}
        return [
            ModeCard(
                slug="interview-training",
                title="Interview Training Mode",
                description="Simulate technical interviews with staged recording analysis, LangChain follow-ups, memory-aware coaching, and persisted reports.",
                status="Live and report-backed" if "Interview Training Mode" in completed_modes else "Ready to launch",
                estimated_duration_minutes=25,
                primary_focus="Technical interviews, follow-up pressure, structured answers",
                next_milestone="Use resume context plus memory-driven follow-ups to tighten weak topics",
            ),
            ModeCard(
                slug="public-speaking",
                title="Public Speaking Training Mode",
                description="Practice presentation delivery with pacing, posture, eye-contact, and confidence feedback plus personalized improvement tips.",
                status="Live and report-backed" if "Public Speaking Training Mode" in completed_modes else "Ready to launch",
                estimated_duration_minutes=15,
                primary_focus="Delivery confidence, body language, storytelling flow",
                next_milestone="Use repeated rehearsals to raise confidence and reduce filler words",
            ),
            ModeCard(
                slug="resume-skill-gap",
                title="Resume + Skill Gap Analysis Mode",
                description="Upload a resume, benchmark it against target roles, and get missing-skill detection, learning roadmap steps, and recommendations.",
                status="Live and upload-ready" if "Resume + Skill Gap Analysis Mode" in completed_modes else "Ready to launch",
                estimated_duration_minutes=10,
                primary_focus="Resume fit, missing technologies, upskilling direction",
                next_milestone="Close the top skill gaps and re-run the analysis after updates",
            ),
        ]

    @staticmethod
    def _focus_area(reports: list[ReportResponse]) -> str:
        weaknesses = [
            weakness
            for report in reports
            for weakness in report.weaknesses[:3]
            if weakness
        ]
        if not weaknesses:
            return "Complete one session in each mode to unlock personalized focus tracking."
        return Counter(weaknesses).most_common(1)[0][0]

    @staticmethod
    def _recommended_mode(reports: list[ReportResponse]) -> str:
        seen_modes = {report.mode for report in reports}
        if "Interview Training Mode" not in seen_modes:
            return "interview-training"
        if "Public Speaking Training Mode" not in seen_modes:
            return "public-speaking"
        if "Resume + Skill Gap Analysis Mode" not in seen_modes:
            return "resume-skill-gap"

        mode_scores = {
            "interview-training": [],
            "public-speaking": [],
            "resume-skill-gap": [],
        }
        for report in reports:
            if report.mode == "Interview Training Mode":
                mode_scores["interview-training"].append(report.overall_score)
            elif report.mode == "Public Speaking Training Mode":
                mode_scores["public-speaking"].append(report.overall_score)
            elif report.mode == "Resume + Skill Gap Analysis Mode":
                mode_scores["resume-skill-gap"].append(report.overall_score)

        averaged = {
            slug: (mean(scores) if scores else 100.0)
            for slug, scores in mode_scores.items()
        }
        return min(averaged, key=averaged.get)

    @staticmethod
    def _delta(values: list[float | int]) -> int:
        if len(values) < 2:
            return 0
        return int(round(values[0] - values[-1]))

    @staticmethod
    def _confidence_trend(reports: list[ReportResponse]) -> list[ConfidenceTrendPoint]:
        if not reports:
            today = date.today()
            return [
                ConfidenceTrendPoint(
                    label=(today - timedelta(days=6 - index)).strftime("%b %d"),
                    confidence_score=0,
                    communication_score=0,
                )
                for index in range(4)
            ]

        grouped: dict[str, list[ReportResponse]] = {}
        ordered = sorted(reports, key=lambda report: report.created_at)
        for report in ordered:
            label = DashboardService._as_utc(report.created_at).strftime("%b %d")
            grouped.setdefault(label, []).append(report)

        trend_points = []
        for label, label_reports in list(grouped.items())[-6:]:
            trend_points.append(
                ConfidenceTrendPoint(
                    label=label,
                    confidence_score=round(mean(report.confidence_score for report in label_reports)),
                    communication_score=round(mean(report.communication_score for report in label_reports)),
                )
            )
        return trend_points

    @staticmethod
    def _recent_reports(reports: list[ReportResponse]) -> list[RecentReport]:
        return [
            RecentReport(
                id=report.report_id,
                title=report.title,
                mode=report.mode,
                completed_at=report.created_at.date().isoformat(),
                communication_score=round(report.communication_score),
                confidence_score=round(report.confidence_score),
                summary=report.summary,
            )
            for report in reports[:5]
        ]

    @staticmethod
    def _mode_performance(reports: list[ReportResponse]) -> list[ModePerformancePoint]:
        mode_meta = {
            "Interview Training Mode": ("interview-training", "Interview"),
            "Public Speaking Training Mode": ("public-speaking", "Public speaking"),
            "Resume + Skill Gap Analysis Mode": ("resume-skill-gap", "Resume"),
        }
        grouped: dict[str, list[ReportResponse]] = {mode: [] for mode in mode_meta}
        for report in reports:
            if report.mode in grouped:
                grouped[report.mode].append(report)

        points: list[ModePerformancePoint] = []
        for mode_name, (slug, title) in mode_meta.items():
            items = grouped[mode_name]
            points.append(
                ModePerformancePoint(
                    slug=slug,
                    title=title,
                    average_overall_score=round(mean([item.overall_score for item in items]), 2) if items else 0.0,
                    average_confidence_score=round(mean([item.confidence_score for item in items]), 2) if items else 0.0,
                    session_count=len(items),
                )
            )
        return points

    @staticmethod
    def _interview_history(reports: list[ReportResponse]) -> list[InterviewHistoryItem]:
        history: list[InterviewHistoryItem] = []
        for report in reports:
            if report.mode != "Interview Training Mode":
                continue
            history.append(
                InterviewHistoryItem(
                    id=report.report_id,
                    role=report.role or "Interview session",
                    level=(report.experience_level or "unspecified").replace("-", " ").title(),
                    completed_at=report.created_at.date().isoformat(),
                    technical_score=round(report.technical_score or 0),
                    communication_score=round(report.communication_score),
                    trend=report.weaknesses[0] if report.weaknesses else report.summary,
                )
            )
            if len(history) >= 5:
                break
        return history

    @staticmethod
    def _featured_recommendations(reports: list[ReportResponse]) -> list[FeaturedRecommendation]:
        featured: list[FeaturedRecommendation] = []
        seen_urls: set[str] = set()
        approved_platforms = {
            "Coursera",
            "Udemy",
            "edX",
            "Pluralsight",
            "Frontend Masters",
            "Codecademy",
            "Skillshare",
            "Skillsoft",
        }

        for report in reports:
            for recommendation in report.recommendations:
                if recommendation.url in seen_urls or recommendation.platform not in approved_platforms:
                    continue
                featured.append(
                    FeaturedRecommendation(
                        **recommendation.model_dump(mode="json"),
                        source_mode=report.mode,
                    )
                )
                seen_urls.add(recommendation.url)
                if len(featured) >= 6:
                    return featured
        return featured

    @staticmethod
    def _priority_actions(reports: list[ReportResponse]) -> list[str]:
        actions = [
            tip
            for report in reports[:6]
            for tip in report.coaching_tips[:3]
            if tip
        ]
        if not actions:
            return [
                "Complete one interview, one speaking rehearsal, and one resume review to unlock tailored next steps."
            ]
        return [item for item, _ in Counter(actions).most_common(4)]

    @staticmethod
    def _streak_days(reports: list[ReportResponse]) -> int:
        if not reports:
            return 0

        session_days = sorted(
            {DashboardService._as_utc(report.created_at).date() for report in reports},
            reverse=True,
        )
        streak = 0
        expected_day = session_days[0]
        for session_day in session_days:
            if session_day != expected_day:
                break
            streak += 1
            expected_day = expected_day - timedelta(days=1)
        return streak

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
