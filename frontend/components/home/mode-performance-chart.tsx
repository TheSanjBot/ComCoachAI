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
          <CartesianGrid strokeDasharray="3 3" stroke="#d8d2c9" vertical={false} />
          <XAxis dataKey="title" tickLine={false} axisLine={false} tick={{ fill: "#577176", fontSize: 12 }} />
          <YAxis tickLine={false} axisLine={false} domain={[0, 100]} tick={{ fill: "#577176", fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              borderRadius: 16,
              border: "1px solid rgba(55, 96, 102, 0.12)",
              backgroundColor: "rgba(255, 255, 255, 0.95)",
              boxShadow: "0 24px 80px rgba(26, 46, 51, 0.16)"
            }}
          />
          <Bar dataKey="average_overall_score" radius={[10, 10, 0, 0]} fill="#376066" name="Overall" />
          <Bar dataKey="average_confidence_score" radius={[10, 10, 0, 0]} fill="#d7a277" name="Confidence" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
