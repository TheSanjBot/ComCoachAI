import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  BriefcaseBusiness,
  ChartColumnBig,
  Mic2,
  ScanSearch,
  Sparkles,
} from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const pillars = [
  {
    icon: BriefcaseBusiness,
    title: "Interview practice that feels realistic",
    description:
      "Train with structured technical questions, recorded answers, technical scoring, and follow-up coaching."
  },
  {
    icon: Mic2,
    title: "Speaking feedback beyond delivery",
    description:
      "Review fluency, grammar, eye contact, posture, confidence, and factual accuracy from one speaking session."
  },
  {
    icon: ScanSearch,
    title: "Resume analysis built for real job targeting",
    description:
      "Map your resume to a target role, surface missing skills, and build a cleaner upskilling plan."
  }
];

const quickStats = [
  { label: "Core modes", value: "3", icon: Sparkles },
  { label: "Coaching home", value: "Unified", icon: ChartColumnBig },
  { label: "Capture approach", value: "Hybrid", icon: Mic2 }
];

type PublicHomeProps = {
  notice?: string | null;
};

export function PublicHome({ notice }: PublicHomeProps) {
  return (
    <main className="relative overflow-hidden bg-background px-6 py-10">
      <div className="pointer-events-none absolute inset-0 bg-grid-pattern opacity-40" />
      <div className="relative z-10 mx-auto flex min-h-[calc(100vh-5rem)] max-w-6xl flex-col justify-center gap-10">
        {notice ? (
          <div className="rounded-2xl border border-primary/30 bg-primary/10 px-4 py-3 text-sm text-primary shadow-orange-glow">
            {notice}
          </div>
        ) : null}

        <motion.div
          initial={{ opacity: 0, y: 28 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55 }}
          className="space-y-8"
        >
          <div className="grid gap-10 lg:grid-cols-[1.15fr_0.85fr] lg:items-end">
            <section className="space-y-6">
              <h1 className="max-w-3xl text-5xl font-semibold leading-tight sm:text-6xl">
                A communication coaching workspace built for <span className="text-gradient-gold">real practice.</span>
              </h1>
              <p className="max-w-2xl text-lg leading-8 text-muted-foreground">
                Practice interviews, rehearse public speaking, and benchmark your resume from one
                polished home dashboard. Every session feeds into feedback, trends, and targeted
                next steps.
              </p>
              <div className="flex flex-wrap gap-4">
                <Link href="/signup" className={cn(buttonVariants({ size: "lg" }), "gap-2")}>
                  Create account
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link href="/login" className={buttonVariants({ variant: "outline", size: "lg" })}>
                  Sign in
                </Link>
              </div>
            </section>

            <Card className="panel-glass shadow-panel-glow">
              <CardHeader>
                <CardTitle>Inside the coaching workspace</CardTitle>
                <CardDescription>
                  Three focused modes, one premium-feeling dashboard, and session history that
                  keeps your progress connected.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3 text-sm text-muted-foreground">
                {quickStats.map(({ label, value, icon: Icon }) => (
                  <div key={label} className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                    <div className="flex items-center gap-3 text-foreground">
                      <div className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-primary/30 bg-primary/12 text-primary shadow-orange-glow">
                        <Icon className="h-4 w-4" />
                      </div>
                      <span className="font-mono text-xs uppercase tracking-[0.16em]">{label}</span>
                    </div>
                    <span className="text-sm font-semibold text-foreground/80">{value}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </motion.div>

        <section className="grid gap-5 md:grid-cols-3">
          {pillars.map(({ icon: Icon, title, description }, index) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: 0.1 + index * 0.08 }}
            >
              <Card className="panel-surface h-full">
                <CardHeader>
                  <div className="mb-2 inline-flex h-12 w-12 items-center justify-center rounded-2xl border border-primary/30 bg-primary/12 text-primary shadow-orange-glow">
                    <Icon className="h-5 w-5" />
                  </div>
                  <CardTitle>{title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm leading-7 text-muted-foreground">{description}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </section>
      </div>
    </main>
  );
}
