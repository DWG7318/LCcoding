import { message } from "./i18n/catalog";
import {
  parseSnapshot,
  type PhaseId,
  type ReportId,
  type Snapshot,
  type StepId,
} from "./model/snapshot";
import { renderMainView } from "./render/main-view";
import { renderReportView } from "./render/report-view";
import { createViewState, type PinPort, type SnapshotSource } from "./state/view-state";

export interface BiController {
  refresh(): Promise<void>;
  destroy(): void;
}

export function mountBi(
  root: HTMLElement,
  { source, pin }: { source: SnapshotSource; pin: PinPort },
): BiController {
  type BodyFocusToken =
    | Readonly<{ kind: "phase"; phaseId: PhaseId }>
    | Readonly<{ kind: "open"; stepId: StepId; reportId: ReportId }>
    | Readonly<{ kind: "back" }>;

  const state = createViewState();
  let destroyed = false;
  let confirmedPin: boolean | null = null;
  let pinSetInFlight = false;
  let pinErrorActive = false;
  let inFlight: Promise<void> | null = null;
  let refreshTimer: ReturnType<typeof setTimeout> | null = null;
  let expandedInitialized = false;
  let currentSnapshot: Readonly<Snapshot> | null = null;
  let errorProjectionActive = false;
  let recoveryFocusToken: BodyFocusToken | null = null;

  const document = root.ownerDocument;
  const shell = document.createElement("section");
  shell.className = "app-shell";
  const controlStrip = document.createElement("header");
  controlStrip.className = "control-strip";
  const appTitle = document.createElement("span");
  appTitle.className = "app-title";
  appTitle.textContent = message("app.title", state.language);
  const languageButton = document.createElement("button");
  languageButton.type = "button";
  languageButton.className = "language-button";

  const renderLanguageControl = (): void => {
    const englishOption = document.createElement("span");
    englishOption.className = "language-option";
    englishOption.textContent = "EN";
    if (state.language === "en") englishOption.setAttribute("aria-current", "true");

    const chineseOption = document.createElement("span");
    chineseOption.className = "language-option";
    chineseOption.textContent = "中";
    if (state.language === "zh_CN") chineseOption.setAttribute("aria-current", "true");

    languageButton.replaceChildren(
      englishOption,
      document.createTextNode(" | "),
      chineseOption,
    );
    languageButton.setAttribute(
      "aria-label",
      message(
        state.language === "en" ? "app.language_current_en" : "app.language_current_zh",
        state.language,
      ),
    );
  };
  renderLanguageControl();

  const pinButton = document.createElement("button");
  pinButton.type = "button";
  pinButton.className = "pin-button";
  pinButton.textContent = message("app.pin_checking", state.language);
  pinButton.disabled = true;

  const body = document.createElement("main");
  body.className = "main-body app-body";

  const captureBodyFocus = (): BodyFocusToken | null => {
    const active = document.activeElement;
    if (active === null || !body.contains(active)) return null;

    if (state.report !== null && active.closest(".back-button") !== null) {
      return { kind: "back" };
    }

    const open = active.closest(".open-report");
    const stepContainer = open?.closest<HTMLElement>("[data-step-id]");
    if (stepContainer !== null && stepContainer !== undefined && currentSnapshot !== null) {
      const renderedStepId = stepContainer.dataset.stepId;
      for (const phase of currentSnapshot.phases) {
        for (const step of phase.steps) {
          if (step.id !== renderedStepId || step.report === null) continue;
          return { kind: "open", stepId: step.id, reportId: step.report };
        }
      }
    }

    const summary = active.closest(".phase-summary");
    const phaseContainer = summary?.closest<HTMLElement>("[data-phase-id]");
    if (phaseContainer !== null && phaseContainer !== undefined && currentSnapshot !== null) {
      const renderedPhaseId = phaseContainer.dataset.phaseId;
      for (const phase of currentSnapshot.phases) {
        if (phase.id === renderedPhaseId) {
          return { kind: "phase", phaseId: phase.id };
        }
      }
    }

    return null;
  };

  const restoreBodyFocus = (token: BodyFocusToken): void => {
    if (token.kind === "back") {
      if (state.report !== null) {
        body.querySelector<HTMLButtonElement>(".back-button")?.focus();
      }
      return;
    }
    if (currentSnapshot === null || state.report !== null) return;

    if (token.kind === "phase") {
      if (!currentSnapshot.phases.some((phase) => phase.id === token.phaseId)) return;
      for (const container of body.querySelectorAll<HTMLElement>("[data-phase-id]")) {
        if (container.dataset.phaseId !== token.phaseId) continue;
        container.querySelector<HTMLButtonElement>(".phase-summary")?.focus();
        return;
      }
      return;
    }

    let trusted = false;
    for (const phase of currentSnapshot.phases) {
      for (const step of phase.steps) {
        if (step.id === token.stepId && step.report === token.reportId) {
          trusted = true;
          break;
        }
      }
      if (trusted) break;
    }
    if (!trusted) return;
    for (const container of body.querySelectorAll<HTMLElement>("[data-step-id]")) {
      if (container.dataset.stepId !== token.stepId) continue;
      container.querySelector<HTMLButtonElement>(".open-report")?.focus();
      return;
    }
  };

  const refreshButton = document.createElement("button");
  refreshButton.type = "button";
  refreshButton.className = "refresh-button";
  refreshButton.textContent = message("app.refresh", state.language);
  const status = document.createElement("div");
  status.className = "refresh-status";
  status.setAttribute("role", "status");
  status.setAttribute("aria-live", "polite");

  const refreshStrip = document.createElement("footer");
  refreshStrip.className = "refresh-strip";
  controlStrip.append(appTitle, languageButton, pinButton);
  refreshStrip.append(refreshButton, status);
  shell.append(controlStrip, body, refreshStrip);
  root.replaceChildren(shell);

  const renderConfirmedPin = (value: boolean): void => {
    if (destroyed) return;
    confirmedPin = value;
    pinErrorActive = false;
    pinButton.disabled = false;
    pinButton.textContent = message(
      value ? "app.pin_on" : "app.pin_off",
      state.language,
    );
    pinButton.setAttribute("aria-pressed", String(value));
    status.textContent = "";
  };

  const handlePinClick = (): void => {
    if (destroyed || pinSetInFlight || confirmedPin === null) return;

    const previous = confirmedPin;
    const requested = !previous;
    pinSetInFlight = true;
    pinButton.disabled = true;
    pinButton.textContent = message("app.pin_checking", state.language);

    void pin
      .set(requested)
      .then(
        (returned) => {
          if (destroyed) return;
          renderConfirmedPin(returned);
        },
        () => {
          if (destroyed) return;
          renderConfirmedPin(previous);
          pinErrorActive = true;
          status.textContent = message("app.pin_error", state.language);
        },
      )
      .finally(() => {
        pinSetInFlight = false;
      });
  };

  pinButton.addEventListener("click", handlePinClick);

  void pin.read().then(
    (isPinned) => {
      if (destroyed) return;
      renderConfirmedPin(isPinned);
    },
    () => {
      if (destroyed) return;
      pinErrorActive = true;
      pinButton.disabled = true;
      pinButton.textContent = message("app.pin_unavailable", state.language);
      pinButton.removeAttribute("aria-pressed");
      status.textContent = message("app.pin_error", state.language);
    },
  );

  const renderErrorProjection = (): void => {
    if (destroyed) return;

    const ownerDocument = root.ownerDocument;
    const errorProjection = ownerDocument.createElement("section");
    errorProjection.className = "error-projection";
    errorProjection.setAttribute("role", "alert");
    errorProjection.tabIndex = -1;
    const projectName = ownerDocument.createElement("h1");
    projectName.textContent = message("app.unnamed_project", state.language);
    const errorState = ownerDocument.createElement("span");
    errorState.className = "state state--error";
    const errorStateGlyph = ownerDocument.createElement("span");
    errorStateGlyph.className = "state-glyph";
    errorStateGlyph.setAttribute("aria-hidden", "true");
    const errorStateText = ownerDocument.createElement("span");
    errorStateText.className = "state-text";
    errorStateText.textContent = message("state.error", state.language);
    errorState.append(errorStateGlyph, errorStateText);
    const errorMessage = ownerDocument.createElement("p");
    errorMessage.textContent = message("app.error", state.language);
    errorProjection.append(projectName, errorState, errorMessage);

    if (state.report === null) {
      body.replaceChildren(errorProjection);
    } else {
      const back = ownerDocument.createElement("button");
      back.type = "button";
      back.className = "back-button";
      back.textContent = message("app.back", state.language);
      back.addEventListener("click", () => {
        if (destroyed || state.report === null) return;
        state.report = null;
        renderErrorProjection();
      });
      const protectedNotice = ownerDocument.createElement("p");
      protectedNotice.className = "protected-notice";
      protectedNotice.textContent = message("app.protected", state.language);
      body.replaceChildren(back, protectedNotice, errorProjection);
    }

    errorProjectionActive = true;
    if (!pinErrorActive) status.textContent = "";
  };

  const renderCurrentSnapshot = (): void => {
    if (destroyed || currentSnapshot === null) return;
    if (currentSnapshot.health === "error") {
      renderErrorProjection();
      return;
    }
    errorProjectionActive = false;
    if (state.report !== null) {
      renderReportView(
        body,
        currentSnapshot.reports[state.report],
        state.language,
        returnFromReport,
      );
      return;
    }
    renderMainView(body, currentSnapshot, state.language, state.expanded, {
      togglePhase: (phase) => {
        if (destroyed || currentSnapshot === null) return;
        const toggledPhase = phase;
        if (state.expanded.has(toggledPhase)) state.expanded.delete(toggledPhase);
        else state.expanded.add(toggledPhase);
        renderCurrentSnapshot();
        for (const container of body.querySelectorAll<HTMLElement>("[data-phase-id]")) {
          if (container.dataset.phaseId !== toggledPhase) continue;
          container.querySelector<HTMLButtonElement>(".phase-summary")?.focus();
          break;
        }
      },
      openReport: (reportId) => {
        if (destroyed || currentSnapshot === null) return;
        state.report = reportId;
        state.mainScrollTop = body.scrollTop;
        renderReportView(
          body,
          currentSnapshot.reports[reportId],
          state.language,
          returnFromReport,
        );
        body.querySelector<HTMLButtonElement>(".back-button")?.focus();
      },
    });
  };

  function returnFromReport(): void {
    if (destroyed || currentSnapshot === null || state.report === null) return;

    const reportId = state.report;
    state.report = null;
    renderCurrentSnapshot();
    body.scrollTop = state.mainScrollTop;

    let trustedStepId: string | null = null;
    for (const phase of currentSnapshot.phases) {
      for (const step of phase.steps) {
        if (step.report !== reportId) continue;
        trustedStepId = step.id;
        break;
      }
      if (trustedStepId !== null) break;
    }
    if (trustedStepId === null) return;

    for (const stepRow of body.querySelectorAll<HTMLElement>("[data-step-id]")) {
      if (stepRow.dataset.stepId !== trustedStepId) continue;
      stepRow.querySelector<HTMLButtonElement>(".open-report")?.focus();
      break;
    }
  }

  const handleLanguageClick = (): void => {
    if (destroyed) return;

    const scrollTop = body.scrollTop;
    const focusedControl =
      document.activeElement === languageButton
        ? "language"
        : document.activeElement === pinButton
          ? "pin"
          : document.activeElement === refreshButton
            ? "refresh"
            : null;
    const statusKey =
      status.textContent === message("app.pin_error", state.language)
        ? "app.pin_error"
        : status.textContent === message("app.updated", state.language)
          ? "app.updated"
          : null;

    state.language = state.language === "en" ? "zh_CN" : "en";
    renderLanguageControl();
    appTitle.textContent = message("app.title", state.language);
    refreshButton.textContent = message("app.refresh", state.language);
    pinButton.textContent = message(
      pinSetInFlight
        ? "app.pin_checking"
        : confirmedPin !== null
          ? confirmedPin
            ? "app.pin_on"
            : "app.pin_off"
          : pinErrorActive
            ? "app.pin_unavailable"
            : "app.pin_checking",
      state.language,
    );
    status.textContent = statusKey === null ? "" : message(statusKey, state.language);

    const reportId = state.report;
    if (errorProjectionActive) {
      renderErrorProjection();
    } else if (reportId !== null && currentSnapshot !== null && currentSnapshot.health === "ok") {
      renderReportView(
        body,
        currentSnapshot.reports[reportId],
        state.language,
        returnFromReport,
      );
    } else {
      renderCurrentSnapshot();
    }
    body.scrollTop = scrollTop;

    if (focusedControl === "language") languageButton.focus();
    else if (focusedControl === "pin") pinButton.focus();
    else if (focusedControl === "refresh") refreshButton.focus();
  };

  languageButton.addEventListener("click", handleLanguageClick);

  const render = (raw: unknown): void => {
    if (destroyed) return;
    const active = document.activeElement;
    const activeWasInside = active !== null && body.contains(active);
    const capturedFocusToken = captureBodyFocus();
    const snapshot = parseSnapshot(raw);
    if (destroyed) return;
    currentSnapshot = snapshot;
    if (snapshot.health === "error") {
      if (capturedFocusToken !== null) recoveryFocusToken = capturedFocusToken;
      renderErrorProjection();
      const errorFocusToken =
        capturedFocusToken ?? (activeWasInside ? recoveryFocusToken : null);
      if (errorFocusToken?.kind === "back") restoreBodyFocus(errorFocusToken);
      else if (errorFocusToken !== null) {
        body.querySelector<HTMLElement>('[role="alert"]')?.focus();
      }
      return;
    }
    const successFocusToken =
      capturedFocusToken ?? (activeWasInside ? recoveryFocusToken : null);
    if (
      !expandedInitialized &&
      snapshot.health === "ok" &&
      snapshot.current_phase !== "UNKNOWN"
    ) {
      state.expanded.add(snapshot.current_phase);
      expandedInitialized = true;
    }
    renderCurrentSnapshot();
    if (successFocusToken !== null) restoreBodyFocus(successFocusToken);
    recoveryFocusToken = null;
    if (!pinErrorActive) {
      status.textContent =
        snapshot.health === "ok" ? message("app.updated", state.language) : "";
    }
  };

  const renderInputFailure = (): void => {
    if (destroyed) return;
    const active = document.activeElement;
    const activeWasInside = active !== null && body.contains(active);
    const capturedFocusToken = captureBodyFocus();
    if (capturedFocusToken !== null) recoveryFocusToken = capturedFocusToken;
    currentSnapshot = null;
    renderErrorProjection();
    const errorFocusToken =
      capturedFocusToken ?? (activeWasInside ? recoveryFocusToken : null);
    if (errorFocusToken?.kind === "back") restoreBodyFocus(errorFocusToken);
    else if (errorFocusToken !== null) {
      body.querySelector<HTMLElement>('[role="alert"]')?.focus();
    }
  };

  const refresh = (): Promise<void> => {
    if (destroyed) return Promise.resolve();
    if (inFlight !== null) return inFlight;

    if (refreshTimer !== null) {
      clearTimeout(refreshTimer);
      refreshTimer = null;
    }

    state.requestInFlight = true;
    let current: Promise<void>;
    try {
      current = source.read().then(
        (raw) => {
          try {
            render(raw);
          } catch {
            renderInputFailure();
          }
        },
        () => {
          renderInputFailure();
        },
      );
    } catch {
      renderInputFailure();
      current = Promise.resolve();
    }
    inFlight = current;

    const finish = (): void => {
      if (inFlight !== current) return;
      inFlight = null;
      state.requestInFlight = false;
      if (destroyed) return;
      refreshTimer = setTimeout(() => {
        refreshTimer = null;
        void refresh().catch(() => undefined);
      }, 2_000);
    };
    void current.then(finish, finish);
    return current;
  };

  const handleRefreshClick = (): void => {
    void refresh().catch(() => undefined);
  };
  refreshButton.addEventListener("click", handleRefreshClick);

  void refresh().catch(() => undefined);

  return {
    refresh,
    destroy() {
      destroyed = true;
      if (refreshTimer !== null) {
        clearTimeout(refreshTimer);
        refreshTimer = null;
      }
      pinButton.removeEventListener("click", handlePinClick);
      languageButton.removeEventListener("click", handleLanguageClick);
      refreshButton.removeEventListener("click", handleRefreshClick);
    },
  };
}
