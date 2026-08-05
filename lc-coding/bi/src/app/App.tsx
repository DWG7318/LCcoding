import { useCallback, useEffect, useReducer, useRef, useState } from "react";

import { BindingView } from "../components/BindingView";
import { DashboardView } from "../components/DashboardView";
import { ProtectedReport } from "../components/ProtectedReport";
import { message } from "../i18n/catalog";
import { parseSnapshot, type ReportId } from "../model/snapshot";
import { appReducer, initialAppState } from "./state";

export type BindResult =
  | Readonly<{ ok: true; project: string }>
  | Readonly<{ ok: false; code: string }>;

export interface AppPorts {
  bindProject(projectRoot: string): Promise<BindResult>;
  chooseProject(): Promise<BindResult>;
  getSnapshot(): Promise<unknown>;
  isPinned(): Promise<boolean>;
  setPinned(enabled: boolean): Promise<boolean>;
}

function errorCode(error: unknown): string {
  if (typeof error === "object" && error !== null && "code" in error) {
    const code = (error as { code?: unknown }).code;
    if (typeof code === "string") return code;
  }
  return "BI_PROJECTION_FAILED";
}

export function App({ ports }: Readonly<{ ports: AppPorts }>) {
  const [state, dispatch] = useReducer(appReducer, initialAppState);
  const [bindingBusy, setBindingBusy] = useState(false);
  const [confirmedPin, setConfirmedPin] = useState<boolean | null>(null);
  const [status, setStatus] = useState("");
  const pendingFocus = useRef<"back" | ReportId | null>(null);
  const mounted = useRef(false);
  const language = useRef(state.language);
  const refreshInFlight = useRef<Promise<void> | null>(null);
  const refreshTimer = useRef<number | null>(null);
  const refreshCurrent = useRef<() => Promise<void>>(() => Promise.resolve());
  language.current = state.language;

  const refresh = useCallback((): Promise<void> => {
    if (refreshInFlight.current !== null) return refreshInFlight.current;
    if (refreshTimer.current !== null) {
      window.clearTimeout(refreshTimer.current);
      refreshTimer.current = null;
    }

    let scheduleNext = true;
    let operation!: Promise<void>;
    operation = (async () => {
      try {
        const snapshot = parseSnapshot(await ports.getSnapshot());
        if (!mounted.current) return;
        dispatch({ type: "BOUND", snapshot });
        setStatus(message("app.updated", language.current));
      } catch (error) {
        if (!mounted.current) return;
        const code = errorCode(error);
        if (code === "BI_NO_PROJECT") {
          scheduleNext = false;
          dispatch({ type: "UNBOUND" });
        } else {
          dispatch({ type: "ERROR", code });
        }
        setStatus("");
      } finally {
        if (refreshInFlight.current === operation) refreshInFlight.current = null;
        if (mounted.current && scheduleNext) {
          refreshTimer.current = window.setTimeout(() => {
            refreshTimer.current = null;
            void refreshCurrent.current();
          }, 2_000);
        }
      }
    })();
    refreshInFlight.current = operation;
    return operation;
  }, [ports]);
  refreshCurrent.current = refresh;

  useEffect(() => {
    mounted.current = true;
    void refresh();
    void ports.isPinned().then(
      (value) => {
        if (mounted.current) setConfirmedPin(value);
      },
      () => {
        if (mounted.current) setConfirmedPin(null);
      },
    );
    return () => {
      mounted.current = false;
      if (refreshTimer.current !== null) {
        window.clearTimeout(refreshTimer.current);
        refreshTimer.current = null;
      }
    };
  }, [ports, refresh]);

  useEffect(() => {
    const target = pendingFocus.current;
    if (target === null) return;
    pendingFocus.current = null;
    if (target === "back") {
      document.querySelector<HTMLButtonElement>(".back-button")?.focus();
      return;
    }
    for (const row of document.querySelectorAll<HTMLElement>("[data-step-id]")) {
      const report = state.snapshot?.phases
        .flatMap((phase) => phase.steps)
        .find((step) => step.id === row.dataset.stepId)?.report;
      if (report === target) {
        row.querySelector<HTMLButtonElement>(".open-report")?.focus();
        return;
      }
    }
  }, [state.mode, state.snapshot]);

  const bind = useCallback(
    async (operation: () => Promise<BindResult>) => {
      setBindingBusy(true);
      try {
        const result = await operation();
        if (!result.ok) dispatch({ type: "ERROR", code: result.code });
        else await refresh();
      } catch (error) {
        dispatch({ type: "ERROR", code: errorCode(error) });
      } finally {
        setBindingBusy(false);
      }
    },
    [refresh],
  );

  const languageLabel = message(
    state.language === "en" ? "app.language_current_en" : "app.language_current_zh",
    state.language,
  );

  return (
    <section className="app-shell">
      <header className="control-strip">
        <span className="app-title">{message("app.title", state.language)}</span>
        <button
          type="button"
          className="language-button"
          aria-label={languageLabel}
          onClick={() => dispatch({ type: "TOGGLE_LANGUAGE" })}
        >
          <span className="language-option" aria-current={state.language === "en" ? "true" : undefined}>
            EN
          </span>{" "}
          |{" "}
          <span
            className="language-option"
            aria-current={state.language === "zh_CN" ? "true" : undefined}
          >
            中
          </span>
        </button>
        <button
          type="button"
          className="pin-button"
          disabled={confirmedPin === null}
          aria-pressed={confirmedPin === null ? undefined : confirmedPin}
          onClick={() => {
            if (confirmedPin === null) return;
            void ports.setPinned(!confirmedPin).then(setConfirmedPin, () => undefined);
          }}
        >
          {message(
            confirmedPin === null
              ? "app.pin_checking"
              : confirmedPin
                ? "app.pin_on"
                : "app.pin_off",
            state.language,
          )}
        </button>
      </header>
      <main className="main-body app-body">
        {state.mode === "loading" ? <div className="read-only-label">{message("app.read_only", state.language)}</div> : null}
        {state.mode === "binding" ? (
          <BindingView
            language={state.language}
            busy={bindingBusy}
            errorCode={state.errorCode}
            onBind={(root) => void bind(() => ports.bindProject(root))}
            onChoose={() => void bind(() => ports.chooseProject())}
          />
        ) : null}
        {state.mode === "error" ? (
          <div className="error-projection" role="alert">
            {message("app.binding_error", state.language)}
          </div>
        ) : null}
        {state.mode === "dashboard" && state.snapshot !== null ? (
          <DashboardView
            snapshot={state.snapshot}
            language={state.language}
            expanded={state.expanded}
            onTogglePhase={(phase) => dispatch({ type: "TOGGLE_PHASE", phase })}
            onOpenReport={(report) => {
              pendingFocus.current = "back";
              dispatch({ type: "OPEN_REPORT", report });
            }}
          />
        ) : null}
        {state.mode === "report" && state.snapshot !== null && state.report !== null ? (
          <ProtectedReport
            report={state.snapshot.reports[state.report]}
            language={state.language}
            onBack={() => {
              pendingFocus.current = state.reportOrigin;
              dispatch({ type: "BACK" });
            }}
          />
        ) : null}
      </main>
      <footer className="refresh-strip">
        <button type="button" className="refresh-button" onClick={() => void refresh()}>
          {message("app.refresh", state.language)}
        </button>
        <span className="refresh-status" role="status" aria-live="polite">
          {status}
        </span>
      </footer>
    </section>
  );
}
