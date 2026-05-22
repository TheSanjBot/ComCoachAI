"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import type { ModePerformancePoint } from "@/lib/dashboard";

export function ModePerformanceChart({ data }: { data: ModePerformancePoint[] }) {
  return (
    <div className="h-[260px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.18)" vertical={false} />
          <XAxis dataKey="title" tickLine={false} axisLine={false} tick={{ fill: "#94A3B8", fontSize: 12 }} />
          <YAxis tickLine={false} axisLine={false} domain={[0, 100]} tick={{ fill: "#94A3B8", fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              borderRadius: 16,
              border: "1px solid rgba(247, 147, 26, 0.22)",
              backgroundColor: "rgba(15, 17, 21, 0.96)",
              color: "#FFFFFF",
              boxShadow: "0 0 30px -8px rgba(247, 147, 26, 0.25)"
            }}
          />
          <Bar dataKey="average_overall_score" radius={[10, 10, 0, 0]} fill="#EA580C" name="Overall" />
          <Bar dataKey="average_confidence_score" radius={[10, 10, 0, 0]} fill="#FFD600" name="Confidence" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
