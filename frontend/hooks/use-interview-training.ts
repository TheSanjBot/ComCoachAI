"use client";

import { useState } from "react";

import {
  createInterviewSession,
  submitInterviewAnswer,
  type ExperienceLevel,
  type InterviewFinalReport,
  type InterviewSession,
  type InterviewTurnResult
} from "@/lib/coaching";

type StartInterviewArgs = {
  role: string;
  experienceLevel: ExperienceLevel;
  targetQuestionCount: number;
  resumeFilename?: string;
  resumeNotes?: string;
};

export function useInterviewTraining(token: string) {
  const [session, setSession] = useState<InterviewSession | null>(null);
  const [latestTurn, setLatestTurn] = useState<InterviewTurnResult | null>(null);
  const [finalReport, setFinalReport] = useState<InterviewFinalReport | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function startSession(args: StartInterviewArgs) {
    setIsStarting(true);
    setError(null);
    try {
      const nextSession = await createInterviewSession({
        token,
        role: args.role,
        experienceLevel: args.experienceLevel,
        targetQuestionCount: args.targetQuestionCount,
        resumeFilename: args.resumeFilename,
        resumeNotes: args.resumeNotes
      });
      setSession(nextSession);
      setLatestTurn(null);
      setFinalReport(null);
      return nextSession;
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Unable to start the interview session.");
      return null;
    } finally {
      setIsStarting(false);
    }
  }

  async function evaluateAnswer(recordingId: string) {
    if (!session) {
      setError("Start an interview session before evaluating an answer.");
      return null;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      const turn = await submitInterviewAnswer(token, session.session_id, recordingId);
      setLatestTurn(turn);
      setSession(turn.session);
      setFinalReport(turn.final_report ?? null);
      return turn;
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Unable to evaluate this interview answer.");
      return null;
    } finally {
      setIsSubmitting(false);
    }
  }

  function resetInterview() {
    setSession(null);
    setLatestTurn(null);
    setFinalReport(null);
    setError(null);
  }

  return {
    session,
    latestTurn,
    finalReport,
    isStarting,
    isSubmitting,
    error,
    startSession,
    evaluateAnswer,
    resetInterview
  };
}

export type InterviewTrainingController = ReturnType<typeof useInterviewTraining>;
