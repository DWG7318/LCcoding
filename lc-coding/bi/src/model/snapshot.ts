export type Health = "ok" | "error";
export type ViewState = "done" | "active" | "pending" | "error";

export type PhaseId =
  | "INITIAL"
  | "PRODUCT_FORMATION"
  | "ENGINEERING_RUNS"
  | "DELIVERY_PREPARATION";

export type PhaseValue = PhaseId | "UNKNOWN";

export type ReportId =
  | "proposal"
  | "candidate"
  | "calabash"
  | "simulation"
  | "workflow"
  | "ui"
  | "baseline"
  | "loop_governance";

export type StepId =
  | "PROPOSAL_READINESS"
  | "PROJECT_INITIALIZATION"
  | "INITIAL_READY"
  | "CALABASH_DRAFT"
  | "SIMULATION_WORLD_FOUNDATION"
  | "WORKFLOW_CAPABILITY_END"
  | "UI_PRODUCT_SURFACE_END"
  | "CALABASH_UPGRADE_READY"
  | "MANDATORY_CALABASH_UPGRADE"
  | "PRODUCT_BASELINE"
  | "FEATURE_SLICE_EXECUTION_COVERAGE"
  | "UI_LOCKED_INTEGRATION_BASELINE"
  | "LOOP_RUN_D0_D3"
  | "LOOP_OWNER_ACCEPTANCE"
  | "ALL_REQUIRED_RUNS_ACCEPTED"
  | "CENTRALIZED_VULNERABILITY_AUDIT"
  | "SECURITY_REMEDIATION"
  | "SECURITY_REAUDIT_VULNERABILITY_CLOSURE"
  | "POST_SECURITY_OWNER_ACCEPTANCE"
  | "DELIVERY_METHOD_QA"
  | "DELIVERY_PACKAGE_GUARD_READY";

export type RowKey =
  | "row.conclusion"
  | "row.initial_gate"
  | "row.identity"
  | "row.integrity"
  | "row.status"
  | "row.version_record"
  | "row.current_phase"
  | "row.realized_peer_subtrees"
  | "row.realized_subtrees"
  | "row.component_version_coverage"
  | "row.primary_mainline"
  | "row.core_implementation"
  | "row.extra_implemented"
  | "row.extra_deferred"
  | "row.api_coverage"
  | "row.mcp_coverage"
  | "row.lock_status"
  | "row.git_identity"
  | "row.locked_subtree_coverage"
  | "row.map_handoff_consistency"
  | "row.owner_confirmed_mainline"
  | "row.worker_checker_wake"
  | "row.supervisor_wait"
  | "row.heartbeat"
  | "row.no_subagents"
  | "row.progress"
  | "row.cell_capacity"
  | "row.pin_policy";

export type LockValue = "LOCKED" | "PENDING" | "UNKNOWN";
export type RecordValue = "RECORDED" | "PRESENT" | "PENDING" | "NOT_RECORDED" | "UNKNOWN";
export type MetricStatus = "COMPLIANT" | "ACTIVE" | "VIOLATION" | "UNKNOWN" | "NOT_RECORDED";

export type MetricValue = Readonly<{
  kind: "metric";
  status: MetricStatus;
  completed: number | null;
  total: number | null;
  interval_minutes: 10 | 15 | 30 | null;
}>;

export type RowValue =
  | Readonly<{ kind: "view_state"; value: ViewState }>
  | Readonly<{ kind: "phase"; value: PhaseValue }>
  | Readonly<{ kind: "lock"; value: LockValue }>
  | Readonly<{ kind: "record"; value: RecordValue }>
  | MetricValue;

export type ReportRow = Readonly<{ key: RowKey; value: RowValue }>;

export type ReportView = Readonly<{
  id: ReportId;
  state: ViewState;
  version: string | null;
  rows: readonly ReportRow[];
}>;

export type StepView = Readonly<{
  id: StepId;
  state: ViewState;
  report: ReportId | null;
}>;

export type PhaseView = Readonly<{
  id: PhaseId;
  state: ViewState;
  steps: readonly StepView[];
}>;

export type Snapshot = Readonly<{
  schema: "LCCoding 2.5.2 derived BI";
  authoritative: false;
  read_only: true;
  health: Health;
  project: string;
  current_phase: PhaseValue;
  phases: readonly [PhaseView, PhaseView, PhaseView, PhaseView];
  reports: Readonly<{
    proposal: ReportView;
    candidate: ReportView;
    calabash: ReportView;
    simulation: ReportView;
    workflow: ReportView;
    ui: ReportView;
    baseline: ReportView;
    loop_governance: ReportView;
  }>;
}>;

