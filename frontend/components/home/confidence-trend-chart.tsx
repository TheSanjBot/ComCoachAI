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
          <CartesianGrid strokeDasharray="3 3" stroke="#d8d2c9" vertical={false} />
          <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fill: "#577176", fontSize: 12 }} />
          <YAxis tickLine={false} axisLine={false} domain={[0, 100]} tick={{ fill: "#577176", fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              borderRadius: 16,
              border: "1px solid rgba(55, 96, 102, 0.12)",
              backgroundColor: "rgba(255, 255, 255, 0.95)",
              boxShadow: "0 24px 80px rgba(26, 46, 51, 0.16)"
            }}
          />
          <Bar
            dataKey="communication_score"
            barSize={18}
            radius={[8, 8, 0, 0]}
            fill="#d7a277"
            name="Communication"
          />
          <Line
            type="monotone"
            dataKey="confidence_score"
            stroke="#376066"
            strokeWidth={3}
            dot={{ r: 4, fill: "#376066", strokeWidth: 0 }}
            name="Confidence"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
