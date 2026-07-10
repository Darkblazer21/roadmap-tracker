/**
 * API helpers: a fetch wrapper that injects the JWT bearer token from
 * localStorage and a thin react-query hook host. Keeps auth concerns in one
 * place so pages stay declarative.
 */

const TOKEN_KEY = "roadmap_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

/**
 * fetch wrapper that:
 *  - prepends Authorization: Bearer <token> when present
 *  - throws on non-ok responses with the JSON detail message
 *  - on 401, clears the stored token so the app bounces to /login
 */
export async function authFetch<T = unknown>(
  url: string,
  init: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const res = await fetch(url, { ...init, headers });
  if (res.status === 401) {
    setToken(null);
    // Notify the AuthGate so react-router can redirect, avoiding a hash jump.
    window.dispatchEvent(new CustomEvent("auth:logout"));
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as unknown as T;
  return (await res.json()) as T;
}

/** POST helper that returns plain JSON or null on auth failure. */
export async function postJSON<T = unknown>(url: string, body: unknown): Promise<T> {
  return authFetch<T>(url, { method: "POST", body: JSON.stringify(body) });
}

export async function patchJSON<T = unknown>(url: string, body: unknown): Promise<T> {
  return authFetch<T>(url, { method: "PATCH", body: JSON.stringify(body) });
}

// --- shared type aliases (mirror backend Pydantic schemas) ---

export type WeekStatus =
  | "not_started"
  | "in_progress"
  | "done"
  | "late"
  | "skipped";

export interface Week {
  number: number;
  phase_id: number;
  theme: string;
  resources: string;
  deliverable: string;
  hours_min: number;
  hours_max: number;
  buffer: boolean;
  week_label: string | null;
  status: WeekStatus;
  actual_hours: number;
  recap_sunday: string | null;
  reviewed_at: string | null;
}

export interface Phase {
  id: number;
  key: string;
  title: string;
  position: number;
  subtitle: string | null;
  notes: string | null;
  weeks: Week[];
}

export interface Settings {
  id: number;
  start_date: string | null;
  timezone: string;
  tracked_repos: string[];
  pomo_work_min: number;
  pomo_short_break_min: number;
  pomo_long_break_min: number;
  pomo_marathon_break_min: number;
  pomo_cycles_per_short_set: number;
  pomo_cycles_per_long_break: number;
  weekly_target_min: number;
  weekly_target_max: number;
}