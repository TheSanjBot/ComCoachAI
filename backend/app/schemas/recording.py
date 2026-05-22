from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class RecordingMode(str, Enum):
    INTERVIEW_TRAINING = "interview-training"
    PUBLIC_SPEAKING = "public-speaking"


class RecordingUploadResponse(BaseModel):
    recording_id: str
    mode: RecordingMode
    original_filename: str
    stored_filename: str
    content_type: str
    duration_seconds: int
    file_size_bytes: int
    uploaded_at: datetime
    relative_path: str
    face_detection_state: str
    face_detected_samples: int
    face_missing_samples: int
    processing_status: str
