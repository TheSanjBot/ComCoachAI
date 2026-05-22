"use client";

import Link from "next/link";
import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { RecordingStudio } from "@/components/studio/recording-studio";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/use-auth";
import { getModeConfig, isModeSlug, isRecordingModeSlug } from "@/lib/mode-config";
import { cn } from "@/lib/utils";

export default function StudioPage() {
  return (
    <Suspense fallback={null}>
      <StudioPageContent />
    </Suspense>
  );
}

function StudioPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { session, status } = useAuth();
  const rawMode = searchParams.get("mode");
  const nextPath = rawMode ? `/studio?mode=${encodeURIComponent(rawMode)}` : "/studio";

  useEffect(() => {
    if (status === "unauthenticated") {
      router.replace(`/login?next=${encodeURIComponent(nextPath)}`);
    }
  }, [nextPath, router, status]);

  if (status === "loading") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background">
        <div className="rounded-full border border-white/10 bg-white/[0.05] px-5 py-3 font-mono text-sm font-medium uppercase tracking-[0.2em] text-muted-foreground shadow-orange-glow">
          Preparing your recording studio...
        </div>
      </main>
    );
  }

  if (status !== "authenticated" || !session) {
    return null;
  }

  if (!isModeSlug(rawMode)) {
    return (
      <StudioFallback
        title="Choose a valid training mode first"
        description="Recording is only available when you launch the studio from Interview Training or Public Speaking."
      />
    );
  }

  if (!isRecordingModeSlug(rawMode)) {
    const config = getModeConfig(rawMode);
    return (
      <StudioFallback
        title={config.studioTitle}
        description={config.studioDescription}
      />
    );
  }

  return <RecordingStudio mode={rawMode} token={session.access_token} />;
}

function StudioFallback({ title, description }: { title: string; description: string }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-6">
      <Card className="panel-glass w-full max-w-2xl">
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>
          <Link href="/" className={cn(buttonVariants({ variant: "outline" }))}>
            Return home
          </Link>
        </CardContent>
      </Card>
    </main>
  );
}
