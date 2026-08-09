# Lifecycle Phases

Four phases make product progress visible. SLK, CLK, GLK, and other execution methods are available across all four phases and are not lifecycle nodes.

## PHASE 0 — INITIAL

**Range:** Owner Proposal through Project Initialization.

**Exit:** `INITIAL_READY` before Calabash Draft.

EXISTING takeover readiness is an INITIAL gate input, not a new phase. `READY` may support `INITIAL_READY`; `BLOCKED` and `NOT_CONTINUING` may not.

## PHASE 1 — PRODUCT FORMATION

**Range:** Calabash Draft through Workflow, UI, and Simulation World.

**Exit:** `CALABASH_UPGRADE_READY` before Mandatory Calabash Upgrade.

Workflow, UI, and Simulation are built as separate runnable product ends. They coordinate through Owner meaning, Calabash, and shared scenarios, but tight connection and integration testing are not yet required.

## PHASE 2 — ENGINEERING RUNS (REAL PRODUCT INTEGRATION)

**Range:** Mandatory Calabash Upgrade through Product Baseline, Feature Slice, and UI-locked Real Product Integration. This phase connects Workflow, UI, and Simulation through real API/MCP-backed capability, real state/data/side effects, visible UI results, and integration/end-to-end proof.

**Per-Run exit:** `LOOP_OWNER_ACCEPTANCE_READY`.

The selected Loop Supervisor immediately facilitates Owner acceptance for that Run. The Owner accepts small completed Runs as they finish.

After Owner decision:

- accepted and more required integration work remains: continue another ENGINEERING_RUNS cycle;
- accepted and all required third-phase integration work is complete: issue the compatibility gate `ALL_REQUIRED_RUNS_ACCEPTED`;
- rework or definition change: route according to the selected Loop and LCCoding impact rules.

## PHASE 3 — DELIVERY PREPARATION

**Range:** immediately after `ALL_REQUIRED_RUNS_ACCEPTED`, through centralized independent vulnerability audit, security remediation, Security Auditor re-audit, `VULNERABILITY_CLOSED`, Post-Security Owner Acceptance, Delivery Method Q&A, and package governance.

**Exit:** `DELIVERY_READY` before Delivery.

## Rules

- A bounded work item in `INITIAL`, `PRODUCT_FORMATION`, `ENGINEERING_RUNS`, or `DELIVERY_PREPARATION` may use a suitable execution method.
- A Run records its phase scope and phase-owned objective. Method completion returns evidence to the calling phase and never auto-advances the phase.
- Loop Owner Acceptance is incremental and belongs to the selected Loop, regardless of phase.
- Post-Security Owner Acceptance is a second, distinct, delta-focused acceptance after security remediation.
- Vulnerability audit is centralized once over the final accepted candidate; it is not distributed as repeated formal audits across D0–D3.
- Phase artifacts reference canonical evidence and do not copy it.
- `status.json` is authoritative; Project Health is assessment evidence; `PHASE-STATUS.json` is derived.
- Feature Slice Execution Coverage Preflight is a Product Integration work admission condition, not a universal precondition for method use in other phases and not an added phase.
- Blocking open Owner gaps prevent `ALL_REQUIRED_RUNS_ACCEPTED`.
