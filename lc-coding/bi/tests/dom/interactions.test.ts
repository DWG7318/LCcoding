import "./setup";

import { describe, expect, it, vi } from "vitest";

import { message, type Language } from "../../src/i18n/catalog";
import { mountBi } from "../../src/main";
import { parseSnapshot, type ReportId, type RowKey } from "../../src/model/snapshot";
import {
  createPreviewDependencies,
  resolvePreviewCase,
  resolveRuntimePreviewCase,
} from "../../src/preview";
import { renderMainView } from "../../src/render/main-view";
import { renderReportView } from "../../src/render/report-view";
import {
  createViewState,
  type PinPort,
  type SnapshotSource,
  type ViewState,
} from "../../src/state/view-state";
import errorFixture from "../fixtures/snapshot-error.json";
import successFixture from "../fixtures/snapshot-ok.json";

const REPORT_CASES = [
  ["proposal", ["row.conclusion", "row.initial_gate"]],
  ["candidate", ["row.identity", "row.integrity"]],
  ["calabash", ["row.status", "row.version_record"]],
  ["simulation", ["row.status", "row.current_phase"]],
  ["workflow", ["row.status", "row.current_phase"]],
  ["ui", ["row.status", "row.current_phase"]],
] as const satisfies readonly (readonly [ReportId, readonly RowKey[]])[];

const LANGUAGES = ["en", "zh_CN"] as const satisfies readonly Language[];
const REPORT_LANGUAGE_CASES = REPORT_CASES.flatMap(([reportId, rowKeys]) =>
  LANGUAGES.map((language) => [reportId, rowKeys, language] as const),
);
const EXPECTED_VERSION = {
  proposal: (language: Language) => message("value.not_recorded", language),
  candidate: (_language: Language) => "v1.11.6",
  calabash: (_language: Language) => "v2.4.0",
  simulation: (language: Language) => message("value.not_recorded", language),
  workflow: (language: Language) => message("value.not_recorded", language),
  ui: (language: Language) => message("value.not_recorded", language),
} as const satisfies Readonly<Record<ReportId, (language: Language) => string>>;
const EXPECTED_ROW_TEXT: Readonly<
  Record<ReportId, (language: Language) => readonly string[]>
> = {
  proposal: (language) => [message("state.done", language), message("state.done", language)],
  candidate: (language) => [
    message("value.locked", language),
    message("value.recorded", language),
  ],
  calabash: (language) => [
    message("state.done", language),
    message("value.recorded", language),
  ],
  simulation: (language) => [
    message("state.done", language),
    message("phase.PRODUCT_FORMATION", language),
  ],
  workflow: (language) => [
    message("state.active", language),
    message("phase.PRODUCT_FORMATION", language),
  ],
  ui: (language) => [
    message("state.error", language),
    message("phase.PRODUCT_FORMATION", language),
  ],
};
const successSnapshot = parseSnapshot(successFixture);
const safeSource: SnapshotSource = {
  read: async (): Promise<unknown> => successFixture,
};

async function flushAsyncDom(): Promise<void> {
  await Promise.resolve();
  await Promise.resolve();
}

function visibleEnabledButtons(root: ParentNode): HTMLButtonElement[] {
  return [...root.querySelectorAll<HTMLButtonElement>("button")].filter(
    (button) => !button.disabled && button.closest("[hidden]") === null,
  );
}

function deferred<T>(): {
  readonly promise: Promise<T>;
  readonly resolve: (value: T) => void;
  readonly reject: (reason?: unknown) => void;
} {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });

  return { promise, resolve, reject };
}

