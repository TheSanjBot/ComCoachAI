import type { ReactNode } from "react";
import Link from "next/link";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type AuthFormShellProps = {
  title: string;
  description: string;
  footerCopy: string;
  footerHref: string;
  footerLinkLabel: string;
  children: ReactNode;
};

export function AuthFormShell({
  title,
  description,
  footerCopy,
  footerHref,
  footerLinkLabel,
  children
}: AuthFormShellProps) {
  return (
    <main className="relative min-h-screen overflow-hidden bg-background px-6 py-10">
      <div className="pointer-events-none absolute inset-0 bg-grid-pattern opacity-40" />
      <div className="relative mx-auto grid min-h-[calc(100vh-5rem)] max-w-6xl items-center gap-10 lg:grid-cols-[1.08fr_0.92fr]">
        <section className="space-y-7">
          <div className="space-y-5">
            <h1 className="max-w-2xl text-4xl font-semibold leading-tight text-foreground sm:text-6xl">
              Build confident communication in one <span className="text-gradient-gold">secure workspace.</span>
            </h1>
            <p className="max-w-xl text-base leading-8 text-muted-foreground sm:text-lg">
              Practice with video, get structured feedback, and come back to a polished coaching
              dashboard that keeps your progress visible.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="panel-glass rounded-[2rem] p-5">
              <p className="font-mono text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">
                Interview coaching
              </p>
              <p className="mt-3 text-lg font-semibold text-foreground">
                Practice technical answers with staged AI review.
              </p>
            </div>
            <div className="panel-glass rounded-[2rem] p-5">
              <p className="font-mono text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">
                Speaking feedback
              </p>
              <p className="mt-3 text-lg font-semibold text-foreground">
                Improve delivery, body language, and factual clarity.
              </p>
            </div>
          </div>
        </section>

        <Card className="panel-glass shadow-panel-glow">
          <CardHeader>
            <CardTitle>{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {children}
            <p className="text-sm text-muted-foreground">
              {footerCopy}{" "}
              <Link href={footerHref} className="font-semibold text-primary underline-offset-4 hover:underline">
                {footerLinkLabel}
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
