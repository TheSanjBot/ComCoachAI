"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Loader2, Mic, PlayCircle, Video } from "lucide-react";

import {
  analyzeResume,
  startInterview,
  startPublicSpeaking,
  submitInterview,
  submitPublicSpeaking
} from "@/lib/api";
import { useRecorder } from "@/hooks/use-recorder";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { InterviewQuestion, ModeId, Report, ResumeAnalysisResult } from "@/types";

const roleOptions = [
  "SDE",
  "Frontend Engineer",
  "Backend Engineer",
  "Cloud Engineer",
  "DevOps Engineer",
  "SRE",
  "Testing Engineer",
  "AI/ML Engineer",
  "Data Analyst"
];

export function RecorderStudio({
  token,
  selectedMode,
  onNewReport
}: {
  token: string | null;
  selectedMode: ModeId;
  onNewReport: (report: Report) => void;
}) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const recorder = useRecorder();
  const [role, setRole] = useState("Backend Engineer");
  const [experienceLevel, setExperienceLevel] = useState("medium");
  const [topic, setTopic] = useState("Present a solution you improved recently.");
  const [transcript, setTranscript] = useState("");
  const [resumeText, setResumeText] = useState("");
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [question, setQuestion] = useState<InterviewQuestion | null>(null);
  const [resumeResult, setResumeResult] = useState<ResumeAnalysisResult | null>(null);
  const [submissionState, setSubmissionState] = useState<"idle" | "working">("idle");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (videoRef.current && recorder.stream) {
      videoRef.current.srcObject = recorder.stream;
      void videoRef.current.play();
    }
  }, [recorder.stream]);

  useEffect(() => {
    setSessionId(null);
    setQuestion(null);
    setTranscript("");
    setResumeResult(null);
    setError(null);
  }, [selectedMode]);

  const canRecord = useMemo(() => selectedMode !== "resume_analysis", [selectedMode]);

  async function handleStartSession() {
    if (!token) {
      setError("Login required before starting a coaching session.");
      return null;
    }

    try {
      setError(null);
      if (selectedMode === "interview") {
        const response = await startInterview(
          {
            mode: "interview",
            role,
            experience_level: experienceLevel
          },
          token
        );
        setSessionId(response.session.id);
        setQuestion(response.question);
        return response.session.id;
      } else if (selectedMode === "public_speaking") {
        const response = await startPublicSpeaking(
          {
            mode: "public_speaking",
            topic
          },
          token
        );
        setSessionId(response.session.id);
        setQuestion({
          question: response.prompt,
          topic: "Presentation",
          difficulty: "custom",
          followups: [],
          context: {}
        });
        return response.session.id;
      }
    } catch (sessionError) {
      setError(
        sessionError instanceof Error
          ? sessionError.message
          : "Unable to start the session."
      );
    }
    return null;
  }

  async function handleSubmit() {
    if (!token) {
      setError("Login required before submitting coaching input.");
      return;
    }

    try {
      setSubmissionState("working");
      setError(null);

      if (selectedMode === "resume_analysis") {
        const result = await analyzeResume(
          { resume_text: resumeText, target_role: role },
          token
        );
        setResumeResult(result);
        return;
      }

      const activeSessionId = sessionId ?? (await handleStartSession());
      if (!activeSessionId) {
        throw new Error("Session could not be initialized.");
      }

      const videoMetrics = {
        direct_gaze_ratio: recorder.faceDetected ? 0.68 : 0.32,
        posture_stability: recorder.faceDetected ? 0.72 : 0.48,
        face_detection_ratio: recorder.faceDetected ? 0.96 : 0.42
      };

      if (selectedMode === "interview") {
        const result = await submitInterview(
          activeSessionId,
          { transcript, video_metrics: videoMetrics },
          token
        );
        onNewReport(result.report);
        setQuestion((current) =>
          current
            ? { ...current, question: result.next_question, followups: [] }
            : current
        );
      } else {
        const result = await submitPublicSpeaking(
          activeSessionId,
          { transcript, video_metrics: videoMetrics },
          token
        );
        onNewReport(result.report);
      }
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Unable to submit the recording."
      );
    } finally {
      setSubmissionState("idle");
    }
  }

  return (
    <Card className="overflow-hidden">
      <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <CardTitle>Hybrid Recording Pipeline</CardTitle>
          <CardDescription className="mt-2">
            Lightweight status during capture, deeper AI analysis only after submit.
          </CardDescription>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge>{selectedMode.replace("_", " ")}</Badge>
          <Badge>Timer {recorder.duration}s</Badge>
          <Badge>{recorder.faceDetected ? "Face detected" : "Face pending"}</Badge>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-4">
          {selectedMode !== "resume_analysis" ? (
            <>
              <div className="overflow-hidden rounded-[28px] border border-border bg-slate-950">
                <video
                  className="aspect-video w-full object-cover"
                  muted
                  playsInline
                  ref={videoRef}
                />
              </div>
              {recorder.previewUrl ? (
                <div className="rounded-[28px] border border-border bg-white p-3">
                  <video className="aspect-video w-full rounded-[20px]" controls src={recorder.previewUrl} />
                </div>
              ) : null}
            </>
          ) : (
            <div className="rounded-[28px] border border-dashed border-primary/25 bg-secondary/30 p-6">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                Resume Intake
              </p>
              <p className="mt-3 text-sm leading-7 text-muted-foreground">
                Paste resume text for role-based gap analysis. The backend keeps this workflow separate from recording but still stores it in the same coaching history model.
              </p>
            </div>
          )}

          <div className="flex flex-wrap gap-3">
            {canRecord ? (
              <>
                <Button
                  disabled={recorder.isRecording}
                  onClick={recorder.startRecording}
                  type="button"
                >
                  <Video className="mr-2 h-4 w-4" />
                  Start Recording
                </Button>
                <Button
                  disabled={!recorder.isRecording}
                  onClick={recorder.stopRecording}
                  type="button"
                  variant="outline"
                >
                  <Mic className="mr-2 h-4 w-4" />
                  Stop Recording
                </Button>
              </>
            ) : null}
            {selectedMode !== "resume_analysis" ? (
              <Button onClick={handleStartSession} type="button" variant="secondary">
                <PlayCircle className="mr-2 h-4 w-4" />
                Initialize Session
              </Button>
            ) : null}
          </div>
        </div>

        <div className="space-y-4">
          <div className="grid gap-3">
            <label className="text-sm font-semibold">Target role</label>
            <select
              className="rounded-2xl border border-border bg-white px-4 py-3 outline-none"
              onChange={(event) => setRole(event.target.value)}
              value={role}
            >
              {roleOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            {selectedMode === "interview" ? (
              <>
                <label className="text-sm font-semibold">Experience level</label>
                <select
                  className="rounded-2xl border border-border bg-white px-4 py-3 outline-none"
                  onChange={(event) => setExperienceLevel(event.target.value)}
                  value={experienceLevel}
                >
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </>
            ) : null}
            {selectedMode === "public_speaking" ? (
              <>
                <label className="text-sm font-semibold">Presentation topic</label>
                <textarea
                  className="min-h-[110px] rounded-2xl border border-border bg-white px-4 py-3 outline-none"
                  onChange={(event) => setTopic(event.target.value)}
                  value={topic}
                />
              </>
            ) : null}
          </div>

          {question ? (
            <div className="rounded-[28px] bg-secondary/45 p-5">
              <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                Current Prompt
              </p>
              <p className="mt-3 text-base font-medium leading-7">{question.question}</p>
            </div>
          ) : null}

          {selectedMode === "resume_analysis" ? (
            <textarea
              className="min-h-[220px] rounded-[28px] border border-border bg-white px-4 py-4 outline-none"
              onChange={(event) => setResumeText(event.target.value)}
              placeholder="Paste resume text here..."
              value={resumeText}
            />
          ) : (
            <textarea
              className="min-h-[220px] rounded-[28px] border border-border bg-white px-4 py-4 outline-none"
              onChange={(event) => setTranscript(event.target.value)}
              placeholder="Paste transcript or answer notes after recording..."
              value={transcript}
            />
          )}

          {resumeResult ? (
            <div className="rounded-[28px] bg-white p-5">
              <p className="text-sm font-semibold">
                Matching score: {Math.round(resumeResult.matching_score)}
              </p>
              <p className="mt-3 text-sm text-muted-foreground">
                Missing skills: {resumeResult.missing_skills.join(", ") || "None"}
              </p>
            </div>
          ) : null}

          {error ? <p className="text-sm text-red-600">{error}</p> : null}
          {recorder.error ? <p className="text-sm text-red-600">{recorder.error}</p> : null}

          <Button
            className="w-full"
            disabled={submissionState === "working"}
            onClick={handleSubmit}
            type="button"
          >
            {submissionState === "working" ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating report
              </>
            ) : (
              "Submit for AI Analysis"
            )}
          </Button>
        </div>
      </div>
    </Card>
  );
}
