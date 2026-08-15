# Changelog

## Unreleased - 2.8.0 candidate

- Added a copy-on-write 2.7-to-2.8 project migration that preserves prior evidence as historical and leaves all new Agent-native conditions explicitly unproved. The current repository and BI release carriers are prepared for 2.8.0; this remains an unreleased candidate, not a release, no formal tag or GitHub Release exists yet, and global installed Skill deployment remains a separate post-release action.

## 2.7.0

- The copy-on-write migration is defined, and the current repository and BI release carriers are finalized for 2.7.0; global installed Skill deployment remains a separate post-release action, performed only after the formal release is independently accepted.

## 2.6.0

### Cross-phase execution methods and real Product Integration

- Removed SLK/CLK/GLK from the canonical mainline as a fixed lifecycle node.
- Defined lifecycle and execution as orthogonal axes: any bounded work item in any of the four phases may select SLK, CLK, GLK, or another registered method, while one Run still uses one execution topology.
- Reaffirmed Phase 3 as real Product Integration: Workflow, UI, and Simulation are built separately in Product Formation, then tightly connected through real API/MCP-backed capability, real state/data/side effects, visible UI results, and integration/end-to-end proof.
- Added phase scope, phase-owned objective, phase authority, and evidence-return fields to existing Run/Loop Owner Acceptance carriers. Method completion never advances a phase by itself.
- Kept `ENGINEERING_RUNS` and `ALL_REQUIRED_RUNS_ACCEPTED` as compatibility identifiers, scoped to required Phase-3 integration work rather than all method invocations across the project.
- Updated the read-only BI display to show Product Integration and Execution Method Governance without adding a phase, control action, runtime state, or independent BI version.

## 2.5.2

### Owner-controlled UI lock and real third-phase integration

- Clarified that `UI=LOCKED` is one-way Owner authority: an Owner may initiate or explicitly approve a controlled UI change, while Workflow, Simulation, integration code, loops, agents, runtime, and automation must never autonomously modify, silently overwrite, or automatically restore locked UI material.
- Required every Engineering-Run Feature Slice to prove a real UI operation through an API/MCP-backed Workflow capability to real state, data, or side effect and back to a visible UI result. Static UI, mocks, stubs, and manually staged state remain Product Formation evidence only and cannot prove third-phase integration, delivery readiness, or D0–D3 acceptance.
- Documented LCCoding's personal origin, adaptable use by other practitioners, welcome discussion and contributions, and the Owner-maintained canonical mainline.
- Preserved the four phases, existing Baseline Change Request route, UI/Workflow/Simulation topology, BI read-only boundary, Loop ownership, and no independent BI version.

## 2.5.1

### GitHub-safe BI installer identity

- Changed only the distributed installer basename to `LCCoding-BI_2.5.1_x64-setup.exe`, which GitHub preserves without normalization.
- Required the downloaded installer basename, `provenance.asset`, `installer.sha256` basename, and workflow upload path to match exactly and reject unsafe characters.
- Preserved the Tauri product name, React/Rust behavior, 300×480 UI, project read-only boundary, and published SLK 2.5.0, CLK 2.5.0, and GLK 3.1.0 identities.

## 2.5.0

### One-click built-in BI

- Replaced the former Vanilla runtime with one React + Vite frontend inside the existing Tauri 2 desktop shell while preserving the accepted 300×480 window, four phases, 21 steps, eight protected reports, bilingual controls, Pin, Refresh, Open/Back, and visual tokens.
- Added one immutable Rust project binding shared by `lccoding-bi.exe --project <root>` and the native Folder Picker, plus a no-argument `get_snapshot` command after binding.
- Added a bounded, no-follow, read-only `gix` projection pipeline for canonical status, Manifest, UI/Workflow/Simulation Maps, Product Baseline Handoff, and the published SLK/CLK/GLK governance contracts; missing evidence remains `UNKNOWN` or `NOT_RECORDED`.
- Added Rust- and frontend-side single-flight refresh, strict allowlisted Snapshots, path-free failure states, project immutability coverage, and production-graph guards that exclude fixtures and the retired Vanilla runtime.
- Added a current-user NSIS installer with embedded WebView2 bootstrapper, the installed `lccoding-bi.exe` command on the user PATH, SHA-256/provenance generation, and install/run/uninstall smoke coverage.
- Kept `status.json` as the only authoritative project status and added no lifecycle node, Gate, runtime control, project write, original-file opening, remote service, or independent BI version/release.
- Release remains blocked until SLK 2.5.0, CLK 2.5.0, and GLK 3.1.0 are each formally locked on their canonical main/tag/GitHub Release; candidate identities are development inputs only.

## 2.4.1

### Built-in BI subtree and Loop-governance reports

