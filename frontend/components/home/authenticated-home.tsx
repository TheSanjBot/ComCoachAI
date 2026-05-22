"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowUpRight,
  BookOpen,
  BriefcaseBusiness,
  FileSearch,
  Flame,
  LogOut,
  Mic2,
  Sparkles,
  Target
} from "lucide-react";

import { buttonVariants, Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ConfidenceTrendChart } from "@/components/home/confidence-trend-chart";
import { ModePerformanceChart } from "@/components/home/mode-performance-chart";
import type { DashboardOverview, FeaturedRecommendation, ModeCard } from "@/lib/dashboard";
import { getModeHref, type ModeSlug } from "@/lib/mode-config";
import { cn } from "@/lib/utils";

const modeIcons = {
  "interview-training": BriefcaseBusiness,
  "public-speaking": Mic2,
  "resume-skill-gap": FileSearch
} as const;

type AuthenticatedHomeProps = {
  overview: DashboardOverview;
  onSignOut: () => void;
};

function formatDate(dateValue: string) {
  const [year, month, day] = dateValue.split("-").map(Number);
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric"
  }).format(new Date(year, month - 1, day));
}

export function AuthenticatedHome({ overview, onSignOut }: AuthenticatedHomeProps) {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(227,197,165,0.34),_transparent_24%),radial-gradient(circle_at_top_right,_rgba(76,140,144,0.18),_transparent_26%),linear-gradient(140deg,_#f8f4ec_0%,_#eff7f5_46%,_#dceae7_100%)] px-6 py-8">
      <div className="mx-auto max-w-7xl space-y-8">
        <motion.section
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
          className="grid gap-5 xl:grid-cols-[1.18fr_0.82fr]"
        >
          <Card className="border-white/70 bg-white/84">
            <CardContent className="p-6">
              <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
                <div className="space-y-4">
                  <div className="inline-flex rounded-full border border-foreground/10 bg-white/80 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-foreground/60">
                    Coaching home
                  </div>
                  <div className="space-y-3">
                    <h1 className="max-w-3xl text-4xl font-semibold leading-tight">
                      Welcome back, {overview.welcome_name}. Let&apos;s keep your communication sharp.
                    </h1>
                    <p className="max-w-2xl text-sm leading-7 text-muted-foreground sm:text-base">
                      Pick the mode you want to work on next, review your momentum, and jump back
                      into focused coaching without leaving the home dashboard.
                    </p>
                  </div>
                </div>

                <Button variant="outline" onClick={onSignOut} className="gap-2 self-start">
                  <LogOut className="h-4 w-4" />
                  Sign out
                </Button>
              </div>

              <div className="mt-6 grid gap-4 sm:grid-cols-3">
                {[
                  {
                    icon: Flame,
                    label: "Streak",
                    value: `${overview.streak_days} days`,
                    note: "Keep the rhythm going"
                  },
                  {
                    icon: Sparkles,
                    label: "Avg confidence",
                    value: `${overview.average_confidence_score}/100`,
                    note: "Across completed sessions"
                  },
                  {
                    icon: Target,
                    label: "Current focus",
                    value: overview.focus_area,
                    note: "Most repeated coaching signal"
                  }
                ].map(({ icon: Icon, label, value, note }) => (
                  <div key={label} className="rounded-[1.75rem] bg-muted/80 p-4">
                    <div className="mb-3 inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                      <Icon className="h-5 w-5" />
                    </div>
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                      {label}
                    </p>
                    <p className="mt-2 text-lg font-semibold text-foreground">{value}</p>
                    <p className="mt-1 text-sm text-muted-foreground">{note}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="border-white/70 bg-[linear-gradient(165deg,_rgba(35,82,90,0.96),_rgba(19,58,64,0.94))] text-white">
            <CardHeader>
              <CardTitle className="text-white">Priority actions</CardTitle>
              <CardDescription className="text-white/75">
                Short, high-signal next steps pulled from your latest reports.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {overview.priority_actions.map((action, index) => (
                <div
                  key={`${index}-${action}`}
                  className="rounded-2xl bg-white/10 px-4 py-3 text-sm leading-6 text-white/90"
                >
                  {action}
                </div>
              ))}
            </CardContent>
          </Card>
        </motion.section>

        <section className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.05 }}
          >
            <Card className="h-full border-white/70 bg-white/84">
              <CardHeader>
                <CardTitle>Choose a mode</CardTitle>
                <CardDescription>
                  Start directly from the experience you want to improve next.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4">
                {overview.mode_cards.map((mode) => (
                  <ModeLaunchCard key={mode.slug} mode={mode} />
                ))}
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.12 }}
            className="grid gap-5"
          >
            <Card className="border-white/70 bg-white/84">
              <CardHeader>
                <CardTitle>Scoreboard</CardTitle>
                <CardDescription>
                  Your core communication and technical indicators at a glance.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4">
                <div className="grid gap-4 sm:grid-cols-3">
                  {overview.score_summaries.map((item) => (
                    <div key={item.label} className="rounded-[1.5rem] bg-muted/80 p-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-foreground">{item.label}</span>
                        <span className="rounded-full bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary">
                          {item.delta >= 0 ? `+${item.delta}` : item.delta}
                        </span>
                      </div>
                      <p className="mt-4 text-3xl font-semibold text-foreground">{item.score}</p>
                      <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.note}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </section>

        <section className="grid gap-5 xl:grid-cols-[1fr_1fr]">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.18 }}
          >
            <Card className="h-full border-white/70 bg-white/84">
              <CardHeader>
                <CardTitle>Momentum trend</CardTitle>
                <CardDescription>
                  Communication bars and confidence trend line across recent sessions.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ConfidenceTrendChart data={overview.confidence_trend} />
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.24 }}
          >
            <Card className="h-full border-white/70 bg-white/84">
              <CardHeader>
                <CardTitle>Mode performance</CardTitle>
                <CardDescription>
                  Compare how each coaching mode is performing over time.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ModePerformanceChart data={overview.mode_performance} />
              </CardContent>
            </Card>
          </motion.div>
        </section>

        <section className="grid gap-5 xl:grid-cols-[1fr_1fr]">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <Card className="h-full border-white/70 bg-white/84">
              <CardHeader>
                <CardTitle>Recommended courses</CardTitle>
                <CardDescription>
                  Curated learning links from course platforms surfaced directly on your home dashboard.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {overview.featured_recommendations.length ? (
                  overview.featured_recommendations.map((item) => (
                    <RecommendationCard key={item.url} item={item} />
                  ))
                ) : (
                  <EmptyState copy="Finish a session to unlock targeted course recommendations here." />
                )}
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.36 }}
          >
            <Card className="h-full border-white/70 bg-white/84">
              <CardHeader>
                <CardTitle>Recent reports</CardTitle>
                <CardDescription>
                  Review what happened last and jump back into the next iteration with context.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {overview.recent_reports.length ? (
                  overview.recent_reports.map((report) => (
                    <div key={report.id} className="rounded-[1.5rem] bg-muted/80 p-4">
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                        <div>
                          <p className="text-base font-semibold text-foreground">{report.title}</p>
                          <p className="text-sm text-muted-foreground">
                            {report.mode} / {formatDate(report.completed_at)}
                          </p>
                        </div>
                        <span className="inline-flex rounded-full bg-white/80 px-3 py-1 text-xs font-semibold text-foreground/70">
                          {report.confidence_score}/100 confidence
                        </span>
                      </div>
                      <p className="mt-3 text-sm leading-6 text-muted-foreground">{report.summary}</p>
                    </div>
                  ))
                ) : (
                  <EmptyState copy="Your completed reports will appear here after you finish a session." />
                )}
              </CardContent>
            </Card>
          </motion.div>
        </section>

        <section className="grid gap-5 xl:grid-cols-[1fr_1fr]">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.42 }}
          >
            <Card className="h-full border-white/70 bg-white/84">
              <CardHeader>
                <CardTitle>Interview history</CardTitle>
                <CardDescription>
                  Your recent technical interview sessions and how they trended.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {overview.interview_history.length ? (
                  overview.interview_history.map((item) => (
                    <div
                      key={item.id}
                      className="flex flex-col gap-4 rounded-[1.5rem] bg-muted/80 p-4 sm:flex-row sm:items-center sm:justify-between"
                    >
                      <div className="space-y-1">
                        <p className="text-base font-semibold text-foreground">
                          {item.role} / {item.level}
                        </p>
                        <p className="text-sm text-muted-foreground">{formatDate(item.completed_at)}</p>
                        <p className="text-sm leading-6 text-muted-foreground">{item.trend}</p>
                      </div>
                      <div className="flex flex-wrap gap-2 sm:justify-end">
                        <ScorePill label="Technical" value={item.technical_score} />
                        <ScorePill label="Communication" value={item.communication_score} />
                      </div>
                    </div>
                  ))
                ) : (
                  <EmptyState copy="Start an interview session to build visible technical history." />
                )}
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.48 }}
          >
            <Card className="h-full border-white/70 bg-white/84">
              <CardHeader>
                <CardTitle>Session volume</CardTitle>
                <CardDescription>
                  All completed interview, speaking, and resume sessions feed this single product dashboard.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-[1.75rem] bg-[linear-gradient(160deg,_rgba(55,96,102,0.96),_rgba(27,70,76,0.96))] p-6 text-white">
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-white/65">
                    Total tracked sessions
                  </p>
                  <p className="mt-3 text-5xl font-semibold">{overview.total_sessions}</p>
                  <div className="mt-6 grid gap-3 sm:grid-cols-2">
                    <div className="rounded-2xl bg-white/10 p-4">
                      <p className="text-sm font-semibold text-white">Recommended next mode</p>
                      <p className="mt-2 text-sm leading-6 text-white/75">
                        {overview.mode_cards.find((item) => item.slug === overview.recommended_mode_slug)?.title ??
                          "Choose any mode"}
                      </p>
                    </div>
                    <div className="rounded-2xl bg-white/10 p-4">
                      <p className="text-sm font-semibold text-white">Focus signal</p>
                      <p className="mt-2 text-sm leading-6 text-white/75">{overview.focus_area}</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </section>
      </div>
    </main>
  );
}

