from datetime import datetime

from pydantic import BaseModel

from app.schemas.recording import RecordingMode


class TranscriptWord(BaseModel):
    word: str
    start: float
    end: float
    probability: float | None = None


class TranscriptSegment(BaseModel):
    segment_id: int
    start: float
    end: float
    text: str
    avg_logprob: float | None = None
    no_speech_prob: float | None = None
    words: list[TranscriptWord] = []


class TranscriptResult(BaseModel):
    transcript: str
    language: str | None = None
    duration_seconds: float | None = None
    segment_count: int = 0
    word_count: int = 0
    segments: list[TranscriptSegment] = []
    word_segments: list[TranscriptWord] = []
    warnings: list[str] = []


class AudioProcessingResult(BaseModel):
    extracted_audio_path: str | None = None
    normalized_audio_path: str | None = None
    sample_rate: int | None = None
    duration_seconds: float | None = None
    normalization_applied: bool = False
    warnings: list[str] = []


class GrammarIssue(BaseModel):
    message: str
    offset: int
    error_length: int
    category: str | None = None
    suggestions: list[str] = []


class FillerWordStat(BaseModel):
    filler: str
    count: int


class CommunicationAnalysisResult(BaseModel):
    fluency_score: int
    grammar_score: int | None = None
    filler_word_total: int
    filler_word_frequency: float
    filler_word_breakdown: list[FillerWordStat]
    pause_count: int
    average_pause_duration: float
    long_pause_count: int
    words_per_minute: float
    pace_classification: str
    sentence_quality_score: int
    lexical_diversity: float
    grammar_issues: list[GrammarIssue] = []
    strengths: list[str] = []
    weaknesses: list[str] = []
    summary: str
    warnings: list[str] = []


class EyeContactAnalysis(BaseModel):
    eye_contact_score: int
    direct_gaze_frames: int
    looking_away_frames: int
    downward_gaze_frames: int
    total_face_frames: int


class PostureAnalysis(BaseModel):
    posture_score: int
    stable_frames: int
    leaning_frames: int
    slouching_frames: int
    instability_index: float


class MalpracticeAnalysis(BaseModel):
    malpractice_confidence_score: int
    repeated_looking_away_events: int
    excessive_downward_gaze_events: int
    multiple_face_frames: int
    summary: str


class VideoBehaviorAnalysisResult(BaseModel):
    sampled_frame_count: int
    frame_sample_interval_seconds: float
    eye_contact: EyeContactAnalysis
    posture: PostureAnalysis
    malpractice: MalpracticeAnalysis
    warnings: list[str] = []


class StageDependencyStatus(BaseModel):
    ffmpeg_available: bool
    whisperx_available: bool
    grammar_llm_available: bool
    cv2_available: bool
    mediapipe_available: bool


class RecordingAnalysisResponse(BaseModel):
    recording_id: str
    mode: RecordingMode
    processing_status: str
    analyzed_at: datetime
    audio_processing: AudioProcessingResult
    transcript: TranscriptResult
    communication_analysis: CommunicationAnalysisResult
    video_analysis: VideoBehaviorAnalysisResult
    dependencies: StageDependencyStatus
    report_relative_path: str | None = None
    warnings: list[str] = []
