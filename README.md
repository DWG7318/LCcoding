# LCCoding 2.4.0

**Owner-led, AI-executed enterprise product development with visible incremental acceptance and centralized independent security closure.**

LCCoding keeps its original method spine:

```text
Proposal Readiness
→ Project Initialization
→ Calabash Draft
→ [Simulation World foundation first → Workflow capability end ∥ UI product-surface end]
→ Mandatory Calabash Upgrade
→ Product Baseline
→ Feature Slice
→ UI-locked Integration
→ SLK / CLK / GLK
→ Independent layered Verification
→ Owner Acceptance
→ Delivery
```


Operational binding:

- every normal Loop Run contains `D0–D3 → Loop Owner Acceptance`;
- after all required normal Runs are accepted, `Independent layered Verification` contains the centralized independent vulnerability audit, remediation, re-audit, and closure;
- the mainline `Owner Acceptance` is the distinct Post-Security Owner Acceptance;
- Delivery begins with customer-specific Delivery Method Q&A.

The mainline has not been replaced. Loop Owner Acceptance remains inside SLK, CLK, and GLK so the Owner accepts small completed Runs as work advances. The later Post-Security Owner Acceptance is a distinct, focused acceptance of the security-remediated delivery candidate.

## Existing engineering intake

Project Initialization supports `NEW` and `EXISTING` modes without adding a lifecycle. EXISTING preserves repository history, declared version, materials, and valid evidence. Prior completion is `CLAIMED_UNATTESTED` until the current candidate and evidence are independently established.

The Owner chooses `CONTINUE`, `NARROW_REDIRECT`, `HOLD`, or `TERMINATE` before engineering. Runnable UI is the first Owner-visible cognition anchor, not completion proof; it is traced back to Workflow, state, data, permissions, failure/recovery, and evidence for invisible behavior. Only real gaps enter normal Feature Slices and Loop Runs.

Takeover stays inside Project Initialization and ends as `READY`, `BLOCKED`, or `NOT_CONTINUING`. `status.json` is the single authoritative durable project status; Project Health is assessment evidence and `PHASE-STATUS.json` is derived. No runtime or Agent-session state belongs in these records.

## Fixed mainline, proportional depth

Every mandatory node remains. Project Fingerprint product uncertainty, system coupling, real risk, irreversibility, and novelty govern analysis, material, and evidence depth. `UNKNOWN` is a recorded pending state that requires assessment and conservative deeper coverage; it is never treated as all-low or a sufficient final judgment. Sufficient evidence is reused; simple work may be concise, while high-risk work must deepen. `recommended_loop` remains topology-only.

## Simulation-first product formation

A minimal, real, runnable, versioned Simulation World foundation comes first inside the existing Workflow/UI/Simulation node. It is intentionally incomplete and remains `VERSIONED_MUTABLE`. A project may add multiple peer Simulation subtrees, never nested Simulation children.

Workflow and UI then advance independently as equal product ends and may proceed in parallel; each must form a real, runnable, inspectable result rather than a plan, shell, or mock. Product Formation keeps their meaning and scenarios synchronized but does not require early connection or three-way joint integration. Feature Slice and UI-locked Integration own the later cross-layer connection and proof, while retaining the Slice's existing Workflow inheritance and improvement responsibilities.

One project Git/GitHub repository contains multiple UI, Workflow, and Simulation logical subtrees. Each realized subtree has its own component version and content hash. Every CORE Workflow and implemented EXTRA Workflow directly provides both API and MCP contracts backed by the same capability; an unimplemented EXTRA has no empty subtree or interface claim. The Owner confirms one Primary product mainline across at least one Simulation, one CORE Workflow, and one UI to set construction priority without relaxing any other CORE obligation. A worktree is optional isolation, not product structure.

## Built-in BI and Windows desktop

LCCoding 2.4.0 includes a built-in, read-only BI projection and a standalone Windows window. The compact 300×480 view presents the fixed `INITIAL`, `PRODUCT_FORMATION`, `ENGINEERING_RUNS`, and `DELIVERY_PREPARATION` phases together with fine-grained milestones, states, artifacts, and protected subreports. Its interface starts in English, can switch to Chinese, and provides native Pin control for always-on-top use.

This BI is a visibility surface, not a second authority or execution system. The released desktop window uses only the authorized sanitized Snapshot: it does not read or mutate project files, does not control Agent or runtime behavior, and does not claim that real project data integration is complete. See [`lc-coding/references/built-in-bi.md`](lc-coding/references/built-in-bi.md) for the closed projection and safety contract.

## Slice execution and Owner gaps

A Feature Slice enters SLK/CLK/GLK only after product-level Execution Coverage Preflight passes. Unproven cross-layer wiring requires a thin production-quality first proving Run or cited sufficient evidence; its failure halts expansion. LCCoding defines admission and handoff, while the selected Loop retains all GO/CELL internals.

Owner rework, definition changes, and deferrals receive stable gap IDs. A blocking gap stays open through Impact Analysis or Calabash routing, correction Run, affected D0–D3, delta re-verification, and Owner re-acceptance. The canonical status indexes open gaps and evidence pointers without becoming a gap archive.

## Logical-subtree baseline protection

Product Baseline freezes the total project exact commit and every realized UI, Workflow, and Simulation subtree name/path/component version/content hash, their ID relations, and the Owner-confirmed Primary product mainline. `UI=LOCKED` pins the applicable UI subtree to that same commit/hash identity. Each Slice compares it before work and acceptance; an approved Baseline Change Request is the only route to replace the lock.

## Four-phase overlay

```text
INITIAL
→ PRODUCT_FORMATION
→ ENGINEERING_RUNS
→ DELIVERY_PREPARATION
```

- `INITIAL` ends before Calabash Draft.
- `PRODUCT_FORMATION` ends before Mandatory Calabash Upgrade.
- `ENGINEERING_RUNS` repeats one Run at a time and exits each Run at Loop Owner Acceptance.
- `DELIVERY_PREPARATION` starts after all required normal Runs are Owner-accepted, then performs one centralized independent security audit, remediation, re-audit, Post-Security Owner Acceptance, Delivery Method Q&A, and packaging governance.

## Security independence

The centralized Security Auditor must be a fresh independent Agent that did not implement, check, verify, supervise, or accept the candidate being audited. The auditor discovers and verifies vulnerabilities; separate engineering roles perform remediation. The auditor then re-audits and signs `VULNERABILITY_CLOSED`.

D0–D3 may contain local security-sensitive checks required by their contracts, but they do not replace the centralized vulnerability audit and do not issue its verdict.

## Validate

```bash
python lc-coding/scripts/validate_repository.py .
python lc-coding/tests/run_tests.py
```

See [`README.zh-CN.md`](README.zh-CN.md), [`CONSTITUTION.md`](CONSTITUTION.md), [`SPEC.md`](SPEC.md), and [`lc-coding/SKILL.md`](lc-coding/SKILL.md).
