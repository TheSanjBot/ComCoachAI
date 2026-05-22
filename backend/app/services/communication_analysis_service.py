from collections import Counter
import re

import nltk.tokenize
import spacy

from app.schemas.analysis import (
    CommunicationAnalysisResult,
    FillerWordStat,
    GrammarIssue,
    TranscriptResult,
)
from app.services.grammar_llm_service import grammar_llm_service

FILLER_PHRASES = [
    "um",
    "uh",
    "like",
    "actually",
    "basically",
    "you know",
]


def _clamp(value: float, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(int(round(value)), maximum))


class CommunicationAnalysisService:
    @staticmethod
    def grammar_llm_available() -> bool:
        return grammar_llm_service.provider_available()

    def analyze(
        self,
        transcript_result: TranscriptResult,
        duration_seconds: float | None,
    ) -> CommunicationAnalysisResult:
        warnings = list(transcript_result.warnings)
        transcript = transcript_result.transcript.strip()
        if not transcript:
            warnings.append("Transcript text was empty, so communication analysis is limited.")
            return CommunicationAnalysisResult(
                fluency_score=0,
                filler_word_total=0,
                filler_word_frequency=0.0,
                filler_word_breakdown=[],
                pause_count=0,
                average_pause_duration=0.0,
                long_pause_count=0,
                words_per_minute=0.0,
                pace_classification="unknown",
                sentence_quality_score=0,
                lexical_diversity=0.0,
                summary="No transcript was available to score communication quality.",
                warnings=warnings,
            )

        normalized_text = transcript.lower()
        filler_counts = Counter(
            {
                phrase: len(re.findall(rf"\b{re.escape(phrase)}\b", normalized_text))
                for phrase in FILLER_PHRASES
            }
        )
        filler_total = sum(filler_counts.values())
        filler_breakdown = [
            FillerWordStat(filler=filler, count=count)
            for filler, count in filler_counts.items()
            if count > 0
        ]

        word_count = transcript_result.word_count or len(re.findall(r"[A-Za-z']+", transcript))
        lexical_words = re.findall(r"[A-Za-z']+", normalized_text)
        lexical_diversity = round(
            len(set(lexical_words)) / len(lexical_words), 3
        ) if lexical_words else 0.0

        effective_duration = duration_seconds or transcript_result.duration_seconds or 0.0
        words_per_minute = round(word_count / (effective_duration / 60), 2) if effective_duration else 0.0
        if words_per_minute == 0:
            pace_classification = "unknown"
        elif words_per_minute < 110:
            pace_classification = "slow"
        elif words_per_minute <= 160:
            pace_classification = "ideal"
        else:
            pace_classification = "fast"

        pause_durations: list[float] = []
        if len(transcript_result.segments) > 1:
            for current, next_segment in zip(
                transcript_result.segments, transcript_result.segments[1:]
            ):
                gap = max(0.0, next_segment.start - current.end)
                if gap >= 0.35:
                    pause_durations.append(round(gap, 3))
        pause_count = len(pause_durations)
        average_pause_duration = round(sum(pause_durations) / pause_count, 3) if pause_count else 0.0
        long_pause_count = sum(1 for pause in pause_durations if pause >= 1.2)

        sentences = self._split_sentences(transcript)
        average_sentence_length = word_count / max(len(sentences), 1)
        sentence_quality_score = _clamp(
            68
            + lexical_diversity * 24
            - abs(average_sentence_length - 17) * 1.6
            - filler_total * 1.5
        )

        grammar_issues, grammar_score, grammar_warnings = self._run_grammar_check(transcript, word_count)
        warnings.extend(grammar_warnings)

        grammar_penalty = (100 - grammar_score) * 0.35 if grammar_score is not None else 0.0
        fluency_score = _clamp(
            100
            - filler_total * 3.2
            - max(words_per_minute - 160, 0) * 0.2
            - max(110 - words_per_minute, 0) * 0.12
            - pause_count * 2.4
            - long_pause_count * 4.5
            - grammar_penalty
        )

        strengths: list[str] = []
        weaknesses: list[str] = []

        if pace_classification == "ideal":
            strengths.append("Speaking pace is inside the ideal range.")
        else:
            weaknesses.append(f"Speaking pace is currently {pace_classification}.")

        if filler_total <= 2:
            strengths.append("Filler word usage stayed low.")
        else:
            weaknesses.append("Filler words appeared often enough to affect fluency.")

        if average_pause_duration and average_pause_duration < 1.0:
            strengths.append("Pauses were mostly controlled and brief.")
        elif pause_count:
            weaknesses.append("Longer pauses broke answer flow.")

        if sentence_quality_score >= 75:
            strengths.append("Sentence structure was generally clear and readable.")
        else:
            weaknesses.append("Sentence structure needs more concise framing.")

        summary = (
            f"Fluency scored {fluency_score}/100 with {words_per_minute} WPM, "
            f"{filler_total} filler words, and {pause_count} notable pauses."
        )

        filler_frequency = round(filler_total / max(word_count, 1), 3)

        return CommunicationAnalysisResult(
            fluency_score=fluency_score,
            grammar_score=grammar_score,
            filler_word_total=filler_total,
            filler_word_frequency=filler_frequency,
            filler_word_breakdown=filler_breakdown,
            pause_count=pause_count,
            average_pause_duration=average_pause_duration,
            long_pause_count=long_pause_count,
            words_per_minute=words_per_minute,
            pace_classification=pace_classification,
            sentence_quality_score=sentence_quality_score,
            lexical_diversity=lexical_diversity,
            grammar_issues=grammar_issues,
            strengths=strengths,
            weaknesses=weaknesses,
            summary=summary,
            warnings=warnings,
        )

    def _run_grammar_check(
        self,
        transcript: str,
        word_count: int,
    ) -> tuple[list[GrammarIssue], int | None, list[str]]:
        return grammar_llm_service.evaluate(transcript)

    @staticmethod
    def _split_sentences(transcript: str) -> list[str]:
        try:
            try:
                nlp = spacy.load("en_core_web_sm")
            except Exception:
                nlp = spacy.blank("en")
                if "sentencizer" not in nlp.pipe_names:
                    nlp.add_pipe("sentencizer")
            document = nlp(transcript)
            sentences = [sentence.text.strip() for sentence in document.sents if sentence.text.strip()]
            if sentences:
                return sentences
        except Exception:
            pass

        try:
            sentences = [
                sentence.strip()
                for sentence in nltk.tokenize.sent_tokenize(transcript)
                if sentence.strip()
            ]
            if sentences:
                return sentences
        except Exception:
            pass

        return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", transcript) if sentence.strip()] or [transcript]
