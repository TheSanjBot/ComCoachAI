"use client";

import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import type { ConfidenceTrendPoint } from "@/lib/dashboard";

type ConfidenceTrendChartProps = {
  data: ConfidenceTrendPoint[];
};

export function ConfidenceTrendChart({ data }: ConfidenceTrendChartProps) {
  return (
    <div className="h-[260px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.18)" vertical={false} />
          <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fill: "#94A3B8", fontSize: 12 }} />
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
          <Bar
            dataKey="communication_score"
            barSize={18}
            radius={[8, 8, 0, 0]}
            fill="#F7931A"
            name="Communication"
          />
          <Line
            type="monotone"
            dataKey="confidence_score"
            stroke="#FFD600"
            strokeWidth={3}
            dot={{ r: 4, fill: "#FFD600", strokeWidth: 0 }}
            name="Confidence"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
