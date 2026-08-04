import "./setup";

import { describe, expect, it } from "vitest";

import { message, type Language } from "../../src/i18n/catalog";
import {
  parseSnapshot,
  type PhaseId,
  type ReportId,
  type Snapshot,
} from "../../src/model/snapshot";
import { renderMainView, type MainViewCallbacks } from "../../src/render/main-view";
import errorFixture from "../fixtures/snapshot-error.json";
import successFixture from "../fixtures/snapshot-ok.json";

const PHASE_IDS = [
  "INITIAL",
  "PRODUCT_FORMATION",
  "ENGINEERING_RUNS",
  "DELIVERY_PREPARATION",
] as const satisfies readonly PhaseId[];

const STEP_IDS_BY_PHASE = [
  ["PROPOSAL_READINESS", "PROJECT_INITIALIZATION", "INITIAL_READY"],
  [
    "CALABASH_DRAFT",
    "SIMULATION_WORLD_FOUNDATION",
    "WORKFLOW_CAPABILITY_END",
    "UI_PRODUCT_SURFACE_END",
    "CALABASH_UPGRADE_READY",
  ],
  [
    "MANDATORY_CALABASH_UPGRADE",
    "PRODUCT_BASELINE",
    "FEATURE_SLICE_EXECUTION_COVERAGE",
    "UI_LOCKED_INTEGRATION_BASELINE",
    "LOOP_RUN_D0_D3",
    "LOOP_OWNER_ACCEPTANCE",
    "ALL_REQUIRED_RUNS_ACCEPTED",
  ],
  [
    "CENTRALIZED_VULNERABILITY_AUDIT",
    "SECURITY_REMEDIATION",
    "SECURITY_REAUDIT_VULNERABILITY_CLOSURE",
    "POST_SECURITY_OWNER_ACCEPTANCE",
    "DELIVERY_METHOD_QA",
    "DELIVERY_PACKAGE_GUARD_READY",
  ],
] as const;

const OPEN_MAPPINGS = [
  ["PROPOSAL_READINESS", "proposal"],
  ["PROJECT_INITIALIZATION", "candidate"],
  ["CALABASH_DRAFT", "calabash"],
  ["SIMULATION_WORLD_FOUNDATION", "simulation"],
  ["WORKFLOW_CAPABILITY_END", "workflow"],
  ["UI_PRODUCT_SURFACE_END", "ui"],
  ["PRODUCT_BASELINE", "baseline"],
  ["LOOP_RUN_D0_D3", "loop_governance"],
] as const satisfies readonly (readonly [string, ReportId])[];

const successSnapshot = parseSnapshot(successFixture);
const errorSnapshot = parseSnapshot(errorFixture);

type RenderedView = Readonly<{
  root: HTMLElement;
  toggled: PhaseId[];
  opened: ReportId[];
}>;

function renderFixture(
  snapshot: Readonly<Snapshot> = successSnapshot,
  language: Language = "en",
  expanded: ReadonlySet<PhaseId> = new Set<PhaseId>(["PRODUCT_FORMATION"]),
): RenderedView {
  const root = document.createElement("main");
  const toggled: PhaseId[] = [];
  const opened: ReportId[] = [];
  const callbacks: MainViewCallbacks = {
    togglePhase: (phase) => toggled.push(phase),
    openReport: (report) => opened.push(report),
  };
  document.body.append(root);
  renderMainView(root, snapshot, language, expanded, callbacks);
  return { root, toggled, opened };
}

function phaseViews(root: HTMLElement): HTMLElement[] {
  return Array.from(root.querySelectorAll<HTMLElement>(".phase-list > .phase-view"));
}

