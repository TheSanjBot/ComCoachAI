export type ModeId = "interview" | "public_speaking" | "resume_analysis";

export interface ModeDefinition {
  id: ModeId;
  title: string;
  description: string;
}

export interface SessionCreatePayload {
  mode: ModeId;
  role?: string;
  experience_level?: string;
  topic?: string;
  prompt_context?: Record<string, unknown>;
}

export interface SubmissionPayload {
  transcript?: string;
  transcript_segments?: Array<Record<string, unknown>>;
  video_metrics?: Record<string, unknown>;
  resume_text?: string;
  target_role?: string;
}

export interface Report {
  report_id: number;
  session_id: number;
  mode: ModeId;
  status: "draft" | "processing" | "completed";
  summary: string;
  communication_score: number;
  technical_score: number | null;
  confidence_score: number;
  posture_score: number;
  eye_contact_score: number;
  malpractice_score: number;
  overall_score: number;
  strengths: string[];
  weaknesses: string[];
  coaching_tips: string[];
  learning_roadmap: Array<Record<string, unknown>>;
  analytics: Record<string, unknown>;
  created_at: string;
}

export interface DashboardSummary {
  total_sessions: number;
  average_scores: {
    communication: number;
    technical: number;
    confidence: number;
    overall: number;
  };
  confidence_trend: Array<{
    sessionId: number;
    confidence: number;
    communication: number;
    overall: number;
    mode: ModeId;
  }>;
  recent_reports: Report[];
}

export interface InterviewQuestion {
  question: string;
  topic: string;
  difficulty: string;
  followups: string[];
  context: Record<string, unknown>;
}

export interface InterviewStartResponse {
  session: {
    id: number;
    mode: ModeId;
    status: string;
    role?: string;
    experience_level?: string;
    topic?: string;
    transcript?: string | null;
  };
  question: InterviewQuestion;
}

export interface ResumeAnalysisResult {
  matching_score: number;
  detected_skills: string[];
  missing_skills: string[];
  learning_roadmap: Array<{ skill: string; next_step: string }>;
}

