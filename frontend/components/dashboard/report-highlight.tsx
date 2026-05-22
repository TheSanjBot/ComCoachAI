import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import type { Report } from "@/types";

export function ReportHighlight({ report }: { report: Report | null }) {
  return (
    <Card className="h-full bg-primary text-primary-foreground">
      <CardTitle className="text-primary-foreground">Coaching Snapshot</CardTitle>
      <CardDescription className="mt-2 text-primary-foreground/80">
        Most recent strengths, weak signals, and next-step coaching.
      </CardDescription>
      {report ? (
        <div className="mt-6 space-y-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-primary-foreground/70">
              Summary
            </p>
            <p className="mt-2 text-lg leading-7">{report.summary}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-primary-foreground/70">
              Strengths
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {report.strengths.map((strength) => (
                <span
                  className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-1 font-mono text-xs uppercase tracking-[0.14em] text-foreground/85"
                  key={strength}
                >
                  {strength}
                </span>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-primary-foreground/70">
              Next Coaching Moves
            </p>
            <ul className="mt-2 space-y-2 text-sm leading-6 text-primary-foreground/90">
              {report.coaching_tips.slice(0, 3).map((tip) => (
                <li key={tip}>{tip}</li>
              ))}
            </ul>
          </div>
        </div>
      ) : (
        <p className="mt-6 text-sm text-primary-foreground/85">
          Complete one session to generate a full coaching snapshot here.
        </p>
      )}
    </Card>
  );
}