const VIEW_STATES = ["done", "active", "pending", "error"] as const;
const PHASE_VALUES = [
  "INITIAL",
  "PRODUCT_FORMATION",
  "ENGINEERING_RUNS",
  "DELIVERY_PREPARATION",
  "UNKNOWN",
] as const;
const LOCK_VALUES = ["LOCKED", "PENDING", "UNKNOWN"] as const;
const RECORD_VALUES = ["RECORDED", "PRESENT", "PENDING", "NOT_RECORDED", "UNKNOWN"] as const;
const METRIC_STATUSES = ["COMPLIANT", "ACTIVE", "VIOLATION", "UNKNOWN", "NOT_RECORDED"] as const;
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

type StepLayout = readonly [id: StepId, report: ReportId | null];
type PhaseLayout = Readonly<{ id: PhaseId; steps: readonly StepLayout[] }>;

const PHASE_LAYOUT: readonly PhaseLayout[] = [
  {
    id: "INITIAL",
    steps: [
      ["PROPOSAL_READINESS", "proposal"],
      ["PROJECT_INITIALIZATION", "candidate"],
      ["INITIAL_READY", null],
    ],
  },
  {
    id: "PRODUCT_FORMATION",
    steps: [
      ["CALABASH_DRAFT", "calabash"],
      ["SIMULATION_WORLD_FOUNDATION", "simulation"],
      ["WORKFLOW_CAPABILITY_END", "workflow"],
      ["UI_PRODUCT_SURFACE_END", "ui"],
      ["CALABASH_UPGRADE_READY", null],
    ],
  },
  {
    id: "ENGINEERING_RUNS",
    steps: [
      ["MANDATORY_CALABASH_UPGRADE", null],
      ["PRODUCT_BASELINE", "baseline"],
      ["FEATURE_SLICE_EXECUTION_COVERAGE", null],
      ["UI_LOCKED_INTEGRATION_BASELINE", null],
      ["LOOP_RUN_D0_D3", "loop_governance"],
      ["LOOP_OWNER_ACCEPTANCE", null],
      ["ALL_REQUIRED_RUNS_ACCEPTED", null],
    ],
  },
  {
    id: "DELIVERY_PREPARATION",
    steps: [
      ["CENTRALIZED_VULNERABILITY_AUDIT", null],
      ["SECURITY_REMEDIATION", null],
      ["SECURITY_REAUDIT_VULNERABILITY_CLOSURE", null],
      ["POST_SECURITY_OWNER_ACCEPTANCE", null],
      ["DELIVERY_METHOD_QA", null],
      ["DELIVERY_PACKAGE_GUARD_READY", null],
    ],
  },
] as const;

type RowKind = RowValue["kind"];
type RowLayout = readonly [key: RowKey, kind: RowKind];

const REPORT_ROWS: Readonly<Record<ReportId, readonly RowLayout[]>> = {
  proposal: [
    ["row.conclusion", "view_state"],
    ["row.initial_gate", "view_state"],
  ],
  candidate: [
    ["row.identity", "lock"],
    ["row.integrity", "record"],
  ],
  calabash: [
    ["row.status", "view_state"],
    ["row.version_record", "record"],
  ],
  simulation: [
    ["row.realized_peer_subtrees", "metric"],
    ["row.component_version_coverage", "metric"],
    ["row.primary_mainline", "metric"],
  ],
  workflow: [
    ["row.core_implementation", "metric"],
    ["row.extra_implemented", "metric"],
    ["row.extra_deferred", "metric"],
    ["row.api_coverage", "metric"],
    ["row.mcp_coverage", "metric"],
    ["row.component_version_coverage", "metric"],
    ["row.primary_mainline", "metric"],
  ],
  ui: [
    ["row.realized_subtrees", "metric"],
    ["row.component_version_coverage", "metric"],
    ["row.lock_status", "metric"],
    ["row.primary_mainline", "metric"],
  ],
  baseline: [
    ["row.git_identity", "metric"],
    ["row.locked_subtree_coverage", "metric"],
    ["row.map_handoff_consistency", "metric"],
    ["row.owner_confirmed_mainline", "metric"],
  ],
  loop_governance: [
    ["row.worker_checker_wake", "metric"],
    ["row.supervisor_wait", "metric"],
    ["row.heartbeat", "metric"],
    ["row.no_subagents", "metric"],
    ["row.progress", "metric"],
    ["row.cell_capacity", "metric"],
    ["row.pin_policy", "metric"],
  ],
};

