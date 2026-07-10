import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { authFetch, type Week } from "../lib/api";

const STATUS_LABELS: Record<string, string> = {
  not_started: "Not started",
  in_progress: "In progress",
  done: "Done",
  late: "Late",
  skipped: "Skipped",
};

async function fetchWeek(number: number): Promise<Week> {
  return authFetch<Week>(`/api/weeks/${number}`);
}

export default function WeekDetailPage() {
  const navigate = useNavigate();
  const { number = "0" } = useParams<{ number: string }>();
  const weekNumber = parseInt(number, 10);

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
          <span className="text-gray-500">(part of "{week.week_label}")</span>
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
            <span className="text-gray-500">Logged:</span> {week.actual_hours}h
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