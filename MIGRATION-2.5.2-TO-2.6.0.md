# Migration 2.5.2 → 2.6.0

## Purpose

LCCoding 2.6.0 separates the product lifecycle from engineering execution methods. SLK, CLK, and GLK are no longer a fixed mainline node or a Phase-3-only handoff. They and other registered methods may guide bounded work in any phase.

## Canonical change

The mainline changes from:

```text
Feature Slice → UI-locked Integration → SLK / CLK / GLK → Verification
```

to:

```text
Feature Slice → UI-locked Real Product Integration → Verification
```

Execution methods form a separate horizontal axis. One Run selects one method; separate Runs may select different methods. SLK, CLK, and GLK are important registered methods, not an exhaustive list.

## Phase meaning

- `INITIAL`: proposal readiness, project identity, continuity, and initialization.
- `PRODUCT_FORMATION`: Workflow, UI, and Simulation are separately built into runnable product ends with semantic/scenario coordination.
- `ENGINEERING_RUNS`: stable compatibility ID for real Product Integration. Workflow, UI, and Simulation are tightly connected and proved through real API/MCP-backed capability, state/data/side effects, visible UI results, and integration/end-to-end testing.
- `DELIVERY_PREPARATION`: security closure, post-security Owner acceptance, delivery decisions, and package governance.

`ALL_REQUIRED_RUNS_ACCEPTED` remains a compatibility gate whose scope is the required Phase-3 integration work. It does not aggregate every method invocation in all four phases.

## Run migration

For every new Run, record:

1. LCCoding phase scope;
2. phase-owned objective;
3. calling phase authority/contract;
4. selected execution method;
5. evidence return target;
6. phase gate evaluation as a separate calling-phase decision.

Product Baseline, Feature Slice, and Integration Baseline are required inputs only when the work is Product Integration and those contracts apply. Earlier or later phases supply their own frozen authority and inputs.

Historical 2.5.2 Runs and receipts remain valid evidence under their original contracts. Do not rewrite them. New or materially revised Runs use the 2.6.0 cross-phase contract.

## BI compatibility

The machine phase ID `ENGINEERING_RUNS`, compatibility step ID `LOOP_RUN_D0_D3`, and existing status fields remain stable. The BI displays Product Integration and Execution Method Governance. It remains a read-only lifecycle projection and does not become an execution-method scheduler.

## Method repositories

This LCCoding release does not change SLK, CLK, or GLK internal topology. Their own repositories should separately update only trigger/input wording that incorrectly assumes every invocation begins after Product Baseline or belongs exclusively to Phase 3.