describe("truthful four-phase main view", () => {
  it("renders the exact phase order with only the current phase expanded and marked current", () => {
    const { root, toggled } = renderFixture();
    const phases = phaseViews(root);

    expect(root.querySelector("ol.phase-list")).not.toBeNull();
    expect(phases.map((phase) => phase.dataset.phaseId)).toEqual(PHASE_IDS);

    const summaries = phases.map((phase) => phase.querySelector<HTMLButtonElement>(".phase-summary")!);
    expect(summaries.map((summary) => summary.getAttribute("aria-expanded"))).toEqual([
      "false",
      "true",
      "false",
      "false",
    ]);
    expect(summaries.map((summary) => summary.getAttribute("aria-current"))).toEqual([
      null,
      "step",
      null,
      null,
    ]);

    for (const [index, phaseId] of PHASE_IDS.entries()) {
      const summary = summaries[index]!;
      const panel = phases[index]!.querySelector<HTMLElement>(".phase-panel")!;
      expect(summary.type).toBe("button");
      expect(summary.getAttribute("aria-controls")).toBe(`phase-panel-${phaseId}`);
      expect(panel.id).toBe(`phase-panel-${phaseId}`);
      expect(panel.hidden).toBe(phaseId !== "PRODUCT_FORMATION");
    }

    summaries[1]!.click();
    expect(toggled).toEqual(["PRODUCT_FORMATION"]);
  });

  it("projects representative success states without flattening active or blocked work", () => {
    const { root } = renderFixture();
    const workflow = root.querySelector<HTMLElement>(
      '[data-step-id="WORKFLOW_CAPABILITY_END"]',
    )!;
    const ui = root.querySelector<HTMLElement>('[data-step-id="UI_PRODUCT_SURFACE_END"]')!;
    const phases = phaseViews(root);

    expect(workflow.querySelector(".state.state--active .state-text")?.textContent).toBe(
      message("state.active", "en"),
    );
    expect(ui.querySelector(".state.state--error .state-text")?.textContent).toBe(
      message("state.error", "en"),
    );
    expect(phases[0]!.querySelector(".phase-summary .state--done")).not.toBeNull();
    expect(phases[2]!.querySelector(".phase-summary .state--pending")).not.toBeNull();
    expect(phases[3]!.querySelector(".phase-summary .state--pending")).not.toBeNull();
  });

  it("renders each of the 21 closed Step IDs exactly once and in its approved phase order", () => {
    const { root } = renderFixture();
    const phases = phaseViews(root);
    const allIds: string[] = [];

    for (const [index, expectedIds] of STEP_IDS_BY_PHASE.entries()) {
      const ids = Array.from(phases[index]!.querySelectorAll<HTMLElement>(".step-row")).map(
        (row) => row.dataset.stepId!,
      );
      expect(ids).toEqual(expectedIds);
      allIds.push(...ids);
    }

    expect(allIds).toHaveLength(21);
    expect(new Set(allIds).size).toBe(21);
    expect(allIds).toEqual(STEP_IDS_BY_PHASE.flat());
  });

  it("adds only the two approved protected reports to the six existing report actions", () => {
    const root = document.createElement("main");
    const calls: unknown[][] = [];
    renderMainView(root, successSnapshot, "en", new Set(["PRODUCT_FORMATION"]), {
      togglePhase: () => undefined,
      openReport: (...args: [ReportId]) => calls.push(args),
    });

    const buttons = Array.from(root.querySelectorAll<HTMLButtonElement>("button.open-report"));
    expect(buttons).toHaveLength(8);
    for (const [stepId, reportId] of OPEN_MAPPINGS) {
      const row = root.querySelector<HTMLElement>(`[data-step-id="${stepId}"]`)!;
      const button = row.querySelector<HTMLButtonElement>("button.open-report")!;
      expect(button.type).toBe("button");
      expect(button.textContent).toBe(message("app.open", "en"));
      button.click();
      expect(calls.at(-1)).toEqual([reportId]);
    }
    expect(calls).toEqual(OPEN_MAPPINGS.map(([, reportId]) => [reportId]));
  });

  it("pairs every row's semantic state and approved symbol with adjacent readable text", () => {
    const { root } = renderFixture();
    const observedStates = new Set<string>();

    for (const phase of successSnapshot.phases) {
      for (const step of phase.steps) {
        const row = root.querySelector<HTMLElement>(`[data-step-id="${step.id}"]`)!;
        const state = row.querySelector<HTMLElement>(".state")!;
        const glyph = state.querySelector<HTMLElement>(":scope > .state-glyph")!;
        const text = state.querySelector<HTMLElement>(":scope > .state-text")!;

        observedStates.add(step.state);
        expect(state.className).toBe(`state state--${step.state}`);
        expect(glyph.matches(`.state--${step.state} > .state-glyph`)).toBe(true);
        expect(glyph.getAttribute("aria-hidden")).toBe("true");
        expect(glyph.nextElementSibling).toBe(text);
        expect(text.hasAttribute("aria-hidden")).toBe(false);
        expect(text.textContent).toBe(message(`state.${step.state}`, "en"));
      }
    }

    expect([...observedStates].sort()).toEqual(["active", "done", "error", "pending"]);
    const spinner = root.querySelector<HTMLElement>(
      '[data-step-id="WORKFLOW_CAPABILITY_END"] .state--active > .state-glyph',
    )!;
    expect(spinner.getAttribute("aria-hidden")).toBe("true");
    expect(spinner.nextElementSibling?.textContent).toBe(message("state.active", "en"));
  });

  it("uses safe inert DOM construction without markup injection, files, URLs, or navigation", () => {
    const descriptor = Object.getOwnPropertyDescriptor(Element.prototype, "innerHTML")!;
    let innerHtmlWrites = 0;
    Object.defineProperty(Element.prototype, "innerHTML", {
      configurable: true,
      enumerable: descriptor.enumerable ?? false,
      get: descriptor.get!,
      set: () => {
        innerHtmlWrites += 1;
        throw new Error("innerHTML is forbidden in the renderer");
      },
    });

    let root: HTMLElement;
    try {
      root = renderFixture().root;
    } finally {
      Object.defineProperty(Element.prototype, "innerHTML", descriptor);
    }

    expect(innerHtmlWrites).toBe(0);
    expect(root!.querySelector("a, form, input, img, iframe, object, embed")).toBeNull();
    expect(
      root!.querySelector("[href], [src], [action], [formaction], [download]"),
    ).toBeNull();
    expect(root!.outerHTML).not.toMatch(/(?:https?|file):\/\//iu);
    expect(Array.from(root!.querySelectorAll("button")).every((button) => button.type === "button")).toBe(
      true,
    );
  });

  it("replaces a complete error Snapshot with one visible red alert and no stale actions", () => {
    const { root } = renderFixture(errorSnapshot, "zh_CN");
    const alert = root.querySelector<HTMLElement>('.error-projection[role="alert"]')!;
    const projectName = alert.querySelector<HTMLElement>(".project-name");

    expect(alert).not.toBeNull();
    expect(alert.hidden).toBe(false);
    expect(alert.hasAttribute("aria-hidden")).toBe(false);
    expect(projectName?.textContent).toBe(message("app.unnamed_project", "zh_CN"));
    expect(projectName?.textContent).not.toBe(errorSnapshot.project);
    expect(alert.querySelector(".state.state--error .state-glyph[aria-hidden=\"true\"]")).not.toBeNull();
    expect(alert.querySelector(".state.state--error .state-text")?.textContent).toBe(
      message("state.error", "zh_CN"),
    );
    expect(alert.textContent).toContain(message("app.error", "zh_CN"));
    expect(root.querySelector(".phase-list, .step-row, .open-report")).toBeNull();
    expect(root.querySelector(".state--done, .state--active, .state--pending")).toBeNull();
    expect(root.textContent).not.toContain(message("app.open", "zh_CN"));
  });
});
