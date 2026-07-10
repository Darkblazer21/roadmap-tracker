/**
 * Lightweight i18n system: a dictionary-based translator with two locales
 * (en, fr), a React context provider, and a `useT()` hook.
 *
 * Strings may use `{name}` placeholders for interpolation, e.g.
 *   t("dashboard.weeks_done_sub", { done: 3, total: 56 })
 * resolves "{done}/{total} weeks done" → "3/56 weeks done".
 *
 * The language preference is persisted in localStorage and defaults to "fr"
 * (the user's primary language). A toggle button in the header switches.
 */

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type Lang = "en" | "fr";

const LANG_KEY = "rt_lang";
const DEFAULT_LANG: Lang = "fr";

// ---- translation dictionary ------------------------------------------- //

type Dict = Record<string, string>;

const en: Dict = {
  // App shell / nav
  "app.title": "Roadmap Tracker",
  "app.current_week_badge": "Current: week {week}",
  "nav.dashboard": "Dashboard",
  "nav.weeks": "Weeks",
  "nav.daily_log": "Daily log",
  "nav.recap": "Recap",
  "nav.github": "GitHub",
  "nav.settings": "Settings",
  "nav.logout": "Sign out",
  "loading.login_page": "Loading login page…",

  // Login
  "login.subtitle": "Sign in to continue",
  "login.username_label": "Username",
  "login.password_label": "Password",
  "login.submitting": "Signing in…",
  "login.submit": "Sign in",

  // Error boundary
  "error.title": "Something went wrong",
  "error.description":
    "The page could not be displayed. You can go back to the dashboard or reload the page.",
  "error.back_home": "Back to dashboard",
  "error.reload": "Reload page",

  // Loading fallback
  "loading.default": "Loading…",
  "loading.inline_aria": "Loading",

  // Pomodoro
  "pomo.phase.working": "Work",
  "pomo.phase.short_break": "Short Break",
  "pomo.phase.long_break": "Long Break",
  "pomo.phase.marathon_break": "Marathon Break",
  "pomo.phase.paused": "Paused",
  "pomo.phase.idle": "Idle",
  "pomo.cycle_progress": "cycle {count}/{total}",
  "pomo.set_progress": "set {count}/{total}",
  "pomo.start_title": "Start pomodoro",
  "pomo.start": "Start",
  "pomo.pause_title": "Pause",
  "pomo.pause": "Pause",
  "pomo.resume_title": "Resume",
  "pomo.resume": "Resume",
  "pomo.stop_title": "Stop / reset",
  "pomo.stop": "Stop",
  "pomo.loading": "Pomodoro…",
  "pomo.error_retry": "Pomodoro: error — retry",
  "pomo.retry_title": "Retry",

  // Week status labels (shared)
  "status.not_started": "Not started",
  "status.in_progress": "In progress",
  "status.done": "Done",
  "status.late": "Late",
  "status.skipped": "Skipped",

  // Weeks list
  "weeks_list.loading": "Loading weeks…",
  "weeks_list.error": "Failed to load weeks.",
  "weeks_list.heading": "Roadmap Weeks",
  "weeks_list.help_text": "Click a week to see its details.",
  "weeks_list.phase_weeks_count": "{count} weeks",
  "weeks_list.col_number": "#",
  "weeks_list.col_theme": "Theme",
  "weeks_list.col_status": "Status",
  "weeks_list.col_hours": "Hours",
  "weeks_list.col_buffer": "Buffer",
  "weeks_list.hours_done_badge": "({hours}h done)",
  "weeks_list.buffer_tooltip": "Buffer week",

  // Week detail
  "week_detail.loading": "Loading week…",
  "week_detail.error_not_found": "Week not found.",
  "week_detail.back_link": "← Back to all weeks",
  "week_detail.heading": "Week {number}",
  "week_detail.part_of_label": '(part of "{label}")',
  "week_detail.buffer_badge": "Buffer week",
  "week_detail.theme_heading": "Theme",
  "week_detail.resources_heading": "Resources",
  "week_detail.deliverable_heading": "Deliverable",
  "week_detail.target_label": "Target:",
  "week_detail.logged_label": "Logged:",
  "week_detail.status_label": "Status:",
  "week_detail.sunday_recap_heading": "Sunday Recap",

  // Dashboard
  "dashboard.loading": "Loading dashboard…",
  "dashboard.error": "Failed to load dashboard.",
  "dashboard.heading": "Dashboard",
  "dashboard.current_week_label": "Current week",
  "dashboard.not_started_sub": "Not started",
  "dashboard.this_week_hours_label": "This week hours",
  "dashboard.target_hours_sub": "target {min}-{max}h",
  "dashboard.last_7_days_label": "Last 7 days",
  "dashboard.active_days_sub": "{count} active day(s)",
  "dashboard.progress_label": "Progress",
  "dashboard.weeks_done_sub": "{done}/{total} weeks done",
  "dashboard.overall_progress": "Overall progress",
  "dashboard.progress_summary": "{done} done · {active} active · {remaining} remaining",
  "dashboard.log_today": "Log today",
  "dashboard.sunday_recap": "Sunday recap",
  "dashboard.github_check": "GitHub check",
  "dashboard.export_json": "Export JSON",
  "dashboard.export_csv": "Export CSV",

  // Daily log
  "daily_log.success_message": "Journal saved",
  "daily_log.heading": "Daily log",
  "daily_log.week_label": "Week",
  "daily_log.date_label": "Date",
  "daily_log.topic_label": "Topic",
  "daily_log.topic_placeholder": "What you worked on today",
  "daily_log.learned_label": "Learned",
  "daily_log.learned_placeholder": "Key takeaways, new concepts…",
  "daily_log.blockers_label": "Blockers",
  "daily_log.blockers_placeholder": "What's stuck, what to revisit?",
  "daily_log.saving": "Saving…",
  "daily_log.save": "Save today's log",
  "daily_log.history_heading": "History — week {weekId}",
  "daily_log.delete_button": "delete",
  "daily_log.topic_inline_label": "Topic:",
  "daily_log.learned_inline_label": "Learned:",
  "daily_log.blockers_inline_label": "Blockers:",
  "daily_log.empty_state": "No logs yet for this week.",

  // Sunday recap
  "recap.heading": "Sunday recap",
  "recap.week_label": "Week",
  "recap.generating": "Drafting…",
  "recap.generate": "Generate draft",
  "recap.copied": "Copied!",
  "recap.copy_markdown": "Copy as Markdown",
  "recap.saving": "Saving…",
  "recap.save": "Save recap",
  "recap.successes_label": "Successes",
  "recap.blockers_label": "Blockers",
  "recap.next_step_label": "Next step",
  "recap.last_saved": "Last saved: {date}",
  "recap.md_heading": "## Recap — week {weekId}",
  "recap.md_successes": "**Successes**",
  "recap.md_blockers": "**Blockers**",
  "recap.md_next_step": "**Next step**",

  // GitHub verdicts
  "github.heading": "GitHub on-time check",
  "github.syncing": "Syncing…",
  "github.sync_now": "Sync now",
  "github.no_repos_message": "No tracked repositories yet. Add repos in Settings.",
  "github.no_graded_weeks_message":
    "No graded weeks yet. Set your start_date in Settings and sync to see verdicts.",
  "github.col_week": "Week",
  "github.col_theme": "Theme",
  "github.verdict_tooltip": "{label} · {count} commit(s)",
  "verdict.on_time": "On time",
  "verdict.late": "Activity but late",
  "verdict.missing": "Missing",
  "verdict.deferred": "Deferred",
  "verdict.future": "Future",

  // Log session form
  "log_session.success_message": "Logged!",
  "log_session.heading": "Log a study session",
  "log_session.week_label": "Week",
  "log_session.hours_label": "Hours",
  "log_session.minutes_label": "Minutes",
  "log_session.type_label": "Type",
  "log_session.type_focus": "Focus (manual)",
  "log_session.type_pomodoro": "Pomodoro",
  "log_session.notes_label": "Notes (optional)",
  "log_session.notes_placeholder": "What you studied…",
  "log_session.submitting": "Logging…",
  "log_session.submit": "Log session",

  // Week hours bar
  "hours_bar.loading": "Loading hours…",
  "hours_bar.error": "Could not load hours.",
  "hours_bar.week_label": "Week {id}",
  "hours_bar.heading": "Hours for week {id}",
  "hours_bar.tooltip_logged": "Logged",
  "hours_bar.over_cap_message": "⚠ Over the plan cap — consider slowing down to avoid burnout.",
  "hours_bar.under_min_message": "Below the plan minimum — push a bit more this week.",
  "hours_bar.on_track_message": "On track — within the planned range.",

  // Settings
  "settings.saved_message": "Saved",
  "settings.loading": "Loading settings…",
  "settings.error": "Failed to load settings.",
  "settings.back_link": "← Back to dashboard",
  "settings.heading": "Settings",
  "settings.timeline_anchor_heading": "Timeline anchor",
  "settings.start_date_label": "Start date (week 1 begins here)",
  "settings.start_date_help":
    'Setting this enables the "current week" highlight on the dashboard and powers the GitHub on-time verdicts.',
  "settings.weekly_target_heading": "Weekly hours target",
  "settings.min_hours_label": "Min hours/week",
  "settings.max_hours_label": "Max hours/week",
  "settings.pomo_defaults_heading": "Pomodoro defaults",
  "settings.pomo_work_label": "Work (min)",
  "settings.pomo_short_break_label": "Short break",
  "settings.pomo_long_break_label": "Long break",
  "settings.pomo_help":
    "Cycle: 25/5 ×4 → 15 min long break. The 2-hour marathon break after the 8th cycle is fixed by design and not editable here.",
  "settings.github_repos_heading": "GitHub tracked repositories",
  "settings.github_repos_help":
    "One repo per line, format owner/repo (e.g. kingbrems/roadmap-tracker)",
  "settings.saving": "Saving…",
  "settings.save": "Save settings",
  "settings.reset_heading": "Danger zone",
  "settings.reset_description": "Delete all sessions, daily logs, recaps, and reset every week to \"not started\". The start date, pomodoro config, and tracked repos are preserved.",
  "settings.reset_confirm": "Are you sure? This cannot be undone.",
  "settings.resetting": "Resetting…",
  "settings.reset": "Reset all progress",
  "settings.reset_done": "All progress has been reset.",

  // Deviation messages (translated on the frontend from backend status)
  "deviation.on_track": "You're on track — calendar week {cal}, working on week {first}.",
  "deviation.buffer": "{gap} week(s) behind, but you're in a known buffer zone — keep going.",
  "deviation.slight_delay": "Slight delay — {gap} week(s) behind the calendar (week {first} vs cal {cal}).",
  "deviation.behind": "⚠ {gap} week(s) behind plan (week {first} vs calendar week {cal}). Consider using a buffer week or adjusting pace.",
  "deviation.not_started": "Your roadmap hasn't started yet.",
  "deviation.complete": "All weeks are done — congratulations!",
  "deviation.unknown": "Set your start_date in Settings to enable deviation tracking.",
};

