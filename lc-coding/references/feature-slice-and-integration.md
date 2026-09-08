# Feature Slice and Real Product Integration

This page connects Real Product Integration clauses; `SPEC.md` alone is semantic authority.

<a id="slice-and-proving-path"></a>
## Slice and proving path

Source clauses: [LC-INTEG-001](../../SPEC.md#lc-integ-001)

A Feature Slice is the canonical product claim for one increment. Start from the Owner-confirmed Primary product mainline unless Impact Analysis selects another governed route. Inherit already verified CORE and implemented EXTRA Workflow capabilities wherever possible; enabling work becomes product progress only when the Slice consumes it.

Execution Coverage Preflight covers the product chain—Baseline, Workflow/UI/Simulation, state/data/permissions, exceptions/recovery, Impact Analysis, Integration Baseline, Required Runs, D0–D3, and Owner Acceptance—without defining GO, CELL, retries, or other Loop internals. `HIGH`/`UNKNOWN` requires deeper evidence or a smaller Run. If wiring is unproved, first run the thinnest production-quality E2E path and halt expansion on failure.

For a `3.0.0` project, real integration retains the exact direct-product path through a real UI, integration boundary, real API/MCP-backed Workflow capability, real state/data/side effect, and visible UI result. Static images, mocks, stubs, simulation-only output, or manually staged state are demonstrations and cannot prove third-phase integration.

For a `4.0.0` project, each required service route has its own route-bound Slice. It proves one ordered real chain: promised real entry → authenticated actor and valid authority → applicable product surface or route adapter → the adopted shared Workflow capability → authoritative state/data/side effect → route result → human-observable business outcome. A Direct Product PASS cannot prove a Personal Agent or Service Center route, and one route's evidence cannot be relabeled for another. API or MCP presence alone, Simulation output, mocks, stubs, manually staged state, and an Agent log without the final human-observable outcome are not real integration evidence.

The Slice, Integration Baseline, and Final Feature Verification repeat the exact Service Route Map ID/hash, route identity, candidate identity, actor/authority, adapter or surface, shared capability, and outcome identity. Workflow, surface, Simulation, and Product Baseline rows supply the authoritative expected route joins, but none is execution evidence. Each route-chain evidence field uses the existing stable evidence ID / exact SHA-256 / contained-path citation and resolves to the canonical candidate-bound `LOOP_OWNER_ACCEPTANCE_RECEIPT` named by that route's acceptance evidence and indexed by authoritative status. Its exact Run-start hash and route/Slice/Integration-Baseline binding, expected Scenario IDs, ordered route IDs, D3 state/effect verification, and human outcome bind the actual invocation and result back to the authoritative tables. Simulation output remains only an expected scenario; an API/MCP/contract name, generic operations log, missing bytes, stale hash, or mismatched record identity cannot close the chain or prove the human outcome. The accepted integration candidate must equal the Slice's Integration candidate ID/hash, and each 4.0 Run-start route/Baseline pair must equal the Slice's Service Route and accepted Integration Baseline. Personal Agent and Service Center routes retain attributable delegation; Service Center evidence retains adopted audit lineage. D0–D3 and Owner Acceptance semantics do not change. Locked UI contact is derived from the route's realized service surfaces: when an applicable UI surface exists, the existing one-way UI lock and Baseline Change Request path remain mandatory; a route without such a surface does not invent UI identity.

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
