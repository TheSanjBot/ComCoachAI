"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import { Card, CardDescription, CardTitle } from "@/components/ui/card";

export function PerformanceChart({
  data
}: {
  data: Array<{
    sessionId: number;
    confidence: number;
    communication: number;
    overall: number;
    mode: string;
  }>;
}) {
  return (
    <Card className="h-full">
      <CardTitle>Progress Trend</CardTitle>
      <CardDescription className="mb-5 mt-2">
        Confidence, communication, and overall coaching scores across recent sessions.
      </CardDescription>
      <div className="h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#dfddd5" />
            <XAxis dataKey="sessionId" stroke="#6b6f68" />
            <YAxis stroke="#6b6f68" />
            <Tooltip />
            <Legend />
            <Line
              dataKey="communication"
              dot={false}
              stroke="#0f4a45"
              strokeWidth={3}
              type="monotone"
            />
            <Line
              dataKey="confidence"
              dot={false}
              stroke="#f09f45"
              strokeWidth={3}
              type="monotone"
            />
            <Line
              dataKey="overall"
              dot={false}
              stroke="#244a9a"
              strokeWidth={3}
              type="monotone"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

