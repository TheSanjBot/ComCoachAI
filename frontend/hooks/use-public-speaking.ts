"use client";

import { useState } from "react";

import {
  coachPublicSpeakingRecording,
  createPublicSpeakingSession,
  type PublicSpeakingCoachingResult,
  type PublicSpeakingSession
} from "@/lib/coaching";

type StartPublicSpeakingArgs = {
  topic: string;
  audience?: string;
};

export function usePublicSpeaking(token: string) {
  const [session, setSession] = useState<PublicSpeakingSession | null>(null);
  const [coachingResult, setCoachingResult] = useState<PublicSpeakingCoachingResult | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [isCoaching, setIsCoaching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function startSession(args: StartPublicSpeakingArgs) {
    setIsStarting(true);
    setError(null);
    try {
      const nextSession = await createPublicSpeakingSession({
        token,
        topic: args.topic,
        audience: args.audience
      });
      setSession(nextSession);
      setCoachingResult(null);
      return nextSession;
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Unable to start the public-speaking rehearsal.");
      return null;
    } finally {
      setIsStarting(false);
    }
  }

  async function coachRecording(recordingId: string) {
    if (!session) {
      setError("Start a public-speaking session before requesting coaching.");
      return null;
    }

    setIsCoaching(true);
    setError(null);
    try {
      const result = await coachPublicSpeakingRecording(token, session.session_id, recordingId);
      setSession(result.session);
      setCoachingResult(result);
      return result;
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Unable to generate the public-speaking coaching report.");
      return null;
    } finally {
      setIsCoaching(false);
    }
  }

  function resetPublicSpeaking() {
    setSession(null);
    setCoachingResult(null);
    setError(null);
  }

  return {
    session,
    coachingResult,
    isStarting,
    isCoaching,
    error,
    startSession,
    coachRecording,
    resetPublicSpeaking
  };
}

export type PublicSpeakingController = ReturnType<typeof usePublicSpeaking>;
