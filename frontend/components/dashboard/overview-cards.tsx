import { Activity, Brain, Mic, ShieldCheck } from "lucide-react";

import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { formatScore } from "@/lib/utils";

export function OverviewCards({
  totalSessions,
  scores
}: {
  totalSessions: number;
  scores: {
    communication: number;
    technical: number;
    confidence: number;
    overall: number;
  };
}) {
  const items = [
    {
      label: "Communication",
      value: formatScore(scores.communication),
      caption: "Fluency, pacing, grammar",
      icon: Mic
    },
    {
      label: "Technical",
      value: formatScore(scores.technical),
      caption: "Reasoning, accuracy, depth",
      icon: Brain
    },
    {
      label: "Confidence",
      value: formatScore(scores.confidence),
      caption: "Presence, eye contact, posture",
      icon: ShieldCheck
    },
    {
      label: "Sessions",
      value: `${totalSessions}`,
      caption: "Recorded coaching history",
      icon: Activity
    }
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <Card key={item.label} className="panel-surface border-white/10 shadow-panel-glow">
            <div className="mb-3 flex items-center justify-between">
              <CardDescription>{item.label}</CardDescription>
              <span className="rounded-full bg-secondary p-2">
                <Icon className="h-4 w-4 text-primary" />
              </span>
            </div>
            <CardTitle className="text-3xl">{item.value}</CardTitle>
            <CardDescription className="mt-2">{item.caption}</CardDescription>
          </Card>
        );
      })}
    </div>
  );
}
