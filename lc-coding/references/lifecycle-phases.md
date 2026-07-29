# Lifecycle Phases

The LCCoding mainline remains unchanged. Four phases make progress visible without moving Loop Owner Acceptance out of SLK, CLK, or GLK.

## PHASE 0 — INITIAL

**Range:** Owner Proposal through Project Initialization.

**Exit:** `INITIAL_READY` before Calabash Draft.

## PHASE 1 — PRODUCT FORMATION

**Range:** Calabash Draft through Workflow, UI, and Simulation World.

**Exit:** `CALABASH_UPGRADE_READY` before Mandatory Calabash Upgrade.

## PHASE 2 — ENGINEERING RUNS

**Range:** Mandatory Calabash Upgrade through Product Baseline, Feature Slice, UI-locked Integration, and one normal SLK/CLK/GLK Run through D3.

**Per-Run exit:** `LOOP_OWNER_ACCEPTANCE_READY`.

The selected Loop Supervisor immediately facilitates Owner acceptance for that Run. The Owner accepts small completed Runs as they finish.

After Owner decision:

- accepted and more Runs remain: continue another ENGINEERING_RUNS cycle;
- accepted and all required Runs are complete: issue `ALL_REQUIRED_RUNS_ACCEPTED`;
- rework or definition change: route according to the selected Loop and LCCoding impact rules.

## PHASE 3 — DELIVERY PREPARATION

**Range:** immediately after `ALL_REQUIRED_RUNS_ACCEPTED`, through centralized independent vulnerability audit, security remediation, Security Auditor re-audit, `VULNERABILITY_CLOSED`, Post-Security Owner Acceptance, Delivery Method Q&A, and package governance.

**Exit:** `DELIVERY_READY` before Delivery.

## Rules

- Loop Owner Acceptance is incremental and belongs to SLK/CLK/GLK.
- Post-Security Owner Acceptance is a second, distinct, delta-focused acceptance after security remediation.
- Vulnerability audit is centralized once over the final accepted candidate; it is not distributed as repeated formal audits across D0–D3.
- Phase artifacts reference canonical evidence and do not copy it.
