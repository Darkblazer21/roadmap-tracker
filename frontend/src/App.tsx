import { Routes, Route, Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

// --- Types matching the backend Pydantic schemas ---

type WeekStatus =
  | "not_started"
  | "in_progress"
  | "done"
  | "late"
  | "skipped";

interface Week {
  number: number;
  phase_id: number;
  theme: string;
  resources: string;
  deliverable: string;
  hours_min: number;
  hours_max: number;
  buffer: boolean;
  week_label: string | null;
  status: WeekStatus;
  actual_hours: number;
  recap_sunday: string | null;
  reviewed_at: string | null;
}

interface Phase {
  id: number;
  key: string;
  title: string;
  position: number;
  subtitle: string | null;
  notes: string | null;
  weeks: Week[];
}

// --- API fetchers ---

async function fetchPhases(): Promise<Phase[]> {
  const res = await fetch("/api/weeks");
  if (!res.ok) throw new Error("Failed to load phases");
  return res.json();
}

async function fetchWeek(number: number): Promise<Week> {
  const res = await fetch(`/api/weeks/${number}`);
  if (!res.ok) throw new Error("Failed to load week");
  return res.json();
}

// --- UI helpers ---

const STATUS_STYLES: Record<WeekStatus, string> = {
  not_started: "bg-gray-300",
  in_progress: "bg-yellow-400",
  done: "bg-green-500",
  late: "bg-red-500",
  skipped: "bg-gray-400",
};

const STATUS_LABELS: Record<WeekStatus, string> = {
  not_started: "Not started",
  in_progress: "In progress",
  done: "Done",
  late: "Late",
  skipped: "Skipped",
};

// --- Pages ---

function WeeksListPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["phases"],
    queryFn: fetchPhases,
  });

  if (isLoading)
    return (
      <div className="p-8 text-gray-500">Loading weeks...</div>
    );
  if (isError)
    return (
      <div className="p-8 text-red-600">Failed to load weeks.</div>
    );

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-4">
      <h1 className="text-2xl font-bold">Roadmap Weeks</h1>
      <p className="text-gray-600 dark:text-gray-400">
        Click a week to see its details.
      </p>

      {data!.map((phase) => (
        <PhaseAccordion key={phase.id} phase={phase} />
      ))}
    </div>
  );
}

function PhaseAccordion({ phase }: { phase: Phase }) {
  return (
    <details className="group rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden" open>
      <summary className="cursor-pointer select-none px-4 py-3 bg-gray-100 dark:bg-gray-800 font-semibold flex items-center justify-between">
        <span>{phase.title}</span>
        <span className="text-sm text-gray-500">
          {phase.weeks.length} weeks
        </span>
      </summary>

      {phase.notes && (
        <div className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700 bg-yellow-50 dark:bg-gray-900/50">
          <pre className="whitespace-pre-wrap font-sans">{phase.notes}</pre>
        </div>
      )}

      <table className="w-full text-sm">
        <thead>
          <tr className="text-left border-b border-gray-200 dark:border-gray-700">
            <th className="px-3 py-2">#</th>
            <th className="px-3 py-2">Theme</th>
            <th className="px-3 py-2 text-center">Status</th>
            <th className="px-3 py-2 text-right">Hours</th>
            <th className="px-3 py-2 text-center">Buffer</th>
          </tr>
        </thead>
        <tbody>
          {phase.weeks.map((w) => (
            <tr
              key={w.number}
              className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer"
            >
              <td className="px-3 py-2 font-mono font-bold">
                <Link to={`/weeks/${w.number}`} className="text-blue-600 hover:underline">
                  {w.number}
                </Link>
              </td>
              <td className="px-3 py-2">{w.theme}</td>
              <td className="px-3 py-2 text-center">
                <span
                  className={`inline-block h-3 w-3 rounded-full ${STATUS_STYLES[w.status]}`}
                  title={STATUS_LABELS[w.status]}
                />
              </td>
              <td className="px-3 py-2 text-right text-gray-600 dark:text-gray-400">
                {w.hours_min}-{w.hours_max}h
                {w.actual_hours > 0 && (
                  <span className="ml-1 text-green-600">
                    ({w.actual_hours}h done)
                  </span>
                )}
              </td>
              <td className="px-3 py-2 text-center">
                {w.buffer ? (
                  <span className="text-orange-500" title="Buffer week">
                    ⚠
                  </span>
                ) : (
                  ""
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </details>
  );
}

function WeekDetailPage() {
  const navigate = useNavigate();
  // Extract week number from the URL path `/weeks/:number`
  const match = window.location.pathname.match(/\/weeks\/(\d+)/);
  const weekNumber = match ? parseInt(match[1], 10) : 0;

  const { data: week, isLoading, isError } = useQuery({
    queryKey: ["week", weekNumber],
    queryFn: () => fetchWeek(weekNumber),
    enabled: weekNumber > 0,
  });

  if (isLoading)
    return <div className="p-8 text-gray-500">Loading week...</div>;
  if (isError || !week)
    return <div className="p-8 text-red-600">Week not found.</div>;

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-4">
      <button
        onClick={() => navigate("/")}
        className="text-blue-600 hover:underline text-sm"
      >
        ← Back to all weeks
      </button>

      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold">Week {week.number}</h1>
        {week.week_label && week.week_label !== String(week.number) && (
          <span className="text-gray-500">
            (part of "{week.week_label}")
          </span>
        )}
        {week.buffer && (
          <span className="px-2 py-0.5 text-xs rounded-full bg-orange-100 text-orange-700">
            Buffer week
          </span>
        )}
      </div>

      <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-4 space-y-3">
        <div>
          <h2 className="font-semibold text-gray-700 dark:text-gray-300">
            Theme
          </h2>
          <p className="mt-1">{week.theme}</p>
        </div>

        <div>
          <h2 className="font-semibold text-gray-700 dark:text-gray-300">
            Resources
          </h2>
          <p className="mt-1 whitespace-pre-wrap">{week.resources}</p>
        </div>

        <div>
          <h2 className="font-semibold text-gray-700 dark:text-gray-300">
            Deliverable
          </h2>
          <p className="mt-1">{week.deliverable}</p>
        </div>

        <div className="flex gap-6 text-sm">
          <div>
            <span className="text-gray-500">Target:</span>{" "}
            {week.hours_min}-{week.hours_max}h
          </div>
          <div>
            <span className="text-gray-500">Logged:</span>{" "}
            {week.actual_hours}h
          </div>
          <div>
            <span className="text-gray-500">Status:</span>{" "}
            {STATUS_LABELS[week.status]}
          </div>
        </div>

        {week.recap_sunday && (
          <div>
            <h2 className="font-semibold text-gray-700 dark:text-gray-300">
              Sunday Recap
            </h2>
            <p className="mt-1 whitespace-pre-wrap">{week.recap_sunday}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<WeeksListPage />} />
      <Route path="/weeks/:number" element={<WeekDetailPage />} />
    </Routes>
  );
}