from dataclasses import dataclass
from pathlib import Path

import ffmpeg
import librosa
from pydub import AudioSegment
from pydub.effects import normalize

from app.core.config import PROJECT_ROOT, settings
from app.schemas.analysis import AudioProcessingResult


@dataclass
class PreparedAudioArtifact:
    extracted_audio_path: Path | None
    normalized_audio_path: Path | None
    sample_rate: int | None
    duration_seconds: float | None
    normalization_applied: bool
    warnings: list[str]

    def to_response(self) -> AudioProcessingResult:
        return AudioProcessingResult(
            extracted_audio_path=_relative_path(self.extracted_audio_path),
            normalized_audio_path=_relative_path(self.normalized_audio_path),
            sample_rate=self.sample_rate,
            duration_seconds=self.duration_seconds,
            normalization_applied=self.normalization_applied,
            warnings=self.warnings,
        )


def _relative_path(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


class AudioProcessingService:
    @staticmethod
    def ffmpeg_available() -> bool:
        return True

    def prepare_audio(self, recording_path: Path, workspace_dir: Path) -> PreparedAudioArtifact:
        warnings: list[str] = []
        workspace_dir.mkdir(parents=True, exist_ok=True)
        extracted_audio_path = workspace_dir / f"{recording_path.stem}-extracted.wav"
        normalized_audio_path = workspace_dir / f"{recording_path.stem}-normalized.wav"

        try:
            stream = ffmpeg.input(str(recording_path))
            stream = ffmpeg.output(
                stream.audio,
                str(extracted_audio_path),
                ac=1,
                ar=settings.audio_sample_rate,
                format="wav",
            )
            ffmpeg.run(
                stream,
                overwrite_output=True,
                quiet=True,
                capture_stdout=True,
                capture_stderr=True,
            )
        except Exception as exc:
            warnings.append(f"Audio extraction failed: {exc}")
            return PreparedAudioArtifact(None, None, None, None, False, warnings)

        duration_seconds: float | None = None
        sample_rate: int | None = settings.audio_sample_rate
        normalization_applied = False
        final_audio_path = extracted_audio_path

        try:
            segment = AudioSegment.from_file(str(extracted_audio_path))
            normalized_segment = normalize(
                segment.set_channels(1).set_frame_rate(settings.audio_sample_rate)
            )
            normalized_segment.export(str(normalized_audio_path), format="wav")
            duration_seconds = round(len(normalized_segment) / 1000.0, 3)
            normalization_applied = True
            final_audio_path = normalized_audio_path
        except Exception as exc:
            warnings.append(f"Audio normalization via pydub failed: {exc}")

        try:
            sample_rate = settings.audio_sample_rate
            duration_seconds = round(
                float(librosa.get_duration(path=str(final_audio_path))),
                3,
            )
        except Exception as exc:
            warnings.append(f"librosa validation failed: {exc}")

        return PreparedAudioArtifact(
            extracted_audio_path=extracted_audio_path if extracted_audio_path.exists() else None,
            normalized_audio_path=final_audio_path if final_audio_path.exists() else None,
            sample_rate=sample_rate,
            duration_seconds=duration_seconds,
            normalization_applied=normalization_applied,
            warnings=warnings,
        )
