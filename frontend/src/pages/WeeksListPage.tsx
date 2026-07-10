import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { authFetch, type Phase, type Week } from "../lib/api";
import { useT } from "../lib/i18n";

async function fetchPhases(): Promise<Phase[]> {
  return authFetch<Phase[]>("/api/weeks");
}

export default function WeeksListPage() {
  const navigate = useNavigate();
  const t = useT();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["phases"],
    queryFn: fetchPhases,
  });

  if (isLoading)
    return <div className="p-8 text-gray-500">{t("weeks_list.loading")}</div>;
  if (isError)
    return <div className="p-8 text-red-600">{t("weeks_list.error")}</div>;

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-4">
      <h1 className="text-2xl font-bold">{t("weeks_list.heading")}</h1>
      <p className="text-gray-600 dark:text-gray-400">
        {t("weeks_list.help_text")}
      </p>

      {data!.map((phase) => (
        <PhaseAccordion key={phase.id} phase={phase} onWeekClick={(n) => navigate(`/weeks/${n}`)} />
      ))}
    </div>
  );
}

const STATUS_STYLES: Record<string, string> = {
  not_started: "bg-gray-300",
  in_progress: "bg-yellow-400",
  done: "bg-green-500",
  late: "bg-red-500",
  skipped: "bg-gray-400",
};

function PhaseAccordion({
  phase,
  onWeekClick,
}: {
  phase: Phase;
  onWeekClick: (n: number) => void;
}) {
  const t = useT();
  function statusLabel(status: string): string {
    return t(`status.${status}`);
  }
  return (
    <details
      className="group rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden"
      open
    >
      <summary className="cursor-pointer select-none px-4 py-3 bg-gray-100 dark:bg-gray-800 font-semibold flex items-center justify-between">
        <span>{phase.title}</span>
        <span className="text-sm text-gray-500">
          {t("weeks_list.phase_weeks_count", { count: phase.weeks.length })}
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
            <th className="px-3 py-2">{t("weeks_list.col_number")}</th>
            <th className="px-3 py-2">{t("weeks_list.col_theme")}</th>
            <th className="px-3 py-2 text-center">{t("weeks_list.col_status")}</th>
            <th className="px-3 py-2 text-right">{t("weeks_list.col_hours")}</th>
            <th className="px-3 py-2 text-center">{t("weeks_list.col_buffer")}</th>
          </tr>
        </thead>
        <tbody>
          {phase.weeks.map((w: Week) => (
            <tr
              key={w.number}
              role="button"
              tabIndex={0}
              onClick={() => onWeekClick(w.number)}
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
                  title={statusLabel(w.status)}
                />
              </td>
              <td className="px-3 py-2 text-right text-gray-600 dark:text-gray-400">
                {w.hours_min}-{w.hours_max}h
                {w.actual_hours > 0 && (
                  <span className="ml-1 text-green-600">
                    {t("weeks_list.hours_done_badge", { hours: w.actual_hours })}
                  </span>
                )}
              </td>
              <td className="px-3 py-2 text-center">
                {w.buffer ? (
                  <span className="text-orange-500" title={t("weeks_list.buffer_tooltip")}>
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