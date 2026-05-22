from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.coaching import (
    InterviewFinalReport,
    InterviewSessionCreateRequest,
    InterviewSessionResponse,
    InterviewSubmitAnswerRequest,
    InterviewTurnResult,
)
from app.services.memory_service import memory_service
from app.services.interview_session_service import InterviewSessionService
from app.services.report_service import GeneratedReportService

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/sessions", response_model=InterviewSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_interview_session(
    payload: InterviewSessionCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> InterviewSessionResponse:
    service = InterviewSessionService(current_user)
    return service.create_session(payload)


@router.get("/sessions/{session_id}", response_model=InterviewSessionResponse)
async def get_interview_session(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> InterviewSessionResponse:
    service = InterviewSessionService(current_user)
    return service.get_session(session_id)


@router.post("/sessions/{session_id}/submit", response_model=InterviewTurnResult)
async def submit_interview_answer(
    session_id: str,
    payload: InterviewSubmitAnswerRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterviewTurnResult:
    service = InterviewSessionService(current_user)
    result = await service.submit_answer(session_id, payload)
    if result.final_report and result.final_report.report_id is None:
        report = await GeneratedReportService(db).create_report(
            current_user,
            _report_payload_from_final_report(result.final_report),
        )
        service.attach_report_id(session_id, report.report_id)
        result.final_report.report_id = report.report_id
        memory_service.store_memory(
            str(current_user.id),
            result.final_report.final_coaching_summary,
            {
                "mode": "interview",
                "role": result.final_report.role,
                "experience_level": result.final_report.experience_level.value,
                "weak_topics": result.final_report.weakest_topics,
                "missing_concepts": result.final_report.recurring_missing_concepts,
                "report_id": report.report_id,
            },
        )
    return result


@router.get("/sessions/{session_id}/report", response_model=InterviewFinalReport)
async def get_interview_report(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> InterviewFinalReport:
    service = InterviewSessionService(current_user)
    return await service.get_final_report(session_id)


def _report_payload_from_final_report(report: InterviewFinalReport) -> dict:
    overall_score = round((report.average_technical_score * 0.6) + (report.average_communication_score * 0.4), 2)
    return {
        "mode": "Interview Training Mode",
        "title": f"{report.role} mock interview",
        "role": report.role,
        "experience_level": report.experience_level.value,
        "summary": report.final_coaching_summary,
        "communication_score": report.average_communication_score,
        "technical_score": report.average_technical_score,
        "confidence_score": report.average_communication_score,
        "posture_score": report.average_posture_score,
        "eye_contact_score": report.average_eye_contact_score,
        "malpractice_score": report.average_malpractice_score,
        "overall_score": overall_score,
        "strengths": report.strengths,
        "weaknesses": report.weaknesses,
        "coaching_tips": report.personalized_coaching,
        "learning_roadmap": [item.model_dump(mode="json") for item in report.learning_roadmap],
        "recommendations": [item.model_dump(mode="json") for item in report.recommendations],
        "analytics": {
            "question_count": report.question_count,
            "strongest_topics": report.strongest_topics,
            "weakest_topics": report.weakest_topics,
            "recurring_missing_concepts": report.recurring_missing_concepts,
            "words_per_minute": report.average_words_per_minute,
            "filler_word_total": report.average_filler_words,
        },
    }
