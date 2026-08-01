import "./setup";

import { describe, expect, it } from "vitest";

import { message, type Language } from "../../src/i18n/catalog";
import { parseSnapshot, type ReportId, type RowKey } from "../../src/model/snapshot";
import { renderMainView } from "../../src/render/main-view";
import { renderReportView } from "../../src/render/report-view";
import {
  createViewState,
  type PinPort,
  type SnapshotSource,
  type ViewState,
} from "../../src/state/view-state";
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

function visibleEnabledButtons(root: ParentNode): HTMLButtonElement[] {
  return [...root.querySelectorAll<HTMLButtonElement>("button")].filter(
    (button) => !button.disabled && button.closest("[hidden]") === null,
  );
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
    expect(state.reportOrigin).toBeNull();
    expect(state.mainScrollTop).toBe(0);
    expect(state.requestInFlight).toBe(false);
    expect([...createViewState().expanded]).toEqual([]);
    expect(source && pin).toBeTruthy();
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

    try {
      const state = createViewState("PRODUCT_FORMATION");
      renderMainView(mainBody, successSnapshot, state.language, state.expanded, {
        togglePhase: () => undefined,
        openReport: (reportId) => {
          state.reportOrigin = document.activeElement as HTMLElement;
          state.mainScrollTop = mainBody.scrollTop;
          state.report = reportId;
          mainBody.hidden = true;
          reportBody.hidden = false;
          renderReportView(reportBody, successSnapshot.reports[reportId], state.language, () => {
            reportBody.hidden = true;
            mainBody.hidden = false;
            state.report = null;
            mainBody.scrollTop = state.mainScrollTop;
            state.reportOrigin?.focus();
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
});
