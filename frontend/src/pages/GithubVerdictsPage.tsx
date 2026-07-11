import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { authFetch, fetchAllWeeks } from "../lib/api";
import { useT } from "../lib/i18n";

/**
 * GitHub verdicts page: a table of weeks × tracked repos showing
 * ✅ on-time / ⚠️ late / ❌ missing / — future, plus a "Sync now" button.
 */

type Verdict = "on_time" | "late" | "missing" | "deferred" | "future";

interface WeekVerdict {
  verdict: Verdict;
  count: number;
  latest_at: string | null;
}

type VerdictMatrix = Record<string, Record<number, WeekVerdict>>;

const VERDICT_CLS: Record<Verdict, { emoji: string; cls: string }> = {
  on_time: { emoji: "✅", cls: "bg-green-100 text-green-700" },
  late: { emoji: "⚠️", cls: "bg-yellow-100 text-yellow-700" },
  missing: { emoji: "❌", cls: "bg-red-100 text-red-700" },
  deferred: { emoji: "⏸", cls: "bg-gray-100 text-gray-500" },
  future: { emoji: "—", cls: "bg-gray-50 text-gray-400" },
};

const VERDICT_LABEL_KEY: Record<Verdict, string> = {
  on_time: "verdict.on_time",
  late: "verdict.late",
  missing: "verdict.missing",
  deferred: "verdict.deferred",
  future: "verdict.future",
};

function verdictMeta(verdict: Verdict, t: (k: string) => string) {
  const base = VERDICT_CLS[verdict];
  return { emoji: base.emoji, cls: base.cls, label: t(VERDICT_LABEL_KEY[verdict]) };
}

async function fetchVerdicts(): Promise<VerdictMatrix> {
  return authFetch<VerdictMatrix>("/api/github/verdicts");
}

export default function GithubVerdictsPage() {
  const t = useT();
  const qc = useQueryClient();
  const { data: weeks } = useQuery({ queryKey: ["all-weeks"], queryFn: fetchAllWeeks });
  const { data: verdicts, isLoading } = useQuery({
    queryKey: ["github-verdicts"],
    queryFn: fetchVerdicts,
  });

  const sync = useMutation({
    mutationFn: () =>
      authFetch<Record<string, number>>("/api/github/sync", { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["github-verdicts"] }),
  });

  const repos = verdicts ? Object.keys(verdicts) : [];
  const weekList = weeks ?? [];
  const sortedWeeks = [...weekList].sort((a, b) => a.number - b.number);

  // Only show graded weeks (not future) to keep the table short.
  const gradedWeeks = sortedWeeks.filter((w) => {
    if (!verdicts) return false;
    return repos.some((r) => {
      const v = verdicts[r]?.[w.number];
      return v && v.verdict !== "future";
    });
  });

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t("github.heading")}</h1>
        <button
          onClick={() => sync.mutate()}
          disabled={sync.isPending}
          className="rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold px-4 py-2 text-sm"
        >
          {sync.isPending ? t("github.syncing") : t("github.sync_now")}
        </button>
      </div>

      {repos.length === 0 && (
        <p className="text-gray-500">
          {t("github.no_repos_message")}
        </p>
      )}

      {repos.length > 0 && !isLoading && verdicts && gradedWeeks.length === 0 && (
        <p className="text-gray-500">
          {t("github.no_graded_weeks_message")}
        </p>
      )}

      {repos.length > 0 && gradedWeeks.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr>
                <th className="text-left px-3 py-2 border-b border-gray-200 dark:border-gray-700">
                  {t("github.col_week")}
                </th>
                <th className="text-left px-3 py-2 border-b border-gray-200 dark:border-gray-700">
                  {t("github.col_theme")}
                </th>
                {repos.map((r) => (
                  <th
                    key={r}
                    className="text-center px-3 py-2 border-b border-gray-200 dark:border-gray-700 font-mono"
                  >
                    {r}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {gradedWeeks.map((w) => (
                <tr
                  key={w.number}
                  className="border-b border-gray-100 dark:border-gray-800"
                >
                  <td className="px-3 py-2 font-mono font-bold">{w.number}</td>
                  <td className="px-3 py-2">{w.theme.slice(0, 50)}</td>
                  {repos.map((r) => {
                    const v = verdicts?.[r]?.[w.number];
                    if (!v) {
                      return (
                        <td key={r} className="px-3 py-2 text-center text-gray-400">
                          —
                        </td>
                      );
                    }
                    const meta = verdictMeta(v.verdict, t);
                    return (
                      <td key={r} className="px-3 py-2 text-center">
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs ${meta.cls}`}
                          title={`${meta.label} · ${v.count} commit(s)`}
                        >
                          {meta.emoji}{" "}
                          {v.count > 0 ? v.count : ""}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Legend */}
      <div className="flex flex-wrap gap-3 text-xs text-gray-600 dark:text-gray-400">
        {(Object.keys(VERDICT_CLS) as Verdict[]).map((k) => {
          const m = verdictMeta(k, t);
          return (
          <span
            key={k}
            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 ${m.cls}`}
          >
            {m.emoji} {m.label}
          </span>
          );
        })}
      </div>
    </div>
  );
}