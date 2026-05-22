"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { Camera, CircleDot, FileAudio2, House, Mic, RotateCcw, Save, ScanFace, Sparkles, Square, UploadCloud, Video } from "lucide-react";

import { useRecordingStudio } from "@/hooks/use-recording-studio";
import { useInterviewTraining } from "@/hooks/use-interview-training";
import { usePublicSpeaking } from "@/hooks/use-public-speaking";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getModeConfig, type RecordingModeSlug } from "@/lib/mode-config";
import { cn } from "@/lib/utils";
import { InterviewTrainingPanel } from "@/components/studio/interview-training-panel";
import { PublicSpeakingPanel } from "@/components/studio/public-speaking-panel";

type RecordingStudioProps = {
  mode: RecordingModeSlug;
  token: string;
};

const faceStateLabels = {
  waiting: "Waiting for camera",
  checking: "Checking frame",
  detected: "Face detected",
  "not-detected": "Face not detected",
  unsupported: "Detector unavailable"
} as const;

export function RecordingStudio({ mode, token }: RecordingStudioProps) {
  const config = getModeConfig(mode);
  const studio = useRecordingStudio({ mode, token });
  const interview = useInterviewTraining(token);
  const speaking = usePublicSpeaking(token);
  const hasReview = Boolean(studio.analysisResult || interview.latestTurn || speaking.coachingResult);

  const isModeSpecificSubmitBusy =
    (mode === "interview-training" && interview.isSubmitting) ||
    (mode === "public-speaking" && speaking.isCoaching);

  async function handleSubmit() {
    const outcome = await studio.submitRecordingForAnalysis();
    if (!outcome) {
      return;
    }

    if (mode === "interview-training" && interview.session?.status === "active") {
      await interview.evaluateAnswer(outcome.recording.recording_id);
      return;
    }

    if (mode === "public-speaking" && speaking.session) {
      await speaking.coachRecording(outcome.recording.recording_id);
    }
  }

  function getSubmitLabel() {
    if (mode === "interview-training" && interview.session?.status === "active") {
      return "Submit answer and continue";
    }
    if (mode === "public-speaking" && speaking.session) {
      return "Submit rehearsal and get coaching";
    }
    return "Submit recording for analysis";
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(227,197,165,0.38),_transparent_24%),radial-gradient(circle_at_bottom_right,_rgba(116,160,153,0.22),_transparent_30%),linear-gradient(145deg,_#f7f1e8_0%,_#edf3f2_46%,_#dde9e4_100%)] px-6 py-8">
      <div className="mx-auto max-w-7xl space-y-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-2">
            <h1 className="text-4xl font-semibold leading-tight">{config.studioTitle}</h1>
            <p className="max-w-3xl text-sm leading-7 text-muted-foreground sm:text-base">
              {config.studioDescription}
            </p>
          </div>

          <Link href="/" className={cn(buttonVariants({ variant: "outline" }), "gap-2 self-start")}>
            <House className="h-4 w-4" />
            Back to home
          </Link>
        </div>

        {mode === "interview-training" ? (
          <InterviewTrainingPanel
            interview={interview}
            savedRecording={studio.savedRecording}
            analysisResult={studio.analysisResult}
          />
        ) : null}

        {mode === "public-speaking" ? (
          <PublicSpeakingPanel
            speaking={speaking}
            savedRecording={studio.savedRecording}
            analysisResult={studio.analysisResult}
          />
        ) : null}

        <section className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
          <Card className="border-white/70 bg-white/82">
            <CardHeader>
              <CardTitle>Live capture</CardTitle>
              <CardDescription>
                Turn on your camera and microphone, record one take, and submit it when you are ready.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="overflow-hidden rounded-[1.75rem] border border-white/70 bg-slate-950 shadow-halo">
                <video
                  ref={studio.videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="aspect-video w-full bg-slate-950 object-cover"
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <MetricCard label="Timer" value={studio.formattedElapsedTime} icon={CircleDot} />
                <MetricCard
                  label="Camera"
                  value={faceStateLabels[studio.faceDetectionState]}
                  icon={ScanFace}
                />
                <MetricCard
                  label="Inputs"
                  value={`${studio.hasCamera ? "Camera on" : "Camera off"} / ${studio.hasMicrophone ? "Mic on" : "Mic off"}`}
                  icon={studio.hasMicrophone ? Mic : Camera}
                />
                <MetricCard
                  label="Recording"
                  value={studio.recordingUrl ? "Take ready" : studio.status === "recording" ? "Recording" : "Waiting"}
                  icon={studio.status === "recording" ? Square : CircleDot}
                />
              </div>

              <div className="flex flex-wrap gap-3">
                <Button
                  onClick={() => void studio.requestPermissions()}
                  disabled={
                    studio.status === "requesting-permissions" ||
                    studio.status === "uploading" ||
                    studio.status === "recording"
                  }
                  className="gap-2"
                >
                  <Camera className="h-4 w-4" />
                  Enable camera + mic
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => void studio.startRecording()}
                  disabled={!studio.canStartRecording || studio.status === "uploading"}
                  className="gap-2"
                >
                  <CircleDot className="h-4 w-4" />
                  Start recording
                </Button>
                <Button
                  variant="outline"
                  onClick={() => studio.stopRecording()}
                  disabled={!studio.canStopRecording}
                  className="gap-2"
                >
                  <Square className="h-4 w-4" />
                  Stop
                </Button>
                <Button
                  variant="outline"
                  onClick={() => studio.resetCapture()}
                  disabled={studio.status === "recording" || studio.status === "requesting-permissions"}
                  className="gap-2"
                >
                  <RotateCcw className="h-4 w-4" />
                  Retake
                </Button>
                <Button
                  variant="outline"
                  onClick={() => studio.releaseDevices()}
                  disabled={studio.status === "requesting-permissions"}
                >
                  Release devices
                </Button>
              </div>

              {studio.permissionError ? (
                <MessageBox tone="danger">{studio.permissionError}</MessageBox>
              ) : null}

              {studio.actionError ? <MessageBox tone="danger">{studio.actionError}</MessageBox> : null}
            </CardContent>
          </Card>

          <div className="grid gap-5">
            <Card className="border-white/70 bg-white/82">
              <CardHeader>
                <CardTitle>Before you record</CardTitle>
                <CardDescription>
                  A few quick reminders to get a cleaner coaching result.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {config.checklist.map((item) => (
                  <div key={item} className="rounded-2xl bg-muted/80 px-4 py-3 text-sm leading-6 text-foreground/85">
                    {item}
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="border-white/70 bg-white/82">
              <CardHeader>
                <CardTitle>Submit your take</CardTitle>
                <CardDescription>
                  When your take feels right, submit it once and review the feedback below.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button
                  onClick={() => void handleSubmit()}
                  disabled={
                    !studio.canSubmitForAnalysis ||
                    studio.status === "uploading" ||
                    studio.status === "analyzing" ||
                    isModeSpecificSubmitBusy
                  }
                  className="w-full gap-2"
                >
                  {studio.status === "uploading" || studio.status === "analyzing" || isModeSpecificSubmitBusy ? (
                    <>
                      <UploadCloud className="h-4 w-4" />
                      {studio.status === "uploading"
                        ? "Saving recording..."
                        : studio.status === "analyzing"
                          ? "Running analysis..."
                          : mode === "interview-training"
                            ? "Evaluating answer..."
                            : "Generating coaching..."}
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4" />
                      {getSubmitLabel()}
                    </>
                  )}
                </Button>

                {studio.savedRecording ? (
                  <MessageBox tone="success">Your recording was saved successfully.</MessageBox>
                ) : null}

                {studio.analysisResult ? (
                  <MessageBox tone={studio.analysisResult.processing_status === "analyzed" ? "success" : "neutral"}>
                    {studio.analysisResult.processing_status === "analyzed"
                      ? "Your review data is ready."
                      : "Your review is ready with a few limited checks."}
                  </MessageBox>
                ) : null}
              </CardContent>
            </Card>
          </div>
        </section>

        <section>
          <Card className="border-white/70 bg-white/82">
            <CardHeader>
              <CardTitle>Playback preview</CardTitle>
              <CardDescription>
                Review your take before you submit it.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {studio.recordingUrl ? (
                <video
                  controls
                  playsInline
                  preload="metadata"
                  className="aspect-video w-full rounded-[1.5rem] border border-white/70 bg-slate-950 object-cover"
                  src={studio.recordingUrl}
                />
              ) : (
                <div className="flex aspect-video items-center justify-center rounded-[1.5rem] border border-dashed border-border bg-muted/70 px-6 text-center text-sm leading-7 text-muted-foreground">
                  Record a take to preview the captured video here before you save it.
                </div>
              )}
            </CardContent>
          </Card>
        </section>

        {hasReview ? (
          <section className="space-y-5">
            <Card className="border-white/70 bg-white/82">
              <CardHeader>
                <CardTitle>AI review</CardTitle>
                <CardDescription>
                  One consolidated view of technical quality, speaking quality, body language, and risk signals.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
                  {mode === "interview-training" && interview.latestTurn ? (
                    <>
                      <MetricCard
                        label="Technical"
                        value={`${interview.latestTurn.technical_evaluation.technical_score}/100`}
                        icon={Sparkles}
                      />
                      <MetricCard
                        label="Correctness"
                        value={`${interview.latestTurn.technical_evaluation.correctness_score}/100`}
                        icon={Sparkles}
                      />
                      <MetricCard
                        label="Depth"
                        value={`${interview.latestTurn.technical_evaluation.explanation_depth_score}/100`}
                        icon={Sparkles}
                      />
                    </>
                  ) : null}

                  {mode === "public-speaking" && speaking.coachingResult ? (
                    <>
                      <MetricCard
                        label="Confidence"
                        value={`${speaking.coachingResult.confidence_score}/100`}
                        icon={Sparkles}
                      />
                      <MetricCard
                        label="Fact check"
                        value={`${speaking.coachingResult.factual_accuracy_score}/100`}
                        icon={Sparkles}
                      />
                    </>
                  ) : null}

                  {studio.analysisResult ? (
                    <>
                      <MetricCard
                        label="Fluency"
                        value={`${studio.analysisResult.communication_analysis.fluency_score}/100`}
                        icon={FileAudio2}
                      />
                      <MetricCard
                        label="Grammar"
                        value={
                          studio.analysisResult.communication_analysis.grammar_score !== null
                            ? `${studio.analysisResult.communication_analysis.grammar_score}/100`
                            : "Unavailable"
                        }
                        icon={FileAudio2}
                      />
                      <MetricCard
                        label="Eye contact"
                        value={`${studio.analysisResult.video_analysis.eye_contact.eye_contact_score}/100`}
                        icon={ScanFace}
                      />
                      <MetricCard
                        label="Posture"
                        value={`${studio.analysisResult.video_analysis.posture.posture_score}/100`}
                        icon={Video}
                      />
                      <MetricCard
                        label="Malpractice"
                        value={`${studio.analysisResult.video_analysis.malpractice.malpractice_confidence_score}/100`}
                        icon={Video}
                      />
                    </>
                  ) : null}
                </div>

                <div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
                  <div className="space-y-5">
                    {mode === "interview-training" && interview.latestTurn ? (
                      <SummaryPanel
                        title="Technical summary"
                        description={interview.latestTurn.technical_evaluation.summary}
                        accent="primary"
                      />
                    ) : null}

                    {mode === "public-speaking" && speaking.coachingResult ? (
                      <SummaryPanel
                        title="Speaking summary"
                        description={`${speaking.coachingResult.summary} ${speaking.coachingResult.factual_accuracy_summary}`.trim()}
                        accent="emerald"
                      />
                    ) : null}

                    {studio.analysisResult ? (
                      <Card className="border-white/70 bg-muted/55 shadow-none">
                        <CardHeader>
                          <CardTitle className="text-base">Transcript + delivery diagnostics</CardTitle>
                          <CardDescription>
                            Raw speech signal, pacing, and transcript cues from your submitted take.
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          <div className="rounded-[1.25rem] bg-white/80 p-4 text-sm leading-7 text-muted-foreground">
                            {studio.analysisResult.transcript.transcript || "No transcript available."}
                          </div>
                          <div className="grid gap-3 sm:grid-cols-2">
                            <DetailRow
                              label="Words per minute"
                              value={String(studio.analysisResult.communication_analysis.words_per_minute)}
                            />
                            <DetailRow
                              label="Pace"
                              value={studio.analysisResult.communication_analysis.pace_classification}
                            />
                            <DetailRow
                              label="Filler words"
                              value={String(studio.analysisResult.communication_analysis.filler_word_total)}
                            />
                            <DetailRow
                              label="Sentence quality"
                              value={`${studio.analysisResult.communication_analysis.sentence_quality_score}/100`}
                            />
                            <DetailRow
                              label="Looking-away events"
                              value={String(
                                studio.analysisResult.video_analysis.malpractice.repeated_looking_away_events
                              )}
                            />
                            <DetailRow
                              label="Downward-gaze events"
                              value={String(
                                studio.analysisResult.video_analysis.malpractice.excessive_downward_gaze_events
                              )}
                            />
                          </div>
                        </CardContent>
                      </Card>
                    ) : null}
                  </div>

                  <div className="space-y-5">
                    {mode === "interview-training" && interview.latestTurn ? (
                      <>
                        <InfoList
                          title="Strengths"
                          items={interview.latestTurn.technical_evaluation.strengths}
                          emptyLabel="No strengths detected yet."
                        />
                        <InfoList
                          title="Weaknesses"
                          items={interview.latestTurn.technical_evaluation.weaknesses}
                          emptyLabel="No weaknesses detected yet."
                        />
                        <InfoList
                          title="Coaching feedback"
                          items={interview.latestTurn.coaching_feedback}
                          emptyLabel="No coaching advice yet."
                        />
                      </>
                    ) : null}

                    {mode === "public-speaking" && speaking.coachingResult ? (
                      <>
                        <InfoList
                          title="Strengths"
                          items={speaking.coachingResult.strengths}
                          emptyLabel="No strengths detected yet."
                        />
                        <InfoList
                          title="What to improve"
                          items={[
                            ...speaking.coachingResult.communication_advice,
                            ...speaking.coachingResult.pacing_suggestions,
                            ...speaking.coachingResult.posture_coaching,
                            ...speaking.coachingResult.eye_contact_coaching
                          ]}
                          emptyLabel="No coaching advice yet."
                        />
                        <InfoList
                          title="Factual corrections"
                          items={speaking.coachingResult.factual_corrections}
                          emptyLabel="No factual corrections were needed for this take."
                        />
                      </>
                    ) : null}

                    {studio.analysisResult ? (
                      <>
                        <InfoList
                          title="Communication strengths"
                          items={studio.analysisResult.communication_analysis.strengths}
                          emptyLabel="No strong communication signals were detected yet."
                        />
                        <InfoList
                          title="Communication gaps"
                          items={studio.analysisResult.communication_analysis.weaknesses}
                          emptyLabel="No communication weaknesses were flagged."
                        />
                      </>
                    ) : null}
                  </div>
                </div>
              </CardContent>
            </Card>

            {(interview.finalReport || speaking.coachingResult) ? (
              <section className="grid gap-5 xl:grid-cols-[1fr_1fr]">
                <Card className="border-white/70 bg-white/82">
                  <CardHeader>
                    <CardTitle>Action plan</CardTitle>
                    <CardDescription>
                      Personalized coaching and roadmap steps generated from this session.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <InfoList
                      title="Coaching priorities"
                      items={
                        mode === "interview-training"
                          ? (interview.finalReport?.personalized_coaching ?? [])
                          : (speaking.coachingResult?.personalized_coaching ?? [])
                      }
                      emptyLabel="Complete a little more practice to unlock a stronger coaching plan."
                    />
                    <RoadmapList
                      items={
                        mode === "interview-training"
                          ? (interview.finalReport?.learning_roadmap ?? [])
                          : (speaking.coachingResult?.learning_roadmap ?? [])
                      }
                    />
                  </CardContent>
                </Card>

                <Card className="border-white/70 bg-white/82">
                  <CardHeader>
                    <CardTitle>Recommended courses</CardTitle>
                    <CardDescription>
                      Direct course links from approved learning platforms, curated from your latest gaps.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <RecommendationList
                      items={
                        mode === "interview-training"
                          ? (interview.finalReport?.recommendations ?? [])
                          : (speaking.coachingResult?.recommendations ?? [])
                      }
                    />
                  </CardContent>
                </Card>
              </section>
            ) : null}
          </section>
        ) : null}

        {studio.analysisResult?.warnings.length ? (
          <MessageBox tone="neutral">
            Some checks were limited for this take. If the feedback looks incomplete, try one more recording.
          </MessageBox>
        ) : null}
      </div>
    </main>
  );
}

function SummaryPanel({
  title,
  description,
  accent
}: {
  title: string;
  description: string;
  accent: "primary" | "emerald";
}) {
  const accentClasses =
    accent === "primary"
      ? "border-primary/20 bg-primary/8 text-foreground"
      : "border-emerald-200 bg-emerald-50 text-emerald-950";

  return (
    <div className={`rounded-[1.5rem] border p-5 ${accentClasses}`}>
      <p className="text-sm font-semibold">{title}</p>
      <p className="mt-3 text-sm leading-7">{description}</p>
    </div>
  );
}

function MetricCard({
  label,
  value,
  icon: Icon
}: {
  label: string;
  value: string;
  icon: LucideIcon;
}) {
  return (
    <div className="rounded-[1.5rem] bg-muted/80 p-4">
      <div className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-white/80 text-primary">
        <Icon className="h-4 w-4" />
      </div>
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">{label}</p>
      <p className="mt-2 text-base font-semibold text-foreground">{value}</p>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-2xl bg-muted/80 px-4 py-3">
      <span>{label}</span>
      <span className="font-medium text-foreground">{value}</span>
    </div>
  );
}

function MessageBox({
  children,
  tone
}: {
  children: ReactNode;
  tone: "danger" | "success" | "neutral";
}) {
  const tones = {
    danger: "border-red-200 bg-red-50 text-red-700",
    success: "border-emerald-200 bg-emerald-50 text-emerald-700",
    neutral: "border-amber-200 bg-amber-50 text-amber-800"
  };

  return <div className={`rounded-2xl border px-4 py-3 text-sm ${tones[tone]}`}>{children}</div>;
}

function InfoList({
  title,
  items,
  emptyLabel
}: {
  title: string;
  items: string[];
  emptyLabel: string;
}) {
  return (
    <div className="rounded-[1.5rem] bg-muted/80 p-4">
      <p className="text-sm font-semibold text-foreground">{title}</p>
      <div className="mt-3 space-y-2">
        {items.length ? (
          items.map((item, index) => (
            <div key={`${title}-${index}-${item}`} className="rounded-2xl bg-white/75 px-3 py-2 text-sm leading-6 text-foreground/85">
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

function RoadmapList({
  items
}: {
  items: {
    skill: string;
    next_step: string;
    resource_title: string | null;
    resource_url: string | null;
  }[];
}) {
  return (
    <div className="rounded-[1.5rem] bg-muted/80 p-4">
      <p className="text-sm font-semibold text-foreground">Roadmap</p>
      <div className="mt-3 space-y-3">
        {items.length ? (
          items.map((item, index) => (
            <div key={`${item.skill}-${index}`} className="rounded-2xl bg-white/75 p-3">
              <p className="text-sm font-semibold text-foreground">{item.skill}</p>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.next_step}</p>
              {item.resource_title && item.resource_url ? (
                <a
                  href={item.resource_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-3 inline-flex text-sm font-medium text-primary underline-offset-4 hover:underline"
                >
                  {item.resource_title}
                </a>
              ) : null}
            </div>
          ))
        ) : (
          <p className="text-sm text-muted-foreground">No roadmap items generated yet.</p>
        )}
      </div>
    </div>
  );
}

function RecommendationList({
  items
}: {
  items: {
    topic: string;
    title: string;
    platform: string;
    price: string;
    url: string;
  }[];
}) {
  return items.length ? (
    <div className="space-y-3">
      {items.map((item) => (
        <a
          key={item.url}
          href={item.url}
          target="_blank"
          rel="noreferrer"
          className="block rounded-[1.5rem] border border-white/70 bg-muted/72 p-4 transition hover:bg-white/92"
        >
          <p className="text-base font-semibold text-foreground">{item.title}</p>
          <p className="mt-2 text-sm text-muted-foreground">
            {item.platform} / {item.topic}
          </p>
        </a>
      ))}
    </div>
  ) : (
    <div className="rounded-[1.5rem] border border-dashed border-border bg-muted/60 p-4 text-sm leading-6 text-muted-foreground">
      Finish a fuller session to unlock targeted course suggestions here.
    </div>
  );
}
