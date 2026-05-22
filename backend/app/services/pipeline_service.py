from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.report import SessionReport
from backend.app.models.session import CoachingSession, SessionMode, SessionStatus
from backend.app.models.user import User
from backend.app.schemas.session import RecordingSubmission, SessionCreate
from backend.app.services.coaching_service import coaching_service
from backend.app.services.communication_analysis_service import communication_analysis_service
from backend.app.services.interview_engine_service import interview_engine_service
from backend.app.services.memory_service import memory_service
from backend.app.services.media_processing_service import media_processing_service
from backend.app.services.recommendation_service import recommendation_service
from backend.app.services.resume_analysis_service import resume_analysis_service
from backend.app.services.speech_processing_service import speech_processing_service
from backend.app.services.technical_evaluation_service import technical_evaluation_service
from backend.app.services.video_analysis_service import video_analysis_service


class PipelineService:
    async def create_session(
        self,
        db: AsyncSession,
        user: User,
        payload: SessionCreate,
    ) -> CoachingSession:
        session = CoachingSession(
            user_id=user.id,
            mode=payload.mode,
            role=payload.role,
            experience_level=payload.experience_level,
            topic=payload.topic,
            prompt_context=payload.prompt_context or {},
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def process_submission(
        self,
        db: AsyncSession,
        user: User,
        session: CoachingSession,
        payload: RecordingSubmission,
    ) -> dict[str, Any]:
        session.status = SessionStatus.PROCESSING
        transcript = payload.transcript
        transcript_segments = payload.transcript_segments

        if session.mode != SessionMode.RESUME_ANALYSIS and not transcript:
            audio_path = payload.audio_path
            if not audio_path and payload.video_path:
                audio_path = media_processing_service.extract_audio(payload.video_path)
            if audio_path:
                speech_result = speech_processing_service.transcribe(audio_path)
                transcript = speech_result["transcript"]
                transcript_segments = speech_result["transcript_segments"]

        session.transcript = transcript
        session.transcript_segments = transcript_segments
        session.video_metrics = payload.video_metrics

        communication = (
            communication_analysis_service.analyze(
                transcript or "",
                transcript_segments,
            )
            if session.mode != SessionMode.RESUME_ANALYSIS
            else {
                "communication_score": 0.0,
                "strengths": [],
                "weaknesses": [],
                "coaching_tips": [],
                "wpm": 0.0,
                "pace": "n/a",
                "filler_count": 0,
                "filler_breakdown": {},
                "filler_frequency": 0.0,
                "pause_count": 0,
                "avg_sentence_length": 0.0,
                "grammar_issue_count": 0,
            }
        )
        video = (
            video_analysis_service.analyze(payload.video_metrics)
            if session.mode != SessionMode.RESUME_ANALYSIS
            else {
                "eye_contact_score": 0.0,
                "posture_score": 0.0,
                "malpractice_score": 0.0,
                "confidence_score": 0.0,
                "strengths": [],
                "weaknesses": [],
                "coaching_tips": [],
                "raw_metrics": {},
            }
        )

        technical: dict[str, Any] | None = None
        resume_analysis: dict[str, Any] | None = None
        next_question: str | None = None
        weak_topics: list[str] = []

        memory_context = memory_service.retrieve_user_context(user.id)

        if session.mode == SessionMode.INTERVIEW:
            question_context = session.prompt_context or {}
            technical = technical_evaluation_service.evaluate(
                question_context=question_context,
                answer=transcript or "",
                role=session.role,
            )
            weak_topics = technical["missing_concepts"]
            next_question = interview_engine_service.generate_followup(
                question_context=question_context,
                evaluation=technical,
                memory_context=memory_context,
            )

        if session.mode == SessionMode.RESUME_ANALYSIS:
            resume_analysis = resume_analysis_service.analyze_text(
                resume_text=payload.resume_text or "",
                target_role=payload.target_role or session.role or "SDE",
            )
            weak_topics = resume_analysis["missing_skills"]

        recommendations = recommendation_service.recommend(weak_topics)
        coaching = coaching_service.generate(
            mode=session.mode.value,
            communication=communication,
            video=video,
            technical=technical,
            memory_context=memory_context,
        )

        overall_components = [
            communication["communication_score"],
            video["confidence_score"],
            video["posture_score"],
            video["eye_contact_score"],
        ]
        if technical and technical.get("technical_score") is not None:
            overall_components.append(technical["technical_score"])
        if resume_analysis:
            overall_components.append(resume_analysis["matching_score"])
        overall_score = round(sum(overall_components) / max(len(overall_components), 1), 2)

        analytics = {
            "wpm": communication["wpm"],
            "pace": communication["pace"],
            "filler_count": communication["filler_count"],
            "grammar_issue_count": communication["grammar_issue_count"],
            "weak_topics": weak_topics,
            "recommendations": recommendations,
        }
        if resume_analysis:
            analytics["detected_skills"] = resume_analysis["detected_skills"]
            analytics["missing_skills"] = resume_analysis["missing_skills"]

        report = SessionReport(
            session_id=session.id,
            communication_score=communication["communication_score"],
            technical_score=(technical or {}).get("technical_score"),
            confidence_score=video["confidence_score"],
            posture_score=video["posture_score"],
            eye_contact_score=video["eye_contact_score"],
            malpractice_score=video["malpractice_score"],
            overall_score=overall_score,
            summary=coaching["summary"],
            strengths=coaching["strengths"],
            weaknesses=coaching["weaknesses"],
            coaching_tips=coaching["coaching_tips"],
            learning_roadmap=resume_analysis["learning_roadmap"] if resume_analysis else recommendations,
            analytics=analytics,
        )
        db.add(report)
        session.status = SessionStatus.COMPLETED

        weak_topic = weak_topics[0] if weak_topics else session.topic or session.role or session.mode.value
        memory_service.store_session_summary(
            user_id=user.id,
            session_id=session.id,
            summary_text=coaching["summary"],
            metadata={"weak_topic": weak_topic, "mode": session.mode.value},
        )

        await db.commit()
        await db.refresh(report)
        await db.refresh(session)

        return {
            "report": report,
            "session": session,
            "next_question": next_question,
            "resume_analysis": resume_analysis,
        }

    async def get_session_for_user(
        self,
        db: AsyncSession,
        user_id: int,
        session_id: int,
    ) -> CoachingSession | None:
        result = await db.execute(
            select(CoachingSession).where(
                CoachingSession.id == session_id,
                CoachingSession.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()


pipeline_service = PipelineService()
