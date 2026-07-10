import { Component, type ErrorInfo, type ReactNode } from "react";
import { useT } from "../lib/i18n";

/**
 * ErrorBoundary: catches render errors (e.g. accessing a property of
 * undefined when a query fails mid-navigation) and shows a recovery UI
 * instead of leaving a blank screen the user would have to reload.
 *
 * Class-based because React still requires a class component for
 * ``getDerivedStateFromError`` / ``componentDidCatch``. The functional
 * wrapper below injects translated strings via props.
 */
interface Props {
  children: ReactNode;
  strings: {
    title: string;
    description: string;
    backHome: string;
    reload: string;
  };
}
interface State {
  hasError: boolean;
  message: string;
}

class ErrorBoundaryInner extends Component<Props, State> {
  state: State = { hasError: false, message: "" };

  static getDerivedStateFromError(error: unknown): State {
    return {
      hasError: true,
      message: error instanceof Error ? error.message : String(error),
    };
  }

  componentDidCatch(error: Error, _info: ErrorInfo) {
    console.error("[ErrorBoundary]", error);
  }

  handleReload = () => {
    this.setState({ hasError: false, message: "" });
    window.location.reload();
  };

  handleHome = () => {
    this.setState({ hasError: false, message: "" });
    window.location.href = "/";
  };

  render() {
    if (!this.state.hasError) return this.props.children;
    const s = this.props.strings;
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center p-8 gap-4 text-center">
        <div className="text-5xl">🧭</div>
        <h1 className="text-2xl font-bold">{s.title}</h1>
        <p className="text-gray-600 dark:text-gray-400 max-w-md">
          {s.description}
        </p>
        <pre className="text-xs text-red-600 bg-red-50 dark:bg-red-900/20 rounded p-2 max-w-md overflow-auto">
          {this.state.message}
        </pre>
        <div className="flex gap-3">
          <button
            onClick={this.handleHome}
            className="rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold px-5 py-2"
          >
            {s.backHome}
          </button>
          <button
            onClick={this.handleReload}
            className="rounded-lg bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 font-semibold px-5 py-2"
          >
            {s.reload}
          </button>
        </div>
      </div>
    );
  }
}

/** Functional wrapper that injects i18n strings. */
export function ErrorBoundary({ children }: { children: ReactNode }) {
  const t = useT();
  return (
    <ErrorBoundaryInner
      strings={{
        title: t("error.title"),
        description: t("error.description"),
        backHome: t("error.back_home"),
        reload: t("error.reload"),
      }}
    >
      {children}
    </ErrorBoundaryInner>
  );
}