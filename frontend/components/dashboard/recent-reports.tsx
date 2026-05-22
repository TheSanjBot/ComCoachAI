import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import type { Report } from "@/types";

export function RecentReports({ reports }: { reports: Report[] }) {
  return (
    <Card>
      <CardTitle>Recent Reports</CardTitle>
      <CardDescription className="mt-2">
        Latest coaching outcomes across interview, public speaking, and resume workflows.
      </CardDescription>

      <div className="mt-6 space-y-5">
        {reports.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Your first saved report will appear here.
          </p>
        ) : (
          reports.map((report) => (
            <div key={report.report_id} className="rounded-3xl bg-secondary/40 p-4">
              <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="text-sm uppercase tracking-[0.2em] text-muted-foreground">
                    {report.mode.replace("_", " ")}
                  </p>
                  <p className="mt-1 font-medium">{report.summary}</p>
                </div>
                <p className="text-2xl font-semibold">{Math.round(report.overall_score)}</p>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-3">
                <div>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                    Communication
                  </p>
                  <Progress value={report.communication_score} />
                </div>
                <div>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                    Confidence
                  </p>
                  <Progress value={report.confidence_score} />
                </div>
                <div>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                    Technical
                  </p>
                  <Progress value={report.technical_score ?? 0} />
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}

