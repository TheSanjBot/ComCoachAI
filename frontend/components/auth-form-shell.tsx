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
    <main className="relative min-h-screen overflow-hidden bg-[radial-gradient(circle_at_top_left,_rgba(228,163,88,0.22),_transparent_28%),radial-gradient(circle_at_bottom_right,_rgba(18,110,130,0.18),_transparent_30%),linear-gradient(145deg,_#f8f4ec_0%,_#eef6f4_45%,_#dceae7_100%)] px-6 py-10">
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.16)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.16)_1px,transparent_1px)] bg-[size:40px_40px] opacity-35" />
      <div className="relative mx-auto grid min-h-[calc(100vh-5rem)] max-w-6xl items-center gap-10 lg:grid-cols-[1.08fr_0.92fr]">
        <section className="space-y-7">
          <div className="space-y-5">
            <h1 className="max-w-2xl text-4xl font-semibold leading-tight text-foreground sm:text-6xl">
              Build confident communication with interview, speaking, and resume coaching in one workspace.
            </h1>
            <p className="max-w-xl text-base leading-8 text-muted-foreground sm:text-lg">
              Practice with video, get structured feedback, and come back to a polished coaching
              dashboard that keeps your progress visible.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-[2rem] border border-white/65 bg-white/72 p-5 shadow-halo backdrop-blur">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">
                Interview coaching
              </p>
              <p className="mt-3 text-lg font-semibold text-foreground">
                Practice technical answers with staged AI review.
              </p>
            </div>
            <div className="rounded-[2rem] border border-white/65 bg-white/72 p-5 shadow-halo backdrop-blur">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">
                Speaking feedback
              </p>
              <p className="mt-3 text-lg font-semibold text-foreground">
                Improve delivery, body language, and factual clarity.
              </p>
            </div>
          </div>
        </section>

        <Card className="border-white/70 bg-white/88 shadow-[0_32px_120px_rgba(22,52,58,0.16)]">
          <CardHeader>
            <CardTitle>{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {children}
            <p className="text-sm text-muted-foreground">
              {footerCopy}{" "}
              <Link href={footerHref} className="font-semibold text-foreground underline-offset-4 hover:underline">
                {footerLinkLabel}
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
