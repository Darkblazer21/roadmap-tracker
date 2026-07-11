import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { authFetch, patchJSON, type Settings } from "../lib/api";
import { useT } from "../lib/i18n";
import { PageFallback } from "../components/PageFallback";

async function fetchSettings(): Promise<Settings> {
  return authFetch<Settings>("/api/settings");
}

export default function SettingsPage() {
  const t = useT();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { data, isError } = useQuery({
    queryKey: ["settings"],
    queryFn: fetchSettings,
  });

  const [form, setForm] = useState<Partial<Settings> | null>(null);
  const [savedMsg, setSavedMsg] = useState<string | null>(null);
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  const reset = useMutation({
    mutationFn: () =>
      authFetch("/api/settings/reset", { method: "POST" }),
    onSuccess: () => {
      // Invalidate every query that depends on user-generated data.
      // We don't use qc.clear() because that would also nuke settings and
      // auth queries, causing a re-fetch storm. Targeted invalidation is
      // cleaner and avoids triggering the loading state on the settings form.
      qc.invalidateQueries({ queryKey: ["phases"] });
      qc.invalidateQueries({ queryKey: ["all-weeks"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      qc.invalidateQueries({ queryKey: ["daily-logs"] });
      qc.invalidateQueries({ queryKey: ["recap"] });
      qc.invalidateQueries({ queryKey: ["pomo"] });
      qc.invalidateQueries({ queryKey: ["aggregate"] });
      qc.invalidateQueries({ queryKey: ["sessions"] });
      qc.invalidateQueries({ queryKey: ["github-verdicts"] });
      setShowResetConfirm(false);
      setSavedMsg(t("settings.reset_done"));
      setTimeout(() => setSavedMsg(null), 4000);
    },
  });

  const save = useMutation({
    mutationFn: (patch: Partial<Settings>) =>
      patchJSON<Settings>("/api/settings", patch),
    onSuccess: (updated) => {
      setForm(null);
      qc.setQueryData(["settings"], updated);
      setSavedMsg(t("settings.saved_message"));
      setTimeout(() => setSavedMsg(null), 2500);
    },
  });

  if (!data) {
    if (isError)
      return <div className="p-8 text-red-600">{t("settings.error")}</div>;
    return <PageFallback label={t("settings.loading")} />;
  }

  const editing = form ?? {};
  const start_date: string = editing.start_date !== undefined
  ? (editing.start_date ?? "")
  : (data.start_date ?? "");
  const weekly_target_min = editing.weekly_target_min !== undefined ? editing.weekly_target_min : data.weekly_target_min;
  const weekly_target_max = editing.weekly_target_max !== undefined ? editing.weekly_target_max : data.weekly_target_max;
  const pomo_work_min = editing.pomo_work_min !== undefined ? editing.pomo_work_min : data.pomo_work_min;
  const pomo_short_break_min = editing.pomo_short_break_min !== undefined ? editing.pomo_short_break_min : data.pomo_short_break_min;
  const pomo_long_break_min = editing.pomo_long_break_min !== undefined ? editing.pomo_long_break_min : data.pomo_long_break_min;
  const tracked_repos_raw = editing.tracked_repos !== undefined ? (editing.tracked_repos as unknown as string[])!.join("\n") : data.tracked_repos.join("\n");

  function set<K extends keyof Settings>(key: K, value: Settings[K] | undefined) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <button
        onClick={() => navigate("/")}
        className="text-blue-600 hover:underline text-sm"
      >
        {t("settings.back_link")}
      </button>

      <h1 className="text-2xl font-bold">{t("settings.heading")}</h1>

      {savedMsg && (
        <div className="rounded bg-green-100 text-green-700 px-3 py-2 text-sm">
          {savedMsg}
        </div>
      )}

      <section className="space-y-3 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
        <h2 className="font-semibold">{t("settings.timeline_anchor_heading")}</h2>
        <label className="block">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {t("settings.start_date_label")}
          </span>
          <input
            type="date"
            className="mt-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2"
            value={start_date}
            onChange={(e) => set("start_date", e.target.value || null)}
          />
        </label>
        <p className="text-xs text-gray-500">
          {t("settings.start_date_help")}
        </p>
      </section>

      <section className="space-y-3 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
        <h2 className="font-semibold">{t("settings.weekly_target_heading")}</h2>
        <div className="flex gap-4">
          <label className="flex-1">
            <span className="text-sm">{t("settings.min_hours_label")}</span>
            <input
              type="number"
              className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2"
              value={weekly_target_min}
              onChange={(e) => set("weekly_target_min", parseInt(e.target.value) || 0)}
            />
          </label>
          <label className="flex-1">
            <span className="text-sm">{t("settings.max_hours_label")}</span>
            <input
              type="number"
              className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2"
              value={weekly_target_max}
              onChange={(e) => set("weekly_target_max", parseInt(e.target.value) || 0)}
            />
          </label>
        </div>
      </section>

      <section className="space-y-3 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
        <h2 className="font-semibold">{t("settings.pomo_defaults_heading")}</h2>
        <div className="grid grid-cols-3 gap-4">
          <label>
            <span className="text-sm">{t("settings.pomo_work_label")}</span>
            <input
              type="number"
              className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2"
              value={pomo_work_min}
              onChange={(e) => set("pomo_work_min", parseInt(e.target.value) || 0)}
            />
          </label>
          <label>
            <span className="text-sm">{t("settings.pomo_short_break_label")}</span>
            <input
              type="number"
              className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2"
              value={pomo_short_break_min}
              onChange={(e) => set("pomo_short_break_min", parseInt(e.target.value) || 0)}
            />
          </label>
          <label>
            <span className="text-sm">{t("settings.pomo_long_break_label")}</span>
            <input
              type="number"
              className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2"
              value={pomo_long_break_min}
              onChange={(e) => set("pomo_long_break_min", parseInt(e.target.value) || 0)}
            />
          </label>
        </div>
        <p className="text-xs text-gray-500">
          {t("settings.pomo_help")}
        </p>
      </section>

      <section className="space-y-3 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
        <h2 className="font-semibold">{t("settings.github_repos_heading")}</h2>
        <label className="block">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {t("settings.github_repos_help")}
          </span>
          <textarea
            rows={3}
            className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 font-mono text-sm"
            value={tracked_repos_raw}
            onChange={(e) =>
              set(
                "tracked_repos",
                e.target.value
                  .split("\n")
                  .map((l) => l.trim())
                  .filter(Boolean)
              )
            }
          />
        </label>
      </section>

      <button
        onClick={() =>
          save.mutate({
            start_date: start_date || null,
            weekly_target_min,
            weekly_target_max,
            pomo_work_min,
            pomo_short_break_min,
            pomo_long_break_min,
            tracked_repos: (editing.tracked_repos !== undefined
              ? (editing.tracked_repos as unknown as string[])
              : data.tracked_repos),
          })
        }
        disabled={save.isPending || !form}
        className="rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold px-6 py-2"
      >
        {save.isPending ? t("settings.saving") : t("settings.save")}
      </button>

      {/* Danger zone: reset all progress */}
      <section className="space-y-3 rounded-xl border-2 border-red-300 dark:border-red-700 p-4">
        <h2 className="font-semibold text-red-700 dark:text-red-400">
          {t("settings.reset_heading")}
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {t("settings.reset_description")}
        </p>
        {!showResetConfirm ? (
          <button
            onClick={() => setShowResetConfirm(true)}
            className="rounded-lg border border-red-400 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 font-semibold px-4 py-2 text-sm"
          >
            {t("settings.reset")}
          </button>
        ) : (
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-red-600">
              {t("settings.reset_confirm")}
            </span>
            <button
              onClick={() => reset.mutate()}
              disabled={reset.isPending}
              className="rounded-lg bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-semibold px-4 py-2 text-sm"
            >
              {reset.isPending ? t("settings.resetting") : t("settings.reset")}
            </button>
            <button
              onClick={() => setShowResetConfirm(false)}
              className="rounded-lg bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 font-semibold px-4 py-2 text-sm"
            >
              ✕
            </button>
          </div>
        )}
      </section>
    </div>
  );
}