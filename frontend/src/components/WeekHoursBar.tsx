import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  Cell,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { authFetch, type WeekAggregate } from "../lib/api";
import { useT } from "../lib/i18n";

async function fetchAggregate(weekId: number): Promise<WeekAggregate> {
  return authFetch<WeekAggregate>(`/api/sessions/aggregate?week_id=${weekId}`);
}

/**
 * Hours bar vs the roadmap plan range [min, max].
 *  - green when actual is within the range
 *  - yellow when under the minimum
 *  - red when over the cap (burnout warning)
 */
export function WeekHoursBar({ weekId }: { weekId: number }) {
  const t = useT();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["aggregate", weekId],
    queryFn: () => fetchAggregate(weekId),
    enabled: weekId > 0,
  });

  if (isLoading)
    return <p className="text-sm text-gray-500">{t("hours_bar.loading")}</p>;
  if (isError || !data)
    return <p className="text-sm text-red-600">{t("hours_bar.error")}</p>;

  const barColor = data.over_cap
    ? "#dc2626"
    : data.under_min
      ? "#eab308"
      : "#16a34a";

  // Cap the chart's Y axis to a sensible ceiling (max + 50% headroom).
  const yMax = Math.max(data.hours_max * 1.5, data.actual_hours + 5);

  const chartData = [{ name: t("hours_bar.week_label", { id: weekId }), hours: data.actual_hours }];

  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-4 space-y-2">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold">{t("hours_bar.heading", { id: weekId })}</h2>
        <span
          className="px-2 py-0.5 text-xs rounded-full"
          style={{
            backgroundColor: barColor + "22",
            color: barColor,
          }}
        >
          {data.actual_hours}h / {data.hours_min}-{data.hours_max}h
        </span>
      </div>

      <div className="h-44">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 8, left: -20 }}>
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis domain={[0, yMax]} tick={{ fontSize: 12 }} />
            <Tooltip
              formatter={(v: number) => [`${v}h`, t("hours_bar.tooltip_logged")]}
              contentStyle={{ fontSize: 12 }}
            />
            {/* Plan range band (green zone behind the bar) */}
            <ReferenceArea
              y1={data.hours_min}
              y2={data.hours_max}
              fill="#16a34a"
              fillOpacity={0.15}
            />
            <Bar dataKey="hours" radius={[4, 4, 0, 0]}>
              {chartData.map((_, idx) => (
                <Cell key={idx} fill={barColor} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <p className="text-xs text-gray-500">
        {data.over_cap
          ? t("hours_bar.over_cap_message")
          : data.under_min
            ? t("hours_bar.under_min_message")
            : t("hours_bar.on_track_message")}
      </p>
    </div>
  );
}