describe("protected report interactions", () => {
  it.each(REPORT_LANGUAGE_CASES)("renders %s rows in %s", (reportId, rowKeys, language) => {
    const root = document.createElement("div");
    let backCalls = 0;

    renderReportView(root, successSnapshot.reports[reportId], language, () => {
      backCalls += 1;
    });

    expect(
      [...root.querySelectorAll<HTMLElement>(".report-row")].map((row) => row.dataset.rowKey),
    ).toEqual(rowKeys);
    const reportRows = [...root.querySelectorAll<HTMLElement>(".report-row")];
    const fixtureRows = successSnapshot.reports[reportId].rows;
    expect(
      reportRows.map(
        (row) => row.querySelector(".state-text, .row-value")?.textContent,
      ),
    ).toEqual(EXPECTED_ROW_TEXT[reportId](language));
    for (const [index, fixtureRow] of fixtureRows.entries()) {
      const row = reportRows[index]!;
      if (fixtureRow.value.kind === "view_state") {
        expect(
          row.querySelector(`.state--${fixtureRow.value.value} .state-text`),
        ).not.toBeNull();
      } else {
        expect(row.querySelector(".state")).toBeNull();
        expect(row.querySelector(".row-value")).not.toBeNull();
      }
    }
    expect(root.querySelector(".report-heading")?.textContent).toContain(
      message(`report.${reportId}`, language),
    );
    expect(root.querySelector(".report-version")?.textContent).toBe(
      EXPECTED_VERSION[reportId](language),
    );
    expect(root.querySelector(".protected-notice")?.textContent).toBe(
      message("app.protected", language),
    );

    const back = root.querySelector<HTMLButtonElement>("button.back-button");
    expect(back?.type).toBe("button");
    expect(back?.textContent).toBe(message("app.back", language));
    back?.click();
    expect(backCalls).toBe(1);

    expect(root.querySelector("a, form, input, [href], [src], [download]")).toBeNull();
    const html = root.outerHTML.toLowerCase();
    expect(html).not.toContain("file:");
    expect(html).not.toContain("http:");
    expect(html).not.toContain("https:");
  });

  it("creates the closed local view-state defaults", () => {
    const state: ViewState = createViewState("PRODUCT_FORMATION");
    const source: SnapshotSource = {
      read: async (): Promise<unknown> => successFixture,
    };
    const pin: PinPort = {
      read: async (): Promise<boolean> => false,
      set: async (enabled: boolean): Promise<boolean> => enabled,
    };

    expect(state.language).toBe("en");
    expect([...state.expanded]).toEqual(["PRODUCT_FORMATION"]);
    expect(state.report).toBeNull();
    expect(Object.prototype.hasOwnProperty.call(state, "reportOrigin")).toBe(false);
    expect(state.mainScrollTop).toBe(0);
    expect(state.requestInFlight).toBe(false);
    expect([...createViewState().expanded]).toEqual([]);
    expect(source && pin).toBeTruthy();
  });

  it("keeps Pin unconfirmed until its initial read settles", async () => {
    const root = document.createElement("div");
    const pinRead = deferred<boolean>();
    let setCalls = 0;
    const source: SnapshotSource = {
      read: async (): Promise<unknown> => successFixture,
    };
    const pin: PinPort = {
      read: (): Promise<boolean> => pinRead.promise,
      set: async (enabled: boolean): Promise<boolean> => {
        setCalls += 1;
        return enabled;
      },
    };
    let controller: ReturnType<typeof mountBi> | undefined;
    document.body.append(root);

    try {
      controller = mountBi(root, { source, pin });

      const checking = root.querySelector<HTMLButtonElement>(".pin-button");
      expect(checking?.disabled).toBe(true);
      expect(checking?.textContent).toBe(message("app.pin_checking", "en"));
      expect(checking?.hasAttribute("aria-pressed")).toBe(false);
      expect(setCalls).toBe(0);

      pinRead.resolve(true);
      await pinRead.promise;
      await Promise.resolve();

      const confirmed = root.querySelector<HTMLButtonElement>(".pin-button");
      expect(confirmed?.disabled).toBe(false);
      expect(confirmed?.textContent).toBe(message("app.pin_on", "en"));
      expect(confirmed?.getAttribute("aria-pressed")).toBe("true");
      expect(setCalls).toBe(0);
    } finally {
      controller?.destroy();
      root.remove();
    }
  });

  it("uses a confirmed false Pin read as the authoritative initial state", async () => {
    const root = document.createElement("div");
    let setCalls = 0;
    const pin: PinPort = {
      read: async (): Promise<boolean> => false,
      set: async (enabled: boolean): Promise<boolean> => {
        setCalls += 1;
        return enabled;
      },
    };
    let controller: ReturnType<typeof mountBi> | undefined;
    document.body.append(root);

    try {
      controller = mountBi(root, { source: safeSource, pin });
      await flushAsyncDom();

      const confirmed = root.querySelector<HTMLButtonElement>(".pin-button");
      expect(confirmed?.disabled).toBe(false);
      expect(confirmed?.textContent).toBe(message("app.pin_off", "en"));
      expect(confirmed?.getAttribute("aria-pressed")).toBe("false");
      expect(setCalls).toBe(0);
    } finally {
      controller?.destroy();
      root.remove();
    }
  });

  it("keeps the confirmed Pin state until set returns its authoritative value", async () => {
    const fixtureBefore = JSON.stringify(successFixture);
    const root = document.createElement("div");
    const pinSet = deferred<boolean>();
    const setArgs: boolean[] = [];
    const pin: PinPort = {
      read: async (): Promise<boolean> => false,
      set: (enabled: boolean): Promise<boolean> => {
        setArgs.push(enabled);
        return pinSet.promise;
      },
    };
    let controller: ReturnType<typeof mountBi> | undefined;
    document.body.append(root);

    try {
      controller = mountBi(root, { source: safeSource, pin });
      await flushAsyncDom();

      const button = root.querySelector<HTMLButtonElement>(".pin-button");
      button?.click();

      expect(setArgs).toEqual([true]);
      expect(button?.disabled).toBe(true);
      expect(button?.textContent).toBe(message("app.pin_checking", "en"));
      expect(button?.getAttribute("aria-pressed")).toBe("false");

      button?.click();
      expect(setArgs).toEqual([true]);

      pinSet.resolve(false);
      await pinSet.promise;
      await flushAsyncDom();

      expect(button?.disabled).toBe(false);
      expect(button?.textContent).toBe(message("app.pin_off", "en"));
      expect(button?.getAttribute("aria-pressed")).toBe("false");
      expect(JSON.stringify(successFixture)).toBe(fixtureBefore);
    } finally {
      controller?.destroy();
      root.remove();
    }
  });

  it("restores the confirmed Pin state after a sanitized set rejection", async () => {
    const root = document.createElement("div");
    const pinSet = deferred<boolean>();
    const setArgs: boolean[] = [];
    const pin: PinPort = {
      read: async (): Promise<boolean> => true,
      set: (enabled: boolean): Promise<boolean> => {
        setArgs.push(enabled);
        return pinSet.promise;
      },
    };
    let controller: ReturnType<typeof mountBi> | undefined;
    document.body.append(root);

    try {
      controller = mountBi(root, { source: safeSource, pin });
      await flushAsyncDom();

      const button = root.querySelector<HTMLButtonElement>(".pin-button");
      button?.click();

      expect(setArgs).toEqual([false]);
      expect(button?.disabled).toBe(true);
      expect(button?.textContent).toBe(message("app.pin_checking", "en"));
      expect(button?.getAttribute("aria-pressed")).toBe("true");

      button?.click();
      expect(setArgs).toEqual([false]);

      pinSet.reject(new Error("private pin path"));
      await pinSet.promise.catch(() => undefined);
      await flushAsyncDom();

      expect(button?.disabled).toBe(false);
      expect(button?.textContent).toBe(message("app.pin_on", "en"));
      expect(button?.getAttribute("aria-pressed")).toBe("true");
      expect(
        root.querySelector<HTMLElement>('[role="status"][aria-live="polite"]')
          ?.textContent,
      ).toBe(message("app.pin_error", "en"));
      const html = root.outerHTML.toLowerCase();
      expect(html).not.toContain("private pin path");
      expect(html).not.toContain("traceback");
      expect(html).not.toContain("file:");
      expect(html).not.toContain("http:");
      expect(html).not.toContain("https:");
    } finally {
      controller?.destroy();
      root.remove();
    }
  });

  it("keeps Pin unavailable and announces a sanitized initial read failure", async () => {
    const root = document.createElement("div");
    let setCalls = 0;
    const pin: PinPort = {
      read: (): Promise<boolean> => Promise.reject(new Error("private detail")),
      set: async (enabled: boolean): Promise<boolean> => {
        setCalls += 1;
        return enabled;
      },
    };
    let controller: ReturnType<typeof mountBi> | undefined;
    document.body.append(root);

    try {
      controller = mountBi(root, { source: safeSource, pin });
      await flushAsyncDom();

      const unavailable = root.querySelector<HTMLButtonElement>(".pin-button");
      expect(unavailable?.disabled).toBe(true);
      expect(unavailable?.textContent).toBe(message("app.pin_unavailable", "en"));
      expect(unavailable?.hasAttribute("aria-pressed")).toBe(false);

      const announcement = root.querySelector<HTMLElement>(
        '[role="status"][aria-live="polite"]',
      );
      expect(announcement?.textContent).toBe(message("app.pin_error", "en"));
      expect(setCalls).toBe(0);
      const html = root.outerHTML.toLowerCase();
      expect(html).not.toContain("private detail");
      expect(html).not.toContain("path");
      expect(html).not.toContain("traceback");
    } finally {
      controller?.destroy();
      root.remove();
    }
  });

  it("joins refresh while pending and schedules only after settlement", async () => {
    vi.useFakeTimers();
    const root = document.createElement("div");
    const reads: Array<ReturnType<typeof deferred<unknown>>> = [];
    const source: SnapshotSource = {
      read: (): Promise<unknown> => {
        const next = deferred<unknown>();
        reads.push(next);
        return next.promise;
      },
    };
    const pin: PinPort = {
      read: async (): Promise<boolean> => false,
      set: async (enabled: boolean): Promise<boolean> => enabled,
    };
    let controller: ReturnType<typeof mountBi> | undefined;
    document.body.append(root);

    try {
      controller = mountBi(root, { source, pin });
      expect(reads).toHaveLength(1);

      const joinedA = controller.refresh();
      const joinedB = controller.refresh();
      expect(joinedA).toBe(joinedB);
      expect(reads).toHaveLength(1);

      reads[0]!.resolve(successFixture);
      await reads[0]!.promise;
      await joinedA;
      expect(vi.getTimerCount()).toBe(1);

      await vi.advanceTimersByTimeAsync(1_999);
      expect(reads).toHaveLength(1);
      await vi.advanceTimersByTimeAsync(1);
      expect(reads).toHaveLength(2);

      await vi.advanceTimersByTimeAsync(4_000);
      expect(reads).toHaveLength(2);

      reads[1]!.resolve(successFixture);
      await reads[1]!.promise;
      await flushAsyncDom();
      expect(vi.getTimerCount()).toBe(1);

      controller.destroy();
      expect(vi.getTimerCount()).toBe(0);
    } finally {
      controller?.destroy();
      root.remove();
      vi.useRealTimers();
    }
  });

  it("restarts the refresh delay after a manual read settles", async () => {
    vi.useFakeTimers();
    const root = document.createElement("div");
    const reads: Array<ReturnType<typeof deferred<unknown>>> = [];
    const source: SnapshotSource = {
      read: (): Promise<unknown> => {
        const next = deferred<unknown>();
        reads.push(next);
        return next.promise;
      },
    };
    const pin: PinPort = {
      read: async (): Promise<boolean> => false,
      set: async (enabled: boolean): Promise<boolean> => enabled,
    };
    let controller: ReturnType<typeof mountBi> | undefined;
    document.body.append(root);

    try {
      controller = mountBi(root, { source, pin });
      expect(reads).toHaveLength(1);
      reads[0]!.resolve(successFixture);
      await reads[0]!.promise;
      await flushAsyncDom();
      expect(vi.getTimerCount()).toBe(1);

      const manual = controller.refresh();
      expect(vi.getTimerCount()).toBe(0);
      expect(reads).toHaveLength(2);

      await vi.advanceTimersByTimeAsync(4_000);
      expect(reads).toHaveLength(2);

      reads[1]!.resolve(successFixture);
      await reads[1]!.promise;
      await manual;
      expect(vi.getTimerCount()).toBe(1);

      await vi.advanceTimersByTimeAsync(1_999);
      expect(reads).toHaveLength(2);
      await vi.advanceTimersByTimeAsync(1);
      expect(reads).toHaveLength(3);
    } finally {
      controller?.destroy();
      root.remove();
      vi.useRealTimers();
    }
  });

  it("announces a successful refreshed main projection", async () => {
    vi.useFakeTimers();
    const fixtureBefore = JSON.stringify(successFixture);
    const recoveredFixture = JSON.parse(fixtureBefore) as typeof successFixture;
    recoveredFixture.project = "Recovered Project";
    const root = document.createElement("div");
    const reads: Array<ReturnType<typeof deferred<unknown>>> = [];
    const source: SnapshotSource = {
      read: (): Promise<unknown> => {
        const next = deferred<unknown>();
        reads.push(next);
        return next.promise;
      },
    };
    const pin: PinPort = {
      read: async (): Promise<boolean> => false,
      set: async (enabled: boolean): Promise<boolean> => enabled,
    };
    let controller: ReturnType<typeof mountBi> | undefined;
    document.body.append(root);

    try {
      controller = mountBi(root, { source, pin });
      const joined = controller.refresh();
      reads[0]!.resolve(successFixture);
      await joined;
      await flushAsyncDom();

      expect(root.querySelector(".project-name")?.textContent).toBe(
        "Example Project",
      );
      expect(
        root.querySelector<HTMLElement>(
          '.refresh-status[role="status"][aria-live="polite"]',
        )?.textContent,
      ).toBe(message("app.updated", "en"));

      const failedRefresh = controller.refresh();
      expect(reads).toHaveLength(2);
      reads[1]!.reject(
        new Error(
          "C:\\private\\STATUS.json\nTraceback\nsecret-refresh-detail",
        ),
      );
      await failedRefresh.catch(() => undefined);
      await flushAsyncDom();

      const mainBody = root.querySelector<HTMLElement>(".main-body");
      const alerts = mainBody?.querySelectorAll<HTMLElement>("[role=alert]");
      expect(alerts).toHaveLength(1);
      expect(mainBody?.children).toHaveLength(1);
      const alert = mainBody?.querySelector<HTMLElement>(
        ".error-projection[role=alert]",
      );
      expect(alert?.textContent).toContain(message("app.unnamed_project", "en"));
      expect(alert?.textContent).toContain(message("app.error", "en"));
      expect(mainBody?.querySelector(".phase-list")).toBeNull();
      expect(mainBody?.querySelector(".open-report")).toBeNull();
      expect(mainBody?.textContent).not.toContain("Example Project");
      expect(mainBody?.textContent).not.toContain(message("state.done", "en"));
      expect(
        root.querySelector<HTMLElement>(
          '.refresh-status[role="status"][aria-live="polite"]',
        )?.textContent,
      ).not.toBe(message("app.updated", "en"));
      const failedHtml = root.outerHTML.toLowerCase();
      expect(failedHtml).not.toContain("private");
      expect(failedHtml).not.toContain("status.json");
      expect(failedHtml).not.toContain("traceback");
      expect(failedHtml).not.toContain("secret-refresh-detail");
      expect(failedHtml).not.toContain("file:");
      expect(failedHtml).not.toContain("http:");
      expect(failedHtml).not.toContain("https:");
      expect(vi.getTimerCount()).toBe(1);

      const recoveredRefresh = controller.refresh();
      expect(reads).toHaveLength(3);
      reads[2]!.resolve(recoveredFixture);
      await recoveredRefresh;
      await flushAsyncDom();

      expect(mainBody?.querySelector("[role=alert]")).toBeNull();
      expect(mainBody?.querySelector(".phase-list")).not.toBeNull();
      expect(mainBody?.querySelector(".project-name")?.textContent).toBe(
        "Recovered Project",
      );
      expect(
        root.querySelector<HTMLElement>(
          '.refresh-status[role="status"][aria-live="polite"]',
        )?.textContent,
      ).toBe(message("app.updated", "en"));
      expect(vi.getTimerCount()).toBe(1);
      expect(JSON.stringify(successFixture)).toBe(fixtureBefore);
    } finally {
      controller?.destroy();
      vi.useRealTimers();
      root.remove();
    }
  });

  it("seeds the current phase once and preserves a user collapse on refresh", async () => {
    vi.useFakeTimers();
    const root = document.createElement("div");
    const reads: Array<ReturnType<typeof deferred<unknown>>> = [];
    const source: SnapshotSource = {
      read: (): Promise<unknown> => {
        const next = deferred<unknown>();
        reads.push(next);
        return next.promise;
      },
    };
    const pin: PinPort = {
      read: async (): Promise<boolean> => false,
      set: async (enabled: boolean): Promise<boolean> => enabled,
    };
    let controller: ReturnType<typeof mountBi> | undefined;
    document.body.append(root);

    try {
      controller = mountBi(root, { source, pin });
      expect(reads).toHaveLength(1);
      reads[0]!.resolve(successFixture);
      await reads[0]!.promise;
      await flushAsyncDom();

      const currentPhaseSelector =
        '[data-phase-id="PRODUCT_FORMATION"] .phase-summary';
      const initialSummary =
        root.querySelector<HTMLButtonElement>(currentPhaseSelector);
      expect(initialSummary?.getAttribute("aria-expanded")).toBe("true");

      initialSummary?.focus();
      initialSummary?.click();
      const collapsedSummary =
        root.querySelector<HTMLButtonElement>(currentPhaseSelector);
      expect(collapsedSummary?.getAttribute("aria-expanded")).toBe("false");
      expect(document.activeElement).toBe(collapsedSummary);

      const manual = controller.refresh();
      expect(reads).toHaveLength(2);
      reads[1]!.resolve(successFixture);
      await manual;
      await flushAsyncDom();

      expect(
        root.querySelector<HTMLButtonElement>(currentPhaseSelector)?.getAttribute(
          "aria-expanded",
        ),
      ).toBe("false");
    } finally {
      controller?.destroy();
      root.remove();
      vi.useRealTimers();
    }
  });

  it("restores the same main view after a report round trip", () => {
    const shell = document.createElement("div");
    const language = document.createElement("button");
    const pin = document.createElement("button");
    const mainBody = document.createElement("main");
    const reportBody = document.createElement("main");
    const refresh = document.createElement("button");
    language.type = "button";
    pin.type = "button";
    refresh.type = "button";
    reportBody.hidden = true;
    shell.append(language, pin, mainBody, reportBody, refresh);
    document.body.append(shell);
    let reportOrigin: HTMLElement | null = null;

    try {
      const state = createViewState("PRODUCT_FORMATION");
      renderMainView(mainBody, successSnapshot, state.language, state.expanded, {
        togglePhase: () => undefined,
        openReport: (reportId) => {
          reportOrigin = document.activeElement as HTMLElement;
          state.mainScrollTop = mainBody.scrollTop;
          state.report = reportId;
          mainBody.hidden = true;
          reportBody.hidden = false;
          renderReportView(reportBody, successSnapshot.reports[reportId], state.language, () => {
            reportBody.hidden = true;
            mainBody.hidden = false;
            state.report = null;
            mainBody.scrollTop = state.mainScrollTop;
            reportOrigin?.focus();
          });
          reportBody.querySelector<HTMLButtonElement>(".back-button")!.focus();
        },
      });

      const workflowOpen = mainBody.querySelector<HTMLButtonElement>(
        '[data-step-id="WORKFLOW_CAPABILITY_END"] .open-report',
      )!;
      mainBody.scrollTop = 73;
      workflowOpen.focus();
      workflowOpen.click();

      const back = reportBody.querySelector<HTMLButtonElement>(".back-button")!;
      expect(state.report).toBe("workflow");
      expect(document.activeElement).toBe(back);

      back.click();

      expect(shell.contains(mainBody)).toBe(true);
      expect(mainBody.contains(workflowOpen)).toBe(true);
      expect(state.report).toBeNull();
      expect(mainBody.scrollTop).toBe(73);
      expect([...state.expanded]).toEqual(["PRODUCT_FORMATION"]);
      expect(document.activeElement).toBe(workflowOpen);
    } finally {
      shell.remove();
    }
  });

  it("preserves external focus when an open report rerenders", () => {
    const shell = document.createElement("div");
    const language = document.createElement("button");
    const reportBody = document.createElement("main");
    language.type = "button";
    shell.append(language, reportBody);
    document.body.append(shell);

    try {
      renderReportView(reportBody, successSnapshot.reports.workflow, "en", () => {});
      language.focus();

      renderReportView(reportBody, successSnapshot.reports.workflow, "en", () => {});

      expect(document.activeElement).toBe(language);
    } finally {
      shell.remove();
    }
  });

  it("keeps the exact visible main-view button order", () => {
    const shell = document.createElement("div");
    const language = document.createElement("button");
    const pin = document.createElement("button");
    const mainBody = document.createElement("main");
    const reportBody = document.createElement("main");
    const refresh = document.createElement("button");
    language.dataset.control = "language";
    pin.dataset.control = "pin";
    refresh.dataset.control = "refresh";
    language.type = "button";
    pin.type = "button";
    refresh.type = "button";
    reportBody.hidden = true;
    shell.append(language, pin, mainBody, reportBody, refresh);
    document.body.append(shell);

    try {
      const state = createViewState("PRODUCT_FORMATION");
      const controlId = (button: HTMLButtonElement): string => {
        if (button.dataset.control !== undefined) return button.dataset.control;
        if (button.matches(".back-button")) return "back";
        const step = button.closest<HTMLElement>("[data-step-id]");
        if (step !== null) return `open:${step.dataset.stepId}`;
        const phase = button.closest<HTMLElement>("[data-phase-id]");
        return `phase:${phase?.dataset.phaseId}`;
      };
      const mainControls = [
        "language",
        "pin",
        "phase:INITIAL",
        "phase:PRODUCT_FORMATION",
        "open:CALABASH_DRAFT",
        "open:SIMULATION_WORLD_FOUNDATION",
        "open:WORKFLOW_CAPABILITY_END",
        "open:UI_PRODUCT_SURFACE_END",
        "phase:ENGINEERING_RUNS",
        "phase:DELIVERY_PREPARATION",
        "refresh",
      ];
      renderMainView(mainBody, successSnapshot, state.language, state.expanded, {
        togglePhase: () => undefined,
        openReport: (reportId) => {
          state.report = reportId;
          mainBody.hidden = true;
          reportBody.hidden = false;
          renderReportView(reportBody, successSnapshot.reports[reportId], state.language, () => {
            reportBody.hidden = true;
            mainBody.hidden = false;
            state.report = null;
          });
        },
      });

      expect(visibleEnabledButtons(shell).map(controlId)).toEqual(mainControls);

      mainBody
        .querySelector<HTMLButtonElement>(
          '[data-step-id="WORKFLOW_CAPABILITY_END"] .open-report',
        )!
        .click();
      expect(visibleEnabledButtons(shell).map(controlId)).toEqual([
        "language",
        "pin",
        "back",
        "refresh",
      ]);

      reportBody.querySelector<HTMLButtonElement>(".back-button")!.click();
      expect(visibleEnabledButtons(shell).map(controlId)).toEqual(mainControls);
    } finally {
      shell.remove();
    }
  });

  it("localizes fixed Chinese labels without changing sanitized identity values", () => {
    const mainRoot = document.createElement("main");
    const reportRoot = document.createElement("main");
    const expanded = new Set(["PRODUCT_FORMATION"] as const);

    renderMainView(mainRoot, successSnapshot, "zh_CN", expanded, {
      togglePhase: () => undefined,
      openReport: () => undefined,
    });
    expect(
      mainRoot.querySelector('[data-phase-id="PRODUCT_FORMATION"] .phase-label')?.textContent,
    ).toBe(message("phase.PRODUCT_FORMATION", "zh_CN"));
    expect(
      visibleEnabledButtons(mainRoot)
        .filter((button) => button.matches(".open-report"))
        .map((button) => button.textContent),
    ).toEqual(Array.from({ length: 4 }, () => message("app.open", "zh_CN")));
    expect(mainRoot.querySelector(".project-name")?.textContent).toBe("Example Project");

    renderReportView(reportRoot, successSnapshot.reports.candidate, "zh_CN", () => {});
    expect(reportRoot.querySelector(".back-button")?.textContent).toBe(
      message("app.back", "zh_CN"),
    );
    expect(reportRoot.querySelector(".report-heading")?.textContent).toBe(
      message("report.candidate", "zh_CN"),
    );
    expect(
      [...reportRoot.querySelectorAll(".row-label")].map((label) => label.textContent),
    ).toEqual([message("row.identity", "zh_CN"), message("row.integrity", "zh_CN")]);
    expect(reportRoot.querySelector(".protected-notice")?.textContent).toBe(
      message("app.protected", "zh_CN"),
    );
    expect(reportRoot.querySelector(".report-version")?.textContent).toBe("v1.11.6");
  });

  it("preserves the controller journey across report navigation and language changes", async () => {
    vi.useFakeTimers();
    const fixtureBefore = JSON.stringify(successFixture);
    const root = document.createElement("div");
    document.body.append(root);
    const pin: PinPort = {
      read: async (): Promise<boolean> => false,
      set: async (requested): Promise<boolean> => requested,
    };
    let controller: ReturnType<typeof mountBi> | undefined;

    try {
      controller = mountBi(root, { source: safeSource, pin });
      await controller.refresh();
      await flushAsyncDom();

      root
        .querySelector<HTMLButtonElement>('[data-phase-id="INITIAL"] .phase-summary')!
        .click();
      root
        .querySelector<HTMLButtonElement>(
          '[data-phase-id="PRODUCT_FORMATION"] .phase-summary',
        )!
        .click();

      const mainBody = root.querySelector<HTMLElement>(".main-body")!;
      expect(
        mainBody
          .querySelector<HTMLButtonElement>('[data-phase-id="INITIAL"] .phase-summary')
          ?.getAttribute("aria-expanded"),
      ).toBe("true");
      expect(
        mainBody
          .querySelector<HTMLButtonElement>(
            '[data-phase-id="PRODUCT_FORMATION"] .phase-summary',
          )
          ?.getAttribute("aria-expanded"),
      ).toBe("false");
      mainBody.scrollTop = 61;
      const candidateOpen = mainBody.querySelector<HTMLButtonElement>(
        '[data-step-id="PROJECT_INITIALIZATION"] .open-report',
      )!;
      candidateOpen.focus();
      candidateOpen.click();

      const back = root.querySelector<HTMLButtonElement>(".back-button");
      expect(back).not.toBeNull();
      expect(document.activeElement).toBe(back);
      expect(root.querySelectorAll(".main-body")).toHaveLength(1);
      expect(mainBody.querySelector(".report-heading")?.textContent).toBe(
        message("report.candidate", "en"),
      );
      expect(
        [...mainBody.querySelectorAll(".row-label")].map((label) => label.textContent),
      ).toEqual([message("row.identity", "en"), message("row.integrity", "en")]);
      expect(mainBody.querySelector(".back-button")?.textContent).toBe(
        message("app.back", "en"),
      );
      expect(mainBody.querySelector(".protected-notice")?.textContent).toBe(
        message("app.protected", "en"),
      );
      expect(mainBody.querySelector(".report-version")?.textContent).toBe("v1.11.6");

      mainBody.scrollTop = 37;
      const reportLanguageButton = root.querySelector<HTMLButtonElement>(".language-button")!;
      reportLanguageButton.focus();
      reportLanguageButton.click();
      expect(document.activeElement).toBe(reportLanguageButton);

      expect(mainBody.querySelector(".report-heading")?.textContent).toBe(
        message("report.candidate", "zh_CN"),
      );
      expect(
        [...mainBody.querySelectorAll(".row-label")].map((label) => label.textContent),
      ).toEqual([
        message("row.identity", "zh_CN"),
        message("row.integrity", "zh_CN"),
      ]);
      expect(mainBody.querySelector(".back-button")?.textContent).toBe(
        message("app.back", "zh_CN"),
      );
      expect(mainBody.querySelector(".protected-notice")?.textContent).toBe(
        message("app.protected", "zh_CN"),
      );
      expect(mainBody.querySelector(".report-version")?.textContent).toBe("v1.11.6");
      expect(mainBody.scrollTop).toBe(37);

      const localizedBack = mainBody.querySelector<HTMLButtonElement>(".back-button")!;
      expect(localizedBack).not.toBe(back);
      localizedBack.click();

      expect(mainBody.querySelector(".report-heading")).toBeNull();
      expect(mainBody.querySelector(".project-name")?.textContent).toBe("Example Project");
      expect(mainBody.scrollTop).toBe(61);
      expect(
        mainBody
          .querySelector<HTMLButtonElement>('[data-phase-id="INITIAL"] .phase-summary')
          ?.getAttribute("aria-expanded"),
      ).toBe("true");
      expect(
        mainBody
          .querySelector<HTMLButtonElement>(
            '[data-phase-id="PRODUCT_FORMATION"] .phase-summary',
          )
          ?.getAttribute("aria-expanded"),
      ).toBe("false");
      expect(
        mainBody.querySelector('[data-phase-id="INITIAL"] .phase-label')?.textContent,
      ).toBe(message("phase.INITIAL", "zh_CN"));
      expect(
        mainBody.querySelector(
          '[data-phase-id="PRODUCT_FORMATION"] .phase-label',
        )?.textContent,
      ).toBe(message("phase.PRODUCT_FORMATION", "zh_CN"));
      const returnedCandidateOpen = mainBody.querySelector<HTMLButtonElement>(
        '[data-step-id="PROJECT_INITIALIZATION"] .open-report',
      )!;
      expect(returnedCandidateOpen.textContent).toBe(message("app.open", "zh_CN"));
      expect(returnedCandidateOpen).not.toBe(candidateOpen);
      expect(candidateOpen.isConnected).toBe(false);
      expect(document.activeElement).toBe(returnedCandidateOpen);

      const languageButton = root.querySelector<HTMLButtonElement>(".language-button")!;
      languageButton.focus();
      languageButton.click();

      expect(mainBody.querySelector(".report-heading")).toBeNull();
      expect(mainBody.querySelector(".project-name")?.textContent).toBe("Example Project");
      expect(mainBody.scrollTop).toBe(61);
      expect(
        mainBody
          .querySelector<HTMLButtonElement>('[data-phase-id="INITIAL"] .phase-summary')
          ?.getAttribute("aria-expanded"),
      ).toBe("true");
      expect(
        mainBody
          .querySelector<HTMLButtonElement>(
            '[data-phase-id="PRODUCT_FORMATION"] .phase-summary',
          )
          ?.getAttribute("aria-expanded"),
      ).toBe("false");
      expect(
        mainBody.querySelector('[data-phase-id="INITIAL"] .phase-label')?.textContent,
      ).toBe(message("phase.INITIAL", "en"));
      expect(
        mainBody.querySelector(
          '[data-phase-id="PRODUCT_FORMATION"] .phase-label',
        )?.textContent,
      ).toBe(message("phase.PRODUCT_FORMATION", "en"));
      expect(
        mainBody.querySelector<HTMLButtonElement>(
          '[data-step-id="PROJECT_INITIALIZATION"] .open-report',
        )?.textContent,
      ).toBe(message("app.open", "en"));
      expect(document.activeElement).toBe(languageButton);
      expect(JSON.stringify(successFixture)).toBe(fixtureBefore);
    } finally {
      controller?.destroy();
      root.remove();
      vi.useRealTimers();
    }
  });

  it("keeps an open candidate report visible when refresh returns an error snapshot", async () => {
    vi.useFakeTimers();
    const successFixtureBefore = JSON.stringify(successFixture);
    const errorFixtureBefore = JSON.stringify(errorFixture);
    const recoveredFixture = JSON.parse(successFixtureBefore) as typeof successFixture;
    recoveredFixture.project = "Recovered Project";
    recoveredFixture.reports.candidate.version = "v1.11.7";
    parseSnapshot(recoveredFixture);
    const recoveredFixtureBefore = JSON.stringify(recoveredFixture);
    const root = document.createElement("div");
    const reads: Array<ReturnType<typeof deferred<unknown>>> = [];
    const source: SnapshotSource = {
      read: (): Promise<unknown> => {
        const next = deferred<unknown>();
        reads.push(next);
        return next.promise;
      },
    };
    const pin: PinPort = {
      read: async (): Promise<boolean> => false,
      set: async (enabled: boolean): Promise<boolean> => enabled,
    };
    let controller: ReturnType<typeof mountBi> | undefined;
    document.body.append(root);

    try {
      controller = mountBi(root, { source, pin });
      const joined = controller.refresh();
      reads[0]!.resolve(successFixture);
      await joined;

      const mainBody = root.querySelector<HTMLElement>(".main-body")!;
      const initialSummary = mainBody.querySelector<HTMLButtonElement>(
        '[data-phase-id="INITIAL"] .phase-summary',
      )!;
      initialSummary.click();
      expect(initialSummary.isConnected).toBe(false);
      const initialExpandedBeforeReport = mainBody
        .querySelector<HTMLButtonElement>('[data-phase-id="INITIAL"] .phase-summary')!
        .getAttribute("aria-expanded");
      const productExpandedBeforeReport = mainBody
        .querySelector<HTMLButtonElement>(
          '[data-phase-id="PRODUCT_FORMATION"] .phase-summary',
        )!
        .getAttribute("aria-expanded");
      mainBody.scrollTop = 61;
      const mainScrollTopBeforeReport = mainBody.scrollTop;
      const candidateOpen = mainBody.querySelector<HTMLButtonElement>(
        '[data-step-id="PROJECT_INITIALIZATION"] .open-report',
      )!;
      candidateOpen.focus();
      candidateOpen.click();
      expect(mainBody.querySelector(".report-heading")).not.toBeNull();

      const failedRefresh = controller.refresh();
      reads[1]!.resolve(errorFixture);
      await failedRefresh;

      expect(root.querySelector(".main-body")).toBe(mainBody);
      const back = mainBody.querySelector<HTMLButtonElement>(".back-button");
      expect(back).not.toBeNull();
      expect(back?.disabled).toBe(false);
      expect(back?.type).toBe("button");
      expect(mainBody.querySelector(".protected-notice")?.textContent).toBe(
        message("app.protected", "en"),
      );
      const alerts = mainBody.querySelectorAll<HTMLElement>('[role="alert"]');
      expect(alerts).toHaveLength(1);
      const errorStates = alerts[0]?.querySelectorAll<HTMLElement>(
        ".state.state--error",
      );
      expect(errorStates).toHaveLength(1);
      expect(
        errorStates?.[0]?.querySelector('.state-glyph[aria-hidden="true"]'),
      ).not.toBeNull();
      expect(
        errorStates?.[0]?.querySelector(".state-text")?.textContent,
      ).toBe(message("state.error", "en"));
      expect(alerts[0]?.textContent).toContain(message("app.unnamed_project", "en"));
      expect(alerts[0]?.textContent).toContain(message("app.error", "en"));
      expect(mainBody.querySelector(".phase-list")).toBeNull();
      expect(mainBody.querySelector(".report-heading")).toBeNull();
      expect(mainBody.querySelector(".report-row")).toBeNull();
      expect(mainBody.querySelector(".report-version")).toBeNull();
      expect(mainBody.textContent).not.toContain("v1.11.6");
      expect(mainBody.textContent).not.toContain(message("value.locked", "en"));
      expect(mainBody.textContent).not.toContain(message("value.recorded", "en"));
      expect(mainBody.textContent).not.toContain(message("state.done", "en"));
      expect(
        root.querySelector<HTMLElement>(
          '.refresh-status[role="status"][aria-live="polite"]',
        )?.textContent,
      ).not.toBe(message("app.updated", "en"));
      const failedHtml = root.outerHTML.toLowerCase();
      expect(failedHtml).not.toContain("file:");
      expect(failedHtml).not.toContain("http:");
      expect(failedHtml).not.toContain("https:");
      expect(failedHtml).not.toMatch(/[a-z]:[\\/]/);
      expect(failedHtml).not.toContain("://");
      await vi.advanceTimersByTimeAsync(0);
      expect(vi.getTimerCount()).toBe(1);

      const recoveredRefresh = controller.refresh();
      reads[2]!.resolve(recoveredFixture);
      await recoveredRefresh;
      await flushAsyncDom();

      expect(root.querySelector(".main-body")).toBe(mainBody);
      expect(mainBody.querySelector('[role="alert"]')).toBeNull();
      expect(mainBody.querySelector(".phase-list")).toBeNull();
      expect(mainBody.querySelector(".report-heading")?.textContent).toBe(
        message("report.candidate", "en"),
      );
      expect(mainBody.querySelector(".report-version")?.textContent).toBe("v1.11.7");
      expect(mainBody.querySelector(".protected-notice")?.textContent).toBe(
        message("app.protected", "en"),
      );
      const recoveredBack = mainBody.querySelector<HTMLButtonElement>(".back-button");
      expect(recoveredBack).not.toBeNull();
      expect(
        root.querySelector<HTMLElement>(
          '.refresh-status[role="status"][aria-live="polite"]',
        )?.textContent,
      ).toBe(message("app.updated", "en"));
      await vi.advanceTimersByTimeAsync(0);
      expect(vi.getTimerCount()).toBe(1);

      recoveredBack!.click();
      await flushAsyncDom();
      expect(mainBody.querySelector(".project-name")?.textContent).toBe(
        "Recovered Project",
      );
      expect(
        mainBody
          .querySelector<HTMLButtonElement>('[data-phase-id="INITIAL"] .phase-summary')
          ?.getAttribute("aria-expanded"),
      ).toBe(initialExpandedBeforeReport);
      expect(
        mainBody
          .querySelector<HTMLButtonElement>(
            '[data-phase-id="PRODUCT_FORMATION"] .phase-summary',
          )
          ?.getAttribute("aria-expanded"),
      ).toBe(productExpandedBeforeReport);
      expect(mainBody.scrollTop).toBe(mainScrollTopBeforeReport);
      expect(candidateOpen.isConnected).toBe(false);
      const recoveredCandidateOpen = mainBody.querySelector<HTMLButtonElement>(
        '[data-step-id="PROJECT_INITIALIZATION"] .open-report',
      )!;
      expect(recoveredCandidateOpen).not.toBe(candidateOpen);
      expect(document.activeElement).toBe(recoveredCandidateOpen);
      expect(JSON.stringify(successFixture)).toBe(successFixtureBefore);
      expect(JSON.stringify(errorFixture)).toBe(errorFixtureBefore);
      expect(JSON.stringify(recoveredFixture)).toBe(recoveredFixtureBefore);
    } finally {
      controller?.destroy();
      root.remove();
      vi.useRealTimers();
    }
  });

  it("preserves logical main focus across success, error, and recovery refreshes", async () => {
    vi.useFakeTimers();
    const timerBaseline = vi.getTimerCount();
    const root = document.createElement("div");
    const reads: Array<ReturnType<typeof deferred<unknown>>> = [];
    const source: SnapshotSource = {
      read: (): Promise<unknown> => {
        const next = deferred<unknown>();
        reads.push(next);
        return next.promise;
      },
    };
    const pin: PinPort = {
      read: async (): Promise<boolean> => false,
      set: async (enabled: boolean): Promise<boolean> => enabled,
    };
    let controller: ReturnType<typeof mountBi> | undefined;
    document.body.append(root);

    const resolveRefresh = async (fixture: unknown): Promise<void> => {
      const refresh = controller!.refresh();
      reads.at(-1)!.resolve(fixture);
      await refresh;
      await flushAsyncDom();
    };

    try {
      controller = mountBi(root, { source, pin });
      await resolveRefresh(successFixture);

      const mainBody = root.querySelector<HTMLElement>(".main-body")!;
      const productSelector =
        '[data-phase-id="PRODUCT_FORMATION"] .phase-summary';
      const candidateSelector =
        '[data-step-id="PROJECT_INITIALIZATION"] .open-report';
      const productSummary =
        mainBody.querySelector<HTMLButtonElement>(productSelector)!;
      productSummary.focus();
      expect(document.activeElement).toBe(productSummary);

      await resolveRefresh(successFixture);

      expect(productSummary.isConnected).toBe(false);
      const refreshedProductSummary =
        mainBody.querySelector<HTMLButtonElement>(productSelector)!;
      expect(refreshedProductSummary).not.toBe(productSummary);
      expect(document.activeElement).toBe(refreshedProductSummary);

      mainBody
        .querySelector<HTMLButtonElement>(
          '[data-phase-id="INITIAL"] .phase-summary',
        )!
        .click();
      const candidateOpen =
        mainBody.querySelector<HTMLButtonElement>(candidateSelector)!;
      candidateOpen.focus();
      expect(document.activeElement).toBe(candidateOpen);

      await resolveRefresh(successFixture);

      expect(candidateOpen.isConnected).toBe(false);
      const refreshedCandidateOpen =
        mainBody.querySelector<HTMLButtonElement>(candidateSelector)!;
      expect(refreshedCandidateOpen).not.toBe(candidateOpen);
      expect(document.activeElement).toBe(refreshedCandidateOpen);

      refreshedCandidateOpen.focus();
      await resolveRefresh(errorFixture);

      expect(refreshedCandidateOpen.isConnected).toBe(false);
      const alerts = mainBody.querySelectorAll<HTMLElement>('[role="alert"]');
      expect(alerts).toHaveLength(1);
      const mainAlert = alerts[0]!;
      expect(mainAlert.getAttribute("role")).toBe("alert");
      expect(mainAlert.getAttribute("tabindex")).toBe("-1");
      expect(document.activeElement).toBe(mainAlert);

      await resolveRefresh(successFixture);

      expect(mainAlert.isConnected).toBe(false);
      const recoveredCandidateOpen =
        mainBody.querySelector<HTMLButtonElement>(candidateSelector)!;
      expect(recoveredCandidateOpen).not.toBe(refreshedCandidateOpen);
      expect(document.activeElement).toBe(recoveredCandidateOpen);
    } finally {
      controller?.destroy();
      root.remove();
      if (vi.getTimerCount() > timerBaseline) vi.clearAllTimers();
      vi.useRealTimers();
    }
  });

  it("preserves logical Report Back focus across success, error, and recovery refreshes", async () => {
    vi.useFakeTimers();
    const timerBaseline = vi.getTimerCount();
    const refreshedFixture = JSON.parse(
      JSON.stringify(successFixture),
    ) as typeof successFixture;
    refreshedFixture.reports.candidate.version = "v1.11.7";
    parseSnapshot(refreshedFixture);
    const root = document.createElement("div");
    const reads: Array<ReturnType<typeof deferred<unknown>>> = [];
    const source: SnapshotSource = {
      read: (): Promise<unknown> => {
        const next = deferred<unknown>();
        reads.push(next);
        return next.promise;
      },
    };
    const pin: PinPort = {
      read: async (): Promise<boolean> => false,
      set: async (enabled: boolean): Promise<boolean> => enabled,
    };
    let controller: ReturnType<typeof mountBi> | undefined;
    document.body.append(root);

    const resolveRefresh = async (fixture: unknown): Promise<void> => {
      const refresh = controller!.refresh();
      reads.at(-1)!.resolve(fixture);
      await refresh;
      await flushAsyncDom();
    };

    try {
      controller = mountBi(root, { source, pin });
      const languageButton =
        root.querySelector<HTMLButtonElement>(".language-button")!;
      const pinButton = root.querySelector<HTMLButtonElement>(".pin-button")!;
      const refreshButton =
        root.querySelector<HTMLButtonElement>(".refresh-button")!;
      const expectExternalControlsStable = (): void => {
        expect(root.querySelector(".language-button")).toBe(languageButton);
        expect(root.querySelector(".pin-button")).toBe(pinButton);
        expect(root.querySelector(".refresh-button")).toBe(refreshButton);
      };

      await resolveRefresh(successFixture);
      const mainBody = root.querySelector<HTMLElement>(".main-body")!;
      mainBody
        .querySelector<HTMLButtonElement>(
          '[data-phase-id="INITIAL"] .phase-summary',
        )!
        .click();
      mainBody
        .querySelector<HTMLButtonElement>(
          '[data-step-id="PROJECT_INITIALIZATION"] .open-report',
        )!
        .click();
      const initialBack =
        mainBody.querySelector<HTMLButtonElement>(".back-button")!;
      expect(document.activeElement).toBe(initialBack);
      expectExternalControlsStable();

      await resolveRefresh(refreshedFixture);

      expect(initialBack.isConnected).toBe(false);
      const refreshedBack =
        mainBody.querySelector<HTMLButtonElement>(".back-button")!;
      expect(refreshedBack).not.toBe(initialBack);
      expect(mainBody.querySelector(".report-version")?.textContent).toBe("v1.11.7");
      expect(document.activeElement).toBe(refreshedBack);
      expectExternalControlsStable();

      await resolveRefresh(errorFixture);

      expect(refreshedBack.isConnected).toBe(false);
      expect(mainBody.querySelectorAll('[role="alert"]')).toHaveLength(1);
      const errorBack =
        mainBody.querySelector<HTMLButtonElement>(".back-button")!;
      expect(errorBack).not.toBe(refreshedBack);
      expect(document.activeElement).toBe(errorBack);
      expectExternalControlsStable();

      await resolveRefresh(successFixture);

      expect(errorBack.isConnected).toBe(false);
      const recoveredBack =
        mainBody.querySelector<HTMLButtonElement>(".back-button")!;
      expect(recoveredBack).not.toBe(errorBack);
      expect(mainBody.querySelector(".report-heading")?.textContent).toBe(
        message("report.candidate", "en"),
      );
      expect(document.activeElement).toBe(recoveredBack);
      expectExternalControlsStable();
    } finally {
      controller?.destroy();
      root.remove();
      if (vi.getTimerCount() > timerBaseline) vi.clearAllTimers();
      vi.useRealTimers();
    }
  });

  it("mounts a stable three-row shell with live language and refresh controls", async () => {
    vi.useFakeTimers();
    const fixtureBefore = JSON.stringify(successFixture);
    const root = document.createElement("div");
    const reads: Array<ReturnType<typeof deferred<unknown>>> = [];
    const source: SnapshotSource = {
      read: (): Promise<unknown> => {
        const next = deferred<unknown>();
        reads.push(next);
        return next.promise;
      },
    };
    const pin: PinPort = {
      read: async (): Promise<boolean> => false,
      set: async (enabled: boolean): Promise<boolean> => enabled,
    };
    let controller: ReturnType<typeof mountBi> | undefined;
    document.body.append(root);

    try {
      controller = mountBi(root, { source, pin });
      expect(reads).toHaveLength(1);

      const joinedInitialRefresh = controller.refresh();
      expect(reads).toHaveLength(1);
      reads[0]!.resolve(successFixture);
      await reads[0]!.promise;
      await joinedInitialRefresh;
      await flushAsyncDom();

      const shells = root.querySelectorAll<HTMLElement>(".app-shell");
      expect(shells).toHaveLength(1);
      const shell = shells[0]!;
      const mainBody = root.querySelector<HTMLElement>(".main-body");
      const rows = Array.from(shell.children);
      expect(rows).toHaveLength(3);
      expect(rows[0]?.matches(".control-strip")).toBe(true);
      expect(rows[1]).toBe(mainBody);
      expect(rows[1]?.matches(".main-body.app-body")).toBe(true);
      expect(rows[2]?.matches(".refresh-strip")).toBe(true);

      const controlStrip = rows[0] as HTMLElement;
      const refreshStrip = rows[2] as HTMLElement;
      expect(controlStrip.querySelector(".app-title")).not.toBeNull();
      expect(controlStrip.querySelector(".language-button")).not.toBeNull();
      expect(controlStrip.querySelector(".pin-button")).not.toBeNull();
      const refreshButton = refreshStrip.querySelector<HTMLButtonElement>(
        ".refresh-button",
      );
      expect(refreshButton).not.toBeNull();
      expect(
        refreshStrip.querySelector(
          '.refresh-status[role="status"][aria-live="polite"]',
        ),
      ).not.toBeNull();

      const languageButton = controlStrip.querySelector<HTMLButtonElement>(
        ".language-button",
      )!;
      const languageOptions = Array.from(
        languageButton.querySelectorAll<HTMLElement>(".language-option"),
      );
      expect(languageOptions).toHaveLength(2);
      expect(languageOptions.map((option) => option.textContent?.trim())).toEqual([
        "EN",
        "中",
      ]);
      expect(
        languageOptions.filter((option) => option.getAttribute("aria-current") === "true"),
      ).toEqual([languageOptions[0]]);

      languageButton.focus();
      languageButton.click();
      await flushAsyncDom();

      expect(root.querySelector(".language-button")).toBe(languageButton);
      expect(document.activeElement).toBe(languageButton);
      const toggledOptions = Array.from(
        languageButton.querySelectorAll<HTMLElement>(".language-option"),
      );
      expect(toggledOptions).toHaveLength(2);
      expect(toggledOptions.map((option) => option.textContent?.trim())).toEqual([
        "EN",
        "中",
      ]);
      expect(
        toggledOptions.filter((option) => option.getAttribute("aria-current") === "true"),
      ).toEqual([toggledOptions[1]]);

      refreshButton!.click();
      expect(reads).toHaveLength(2);
      const timerBaseline = vi.getTimerCount();
      refreshButton!.click();
      expect(reads).toHaveLength(2);

      reads[1]!.resolve(successFixture);
      await reads[1]!.promise;
      await flushAsyncDom();
      expect(vi.getTimerCount()).toBe(timerBaseline + 1);
      expect(JSON.stringify(successFixture)).toBe(fixtureBefore);

      controller.destroy();
      controller = undefined;
      refreshButton!.click();
      expect(reads).toHaveLength(2);
    } finally {
      controller?.destroy();
      root.remove();
      vi.useRealTimers();
    }
  });
});

