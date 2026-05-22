from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.utils.optional_imports import optional_import


class SpeechProcessingService:
    def __init__(self) -> None:
        self._model = None

    def _get_model(self):
        whisperx_module = optional_import("whisperx")
        if whisperx_module is None:
            raise RuntimeError("WhisperX is not installed.")
        if self._model is None:
            self._model = (
                whisperx_module,
                whisperx_module.load_model(
                    settings.transcription_model_size,
                    settings.transcription_device,
                    compute_type=settings.transcription_compute_type,
                    language=None,
                ),
            )
        return self._model

    def transcribe(self, audio_path: str) -> dict[str, Any]:
        whisperx_module, model = self._get_model()
        audio = whisperx_module.load_audio(audio_path)
        result = model.transcribe(audio, batch_size=settings.transcription_batch_size)
        segments = result.get("segments", []) or []
        language = result.get("language", "en")
        segment_list = [
            {
                "start": segment.get("start", 0.0),
                "end": segment.get("end", 0.0),
                "text": str(segment.get("text", "")).strip(),
            }
            for segment in segments
        ]
        transcript = " ".join(segment["text"] for segment in segment_list).strip()
        return {
            "transcript": transcript,
            "transcript_segments": segment_list,
            "language": language,
        }


speech_processing_service = SpeechProcessingService()
