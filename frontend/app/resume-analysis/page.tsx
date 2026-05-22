"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  BadgeCheck,
  FileSearch,
  FileUp,
  LoaderCircle,
  LogOut,
  ShieldCheck,
  Sparkles,
  Target
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/use-auth";
import { analyzeResumeText, analyzeResumeUpload, type ResumeAnalysisResponse } from "@/lib/resume";

const ROLES = [
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

export default function ResumeAnalysisPage() {
  const router = useRouter();
  const { session, status, signOut } = useAuth();
  const [targetRole, setTargetRole] = useState("Backend Engineer");
  const [resumeText, setResumeText] = useState("");
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ResumeAnalysisResponse | null>(null);

  const canSubmit = useMemo(() => Boolean(resumeFile || resumeText.trim()), [resumeFile, resumeText]);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.replace("/login");
    }
  }, [router, status]);

  if (status === "loading") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[linear-gradient(135deg,_#f7f2ea_0%,_#eef3f3_45%,_#e0ebe8_100%)]">
        <div className="rounded-full border border-foreground/10 bg-white/75 px-5 py-3 text-sm text-foreground/70">
          Loading resume workspace...
        </div>
      </main>
    );
  }

  if (status === "unauthenticated" || !session) {
    return null;
  }

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) {
      setError("Upload a resume file or paste resume text before analyzing.");
      return;
    }
    if (!session) {
      setError("Your session expired. Please sign in again.");
      return;
    }

    const accessToken = session.access_token;
    setSubmitting(true);
    setError(null);
    try {
      const payload = resumeFile
        ? await analyzeResumeUpload(accessToken, { file: resumeFile, targetRole })
        : await analyzeResumeText(accessToken, {
            resume_text: resumeText,
            target_role: targetRole
          });
      setResult(payload);
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Resume analysis failed. Please try again."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(227,197,165,0.38),_transparent_24%),radial-gradient(circle_at_top_right,_rgba(116,160,153,0.2),_transparent_28%),linear-gradient(140deg,_#f8f4ec_0%,_#eef6f4_48%,_#ddeae5_100%)] px-6 py-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <section className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
          <Card className="border-white/70 bg-white/84">
            <CardContent className="p-6">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="space-y-3">
                  <Link href="/" className="inline-flex items-center gap-2 text-sm font-medium text-foreground/70">
                    <ArrowLeft className="h-4 w-4" />
                    Back to dashboard
                  </Link>
                  <div className="space-y-3">
                    <div className="inline-flex rounded-full border border-foreground/10 bg-white/80 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-foreground/60">
                      Resume intelligence
                    </div>
                    <h1 className="max-w-3xl text-4xl font-semibold leading-tight">
                      Turn your resume into a hiring-ready action plan.
                    </h1>
                    <p className="max-w-2xl text-sm leading-7 text-muted-foreground sm:text-base">
                      Benchmark your resume against a target role, surface real gaps, and get a more practical roadmap than a simple keyword match.
                    </p>
                  </div>
                </div>
                <Button variant="outline" onClick={signOut} className="gap-2">
                  <LogOut className="h-4 w-4" />
                  Sign out
                </Button>
              </div>

              <div className="mt-6 grid gap-4 sm:grid-cols-3">
                <HeroMetric
                  label="Role alignment"
                  value={result ? `${result.matching_score}/100` : "Waiting"}
                  note="How closely your resume matches the role you selected."
                  icon={Target}
                />
                <HeroMetric
                  label="ATS readiness"
                  value={result ? `${result.ats_readiness_score}/100` : "Waiting"}
                  note="Signal quality for real screening and recruiter skim."
                  icon={ShieldCheck}
                />
                <HeroMetric
                  label="Priority gaps"
                  value={result ? String(result.priority_gaps.length) : "0"}
                  note="The most important missing proof points to fix next."
                  icon={BadgeCheck}
                />
              </div>
            </CardContent>
          </Card>

          <Card className="border-white/70 bg-[linear-gradient(165deg,_rgba(35,82,90,0.96),_rgba(19,58,64,0.94))] text-white">
            <CardHeader>
              <CardTitle className="text-white">How this review works</CardTitle>
              <CardDescription className="text-white/75">
                The analyzer looks for evidence, not just keywords, and then maps the gaps into realistic next steps.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                "Role-fit scoring compares your resume to the selected job family.",
                "ATS readiness checks whether the structure and evidence look screening-friendly.",
                "Priority gaps focus on what would most improve real recruiter confidence.",
                "Course links point to direct learning pages on approved platforms."
              ].map((item, index) => (
                <div key={`${index}-${item}`} className="rounded-2xl bg-white/10 px-4 py-3 text-sm leading-6 text-white/90">
                  {item}
                </div>
              ))}
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-5 xl:grid-cols-[0.88fr_1.12fr]">
          <Card className="border-white/70 bg-white/84">
            <CardHeader>
              <CardTitle>Analyze your resume</CardTitle>
              <CardDescription>
                File upload is preferred. Pasted text works well for quick iteration and testing.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-4" onSubmit={onSubmit}>
                <label className="grid gap-2 text-sm font-medium text-foreground">
                  Target role
                  <select
                    value={targetRole}
                    onChange={(event) => setTargetRole(event.target.value)}
                    className="h-11 rounded-2xl border border-border bg-background px-4 text-sm"
                  >
                    {ROLES.map((role) => (
                      <option key={role} value={role}>
                        {role}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="grid gap-2 text-sm font-medium text-foreground">
                  Resume file
                  <div className="rounded-[1.5rem] border border-dashed border-border bg-muted/50 p-4">
                    <input
                      type="file"
                      accept=".pdf,.txt,.md"
                      onChange={(event) => setResumeFile(event.target.files?.[0] ?? null)}
                      className="block w-full text-sm"
                    />
                    <p className="mt-2 text-xs leading-6 text-muted-foreground">
                      Supports `.pdf`, `.txt`, and `.md` files.
                    </p>
                  </div>
                </label>

                <label className="grid gap-2 text-sm font-medium text-foreground">
                  Or paste resume text
                  <textarea
                    value={resumeText}
                    onChange={(event) => setResumeText(event.target.value)}
                    rows={10}
                    placeholder="Paste your resume content here if you do not want to upload a file."
                    className="rounded-[1.5rem] border border-border bg-background px-4 py-3 text-sm leading-6"
                  />
                </label>

                {error ? (
                  <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900">
                    {error}
                  </div>
                ) : null}

                <Button type="submit" size="lg" disabled={submitting || !canSubmit} className="gap-2">
                  {submitting ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <FileUp className="h-4 w-4" />}
                  {submitting ? "Analyzing..." : "Analyze resume"}
                </Button>
              </form>
            </CardContent>
          </Card>

          <div className="grid gap-5">
            {result ? (
              <>
                <Card className="border-white/70 bg-white/84">
                  <CardHeader>
                    <CardTitle>Hiring summary</CardTitle>
                    <CardDescription>
                      A recruiter-style view of fit, evidence quality, and the next improvement areas.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-5">
                    <div className="grid gap-4 sm:grid-cols-3">
                      <ResultMetric label="Role match" value={`${result.matching_score}/100`} icon={Target} />
                      <ResultMetric label="ATS readiness" value={`${result.ats_readiness_score}/100`} icon={ShieldCheck} />
                      <ResultMetric label="Saved report" value={result.report_id ?? "Pending"} icon={FileSearch} />
                    </div>

                    <div className="rounded-[1.5rem] border border-primary/15 bg-primary/8 p-5">
                      <p className="text-sm font-semibold text-foreground">Role-fit summary</p>
                      <p className="mt-3 text-sm leading-7 text-foreground/80">
                        {result.role_fit_summary || "The role-fit summary will appear here once analysis completes."}
                      </p>
                    </div>

                    <div className="grid gap-4 xl:grid-cols-2">
                      <TokenBlock
                        title="Detected skills"
                        items={result.detected_skills}
                        emptyText="No role-relevant skills were detected yet."
                      />
                      <TokenBlock
                        title="Missing skills"
                        items={result.missing_skills}
                        emptyText="No major missing skills were flagged."
                      />
                    </div>

                    <div className="grid gap-4 xl:grid-cols-2">
                      <ListBlock
                        title="Priority gaps"
                        items={result.priority_gaps}
                        emptyText="No priority gaps were identified."
                      />
                      <ListBlock
                        title="Evidence highlights"
                        items={result.evidence_highlights}
                        emptyText="No evidence highlights were extracted."
                      />
                    </div>
                  </CardContent>
                </Card>

                <section className="grid gap-5 xl:grid-cols-[1fr_1fr]">
                  <Card className="border-white/70 bg-white/84">
                    <CardHeader>
                      <CardTitle>Coaching plan</CardTitle>
                      <CardDescription>
                        Practical guidance and roadmap steps to strengthen the resume for real applications.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <ListBlock
                        title="Personalized coaching"
                        items={result.personalized_coaching}
                        emptyText="Personalized coaching will appear here once gaps are identified."
                      />
                      <RoadmapBlock items={result.learning_roadmap} />
                    </CardContent>
                  </Card>

                  <Card className="border-white/70 bg-white/84">
                    <CardHeader>
                      <CardTitle>Recommended courses</CardTitle>
                      <CardDescription>
                        Direct learning links from approved course platforms based on your current gaps.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {result.recommendations.length ? (
                        result.recommendations.map((item) => (
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
                        ))
                      ) : (
                        <EmptyBlock copy="No course recommendations were generated for this resume yet." />
                      )}
                    </CardContent>
                  </Card>
                </section>

                <Card className="border-white/70 bg-white/84">
                  <CardHeader>
                    <CardTitle>Parsed resume snapshot</CardTitle>
                    <CardDescription>
                      Use this to sanity-check what the parser actually extracted from the resume.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="rounded-[1.5rem] bg-muted/70 p-4 text-sm leading-7 text-muted-foreground">
                      {result.extracted_text_preview || "No extracted text preview available."}
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card className="border-white/70 bg-white/84">
                <CardContent className="p-6">
                  <EmptyBlock copy="Upload a resume or paste resume text to generate role-fit scoring, ATS readiness, gap analysis, a roadmap, and direct course recommendations." />
                </CardContent>
              </Card>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

function HeroMetric({
  label,
  value,
  note,
  icon: Icon
}: {
  label: string;
  value: string;
  note: string;
  icon: typeof Sparkles;
}) {
  return (
    <div className="rounded-[1.75rem] bg-muted/80 p-4">
      <div className="mb-3 inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
        <Icon className="h-5 w-5" />
      </div>
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">{label}</p>
      <p className="mt-2 text-lg font-semibold text-foreground">{value}</p>
      <p className="mt-1 text-sm leading-6 text-muted-foreground">{note}</p>
    </div>
  );
}

function ResultMetric({
  label,
  value,
  icon: Icon
}: {
  label: string;
  value: string;
  icon: typeof Sparkles;
}) {
  return (
    <div className="rounded-[1.5rem] bg-muted/75 p-4">
      <div className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-white/80 text-primary">
        <Icon className="h-4 w-4" />
      </div>
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">{label}</p>
      <p className="mt-2 text-base font-semibold text-foreground">{value}</p>
    </div>
  );
}

function TokenBlock({
  title,
  items,
  emptyText
}: {
  title: string;
  items: string[];
  emptyText: string;
}) {
  return (
    <div className="rounded-[1.5rem] bg-muted/70 p-4">
      <p className="text-sm font-semibold text-foreground">{title}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {items.length ? (
          items.map((item, index) => (
            <span
              key={`${title}-${index}-${item}`}
              className="inline-flex rounded-full bg-white/85 px-3 py-2 text-xs font-semibold text-foreground/75"
            >
              {item}
            </span>
          ))
        ) : (
          <p className="text-sm text-muted-foreground">{emptyText}</p>
        )}
      </div>
    </div>
  );
}

function ListBlock({
  title,
  items,
  emptyText
}: {
  title: string;
  items: string[];
  emptyText: string;
}) {
  return (
    <div className="rounded-[1.5rem] bg-muted/70 p-4">
      <p className="text-sm font-semibold text-foreground">{title}</p>
      <div className="mt-3 space-y-2">
        {items.length ? (
          items.map((item, index) => (
            <div
              key={`${title}-${index}-${item}`}
              className="rounded-2xl bg-white/80 px-3 py-2 text-sm leading-6 text-foreground/85"
            >
              {item}
            </div>
          ))
        ) : (
          <p className="text-sm text-muted-foreground">{emptyText}</p>
        )}
      </div>
    </div>
  );
}

function RoadmapBlock({
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
    <div className="rounded-[1.5rem] bg-muted/70 p-4">
      <p className="text-sm font-semibold text-foreground">Learning roadmap</p>
      <div className="mt-3 space-y-3">
        {items.length ? (
          items.map((item, index) => (
            <div key={`${item.skill}-${index}`} className="rounded-2xl bg-white/80 p-3">
              <p className="font-medium text-foreground">{item.skill}</p>
              <p className="mt-1 text-sm leading-6 text-muted-foreground">{item.next_step}</p>
              {item.resource_title && item.resource_url ? (
                <a
                  href={item.resource_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 inline-flex text-sm font-medium text-primary underline-offset-4 hover:underline"
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

function EmptyBlock({ copy }: { copy: string }) {
  return (
    <div className="rounded-[1.75rem] border border-dashed border-border bg-muted/55 p-6 text-sm leading-7 text-muted-foreground">
      {copy}
    </div>
  );
}
