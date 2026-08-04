---
name: lc-coding
description: Use when an Owner wants AI to develop or admit an existing enterprise product through Proposal Readiness, new/existing Project Initialization, Calabash Draft, Simulation-first Workflow/UI product formation, Mandatory Calabash Upgrade, Product Baseline, Feature Slice, UI-locked Integration, SLK/CLK/GLK execution with incremental Loop Owner Acceptance, centralized independent vulnerability closure, Post-Security Owner Acceptance, and protected customer-specific Delivery.
---

# LCCoding 2.4.1

## Canonical mainline

```text
Owner Proposal
→ Proposal Readiness Check
→ Project Initialization
→ Calabash Draft
→ [Simulation World foundation first → Workflow capability end ∥ UI product-surface end]
→ Mandatory Calabash Upgrade
→ Product Baseline
→ Feature Slice
→ UI-locked Feature Integration
→ SLK / CLK / GLK
→ Independent layered Verification
→ Owner Acceptance
→ Delivery
```

Operational meaning:

- every normal Loop Run includes D0–D3 and its own Loop Owner Acceptance;
- after all required Runs are accepted, Independent Verification performs one centralized vulnerability audit and remediation closure;
- the mainline Owner Acceptance is Post-Security Owner Acceptance;
- Delivery begins only after customer-specific Q&A.

## Phase overlay

- `INITIAL`: through Project Initialization; exit `INITIAL_READY` before Calabash Draft.
- `PRODUCT_FORMATION`: Calabash Draft through Workflow/UI/Simulation; exit `CALABASH_UPGRADE_READY`.
- `ENGINEERING_RUNS`: repeat one Run at a time through D3; exit each Run at `LOOP_OWNER_ACCEPTANCE_READY`; aggregate exit `ALL_REQUIRED_RUNS_ACCEPTED`.
- `DELIVERY_PREPARATION`: centralized vulnerability audit/remediation/re-audit, Post-Security Owner Acceptance, Delivery Method Q&A, and package governance; exit `DELIVERY_READY`.

## Principle Zero

Owner decides product meaning. AI completes routine engineering autonomously inside frozen boundaries.

## Start

1. Run Proposal Readiness once over all supplied material.
2. Ask only blocking gaps; persist answers and never re-ask without contradictory evidence.
3. Select NEW or EXISTING Project Initialization.
4. For NEW, initialize Git/GitHub and version `0.0.1`. For EXISTING, preserve repository/history/version/materials and record current HEAD/candidate before adding LCCoding artifacts.
5. Initialize or reuse Agents Rule, skills, capabilities, canonical lock, profile, fingerprint, health, and the one authoritative `status.json`.
6. Revalidate only changed initialization inputs.

Use one project Git/GitHub repository by default. Do not pre-create empty UI, Workflow, or Simulation directories. Product units become logical subtrees only when real work exists. A worktree is optional for parallel work or environment isolation and never becomes product structure or baseline identity.

## Existing engineering intake

- Treat inherited completion as `CLAIMED_UNATTESTED` until candidate identity and evidence coverage are valid.
- Present facts and obtain Owner `CONTINUE`, `NARROW_REDIRECT`, `HOLD`, or `TERMINATE`; do not optimize the Owner's product direction.
- Use runnable UI as the first Owner-visible cognition anchor, not proof. Trace it to Workflow, state, data, permissions, exceptions, recovery, and independently evidenced invisible behavior.
- Reuse trustworthy evidence; unknown remains unknown. Route only real gaps into existing Feature Slices and Loop Runs.
- Classify the result as `ATTESTED_COMPLETE`, `NEEDS_GAP_CLOSURE`, `PARTIAL`, `DIRECTION_CHANGED`, or `NOT_CONTINUING`.
- Keep takeover inside Project Initialization. Output only `READY`, `BLOCKED`, or `NOT_CONTINUING`; do not enter engineering until repository/version/candidate, historical materials, evidence, product mainline, and blockers support the result.
- Treat Project Health as assessment evidence and `PHASE-STATUS.json` as a derived view of authoritative `status.json`. Persist method facts only, never runtime/session/Agent state.

## Fixed mainline, proportional depth

Keep every mandatory mainline node. Use Project Fingerprint product uncertainty, system coupling, real risk, irreversibility, and novelty to deepen analysis, material, and evidence where needed. Record `UNKNOWN` as unresolved, require depth assessment plus conservative rationale and coverage, and do not treat it as a sufficient final judgment or all-low work. Cite sufficient existing evidence instead of duplicating it. Concise is allowed; empty or risk-blind is not. `recommended_loop` selects execution topology only.

## Product formation