describe("controller destroy lifecycle", () => {
  const displayedState = (root: HTMLElement): string[] =>
    [...root.querySelectorAll<HTMLElement>("*")].map((element) =>
      [
        element.tagName,
        element.className,
        String(element.hidden),
        element.getAttribute("aria-expanded") ?? "",
        element.getAttribute("aria-pressed") ?? "",
        element.getAttribute("aria-busy") ?? "",
        element.getAttribute("aria-disabled") ?? "",
        element.hasAttribute("disabled") ? "disabled" : "",
      ].join("|"),
    );

  it("is idempotent while initial source and Pin reads settle after destroy", async () => {
    vi.useFakeTimers();
    const timerBaseline = vi.getTimerCount();
    const root = document.createElement("div");
    const sourceRead = deferred<unknown>();
    const pinRead = deferred<boolean>();
    const calls = { sourceRead: 0, pinRead: 0, pinSet: 0 };
    const source: SnapshotSource = {
      read: (): Promise<unknown> => {
        calls.sourceRead += 1;
        return sourceRead.promise;
      },
    };
    const pin: PinPort = {
      read: (): Promise<boolean> => {
        calls.pinRead += 1;
        return pinRead.promise;
      },
      set: async (enabled: boolean): Promise<boolean> => {
        calls.pinSet += 1;
        return enabled;
      },
    };
    const unhandled: unknown[] = [];
    const onUnhandled = (event: PromiseRejectionEvent) => unhandled.push(event.reason);
    window.addEventListener("unhandledrejection", onUnhandled);
    let controller: ReturnType<typeof mountBi> | undefined;
    document.body.append(root);

    try {
      const mounted = mountBi(root, { source, pin });
      controller = mounted;
      expect(calls).toEqual({ sourceRead: 1, pinRead: 1, pinSet: 0 });

      const languageButton = root.querySelector<HTMLButtonElement>(".language-button")!;
      const pinButton = root.querySelector<HTMLButtonElement>(".pin-button")!;
      const refreshButton = root.querySelector<HTMLButtonElement>(".refresh-button")!;
      languageButton.focus();
      const before = {
        html: root.innerHTML,
        text: root.textContent,
        active: document.activeElement,
        displayed: displayedState(root),
        calls: { ...calls },
        timers: vi.getTimerCount(),
      };

      expect(() => mounted.destroy()).not.toThrow();
      expect(() => mounted.destroy()).not.toThrow();
      sourceRead.resolve(successFixture);
      pinRead.reject(new Error("late pin read failure"));
      await flushAsyncDom();

      await mounted.refresh();
      languageButton.click();
      pinButton.click();
      refreshButton.click();
      await flushAsyncDom();

      expect(calls).toEqual(before.calls);
      expect(root.innerHTML).toBe(before.html);
      expect(root.textContent).toBe(before.text);
      expect(document.activeElement).toBe(before.active);
      expect(displayedState(root)).toEqual(before.displayed);
      expect(root.textContent).not.toContain("late pin read failure");
      expect(vi.getTimerCount()).toBeLessThanOrEqual(before.timers);
      expect(unhandled).toEqual([]);
    } finally {
      controller?.destroy();
      window.removeEventListener("unhandledrejection", onUnhandled);
      root.remove();
      vi.clearAllTimers();
      expect(vi.getTimerCount()).toBe(0);
      expect(timerBaseline).toBe(0);
      vi.useRealTimers();
    }
  });

  it("isolates a pending confirmed Pin write and all captured controls after destroy", async () => {
    vi.useFakeTimers();
    const timerBaseline = vi.getTimerCount();
    const root = document.createElement("div");
    const pinSet = deferred<boolean>();
    const calls = { sourceRead: 0, pinRead: 0, pinSet: 0 };
    const source: SnapshotSource = {
      read: async (): Promise<unknown> => {
        calls.sourceRead += 1;
        return successFixture;
      },
    };
    const pin: PinPort = {
      read: async (): Promise<boolean> => {
        calls.pinRead += 1;
        return false;
      },
      set: (_enabled: boolean): Promise<boolean> => {
        calls.pinSet += 1;
        return pinSet.promise;
      },
    };
    const unhandled: unknown[] = [];
    const onUnhandled = (event: PromiseRejectionEvent) => unhandled.push(event.reason);
    window.addEventListener("unhandledrejection", onUnhandled);
    let controller: ReturnType<typeof mountBi> | undefined;
    document.body.append(root);

    try {
      const mounted = mountBi(root, { source, pin });
      controller = mounted;
      await mounted.refresh();
      await flushAsyncDom();
      expect(calls).toEqual({ sourceRead: 1, pinRead: 1, pinSet: 0 });

      const languageButton = root.querySelector<HTMLButtonElement>(".language-button")!;
      const pinButton = root.querySelector<HTMLButtonElement>(".pin-button")!;
      const refreshButton = root.querySelector<HTMLButtonElement>(".refresh-button")!;
      expect(pinButton.disabled).toBe(false);
      pinButton.focus();
      pinButton.click();
      expect(calls.pinSet).toBe(1);

      const before = {
        html: root.innerHTML,
        text: root.textContent,
        active: document.activeElement,
        displayed: displayedState(root),
        calls: { ...calls },
        timers: vi.getTimerCount(),
      };

      expect(() => mounted.destroy()).not.toThrow();
      expect(() => mounted.destroy()).not.toThrow();
      pinSet.reject(new Error("late pin set failure"));
      await flushAsyncDom();

      await mounted.refresh();
      languageButton.click();
      pinButton.click();
      refreshButton.click();
      await flushAsyncDom();

      expect(calls).toEqual(before.calls);
      expect(root.innerHTML).toBe(before.html);
      expect(root.textContent).toBe(before.text);
      expect(document.activeElement).toBe(before.active);
      expect(displayedState(root)).toEqual(before.displayed);
      expect(root.textContent).not.toContain("late pin set failure");
      expect(vi.getTimerCount()).toBeLessThanOrEqual(before.timers);
      expect(unhandled).toEqual([]);
    } finally {
      controller?.destroy();
      window.removeEventListener("unhandledrejection", onUnhandled);
      root.remove();
      vi.clearAllTimers();
      expect(vi.getTimerCount()).toBe(0);
      expect(timerBaseline).toBe(0);
      vi.useRealTimers();
    }
  });
});

