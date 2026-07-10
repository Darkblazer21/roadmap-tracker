import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { authFetch, type Phase, type Week } from "../lib/api";
import { useT } from "../lib/i18n";

/**
 * Daily log page: today-by-default form + scrollable history of logs for the
 * selected week. Uses an upsert endpoint so re-submitting a date replaces it.
 */

interface DailyLog {
  id: number;
  week_id: number;
  log_date: string;
  topic: string | null;
  learned: string | null;
  blockers: string | null;
  hours_override: number | null;
}

async function fetchWeeks(): Promise<Week[]> {
  const phases = await authFetch<Phase[]>("/api/weeks");
  return phases.flatMap((p) => p.weeks);
}

async function fetchLogs(weekId: number): Promise<DailyLog[]> {
  return authFetch<DailyLog[]>(`/api/daily-logs?week_id=${weekId}`);
}

function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function DailyLogPage() {
  const t = useT();
  const qc = useQueryClient();
  const [weekId, setWeekId] = useState<number>(1);
  const [date, setDate] = useState<string>(todayISO());
  const [topic, setTopic] = useState("");
  const [learned, setLearned] = useState("");
  const [blockers, setBlockers] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  const { data: weeks } = useQuery({ queryKey: ["phases"], queryFn: fetchWeeks });
  const { data: logs } = useQuery({
    queryKey: ["daily-logs", weekId],
    queryFn: () => fetchLogs(weekId),
  });

  const submit = useMutation({
    mutationFn: () =>
      authFetch<DailyLog>("/api/daily-logs", {
        method: "POST",
        body: JSON.stringify({
          week_id: weekId,
          log_date: date,
          topic: topic || null,
          learned: learned || null,
          blockers: blockers || null,
        }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["daily-logs", weekId] });
      setMsg(t("daily_log.success_message"));
      setTopic("");
      setLearned("");
      setBlockers("");
      setTimeout(() => setMsg(null), 2500);
    },
  });

  const del = useMutation({
    mutationFn: (id: number) =>
      authFetch(`/api/daily-logs/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["daily-logs", weekId] }),
  });

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold">{t("daily_log.heading")}</h1>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit.mutate();
        }}
        className="rounded-xl border border-gray-200 dark:border-gray-700 p-4 space-y-3"
      >
        <div className="grid grid-cols-2 gap-3">
          <label>
            <span className="text-sm">{t("daily_log.week_label")}</span>
            <select
              className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2"
              value={weekId}
              onChange={(e) => setWeekId(parseInt(e.target.value, 10))}
            >
              {(weeks ?? []).map((w) => (
                <option key={w.number} value={w.number}>
                  #{w.number} — {w.theme.slice(0, 50)}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span className="text-sm">{t("daily_log.date_label")}</span>
            <input
              type="date"
              className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2"
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
          </label>
        </div>

        <label className="block">
          <span className="text-sm">{t("daily_log.topic_label")}</span>
          <input
            className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder={t("daily_log.topic_placeholder")}
          />
        </label>

        <label className="block">
          <span className="text-sm">{t("daily_log.learned_label")}</span>
          <textarea
            rows={3}
            className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2"
            value={learned}
            onChange={(e) => setLearned(e.target.value)}
            placeholder={t("daily_log.learned_placeholder")}
          />
        </label>

        <label className="block">
          <span className="text-sm">{t("daily_log.blockers_label")}</span>
          <textarea
            rows={2}
            className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2"
            value={blockers}
            onChange={(e) => setBlockers(e.target.value)}
            placeholder={t("daily_log.blockers_placeholder")}
          />
        </label>

        {msg && (
          <div className="rounded bg-green-100 text-green-700 px-3 py-2 text-sm">
            {msg}
          </div>
        )}

        <button
          type="submit"
          disabled={submit.isPending}
          className="rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold px-6 py-2"
        >
          {submit.isPending ? t("daily_log.saving") : t("daily_log.save")}
        </button>
      </form>

      <section className="space-y-2">
        <h2 className="font-semibold">{t("daily_log.history_heading", { weekId })}</h2>
        <ul className="space-y-2">
          {(logs ?? []).map((l) => (
            <li
              key={l.id}
              className="rounded-lg border border-gray-200 dark:border-gray-700 p-3 text-sm"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono">{l.log_date}</span>
                <button
                  className="text-xs text-red-600 hover:underline"
                  onClick={() => del.mutate(l.id)}
                >
                  {t("daily_log.delete_button")}
                </button>
              </div>
              {l.topic && <div className="mt-1"><b>{t("daily_log.topic_inline_label")}</b> {l.topic}</div>}
              {l.learned && (
                <div className="mt-1 whitespace-pre-wrap"><b>{t("daily_log.learned_inline_label")}</b> {l.learned}</div>
              )}
              {l.blockers && (
                <div className="mt-1 text-red-700 dark:text-red-400">
                  <b>{t("daily_log.blockers_inline_label")}</b> {l.blockers}
                </div>
              )}
            </li>
          ))}
          {(logs ?? []).length === 0 && (
            <li className="text-gray-500 text-sm">{t("daily_log.empty_state")}</li>
          )}
        </ul>
      </section>
    </div>
  );
}