1. Create Calabash Draft from the ready Proposal.
2. Build at least one minimal, real, runnable, versioned Simulation World foundation before actual Workflow or UI construction. A project may then add multiple peer Simulation logical subtrees; never nest one Simulation under another. Reuse scenario IDs downstream and strengthen each Simulation as scenarios and learning grow. Never treat the foundation as a complete or frozen Simulation; all Simulation subtrees remain `VERSIONED_MUTABLE`.
3. Then advance Workflow and UI as equal product ends, independently; they may proceed in parallel, and each must produce a real, runnable, inspectable result. Multiple UI, Workflow, and Simulation logical subtrees may coexist inside the one project Git/GitHub repository. Each realized subtree has a safe relative path, component version, and content hash. Do not require early Workflow-to-UI connection or three-way joint integration. Continue semantic and scenario synchronization without treating it as early integration; use Map IDs, not directory nesting, and allow UI-to-Workflow and Simulation-to-Workflow many-to-many relations. Keep cross-layer connection and end-to-end proof in Feature Slice and UI-locked Integration. Use Calabash and available Simulation Worlds to split Workflow into enough business lines and progressively implement real, runnable business functions. Plans, empty shells, mocks, and simulation-only results cannot replace real Workflow; it may continue to iterate with Calabash and Simulation until Mandatory Calabash Upgrade is complete. Mark each Workflow business line `CORE` or `EXTRA`; this classification is business necessity, not a Workflow Core technical layer. CORE means Calabash and Owner confirmation make the business line required product capability. EXTRA comes from Calabash extension space, external research, or comparable-product analysis. Every CORE Workflow and every implemented EXTRA Workflow directly provides both API and MCP contracts backed by the same capability. Do not introduce duplicate logic, mandatory microservices, runtime, or deployment topology. An unimplemented EXTRA remains only a registry row with no subtree, API, or MCP claim. Do not claim unimplemented EXTRA as product capability. Never reclassify CORE as EXTRA to pass Product Baseline; change classification only through Calabash with Owner confirmation.
4. Synchronize only consequential learning into one existing canonical artifact; the field may be blank when no future decision, constraint, check, template, or reuse rule changes.
5. When several subtrees exist, obtain Owner confirmation for one Primary product mainline linking at least one Simulation, one CORE Workflow, and one UI. Use it as the first proving and construction priority; finish every other CORE without downgrading it. A controlled Calabash upgrade may re-confirm the selection.
6. Run Mandatory Calabash Upgrade before Product Baseline.
7. The Product Baseline gate applies only to CORE Workflow. Freeze Product Baseline only after every CORE business line is real, runnable, and proved feasible; each must also have direct API and MCP evidence. If any CORE is not real and runnable, lacks either interface, or is proved infeasible under current product constraints, first adjust Calabash, narrow, hold, or terminate under Owner authority. EXTRA does not block Product Baseline and remains a non-capability until implemented and verified. Product Baseline Handoff locks one total project repository at an exact Git-resolvable commit plus every realized UI, Workflow, and Simulation subtree name/path/`MAJOR.MINOR.PATCH` component version/content hash, their ID relations, and the Owner-confirmed Primary product mainline. Recompute every subtree hash from the frozen commit with the one canonical tracked-blob manifest algorithm, never from the worktree, and require Handoff identities, Workflow classification/API/MCP evidence, relations, and mainline markers to match the three canonical Maps. Commit and content hash are authoritative; component version is the human-readable label.

## Feature Slice and Integration

Create one canonical Slice contract tracing actor intent through UI, Integration, Workflow, state/data/side effects, visible result, evidence, and acceptance. Start from the Owner-confirmed Primary product mainline unless impact evidence selects another governed route. Identify all already implemented and verified Workflow capabilities across CORE and EXTRA and inherit and reuse them wherever possible. Pin the applicable UI subtree to the total-project exact commit/path/component version/content hash. Because the Slice covers UI, Integration, state, data, permissions, exceptions, recovery, and visible results more completely, it may supplement, adjust, or improve Workflow under the existing Impact Analysis and `CONTROLLED_MUTABLE` rules.

Before selecting a Loop Run for execution, require Execution Coverage Preflight `PASS` across Product Baseline, Workflow/UI/Simulation, state/data/permissions, exception/recovery, Impact Analysis, Integration Baseline, Required Runs, D0–D3, and Owner Acceptance. It must include the total project repository/full exact baseline commit, applicable UI subtree ID/path/component version/content hash and scope, Product/Integration identity `MATCH`, Slice/Run-start `MATCH`, and a required before-acceptance comparison route. `HIGH/UNKNOWN` requires deeper evidence or smaller independently verifiable Runs.

If cross-layer wiring is unproven, make the first Required Run a thin production-quality E2E proving path. Halt expansion when it fails. Reuse sufficient existing proof instead of manufacturing a new Run.

Use the integration lock:

```text
UI = LOCKED
Workflow = CONTROLLED_MUTABLE
Simulation = VERSIONED_MUTABLE
Calabash = LIVING_WITH_IMPACT_TRACE
```

The UI lock applies to the applicable UI logical subtree in the total project repository. Screenshots, exports, previews, and build output are evidence only, never the recoverable baseline. Integration Baseline pins the total-project exact commit plus UI subtree ID/path/component version/deterministic content hash and must match Product Handoff; never use a branch, tag, `HEAD`, worktree, or `latest` as the lock.

