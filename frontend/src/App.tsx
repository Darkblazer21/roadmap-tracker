import { useEffect, useState } from "react";
import {
  Routes,
  Route,
  Navigate,
  NavLink,
  Outlet,
  useNavigate,
} from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { authFetch, getToken, setToken } from "./lib/api";
import LoginPage from "./pages/LoginPage";
import WeeksListPage from "./pages/WeeksListPage";
import WeekDetailPage from "./pages/WeekDetailPage";
import SettingsPage from "./pages/SettingsPage";

/** AuthGate: bounces to /login when no token is stored. Reads on mount and
 * on the custom "auth:logout" event the api fires on a 401. */
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

  function logout() {
    setToken(null);
    navigate("/login", { replace: true });
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-10 backdrop-blur bg-white/80 dark:bg-gray-900/80 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-5xl mx-auto flex items-center justify-between px-4 h-12">
          <div className="flex items-center gap-4">
            <NavLink to="/" className="font-bold">
              Roadmap Tracker
            </NavLink>
            {currentWeek !== null && (
              <span className="px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-700">
                Current: week {currentWeek}
              </span>
            )}
          </div>
          <nav className="flex items-center gap-4 text-sm">
            <NavLink to="/" className="text-blue-600 hover:underline">
              Weeks
            </NavLink>
            <NavLink to="/settings" className="text-blue-600 hover:underline">
              Settings
            </NavLink>
            <button className="text-gray-500 hover:text-gray-700" onClick={logout}>
              Sign out
            </button>
          </nav>
        </div>
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}

function useCurrentWeek(): number | null {
  const { data } = useQuery({
    queryKey: ["current-week"],
    queryFn: () => authFetch<{ current_week: number | null }>("/api/settings/current-week"),
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
      <Route path="/login" element={hasToken ? <Navigate to="/" replace /> : <LoginPage />} />
      <Route element={<AuthGate />}>
        <Route element={<LayoutWithCurrentWeek />}>
          <Route path="/" element={<WeeksListPage />} />
          <Route path="/weeks/:number" element={<WeekDetailPage />} />
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