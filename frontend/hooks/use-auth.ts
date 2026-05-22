"use client";

import { useEffect, useState } from "react";

import { fetchProfile } from "@/lib/api";
import { clearSession, getAuthEventName, getStoredSession, type AuthSession } from "@/lib/auth";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

export function useAuth() {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  useEffect(() => {
    let isActive = true;

    async function syncSession() {
      const existingSession = getStoredSession();
      if (!existingSession) {
        if (isActive) {
          setSession(null);
          setStatus("unauthenticated");
        }
        return;
      }

      try {
        await fetchProfile(existingSession.access_token);
        if (isActive) {
          setSession(existingSession);
          setStatus("authenticated");
        }
      } catch {
        clearSession();
        if (isActive) {
          setSession(null);
          setStatus("unauthenticated");
        }
      }
    }

    void syncSession();

    const handleAuthChange = () => {
      void syncSession();
    };

    const handleStorage = (event: StorageEvent) => {
      if (event.key === "commcoach.session") {
        void syncSession();
      }
    };

    window.addEventListener(getAuthEventName(), handleAuthChange);
    window.addEventListener("storage", handleStorage);

    return () => {
      isActive = false;
      window.removeEventListener(getAuthEventName(), handleAuthChange);
      window.removeEventListener("storage", handleStorage);
    };
  }, []);

  function signOut() {
    clearSession();
    setSession(null);
    setStatus("unauthenticated");
  }

  return {
    session,
    status,
    setSession,
    setStatus,
    signOut
  };
}