Compare current UI subtree to the locked project commit and hash before a Slice/Run and before acceptance. An unapproved difference or identity mismatch blocks progress or acceptance; preserve its evidence, then restore from the locked project commit or isolate the work. Never silently overwrite user material. Modify locked UI only through an approved Baseline Change Request that records necessity, Owner approval, a distinct total-project commit, matching affected UI subtree component version/hash updates in Product and Integration Baselines, and affected evidence re-verification. Logical subtree means an in-repository product path, not Git's external-repository subtree mechanism.

## Loop selection

- SLK for one serial stream.
- CLK for fixed Chains and ordered Stages/full barriers.
- GLK for a real GO-to-GO graph.

Use one method per Run. Each Run has a fresh Run Supervisor, Run Scope, and Run Feature.

## Verification without waste

- D0: Worker local self-check; never acceptance.
- D1: independent Checker CELL acceptance.
- D2: independent GO outcome Verification using D0/D1 receipts.
- D3: fresh independent Stage/Run/Final composition Verification using lower receipts.

Worker, CELL Checker, and Run Supervisor cannot author D2/D3 verdicts. Repeat lower checks only for candidate change, stale/contradictory evidence, material environment difference, composition-sensitive behavior, affected regression, or a named risk.

## Loop Owner Acceptance

Every normal SLK/CLK/GLK Run must end:

```text
D3 PASS
→ LOOP_OWNER_ACCEPTANCE_READY
→ Supervisor-guided Loop Owner Acceptance
```

Do not aggregate several normal Runs into one late Owner acceptance. The Owner accepts each small completed Run while context is fresh.

Only after every required normal Run is `LOOP_OWNER_ACCEPTED` issue `ALL_REQUIRED_RUNS_ACCEPTED`.

For rework, definition change, or defer, assign one Owner gap ID. Keep the full lineage in existing Acceptance, Impact/Calabash route, correction Run, D0–D3, re-verification, and re-acceptance artifacts; keep only open gap indexes and evidence pointers in `status.json`. Never close a gap or aggregate the Slice without the required evidence and Owner result.

## Centralized vulnerability audit

Immediately after `ALL_REQUIRED_RUNS_ACCEPTED`:

1. Freeze the accepted aggregate candidate.
2. Create a fresh independent Security Auditor Agent/context/workspace.
3. Ensure the auditor did not act as Worker, Checker, Verifier, Run Supervisor, acceptance preparer, or remediation implementer.
4. Perform one coverage-complete audit over the final accepted candidate.
5. Reuse valid local security evidence but do not treat D0–D3 as the centralized verdict.
6. Route findings to separate engineering roles for remediation.
7. Re-run only invalidated engineering evidence.
8. Security Auditor independently re-audits and issues `VULNERABILITY_CLOSED` or blocks.

Formal vulnerability audit is centralized, not scattered across every engineering layer.

## Post-Security Owner Acceptance

After `VULNERABILITY_CLOSED`, perform one focused Owner Acceptance of the security-remediated candidate.

Reuse all Loop Owner Acceptance receipts. Check only remediation-affected UI/Workflow surfaces, affected Feature behavior, final candidate identity, and a critical smoke route. Do not make the Owner repeat unchanged prior acceptance.

Delivery requires `POST_SECURITY_OWNER_ACCEPTED`.

## Delivery

Run customer-specific Delivery Method Q&A after Post-Security Owner Acceptance. Load Owner Policy and contract facts, ask only unresolved questions, give a recommended option, persist every answer, and require `DELIVERY_METHOD_CONFIRMED`.

Deliver only approved product assets. Exclude LCagent, LCapi, LCCoding, Calabash, SLK, CLK, GLK, internal tools, canonical assets, internal knowledge/workflow/recommendation logic, development evidence, and source code unless Owner authorizes them.

Ubuntu remains the preferred recommendation where suitable. Docker is not required. Enforce Owner-confirmed no-resale, redistribution, sublicense, repackaging, unauthorized-modification, reverse-engineering, transfer, and control-removal boundaries.

## Built-in BI

Use the built-in BI only as a read-only Owner-visible projection of the fixed four phases, fine-grained milestones, states, artifacts, and protected subreports. The compact Windows window starts in English, can switch to Chinese, and may Pin only its own native always-on-top state.

The 2.4.1 desktop release adds only a protected Product Baseline report to `PRODUCT_BASELINE` and a protected Loop Governance report to `LOOP_RUN_D0_D3`; it does not add lifecycle nodes. Project-subtree and lower-method governance facts may appear only as strict sanitized metrics with `UNKNOWN`/`NOT_RECORDED` for absent evidence. Never infer `7/7`, progress, versions, API/MCP coverage, Heartbeat interval, or compliance from missing data.

The desktop still uses the authorized synthetic sanitized Snapshot; the real project adapter remains not implemented. Do not read Maps/Handoff or SLK/CLK/GLK files into the webview, add a parser/runtime, or expose a control command. The BI does not write project files, control Agent/runtime behavior, or become a second status authority; `status.json` remains authoritative.

## Version policy

- NEW initial `0.0.1`; EXISTING preserves its declared version or records `UNKNOWN`;
- small upgrade: commit only;
- medium: `0.0.x`;
- large: `0.x.1`;
- `1.0.1+`: Owner approval required.
