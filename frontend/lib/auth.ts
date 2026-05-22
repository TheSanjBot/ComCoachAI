import { apiRequest } from "@/lib/api";

const STORAGE_KEY = "commcoach.session";
const AUTH_EVENT_NAME = "commcoach:auth-state-changed";

export type AuthUser = {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
};

export type AuthSession = {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export type SignupPayload = {
  fullName: string;
  email: string;
  password: string;
};

export async function login(payload: LoginPayload): Promise<AuthSession> {
  return apiRequest<AuthSession>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function signup(payload: SignupPayload): Promise<AuthSession> {
  return apiRequest<AuthSession>("/auth/signup", {
    method: "POST",
    body: JSON.stringify({
      email: payload.email,
      full_name: payload.fullName,
      password: payload.password
    })
  });
}

export function saveSession(session: AuthSession) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  window.dispatchEvent(new Event(AUTH_EVENT_NAME));
}

export function getStoredSession(): AuthSession | null {
  if (typeof window === "undefined") {
    return null;
  }

  const rawSession = window.localStorage.getItem(STORAGE_KEY);
  if (!rawSession) {
    return null;
  }

  try {
    return JSON.parse(rawSession) as AuthSession;
  } catch {
    window.localStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

export function clearSession() {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(STORAGE_KEY);
  window.dispatchEvent(new Event(AUTH_EVENT_NAME));
}

export function getAuthEventName() {
  return AUTH_EVENT_NAME;
}
