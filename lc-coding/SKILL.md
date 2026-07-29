---
name: lc-coding
description: Use when an Owner wants AI to develop an enterprise product through Proposal Readiness, project initialization, Calabash Draft, Workflow/UI dual-end design, realistic Simulation, Mandatory Calabash Upgrade, Product Baseline, Feature Slice, UI-locked Integration, SLK/CLK/GLK execution with incremental Loop Owner Acceptance, centralized independent vulnerability closure, Post-Security Owner Acceptance, and protected customer-specific Delivery.
---

# LCCoding 2.0.0

## Canonical mainline

```text
Owner Proposal
→ Proposal Readiness Check
→ Project Initialization
→ Calabash Draft
→ Workflow capability end ↔ UI product-surface end ↔ Simulation World
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
3. Initialize Git/GitHub, Agents Rule, skills, capabilities, canonical lock, profile, fingerprint, and health.
4. Revalidate only changed initialization inputs.

## Product formation

1. Create Calabash Draft from the ready Proposal.
2. Develop Workflow and UI as equal ends.
3. Build one versioned Simulation World and reuse scenario IDs downstream.
4. Synchronize confirmed learning into Calabash lineage.
5. Run Mandatory Calabash Upgrade before Product Baseline.
6. Freeze Product Baseline.

## Feature Slice and Integration

Create one canonical Slice contract tracing actor intent through UI, Integration, Workflow, state/data/side effects, visible result, evidence, and acceptance.

Use the integration lock:

```text
UI = LOCKED
Workflow = CONTROLLED_MUTABLE
Simulation = VERSIONED_MUTABLE
Calabash = LIVING_WITH_IMPACT_TRACE
```

Modify locked UI only through approved Baseline Change Request.

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

## Version policy

- initial `0.0.1`;
- small upgrade: commit only;
- medium: `0.0.x`;
- large: `0.x.1`;
- `1.0.1+`: Owner approval required.
