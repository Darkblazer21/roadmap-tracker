import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { authFetch } from "../lib/api";

/**
 * Live pomodoro widget. Polls /api/pomo/state every second while a timer
 * is active (idle state polls much less often to save round trips).
 */

interface PomoState {
  phase: string;
  cycle_count: number;
  week_id: number | null;
  target_ends_at: number | null;
  remaining_sec: number;
  paused: boolean;
  work_min: number;
  short_break_min: number;
  long_break_min: number;
  marathon_break_min: number;
  cycles_per_set: number;
  cycles_per_marathon: number;
  cycles_in_set: number;
  set_count: number;
}

const PHASE_COLORS: Record<string, string> = {
  working: "#dc2626",
  short_break: "#16a34a",
  long_break: "#2563eb",
  marathon_break: "#7c3aed",
  paused: "#6b7280",
  idle: "#9ca3af",
};

const PHASE_LABELS: Record<string, string> = {
  working: "Work",
  short_break: "Short Break",
  long_break: "Long Break",
  marathon_break: "Marathon Break",
  paused: "Paused",
  idle: "Idle",
};

function fmtTime(sec: number): string {
  const s = Math.max(0, Math.floor(sec));
  const m = Math.floor(s / 60);
  const ss = s % 60;
  return `${m}:${ss.toString().padStart(2, "0")}`;
}

export function PomodoroWidget() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["pomo"],
    queryFn: () => authFetch<PomoState>("/api/pomo/state"),
    refetchInterval: (q) => {
      const d = q.state.data as PomoState | undefined;
      // Poll every second when running; every 10s when idle/paused.
      if (!d || d.phase === "idle") return 10_000;
      return 1_000;
    },
  });

  const startMut = useMutation({
    mutationFn: () => authFetch<PomoState>("/api/pomo/start", { method: "POST", body: "{}" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pomo"] }),
  });
  const pauseMut = useMutation({
    mutationFn: () => authFetch<PomoState>("/api/pomo/pause", { method: "POST", body: "{}" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pomo"] }),
  });
  const resumeMut = useMutation({
    mutationFn: () => authFetch<PomoState>("/api/pomo/resume", { method: "POST", body: "{}" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pomo"] }),
  });
  const stopMut = useMutation({
    mutationFn: () => authFetch<PomoState>("/api/pomo/stop", { method: "POST", body: "{}" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pomo"] });
      // Refresh hours bar / sessions since completed pomodoros logged sessions.
      qc.invalidateQueries({ queryKey: ["phases"] });
      qc.invalidateQueries({ queryKey: ["aggregate"] });
    },
  });

  if (isLoading || !data) {
    return <span className="text-sm text-gray-500">Pomodoro…</span>;
  }

  const phase = data.phase;
  const color = PHASE_COLORS[phase] ?? "#9ca3af";
  const isIdle = phase === "idle";
  const isPaused = data.paused;

  // Compute total duration for the ring fraction (based on phase config).
  const totalSec =
    phase === "working"
      ? data.work_min * 60
      : phase === "short_break"
        ? data.short_break_min * 60
        : phase === "long_break"
          ? data.long_break_min * 60
          : phase === "marathon_break"
            ? data.marathon_break_min * 60
            : data.work_min * 60;

  const fraction = totalSec > 0 ? Math.max(0, Math.min(1, data.remaining_sec / totalSec)) : 0;
  const RADIUS = 14;
  const CIRC = 2 * Math.PI * RADIUS;
  const dash = CIRC * fraction;

  return (
    <div className="flex items-center gap-3">
      {/* Ring */}
      <div className="relative h-8 w-8">
        <svg viewBox="0 0 32 32" className="h-8 w-8 -rotate-90">
          <circle
            cx="16" cy="16" r={RADIUS}
            fill="none" stroke="#e5e7eb" strokeWidth="3"
          />
          <circle
            cx="16" cy="16" r={RADIUS}
            fill="none" stroke={color} strokeWidth="3"
            strokeDasharray={`${dash} ${CIRC}`}
            strokeLinecap="round"
          />
        </svg>
      </div>

      <div className="flex flex-col leading-tight">
        <span className="text-xs text-gray-500">{PHASE_LABELS[phase] ?? phase}</span>
        <span className="font-mono font-bold tabular-nums" style={{ color }}>
          {fmtTime(data.remaining_sec)}
        </span>
      </div>

      {/* Cycle indicator */}
      {phase !== "idle" && (
        <div className="flex flex-col leading-tight ml-1 pl-2 border-l border-gray-200 dark:border-gray-700">
          <span className="text-xs text-gray-500">
            cycle {data.cycle_count}/{data.cycles_per_marathon}
          </span>
          <span className="text-xs text-gray-500">
            set {data.cycles_in_set}/{data.cycles_per_set}
          </span>
        </div>
      )}

      {/* Buttons */}
      <div className="flex gap-1">
        {isIdle && (
          <button
            onClick={() => startMut.mutate()}
            disabled={startMut.isPending}
            className="rounded-md bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-xs px-2 py-1"
            title="Start pomodoro"
          >
            Start
          </button>
        )}
        {phase === "working" && !isPaused && (
          <button
            onClick={() => pauseMut.mutate()}
            disabled={pauseMut.isPending}
            className="rounded-md bg-gray-600 hover:bg-gray-700 disabled:opacity-50 text-white text-xs px-2 py-1"
            title="Pause"
          >
            Pause
          </button>
        )}
        {isPaused && (
          <button
            onClick={() => resumeMut.mutate()}
            disabled={resumeMut.isPending}
            className="rounded-md bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-xs px-2 py-1"
            title="Resume"
          >
            Resume
          </button>
        )}
        {!isIdle && (
          <button
            onClick={() => stopMut.mutate()}
            disabled={stopMut.isPending}
            className="rounded-md bg-gray-300 hover:bg-gray-400 disabled:opacity-50 text-gray-700 text-xs px-2 py-1"
            title="Stop / reset"
          >
            Stop
          </button>
        )}
      </div>
    </div>
  );
}