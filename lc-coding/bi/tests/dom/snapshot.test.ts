import "./setup";

import { describe, expect, it } from "vitest";

import { parseSnapshot } from "../../src/model/snapshot";
import errorFixture from "../fixtures/snapshot-error.json";
import successFixture from "../fixtures/snapshot-ok.json";

const PHASE_IDS = [
  "INITIAL",
  "PRODUCT_FORMATION",
  "ENGINEERING_RUNS",
  "DELIVERY_PREPARATION",
] as const;

const REPORT_IDS = [
  "proposal",
  "candidate",
  "calabash",
  "simulation",
  "workflow",
  "ui",
] as const;

const EXPECTED_SUCCESS = {
  schema: "LCCoding 2.3.0 derived BI",
  authoritative: false,
  read_only: true,
  health: "ok",
  project: "Example Project",
  current_phase: "PRODUCT_FORMATION",
  phases: [
    {
      id: "INITIAL",
      state: "done",
      steps: [
        { id: "PROPOSAL_READINESS", state: "done", report: "proposal" },
        { id: "PROJECT_INITIALIZATION", state: "done", report: "candidate" },
        { id: "INITIAL_READY", state: "done", report: null },
      ],
    },
    {
      id: "PRODUCT_FORMATION",
      state: "active",
      steps: [
        { id: "CALABASH_DRAFT", state: "done", report: "calabash" },
        { id: "SIMULATION_WORLD_FOUNDATION", state: "done", report: "simulation" },
        { id: "WORKFLOW_CAPABILITY_END", state: "active", report: "workflow" },
        { id: "UI_PRODUCT_SURFACE_END", state: "error", report: "ui" },
        { id: "CALABASH_UPGRADE_READY", state: "pending", report: null },
      ],
    },
    {
      id: "ENGINEERING_RUNS",
      state: "pending",
      steps: [
        { id: "MANDATORY_CALABASH_UPGRADE", state: "pending", report: null },
        { id: "PRODUCT_BASELINE", state: "pending", report: null },
        { id: "FEATURE_SLICE_EXECUTION_COVERAGE", state: "pending", report: null },
        { id: "UI_LOCKED_INTEGRATION_BASELINE", state: "pending", report: null },
        { id: "LOOP_RUN_D0_D3", state: "pending", report: null },
        { id: "LOOP_OWNER_ACCEPTANCE", state: "pending", report: null },
        { id: "ALL_REQUIRED_RUNS_ACCEPTED", state: "pending", report: null },
      ],
    },
    {
      id: "DELIVERY_PREPARATION",
      state: "pending",
      steps: [
        { id: "CENTRALIZED_VULNERABILITY_AUDIT", state: "pending", report: null },
        { id: "SECURITY_REMEDIATION", state: "pending", report: null },
        {
          id: "SECURITY_REAUDIT_VULNERABILITY_CLOSURE",
          state: "pending",
          report: null,
        },
        { id: "POST_SECURITY_OWNER_ACCEPTANCE", state: "pending", report: null },
        { id: "DELIVERY_METHOD_QA", state: "pending", report: null },
        { id: "DELIVERY_PACKAGE_GUARD_READY", state: "pending", report: null },
      ],
    },
  ],
  reports: {
    proposal: {
      id: "proposal",
      state: "done",
      version: null,
      rows: [
        { key: "row.conclusion", value: { kind: "view_state", value: "done" } },
        { key: "row.initial_gate", value: { kind: "view_state", value: "done" } },
      ],
    },
    candidate: {
      id: "candidate",
      state: "done",
      version: "v1.11.6",
      rows: [
        { key: "row.identity", value: { kind: "lock", value: "LOCKED" } },
        { key: "row.integrity", value: { kind: "record", value: "RECORDED" } },
      ],
    },
    calabash: {
      id: "calabash",
      state: "done",
      version: "v2.4.0",
      rows: [
        { key: "row.status", value: { kind: "view_state", value: "done" } },
        { key: "row.version_record", value: { kind: "record", value: "RECORDED" } },
      ],
    },
    simulation: {
      id: "simulation",
      state: "done",
      version: null,
      rows: [
        { key: "row.status", value: { kind: "view_state", value: "done" } },
        {
          key: "row.current_phase",
          value: { kind: "phase", value: "PRODUCT_FORMATION" },
        },
      ],
    },
    workflow: {
      id: "workflow",
      state: "active",
      version: null,
      rows: [
        { key: "row.status", value: { kind: "view_state", value: "active" } },
        {
          key: "row.current_phase",
          value: { kind: "phase", value: "PRODUCT_FORMATION" },
        },
      ],
    },
    ui: {
      id: "ui",
      state: "error",
      version: null,
      rows: [
        { key: "row.status", value: { kind: "view_state", value: "error" } },
        {
          key: "row.current_phase",
          value: { kind: "phase", value: "PRODUCT_FORMATION" },
        },
      ],
    },
  },
} as const;

