import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { authFetch, type Phase, type Week } from "../lib/api";

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

const VERDICT_META: Record<Verdict, { emoji: string; label: string; cls: string }> = {
  on_time: { emoji: "✅", label: "On time", cls: "bg-green-100 text-green-700" },
  late: { emoji: "⚠️", label: "Activity but late", cls: "bg-yellow-100 text-yellow-700" },
  missing: { emoji: "❌", label: "Missing", cls: "bg-red-100 text-red-700" },
  deferred: { emoji: "⏸", label: "Deferred", cls: "bg-gray-100 text-gray-500" },
  future: { emoji: "—", label: "Future", cls: "bg-gray-50 text-gray-400" },
};

async function fetchWeeks(): Promise<Week[]> {
  const phases = await authFetch<Phase[]>("/api/weeks");
  return phases.flatMap((p) => p.weeks);
}

async function fetchVerdicts(): Promise<VerdictMatrix> {
  return authFetch<VerdictMatrix>("/api/github/verdicts");
}

export default function GithubVerdictsPage() {
  const qc = useQueryClient();
  const { data: weeks } = useQuery({ queryKey: ["phases"], queryFn: fetchWeeks });
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
        <h1 className="text-2xl font-bold">GitHub on-time check</h1>
        <button
          onClick={() => sync.mutate()}
          disabled={sync.isPending}
          className="rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold px-4 py-2 text-sm"
        >
          {sync.isPending ? "Syncing…" : "Sync now"}
        </button>
      </div>

      {repos.length === 0 && (
        <p className="text-gray-500">
          No tracked repositories yet. Add repos in{" "}
          <a href="/settings" className="text-blue-600 underline">
            Settings
          </a>
          .
        </p>
      )}

      {repos.length > 0 && !isLoading && verdicts && gradedWeeks.length === 0 && (
        <p className="text-gray-500">
          No graded weeks yet. Set your start_date in Settings and sync to see
          verdicts.
        </p>
      )}

      {repos.length > 0 && gradedWeeks.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr>
                <th className="text-left px-3 py-2 border-b border-gray-200 dark:border-gray-700">
                  Week
                </th>
                <th className="text-left px-3 py-2 border-b border-gray-200 dark:border-gray-700">
                  Theme
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
                    const meta = VERDICT_META[v.verdict];
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
        {(Object.keys(VERDICT_META) as Verdict[]).map((k) => (
          <span
            key={k}
            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 ${VERDICT_META[k].cls}`}
          >
            {VERDICT_META[k].emoji} {VERDICT_META[k].label}
          </span>
        ))}
      </div>
    </div>
  );
}