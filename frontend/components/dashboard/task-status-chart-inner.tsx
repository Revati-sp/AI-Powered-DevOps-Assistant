"use client";

import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { DashboardTaskCounts } from "@/features/dashboard/api";

const STATUS_COLORS: Record<keyof DashboardTaskCounts, string> = {
  queued: "var(--chart-4)",
  running: "var(--chart-2)",
  succeeded: "var(--chart-1)",
  failed: "var(--chart-5)",
};

export function TaskStatusChartInner({ counts }: { counts: DashboardTaskCounts }) {
  const data = (Object.entries(counts) as [keyof DashboardTaskCounts, number][]).map(
    ([status, value]) => ({
      status,
      value,
      fill: STATUS_COLORS[status],
    }),
  );

  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <XAxis dataKey="status" tickLine={false} axisLine={false} tick={{ fontSize: 12 }} />
          <YAxis
            allowDecimals={false}
            tickLine={false}
            axisLine={false}
            width={28}
            tick={{ fontSize: 12 }}
          />
          <Tooltip
            cursor={{ fill: "var(--muted)" }}
            contentStyle={{
              borderRadius: 8,
              border: "1px solid var(--border)",
              background: "var(--card)",
            }}
          />
          <Bar dataKey="value" radius={[6, 6, 0, 0]}>
            {data.map((entry) => (
              <Cell key={entry.status} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
