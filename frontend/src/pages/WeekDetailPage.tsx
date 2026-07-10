import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { authFetch, type Phase, type Week } from "../lib/api";
import { useT } from "../lib/i18n";
import { LogSessionForm } from "../components/LogSessionForm";
import { WeekHoursBar } from "../components/WeekHoursBar";

async function fetchWeek(number: number): Promise<Week> {
  return authFetch<Week>(`/api/weeks/${number}`);
}

async function fetchAllWeeks(): Promise<Week[]> {
  const phases = await authFetch<Phase[]>("/api/weeks");
  return phases.flatMap((p) => p.weeks);
}

export default function WeekDetailPage() {
  const navigate = useNavigate();
  const t = useT();
  const { number = "0" } = useParams<{ number: string }>();
  const weekNumber = parseInt(number, 10);

  function statusLabel(status: string): string {
    return t(`status.${status}`);
  }

  const { data: week, isLoading, isError } = useQuery({
    queryKey: ["week", weekNumber],
    queryFn: () => fetchWeek(weekNumber),
    enabled: weekNumber > 0,
  });
  const { data: allWeeks } = useQuery({
    queryKey: ["phases"],
    queryFn: fetchAllWeeks,
  });

  if (isLoading)
    return <div className="p-8 text-gray-500">{t("week_detail.loading")}</div>;
  if (isError || !week)
    return <div className="p-8 text-red-600">{t("week_detail.error_not_found")}</div>;

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-4">
      <button
        onClick={() => navigate("/")}
        className="text-blue-600 hover:underline text-sm"
      >
        {t("week_detail.back_link")}
      </button>

      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold">{t("week_detail.heading", { number: week.number })}</h1>
        {week.week_label && week.week_label !== String(week.number) && (
          <span className="text-gray-500">{t("week_detail.part_of_label", { label: week.week_label })}</span>
        )}
        {week.buffer && (
          <span className="px-2 py-0.5 text-xs rounded-full bg-orange-100 text-orange-700">
            {t("week_detail.buffer_badge")}
          </span>
        )}
      </div>

      <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-4 space-y-3">
        <div>
          <h2 className="font-semibold text-gray-700 dark:text-gray-300">
            {t("week_detail.theme_heading")}
          </h2>
          <p className="mt-1">{week.theme}</p>
        </div>

        <div>
          <h2 className="font-semibold text-gray-700 dark:text-gray-300">
            {t("week_detail.resources_heading")}
          </h2>
          <p className="mt-1 whitespace-pre-wrap">{week.resources}</p>
        </div>

        <div>
          <h2 className="font-semibold text-gray-700 dark:text-gray-300">
            {t("week_detail.deliverable_heading")}
          </h2>
          <p className="mt-1">{week.deliverable}</p>
        </div>

        <div className="flex gap-6 text-sm">
          <div>
            <span className="text-gray-500">{t("week_detail.target_label")}</span>{" "}
            {week.hours_min}-{week.hours_max}h
          </div>
          <div>
            <span className="text-gray-500">{t("week_detail.logged_label")}</span> {week.actual_hours}h
          </div>
          <div>
            <span className="text-gray-500">{t("week_detail.status_label")}</span>{" "}
            {statusLabel(week.status)}
          </div>
        </div>

        {week.recap_sunday && (
          <div>
            <h2 className="font-semibold text-gray-700 dark:text-gray-300">
              {t("week_detail.sunday_recap_heading")}
            </h2>
            <p className="mt-1 whitespace-pre-wrap">{week.recap_sunday}</p>
          </div>
        )}
      </div>

      {/* M3: hours visualization + manual log form */}
      <WeekHoursBar weekId={weekNumber} />

      {allWeeks && allWeeks.length > 0 && (
        <LogSessionForm weeks={allWeeks} defaultWeek={weekNumber} />
      )}
    </div>
  );
}