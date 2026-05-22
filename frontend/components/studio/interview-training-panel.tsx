"use client";

import type { ReactNode } from "react";
import { useState } from "react";
import { BriefcaseBusiness, BrainCircuit, ListChecks, RotateCcw, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { InterviewTrainingController } from "@/hooks/use-interview-training";
import type { RecordingAnalysisResult, RecordingUploadReceipt } from "@/lib/recording";

const roles = [
  "SDE",
  "Frontend Engineer",
  "Backend Engineer",
  "Cloud Engineer",
  "DevOps Engineer",
  "SRE",
  "Testing Engineer",
  "AI/ML Engineer",
  "Data Analyst"
] as const;

export function InterviewTrainingPanel({
  interview,
  savedRecording,
  analysisResult
}: {
  interview: InterviewTrainingController;
  savedRecording: RecordingUploadReceipt | null;
  analysisResult: RecordingAnalysisResult | null;
}) {
  const [role, setRole] = useState<(typeof roles)[number]>("Backend Engineer");
  const [experienceLevel, setExperienceLevel] = useState<"entry-level" | "mid-level" | "senior">(
    "mid-level"
  );
  const [targetQuestionCount, setTargetQuestionCount] = useState(3);
  const [resumeNotes, setResumeNotes] = useState("");

  return (
    <section className="grid gap-5">
      {!interview.session ? (
        <Card className="panel-surface">
          <CardHeader>
            <CardTitle>Interview session setup</CardTitle>
            <CardDescription>
              Choose your interview target once, then the screen will switch to question-and-answer mode.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="grid gap-4">
              <Field label="Role">
                <select
                  value={role}
                  onChange={(event) => setRole(event.target.value as (typeof roles)[number])}
                  className="flex h-11 w-full rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-foreground outline-none transition-all duration-200 focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/30"
                >
                  {roles.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </Field>

              <Field label="Experience level">
                <select
                  value={experienceLevel}
                  onChange={(event) =>
                    setExperienceLevel(event.target.value as "entry-level" | "mid-level" | "senior")
                  }
                  className="flex h-11 w-full rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-foreground outline-none transition-all duration-200 focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/30"
                >
                  <option value="entry-level">Entry-level</option>
                  <option value="mid-level">Mid-level</option>
                  <option value="senior">Senior</option>
                </select>
              </Field>

              <Field label="Target question count">
                <Input
                  type="number"
                  min={1}
                  max={5}
                  value={targetQuestionCount}
                  onChange={(event) => setTargetQuestionCount(Number(event.target.value) || 1)}
                />
              </Field>

              <Field label="Resume notes (optional)">
                <textarea
                  value={resumeNotes}
                  onChange={(event) => setResumeNotes(event.target.value)}
                  rows={4}
                  placeholder="Paste a few role-relevant strengths or gaps from the resume here."
                  className="w-full rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-foreground outline-none transition-all duration-200 placeholder:text-white/30 focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/30"
                />
              </Field>
            </div>

            <Button
              onClick={() =>
                void interview.startSession({
                  role,
                  experienceLevel,
                  targetQuestionCount,
                  resumeNotes: resumeNotes || undefined
                })
              }
              disabled={interview.isStarting}
              className="gap-2"
            >
              <BriefcaseBusiness className="h-4 w-4" />
              {interview.isStarting ? "Starting interview..." : "Start interview session"}
            </Button>

            {interview.error ? (
                <div className="rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                {interview.error}
              </div>
            ) : null}
          </CardContent>
        </Card>
      ) : null}

      <Card className="panel-surface">
        <CardHeader>
          <CardTitle>Interview flow</CardTitle>
          <CardDescription>
            Answer the current question, then use the main submit button below to run communication, video, and technical evaluation together.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          {interview.session?.current_question ? (
            <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
              <div className="flex flex-wrap items-center gap-2 font-mono text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                <span>{interview.session.role}</span>
                <span>/</span>
                <span>{interview.session.current_question.topic}</span>
                <span>/</span>
                <span>{interview.session.current_question.difficulty}</span>
              </div>
              <p className="mt-3 text-lg font-semibold leading-8 text-foreground">
                {interview.session.current_question.question}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {interview.session.current_question.expected_concepts.map((concept, index) => (
                  <span
                    key={`${concept}-${index}`}
                    className="inline-flex rounded-full border border-primary/20 bg-primary/10 px-3 py-2 font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-primary"
                  >
                    {concept}
                  </span>
                ))}
              </div>
            </div>
          ) : (
            <div className="rounded-[1.5rem] border border-dashed border-white/10 bg-white/[0.03] px-4 py-6 text-sm leading-7 text-muted-foreground">
              Start an interview session to generate the first role-based question.
            </div>
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            <MiniMetric
              label="Answered"
              value={
                interview.session
                  ? `${interview.session.answered_question_count}/${interview.session.target_question_count}`
                  : "0/0"
              }
              icon={ListChecks}
            />
            <MiniMetric
              label="Review status"
              value={interview.latestTurn ? "Insights ready" : savedRecording && analysisResult ? "Processing" : "Waiting"}
              icon={Sparkles}
            />
          </div>

          {interview.latestTurn ? (
            <div className="space-y-4">
              <div className="rounded-[1.5rem] border border-primary/25 bg-primary/10 p-5 text-sm leading-7 text-foreground/85 shadow-orange-glow">
                {interview.latestTurn.technical_evaluation.summary}
              </div>

              {interview.latestTurn.next_question ? (
                <div className="rounded-[1.5rem] border border-primary/20 bg-white/[0.03] p-5">
                  <p className="text-sm font-semibold text-foreground">Next interview question</p>
                  <p className="mt-3 text-base leading-7 text-foreground/90">
                    {interview.latestTurn.next_question.question}
                  </p>
                </div>
              ) : null}
            </div>
          ) : null}

          {interview.finalReport ? (
            <div className="space-y-4 rounded-[1.5rem] border border-gold/20 bg-gold/10 p-5 shadow-gold-glow">
              <p className="text-lg font-semibold text-foreground">Final interview report</p>
              <div className="grid gap-4 sm:grid-cols-2">
                <MiniMetric
                  label="Avg technical"
                  value={`${interview.finalReport.average_technical_score}/100`}
                  icon={BrainCircuit}
                />
                <MiniMetric
                  label="Avg communication"
                  value={`${interview.finalReport.average_communication_score}/100`}
                  icon={Sparkles}
                />
              </div>
              <InfoBlock
                title="Strongest topics"
                items={interview.finalReport.strongest_topics}
                emptyLabel="No strongest topics yet."
              />
              <InfoBlock
                title="Recurring missing concepts"
                items={interview.finalReport.recurring_missing_concepts}
                emptyLabel="No recurring concept gaps were detected."
              />
              <p className="text-sm leading-7 text-foreground/85">
                {interview.finalReport.final_coaching_summary}
              </p>
            </div>
          ) : null}

          {interview.error ? (
            <div className="rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {interview.error}
            </div>
          ) : null}

          {interview.session ? (
            <div className="flex flex-wrap gap-3">
              <Button variant="outline" onClick={interview.resetInterview} className="gap-2">
                <RotateCcw className="h-4 w-4" />
                Start a new interview
              </Button>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </section>
  );
}

function Field({
  label,
  children
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
    </div>
  );
}

function MiniMetric({
  label,
  value,
  icon: Icon
}: {
  label: string;
  value: string;
  icon: typeof BrainCircuit;
}) {
  return (
    <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-4">
      <div className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-primary/25 bg-primary/12 text-primary shadow-orange-glow">
        <Icon className="h-4 w-4" />
      </div>
      <p className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">{label}</p>
      <p className="mt-2 text-base font-semibold text-foreground">{value}</p>
    </div>
  );
}

function InfoBlock({
  title,
  items,
  emptyLabel
}: {
  title: string;
  items: string[];
  emptyLabel: string;
}) {
  return (
    <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-4">
      <p className="text-sm font-semibold text-foreground">{title}</p>
      <div className="mt-3 space-y-2">
        {items.length ? (
          items.map((item, index) => (
            <div
              key={`${title}-${index}-${item}`}
              className="rounded-2xl border border-white/10 bg-white/[0.04] px-3 py-2 text-sm leading-6 text-foreground/85"
            >
              {item}
            </div>
          ))
        ) : (
          <p className="text-sm text-muted-foreground">{emptyLabel}</p>
        )}
      </div>
    </div>
  );
}
