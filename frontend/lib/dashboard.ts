import { apiRequest } from "@/lib/api";

export type ModeCard = {
  slug: string;
  title: string;
  description: string;
  status: string;
  estimated_duration_minutes: number;
  primary_focus: string;
  next_milestone: string;
};

export type ScoreSummary = {
  label: string;
  score: number;
  delta: number;
  note: string;
};

export type ConfidenceTrendPoint = {
  label: string;
  confidence_score: number;
  communication_score: number;
};

export type ModePerformancePoint = {
  mode: string;
  average_overall_score: number;
  average_confidence_score: number;
};

export type FeaturedRecommendation = {
  topic: string;
  title: string;
  platform: string;
  url: string;
  source_mode: string;
};

export type RecentReport = {
  id: string;
  title: string;
  mode: string;
  completed_at: string;
  communication_score: number;
  confidence_score: number;
  summary: string;
};

export type InterviewHistoryItem = {
  id: string;
  role: string;
  level: string;
  completed_at: string;
  technical_score: number;
  communication_score: number;
  trend: string;
};

export type DashboardOverview = {
  welcome_name: string;
  streak_days: number;
  total_sessions: number;
  average_confidence_score: number;
  focus_area: string;
  recommended_mode_slug: string;
  mode_cards: ModeCard[];
  priority_actions: string[];
  score_summaries: ScoreSummary[];
  confidence_trend: ConfidenceTrendPoint[];
  mode_performance: ModePerformancePoint[];
  featured_recommendations: FeaturedRecommendation[];
  recent_reports: RecentReport[];
  interview_history: InterviewHistoryItem[];
};

export async function fetchDashboardOverview(token: string): Promise<DashboardOverview> {
  return apiRequest<DashboardOverview>("/dashboard/overview", {
    method: "GET",
    token
  });
}