const fr: Dict = {
  // App shell / nav
  "app.title": "Roadmap Tracker",
  "app.current_week_badge": "Semaine actuelle : {week}",
  "nav.dashboard": "Tableau de bord",
  "nav.weeks": "Semaines",
  "nav.daily_log": "Journal",
  "nav.recap": "Récap",
  "nav.github": "GitHub",
  "nav.settings": "Réglages",
  "nav.logout": "Déconnexion",
  "loading.login_page": "Chargement de la page de connexion…",

  // Login
  "login.subtitle": "Connectez-vous pour continuer",
  "login.username_label": "Identifiant",
  "login.password_label": "Mot de passe",
  "login.submitting": "Connexion…",
  "login.submit": "Se connecter",

  // Error boundary
  "error.title": "Une erreur est survenue",
  "error.description":
    "La page n'a pas pu s'afficher. Vous pouvez revenir au tableau de bord ou recharger la page.",
  "error.back_home": "Retour au tableau de bord",
  "error.reload": "Recharger la page",

  // Loading fallback
  "loading.default": "Chargement…",
  "loading.inline_aria": "Chargement",

  // Pomodoro
  "pomo.phase.working": "Travail",
  "pomo.phase.short_break": "Pause courte",
  "pomo.phase.long_break": "Pause longue",
  "pomo.phase.marathon_break": "Pause marathon",
  "pomo.phase.paused": "En pause",
  "pomo.phase.idle": "Inactif",
  "pomo.cycle_progress": "cycle {count}/{total}",
  "pomo.set_progress": "série {count}/{total}",
  "pomo.start_title": "Démarrer le pomodoro",
  "pomo.start": "Démarrer",
  "pomo.pause_title": "Mettre en pause",
  "pomo.pause": "Pause",
  "pomo.resume_title": "Reprendre",
  "pomo.resume": "Reprendre",
  "pomo.stop_title": "Arrêter / réinitialiser",
  "pomo.stop": "Arrêter",
  "pomo.loading": "Pomodoro…",
  "pomo.error_retry": "Pomodoro : erreur — réessayer",
  "pomo.retry_title": "Réessayer",

  // Week status labels (shared)
  "status.not_started": "Non commencée",
  "status.in_progress": "En cours",
  "status.done": "Terminée",
  "status.late": "En retard",
  "status.skipped": "Ignorée",

  // Weeks list
  "weeks_list.loading": "Chargement des semaines…",
  "weeks_list.error": "Échec du chargement des semaines.",
  "weeks_list.heading": "Semaines du parcours",
  "weeks_list.help_text": "Cliquez sur une semaine pour voir les détails.",
  "weeks_list.phase_weeks_count": "{count} semaines",
  "weeks_list.col_number": "#",
  "weeks_list.col_theme": "Thème",
  "weeks_list.col_status": "Statut",
  "weeks_list.col_hours": "Heures",
  "weeks_list.col_buffer": "Buffer",
  "weeks_list.hours_done_badge": "({hours}h effectuées)",
  "weeks_list.buffer_tooltip": "Semaine tampon",

  // Week detail
  "week_detail.loading": "Chargement de la semaine…",
  "week_detail.error_not_found": "Semaine introuvable.",
  "week_detail.back_link": "← Retour aux semaines",
  "week_detail.heading": "Semaine {number}",
  "week_detail.part_of_label": '(fait partie de « {label} »)',
  "week_detail.buffer_badge": "Semaine tampon",
  "week_detail.theme_heading": "Thème",
  "week_detail.resources_heading": "Ressources",
  "week_detail.deliverable_heading": "Livrable",
  "week_detail.target_label": "Objectif :",
  "week_detail.logged_label": "Effectuées :",
  "week_detail.status_label": "Statut :",
  "week_detail.sunday_recap_heading": "Récap du dimanche",

  // Dashboard
  "dashboard.loading": "Chargement du tableau de bord…",
  "dashboard.error": "Échec du chargement du tableau de bord.",
  "dashboard.heading": "Tableau de bord",
  "dashboard.current_week_label": "Semaine actuelle",
  "dashboard.not_started_sub": "Non démarré",
  "dashboard.this_week_hours_label": "Heures cette semaine",
  "dashboard.target_hours_sub": "objectif {min}-{max}h",
  "dashboard.last_7_days_label": "7 derniers jours",
  "dashboard.active_days_sub": "{count} jour(s) actif(s)",
  "dashboard.progress_label": "Progression",
  "dashboard.weeks_done_sub": "{done}/{total} semaines terminées",
  "dashboard.overall_progress": "Progression globale",
  "dashboard.progress_summary": "{done} terminées · {active} actives · {remaining} restantes",
  "dashboard.log_today": "Journaliser aujourd'hui",
  "dashboard.sunday_recap": "Récap du dimanche",
  "dashboard.github_check": "Vérification GitHub",
  "dashboard.export_json": "Export JSON",
  "dashboard.export_csv": "Export CSV",

  // Daily log
  "daily_log.success_message": "Journal enregistré",
  "daily_log.heading": "Journal quotidien",
  "daily_log.week_label": "Semaine",
  "daily_log.date_label": "Date",
  "daily_log.topic_label": "Sujet",
  "daily_log.topic_placeholder": "Ce sur quoi vous avez travaillé aujourd'hui",
  "daily_log.learned_label": "Appris",
  "daily_log.learned_placeholder": "Points clés, nouveaux concepts…",
  "daily_log.blockers_label": "Blocages",
  "daily_log.blockers_placeholder": "Qu'est-ce qui coince ? À revoir ?",
  "daily_log.saving": "Enregistrement…",
  "daily_log.save": "Enregistrer le journal du jour",
  "daily_log.history_heading": "Historique — semaine {weekId}",
  "daily_log.delete_button": "supprimer",
  "daily_log.topic_inline_label": "Sujet :",
  "daily_log.learned_inline_label": "Appris :",
  "daily_log.blockers_inline_label": "Blocages :",
  "daily_log.empty_state": "Aucun journal pour cette semaine.",

  // Sunday recap
  "recap.heading": "Récap du dimanche",
  "recap.week_label": "Semaine",
  "recap.generating": "Génération…",
  "recap.generate": "Générer le brouillon",
  "recap.copied": "Copié !",
  "recap.copy_markdown": "Copier en Markdown",
  "recap.saving": "Enregistrement…",
  "recap.save": "Enregistrer le récap",
  "recap.successes_label": "Succès",
  "recap.blockers_label": "Blocages",
  "recap.next_step_label": "Prochaine étape",
  "recap.last_saved": "Dernier enregistrement : {date}",
  "recap.md_heading": "## Récap — semaine {weekId}",
  "recap.md_successes": "**Succès**",
  "recap.md_blockers": "**Blocages**",
  "recap.md_next_step": "**Prochaine étape**",

  // GitHub verdicts
  "github.heading": "Vérification GitHub — ponctualité",
  "github.syncing": "Synchronisation…",
  "github.sync_now": "Synchroniser",
  "github.no_repos_message": "Aucun dépôt suivi. Ajoutez-en dans les Réglages.",
  "github.no_graded_weeks_message":
    "Aucune semaine notée. Configurez la date de départ dans les Réglages et synchronisez pour voir les verdicts.",
  "github.col_week": "Semaine",
  "github.col_theme": "Thème",
  "github.verdict_tooltip": "{label} · {count} commit(s)",
  "verdict.on_time": "À l'heure",
  "verdict.late": "Actif mais en retard",
  "verdict.missing": "Manquant",
  "verdict.deferred": "Différé",
  "verdict.future": "À venir",

  // Log session form
  "log_session.success_message": "Enregistré !",
  "log_session.heading": "Enregistrer une session d'étude",
  "log_session.week_label": "Semaine",
  "log_session.hours_label": "Heures",
  "log_session.minutes_label": "Minutes",
  "log_session.type_label": "Type",
  "log_session.type_focus": "Focus (manuel)",
  "log_session.type_pomodoro": "Pomodoro",
  "log_session.notes_label": "Notes (optionnel)",
  "log_session.notes_placeholder": "Ce que vous avez étudié…",
  "log_session.submitting": "Enregistrement…",
  "log_session.submit": "Enregistrer la session",

  // Week hours bar
  "hours_bar.loading": "Chargement des heures…",
  "hours_bar.error": "Impossible de charger les heures.",
  "hours_bar.week_label": "Semaine {id}",
  "hours_bar.heading": "Heures pour la semaine {id}",
  "hours_bar.tooltip_logged": "Effectuées",
  "hours_bar.over_cap_message": "⚠ Au-dessus du plafond — ralentissez pour éviter la surchauffe.",
  "hours_bar.under_min_message": "En dessous du minimum — poussez un peu plus cette semaine.",
  "hours_bar.on_track_message": "Sur la bonne voie — dans la plage prévue.",

  // Settings
  "settings.saved_message": "Enregistré",
  "settings.loading": "Chargement des réglages…",
  "settings.error": "Échec du chargement des réglages.",
  "settings.back_link": "← Retour au tableau de bord",
  "settings.heading": "Réglages",
  "settings.timeline_anchor_heading": "Ancrage de la timeline",
  "settings.start_date_label": "Date de début (la semaine 1 commence ici)",
  "settings.start_date_help":
    'Ceci active la surbrillance de la « semaine actuelle » sur le tableau de bord et alimente les verdicts de ponctualité GitHub.',
  "settings.weekly_target_heading": "Objectif hebdomadaire (heures)",
  "settings.min_hours_label": "Heures min/semaine",
  "settings.max_hours_label": "Heures max/semaine",
  "settings.pomo_defaults_heading": "Pomodoro — valeurs par défaut",
  "settings.pomo_work_label": "Travail (min)",
  "settings.pomo_short_break_label": "Pause courte",
  "settings.pomo_long_break_label": "Pause longue",
  "settings.pomo_help":
    "Cycle : 25/5 ×4 → pause longue 15 min. La pause marathon de 2h après le 8e cycle est fixée par conception et non modifiable ici.",
  "settings.github_repos_heading": "Dépôts GitHub suivis",
  "settings.github_repos_help":
    "Un dépôt par ligne, format owner/repo (ex. kingbrems/roadmap-tracker)",
  "settings.saving": "Enregistrement…",
  "settings.save": "Enregistrer les réglages",
  "settings.reset_heading": "Zone de danger",
  "settings.reset_description": "Supprime toutes les sessions, journaux, récaps et réinitialise toutes les semaines à « non commencée ». La date de début, la configuration pomodoro et les dépôts suivis sont conservés.",
  "settings.reset_confirm": "Êtes-vous sûr ? Cette action est irréversible.",
  "settings.resetting": "Réinitialisation…",
  "settings.reset": "Réinitialiser toute la progression",
  "settings.reset_done": "Toute la progression a été réinitialisée.",

  // Deviation messages
  "deviation.on_track": "Vous êtes dans les temps — semaine calendaire {cal}, en cours sur la semaine {first}.",
  "deviation.buffer": "{gap} semaine(s) de retard, mais vous êtes dans une zone tampon connue — continuez.",
  "deviation.slight_delay": "Léger retard — {gap} semaine(s) de retard (semaine {first} vs cal {cal}).",
  "deviation.behind": "⚠ {gap} semaine(s) de retard sur le planning (semaine {first} vs semaine calendaire {cal}). Envisagez d'utiliser une semaine tampon ou d'ajuster le rythme.",
  "deviation.not_started": "Votre parcours n'a pas encore commencé.",
  "deviation.complete": "Toutes les semaines sont terminées — félicitations !",
  "deviation.unknown": "Configurez votre date de début dans les Réglages pour activer le suivi de déviation.",
};

