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
      <main className="flex min-h-screen items-center justify-center bg-[linear-gradient(135deg,_#f7f2ea_0%,_#eef3f3_45%,_#e0ebe8_100%)]">
        <div className="rounded-full border border-foreground/10 bg-white/70 px-5 py-3 text-sm font-medium text-foreground/70 shadow-halo">
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
    <main className="flex min-h-screen items-center justify-center bg-[linear-gradient(135deg,_#f7f2ea_0%,_#eef3f3_45%,_#e0ebe8_100%)] px-6">
      <Card className="w-full max-w-2xl border-white/70 bg-white/84">
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
