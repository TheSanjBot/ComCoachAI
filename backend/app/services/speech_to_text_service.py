from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re

import numpy as np
from pyannote.core import SlidingWindow, SlidingWindowFeature
import torch
import whisperx
from whisperx.audio import SAMPLE_RATE

from app.core.config import settings
from app.schemas.analysis import TranscriptResult, TranscriptSegment, TranscriptWord


def _resolved_transcription_device() -> str:
    configured = settings.transcription_device.strip().lower()
    if configured != "auto":
        return configured
    return "cuda" if torch.cuda.is_available() else "cpu"


def _patch_torch_load_for_whisperx() -> None:
    if getattr(torch.load, "_commcoach_whisperx_patch", False):
        return

    original_load = torch.load

    def patched_load(*args, **kwargs):
        kwargs["weights_only"] = False
        return original_load(*args, **kwargs)

    setattr(patched_load, "_commcoach_whisperx_patch", True)
    torch.load = patched_load


@dataclass
class _FullAudioSegmentationVAD:
    def __call__(self, batch) -> SlidingWindowFeature:
        waveform = batch["waveform"]
        samples = waveform.shape[-1]
        duration = samples / SAMPLE_RATE
        frame_step_seconds = 0.5
        frame_count = max(int(np.ceil(duration / frame_step_seconds)), 2)
        data = np.ones((frame_count, 1), dtype=np.float32)
        window = SlidingWindow(
            start=0.0,
            duration=frame_step_seconds,
            step=frame_step_seconds,
        )
        return SlidingWindowFeature(data, window)


@lru_cache(maxsize=1)
def _get_whisperx_model():
    _patch_torch_load_for_whisperx()
    return whisperx.load_model(
        settings.transcription_model_size,
        _resolved_transcription_device(),
        compute_type=settings.transcription_compute_type,
        language=None,
        vad_model=_FullAudioSegmentationVAD(),
    )


@lru_cache(maxsize=8)
def _get_alignment_components(language_code: str):
    return whisperx.load_align_model(
        language_code=language_code,
        device=_resolved_transcription_device(),
    )


class SpeechToTextService:
    @staticmethod
    def whisperx_available() -> bool:
        return True

    def transcribe_audio(
        self,
        audio_path: Path | None,
        duration_seconds: float | None,
    ) -> TranscriptResult:
        warnings: list[str] = []
        if audio_path is None or not audio_path.exists():
            warnings.append("No prepared audio file was available for transcription.")
            return TranscriptResult(
                transcript="",
                duration_seconds=duration_seconds,
                warnings=warnings,
            )

        model = _get_whisperx_model()
        audio = whisperx.load_audio(str(audio_path))
        result = self._run_transcription(model, audio)

        language = result.get("language")
        if not language:
            raise RuntimeError("WhisperX did not return a detected language.")

        segments_payload = result.get("segments", []) or []
        model_a, metadata = _get_alignment_components(str(language))
        aligned_result = whisperx.align(
            segments_payload,
            model_a,
            metadata,
            audio,
            _resolved_transcription_device(),
            return_char_alignments=False,
        )
        segments_payload = aligned_result.get("segments", segments_payload) or []

        transcript_segments: list[TranscriptSegment] = []
        word_segments: list[TranscriptWord] = []
        transcript_parts: list[str] = []

        for segment_index, segment in enumerate(segments_payload):
            segment_text = str(segment.get("text", "")).strip()
            if segment_text:
                transcript_parts.append(segment_text)
            segment_words: list[TranscriptWord] = []
            for word in segment.get("words", []) or []:
                word_item = TranscriptWord(
                    word=str(word.get("word", "")).strip(),
                    start=round(float(word.get("start", 0.0) or 0.0), 3),
                    end=round(float(word.get("end", 0.0) or 0.0), 3),
                    probability=(
                        float(word.get("score"))
                        if word.get("score") is not None
                        else float(word.get("probability"))
                        if word.get("probability") is not None
                        else None
                    ),
                )
                if word_item.word:
                    segment_words.append(word_item)
                    word_segments.append(word_item)

            transcript_segments.append(
                TranscriptSegment(
                    segment_id=segment_index,
                    start=round(float(segment.get("start", 0.0) or 0.0), 3),
                    end=round(float(segment.get("end", 0.0) or 0.0), 3),
                    text=segment_text,
                    avg_logprob=float(segment.get("avg_logprob"))
                    if segment.get("avg_logprob") is not None
                    else None,
                    no_speech_prob=float(segment.get("no_speech_prob"))
                    if segment.get("no_speech_prob") is not None
                    else None,
                    words=segment_words,
                )
            )

        transcript = " ".join(part for part in transcript_parts if part).strip()
        word_count = len(word_segments)
        if word_count == 0 and transcript:
            word_count = len(re.findall(r"[A-Za-z']+", transcript))

        return TranscriptResult(
            transcript=transcript,
            language=language,
            duration_seconds=duration_seconds,
            segment_count=len(transcript_segments),
            word_count=word_count,
            segments=transcript_segments,
            word_segments=word_segments,
            warnings=warnings,
        )

    @staticmethod
    def _run_transcription(model, audio):
        attempts = [
            {"batch_size": settings.transcription_batch_size, "chunk_size": 20},
            {"batch_size": 1, "chunk_size": 15},
        ]

        last_error: Exception | None = None
        for options in attempts:
            try:
                return model.transcribe(
                    audio,
                    batch_size=options["batch_size"],
                    chunk_size=options["chunk_size"],
                )
            except ValueError as exc:
                if "Invalid input features shape" not in str(exc):
                    raise
                last_error = exc

        if last_error is not None:
            raise last_error
        raise RuntimeError("WhisperX transcription failed before any attempt ran.")