const DICTS: Record<Lang, Dict> = { en, fr };

// ---- context + provider ----------------------------------------------- //

interface I18nContextValue {
  lang: Lang;
  setLang: (l: Lang) => void;
  toggleLang: () => void;
  t: (key: string, params?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18nContextValue | null>(null);

function detectLang(): Lang {
  const stored = localStorage.getItem(LANG_KEY);
  if (stored === "en" || stored === "fr") return stored;
  return DEFAULT_LANG;
}

function interpolate(
  template: string,
  params?: Record<string, string | number>
): string {
  if (!params) return template;
  return template.replace(/\{(\w+)\}/g, (_, key) =>
    key in params ? String(params[key]) : `{${key}}`
  );
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(detectLang);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const setLang = (l: Lang) => {
    localStorage.setItem(LANG_KEY, l);
    setLangState(l);
  };

  const toggleLang = () => setLang(lang === "en" ? "fr" : "en");

  const t = useMemo(() => {
    const dict = DICTS[lang];
    return (key: string, params?: Record<string, string | number>) => {
      const template = dict[key] ?? DICTS.en[key] ?? key;
      return interpolate(template, params);
    };
  }, [lang]);

  const value = useMemo<I18nContextValue>(
    () => ({ lang, setLang, toggleLang, t }),
    [lang, t]
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

// ---- hook -------------------------------------------------------------- //

export function useI18n(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within an I18nProvider");
  return ctx;
}

export function useT() {
  return useI18n().t;
}