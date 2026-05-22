from datetime import datetime, timezone

from app.models.user import User
from app.schemas.coaching import (
    PublicSpeakingCoachingResult,
    PublicSpeakingSessionCreateRequest,
    PublicSpeakingSessionResponse,
    PublicSpeakingSubmitRequest,
)
from app.schemas.report import LearningRoadmapItem
from app.services.coaching_service import coaching_service
from app.services.content_accuracy_service import content_accuracy_service
from app.services.memory_service import memory_service
from app.services.recommendation_service import recommendation_service
from app.services.recording_analysis_service import RecordingAnalysisService
from app.services.session_storage_service import SessionStorageService


def _clamp(value: float, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(int(round(value)), maximum))


class PublicSpeakingService:
    def __init__(self, user: User):
        self.user = user
        self.storage = SessionStorageService(str(user.id), "public_speaking_sessions")
        self.analysis_service = RecordingAnalysisService(user)

    def create_session(self, payload: PublicSpeakingSessionCreateRequest) -> PublicSpeakingSessionResponse:
        now = datetime.now(timezone.utc)
        session_id = self.storage.create_id()
        raw_session = {
            "session_id": session_id,
            "topic": payload.topic,
            "audience": payload.audience,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "status": "ready",
            "latest_coaching": None,
        }
        self.storage.save(session_id, raw_session)
        return self._to_session_response(raw_session)

    def get_session(self, session_id: str) -> PublicSpeakingSessionResponse:
        return self._to_session_response(self.storage.load(session_id))

    async def coach_recording(
        self,
        session_id: str,
        payload: PublicSpeakingSubmitRequest,
    ) -> PublicSpeakingCoachingResult:
        raw_session = self.storage.load(session_id)
        analysis = self.analysis_service.get_existing_analysis(payload.recording_id)

        confidence_score = _clamp(
            analysis.communication_analysis.fluency_score * 0.45
            + analysis.video_analysis.eye_contact.eye_contact_score * 0.25
            + analysis.video_analysis.posture.posture_score * 0.2
            + analysis.communication_analysis.sentence_quality_score * 0.1
        )

        pacing_suggestions: list[str] = []
        if analysis.communication_analysis.pace_classification == "fast":
            pacing_suggestions.append("Slow your pace slightly so the audience can absorb each key point.")
        elif analysis.communication_analysis.pace_classification == "slow":
            pacing_suggestions.append("Add a little more energy to the pace so the delivery feels more confident.")
        else:
            pacing_suggestions.append("Keep the current pace range and preserve the controlled rhythm.")

        if analysis.communication_analysis.long_pause_count:
            pacing_suggestions.append("Use shorter transitions between ideas to reduce long silent gaps.")
        if analysis.communication_analysis.filler_word_total > 3:
            pacing_suggestions.append("Reduce filler words by pausing briefly before the next idea instead of filling space.")

        posture_coaching = [
            "Maintain a taller chest-up posture and reduce side-to-side movement."
            if analysis.video_analysis.posture.posture_score < 70
            else "Posture stayed stable enough to support a confident presence."
        ]
        eye_contact_coaching = [
            "Spend more time looking toward the camera to create stronger audience connection."
            if analysis.video_analysis.eye_contact.eye_contact_score < 70
            else "Eye contact pattern supports a steady speaking presence."
        ]
        communication_advice = list(analysis.communication_analysis.weaknesses[:3]) or [
            "Continue opening with a short framing sentence before expanding into details."
        ]
        storytelling_feedback = self._build_storytelling_feedback(analysis.transcript.transcript)
        factual_review = content_accuracy_service.review_public_speaking_transcript(
            raw_session["topic"],
            analysis.transcript.transcript,
        )

        strengths = list(analysis.communication_analysis.strengths)
        if confidence_score >= 75:
            strengths.append("Overall delivery reads as confident and controlled.")
        strengths.extend(factual_review.factual_highlights[:2])
        weaknesses = list(analysis.communication_analysis.weaknesses)
        if analysis.video_analysis.posture.posture_score < 65:
            weaknesses.append("Body language still loses some confidence during the take.")
        weaknesses.extend(factual_review.factual_corrections[:2])
        focus_topics = self._focus_topics(raw_session["topic"], weaknesses)
        memory_context = memory_service.retrieve_user_context(
            str(self.user.id),
            raw_session["topic"],
            limit=3,
        )
        recommendations = await recommendation_service.recommend(
            focus_topics,
            include_communication=True,
        )
        recommendation_lookup = {resource.topic.lower(): resource for resource in recommendations}
        learning_roadmap = [
            LearningRoadmapItem(
                skill=topic,
                next_step=f"Run one focused rehearsal specifically targeting {topic}.",
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
            mode="public-speaking",
            strengths=strengths,
            weaknesses=weaknesses,
            current_focus_topics=focus_topics[:3],
            memory_context=memory_context,
        )

        raw_session["status"] = "coached"
        raw_session["latest_coaching"] = {
            "recording_id": payload.recording_id,
            "confidence_score": confidence_score,
            "summary": f"Public speaking confidence scored {confidence_score}/100 for topic {raw_session['topic']}.",
        }
        saved = self.storage.save(session_id, raw_session)
        session = self._to_session_response(saved)

        return PublicSpeakingCoachingResult(
            session=session,
            recording_id=payload.recording_id,
            confidence_score=confidence_score,
            communication_score=analysis.communication_analysis.fluency_score,
            factual_accuracy_score=factual_review.factual_accuracy_score,
            words_per_minute=analysis.communication_analysis.words_per_minute,
            filler_word_total=analysis.communication_analysis.filler_word_total,
            posture_score=analysis.video_analysis.posture.posture_score,
            eye_contact_score=analysis.video_analysis.eye_contact.eye_contact_score,
            malpractice_score=analysis.video_analysis.malpractice.malpractice_confidence_score,
            pacing_suggestions=pacing_suggestions,
            posture_coaching=posture_coaching,
            eye_contact_coaching=eye_contact_coaching,
            communication_advice=communication_advice,
            storytelling_feedback=storytelling_feedback,
            factual_highlights=factual_review.factual_highlights,
            factual_corrections=factual_review.factual_corrections,
            strengths=strengths,
            weaknesses=weaknesses,
            summary=f"Public speaking confidence scored {confidence_score}/100 for topic {raw_session['topic']}.",
            factual_accuracy_summary=factual_review.factual_accuracy_summary,
            personalized_coaching=personalized_coaching,
            learning_roadmap=learning_roadmap,
            recommendations=recommendations,
            report_id=raw_session.get("report_id"),
        )

    def attach_report_id(self, session_id: str, report_id: str) -> None:
        raw_session = self.storage.load(session_id)
        raw_session["report_id"] = report_id
        self.storage.save(session_id, raw_session)

    @staticmethod
    def _build_storytelling_feedback(transcript: str) -> list[str]:
        cleaned = transcript.strip()
        if not cleaned:
            return ["A clearer opening and a complete rehearsal will help storytelling feedback become more specific."]

        sentence_count = max(cleaned.count("."), 1)
        if sentence_count < 3:
            return [
                "Add a clearer beginning-middle-end structure so the talk feels more like a full mini-story.",
                "Consider opening with one concise context-setting sentence before the main point.",
            ]

        return [
            "The rehearsal has enough structure to coach flow; keep transitions explicit between your main ideas.",
            "Close with one stronger takeaway sentence so the audience remembers the core message.",
        ]

    @staticmethod
    def _focus_topics(topic: str, weaknesses: list[str]) -> list[str]:
        focus_topics = ["public speaking", "communication", "storytelling"]
        lowered_weaknesses = " ".join(weaknesses).lower()
        if "posture" in lowered_weaknesses or "body language" in lowered_weaknesses:
            focus_topics.append("body language")
        if "eye contact" in lowered_weaknesses:
            focus_topics.append("presentation delivery")
        if "pace" in lowered_weaknesses or "filler" in lowered_weaknesses:
            focus_topics.append("speaking clarity")
        if "fact" in lowered_weaknesses or "incorrect" in lowered_weaknesses:
            focus_topics.append("research and fact checking")
        if topic.strip():
            focus_topics.append(f"{topic} presentation")
        return list(dict.fromkeys(focus_topics))

    @staticmethod
    def _to_session_response(raw_session: dict) -> PublicSpeakingSessionResponse:
        return PublicSpeakingSessionResponse(
            session_id=raw_session["session_id"],
            topic=raw_session["topic"],
            audience=raw_session.get("audience"),
            created_at=datetime.fromisoformat(raw_session["created_at"]),
            updated_at=datetime.fromisoformat(raw_session["updated_at"]),
            status=raw_session["status"],
        )