const errorStep = (id: string, report: string | null = null) => ({
  id,
  state: "error",
  report,
});

const EXPECTED_ERROR = {
  schema: "LCCoding 2.3.0 derived BI",
  authoritative: false,
  read_only: true,
  health: "error",
  project: "Unnamed project",
  current_phase: "UNKNOWN",
  phases: [
    {
      id: "INITIAL",
      state: "error",
      steps: [
        errorStep("PROPOSAL_READINESS", "proposal"),
        errorStep("PROJECT_INITIALIZATION", "candidate"),
        errorStep("INITIAL_READY"),
      ],
    },
    {
      id: "PRODUCT_FORMATION",
      state: "error",
      steps: [
        errorStep("CALABASH_DRAFT", "calabash"),
        errorStep("SIMULATION_WORLD_FOUNDATION", "simulation"),
        errorStep("WORKFLOW_CAPABILITY_END", "workflow"),
        errorStep("UI_PRODUCT_SURFACE_END", "ui"),
        errorStep("CALABASH_UPGRADE_READY"),
      ],
    },
    {
      id: "ENGINEERING_RUNS",
      state: "error",
      steps: [
        errorStep("MANDATORY_CALABASH_UPGRADE"),
        errorStep("PRODUCT_BASELINE"),
        errorStep("FEATURE_SLICE_EXECUTION_COVERAGE"),
        errorStep("UI_LOCKED_INTEGRATION_BASELINE"),
        errorStep("LOOP_RUN_D0_D3"),
        errorStep("LOOP_OWNER_ACCEPTANCE"),
        errorStep("ALL_REQUIRED_RUNS_ACCEPTED"),
      ],
    },
    {
      id: "DELIVERY_PREPARATION",
      state: "error",
      steps: [
        errorStep("CENTRALIZED_VULNERABILITY_AUDIT"),
        errorStep("SECURITY_REMEDIATION"),
        errorStep("SECURITY_REAUDIT_VULNERABILITY_CLOSURE"),
        errorStep("POST_SECURITY_OWNER_ACCEPTANCE"),
        errorStep("DELIVERY_METHOD_QA"),
        errorStep("DELIVERY_PACKAGE_GUARD_READY"),
      ],
    },
  ],
  reports: {
    proposal: {
      id: "proposal",
      state: "error",
      version: null,
      rows: [
        { key: "row.conclusion", value: { kind: "view_state", value: "error" } },
        { key: "row.initial_gate", value: { kind: "view_state", value: "error" } },
      ],
    },
    candidate: {
      id: "candidate",
      state: "error",
      version: null,
      rows: [
        { key: "row.identity", value: { kind: "lock", value: "UNKNOWN" } },
        { key: "row.integrity", value: { kind: "record", value: "UNKNOWN" } },
      ],
    },
    calabash: {
      id: "calabash",
      state: "error",
      version: null,
      rows: [
        { key: "row.status", value: { kind: "view_state", value: "error" } },
        { key: "row.version_record", value: { kind: "record", value: "UNKNOWN" } },
      ],
    },
    simulation: {
      id: "simulation",
      state: "error",
      version: null,
      rows: [
        { key: "row.status", value: { kind: "view_state", value: "error" } },
        { key: "row.current_phase", value: { kind: "phase", value: "UNKNOWN" } },
      ],
    },
    workflow: {
      id: "workflow",
      state: "error",
      version: null,
      rows: [
        { key: "row.status", value: { kind: "view_state", value: "error" } },
        { key: "row.current_phase", value: { kind: "phase", value: "UNKNOWN" } },
      ],
    },
    ui: {
      id: "ui",
      state: "error",
      version: null,
      rows: [
        { key: "row.status", value: { kind: "view_state", value: "error" } },
        { key: "row.current_phase", value: { kind: "phase", value: "UNKNOWN" } },
      ],
    },
  },
} as const;

