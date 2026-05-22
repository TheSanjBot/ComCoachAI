import { API_BASE_URL, clearClientSessionState } from "@/lib/api";
import type { RecordingModeSlug } from "@/lib/mode-config";

export type FaceDetectionState =
  | "waiting"
  | "checking"
  | "detected"
  | "not-detected"
  | "unsupported";

export type RecordingUploadReceipt = {
  recording_id: string;
  mode: RecordingModeSlug;
  original_filename: string;
  stored_filename: string;
  content_type: string;
  duration_seconds: number;
  file_size_bytes: number;
  uploaded_at: string;
  relative_path: string;
  face_detection_state: string;
  face_detected_samples: number;
  face_missing_samples: number;
  processing_status: string;
};

export type TranscriptWord = {
  word: string;
  start: number;
  end: number;
  probability: number | null;
};

export type TranscriptSegment = {
  segment_id: number;
  start: number;
  end: number;
  text: string;
  avg_logprob: number | null;
  no_speech_prob: number | null;
  words: TranscriptWord[];
};

export type TranscriptResult = {
  transcript: string;
  language: string | null;
  duration_seconds: number | null;
  segment_count: number;
  word_count: number;
  segments: TranscriptSegment[];
  word_segments: TranscriptWord[];
  warnings: string[];
};

export type AudioProcessingResult = {
  extracted_audio_path: string | null;
  normalized_audio_path: string | null;
  sample_rate: number | null;
  duration_seconds: number | null;
  normalization_applied: boolean;
  warnings: string[];
};

export type GrammarIssue = {
  message: string;
  offset: number;
  error_length: number;
  category: string | null;
  suggestions: string[];
};

export type FillerWordStat = {
  filler: string;
  count: number;
};

export type CommunicationAnalysisResult = {
  fluency_score: number;
  grammar_score: number | null;
  filler_word_total: number;
  filler_word_frequency: number;
  filler_word_breakdown: FillerWordStat[];
  pause_count: number;
  average_pause_duration: number;
  long_pause_count: number;
  words_per_minute: number;
  pace_classification: string;
  sentence_quality_score: number;
  lexical_diversity: number;
  grammar_issues: GrammarIssue[];
  strengths: string[];
  weaknesses: string[];
  summary: string;
  warnings: string[];
};

export type VideoBehaviorAnalysisResult = {
  sampled_frame_count: number;
  frame_sample_interval_seconds: number;
  eye_contact: {
    eye_contact_score: number;
    direct_gaze_frames: number;
    looking_away_frames: number;
    downward_gaze_frames: number;
    total_face_frames: number;
  };
  posture: {
    posture_score: number;
    stable_frames: number;
    leaning_frames: number;
    slouching_frames: number;
    instability_index: number;
  };
  malpractice: {
    malpractice_confidence_score: number;
    repeated_looking_away_events: number;
    excessive_downward_gaze_events: number;
    multiple_face_frames: number;
    summary: string;
  };
  warnings: string[];
};

export type RecordingAnalysisResult = {
  recording_id: string;
  mode: RecordingModeSlug;
  processing_status: "analyzed" | "partial" | string;
  analyzed_at: string;
  audio_processing: AudioProcessingResult;
  transcript: TranscriptResult;
  communication_analysis: CommunicationAnalysisResult;
  video_analysis: VideoBehaviorAnalysisResult;
  dependencies: {
    ffmpeg_available: boolean;
    whisperx_available: boolean;
    grammar_llm_available: boolean;
    cv2_available: boolean;
    mediapipe_available: boolean;
  };
  report_relative_path: string | null;
  warnings: string[];
};

const RECORDING_MIME_CANDIDATES = [
  "video/webm;codecs=vp8,opus",
  "video/webm;codecs=vp9,opus",
  "video/webm",
  "video/mp4"
];

export function pickSupportedRecordingMimeType() {
  if (typeof window === "undefined" || typeof MediaRecorder === "undefined") {
    return "video/webm";
  }

  return (
    RECORDING_MIME_CANDIDATES.find((candidate) => MediaRecorder.isTypeSupported(candidate)) ??
    "video/webm"
  );
}

export function getRecordingExtension(mimeType: string) {
  return mimeType.includes("mp4") ? "mp4" : "webm";
}

export function formatElapsedTime(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60)
    .toString()
    .padStart(2, "0");
  const seconds = (totalSeconds % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}

type UploadRecordingArgs = {
  token: string;
  mode: RecordingModeSlug;
  blob: Blob;
  durationSeconds: number;
  mimeType: string;
  faceDetectionState: FaceDetectionState;
  faceDetectedSamples: number;
  faceMissingSamples: number;
};

export async function uploadRecording(args: UploadRecordingArgs): Promise<RecordingUploadReceipt> {
  const extension = getRecordingExtension(args.mimeType);
  const filename = `${args.mode}-${Date.now()}.${extension}`;
  const formData = new FormData();
  formData.append("mode", args.mode);
  formData.append("duration_seconds", String(args.durationSeconds));
  formData.append("face_detection_state", args.faceDetectionState);
  formData.append("face_detected_samples", String(args.faceDetectedSamples));
  formData.append("face_missing_samples", String(args.faceMissingSamples));
  formData.append("recording", args.blob, filename);

  const response = await fetch(`${API_BASE_URL}/recordings/upload`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${args.token}`
    },
    body: formData
  });

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401) {
      clearClientSessionState();
      throw new Error("Your session expired. Please sign in again.");
    }
    throw new Error(payload?.detail ?? "Unable to upload the recording.");
  }

  return payload as RecordingUploadReceipt;
}

export async function analyzeRecording(
  token: string,
  recordingId: string
): Promise<RecordingAnalysisResult> {
  const response = await fetch(`${API_BASE_URL}/recordings/${recordingId}/analyze`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401) {
      clearClientSessionState();
      throw new Error("Your session expired. Please sign in again.");
    }
    throw new Error(payload?.detail ?? "Unable to analyze the recording.");
  }

  return payload as RecordingAnalysisResult;
}
