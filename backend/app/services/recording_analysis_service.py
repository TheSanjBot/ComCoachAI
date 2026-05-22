from datetime import datetime, timezone
import json
from pathlib import Path

from app.core.config import PROJECT_ROOT, settings
from app.models.user import User
from app.schemas.analysis import (
    RecordingAnalysisResponse,
    StageDependencyStatus,
)
from app.schemas.recording import RecordingMode
from app.services.audio_processing_service import AudioProcessingService
from app.services.communication_analysis_service import CommunicationAnalysisService
from app.services.recording_service import RecordingService
from app.services.speech_to_text_service import SpeechToTextService
from app.services.video_analysis_service import VideoAnalysisService


class RecordingAnalysisService:
    def __init__(self, user: User):
        self.user = user
        self.recording_service = RecordingService(user)
        self.audio_service = AudioProcessingService()
        self.speech_service = SpeechToTextService()
        self.communication_service = CommunicationAnalysisService()
        self.video_service = VideoAnalysisService()

    async def analyze_recording(self, recording_id: str) -> RecordingAnalysisResponse:
        asset = self.recording_service.get_recording_asset(recording_id)
        mode = RecordingMode(asset.metadata["mode"])
        report_dir = (
            settings.reports_dir_path
            / "sessions"
            / str(self.user.id)
            / mode.value
            / recording_id
        )
        report_dir.mkdir(parents=True, exist_ok=True)

        audio_artifact = self.audio_service.prepare_audio(asset.file_path, report_dir)
        transcript_result = self.speech_service.transcribe_audio(
            audio_artifact.normalized_audio_path or audio_artifact.extracted_audio_path,
            audio_artifact.duration_seconds or asset.metadata.get("duration_seconds"),
        )
        communication_result = self.communication_service.analyze(
            transcript_result,
            audio_artifact.duration_seconds or asset.metadata.get("duration_seconds"),
        )
        video_result = self.video_service.analyze(
            asset.file_path,
            str(asset.metadata.get("face_detection_state", "waiting")),
        )

        combined_warnings = [
            *audio_artifact.warnings,
            *transcript_result.warnings,
            *communication_result.warnings,
            *video_result.warnings,
        ]
        processing_status = "analyzed" if not combined_warnings else "partial"
        analyzed_at = datetime.now(timezone.utc)
        report_path = report_dir / f"{recording_id}-analysis.json"
        report_relative_path = self._relative_path(report_path)

        response = RecordingAnalysisResponse(
            recording_id=recording_id,
            mode=mode,
            processing_status=processing_status,
            analyzed_at=analyzed_at,
            audio_processing=audio_artifact.to_response(),
            transcript=transcript_result,
            communication_analysis=communication_result,
            video_analysis=video_result,
            dependencies=StageDependencyStatus(
                ffmpeg_available=self.audio_service.ffmpeg_available(),
                whisperx_available=self.speech_service.whisperx_available(),
                grammar_llm_available=self.communication_service.grammar_llm_available(),
                cv2_available=self.video_service.cv2_available(),
                mediapipe_available=self.video_service.mediapipe_available(),
            ),
            report_relative_path=report_relative_path,
            warnings=combined_warnings,
        )

        report_path.write_text(
            json.dumps(response.model_dump(mode="json"), indent=2),
            encoding="utf-8",
        )

        self.recording_service.update_recording_metadata(
            asset,
            {
                "processing_status": processing_status,
                "analysis_report_relative_path": report_relative_path,
                "analyzed_at": analyzed_at.isoformat(),
            },
        )
        return response

    def get_existing_analysis(self, recording_id: str) -> RecordingAnalysisResponse:
        asset = self.recording_service.get_recording_asset(recording_id)
        relative_report_path = asset.metadata.get("analysis_report_relative_path")
        if not relative_report_path:
            raise self.recording_service.not_found(
                f"No analysis report exists yet for recording {recording_id}."
            )

        report_path = PROJECT_ROOT / relative_report_path
        if not report_path.exists():
            raise self.recording_service.not_found(
                f"The analysis report for recording {recording_id} could not be found."
            )

        payload = json.loads(report_path.read_text(encoding="utf-8"))
        return RecordingAnalysisResponse.model_validate(payload)

    @staticmethod
    def _relative_path(path: Path) -> str:
        try:
            return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
        except ValueError:
            return str(path)
