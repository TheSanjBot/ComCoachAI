import { apiRequest } from "@/lib/api";

export type ResourceRecommendation = {
  topic: string;
  title: string;
  platform: string;
  price: string;
  url: string;
};

export type LearningRoadmapItem = {
  skill: string;
  next_step: string;
  resource_title: string | null;
  resource_url: string | null;
};

export type ResumeAnalysisResponse = {
  target_role: string;
  matching_score: number;
  ats_readiness_score: number;
  role_fit_summary: string;
  detected_skills: string[];
  missing_skills: string[];
  priority_gaps: string[];
  evidence_highlights: string[];
  extracted_text_preview: string;
  learning_roadmap: LearningRoadmapItem[];
  recommendations: ResourceRecommendation[];
  personalized_coaching: string[];
  report_id: string | null;
  artifact_relative_path: string | null;
};

export async function analyzeResumeText(
  token: string,
  payload: { resume_text: string; target_role: string }
) {
  return apiRequest<ResumeAnalysisResponse>("/resume-analysis/text", {
    method: "POST",
    token,
    body: JSON.stringify(payload)
  });
}

export async function analyzeResumeUpload(
  token: string,
  payload: { file: File; targetRole: string }
) {
  const formData = new FormData();
  formData.append("resume", payload.file);
  formData.append("target_role", payload.targetRole);

  return apiRequest<ResumeAnalysisResponse>("/resume-analysis/upload", {
    method: "POST",
    token,
    body: formData
  });
}
