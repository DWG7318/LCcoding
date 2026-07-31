# Changelog

## 2.2.1

### Workflow realization and CORE/EXTRA classification

- Required Workflow business lines become real, runnable product capability during the existing Workflow/UI/Simulation stage; plans, shells, mocks, and simulation-only results do not substitute for implementation.
- One Workflow Map classifies each business line as `CORE` or `EXTRA`; technically difficult or infeasible EXTRA may remain deferred and does not block Product Baseline, but cannot be claimed as existing capability until implemented and verified.
- Product Baseline is blocked until every CORE business line is implemented and proved feasible; AI cannot downgrade CORE to EXTRA without returning the classification to Calabash and Owner confirmation.
- Feature Slice inherits and reuses verified CORE and EXTRA Workflow capabilities and may continue improving Workflow under existing Impact Analysis and `CONTROLLED_MUTABLE` rules.
- Canonical mainline, phases, states, gates, runtime boundaries, and lower-method responsibilities remain unchanged.

## 2.2.0

### Takeover and canonical status

- Added `READY`, `BLOCKED`, and `NOT_CONTINUING` takeover readiness inside EXISTING Project Initialization without adding a phase.
- Made `status.json` the single authoritative durable project status; Project Health remains assessment evidence and `PHASE-STATUS.json` is derived.
- Explicitly excluded runtime, session, Agent, queue, retry, model, hook, and orchestration state.

### Slice admission and Owner gap closure

- Added product-level Feature Slice Execution Coverage Preflight before SLK/CLK/GLK handoff.
- Required deeper evidence or smaller independently verifiable Runs for `HIGH/UNKNOWN` complexity.
- Added a first production-quality proving Run only when cross-layer wiring lacks trustworthy proof.
- Added stable Owner gap lineage through Impact/Calabash routing, correction Run, affected D0–D3, delta re-verification, and Owner re-acceptance.
- Kept Loop internals, runtime state, centralized security, and Delivery boundaries unchanged.

## 2.1.0

### Existing engineering intake

- Added NEW and EXISTING modes inside Project Initialization without changing the mainline.
- Preserved existing repositories, history, versions, materials, and valid evidence instead of resetting or rebuilding by default.
- Bound inherited completion claims to `CLAIMED_UNATTESTED` until current evidence is established.
- Added Owner continuation decisions and UI-anchored, evidence-backed reconstruction through existing project artifacts.

### Proportional depth

- Kept every mandatory mainline node while making analysis, material, and evidence depth proportional to five Project Fingerprint factors.
- Kept `recommended_loop` separate as execution topology only.
- Clarified that sufficient evidence is reused, concise work remains truthful, and high-risk work deepens coverage.
- Preserved template-default `UNKNOWN` as an unresolved state that requires depth assessment and conservative coverage rather than being rejected or treated as all-low.

### Learning return

- Clarified that Product learning may be blank and returns only when it changes future governance.
- Reused one existing canonical artifact; no learning phase, repository, directory, or mandatory document was added.

## 2.0.0

### Preserved

- Calabash / Workflow / UI three-layer product structure.
- Simulation World.
- Mandatory Calabash Upgrade and Product Baseline.
- Feature Slice and UI-locked Integration.
- SLK / CLK / GLK Loop Engineering.
- Independent Verification and Owner Acceptance.
- Protected Delivery.

### Simplified

- One canonical definition per concept.
- Proposal questions are asked only for real gaps.
- Initialization and canonical checks rerun only on change.
- Workflow/UI/Simulation share scenario identifiers.
- One Impact Analysis is updated by delta.
- Feature Slice definition is referenced rather than copied.
- Verification receipts are inherited upward.
- Final Feature Verification tests only new composition risk.
- Owner Acceptance reuses the accepted candidate and scenarios.
- Delivery reuses product Verification and checks only package deltas.

### Added to the complete repository

- Proposal Readiness templates and checker.
- Project bootstrap, capability manifest, Agents Rule, Fingerprint, Health, and Interpretation Lock.
- Full integration-lock and delivery-governance templates.
- Verification receipt contract and anti-duplication validator.
- Repository and project validation scripts.
- Enterprise example and GitHub Actions validation.

### Final phase and closure refinement

- Added a four-phase overlay without changing the mainline.
- Unified human product acceptance at LCCoding Owner Acceptance; Loop methods now hand off rather than duplicate acceptance.
- Added non-duplicative Vulnerability Detection and Closure before Owner Acceptance.
- Added mandatory customer-specific Delivery Method Q&A; defaults are recommendations rather than silent delivery choices.
- Added phase, vulnerability, delivery-decision contracts, templates, guards, and tests.
### Acceptance and security boundary correction

- Restored incremental Owner Acceptance inside every normal SLK/CLK/GLK Run.
- Removed the incorrect single late aggregate acceptance model.
- Moved formal vulnerability audit after all normal Loop Owner Acceptances.
- Required one fresh independent Security Auditor Agent.
- Separated audit from remediation implementation.
- Added Post-Security Owner Acceptance as a focused delta acceptance before Delivery.
