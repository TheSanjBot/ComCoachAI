export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
const SESSION_STORAGE_KEY = "commcoach.session";
const AUTH_EVENT_NAME = "commcoach:auth-state-changed";

type ApiRequestOptions = RequestInit & {
  token?: string;
};

export function clearClientSessionState() {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(SESSION_STORAGE_KEY);
  window.dispatchEvent(new Event(AUTH_EVENT_NAME));
}

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {}
): Promise<T> {
  const { token, headers, ...rest } = options;
  const requestHeaders =
    rest.body instanceof FormData
      ? {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...headers
        }
      : {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...headers
        };

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: requestHeaders,
    cache: "no-store"
  });

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    if (response.status === 401) {
      clearClientSessionState();
      throw new Error("Your session expired. Please sign in again.");
    }
    throw new Error(payload?.detail ?? "Something went wrong while contacting the API.");
  }

  return payload as T;
}

// Legacy compatibility wrappers for older prototype components that still compile in the repo.

export async function login(payload: { email: string; password: string }): Promise<any> {
  return apiRequest<any>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function signup(payload: {
  email: string;
  password: string;
  full_name?: string;
  fullName?: string;
}): Promise<any> {
  return apiRequest<any>("/auth/signup", {
    method: "POST",
    body: JSON.stringify({
      email: payload.email,
      password: payload.password,
      full_name: payload.full_name ?? payload.fullName ?? ""
    })
  });
}

export async function fetchProfile(token: string): Promise<any> {
  return apiRequest<any>("/auth/me", {
    method: "GET",
    token
  });
}

export async function fetchModes(): Promise<
  Array<{
    id: "interview" | "public_speaking" | "resume_analysis";
    title: string;
    description: string;
  }>
> {
  return [
    {
      id: "interview",
      title: "Interview Training Mode",
      description: "Structured mock interviews with staged analysis."
    },
    {
      id: "public_speaking",
      title: "Public Speaking Training Mode",
      description: "Delivery coaching for pacing, posture, and confidence."
    },
    {
      id: "resume_analysis",
      title: "Resume + Skill Gap Analysis Mode",
      description: "Resume parsing, skill-gap analysis, and learning roadmaps."
    }
  ];
}

export async function fetchDashboardSummary(token: string): Promise<any> {
  const overview = await apiRequest<any>("/dashboard/overview", {
    method: "GET",
    token
  });
  return {
    total_sessions: overview.total_sessions,
    average_scores: {
      communication: overview.score_summaries?.[1]?.score ?? 0,
      technical: overview.score_summaries?.[2]?.score ?? 0,
      confidence: overview.score_summaries?.[0]?.score ?? 0,
      overall: Math.round(
        ((overview.score_summaries?.[0]?.score ?? 0) +
          (overview.score_summaries?.[1]?.score ?? 0) +
          (overview.score_summaries?.[2]?.score ?? 0)) / 3
      )
    },
    confidence_trend: (overview.confidence_trend ?? []).map((item: any, index: number) => ({
      sessionId: index + 1,
      confidence: item.confidence_score,
      communication: item.communication_score,
      overall: Math.round((item.confidence_score + item.communication_score) / 2),
      mode: "interview"
    })),
    recent_reports: []
  };
}

export async function analyzeResume(
  payload: { resume_text: string; target_role: string },
  token: string
): Promise<any> {
  return apiRequest<any>("/resume-analysis/text", {
    method: "POST",
    token,
    body: JSON.stringify(payload)
  });
}

export async function startInterview(..._args: any[]): Promise<any> {
  throw new Error("Legacy recorder studio is no longer supported in the current frontend flow.");
}

export async function startPublicSpeaking(..._args: any[]): Promise<any> {
  throw new Error("Legacy recorder studio is no longer supported in the current frontend flow.");
}

export async function submitInterview(..._args: any[]): Promise<any> {
  throw new Error("Legacy recorder studio is no longer supported in the current frontend flow.");
}

export async function submitPublicSpeaking(..._args: any[]): Promise<any> {
  throw new Error("Legacy recorder studio is no longer supported in the current frontend flow.");
}
