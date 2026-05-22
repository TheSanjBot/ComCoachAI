from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.resume import ResumeAnalysisResponse, ResumeAnalysisTextRequest
from app.services.memory_service import memory_service
from app.services.report_service import GeneratedReportService
from app.services.resume_analysis_service import resume_analysis_service

router = APIRouter(prefix="/resume-analysis", tags=["resume-analysis"])


@router.post("/text", response_model=ResumeAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_resume_text(
    payload: ResumeAnalysisTextRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResumeAnalysisResponse:
    analysis = await resume_analysis_service.analyze_text(
        user=current_user,
        resume_text=payload.resume_text,
        target_role=payload.target_role,
    )
    return await _persist_analysis(db, current_user, analysis)


@router.post("/upload", response_model=ResumeAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_resume_upload(
    target_role: Annotated[str, Form(...)],
    resume: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResumeAnalysisResponse:
    resume_text = await resume_analysis_service.extract_text_from_upload(resume)
    analysis = await resume_analysis_service.analyze_text(
        user=current_user,
        resume_text=resume_text,
        target_role=target_role,
    )
    return await _persist_analysis(db, current_user, analysis)


async def _persist_analysis(
    db: AsyncSession,
    current_user: User,
    analysis: ResumeAnalysisResponse,
) -> ResumeAnalysisResponse:
    if analysis.report_id:
        return analysis

    report = await GeneratedReportService(db).create_report(
        current_user,
        {
            "mode": "Resume + Skill Gap Analysis Mode",
            "title": f"{analysis.target_role} resume review",
            "role": analysis.target_role,
            "summary": (
                f"Resume alignment for {analysis.target_role} is {analysis.matching_score}/100 "
                f"with {len(analysis.missing_skills)} main skill gaps identified."
            ),
            "communication_score": 0.0,
            "technical_score": analysis.matching_score,
            "confidence_score": analysis.matching_score,
            "posture_score": 0.0,
            "eye_contact_score": 0.0,
            "malpractice_score": 0.0,
            "overall_score": analysis.matching_score,
            "strengths": [f"Detected {skill}" for skill in analysis.detected_skills[:5]],
            "weaknesses": [f"Missing {skill}" for skill in analysis.missing_skills[:5]],
            "coaching_tips": analysis.personalized_coaching,
            "learning_roadmap": [item.model_dump(mode="json") for item in analysis.learning_roadmap],
            "recommendations": [item.model_dump(mode="json") for item in analysis.recommendations],
            "analytics": {
                "detected_skills": analysis.detected_skills,
                "missing_skills": analysis.missing_skills,
                "extracted_text_preview": analysis.extracted_text_preview,
            },
        },
    )
    analysis.report_id = report.report_id
    analysis.artifact_relative_path = report.artifact_relative_path
    memory_service.store_memory(
        str(current_user.id),
        f"Resume review for {analysis.target_role} scored {analysis.matching_score}/100.",
        {
            "mode": "resume-skill-gap",
            "target_role": analysis.target_role,
            "weak_topics": analysis.missing_skills,
            "report_id": report.report_id,
        },
    )
    return analysis