describe("closed preview adapters", () => {
  it("fixes the packaged desktop to the sanitized success Snapshot", () => {
    expect(resolveRuntimePreviewCase(true, null)).toBe("ok");
    expect(resolveRuntimePreviewCase(true, "error")).toBe("ok");
    expect(resolveRuntimePreviewCase(false, null)).toBe("error");
    expect(resolveRuntimePreviewCase(false, "ok")).toBe("ok");
  });

  it("accepts only the four exact preview case names", () => {
    expect(resolvePreviewCase("ok")).toBe("ok");
    expect(resolvePreviewCase("error")).toBe("error");
    expect(resolvePreviewCase("max-en")).toBe("max-en");
    expect(resolvePreviewCase("max-zh")).toBe("max-zh");

    for (const rejected of [
      null,
      "",
      "OK",
      " ok",
      "ok ",
      "ok&path=C:/private",
      "https://example.invalid",
      "../../snapshot-ok.json",
      "unknown",
    ]) {
      expect(resolvePreviewCase(rejected)).toBe("error");
    }
  });

  it("serves immutable allowlisted snapshots without mutating fixture imports", async () => {
    const okBefore = JSON.stringify(successFixture);
    const errorBefore = JSON.stringify(errorFixture);
    const expectedProjects = new Map([
      ["ok", "Example Project"],
      ["error", "Unnamed project"],
      ["max-en", "A".repeat(80)],
      ["max-zh", "工程".repeat(40)],
    ] as const);

    for (const [previewCase, expectedProject] of expectedProjects) {
      const { source } = createPreviewDependencies(previewCase);
      const first = await source.read();
      const second = await source.read();
      const parsed = parseSnapshot(first);

      expect(first).toBe(second);
      expect(Object.isFrozen(first)).toBe(true);
      expect(parsed.project).toBe(expectedProject);
      expect(parsed.health).toBe(previewCase === "error" ? "error" : "ok");
    }

    expect(JSON.stringify(successFixture)).toBe(okBefore);
    expect(JSON.stringify(errorFixture)).toBe(errorBefore);
  });

  it("keeps preview Pin deterministic and in memory", async () => {
    const first = createPreviewDependencies("ok").pin;
    const second = createPreviewDependencies("ok").pin;

    expect(await first.read()).toBe(false);
    expect(await first.set(true)).toBe(true);
    expect(await first.read()).toBe(true);
    expect(await first.set(false)).toBe(false);
    expect(await first.read()).toBe(false);
    expect(await second.read()).toBe(false);
  });
});
