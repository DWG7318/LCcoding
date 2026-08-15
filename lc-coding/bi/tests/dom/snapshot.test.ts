import "./setup";

import { describe, expect, it } from "vitest";

import { parseSnapshot } from "../../src/model/snapshot";
import errorFixture from "../fixtures/snapshot-error.json";
import successFixture from "../fixtures/snapshot-ok.json";

const PHASE_IDS_280 = [
  "INITIAL",
  "PRODUCT_FORMATION",
  "REAL_PRODUCT_INTEGRATION",
  "DELIVERY_PREPARATION",
] as const;

const REPORT_IDS = [
  "proposal",
  "candidate",
  "calabash",
  "simulation",
  "workflow",
  "ui",
  "baseline",
  "loop_governance",
] as const;

const REPORT_STATE_BINDINGS = [
  ["proposal", 0, 0, "pending"],
  ["candidate", 0, 1, "pending"],
  ["calabash", 1, 0, "pending"],
  ["simulation", 1, 1, "pending"],
  ["workflow", 1, 2, "done"],
  ["ui", 1, 3, "pending"],
  ["baseline", 1, 6, "done"],
  ["loop_governance", 2, 2, "done"],
] as const;

const NOT_RECORDED_METRIC = {
  kind: "metric",
  status: "NOT_RECORDED",
  completed: null,
  total: null,
  interval_minutes: null,
} as const;

const UNKNOWN_METRIC = {
  kind: "metric",
  status: "UNKNOWN",
  completed: null,
  total: null,
  interval_minutes: null,
} as const;

