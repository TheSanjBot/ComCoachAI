from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import PROJECT_ROOT, settings
from app.models.report import GeneratedReport
from app.models.user import User
from app.schemas.report import LearningRoadmapItem, ReportResponse, ResourceRecommendation


class GeneratedReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_report(
        self,
        user: User,
        payload: dict[str, Any],
    ) -> ReportResponse:
        report_id = uuid4().hex
        artifact_path = self._artifact_path(str(user.id), report_id)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)

        created_at = datetime.now(timezone.utc)
        artifact_payload = {
            "report_id": report_id,
            **payload,
            "created_at": created_at.isoformat(),
        }
        artifact_path.write_text(json.dumps(artifact_payload, indent=2), encoding="utf-8")

        record = GeneratedReport(
            id=report_id,
            user_id=user.id,
            mode=str(payload["mode"]),
            title=str(payload["title"]),
            role=payload.get("role"),
            experience_level=payload.get("experience_level"),
            topic=payload.get("topic"),
            summary=str(payload["summary"]),
            communication_score=float(payload.get("communication_score", 0.0)),
            technical_score=payload.get("technical_score"),
            confidence_score=float(payload.get("confidence_score", 0.0)),
            posture_score=float(payload.get("posture_score", 0.0)),
            eye_contact_score=float(payload.get("eye_contact_score", 0.0)),
            malpractice_score=float(payload.get("malpractice_score", 0.0)),
            overall_score=float(payload.get("overall_score", 0.0)),
            strengths=list(payload.get("strengths", [])),
            weaknesses=list(payload.get("weaknesses", [])),
            coaching_tips=list(payload.get("coaching_tips", [])),
            learning_roadmap=list(payload.get("learning_roadmap", [])),
            recommendations=list(payload.get("recommendations", [])),
            analytics=dict(payload.get("analytics", {})),
            artifact_relative_path=self._relative_path(artifact_path),
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return self._to_response(record)

    async def list_reports(self, user: User) -> list[ReportResponse]:
        result = await self.db.execute(
            select(GeneratedReport)
            .where(GeneratedReport.user_id == user.id)
            .order_by(GeneratedReport.created_at.desc())
        )
        records = result.scalars().all()
        return [self._to_response(record) for record in records]

    async def get_report(self, user: User, report_id: str) -> ReportResponse:
        result = await self.db.execute(
            select(GeneratedReport).where(
                GeneratedReport.id == report_id,
                GeneratedReport.user_id == user.id,
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
        return self._to_response(record)

    @staticmethod
    def _to_response(record: GeneratedReport) -> ReportResponse:
        return ReportResponse(
            report_id=record.id,
            mode=record.mode,
            title=record.title,
            role=record.role,
            experience_level=record.experience_level,
            topic=record.topic,
            summary=record.summary,
            communication_score=record.communication_score,
            technical_score=record.technical_score,
            confidence_score=record.confidence_score,
            posture_score=record.posture_score,
            eye_contact_score=record.eye_contact_score,
            malpractice_score=record.malpractice_score,
            overall_score=record.overall_score,
            strengths=list(record.strengths or []),
            weaknesses=list(record.weaknesses or []),
            coaching_tips=list(record.coaching_tips or []),
            learning_roadmap=[
                LearningRoadmapItem.model_validate(item)
                for item in list(record.learning_roadmap or [])
            ],
            recommendations=[
                ResourceRecommendation.model_validate(item)
                for item in list(record.recommendations or [])
            ],
            analytics=dict(record.analytics or {}),
            artifact_relative_path=record.artifact_relative_path,
            created_at=record.created_at,
        )

    @staticmethod
    def _artifact_path(user_id: str, report_id: str) -> Path:
        return settings.reports_dir_path / "final" / user_id / f"{report_id}.json"

    @staticmethod
    def _relative_path(path: Path) -> str:
        try:
            return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
        except ValueError:
            return str(path)