const SNAPSHOT_KEYS = [
  "schema",
  "authoritative",
  "read_only",
  "health",
  "project",
  "current_phase",
  "phases",
  "reports",
] as const;

const SAFE_VERSION = /^[A-Za-z0-9][A-Za-z0-9._+-]{0,31}$/u;
const SAFE_PROJECT = /^[\p{L}\p{N}](?:[\p{L}\p{N} _().\[\]—-]{0,78}[\p{L}\p{N}])?$/u;

type InputObject = Record<string, unknown>;

function invalid(): never {
  throw new TypeError("Invalid Snapshot");
}

function exactObject(value: unknown, keys: readonly string[]): InputObject {
  if (value === null || typeof value !== "object" || Array.isArray(value)) invalid();
  const prototype = Object.getPrototypeOf(value);
  if (prototype !== Object.prototype && prototype !== null) invalid();

  const ownKeys = Reflect.ownKeys(value);
  if (ownKeys.length !== keys.length || ownKeys.some((key) => typeof key !== "string")) invalid();
  if (keys.some((key) => !Object.prototype.hasOwnProperty.call(value, key))) invalid();
  for (const key of ownKeys) {
    const descriptor = Object.getOwnPropertyDescriptor(value, key);
    if (descriptor === undefined || !descriptor.enumerable || !("value" in descriptor)) invalid();
  }
  return value as InputObject;
}

function exactArray(value: unknown, length: number): unknown[] {
  if (
    !Array.isArray(value) ||
    Object.getPrototypeOf(value) !== Array.prototype ||
    value.length !== length
  ) {
    invalid();
  }
  if (Reflect.ownKeys(value).length !== length + 1) invalid();
  for (let index = 0; index < length; index += 1) {
    const descriptor = Object.getOwnPropertyDescriptor(value, String(index));
    if (descriptor === undefined || !descriptor.enumerable || !("value" in descriptor)) invalid();
  }
  return value;
}

function exactLiteral<T extends boolean | string | null>(value: unknown, expected: T): T {
  if (value !== expected) invalid();
  return expected;
}

function exactEnum<T extends string>(value: unknown, values: readonly T[]): T {
  if (typeof value !== "string" || !values.includes(value as T)) invalid();
  return value as T;
}

function safeProject(value: unknown): string {
  if (typeof value !== "string" || Array.from(value).length > 80 || !SAFE_PROJECT.test(value)) invalid();
  return value;
}

function safeVersion(value: unknown, nullable: boolean): string | null {
  if (value === null && nullable) return null;
  if (typeof value !== "string" || !SAFE_VERSION.test(value)) invalid();
  return value;
}

function metricCount(value: unknown): number | null {
  if (value === null) return null;
  if (typeof value !== "number" || !Number.isInteger(value) || value < 0 || value > 1_000_000) {
    invalid();
  }
  return value;
}

function metricInterval(value: unknown): 10 | 15 | 30 | null {
  if (value === null || value === 10 || value === 15 || value === 30) return value;
  return invalid();
}

function parseMetric(input: unknown): MetricValue {
  const value = exactObject(input, ["kind", "status", "completed", "total", "interval_minutes"]);
  const status = exactEnum(value.status, METRIC_STATUSES);
  const completed = metricCount(value.completed);
  const total = metricCount(value.total);
  const intervalMinutes = metricInterval(value.interval_minutes);

  if (
    (status === "UNKNOWN" || status === "NOT_RECORDED") &&
    (completed !== null || total !== null || intervalMinutes !== null)
  ) {
    invalid();
  }
  if (total !== null && completed === null) invalid();
  if (completed !== null && total !== null && completed > total) invalid();

  return {
    kind: exactLiteral(value.kind, "metric"),
    status,
    completed,
    total,
    interval_minutes: intervalMinutes,
  };
}

function parseStep(input: unknown, layout: StepLayout): StepView {
  const value = exactObject(input, ["id", "state", "report"]);
  return {
    id: exactLiteral(value.id, layout[0]),
    state: exactEnum(value.state, VIEW_STATES),
    report: layout[1] === null ? exactLiteral(value.report, null) : exactLiteral(value.report, layout[1]),
  };
}