- Kept the accepted 300×480 four-phase BI, lifecycle steps, visual tokens, language/Pin/Refresh behavior, and two-command read-only Tauri boundary unchanged.
- Added protected Open reports to the existing Product Baseline and Loop Run · D0–D3 steps without adding a phase, step, Gate, status field, or control capability.
- Adapted Simulation, Workflow, and UI reports to strict plural-subtree, CORE/EXTRA, API/MCP, component-version, lock, and Primary-mainline summary metrics; absent evidence remains `UNKNOWN` or `NOT_RECORDED`.
- Added the seven-item Loop Governance summary as a sanitized read-only compatibility contract. It does not copy SLK/CLK/GLK internals or perform wake, wait, Heartbeat, archive, subagent, progress, CELL-sizing, or pin actions.
- Kept the desktop on its synthetic sanitized Snapshot. Real Maps/Handoff and Loop-artifact integration remains unimplemented rather than introducing a broad parser, second runtime, or unsafe project-data command.

## 2.4.0

### Logical product subtree governance

- Kept one canonical mainline while allowing multiple UI, Workflow, and peer Simulation logical subtrees inside one total project Git/GitHub repository.
- Required every CORE Workflow and every implemented EXTRA Workflow to expose both API and MCP contracts backed by the same capability, without a Workflow Core layer, mandatory microservice, runtime, or deployment topology.
- Added one Owner-confirmed Primary product mainline across at least one Simulation, one CORE Workflow, and one UI to prioritize proving and integration without relaxing any other CORE obligation.
- Product Baseline now freezes the total-project exact commit plus each realized subtree name/path/component version/content hash and their ID relations. `UI=LOCKED` pins the applicable UI subtree to that identity.
- Product Baseline validation resolves the exact Git commit, recomputes every locked subtree hash from that commit's tracked blobs, and rejects missing trees, forged hashes, invalid component versions, unbound mainline IDs, empty Owner evidence, or Map/Handoff identity drift.
- Kept worktrees optional for parallel construction or environment isolation and prohibited empty product subtrees or empty interfaces for unimplemented EXTRA.
- Preserved Simulation-first formation, CORE/EXTRA meaning, Feature Slice inheritance, phases, gates, status authority, Loop boundaries, security closure, and Delivery governance.

## 2.3.0

### Built-in BI and standalone Windows window

- Added a built-in, read-only BI projection for LCCoding with the fixed `INITIAL`, `PRODUCT_FORMATION`, `ENGINEERING_RUNS`, and `DELIVERY_PREPARATION` phases, plus fine-grained milestones, states, artifacts, and protected subreports.
- Added a compact standalone Windows window with an English-first interface, a Chinese language switch, and native Pin control for always-on-top use.
- Kept the accepted 300×480 visual design and its browser preview safety boundary; the desktop shell displays only the authorized sanitized Snapshot.
- The BI does not read or mutate project files, does not control Agent or runtime behavior, and does not claim that real project data integration is complete.
- Preserved the canonical mainline, phase/gate authority, Owner acceptance boundaries, security closure, protected Delivery, and lower-method responsibilities.

## 2.2.3

### Simulation-first Product Formation

- Clarified the internal order of the existing `WORKFLOW_UI_SIMULATION` node: establish a minimal, real, runnable, versioned Simulation World foundation before actual Workflow or UI construction.
- Kept the foundation deliberately incomplete and `VERSIONED_MUTABLE`; it gains fidelity, scenarios, and project learning instead of becoming a one-time complete freeze.
- After the foundation exists, Workflow and UI advance independently as equal product ends and may proceed concurrently, but each must produce real, runnable, inspectable results rather than plans, shells, mocks, or simulation-only substitutes.
- Early Product Formation does not require Workflow-to-UI connection or three-way joint integration. Semantic/scenario synchronization continues, while cross-layer connection and end-to-end proof remain with Feature Slice and UI-locked Integration.
- Workflow realization, CORE/EXTRA and Product Baseline rules, Feature Slice inheritance/improvement, Private UI baseline protection, canonical mainline, phases, states, gates, Loop responsibilities, and runtime boundaries remain unchanged.

## 2.2.2

### Private UI baseline protection

- Strengthened the existing `UI=LOCKED` rule so the complete, rebuildable UI baseline lives in an independent, Owner-controlled GitHub repository that remains `PRIVATE`, regardless of product-repository visibility.
- Required Product Baseline Handoff and Integration Baseline to share one remote/path/exact-SHA/content-hash identity, with deterministic hash-scope, Private-visibility, remote-resolution, push, and recovery evidence; local-only, Public/Unknown, branch/latest, unresolved, mismatched, or render-only references do not lock UI.
- Required baseline comparison before a Feature Slice or Run starts and before acceptance, with Owner-control, Private-visibility, and exact-commit resolution re-proved before acceptance. Unauthorized UI deltas block progress, preserve evidence, and are restored from the locked Private remote commit or handled in isolation without silently overwriting Owner material.
- Kept the existing Baseline Change Request as the only route for absolutely necessary UI changes, including a distinct new Private remote commit, identical Product/Integration reference updates, and affected-evidence re-verification.
- Canonical mainline, phases, states, gates, Feature Slice placement, Loop responsibilities, and runtime boundaries remain unchanged.

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
