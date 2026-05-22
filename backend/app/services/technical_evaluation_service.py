from collections import Counter
import re

from app.schemas.analysis import RecordingAnalysisResponse
from app.schemas.coaching import InterviewQuestionPrompt, TechnicalEvaluationResult

UNCERTAINTY_MARKERS = [
    "i am not sure",
    "i don't know",
    "maybe",
    "probably",
    "i guess",
]


def _clamp(value: float, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(int(round(value)), maximum))


class TechnicalEvaluationService:
    def evaluate(
        self,
        question: InterviewQuestionPrompt,
        analysis: RecordingAnalysisResponse,
    ) -> TechnicalEvaluationResult:
        transcript = analysis.transcript.transcript.strip()
        warnings = list(analysis.warnings)

        if not transcript:
            return TechnicalEvaluationResult(
                technical_score=0,
                correctness_score=0,
                explanation_depth_score=0,
                technical_clarity_score=analysis.communication_analysis.fluency_score,
                strengths=[],
                weaknesses=[
                    "No transcribed answer was available, so technical evaluation could not inspect concept coverage."
                ],
                missing_concepts=question.expected_concepts,
                evidence_found=[],
                suggested_followup_topics=[question.topic],
                summary="Technical evaluation is limited because the submitted answer did not produce usable transcript text.",
                strategy="heuristic-fallback",
                warnings=warnings,
            )

        normalized = self._normalize(transcript)
        mentioned_concepts = [
            concept
            for concept in question.expected_concepts
            if self._matches_concept(normalized, concept)
        ]
        missing_concepts = [
            concept for concept in question.expected_concepts if concept not in mentioned_concepts
        ]
        uncertainty_hits = sum(1 for marker in UNCERTAINTY_MARKERS if marker in normalized)
        word_count = analysis.transcript.word_count or len(re.findall(r"[A-Za-z']+", transcript))

        coverage_ratio = len(mentioned_concepts) / max(len(question.expected_concepts), 1)
        correctness_score = _clamp(coverage_ratio * 100 - uncertainty_hits * 12)
        explanation_depth_score = _clamp(
            40
            + min(word_count, 120) * 0.35
            + coverage_ratio * 30
            - max(25 - word_count, 0) * 1.1
        )
        technical_clarity_score = _clamp(
            analysis.communication_analysis.fluency_score * 0.55
            + analysis.communication_analysis.sentence_quality_score * 0.45
        )
        technical_score = _clamp(
            correctness_score * 0.45
            + explanation_depth_score * 0.3
            + technical_clarity_score * 0.25
        )

        strengths: list[str] = []
        weaknesses: list[str] = []
        if mentioned_concepts:
            strengths.append(
                f"Covered {len(mentioned_concepts)} of {len(question.expected_concepts)} expected concepts, including {', '.join(mentioned_concepts[:3])}."
            )
        if correctness_score >= 75:
            strengths.append("Answer stayed technically aligned with the question prompt.")
        if explanation_depth_score >= 70:
            strengths.append("Explanation had enough depth to move beyond a one-line definition.")
        if technical_clarity_score >= 75:
            strengths.append("Technical explanation stayed relatively clear and easy to follow.")

        if missing_concepts:
            weaknesses.append(
                f"Important concepts were missing: {', '.join(missing_concepts[:4])}."
            )
        if word_count < 30:
            weaknesses.append("The answer was short, so important implementation detail was likely left out.")
        if uncertainty_hits:
            weaknesses.append("Hesitation markers reduced confidence in the technical explanation.")
        if technical_clarity_score < 65:
            weaknesses.append("The delivery made some technical points harder to follow cleanly.")

        followup_topics = missing_concepts[:3] or [question.topic]
        summary = (
            f"Technical score {technical_score}/100 with coverage of {len(mentioned_concepts)}/"
            f"{len(question.expected_concepts)} expected concepts."
        )

        return TechnicalEvaluationResult(
            technical_score=technical_score,
            correctness_score=correctness_score,
            explanation_depth_score=explanation_depth_score,
            technical_clarity_score=technical_clarity_score,
            strengths=strengths,
            weaknesses=weaknesses,
            missing_concepts=missing_concepts,
            evidence_found=mentioned_concepts,
            suggested_followup_topics=followup_topics,
            summary=summary,
            strategy="heuristic-question-bank",
            warnings=warnings,
        )

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.lower()).strip()

    @staticmethod
    def _matches_concept(normalized_transcript: str, concept: str) -> bool:
        normalized_concept = concept.lower().strip()
        if normalized_concept in normalized_transcript:
            return True

        concept_tokens = [token for token in re.findall(r"[a-z0-9]+", normalized_concept) if len(token) > 2]
        transcript_counter = Counter(re.findall(r"[a-z0-9]+", normalized_transcript))
        return bool(concept_tokens) and all(transcript_counter[token] > 0 for token in concept_tokens)
