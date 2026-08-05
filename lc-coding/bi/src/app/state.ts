import type { Language } from "../i18n/catalog";
import type { PhaseId, ReportId, Snapshot } from "../model/snapshot";

export type AppMode = "loading" | "binding" | "dashboard" | "report" | "error";

export type AppState = Readonly<{
  mode: AppMode;
  language: Language;
  snapshot: Readonly<Snapshot> | null;
  report: ReportId | null;
  reportOrigin: ReportId | null;
  expanded: ReadonlySet<PhaseId>;
  errorCode: string | null;
}>;

export type AppAction =
  | Readonly<{ type: "BOUND"; snapshot: Readonly<Snapshot> }>
  | Readonly<{ type: "UNBOUND" }>
  | Readonly<{ type: "ERROR"; code: string }>
  | Readonly<{ type: "TOGGLE_LANGUAGE" }>
  | Readonly<{ type: "TOGGLE_PHASE"; phase: PhaseId }>
  | Readonly<{ type: "OPEN_REPORT"; report: ReportId }>
  | Readonly<{ type: "BACK" }>;

export const initialAppState: AppState = Object.freeze({
  mode: "loading",
  language: "en",
  snapshot: null,
  report: null,
  reportOrigin: null,
  expanded: new Set<PhaseId>(),
  errorCode: null,
});

export function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case "BOUND": {
      const current = action.snapshot.current_phase;
      const expanded = new Set(state.expanded);
      if (expanded.size === 0 && current !== "UNKNOWN") expanded.add(current);
      const mode = state.report === null ? "dashboard" : "report";
      return { ...state, mode, snapshot: action.snapshot, expanded, errorCode: null };
    }
    case "UNBOUND":
      return { ...state, mode: "binding", snapshot: null, report: null, errorCode: null };
    case "ERROR":
      return { ...state, mode: "error", errorCode: action.code };
    case "TOGGLE_LANGUAGE":
      return { ...state, language: state.language === "en" ? "zh_CN" : "en" };
    case "TOGGLE_PHASE": {
      const expanded = new Set(state.expanded);
      if (expanded.has(action.phase)) expanded.delete(action.phase);
      else expanded.add(action.phase);
      return { ...state, expanded };
    }
    case "OPEN_REPORT":
      return { ...state, mode: "report", report: action.report, reportOrigin: action.report };
    case "BACK":
      return { ...state, mode: "dashboard", report: null };
  }
}
