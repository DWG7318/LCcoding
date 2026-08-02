import type { Language } from "../i18n/catalog";
import type { PhaseId, ReportId } from "../model/snapshot";

export interface SnapshotSource {
  read(): Promise<unknown>;
}

export interface PinPort {
  read(): Promise<boolean>;
  set(enabled: boolean): Promise<boolean>;
}

export interface ViewState {
  language: Language;
  expanded: Set<PhaseId>;
  report: ReportId | null;
  mainScrollTop: number;
  requestInFlight: boolean;
}

export function createViewState(currentPhase?: PhaseId): ViewState {
  return {
    language: "en",
    expanded: currentPhase === undefined ? new Set<PhaseId>() : new Set([currentPhase]),
    report: null,
    mainScrollTop: 0,
    requestInFlight: false,
  };
}
