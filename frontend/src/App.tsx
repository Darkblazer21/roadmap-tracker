import { useQuery } from "@tanstack/react-query";

async function fetchHealth(): Promise<{ status: string }> {
  const res = await fetch("/health");
  if (!res.ok) throw new Error("backend unreachable");
  return res.json();
}

export default function App() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
  });

  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-4 p-8">
      <h1 className="text-3xl font-bold tracking-tight">Roadmap Tracker</h1>
      <p className="text-gray-600 dark:text-gray-400">
        Local study tracker — pomodoro, hours, Sunday recaps, GitHub checks.
      </p>

      <div className="mt-4 flex items-center gap-2 rounded-lg border border-gray-200 dark:border-gray-700 px-4 py-2">
        <span
          className={`h-2.5 w-2.5 rounded-full ${
            isLoading
              ? "bg-yellow-400 animate-pulse"
              : isError
                ? "bg-red-500"
                : data?.status === "ok"
                  ? "bg-green-500"
                  : "bg-gray-400"
          }`}
        />
        <span className="font-mono text-sm">
          {isLoading
            ? "Backend connecting..."
            : isError
              ? "Backend unreachable"
              : data?.status === "ok"
                ? "Backend healthy"
                : "Unknown"}
        </span>
      </div>

      <p className="mt-6 text-sm text-gray-500">
        Milestone M0 scaffold — routers and pages land from M1 onward.
      </p>
    </div>
  );
}