type JsonObject = { [key: string]: JsonValue };
type JsonValue = JsonObject | JsonValue[] | boolean | null | number | string;

function object(value: unknown): JsonObject {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new TypeError("expected object in test fixture mutation");
  }
  return value as JsonObject;
}

function array(value: unknown): JsonValue[] {
  if (!Array.isArray(value)) {
    throw new TypeError("expected array in test fixture mutation");
  }
  return value as JsonValue[];
}

function phase(root: JsonObject, index = 0): JsonObject {
  return object(array(root.phases)[index]);
}

function step(root: JsonObject, phaseIndex = 0, stepIndex = 0): JsonObject {
  return object(array(phase(root, phaseIndex).steps)[stepIndex]);
}

function report(root: JsonObject, id: string): JsonObject {
  return object(object(root.reports)[id]);
}

function row(root: JsonObject, id: string, index = 0): JsonObject {
  return object(array(report(root, id).rows)[index]);
}

function rowValue(root: JsonObject, id: string, index = 0): JsonObject {
  return object(row(root, id, index).value);
}

function mutated(change: (draft: JsonObject) => void): unknown {
  const draft = structuredClone(successFixture) as JsonObject;
  change(draft);
  return draft;
}

function expectDeepFrozen(value: unknown): void {
  if (value === null || typeof value !== "object") {
    return;
  }
  expect(Object.isFrozen(value)).toBe(true);
  for (const child of Object.values(value)) {
    expectDeepFrozen(child);
  }
}

function collectKeys(value: unknown, keys: string[] = []): string[] {
  if (Array.isArray(value)) {
    for (const child of value) collectKeys(child, keys);
  } else if (value !== null && typeof value === "object") {
    for (const [key, child] of Object.entries(value)) {
      keys.push(key);
      collectKeys(child, keys);
    }
  }
  return keys;
}

