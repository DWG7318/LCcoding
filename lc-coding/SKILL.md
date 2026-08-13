---
name: lc-coding
description: Use when an Owner wants AI to develop or admit an enterprise product through four lifecycle phases and bounded cross-phase execution methods.
---

# LCCoding 2.7.0

## Canonical mainline

Source clauses: [LC-PHASE-001](../SPEC.md#lc-phase-001), [LC-PHASE-002](../SPEC.md#lc-phase-002), [LC-PHASE-003](../SPEC.md#lc-phase-003), [LC-PHASE-004](../SPEC.md#lc-phase-004)

```text
Owner Proposal
→ Proposal Readiness Check
→ Project Initialization
→ Calabash Draft
→ [Simulation World foundation first → Workflow capability end ∥ UI product-surface end]
→ Mandatory Calabash Upgrade
→ Product Baseline
→ Feature Slice
→ UI-locked Real Product Integration
→ Independent layered Verification
→ Owner Acceptance
→ Delivery
```

Operational meaning:

The lifecycle axis identifies the product condition of each phase. The execution-method axis organizes bounded work in any LCCoding phase. The four phases are `INITIAL`, `PRODUCT_FORMATION`, the Real Product Integration phase (compatibility ID `ENGINEERING_RUNS`), and `DELIVERY_PREPARATION`.

## Principle Zero and Owner authority

Source clauses: [LC-AUTH-001](../SPEC.md#lc-auth-001), [LC-AUTH-002](../SPEC.md#lc-auth-002)

Owner decides product meaning. AI completes routine engineering autonomously inside frozen boundaries. The Owner retains final authority over baselines/UI changes, continuation, acceptance, release, and Delivery; `SPEC.md` remains the complete semantic authority.

## Start, stop, and route

Source clauses: [LC-AUTH-001](../SPEC.md#lc-auth-001), [LC-PHASE-001](../SPEC.md#lc-phase-001), [LC-INTEG-003](../SPEC.md#lc-integ-003)

1. Load [SPEC](../SPEC.md), Owner/project rules, the applicable contract/template, and current evidence.
2. Identify the calling phase and bounded objective; use [Proposal Readiness](references/proposal-readiness.md) and [Project Initialization](references/project-initialization.md) for entry work.
3. `STOP` on `HOLD`, `TERMINATE`, contradiction, or a failed authoritative boundary; preserve evidence before changing course.
4. Then route `NARROW_REDIRECT`, meaning change, rework, or invalidation through the calling phase and its cited focused reference.
5. Only resume inside the accepted authority and current evidence boundary.

## Product Formation operator summary

Source clauses: [LC-FORM-001](../SPEC.md#lc-form-001), [LC-FORM-002](../SPEC.md#lc-form-002), [LC-FORM-003](../SPEC.md#lc-form-003)

Build at least one minimal, real, runnable, versioned Simulation World foundation before actual Workflow or UI construction. Never treat the foundation as a complete or frozen Simulation. Then advance Workflow and UI as equal product ends, independently; they may proceed in parallel, and each forms a real, runnable, inspectable result. Do not require early Workflow-to-UI connection or three-way joint integration. Continue semantic and scenario synchronization without treating it as early integration. Keep cross-layer connection and end-to-end proof in Feature Slice and UI-locked Integration.

Use Calabash and available Simulation Worlds to split Workflow into enough business lines and produce real, runnable business functions; plans or simulation-only results cannot replace real Workflow while formation continues until Mandatory Calabash Upgrade is complete. Mark each Workflow business line `CORE` or `EXTRA`. CORE means Calabash and Owner confirmation make the business line required product capability. EXTRA comes from Calabash extension space, external research, or comparable-product analysis. Do not claim unimplemented EXTRA as product capability. Never reclassify CORE as EXTRA to pass Product Baseline.

The Product Baseline gate applies only to CORE Workflow. Freeze Product Baseline only after every CORE business line is real, runnable, and proved feasible. If a CORE is proved infeasible under current product constraints, adjust Calabash, narrow, hold, or terminate; EXTRA does not block Product Baseline. Details: [LC-FORM-003](../SPEC.md#lc-form-003).

## Real Product Integration operator summary

Source clauses: [LC-INTEG-001](../SPEC.md#lc-integ-001), [LC-INTEG-002](../SPEC.md#lc-integ-002), [LC-INTEG-003](../SPEC.md#lc-integ-003)

Feature Slice considers all already implemented and verified Workflow capabilities across CORE and EXTRA; identify already implemented and verified Workflow capabilities and inherit and reuse them wherever possible. It may supplement, adjust, or improve Workflow under Impact Analysis and `CONTROLLED_MUTABLE` rules.

Pin the applicable UI subtree to the one total project repository and total-project exact commit; never use a branch, tag, `HEAD`, worktree, or `latest` as the lock. The lock is one-way Owner authority: system actors must not autonomously modify a locked UI.

Each Slice proves a real UI operation through a real API/MCP-backed Workflow to state/data/side effects and a visible result. Static UI, mock, stub, or manually staged state is demonstration evidence, not integration proof. Details: [Feature Slice and integration](references/feature-slice-and-integration.md).

## Cross-phase execution axis

Source clauses: [LC-RUN-001](../SPEC.md#lc-run-001), [LC-RUN-002](../SPEC.md#lc-run-002), [LC-RUN-003](../SPEC.md#lc-run-003), [LC-COMPAT-002](../SPEC.md#lc-compat-002)

SLK, CLK, GLK, and other registered methods may run in any LCCoding phase. This cross-phase execution axis is not a lifecycle node and is not an exhaustive method list. One Run selects one compatible method and returns evidence to its calling phase. Completing or accepting a Run does not advance a phase. See [method selection](references/loop-method-selection.md) and [shared Loop Control](references/loop-control-contract.md).

## Verification and acceptance entry

Source clauses: [LC-VERIFY-001](../SPEC.md#lc-verify-001), [LC-ACCEPT-001](../SPEC.md#lc-accept-001), [LC-ACCEPT-002](../SPEC.md#lc-accept-002), [LC-ACCEPT-003](../SPEC.md#lc-accept-003)

D0–D3 use independent evidence and reuse unaffected proof. Every normal SLK/CLK/GLK Run must end in its own Loop Owner Acceptance; Post-Security Owner Acceptance remains a distinct final-candidate decision. Use [acceptance boundaries](references/loop-acceptance-boundary.md) and [verification reuse](references/verification-de-duplication.md).

## Security and Delivery entry

Source clauses: [LC-SEC-001](../SPEC.md#lc-sec-001), [LC-SEC-002](../SPEC.md#lc-sec-002), [LC-DELIVERY-001](../SPEC.md#lc-delivery-001)

Centralized independent vulnerability closure and current Post-Security acceptance precede customer-specific Q&A and protected Delivery. Later material change invalidates affected evidence. Use [vulnerability closure](references/vulnerability-closure.md), [Delivery Q&A](references/delivery-method-qa.md), and [delivery governance](references/delivery-governance.md).

## Built-in BI entry

Source clauses: [LC-BI-001](../SPEC.md#lc-bi-001), [LC-BI-002](../SPEC.md#lc-bi-002)

The built-in BI is a read-only projection, not project authority or runtime control. Product, compatibility, implementation, and release navigation begins at [built-in BI](references/built-in-bi.md).

## Version navigation

Source clauses: [LC-COMPAT-001](../SPEC.md#lc-compat-001)

Version and migration rules are defined by the clause and explained in [version governance](references/version-governance.md).
