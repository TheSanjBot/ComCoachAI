"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";

import { fetchDashboardSummary, fetchModes, fetchProfile } from "@/lib/api";
import type { DashboardSummary, ModeDefinition, ModeId, Report } from "@/types";
import { AuthPanel } from "@/components/dashboard/auth-panel";
import { ModeSelector } from "@/components/dashboard/mode-selector";
import { OverviewCards } from "@/components/dashboard/overview-cards";
import { PerformanceChart } from "@/components/dashboard/performance-chart";
import { RecentReports } from "@/components/dashboard/recent-reports";
import { ReportHighlight } from "@/components/dashboard/report-highlight";
import { RecorderStudio } from "@/components/recording/recorder-studio";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const mockSummary: DashboardSummary = {
  total_sessions: 4,
  average_scores: {
    communication: 78,
    technical: 74,
    confidence: 71,
    overall: 76
  },
  confidence_trend: [
    { sessionId: 1, confidence: 62, communication: 68, overall: 67, mode: "interview" },
    { sessionId: 2, confidence: 69, communication: 72, overall: 71, mode: "public_speaking" },
    { sessionId: 3, confidence: 73, communication: 79, overall: 76, mode: "interview" },
    { sessionId: 4, confidence: 81, communication: 84, overall: 82, mode: "public_speaking" }
  ],
  recent_reports: []
};

const fallbackModes: ModeDefinition[] = [
  {
    id: "interview",
    title: "Interview Training Mode",
    description:
      "Structured role-based interviews with contextual follow-up questions and technical evaluation."
  },
  {
    id: "public_speaking",
    title: "Public Speaking Training Mode",
    description:
      "Speech and body-language coaching for pacing, confidence, storytelling, and presence."
  },
  {
    id: "resume_analysis",
    title: "Resume + Skill Gap Analysis Mode",
    description:
      "Role-matched resume analysis, missing skill detection, and upskilling roadmap generation."
  }
];

export function DashboardShell() {
  const [token, setToken] = useState<string | null>(null);
  const [name, setName] = useState<string>("Coach-ready guest");
  const [modes, setModes] = useState<ModeDefinition[]>(fallbackModes);
  const [selectedMode, setSelectedMode] = useState<ModeId>("interview");
  const [summary, setSummary] = useState<DashboardSummary>(mockSummary);
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  async function refreshAuthenticatedState(activeToken: string) {
    localStorage.setItem("commcoach_token", activeToken);
    setToken(activeToken);
    const [profile, dashboard, modeList] = await Promise.all([
      fetchProfile(activeToken),
      fetchDashboardSummary(activeToken),
      fetchModes()
    ]);
    setName(profile.full_name);
    setSummary(dashboard);
    setReports(dashboard.recent_reports);
    setModes(modeList);
  }

  useEffect(() => {
    const storedToken = localStorage.getItem("commcoach_token");

    async function bootstrap() {
      try {
        const modeList = await fetchModes();
        setModes(modeList);
      } catch {
        setModes(fallbackModes);
      }

      if (!storedToken) {
        setLoading(false);
        return;
      }

      try {
        await refreshAuthenticatedState(storedToken);
      } catch {
        localStorage.removeItem("commcoach_token");
      } finally {
        setLoading(false);
      }
    }

    void bootstrap();
  }, []);

  const activeReport = useMemo(() => reports[0] ?? null, [reports]);

  function handleNewReport(report: Report) {
    setReports((current) => [report, ...current].slice(0, 6));
    setSummary((current) => ({
      ...current,
      recent_reports: [report, ...current.recent_reports].slice(0, 6),
      total_sessions: current.total_sessions + 1
    }));
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="pointer-events-none fixed inset-0 bg-grid-pattern opacity-40" />
      <div className="mx-auto max-w-7xl px-5 py-8 md:px-8 lg:px-10">
        <motion.section
          animate={{ opacity: 1, y: 0 }}
          className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]"
          initial={{ opacity: 0, y: 16 }}
          transition={{ duration: 0.45 }}
        >
          <Card className="panel-glass holographic-gradient overflow-hidden text-white shadow-orange-glow-subtle">
            <div className="flex flex-wrap gap-2">
              <Badge className="border-primary/30 bg-primary/15 font-mono uppercase tracking-[0.16em] text-primary shadow-orange-glow">AI Communication Coaching</Badge>
              <Badge className="border-primary/30 bg-primary/15 font-mono uppercase tracking-[0.16em] text-primary shadow-orange-glow">Hybrid Processing</Badge>
              <Badge className="border-primary/30 bg-primary/15 font-mono uppercase tracking-[0.16em] text-primary shadow-orange-glow">Semantic Memory</Badge>
            </div>
            <h1 className="mt-6 max-w-3xl font-heading text-4xl font-semibold leading-tight md:text-6xl">
              CommCoach AI helps people sound sharper, calmer, and more
              <span className="text-gradient-gold"> credible.</span>
            </h1>
            <p className="mt-6 max-w-2xl text-base leading-8 text-white/75 md:text-lg">
              Practice technical interviews, coach public speaking, and diagnose role gaps with a staged pipeline that keeps live capture lightweight and deeper analysis explainable.
            </p>
            <div className="mt-8 flex flex-wrap gap-3 text-sm text-white/80">
              <span className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-2 font-mono uppercase tracking-[0.14em]">Speech intelligence</span>
              <span className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-2 font-mono uppercase tracking-[0.14em]">Body-language signals</span>
              <span className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-2 font-mono uppercase tracking-[0.14em]">Context-aware follow-ups</span>
              <span className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-2 font-mono uppercase tracking-[0.14em]">Personalized upskilling</span>
            </div>
          </Card>

          {token ? (
            <Card className="panel-surface flex flex-col justify-between shadow-panel-glow">
              <div>
                <p className="font-mono text-sm uppercase tracking-[0.2em] text-muted-foreground">
                  Active Coach Profile
                </p>
                <h2 className="mt-4 font-heading text-3xl font-semibold">{name}</h2>
                <p className="mt-3 text-sm leading-7 text-muted-foreground">
                  Your homepage dashboard stays in one place so you can move between interview prep, speech coaching, and resume analysis without context switching.
                </p>
              </div>
              <Button
                className="mt-6"
                onClick={() => {
                  localStorage.removeItem("commcoach_token");
                  setToken(null);
                  setName("Coach-ready guest");
                  setSummary(mockSummary);
                  setReports([]);
                }}
                type="button"
                variant="outline"
              >
                Logout
              </Button>
            </Card>
          ) : (
            <AuthPanel
              onAuthenticated={async (activeToken) => {
                await refreshAuthenticatedState(activeToken);
              }}
            />
          )}
        </motion.section>

        <section className="mt-8">
          <OverviewCards
            scores={summary.average_scores}
            totalSessions={summary.total_sessions}
          />
        </section>

        <section className="mt-8">
          <ModeSelector
            modes={modes}
            onSelect={setSelectedMode}
            selectedMode={selectedMode}
          />
        </section>

        <section className="mt-8">
          <RecorderStudio
            onNewReport={handleNewReport}
            selectedMode={selectedMode}
            token={token}
          />
        </section>

        <section className="mt-8 grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <PerformanceChart data={summary.confidence_trend} />
          <ReportHighlight report={activeReport} />
        </section>

        <section className="mt-8">
          <RecentReports reports={reports} />
        </section>

        {loading ? (
          <p className="mt-8 text-sm text-muted-foreground">
            Loading dashboard context...
          </p>
        ) : null}
      </div>
    </main>
  );
}