describe("parseSnapshot", () => {
  it.each([
    ["success", successFixture, EXPECTED_SUCCESS],
    ["error", errorFixture, EXPECTED_ERROR],
  ])("accepts the exact %s fixture as a fresh deep-frozen Snapshot", (_name, fixture, exact) => {
    expect(fixture).toEqual(exact);
    expect(Object.keys(fixture.reports)).toEqual(REPORT_IDS);
    expect(fixture.phases.map(({ id }) => id)).toEqual(PHASE_IDS);

    const parsed = parseSnapshot(fixture);

    expect(parsed).toEqual(exact);
    expect(parsed).not.toBe(fixture);
    expect(parsed.phases).not.toBe(fixture.phases);
    expect(parsed.reports).not.toBe(fixture.reports);
    expectDeepFrozen(parsed);
  });

  it("keeps both serialized fixtures free of raw or diagnostic fields", () => {
    const forbiddenKey =
      /^(?:repository|commit|path|evidence(?:_.*)?|url|date|updated_at|parser(?:_.*)?|details?|message|stack|raw|error_(?:code|details?|message|stack))$/iu;
    const forbiddenValue =
      /(?:https?:\/\/|file:\/\/|[A-Za-z]:[\\/]|\b[0-9a-f]{40,64}\b|\d{4}-\d{2}-\d{2}T|BI_[A-Z_]+)/u;

    for (const fixture of [successFixture, errorFixture]) {
      expect(collectKeys(fixture).filter((key) => forbiddenKey.test(key))).toEqual([]);
      expect(JSON.stringify(fixture)).not.toMatch(forbiddenValue);
    }
  });

  it.each([
    ["unknown top-level key", (draft: JsonObject) => void (draft.extra = true)],
    ["unknown recursive key", (draft: JsonObject) => void (row(draft, "proposal").extra = true)],
    ["missing top-level key", (draft: JsonObject) => void delete draft.health],
    ["missing recursive key", (draft: JsonObject) => void delete step(draft).state],
    ["wrong phase tuple", (draft: JsonObject) => void (phase(draft).id = "PRODUCT_FORMATION")],
    ["missing phase tuple item", (draft: JsonObject) => void array(draft.phases).pop()],
    ["reordered phase tuple", (draft: JsonObject) => void array(draft.phases).reverse()],
    ["wrong step tuple", (draft: JsonObject) => void (step(draft).id = "INITIAL_READY")],
    ["missing step tuple item", (draft: JsonObject) => void array(phase(draft).steps).pop()],
    ["missing step tuple slot", (draft: JsonObject) => void delete array(phase(draft).steps)[0]],
    [
      "reordered step tuple",
      (draft: JsonObject) => {
        const steps = array(phase(draft).steps);
        [steps[0], steps[1]] = [steps[1]!, steps[0]!];
      },
    ],
    ["wrong report tuple", (draft: JsonObject) => void (report(draft, "proposal").id = "candidate")],
    ["missing report tuple item", (draft: JsonObject) => void delete object(draft.reports).ui],
    [
      "reordered report tuple",
      (draft: JsonObject) => {
        const reports = object(draft.reports);
        draft.reports = {
          candidate: reports.candidate!,
          proposal: reports.proposal!,
          calabash: reports.calabash!,
          simulation: reports.simulation!,
          workflow: reports.workflow!,
          ui: reports.ui!,
        };
      },
    ],
    ["wrong row kind", (draft: JsonObject) => void (rowValue(draft, "proposal").kind = "phase")],
    ["wrong row order", (draft: JsonObject) => void array(report(draft, "proposal").rows).reverse()],
    ["extra report", (draft: JsonObject) => void (object(draft.reports).extra = report(draft, "ui"))],
  ])("rejects %s", (_name, change) => {
    expect(() => parseSnapshot(mutated(change))).toThrow(TypeError);
  });

  it.each([
    ["Snapshot", (draft: JsonObject) => void (draft.schema = "LCCoding 2.3 derived BI")],
    ["reports object", (draft: JsonObject) => void (object(draft.reports).proposal = null)],
    ["PhaseView", (draft: JsonObject) => void (phase(draft).state = "DONE")],
    ["StepView", (draft: JsonObject) => void (step(draft).report = "ui")],
    ["ReportView", (draft: JsonObject) => void (report(draft, "candidate").version = " v1.11.6")],
    ["ReportRow", (draft: JsonObject) => void (row(draft, "proposal").key = "row.unknown")],
    ["view_state RowValue", (draft: JsonObject) => void (rowValue(draft, "proposal").value = "UNKNOWN")],
    ["phase RowValue", (draft: JsonObject) => void (rowValue(draft, "simulation", 1).value = "active")],
    ["lock RowValue", (draft: JsonObject) => void (rowValue(draft, "candidate").value = "RECORDED")],
    ["record RowValue", (draft: JsonObject) => void (rowValue(draft, "candidate", 1).value = "LOCKED")],
  ])("rejects a one-field mutation of %s", (_name, change) => {
    expect(() => parseSnapshot(mutated(change))).toThrow(TypeError);
  });
});
