from __future__ import annotations

from pathlib import Path

from backend.app.core.config import get_settings

try:
    import ffmpeg
except ImportError:  # pragma: no cover - optional dependency
    ffmpeg = None


class MediaProcessingService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def extract_audio(self, video_path: str) -> str:
        source = Path(video_path)
        output = self.settings.uploads_dir / f"{source.stem}.wav"

        if ffmpeg is None:
            raise RuntimeError("ffmpeg-python is not installed.")

        (
            ffmpeg.input(str(source))
            .output(str(output), acodec="pcm_s16le", ac=1, ar="16000")
            .overwrite_output()
            .run(quiet=True)
        )
        return str(output)


media_processing_service = MediaProcessingService()

