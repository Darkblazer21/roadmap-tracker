import { useEffect, useState } from "react";
import { useT } from "../lib/i18n";

/**
 * Minimum time (ms) the fallback stays visible. Without this, lazy chunks
 * load so fast on localhost that the spinner flashes for a single frame and
 * the user perceives an instant blank-to-content swap with no transition.
 * 350ms is long enough to register as "loading" but short enough not to feel
 * sluggish.
 */
const MIN_DISPLAY_MS = 350;

/**
 * Animated fallback shown while a lazy-loaded route is fetching its chunk
 * or while the first render is mounting. Uses a minimum-duration gate so the
 * spinner is always perceptible, even on fast connections.
 */
export function PageFallback({ label }: { label?: string }) {
  const t = useT();
  const text = label ? t(label) : t("loading.default");
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    setVisible(true);
    const timer = setTimeout(() => setVisible(false), MIN_DISPLAY_MS);
    return () => clearTimeout(timer);
  }, [label]);

  if (!visible && label) return null;

  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center gap-4 page-fade-in">
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