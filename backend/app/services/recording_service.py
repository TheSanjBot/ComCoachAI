from dataclasses import dataclass
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.models.user import User
from app.schemas.recording import RecordingMode, RecordingUploadResponse

logger = logging.getLogger("commcoach")


@dataclass
class RecordingAsset:
    recording_id: str
    file_path: Path
    metadata_path: Path
    metadata: dict[str, Any]


class RecordingService:
    def __init__(self, user: User):
        self.user = user

    async def store_recording(
        self,
        *,
        mode: RecordingMode,
        duration_seconds: int,
        face_detection_state: str,
        face_detected_samples: int,
        face_missing_samples: int,
        recording: UploadFile,
    ) -> RecordingUploadResponse:
        content = await recording.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded recording is empty",
            )

        max_upload_bytes = settings.max_upload_size_mb * 1024 * 1024
        if len(content) > max_upload_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Recording exceeds the {settings.max_upload_size_mb} MB upload limit",
            )

        uploaded_at = datetime.now(timezone.utc)
        recording_id = uuid4().hex
        extension = self._resolve_extension(recording.filename, recording.content_type)

        relative_directory = Path("sessions") / str(self.user.id) / mode.value
        absolute_directory = settings.uploads_dir_path / relative_directory
        absolute_directory.mkdir(parents=True, exist_ok=True)

        stored_filename = f"{uploaded_at.strftime('%Y%m%dT%H%M%SZ')}-{recording_id}{extension}"
        file_path = absolute_directory / stored_filename
        file_path.write_bytes(content)

        metadata = {
            "recording_id": recording_id,
            "user_id": str(self.user.id),
            "mode": mode.value,
            "original_filename": recording.filename or f"recording{extension}",
            "stored_filename": stored_filename,
            "content_type": recording.content_type or self._content_type_from_extension(extension),
            "duration_seconds": duration_seconds,
            "file_size_bytes": len(content),
            "uploaded_at": uploaded_at.isoformat(),
            "relative_path": str(relative_directory / stored_filename).replace("\\", "/"),
            "face_detection_state": face_detection_state,
            "face_detected_samples": face_detected_samples,
            "face_missing_samples": face_missing_samples,
            "processing_status": "stored",
            "analysis_report_relative_path": None,
            "analyzed_at": None,
        }

        metadata_path = file_path.with_suffix(file_path.suffix + ".json")
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        logger.info(
            "Stored recording %s for user=%s mode=%s at %s",
            recording_id,
            self.user.id,
            mode.value,
            file_path,
        )

        return RecordingUploadResponse(
            recording_id=recording_id,
            mode=mode,
            original_filename=metadata["original_filename"],
            stored_filename=stored_filename,
            content_type=metadata["content_type"],
            duration_seconds=duration_seconds,
            file_size_bytes=len(content),
            uploaded_at=uploaded_at,
            relative_path=metadata["relative_path"],
            face_detection_state=face_detection_state,
            face_detected_samples=face_detected_samples,
            face_missing_samples=face_missing_samples,
            processing_status="stored",
        )

    @staticmethod
    def _resolve_extension(original_filename: str | None, content_type: str | None) -> str:
        if original_filename:
            suffix = Path(original_filename).suffix.lower()
            if suffix in {".webm", ".mp4"}:
                return suffix
        if content_type == "video/mp4":
            return ".mp4"
        return ".webm"

    @staticmethod
    def _content_type_from_extension(extension: str) -> str:
        return "video/mp4" if extension == ".mp4" else "video/webm"

    def get_recording_asset(self, recording_id: str) -> RecordingAsset:
        user_sessions_dir = settings.uploads_dir_path / "sessions" / str(self.user.id)
        if not user_sessions_dir.exists():
            raise self.not_found(f"No recordings exist yet for user {self.user.id}.")

        for metadata_path in user_sessions_dir.glob(f"**/*{recording_id}*.json"):
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if str(metadata.get("recording_id")) != recording_id:
                continue
            if str(metadata.get("user_id")) != str(self.user.id):
                continue
            file_path = metadata_path.with_suffix("")
            if not file_path.exists():
                raise self.not_found(
                    f"The recording file for {recording_id} could not be found."
                )
            return RecordingAsset(
                recording_id=recording_id,
                file_path=file_path,
                metadata_path=metadata_path,
                metadata=metadata,
            )

        raise self.not_found(f"Recording {recording_id} was not found.")

    def update_recording_metadata(
        self,
        asset: RecordingAsset,
        updates: dict[str, Any],
    ) -> RecordingAsset:
        metadata = {**asset.metadata, **updates}
        asset.metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return RecordingAsset(
            recording_id=asset.recording_id,
            file_path=asset.file_path,
            metadata_path=asset.metadata_path,
            metadata=metadata,
        )

    @staticmethod
    def not_found(detail: str) -> HTTPException:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
