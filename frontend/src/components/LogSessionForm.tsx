import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authFetch, type Week } from "../lib/api";
import { useT } from "../lib/i18n";

interface NewSessionPayload {
  week_id: number;
  type: "focus" | "pomodoro";
  duration_sec: number;
  notes: string | null;
}

export function LogSessionForm({
  weeks,
  defaultWeek,
}: {
  weeks: Week[];
  defaultWeek: number;
}) {
  const t = useT();
  const qc = useQueryClient();
  const [weekId, setWeekId] = useState<number>(defaultWeek);
  const [hours, setHours] = useState<string>("2");
  const [minutes, setMinutes] = useState<string>("0");
  const [type, setType] = useState<"focus" | "pomodoro">("focus");
  const [notes, setNotes] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: (p: NewSessionPayload) =>
      authFetch("/api/sessions", {
        method: "POST",
        body: JSON.stringify(p),
      }),
    onSuccess: () => {
      // Invalidate the queries that depend on session data.
      qc.invalidateQueries({ queryKey: ["phases"] });
      qc.invalidateQueries({ queryKey: ["week", weekId] });
      qc.invalidateQueries({ queryKey: ["aggregate", weekId] });
      qc.invalidateQueries({ queryKey: ["sessions", weekId] });
      setMsg(t("log_session.success_message"));
      setNotes("");
      setTimeout(() => setMsg(null), 2500);
    },
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const secs =
      (parseFloat(hours || "0") * 3600) + (parseFloat(minutes || "0") * 60);
    if (secs <= 0) return;
    create.mutate({
      week_id: weekId,
      type,
      duration_sec: secs,
      notes: notes.trim() || null,
    });
  }

  return (
    <form
      onSubmit={submit}
      className="rounded-xl border border-gray-200 dark:border-gray-700 p-4 space-y-3"
    >
      <h2 className="font-semibold">{t("log_session.heading")}</h2>

      <label className="block">
        <span className="text-sm text-gray-600 dark:text-gray-400">{t("log_session.week_label")}</span>
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

      <div className="grid grid-cols-2 gap-3">
        <label>
          <span className="text-sm">{t("log_session.hours_label")}</span>
          <input
            type="number"
            min={0}
            max={24}
            className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2"
            value={hours}
            onChange={(e) => setHours(e.target.value)}
          />
        </label>
        <label>
          <span className="text-sm">{t("log_session.minutes_label")}</span>
          <input
            type="number"
            min={0}
            max={59}
            className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2"
            value={minutes}
            onChange={(e) => setMinutes(e.target.value)}
          />
        </label>
      </div>

      <label className="block">
        <span className="text-sm">{t("log_session.type_label")}</span>
        <select
          className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2"
          value={type}
          onChange={(e) => setType(e.target.value as "focus" | "pomodoro")}
        >
          <option value="focus">{t("log_session.type_focus")}</option>
          <option value="pomodoro">{t("log_session.type_pomodoro")}</option>
        </select>
      </label>

      <label className="block">
        <span className="text-sm">{t("log_session.notes_label")}</span>
        <input
          className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder={t("log_session.notes_placeholder")}
        />
      </label>

      {msg && (
        <div className="rounded bg-green-100 text-green-700 px-3 py-2 text-sm">
          {msg}
        </div>
      )}

      <button
        type="submit"
        disabled={create.isPending}
        className="w-full rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold py-2"
      >
        {create.isPending ? t("log_session.submitting") : t("log_session.submit")}
      </button>
    </form>
  );
}