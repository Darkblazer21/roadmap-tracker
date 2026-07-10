import { useT } from "../lib/i18n";

/**
 * Animated fallback shown while a lazy-loaded route is fetching its chunk
 * or while the first render is mounting. Doubles as the per-query loading
 * indicator on heavy pages to avoid a flash of empty content.
 */
export function PageFallback({ label }: { label?: string }) {
  const t = useT();
  const text = label ? t(label) : t("loading.default");
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center gap-4">
      <div
        className="h-10 w-10 rounded-full border-4 border-gray-200 dark:border-gray-700 border-t-blue-600 animate-spin"
        role="status"
        aria-label={text}
      />
      <p className="text-sm text-gray-500 animate-pulse">{text}</p>
    </div>
  );
}

/**
 * Compact inline spinner for small surfaces (e.g. buttons pending).
 */
export function InlineSpinner({ className = "" }: { className?: string }) {
  const t = useT();
  return (
    <span
      className={`inline-block h-3.5 w-3.5 rounded-full border-2 border-current border-t-transparent animate-spin ${className}`}
      role="status"
      aria-label={t("loading.inline_aria")}
    />
  );
}