function parsePhase(input: unknown, layout: PhaseLayout): PhaseView {
  const value = exactObject(input, ["id", "state", "steps"]);
  const stepInputs = exactArray(value.steps, layout.steps.length);
  const steps: StepView[] = [];
  for (let index = 0; index < layout.steps.length; index += 1) {
    steps[index] = parseStep(stepInputs[index], layout.steps[index]!);
  }
  return {
    id: exactLiteral(value.id, layout.id),
    state: exactEnum(value.state, VIEW_STATES),
    steps,
  };
}

function parseRowValue(input: unknown, kind: RowKind): RowValue {
  if (kind === "metric") return parseMetric(input);
  const value = exactObject(input, ["kind", "value"]);
  exactLiteral(value.kind, kind);
  switch (kind) {
    case "view_state":
      return { kind, value: exactEnum(value.value, VIEW_STATES) };
    case "phase":
      return { kind, value: exactEnum(value.value, PHASE_VALUES) };
    case "lock":
      return { kind, value: exactEnum(value.value, LOCK_VALUES) };
    case "record":
      return { kind, value: exactEnum(value.value, RECORD_VALUES) };
  }
}

function parseRow(input: unknown, layout: RowLayout): ReportRow {
  const value = exactObject(input, ["key", "value"]);
  const parsedValue = parseRowValue(value.value, layout[1]);
  if (
    parsedValue.kind === "metric" &&
    parsedValue.interval_minutes !== null &&
    layout[0] !== "row.heartbeat"
  ) {
    invalid();
  }
  return {
    key: exactLiteral(value.key, layout[0]),
    value: parsedValue,
  };
}

function parseReport(input: unknown, id: ReportId): ReportView {
  const value = exactObject(input, ["id", "state", "version", "rows"]);
  const rowLayout = REPORT_ROWS[id];
  const rowInputs = exactArray(value.rows, rowLayout.length);
  const rows: ReportRow[] = [];
  for (let index = 0; index < rowLayout.length; index += 1) {
    rows[index] = parseRow(rowInputs[index], rowLayout[index]!);
  }
  const mayHaveVersion = id === "candidate" || id === "calabash";
  return {
    id: exactLiteral(value.id, id),
    state: exactEnum(value.state, VIEW_STATES),
    version: mayHaveVersion ? safeVersion(value.version, true) : exactLiteral(value.version, null),
    rows,
  };
}

function deepFreeze<T>(value: T): T {
  if (value !== null && typeof value === "object") {
    for (const child of Object.values(value)) deepFreeze(child);
    Object.freeze(value);
  }
  return value;
}

export function parseSnapshot(input: unknown): Readonly<Snapshot> {
  const value = exactObject(input, SNAPSHOT_KEYS);
  const phasesInput = exactArray(value.phases, PHASE_LAYOUT.length);
  const phases: PhaseView[] = [];
  for (let index = 0; index < PHASE_LAYOUT.length; index += 1) {
    phases[index] = parsePhase(phasesInput[index], PHASE_LAYOUT[index]!);
  }

  const reportsInput = exactObject(value.reports, REPORT_IDS);
  if (Object.keys(reportsInput).some((key, index) => key !== REPORT_IDS[index])) invalid();
  const reports = {
    proposal: parseReport(reportsInput.proposal, "proposal"),
    candidate: parseReport(reportsInput.candidate, "candidate"),
    calabash: parseReport(reportsInput.calabash, "calabash"),
    simulation: parseReport(reportsInput.simulation, "simulation"),
    workflow: parseReport(reportsInput.workflow, "workflow"),
    ui: parseReport(reportsInput.ui, "ui"),
    baseline: parseReport(reportsInput.baseline, "baseline"),
    loop_governance: parseReport(reportsInput.loop_governance, "loop_governance"),
  };

  for (const phase of phases) {
    for (const step of phase.steps) {
      if (step.report !== null && reports[step.report].state !== step.state) invalid();
    }
  }

  const snapshot = {
    schema: exactLiteral(value.schema, "LCCoding 2.5.2 derived BI"),
    authoritative: exactLiteral(value.authoritative, false),
    read_only: exactLiteral(value.read_only, true),
    health: exactEnum(value.health, ["ok", "error"] as const),
    project: safeProject(value.project),
    current_phase: exactEnum(value.current_phase, PHASE_VALUES),
    phases,
    reports,
  } as unknown as Snapshot;

  return deepFreeze(snapshot);
}
