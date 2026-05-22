from collections import Counter
from datetime import datetime, timezone
from statistics import mean

from app.models.user import User
from app.schemas.coaching import (
    ExperienceLevel,
    InterviewFinalReport,
    InterviewQuestionPrompt,
    InterviewSessionCreateRequest,
    InterviewSessionResponse,
    InterviewSessionStatus,
    InterviewSubmitAnswerRequest,
    InterviewTurnResult,
    TechnicalEvaluationResult,
)
from app.schemas.report import LearningRoadmapItem
from app.services.coaching_service import coaching_service
from app.services.interview_llm_service import InterviewLLMService
from app.services.memory_service import memory_service
from app.services.question_bank_service import QuestionBankService
from app.services.recommendation_service import recommendation_service
from app.services.recording_analysis_service import RecordingAnalysisService
from app.services.session_storage_service import SessionStorageService

LEVEL_TO_DIFFICULTY = {
    ExperienceLevel.ENTRY: "easy",
    ExperienceLevel.MID: "medium",
    ExperienceLevel.SENIOR: "hard",
}


class InterviewSessionService:
    def __init__(self, user: User):
        self.user = user
        self.storage = SessionStorageService(str(user.id), "interview_sessions")
        self.question_bank = QuestionBankService()
        self.analysis_service = RecordingAnalysisService(user)
        self.interview_llm_service = InterviewLLMService()

    def create_session(self, payload: InterviewSessionCreateRequest) -> InterviewSessionResponse:
        difficulty = LEVEL_TO_DIFFICULTY[payload.experience_level]
        current_question = self.question_bank.select_initial_question(payload.role, difficulty)
        now = datetime.now(timezone.utc)
        session_id = self.storage.create_id()
        raw_session = {
            "session_id": session_id,
            "role": payload.role,
            "experience_level": payload.experience_level.value,
            "difficulty": difficulty,
            "target_question_count": max(payload.target_question_count, 1),
            "answered_question_count": 0,
            "status": InterviewSessionStatus.ACTIVE.value,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "current_question": current_question.model_dump(mode="json"),
            "resume_filename": payload.resume_filename,
            "resume_notes": payload.resume_notes,
            "turns": [],
            "used_question_ids": [current_question.question_id],
        }
        self.storage.save(session_id, raw_session)
        return self._to_session_response(raw_session)

    def get_session(self, session_id: str) -> InterviewSessionResponse:
        return self._to_session_response(self.storage.load(session_id))

    async def submit_answer(
        self,
        session_id: str,
        payload: InterviewSubmitAnswerRequest,
    ) -> InterviewTurnResult:
        raw_session = self.storage.load(session_id)
        if raw_session["status"] == InterviewSessionStatus.COMPLETED.value:
            final_report = await self._build_final_report(raw_session)
            session = self._to_session_response(raw_session)
            completed_question = InterviewQuestionPrompt.model_validate(raw_session["turns"][-1]["question"])
            completed_evaluation = TechnicalEvaluationResult.model_validate(
                raw_session["turns"][-1]["technical_evaluation"]
            )
            return InterviewTurnResult(
                session=session,
                question=completed_question,
                technical_evaluation=completed_evaluation,
                communication_score=raw_session["turns"][-1]["communication_score"],
                coaching_feedback=raw_session["turns"][-1]["coaching_feedback"],
                next_question=None,
                final_report=final_report,
            )

        current_question = InterviewQuestionPrompt.model_validate(raw_session["current_question"])
        analysis = self.analysis_service.get_existing_analysis(payload.recording_id)
        conversation_history = self._conversation_history(raw_session)
        memory_context = memory_service.retrieve_user_context(
            str(self.user.id),
            f"{raw_session['role']} {current_question.topic}",
            limit=3,
        )
        technical_evaluation = self.interview_llm_service.evaluate_answer(
            current_question,
            analysis,
            conversation_history,
            memory_context=memory_context,
        )
        communication_score = analysis.communication_analysis.fluency_score
        coaching_feedback = self._build_turn_feedback(technical_evaluation, analysis, current_question)

        turn = {
            "turn_index": raw_session["answered_question_count"] + 1,
            "recording_id": payload.recording_id,
            "question": current_question.model_dump(mode="json"),
            "technical_evaluation": technical_evaluation.model_dump(mode="json"),
            "communication_score": communication_score,
            "words_per_minute": analysis.communication_analysis.words_per_minute,
            "filler_word_total": analysis.communication_analysis.filler_word_total,
            "posture_score": analysis.video_analysis.posture.posture_score,
            "eye_contact_score": analysis.video_analysis.eye_contact.eye_contact_score,
            "malpractice_score": analysis.video_analysis.malpractice.malpractice_confidence_score,
            "coaching_feedback": coaching_feedback,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }
        raw_session["turns"].append(turn)
        raw_session["answered_question_count"] += 1

        next_question = None
        if raw_session["answered_question_count"] >= raw_session["target_question_count"]:
            raw_session["status"] = InterviewSessionStatus.COMPLETED.value
            raw_session["current_question"] = None
        else:
            next_question = self.interview_llm_service.generate_follow_up_question(
                current_question=current_question,
                role=raw_session["role"],
                difficulty=raw_session["difficulty"],
                analysis=analysis,
                technical_evaluation=technical_evaluation,
                conversation_history=conversation_history + [
                    {
                        "question": current_question.question,
                        "technical_summary": technical_evaluation.summary,
                        "missing_concepts": technical_evaluation.missing_concepts,
                        "communication_score": communication_score,
                    }
                ],
                memory_context=memory_context,
                used_question_ids=set(raw_session.get("used_question_ids", [])),
            )
            if next_question:
                raw_session["current_question"] = next_question.model_dump(mode="json")
                raw_session.setdefault("used_question_ids", []).append(next_question.question_id)
            else:
                raw_session["status"] = InterviewSessionStatus.COMPLETED.value
                raw_session["current_question"] = None

        saved = self.storage.save(session_id, raw_session)
        session = self._to_session_response(saved)
        final_report = await self._build_final_report(saved) if session.status == InterviewSessionStatus.COMPLETED else None

        return InterviewTurnResult(
            session=session,
            question=current_question,
            technical_evaluation=technical_evaluation,
            communication_score=communication_score,
            coaching_feedback=coaching_feedback,
            next_question=next_question,
            final_report=final_report,
        )

    async def get_final_report(self, session_id: str) -> InterviewFinalReport:
        return await self._build_final_report(self.storage.load(session_id))

    def attach_report_id(self, session_id: str, report_id: str) -> None:
        raw_session = self.storage.load(session_id)
        raw_session["report_id"] = report_id
        self.storage.save(session_id, raw_session)

    @staticmethod
    def _build_turn_feedback(
        technical_evaluation: TechnicalEvaluationResult,
        analysis,
        question: InterviewQuestionPrompt,
    ) -> list[str]:
        feedback: list[str] = []
        if technical_evaluation.missing_concepts:
            feedback.append(
                f"Revisit {', '.join(technical_evaluation.missing_concepts[:3])} before answering another {question.topic} question."
            )
        if analysis.communication_analysis.words_per_minute > 160:
            feedback.append("Slow down slightly so the explanation feels more controlled under interview pressure.")
        if analysis.communication_analysis.filler_word_total > 3:
            feedback.append("Reduce filler words when transitioning between technical points.")
        if analysis.video_analysis.posture.posture_score < 65:
            feedback.append("Stabilize posture so technical confidence comes across more clearly on camera.")
        if not feedback:
            feedback.append("Keep the same concise structure and add one extra implementation detail in the next answer.")
        return feedback

    @staticmethod
    def _conversation_history(raw_session: dict) -> list[dict]:
        history: list[dict] = []
        for turn in raw_session.get("turns", []):
            history.append(
                {
                    "question": turn["question"]["question"],
                    "topic": turn["question"]["topic"],
                    "technical_summary": turn["technical_evaluation"]["summary"],
                    "missing_concepts": turn["technical_evaluation"].get("missing_concepts", []),
                    "communication_score": turn.get("communication_score", 0),
                }
            )
        return history

    async def _build_final_report(self, raw_session: dict) -> InterviewFinalReport:
        turns = raw_session.get("turns", [])
        technical_scores = [turn["technical_evaluation"]["technical_score"] for turn in turns] or [0]
        communication_scores = [turn.get("communication_score", 0) for turn in turns] or [0]
        words_per_minute_scores = [turn.get("words_per_minute", 0) for turn in turns] or [0]
        filler_word_totals = [turn.get("filler_word_total", 0) for turn in turns] or [0]
        posture_scores = [turn.get("posture_score", 0) for turn in turns] or [0]
        eye_contact_scores = [turn.get("eye_contact_score", 0) for turn in turns] or [0]
        malpractice_scores = [turn.get("malpractice_score", 0) for turn in turns] or [0]

        topic_scores: list[tuple[str, int]] = [
            (turn["question"]["topic"], turn["technical_evaluation"]["technical_score"])
            for turn in turns
        ]
        strongest_topics = [
            topic for topic, _ in sorted(topic_scores, key=lambda item: item[1], reverse=True)[:2]
        ]
        weakest_topics = [
            topic for topic, _ in sorted(topic_scores, key=lambda item: item[1])[:2]
        ]

        recurring_missing_concepts = [
            concept
            for concept, _ in Counter(
                concept
                for turn in turns
                for concept in turn["technical_evaluation"].get("missing_concepts", [])
            ).most_common(5)
        ]
        strengths = [
            strength
            for strength, _ in Counter(
                item
                for turn in turns
                for item in turn["technical_evaluation"].get("strengths", [])
            ).most_common(4)
        ]
        weaknesses = [
            weakness
            for weakness, _ in Counter(
                item
                for turn in turns
                for item in turn["technical_evaluation"].get("weaknesses", [])
            ).most_common(4)
        ]
        focus_topics = list(dict.fromkeys([*weakest_topics, *recurring_missing_concepts]))[:5]
        memory_context = memory_service.retrieve_user_context(
            str(self.user.id),
            " ".join([raw_session["role"], *focus_topics]),
            limit=3,
        )
        recommendations = await recommendation_service.recommend(
            focus_topics or weakest_topics,
            include_communication=True,
        )
        recommendation_lookup = {resource.topic.lower(): resource for resource in recommendations}
        learning_roadmap = [
            LearningRoadmapItem(
                skill=topic,
                next_step=f"Rehearse one tighter explanation and one hands-on exercise for {topic}.",
                resource_title=(
                    recommendation_lookup.get(topic.lower()).title
                    if recommendation_lookup.get(topic.lower())
                    else None
                ),
                resource_url=(
                    recommendation_lookup.get(topic.lower()).url
                    if recommendation_lookup.get(topic.lower())
                    else None
                ),
            )
            for topic in focus_topics[:5]
        ]
        personalized_coaching = coaching_service.personalize(
            mode="interview",
            strengths=strengths,
            weaknesses=weaknesses,
            current_focus_topics=focus_topics[:3],
            memory_context=memory_context,
        )

        return InterviewFinalReport(
            session_id=raw_session["session_id"],
            role=raw_session["role"],
            experience_level=ExperienceLevel(raw_session["experience_level"]),
            completed_at=datetime.now(timezone.utc),
            question_count=len(turns),
            average_technical_score=round(mean(technical_scores), 2),
            average_communication_score=round(mean(communication_scores), 2),
            average_words_per_minute=round(mean(words_per_minute_scores), 2),
            average_filler_words=round(mean(filler_word_totals), 2),
            average_posture_score=round(mean(posture_scores), 2),
            average_eye_contact_score=round(mean(eye_contact_scores), 2),
            average_malpractice_score=round(mean(malpractice_scores), 2),
            strongest_topics=strongest_topics,
            weakest_topics=weakest_topics,
            recurring_missing_concepts=recurring_missing_concepts,
            strengths=strengths,
            weaknesses=weaknesses,
            final_coaching_summary=(
                f"Across {len(turns)} answers, technical performance averaged {round(mean(technical_scores), 2)}/100 "
                f"and communication averaged {round(mean(communication_scores), 2)}/100."
            ),
            personalized_coaching=personalized_coaching,
            learning_roadmap=learning_roadmap,
            recommendations=recommendations,
            report_id=raw_session.get("report_id"),
        )

    @staticmethod
    def _to_session_response(raw_session: dict) -> InterviewSessionResponse:
        current_question = (
            InterviewQuestionPrompt.model_validate(raw_session["current_question"])
            if raw_session.get("current_question")
            else None
        )
        return InterviewSessionResponse(
            session_id=raw_session["session_id"],
            role=raw_session["role"],
            experience_level=ExperienceLevel(raw_session["experience_level"]),
            target_question_count=raw_session["target_question_count"],
            answered_question_count=raw_session["answered_question_count"],
            status=InterviewSessionStatus(raw_session["status"]),
            created_at=datetime.fromisoformat(raw_session["created_at"]),
            updated_at=datetime.fromisoformat(raw_session["updated_at"]),
            current_question=current_question,
            resume_filename=raw_session.get("resume_filename"),
            resume_notes=raw_session.get("resume_notes"),
        )
