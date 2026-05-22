"use client";

import { useState } from "react";

import { login, signup } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";

interface AuthPanelProps {
  onAuthenticated: (token: string) => Promise<void> | void;
}

export function AuthPanel({ onAuthenticated }: AuthPanelProps) {
  const [mode, setMode] = useState<"login" | "signup">("signup");
  const [form, setForm] = useState({
    email: "",
    full_name: "",
    password: ""
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit() {
    try {
      setLoading(true);
      setError(null);

      if (mode === "signup") {
        await signup(form);
      }

      const response = await login({
        email: form.email,
        password: form.password
      });
      await onAuthenticated(response.access_token);
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Unable to authenticate."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="panel-glass border-white/10 shadow-panel-glow">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <CardTitle>Coach Access</CardTitle>
          <CardDescription>
            Sign in to save reports, track weaknesses, and personalize coaching.
          </CardDescription>
        </div>
        <div className="rounded-full bg-secondary/70 p-1">
          <button
            className={`rounded-full border px-3 py-1.5 font-mono text-xs uppercase tracking-[0.16em] transition-all duration-200 ${mode === "signup" ? "border-primary bg-primary/15 text-primary shadow-orange-glow" : "border-white/10 bg-white/[0.03] text-muted-foreground hover:border-white/20 hover:text-foreground"}`}
            onClick={() => setMode("signup")}
            type="button"
          >
            Sign up
          </button>
          <button
            className={`rounded-full border px-3 py-1.5 font-mono text-xs uppercase tracking-[0.16em] transition-all duration-200 ${mode === "login" ? "border-primary bg-primary/15 text-primary shadow-orange-glow" : "border-white/10 bg-white/[0.03] text-muted-foreground hover:border-white/20 hover:text-foreground"}`}
            onClick={() => setMode("login")}
            type="button"
          >
            Login
          </button>
        </div>
      </div>

      <div className="grid gap-3">
        <input
          className="h-12 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-foreground outline-none transition-all duration-200 placeholder:text-white/30 focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/30"
          onChange={(event) =>
            setForm((current) => ({ ...current, email: event.target.value }))
          }
          placeholder="Email"
          type="email"
          value={form.email}
        />
        {mode === "signup" && (
          <input
            className="h-12 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-foreground outline-none transition-all duration-200 placeholder:text-white/30 focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/30"
            onChange={(event) =>
              setForm((current) => ({ ...current, full_name: event.target.value }))
            }
            placeholder="Full name"
            type="text"
            value={form.full_name}
          />
        )}
        <input
          className="h-12 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-foreground outline-none transition-all duration-200 placeholder:text-white/30 focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/30"
          onChange={(event) =>
            setForm((current) => ({ ...current, password: event.target.value }))
          }
          placeholder="Password"
          type="password"
          value={form.password}
        />
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        <Button disabled={loading} onClick={handleSubmit} type="button">
          {loading ? "Working..." : mode === "signup" ? "Create account" : "Login"}
        </Button>
      </div>
    </Card>
  );
}
