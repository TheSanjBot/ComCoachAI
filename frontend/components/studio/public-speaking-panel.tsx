"use client";

import { useState } from "react";
import { Mic2, RotateCcw, Sparkles, Video } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { PublicSpeakingController } from "@/hooks/use-public-speaking";
import type { RecordingAnalysisResult, RecordingUploadReceipt } from "@/lib/recording";

export function PublicSpeakingPanel({
  speaking,
  savedRecording,
  analysisResult
}: {
  speaking: PublicSpeakingController;
  savedRecording: RecordingUploadReceipt | null;
  analysisResult: RecordingAnalysisResult | null;
}) {
  return (
    <section className="grid gap-5">
      {!speaking.session ? (
        <Card className="panel-surface">
          <CardHeader>
            <CardTitle>Public-speaking setup</CardTitle>
            <CardDescription>
              Set your rehearsal topic once, then the screen switches to record-and-review mode.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <PublicSpeakingForm
              onStart={(topic, audience) => void speaking.startSession({ topic, audience })}
              isStarting={speaking.isStarting}
            />

            {speaking.error ? (
                <div className="rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                  {speaking.error}
                </div>
            ) : null}
          </CardContent>
        </Card>
      ) : null}

      <Card className="panel-surface">
        <CardHeader>
          <CardTitle>Speaking flow</CardTitle>
          <CardDescription>
            Start the topic once, record a take, and use the main submit button below to generate the full coaching review automatically.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-3">
            <MiniMetric
              label="Topic session"
              value={speaking.session ? "Ready" : "Missing"}
              icon={Mic2}
            />
            <MiniMetric
              label="Last take"
              value={savedRecording && analysisResult ? "Coached" : "Waiting"}
              icon={Video}
            />
            <MiniMetric
              label="Review status"
              value={speaking.coachingResult ? "Insights ready" : "Not generated"}
              icon={Sparkles}
            />
          </div>

          {speaking.session ? (
            <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
              <p className="font-mono text-sm font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Rehearsal topic
              </p>
              <p className="mt-3 text-lg font-semibold text-foreground">{speaking.session.topic}</p>
              <p className="mt-2 text-sm leading-7 text-muted-foreground">
                Audience: {speaking.session.audience ?? "General audience"}
              </p>
            </div>
          ) : null}

          {speaking.coachingResult ? (
            <div className="rounded-[1.5rem] border border-primary/25 bg-primary/10 p-5 text-sm leading-7 text-foreground/85 shadow-orange-glow">
              {speaking.coachingResult.summary}
            </div>
          ) : null}

          {speaking.error ? (
            <div className="rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {speaking.error}
            </div>
          ) : null}

          {speaking.session ? (
            <div className="flex flex-wrap gap-3">
              <Button variant="outline" onClick={speaking.resetPublicSpeaking} className="gap-2">
                <RotateCcw className="h-4 w-4" />
                Start a new speaking session
              </Button>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </section>
  );
}

function PublicSpeakingForm({
  onStart,
  isStarting
}: {
  onStart: (topic: string, audience?: string) => void;
  isStarting: boolean;
}) {
  return <PublicSpeakingFormInner onStart={onStart} isStarting={isStarting} />;
}

function PublicSpeakingFormInner({
  onStart,
  isStarting
}: {
  onStart: (topic: string, audience?: string) => void;
  isStarting: boolean;
}) {
  const [topic, setTopic] = useState("");
  const [audience, setAudience] = useState("");
  const topicId = "public-speaking-topic";
  const audienceId = "public-speaking-audience";

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault();
        const nextTopic = topic.trim();
        const nextAudience = audience.trim();
        if (nextTopic) {
          onStart(nextTopic, nextAudience || undefined);
        }
      }}
    >
      <div className="space-y-2">
        <Label htmlFor={topicId}>Topic</Label>
        <Input
          id={topicId}
          name="topic"
          value={topic}
          onChange={(event) => setTopic(event.target.value)}
          placeholder="Explain your product demo, keynote, or interview presentation topic."
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor={audienceId}>Audience (optional)</Label>
        <Input
          id={audienceId}
          name="audience"
          value={audience}
          onChange={(event) => setAudience(event.target.value)}
          placeholder="Hiring manager, product team, customer demo audience..."
        />
      </div>
      <div className="flex flex-wrap gap-3">
        <Button type="submit" disabled={isStarting} className="gap-2">
          <Mic2 className="h-4 w-4" />
          {isStarting ? "Starting rehearsal..." : "Start public-speaking session"}
        </Button>
      </div>
    </form>
  );
}

function MiniMetric({
  label,
  value,
  icon: Icon
}: {
  label: string;
  value: string;
  icon: typeof Sparkles;
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
