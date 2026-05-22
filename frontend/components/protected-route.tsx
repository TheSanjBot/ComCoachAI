"use client";

import type { ReactNode } from "react";
import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import { useAuth } from "@/hooks/use-auth";

type ProtectedRouteProps = {
  children: ReactNode;
};

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { status } = useAuth();

  useEffect(() => {
    if (status === "unauthenticated") {
      const nextPath = pathname ? `?next=${encodeURIComponent(pathname)}` : "";
      router.replace(`/login${nextPath}`);
    }
  }, [pathname, router, status]);

  if (status === "loading") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[linear-gradient(135deg,_#f7f2ea_0%,_#eef3f3_45%,_#e0ebe8_100%)]">
        <div className="rounded-full border border-white/10 bg-white/[0.05] px-5 py-3 font-mono text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground shadow-orange-glow">
          Securing your coaching workspace...
        </div>
      </main>
    );
  }

  if (status === "unauthenticated") {
    return null;
  }

  return <>{children}</>;
}
