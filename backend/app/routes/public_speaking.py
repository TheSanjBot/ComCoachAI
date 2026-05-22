from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.coaching import (
    PublicSpeakingCoachingResult,
    PublicSpeakingSessionCreateRequest,
    PublicSpeakingSessionResponse,
    PublicSpeakingSubmitRequest,
)
from app.services.memory_service import memory_service
from app.services.public_speaking_service import PublicSpeakingService
from app.services.report_service import GeneratedReportService

router = APIRouter(prefix="/public-speaking", tags=["public-speaking"])


@router.post("/sessions", response_model=PublicSpeakingSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_public_speaking_session(
    payload: PublicSpeakingSessionCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> PublicSpeakingSessionResponse:
    service = PublicSpeakingService(current_user)
    return service.create_session(payload)


@router.get("/sessions/{session_id}", response_model=PublicSpeakingSessionResponse)
async def get_public_speaking_session(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> PublicSpeakingSessionResponse:
    service = PublicSpeakingService(current_user)
    return service.get_session(session_id)


@router.post("/sessions/{session_id}/coach", response_model=PublicSpeakingCoachingResult)
async def coach_public_speaking_recording(
    session_id: str,
    payload: PublicSpeakingSubmitRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PublicSpeakingCoachingResult:
    service = PublicSpeakingService(current_user)
    result = await service.coach_recording(session_id, payload)
    if result.report_id is None:
        report = await GeneratedReportService(db).create_report(
            current_user,
            _report_payload_from_coaching_result(result),
        )
        service.attach_report_id(session_id, report.report_id)
        result.report_id = report.report_id
        memory_service.store_memory(
            str(current_user.id),
            result.summary,
            {
                "mode": "public-speaking",
                "topic": result.session.topic,
                "weak_topics": result.weaknesses[:3],
                "report_id": report.report_id,
            },
        )
    return result


def _report_payload_from_coaching_result(result: PublicSpeakingCoachingResult) -> dict:
    overall_score = round(
        (result.confidence_score * 0.35)
        + (result.communication_score * 0.3)
        + (result.posture_score * 0.2)
        + (result.eye_contact_score * 0.15),
        2,
    )
    return {
        "mode": "Public Speaking Training Mode",
        "title": f"{result.session.topic} speaking rehearsal",
        "topic": result.session.topic,
        "summary": result.summary,
        "communication_score": result.communication_score,
        "technical_score": None,
        "confidence_score": result.confidence_score,
        "posture_score": result.posture_score,
        "eye_contact_score": result.eye_contact_score,
        "malpractice_score": result.malpractice_score,
        "overall_score": overall_score,
        "strengths": result.strengths,
        "weaknesses": result.weaknesses,
        "coaching_tips": [
            *result.pacing_suggestions,
            *result.posture_coaching,
            *result.eye_contact_coaching,
            *result.communication_advice,
            *result.personalized_coaching,
        ][:8],
        "learning_roadmap": [item.model_dump(mode="json") for item in result.learning_roadmap],
        "recommendations": [item.model_dump(mode="json") for item in result.recommendations],
        "analytics": {
            "storytelling_feedback": result.storytelling_feedback,
            "pacing_suggestions": result.pacing_suggestions,
            "words_per_minute": result.words_per_minute,
            "filler_word_total": result.filler_word_total,
            "factual_accuracy_score": result.factual_accuracy_score,
            "factual_accuracy_summary": result.factual_accuracy_summary,
            "factual_corrections": result.factual_corrections,
        },
    }
