import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { postJSON, setToken } from "../lib/api";

export default function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const login = useMutation({
    mutationFn: () =>
      postJSON<{ access_token: string }>("/api/auth/login", { username, password }),
    onSuccess: (data) => {
      setToken(data.access_token);
      navigate("/");
    },
    onError: (e: Error) => setError(e.message),
  });

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <form
        className="w-full max-w-sm space-y-4 rounded-2xl border border-gray-200 dark:border-gray-700 p-6"
        onSubmit={(e) => {
          e.preventDefault();
          login.mutate();
        }}
      >
        <h1 className="text-2xl font-bold text-center">Roadmap Tracker</h1>
        <p className="text-sm text-gray-500 text-center">Sign in to continue</p>

        {error && (
          <div className="rounded bg-red-100 text-red-700 px-3 py-2 text-sm">
            {error}
          </div>
        )}

        <label className="block">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Username
          </span>
          <input
            className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Password
          </span>
          <input
            type="password"
            className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>

        <button
          type="submit"
          disabled={login.isPending}
          className="w-full rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold py-2"
        >
          {login.isPending ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </div>
  );
}