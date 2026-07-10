import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { authFetch } from "../lib/api";

interface DashboardData {
  calendar_week: number | null;
  current_week_theme: string | null;
  this_week: {
    total_hours: number;
    hours_min: number;
    hours_max: number;
    over_cap: boolean;
    under_min: boolean;
    in_range: boolean;
  } | null;
  last_7_days: {
    total_hours: number;
    active_days: number;
  };
  deviation: {
    status: string;
    message: string;
    calendar_week: number | null;
    first_incomplete_week: number | null;
    gap: number;
    tolerance: number;
    in_buffer: boolean;
  };
  week_counts: {
    done: number;
    in_progress: number;
    remaining: number;
    total: number;
  };
}

async function fetchDashboard(): Promise<DashboardData> {
  return authFetch<DashboardData>("/api/dashboard");
}

const DEVIATION_STYLES: Record<string, string> = {
  on_track: "bg-green-100 text-green-700 border-green-300",
  buffer: "bg-blue-100 text-blue-700 border-blue-300",
  slight_delay: "bg-yellow-100 text-yellow-700 border-yellow-300",
  behind: "bg-red-100 text-red-700 border-red-300",
  not_started: "bg-gray-100 text-gray-600 border-gray-300",
  complete: "bg-green-100 text-green-700 border-green-300",
  unknown: "bg-gray-100 text-gray-600 border-gray-300",
};

export default function DashboardPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["dashboard"],
    queryFn: fetchDashboard,
    staleTime: 60_000,
  });

  if (isLoading) return <div className="p-8 text-gray-500">Loading dashboard…</div>;
  if (isError || !data)
    return <div className="p-8 text-red-600">Failed to load dashboard.</div>;

  const dev = data.deviation;
  const wk = data.this_week;
  const progress =
    data.week_counts.total > 0
      ? Math.round((data.week_counts.done / data.week_counts.total) * 100)
      : 0;

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* Deviation banner */}
      <div className={`rounded-xl border p-4 ${DEVIATION_STYLES[dev.status] ?? DEVIATION_STYLES.unknown}`}>
        <p className="font-medium">{dev.message}</p>
      </div>

      {/* Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Current week"
          value={data.calendar_week ? `#${data.calendar_week}` : "—"}
          sub={data.current_week_theme?.slice(0, 40) ?? "Not started"}
        />
        <StatCard
          label="This week hours"
          value={wk ? `${wk.total_hours}h` : "—"}
          sub={wk ? `target ${wk.hours_min}-${wk.hours_max}h` : ""}
          color={wk?.over_cap ? "text-red-600" : wk?.under_min ? "text-yellow-600" : "text-green-600"}
        />
        <StatCard
          label="Last 7 days"
          value={`${data.last_7_days.total_hours}h`}
          sub={`${data.last_7_days.active_days} active day(s)`}
        />
        <StatCard
          label="Progress"
          value={`${progress}%`}
          sub={`${data.week_counts.done}/${data.week_counts.total} weeks done`}
        />
      </div>

      {/* Progress bar */}
      <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-semibold">Overall progress</span>
          <span className="text-sm text-gray-500">
            {data.week_counts.done} done · {data.week_counts.in_progress} active ·{" "}
            {data.week_counts.remaining} remaining
          </span>
        </div>
        <div className="h-4 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
          <div
            className="h-full bg-green-500 transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Quick actions */}
      <div className="flex flex-wrap gap-3">
        <Link to="/daily-log" className="rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 text-sm">
          Log today
        </Link>
        <Link to="/recap" className="rounded-lg bg-purple-600 hover:bg-purple-700 text-white font-semibold px-4 py-2 text-sm">
          Sunday recap
        </Link>
        <Link to="/github" className="rounded-lg bg-gray-700 hover:bg-gray-800 text-white font-semibold px-4 py-2 text-sm">
          GitHub check
        </Link>
        <a
          href="/api/export/all.json"
          className="rounded-lg bg-gray-200 hover:bg-gray-300 text-gray-800 dark:bg-gray-700 dark:text-gray-200 font-semibold px-4 py-2 text-sm"
        >
          Export JSON
        </a>
        <a
          href="/api/export/sessions.csv"
          className="rounded-lg bg-gray-200 hover:bg-gray-300 text-gray-800 dark:bg-gray-700 dark:text-gray-200 font-semibold px-4 py-2 text-sm"
        >
          Export CSV
        </a>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  sub,
  color,
}: {
  label: string;
  value: string;
  sub: string;
  color?: string;
}) {
  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-4">
      <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${color ?? ""}`}>{value}</p>
      <p className="text-xs text-gray-500 mt-1 truncate">{sub}</p>
    </div>
  );
}