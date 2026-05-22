import { apiRequest } from "@/lib/api";

export type ExperienceLevel = "entry-level" | "mid-level" | "senior";

export type InterviewQuestionPrompt = {
  question_id: string;
  role: string;
  topic: string;
  difficulty: string;
  question: string;
  followups: string[];
  expected_concepts: string[];
  source: string;
};

export type InterviewSession = {
  session_id: string;
  role: string;
  experience_level: ExperienceLevel;
  target_question_count: number;
  answered_question_count: number;
  status: "active" | "completed";
  created_at: string;
  updated_at: string;
  current_question: InterviewQuestionPrompt | null;
  supported_roles: string[];
  resume_filename: string | null;
  resume_notes: string | null;
};

export type TechnicalEvaluationResult = {
  technical_score: number;
  correctness_score: number;
  explanation_depth_score: number;
  technical_clarity_score: number;
  strengths: string[];
  weaknesses: string[];
  missing_concepts: string[];
  evidence_found: string[];
  suggested_followup_topics: string[];
  summary: string;
  strategy: string;
  warnings: string[];
};

export type InterviewFinalReport = {
  session_id: string;
  role: string;
  experience_level: ExperienceLevel;
  completed_at: string;
  question_count: number;
  average_technical_score: number;
  average_communication_score: number;
  average_words_per_minute: number;
  average_filler_words: number;
  average_posture_score: number;
  average_eye_contact_score: number;
  average_malpractice_score: number;
  strongest_topics: string[];
  weakest_topics: string[];
  recurring_missing_concepts: string[];
  strengths: string[];
  weaknesses: string[];
  final_coaching_summary: string;
  personalized_coaching: string[];
  learning_roadmap: {
    skill: string;
    next_step: string;
    resource_title: string | null;
    resource_url: string | null;
  }[];
  recommendations: {
    topic: string;
    title: string;
    platform: string;
    price: string;
    url: string;
  }[];
  report_id: string | null;
};

export type InterviewTurnResult = {
  session: InterviewSession;
  question: InterviewQuestionPrompt;
  technical_evaluation: TechnicalEvaluationResult;
  communication_score: number;
  coaching_feedback: string[];
  next_question: InterviewQuestionPrompt | null;
  final_report: InterviewFinalReport | null;
};

export type PublicSpeakingSession = {
  session_id: string;
  topic: string;
  audience: string | null;
  created_at: string;
  updated_at: string;
  status: string;
};

export type PublicSpeakingCoachingResult = {
  session: PublicSpeakingSession;
  recording_id: string;
  confidence_score: number;
  communication_score: number;
  factual_accuracy_score: number;
  words_per_minute: number;
  filler_word_total: number;
  posture_score: number;
  eye_contact_score: number;
  malpractice_score: number;
  pacing_suggestions: string[];
  posture_coaching: string[];
  eye_contact_coaching: string[];
  communication_advice: string[];
  storytelling_feedback: string[];
  factual_highlights: string[];
  factual_corrections: string[];
  strengths: string[];
  weaknesses: string[];
  summary: string;
  factual_accuracy_summary: string;
  personalized_coaching: string[];
  learning_roadmap: {
    skill: string;
    next_step: string;
    resource_title: string | null;
    resource_url: string | null;
  }[];
  recommendations: {
    topic: string;
    title: string;
    platform: string;
    price: string;
    url: string;
  }[];
  report_id: string | null;
};

type CreateInterviewSessionArgs = {
  token: string;
  role: string;
  experienceLevel: ExperienceLevel;
  targetQuestionCount: number;
  resumeFilename?: string;
  resumeNotes?: string;
};

export async function createInterviewSession(
  args: CreateInterviewSessionArgs
): Promise<InterviewSession> {
  return apiRequest<InterviewSession>("/interview/sessions", {
    method: "POST",
    token: args.token,
    body: JSON.stringify({
      role: args.role,
      experience_level: args.experienceLevel,
      target_question_count: args.targetQuestionCount,
      resume_filename: args.resumeFilename ?? null,
      resume_notes: args.resumeNotes ?? null
    })
  });
}

export async function submitInterviewAnswer(
  token: string,
  sessionId: string,
  recordingId: string
): Promise<InterviewTurnResult> {
  return apiRequest<InterviewTurnResult>(`/interview/sessions/${sessionId}/submit`, {
    method: "POST",
    token,
    body: JSON.stringify({ recording_id: recordingId })
  });
}

type CreatePublicSpeakingSessionArgs = {
  token: string;
  topic: string;
  audience?: string;
};

export async function createPublicSpeakingSession(
  args: CreatePublicSpeakingSessionArgs
): Promise<PublicSpeakingSession> {
  return apiRequest<PublicSpeakingSession>("/public-speaking/sessions", {
    method: "POST",
    token: args.token,
    body: JSON.stringify({
      topic: args.topic,
      audience: args.audience ?? null
    })
  });
}

export async function coachPublicSpeakingRecording(
  token: string,
  sessionId: string,
  recordingId: string
): Promise<PublicSpeakingCoachingResult> {
  return apiRequest<PublicSpeakingCoachingResult>(`/public-speaking/sessions/${sessionId}/coach`, {
    method: "POST",
    token,
    body: JSON.stringify({ recording_id: recordingId })
  });
}