function ModeLaunchCard({ mode }: { mode: ModeCard }) {
  const Icon = modeIcons[mode.slug as keyof typeof modeIcons] ?? Sparkles;
  const modeSlug = mode.slug as ModeSlug;

  return (
    <div className="rounded-[1.8rem] border border-white/70 bg-muted/72 p-5 transition hover:bg-white/90">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-3">
          <div className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-white/90 text-primary">
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <p className="text-lg font-semibold text-foreground">{mode.title}</p>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">{mode.description}</p>
          </div>
        </div>
        <span className="inline-flex rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-foreground/70">
          {mode.status}
        </span>
      </div>

      <div className="mt-4 flex flex-wrap gap-2 text-xs font-semibold text-foreground/70">
        <span className="inline-flex rounded-full bg-white/85 px-3 py-2">{mode.primary_focus}</span>
        <span className="inline-flex rounded-full bg-white/85 px-3 py-2">
          {mode.estimated_duration_minutes} min
        </span>
      </div>

      <div className="mt-5 flex items-center justify-between gap-4">
        <p className="text-sm leading-6 text-muted-foreground">{mode.next_milestone}</p>
        <Link href={getModeHref(modeSlug)} className={cn(buttonVariants({ size: "sm" }), "gap-2 shrink-0")}>
          Open
          <ArrowUpRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}

function RecommendationCard({ item }: { item: FeaturedRecommendation }) {
  return (
    <a
      href={item.url}
      target="_blank"
      rel="noreferrer"
      className="block rounded-[1.5rem] border border-white/70 bg-muted/72 p-4 transition hover:bg-white/90"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-base font-semibold text-foreground">{item.title}</p>
          <p className="mt-2 text-sm text-muted-foreground">
            {item.platform} / {item.topic}
          </p>
          <p className="mt-2 text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            From {item.source_mode}
          </p>
        </div>
        <div className="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-white/90 text-primary">
          <BookOpen className="h-4 w-4" />
        </div>
      </div>
    </a>
  );
}

function ScorePill({ label, value }: { label: string; value: number }) {
  return (
    <span className="inline-flex rounded-full bg-white/85 px-3 py-2 text-xs font-semibold text-foreground/75">
      {label}: {value}/100
    </span>
  );
}

function EmptyState({ copy }: { copy: string }) {
  return (
    <div className="rounded-[1.5rem] border border-dashed border-border bg-muted/60 p-4 text-sm leading-6 text-muted-foreground">
      {copy}
    </div>
  );
}
