import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { authFetch, type Phase, type Week } from "../lib/api";

interface RecapDraft {
  week_id: number;
  successes: string;
  blockers: string;
  next_step: string;
}

interface Recap {
  week_id: number;
  successes: string | null;
  blockers: string | null;
  next_step: string | null;
  updated_at: string | null;
}

async function fetchWeeks(): Promise<Week[]> {
  const phases = await authFetch<Phase[]>("/api/weeks");
  return phases.flatMap((p) => p.weeks);
}

async function fetchSaved(weekId: number): Promise<Recap | null> {
  try {
    return await authFetch<Recap>(`/api/recaps/${weekId}`);
  } catch {
    return null; // 404 means nothing saved yet
  }
}

export default function SundayRecapPage() {
  const qc = useQueryClient();
  const [weekId, setWeekId] = useState<number>(1);
  const [successes, setSuccesses] = useState<string>("");
  const [blockers, setBlockers] = useState<string>("");
  const [nextStep, setNextStep] = useState<string>("");
  const [copied, setCopied] = useState(false);

  const { data: weeks } = useQuery({ queryKey: ["phases"], queryFn: fetchWeeks });
  const { data: saved } = useQuery({
    queryKey: ["recap", weekId],
    queryFn: () => fetchSaved(weekId),
  });

  // When saved recap loads, populate the form (unless user is editing).
  useEffect(() => {
    if (saved) {
      setSuccesses(saved.successes ?? "");
      setBlockers(saved.blockers ?? "");
      setNextStep(saved.next_step ?? "");
    }
  }, [saved]);

  const generate = useMutation({
    mutationFn: () =>
      authFetch<RecapDraft>(`/api/recaps/${weekId}/generate`, { method: "POST" }),
    onSuccess: (d) => {
      setSuccesses(d.successes);
      setBlockers(d.blockers);
      setNextStep(d.next_step);
    },
  });

  const save = useMutation({
    mutationFn: () =>
      authFetch<Recap>(`/api/recaps/${weekId}`, {
        method: "PUT",
        body: JSON.stringify({
          week_id: weekId,
          successes,
          blockers,
          next_step: nextStep,
        }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["recap", weekId] }),
  });

  function copyMarkdown() {
    const md = [
      `## Recap — semaine ${weekId}`,
      "",
      "**Succès**",
      successes,
      "",
      "**Blocages**",
      blockers,
      "",
      "**Prochaine étape**",
      nextStep,
    ].join("\n");
    navigator.clipboard.writeText(md);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  }

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold">Sunday recap</h1>

      <label className="block">
        <span className="text-sm">Week</span>
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

      <div className="flex gap-2">
        <button
          onClick={() => generate.mutate()}
          disabled={generate.isPending}
          className="rounded-lg bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-semibold px-4 py-2"
        >
          {generate.isPending ? "Drafting..." : "Generate draft"}
        </button>
        <button
          onClick={copyMarkdown}
          className="rounded-lg bg-gray-200 hover:bg-gray-300 text-gray-800 dark:bg-gray-700 dark:text-gray-200 font-semibold px-4 py-2"
        >
          {copied ? "Copied!" : "Copy as Markdown"}
        </button>
        <button
          onClick={() => save.mutate()}
          disabled={save.isPending}
          className="rounded-lg bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-semibold px-4 py-2"
        >
          {save.isPending ? "Saving..." : "Save recap"}
        </button>
      </div>

      <div className="space-y-3">
        <label className="block">
          <span className="text-sm font-semibold">Succès</span>
          <textarea
            rows={3}
            className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2"
            value={successes}
            onChange={(e) => setSuccesses(e.target.value)}
          />
        </label>
        <label className="block">
          <span className="text-sm font-semibold">Blocages</span>
          <textarea
            rows={2}
            className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2"
            value={blockers}
            onChange={(e) => setBlockers(e.target.value)}
          />
        </label>
        <label className="block">
          <span className="text-sm font-semibold">Prochaine étape</span>
          <textarea
            rows={2}
            className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2"
            value={nextStep}
            onChange={(e) => setNextStep(e.target.value)}
          />
        </label>
      </div>

      {saved?.updated_at && (
        <p className="text-xs text-gray-500">
          Last saved: {saved.updated_at}
        </p>
      )}
    </div>
  );
}