const EXPECTED_SUCCESS = {
  schema: "LCCoding 2.8.0 derived BI",
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
        { id: "MANDATORY_CALABASH_UPGRADE", state: "pending", report: null },
        { id: "PRODUCT_BASELINE", state: "pending", report: "baseline" },
      ],
    },
    {
      id: "REAL_PRODUCT_INTEGRATION",
      state: "pending",
      steps: [
        { id: "FEATURE_SLICE_EXECUTION_COVERAGE", state: "pending", report: null },
        { id: "UI_LOCKED_INTEGRATION_BASELINE", state: "pending", report: null },
        { id: "LOOP_RUN_D0_D3", state: "pending", report: "loop_governance" },
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
        {
          key: "row.operations_agent_integration",
          value: { kind: "record", value: "UNPROVED" },
        },
        {
          key: "row.product_agent_integration",
          value: { kind: "agent_status", applicability: "UNPROVED", integration: "UNPROVED" },
        },
        {
          key: "row.runtime_adapter",
          value: { kind: "safe_identity", id: "NOT_APPLICABLE", version: "NOT_APPLICABLE" },
        },
        {
          key: "row.dual_agent_isolation",
          value: { kind: "record", value: "UNPROVED" },
        },
        {
          key: "row.product_slice_progress",
          value: {
            kind: "metric",
            status: "UNPROVED",
            completed: 0,
            total: null,
            interval_minutes: null,
          },
        },
        {
          key: "row.operations_slice_progress",
          value: {
            kind: "metric",
            status: "UNPROVED",
            completed: 0,
            total: null,
            interval_minutes: null,
          },
        },
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
        { key: "row.realized_peer_subtrees", value: NOT_RECORDED_METRIC },
        { key: "row.component_version_coverage", value: NOT_RECORDED_METRIC },
        { key: "row.primary_mainline", value: NOT_RECORDED_METRIC },
      ],
    },
    workflow: {
      id: "workflow",
      state: "active",
      version: null,
      rows: [
        { key: "row.core_implementation", value: NOT_RECORDED_METRIC },
        { key: "row.extra_implemented", value: NOT_RECORDED_METRIC },
        { key: "row.extra_deferred", value: NOT_RECORDED_METRIC },
        { key: "row.api_coverage", value: NOT_RECORDED_METRIC },
        { key: "row.mcp_coverage", value: NOT_RECORDED_METRIC },
        { key: "row.component_version_coverage", value: NOT_RECORDED_METRIC },
        { key: "row.primary_mainline", value: NOT_RECORDED_METRIC },
      ],
    },
    ui: {
      id: "ui",
      state: "error",
      version: null,
      rows: [
        { key: "row.realized_subtrees", value: NOT_RECORDED_METRIC },
        { key: "row.component_version_coverage", value: NOT_RECORDED_METRIC },
        { key: "row.lock_status", value: NOT_RECORDED_METRIC },
        { key: "row.primary_mainline", value: NOT_RECORDED_METRIC },
      ],
    },
    baseline: {
      id: "baseline",
      state: "pending",
      version: null,
      rows: [
        { key: "row.git_identity", value: NOT_RECORDED_METRIC },
        { key: "row.locked_subtree_coverage", value: NOT_RECORDED_METRIC },
        { key: "row.map_handoff_consistency", value: NOT_RECORDED_METRIC },
        { key: "row.owner_confirmed_mainline", value: NOT_RECORDED_METRIC },
      ],
    },
    loop_governance: {
      id: "loop_governance",
      state: "pending",
      version: null,
      rows: [
        { key: "row.worker_checker_wake", value: NOT_RECORDED_METRIC },
        { key: "row.supervisor_wait", value: NOT_RECORDED_METRIC },
        { key: "row.heartbeat", value: NOT_RECORDED_METRIC },
        { key: "row.no_subagents", value: NOT_RECORDED_METRIC },
        { key: "row.progress", value: NOT_RECORDED_METRIC },
        { key: "row.cell_capacity", value: NOT_RECORDED_METRIC },
        { key: "row.pin_policy", value: NOT_RECORDED_METRIC },
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
  schema: "LCCoding 2.6.0 derived BI",
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
        errorStep("PRODUCT_BASELINE", "baseline"),
        errorStep("FEATURE_SLICE_EXECUTION_COVERAGE"),
        errorStep("UI_LOCKED_INTEGRATION_BASELINE"),
        errorStep("LOOP_RUN_D0_D3", "loop_governance"),
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
        { key: "row.realized_peer_subtrees", value: UNKNOWN_METRIC },
        { key: "row.component_version_coverage", value: UNKNOWN_METRIC },
        { key: "row.primary_mainline", value: UNKNOWN_METRIC },
      ],
    },
    workflow: {
      id: "workflow",
      state: "error",
      version: null,
      rows: [
        { key: "row.core_implementation", value: UNKNOWN_METRIC },
        { key: "row.extra_implemented", value: UNKNOWN_METRIC },
        { key: "row.extra_deferred", value: UNKNOWN_METRIC },
        { key: "row.api_coverage", value: UNKNOWN_METRIC },
        { key: "row.mcp_coverage", value: UNKNOWN_METRIC },
        { key: "row.component_version_coverage", value: UNKNOWN_METRIC },
        { key: "row.primary_mainline", value: UNKNOWN_METRIC },
      ],
    },
    ui: {
      id: "ui",
      state: "error",
      version: null,
      rows: [
        { key: "row.realized_subtrees", value: UNKNOWN_METRIC },
        { key: "row.component_version_coverage", value: UNKNOWN_METRIC },
        { key: "row.lock_status", value: UNKNOWN_METRIC },
        { key: "row.primary_mainline", value: UNKNOWN_METRIC },
      ],
    },
    baseline: {
      id: "baseline",
      state: "error",
      version: null,
      rows: [
        { key: "row.git_identity", value: UNKNOWN_METRIC },
        { key: "row.locked_subtree_coverage", value: UNKNOWN_METRIC },
        { key: "row.map_handoff_consistency", value: UNKNOWN_METRIC },
        { key: "row.owner_confirmed_mainline", value: UNKNOWN_METRIC },
      ],
    },
    loop_governance: {
      id: "loop_governance",
      state: "error",
      version: null,
      rows: [
        { key: "row.worker_checker_wake", value: UNKNOWN_METRIC },
        { key: "row.supervisor_wait", value: UNKNOWN_METRIC },
        { key: "row.heartbeat", value: UNKNOWN_METRIC },
        { key: "row.no_subagents", value: UNKNOWN_METRIC },
        { key: "row.progress", value: UNKNOWN_METRIC },
        { key: "row.cell_capacity", value: UNKNOWN_METRIC },
        { key: "row.pin_policy", value: UNKNOWN_METRIC },
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

function legacy270Fixture(): JsonObject {
  const draft = structuredClone(successFixture) as JsonObject;
  draft.schema = "LCCoding 2.7.0 derived BI";
  phase(draft, 2).id = "ENGINEERING_RUNS";
  array(report(draft, "candidate").rows).splice(2);
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
    expect(fixture.phases.map(({ id }) => id)).toEqual(exact.phases.map(({ id }) => id));

    const parsed = parseSnapshot(fixture);

    expect(parsed).toEqual(exact);
    expect(parsed).not.toBe(fixture);
    expect(parsed.phases).not.toBe(fixture.phases);
    expect(parsed.reports).not.toBe(fixture.reports);
    expectDeepFrozen(parsed);
  });

  it("keeps both serialized fixtures free of raw or diagnostic fields", () => {
    const forbiddenKey =
      /^(?:repository|commit|hash(?:_.*)?|path|evidence(?:_.*)?|thread(?:_.*)?|url|date|updated_at|parser(?:_.*)?|details?|message|stack|raw|error_(?:code|details?|message|stack))$/iu;
    const forbiddenValue =
      /(?:https?:\/\/|file:\/\/|[A-Za-z]:[\\/]|\b[0-9a-f]{40,64}\b|\d{4}-\d{2}-\d{2}T|BI_[A-Z_]+)/u;

    for (const fixture of [successFixture, errorFixture]) {
      expect(collectKeys(fixture).filter((key) => forbiddenKey.test(key))).toEqual([]);
      expect(JSON.stringify(fixture)).not.toMatch(forbiddenValue);
    }
  });

  it("binds each accepted schema to exactly one phase and step tuple", () => {
    expect(parseSnapshot(structuredClone(successFixture)).schema).toBe(
      "LCCoding 2.8.0 derived BI",
    );
    expect(parseSnapshot(structuredClone(errorFixture)).schema).toBe(
      "LCCoding 2.6.0 derived BI",
    );

    const legacy270 = legacy270Fixture();
    expect(parseSnapshot(legacy270)).toEqual(legacy270);

    expect(() =>
      parseSnapshot(mutated((draft) => {
        draft.schema = "LCCoding 2.6.0 derived BI";
      })),
    ).toThrow(TypeError);

    const legacyAsCurrent = structuredClone(errorFixture) as JsonObject;
    legacyAsCurrent.schema = "LCCoding 2.7.0 derived BI";
    expect(() => parseSnapshot(legacyAsCurrent)).toThrow(TypeError);

    const hybrid280 = legacy270Fixture();
    hybrid280.schema = "LCCoding 2.8.0 derived BI";
    expect(() => parseSnapshot(hybrid280)).toThrow(TypeError);

    const hybrid270 = legacy270Fixture();
    phase(hybrid270, 2).id = PHASE_IDS_280[2];
    expect(() => parseSnapshot(hybrid270)).toThrow(TypeError);

    expect(() =>
      parseSnapshot(mutated((draft) => {
        const formation = array(phase(draft, 1).steps);
        const engineering = array(phase(draft, 2).steps);
        engineering.unshift(formation.pop()!);
      })),
    ).toThrow(TypeError);
  });

  it.each(REPORT_STATE_BINDINGS)(
    "rejects %s report state when it differs from its bound StepView",
    (reportId, phaseIndex, stepIndex, mismatchState) => {
      expect(() =>
        parseSnapshot(mutated((draft) => {
          const boundStep = step(draft, phaseIndex, stepIndex);
          expect(boundStep.report).toBe(reportId);
          expect(boundStep.state).not.toBe(mismatchState);
          report(draft, reportId).state = mismatchState;
        })),
      ).toThrow(TypeError);
    },
  );

  it.each([
    ["unknown top-level key", (draft: JsonObject) => void (draft.extra = true)],
    ["unknown recursive key", (draft: JsonObject) => void (row(draft, "proposal").extra = true)],
    ["missing top-level key", (draft: JsonObject) => void delete draft.health],
    ["missing recursive key", (draft: JsonObject) => void delete step(draft).state],
    ["wrong phase tuple", (draft: JsonObject) => void (phase(draft).id = "PRODUCT_FORMATION")],
    ["missing phase tuple item", (draft: JsonObject) => void array(draft.phases).pop()],
    ["reordered phase tuple", (draft: JsonObject) => void array(draft.phases).reverse()],
    ["wrong step tuple", (draft: JsonObject) => void (step(draft).id = "INITIAL_READY")],
    ["duplicate step tuple", (draft: JsonObject) => void (step(draft, 1, 6).id = "MANDATORY_CALABASH_UPGRADE")],
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
          baseline: reports.baseline!,
          loop_governance: reports.loop_governance!,
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
    ["Snapshot", (draft: JsonObject) => void (draft.schema = "LCCoding 2.4.0 derived BI")],
    ["reports object", (draft: JsonObject) => void (object(draft.reports).proposal = null)],
    ["PhaseView", (draft: JsonObject) => void (phase(draft).state = "DONE")],
    ["StepView", (draft: JsonObject) => void (step(draft).report = "ui")],
    ["ReportView", (draft: JsonObject) => void (report(draft, "candidate").version = " v1.11.6")],
    ["ReportRow", (draft: JsonObject) => void (row(draft, "proposal").key = "row.unknown")],
    ["view_state RowValue", (draft: JsonObject) => void (rowValue(draft, "proposal").value = "UNKNOWN")],
    ["phase RowValue", (draft: JsonObject) => void (rowValue(draft, "proposal").kind = "phase")],
    ["lock RowValue", (draft: JsonObject) => void (rowValue(draft, "candidate").value = "RECORDED")],
    ["record RowValue", (draft: JsonObject) => void (rowValue(draft, "candidate", 1).value = "LOCKED")],
    ["metric RowValue", (draft: JsonObject) => void (rowValue(draft, "baseline").status = "DONE")],
    ["Agent record RowValue", (draft: JsonObject) => void (rowValue(draft, "candidate", 2).value = "VERIFIED")],
    ["AgentStatus applicability", (draft: JsonObject) => void (rowValue(draft, "candidate", 3).applicability = "CORE")],
    ["AgentStatus integration", (draft: JsonObject) => void (rowValue(draft, "candidate", 3).integration = "PENDING")],
    ["SafeIdentity id", (draft: JsonObject) => void (rowValue(draft, "candidate", 4).id = "sk-secret")],
    ["SafeIdentity version", (draft: JsonObject) => void (rowValue(draft, "candidate", 4).version = "latest")],
    ["SafeIdentity raw hash", (draft: JsonObject) => void (rowValue(draft, "candidate", 4).hash = "raw")],
    ["Agent Slice metric", (draft: JsonObject) => void (rowValue(draft, "candidate", 6).status = "ACTIVE")],
  ])("rejects a one-field mutation of %s", (_name, change) => {
    expect(() => parseSnapshot(mutated(change))).toThrow(TypeError);
  });

  it("accepts only the exact accepted Agent summary forms and keeps the two Slice counts independent", () => {
    const parsed = parseSnapshot(mutated((draft) => {
      rowValue(draft, "candidate", 2).value = "ACCEPTED";
      Object.assign(rowValue(draft, "candidate", 3), {
        applicability: "APPLICABLE_CORE",
        integration: "ACCEPTED",
      });
      Object.assign(rowValue(draft, "candidate", 4), {
        id: "RUNTIME-ADAPTER-1",
        version: "1.2.3",
      });
      rowValue(draft, "candidate", 5).value = "VERIFIED";
      Object.assign(rowValue(draft, "candidate", 6), { status: "ACCEPTED", completed: 2 });
      Object.assign(rowValue(draft, "candidate", 7), { status: "ACCEPTED", completed: 1 });
    }));

    expect(parsed.reports.candidate.rows[3]?.value).toEqual({
      kind: "agent_status",
      applicability: "APPLICABLE_CORE",
      integration: "ACCEPTED",
    });
    expect(parsed.reports.candidate.rows[4]?.value).toEqual({
      kind: "safe_identity",
      id: "RUNTIME-ADAPTER-1",
      version: "1.2.3",
    });
    expect(parsed.reports.candidate.rows[6]?.value).toMatchObject({ completed: 2 });
    expect(parsed.reports.candidate.rows[7]?.value).toMatchObject({ completed: 1 });
  });

  it("accepts Product Agent not-applicable only as a closed not-applicable pair", () => {
    const parsed = parseSnapshot(mutated((draft) => {
      rowValue(draft, "candidate", 2).value = "ACCEPTED";
      Object.assign(rowValue(draft, "candidate", 3), {
        applicability: "NOT_APPLICABLE",
        integration: "NOT_APPLICABLE",
      });
      Object.assign(rowValue(draft, "candidate", 4), {
        id: "RUNTIME-ADAPTER-1",
        version: "1.2.3",
      });
      rowValue(draft, "candidate", 5).value = "VERIFIED";
      Object.assign(rowValue(draft, "candidate", 6), { status: "ACCEPTED", completed: 1 });
      Object.assign(rowValue(draft, "candidate", 7), { status: "ACCEPTED", completed: 1 });
    }));
    expect(parsed.reports.candidate.rows[3]?.value).toEqual({
      kind: "agent_status",
      applicability: "NOT_APPLICABLE",
      integration: "NOT_APPLICABLE",
    });

    expect(() =>
      parseSnapshot(mutated((draft) => {
        rowValue(draft, "candidate", 2).value = "ACCEPTED";
        Object.assign(rowValue(draft, "candidate", 3), {
          applicability: "NOT_APPLICABLE",
          integration: "ACCEPTED",
        });
        Object.assign(rowValue(draft, "candidate", 4), {
          id: "RUNTIME-ADAPTER-1",
          version: "1.2.3",
        });
        rowValue(draft, "candidate", 5).value = "VERIFIED";
        Object.assign(rowValue(draft, "candidate", 6), { status: "ACCEPTED", completed: 1 });
        Object.assign(rowValue(draft, "candidate", 7), { status: "ACCEPTED", completed: 1 });
      })),
    ).toThrow(TypeError);
  });

  it("rejects mixed UNPROVED and accepted Agent summary rows", () => {
    expect(() =>
      parseSnapshot(mutated((draft) => {
        rowValue(draft, "candidate", 2).value = "ACCEPTED";
      })),
    ).toThrow(TypeError);
  });

  it.each([
    "secret",
    "token",
    "path",
    "hash",
    "raw_prompt",
    "memory",
    "credential",
    "event",
  ])("rejects %s material attached to SafeIdentity", (field) => {
    expect(() =>
      parseSnapshot(mutated((draft) => {
        rowValue(draft, "candidate", 4)[field] = "hidden";
      })),
    ).toThrow(TypeError);
  });

  it.each([
    ["negative completed", (value: JsonObject) => void (value.completed = -1)],
    ["fractional completed", (value: JsonObject) => void (value.completed = 0.5)],
    ["oversized completed", (value: JsonObject) => void (value.completed = 1_000_001)],
    ["negative total", (value: JsonObject) => void (value.total = -1)],
    ["completed over total", (value: JsonObject) => {
      value.status = "ACTIVE";
      value.completed = 2;
      value.total = 1;
    }],
    ["total without completed", (value: JsonObject) => {
      value.status = "ACTIVE";
      value.total = 1;
    }],
    ["invalid Heartbeat interval", (value: JsonObject) => {
      value.status = "ACTIVE";
      value.interval_minutes = 20;
    }],
    ["invented UNKNOWN progress", (value: JsonObject) => void (value.completed = 7)],
    ["raw path field", (value: JsonObject) => void (value.path = "C:\\private")],
  ])("rejects metric %s", (_name, change) => {
    expect(() =>
      parseSnapshot(mutated((draft) => change(rowValue(draft, "loop_governance")))),
    ).toThrow(TypeError);
  });

  it("accepts only bounded honest metric forms and the fixed Heartbeat intervals", () => {
    const parsed = parseSnapshot(mutated((draft) => {
      Object.assign(rowValue(draft, "simulation"), {
        status: "COMPLIANT",
        completed: 2,
      });
      Object.assign(rowValue(draft, "workflow"), {
        status: "ACTIVE",
        completed: 2,
        total: 3,
      });
      Object.assign(rowValue(draft, "baseline"), {
        status: "VIOLATION",
      });
      Object.assign(rowValue(draft, "loop_governance", 2), {
        status: "ACTIVE",
        interval_minutes: 15,
      });
    }));

    expect(parsed.reports.simulation.rows[0]?.value).toMatchObject({ completed: 2 });
    expect(parsed.reports.workflow.rows[0]?.value).toMatchObject({ completed: 2, total: 3 });
    expect(parsed.reports.baseline.rows[0]?.value).toMatchObject({ status: "VIOLATION" });
    expect(parsed.reports.loop_governance.rows[2]?.value).toMatchObject({
      status: "ACTIVE",
      interval_minutes: 15,
    });
  });

  it("rejects an otherwise valid Heartbeat interval on any non-Heartbeat metric", () => {
    expect(() =>
      parseSnapshot(mutated((draft) => {
        Object.assign(rowValue(draft, "simulation"), {
          status: "ACTIVE",
          interval_minutes: 15,
        });
      })),
    ).toThrow(TypeError);
  });

  it.each([
    ["phase tuple", (draft: JsonObject) => array(draft.phases)],
    ["step tuple", (draft: JsonObject) => array(phase(draft).steps)],
    ["report-row tuple", (draft: JsonObject) => array(report(draft, "proposal").rows)],
  ])("rejects a poisoned %s without invoking inherited methods", (_name, select) => {
    let poisonCalls = 0;
    const input = mutated((draft) => {
      const poisonedPrototype: object = Object.create(Array.prototype);
      Object.defineProperty(poisonedPrototype, "map", {
        value: () => {
          poisonCalls += 1;
          throw new Error("poisoned map invoked");
        },
      });
      Object.setPrototypeOf(select(draft), poisonedPrototype);
    });

    let thrown: unknown;
    try {
      parseSnapshot(input);
    } catch (error) {
      thrown = error;
    }

    expect({ rejected: thrown instanceof TypeError, poisonCalls }).toEqual({
      rejected: true,
      poisonCalls: 0,
    });
  });
});
