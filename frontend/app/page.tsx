"use client";

import { useEffect, useState } from "react";

import { AuthenticatedHome } from "@/components/home/authenticated-home";
import { PublicHome } from "@/components/home/public-home";
import { clearSession } from "@/lib/auth";
import { fetchDashboardOverview, type DashboardOverview } from "@/lib/dashboard";
import { useAuth } from "@/hooks/use-auth";

export default function HomePage() {
  const { session, status, setSession, setStatus, signOut } = useAuth();
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [loadingOverview, setLoadingOverview] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    if (status !== "authenticated" || !session) {
      if (status === "unauthenticated") {
        setOverview(null);
      }
      return;
    }

    setLoadingOverview(true);
    fetchDashboardOverview(session.access_token)
      .then((payload) => {
        setOverview(payload);
        setNotice(null);
      })
      .catch((error) => {
        clearSession();
        setSession(null);
        setStatus("unauthenticated");
        setOverview(null);
        setNotice(
          error instanceof Error
            ? `${error.message} Please sign in again to continue.`
            : "Your session expired. Please sign in again."
        );
      })
      .finally(() => setLoadingOverview(false));
  }, [session, setSession, setStatus, status]);

  if (status === "loading" || (status === "authenticated" && loadingOverview && !overview)) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[linear-gradient(135deg,_#f7f2ea_0%,_#eef3f3_45%,_#e0ebe8_100%)]">
        <div className="rounded-full border border-foreground/10 bg-white/70 px-5 py-3 text-sm font-medium text-foreground/70 shadow-halo">
          Preparing your CommCoach AI home dashboard...
        </div>
      </main>
    );
  }

  if (status === "authenticated" && overview) {
    return <AuthenticatedHome overview={overview} onSignOut={signOut} />;
  }

  return <PublicHome notice={notice} />;
}
