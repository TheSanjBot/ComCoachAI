from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.analysis import RecordingAnalysisResponse
from app.schemas.recording import RecordingMode, RecordingUploadResponse
from app.services.recording_analysis_service import RecordingAnalysisService
from app.services.recording_service import RecordingService

router = APIRouter(prefix="/recordings", tags=["recordings"])


@router.post("/upload", response_model=RecordingUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_recording(
    current_user: Annotated[User, Depends(get_current_user)],
    mode: Annotated[RecordingMode, Form(...)],
    duration_seconds: Annotated[int, Form(...)],
    recording: Annotated[UploadFile, File(...)],
    face_detection_state: Annotated[str, Form()] = "waiting",
    face_detected_samples: Annotated[int, Form()] = 0,
    face_missing_samples: Annotated[int, Form()] = 0,
) -> RecordingUploadResponse:
    service = RecordingService(current_user)
    return await service.store_recording(
        mode=mode,
        duration_seconds=max(duration_seconds, 0),
        face_detection_state=face_detection_state,
        face_detected_samples=max(face_detected_samples, 0),
        face_missing_samples=max(face_missing_samples, 0),
        recording=recording,
    )


@router.post("/{recording_id}/analyze", response_model=RecordingAnalysisResponse)
async def analyze_recording(
    recording_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> RecordingAnalysisResponse:
    service = RecordingAnalysisService(current_user)
    return await service.analyze_recording(recording_id)


@router.get("/{recording_id}/analysis", response_model=RecordingAnalysisResponse)
async def get_recording_analysis(
    recording_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> RecordingAnalysisResponse:
    service = RecordingAnalysisService(current_user)
    return service.get_existing_analysis(recording_id)
