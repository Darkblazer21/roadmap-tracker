import { useI18n } from "../lib/i18n";

/** Compact EN/FR toggle button shown in the header. */
export function LanguageToggle() {
  const { lang, toggleLang } = useI18n();
  return (
    <button
      onClick={toggleLang}
      className="rounded-md border border-gray-300 dark:border-gray-600 px-2 py-0.5 text-xs font-semibold hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
      title={lang === "en" ? "Passer en français" : "Switch to English"}
    >
      {lang === "en" ? "FR" : "EN"}
    </button>
  );
}