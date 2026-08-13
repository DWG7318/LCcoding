# Feature Slice and Real Product Integration

This page connects Real Product Integration clauses; `SPEC.md` alone is semantic authority.

<a id="slice-and-proving-path"></a>
## Slice and proving path

Source clauses: [LC-INTEG-001](../../SPEC.md#lc-integ-001)

A Feature Slice is the canonical product claim for one increment. Start from the Owner-confirmed Primary product mainline unless Impact Analysis selects another governed route. Inherit already verified CORE and implemented EXTRA Workflow capabilities wherever possible; enabling work becomes product progress only when the Slice consumes it.

Execution Coverage Preflight covers the product chain—Baseline, Workflow/UI/Simulation, state/data/permissions, exceptions/recovery, Impact Analysis, Integration Baseline, Required Runs, D0–D3, and Owner Acceptance—without defining GO, CELL, retries, or other Loop internals. `HIGH`/`UNKNOWN` requires deeper evidence or a smaller Run. If wiring is unproved, first run the thinnest production-quality E2E path and halt expansion on failure.

Real integration follows actor intent through a real UI, integration boundary, real API/MCP-backed Workflow capability, real state/data/side effect, and visible UI result. Static images, mocks, stubs, simulation-only output, or manually staged state are demonstrations and cannot prove third-phase integration.

<a id="one-way-ui-lock-and-recoverable-identity"></a>
## One-way UI lock and recoverable identity

Source clauses: [LC-INTEG-002](../../SPEC.md#lc-integ-002)

The lock is one-way system restraint, not a limit on Owner authority. The applicable UI logical subtree keeps complete recoverable source inside the one total project repository; logical subtree means a product path, not an external Git import. Product and Integration Baselines agree on total-project repository/exact commit plus UI ID/path/component version/content hash. A branch, tag, `HEAD`, worktree, screenshot, export, build, or `latest` cannot substitute. The mechanical identities remain in `PRODUCT-BASELINE-HANDOFF.md` and `INTEGRATION-BASELINE.md`.

Compare current UI to the lock before a Slice/Run and before acceptance. An unauthorized delta blocks work or acceptance and is preserved and isolated; never silently overwrite or automatically restore Owner material.

An Owner-initiated or Owner-approved change uses the existing Baseline Change Request. Record necessity and authority, create a distinct project commit and UI version/hash, synchronize both baselines, and re-verify affected evidence. This route adds no approval layer beyond Owner authority.

<a id="impact-mutability-evidence-and-learning"></a>
## Impact, mutability, evidence, and learning

Source clauses: [LC-INTEG-003](../../SPEC.md#lc-integ-003)

Keep one Impact Analysis and update it by delta; redo it only when scope, baseline, or architecture materially changes. Change only affected connected layers and evidence, not every UI/Workflow/Simulation surface mechanically.

The integration lock remains `UI = LOCKED`, `Workflow = CONTROLLED_MUTABLE`, `Simulation = VERSIONED_MUTABLE`, and `Calabash = LIVING_WITH_IMPACT_TRACE`. Reuse evidence only when candidate/artifact identity, contract version, relevant environment, authority, currency/completeness, and lack of contradiction still match; otherwise re-check the affected risk and record source, reason, scope difference, and result.

Product learning may be blank. Return it only when it changes a future decision, constraint, check, template, or reuse rule, and update one existing canonical artifact rather than creating a learning system.
