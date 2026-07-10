import { lazy, Suspense, useEffect, useState } from "react";
import {
  Routes,
  Route,
  Navigate,
  NavLink,
  Outlet,
  useNavigate,
  useLocation,
} from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { authFetch, getToken, setToken } from "./lib/api";
import { useT } from "./lib/i18n";
import { PomodoroWidget } from "./components/PomodoroWidget";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { PageFallback } from "./components/PageFallback";
import { LanguageToggle } from "./components/LanguageToggle";

// Route-level code splitting: each page is its own JS chunk so the initial
// bundle stays small and navigation fetches only what it needs.
const LoginPage = lazy(() => import("./pages/LoginPage"));
const WeeksListPage = lazy(() => import("./pages/WeeksListPage"));
const WeekDetailPage = lazy(() => import("./pages/WeekDetailPage"));
const SettingsPage = lazy(() => import("./pages/SettingsPage"));
const DailyLogPage = lazy(() => import("./pages/DailyLogPage"));
const SundayRecapPage = lazy(() => import("./pages/SundayRecapPage"));
const GithubVerdictsPage = lazy(() => import("./pages/GithubVerdictsPage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));

/** AuthGate: bounces to /login when no token is stored. */
function AuthGate() {
  const navigate = useNavigate();
  useEffect(() => {
    if (!getToken()) navigate("/login", { replace: true });
    const onLogout = () => navigate("/login", { replace: true });
    window.addEventListener("auth:logout", onLogout);
    return () => window.removeEventListener("auth:logout", onLogout);
  }, [navigate]);
  return <Outlet />;
}

function Layout({ currentWeek }: { currentWeek: number | null }) {
  const navigate = useNavigate();
  const t = useT();

  function logout() {
    setToken(null);
    navigate("/login", { replace: true });
  }

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    isActive ? "font-semibold text-blue-700" : "text-blue-600 hover:underline";

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-10 backdrop-blur bg-white/80 dark:bg-gray-900/80 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-5xl mx-auto flex items-center justify-between px-4 h-12">
          <div className="flex items-center gap-4">
            <NavLink to="/" className="font-bold">
              {t("app.title")}
            </NavLink>
            {currentWeek !== null && (
              <span className="px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-700">
                {t("app.current_week_badge", { week: currentWeek })}
              </span>
            )}
          </div>
          <nav className="flex items-center gap-3 text-sm">
            <NavLink to="/" className={navLinkClass}>{t("nav.dashboard")}</NavLink>
            <NavLink to="/weeks" className={navLinkClass}>{t("nav.weeks")}</NavLink>
            <NavLink to="/daily-log" className={navLinkClass}>{t("nav.daily_log")}</NavLink>
            <NavLink to="/recap" className={navLinkClass}>{t("nav.recap")}</NavLink>
            <NavLink to="/github" className={navLinkClass}>{t("nav.github")}</NavLink>
            <NavLink to="/settings" className={navLinkClass}>{t("nav.settings")}</NavLink>
            <span className="w-px h-5 bg-gray-300 dark:bg-gray-600" />
            <PomodoroWidget />
            <LanguageToggle />
            <button className="text-gray-500 hover:text-gray-700" onClick={logout}>
              {t("nav.logout")}
            </button>
          </nav>
        </div>
      </header>
      <main className="flex-1">
        <ErrorBoundary key={useLocation().pathname}>
          <Suspense fallback={<PageFallback />}>
            <div className="page-fade-in">
              <Outlet />
            </div>
          </Suspense>
        </ErrorBoundary>
      </main>
    </div>
  );
}

function useCurrentWeek(): number | null {
  const { data } = useQuery({
    queryKey: ["current-week"],
    queryFn: ({ signal }) =>
      authFetch<{ current_week: number | null }>("/api/settings/current-week", { signal }),
    enabled: !!getToken(),
    staleTime: 60_000,
    refetchInterval: 60_000,
  });
  return data?.current_week ?? null;
}

export default function App() {
  const [bootChecked, setBootChecked] = useState(false);
  useEffect(() => setBootChecked(true), []);

  if (!bootChecked) return null;
  const hasToken = !!getToken();

  return (
    <Routes>
      <Route
        path="/login"
        element={
          <Suspense fallback={<PageFallback label="loading.login_page" />}>
            {hasToken ? <Navigate to="/" replace /> : <LoginPage />}
          </Suspense>
        }
      />
      <Route element={<AuthGate />}>
        <Route element={<LayoutWithCurrentWeek />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/weeks" element={<WeeksListPage />} />
          <Route path="/weeks/:number" element={<WeekDetailPage />} />
          <Route path="/daily-log" element={<DailyLogPage />} />
          <Route path="/recap" element={<SundayRecapPage />} />
          <Route path="/github" element={<GithubVerdictsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Route>
    </Routes>
  );
}

function LayoutWithCurrentWeek() {
  const currentWeek = useCurrentWeek();
  return <Layout currentWeek={currentWeek} />;
}