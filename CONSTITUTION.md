# LCCoding Constitution 2.3.0

## Identity

LCCoding is an Owner-led, AI-executed enterprise product-development method. It governs the path from a sufficiently mature proposal to a protected customer delivery.

LCCoding is an Agent-platform-independent methodology. It defines product governance and evidence boundaries; it does not own runtime, session control, or an Agent execution kernel.

LCCoding may expose a built-in read-only BI projection of its fixed phases, milestones, states, artifacts, and protected subreports. That projection is observational only: it never becomes authoritative project state, reads or mutates no project files without a separately authorized adapter, and controls neither Agent nor runtime behavior. Window-local presentation features such as language and native Pin do not expand method authority.

## Frozen mainline

```text
Owner Proposal
      ↓
Proposal Readiness Check
      ↓
Project Initialization
      ↓
Calabash Draft
      ↓
[Simulation World foundation first → Workflow capability end ∥ UI product-surface end]
      ↓
Mandatory Calabash Upgrade
      ↓
Product Baseline
      ↓
Feature Slice
      ↓
UI-locked Feature Integration
      ↓
SLK / CLK / GLK Loop Engineering
      ↓
Independent layered Verification
      ↓
Owner Acceptance
      ↓
Delivery
```

The bracket is the one existing `WORKFLOW_UI_SIMULATION` node: it states internal formation order, not a new lifecycle node, phase, gate, or readiness verdict.

The mainline is unchanged. Its operational meaning is:

- each normal Loop Run contains its own D0–D3 and Loop Owner Acceptance;
- after all required normal Runs are Owner-accepted, LCCoding performs one centralized independent vulnerability audit and remediation closure;
- the mainline Owner Acceptance is the distinct Post-Security Owner Acceptance of the final remediated candidate;
- Delivery begins only after that acceptance and customer-specific Delivery Method Q&A.

## Existing engineering mode

Project Initialization may admit an existing engineering project without creating a new lifecycle. LCCoding preserves its repository, history, declared version, materials, and valid evidence. A prior completion statement is only `CLAIMED_UNATTESTED` until the current candidate, coverage, authority, and evidence are independently established.

Before engineering resumes, the Owner decides `CONTINUE`, `NARROW_REDIRECT`, `HOLD`, or `TERMINATE`. Runnable UI may anchor Owner understanding but is not completion proof; Workflow, state, data, permissions, failure/recovery, and invisible behavior still require trace and evidence. Takeover remains inside Project Initialization and outputs only `READY`, `BLOCKED`, or `NOT_CONTINUING`. Only real gaps enter the existing Feature Slice and Loop path.

`status.json` is the one authoritative durable project status. Project Health is assessment evidence and `PHASE-STATUS.json` is derived from status. None may contain runtime, session, Agent, queue, retry, model, hook, or orchestration state.

## Fixed mainline, proportional depth

Every mandatory mainline node remains. Analysis, material, and evidence depth is proportional to product uncertainty, system coupling, real risk, irreversibility, and novelty. `UNKNOWN` is recorded without being normalized to low, requires conservative deeper coverage, and blocks a sufficient final depth judgment until assessed. Sufficient evidence is cited and reused. Concise work must remain truthful; high-risk work must deepen coverage. Depth never deletes a node or authorizes an empty artifact.

Before Loop execution, the Feature Slice must pass product-level execution coverage preflight. Unproven cross-layer wiring requires a first thin production-quality proving Run or cited sufficient evidence. LCCoding specifies admission and handoff; the selected Loop owns all internal execution decomposition.

Owner gaps retain one trace from source Acceptance through candidate/scenario, Impact or Calabash route, correction Run, affected D0–D3, delta re-verification, and delta re-acceptance. Open blocking gaps prevent aggregate acceptance.

## Four-phase overlay

```text
PHASE 0 — INITIAL
Owner Proposal → Proposal Readiness Check → Project Initialization
Exit: INITIAL_READY
Boundary: before Calabash Draft

PHASE 1 — PRODUCT_FORMATION
Calabash Draft → [Simulation foundation first → Workflow ∥ UI]
Exit: CALABASH_UPGRADE_READY
Boundary: before Mandatory Calabash Upgrade

PHASE 2 — ENGINEERING_RUNS
Mandatory Calabash Upgrade → Product Baseline → Feature Slice
→ UI-locked Integration → one selected Loop Run → D0–D3
Exit per Run: LOOP_OWNER_ACCEPTANCE_READY
Owner decision: Loop Owner Acceptance
Aggregate exit: ALL_REQUIRED_RUNS_ACCEPTED

PHASE 3 — DELIVERY_PREPARATION
Centralized Vulnerability Audit → Security Remediation → independent Re-audit
→ VULNERABILITY_CLOSED → Post-Security Owner Acceptance
→ customer-specific Delivery Method Q&A → package governance
Exit: DELIVERY_READY
Boundary: before Delivery
```

The phase overlay is navigation and gating only. `ENGINEERING_RUNS` repeats until every required normal Run is Owner-accepted.

## Foundation principles

1. Everything Starts Small.
2. Everything is Governed.
3. Everything is an Artifact.
4. Everything is Traceable.
5. Canonical Before Reasoning.
6. Compatibility Before Execution.
7. Enterprise First.
8. AI Autonomous, Owner Controlled.

## Method laws

- Workflow, UI, and Calabash are three distinct product layers.
- Simulation makes Workflow and UI observable; it does not replace real integration.
- Calabash begins as a Draft and must receive Mandatory Upgrade before Product Baseline.
- Feature Slice is the product-progress unit; GO and CELL are engineering-execution units.
- During integration, UI is the default locked target.
- Select the lightest truthful Loop method: SLK, then CLK, then GLK.
- Worker never accepts its own work.
- Higher Verification layers reuse lower evidence and verify only the new claim or risk.
- Every normal SLK/CLK/GLK Run ends with incremental Loop Owner Acceptance; it must not be replaced by one giant end-of-project acceptance.
- Formal vulnerability assessment is centralized after all required normal Runs are Owner-accepted.
- The Security Auditor must be independent from implementation, checking, Verification, supervision, and prior Owner acceptance preparation.
- The Security Auditor discovers and verifies; separate engineering roles remediate.
- Post-Security Owner Acceptance is distinct from Loop Owner Acceptance and checks only the security-remediation delta plus critical smoke paths.
- Delivery method is confirmed for each customer through Owner Q&A; defaults are recommendations, while Owner-locked exclusions remain mandatory.
- Delivery exposes the product, not the internal LC development system.
- Every addition must reduce internal or external engineering friction.
- Project Fingerprint complexity governs depth; `recommended_loop` governs execution topology only.
- `status.json` is authoritative; Project Health is evidence; Phase Status is derived.
- Feature Slice readiness is decided before execution without importing GO/CELL internals.
- Owner gaps close only on evidenced correction and Owner re-acceptance.
