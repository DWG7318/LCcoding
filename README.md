# LCCoding 2.2.2

**Owner-led, AI-executed enterprise product development with visible incremental acceptance and centralized independent security closure.**

LCCoding keeps its original method spine:

```text
Proposal Readiness
→ Project Initialization
→ Calabash Draft
→ Workflow ↔ UI ↔ Simulation
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

## Slice execution and Owner gaps

A Feature Slice enters SLK/CLK/GLK only after product-level Execution Coverage Preflight passes. Unproven cross-layer wiring requires a thin production-quality first proving Run or cited sufficient evidence; its failure halts expansion. LCCoding defines admission and handoff, while the selected Loop retains all GO/CELL internals.

Owner rework, definition changes, and deferrals receive stable gap IDs. A blocking gap stays open through Impact Analysis or Calabash routing, correction Run, affected D0–D3, delta re-verification, and Owner re-acceptance. The canonical status indexes open gaps and evidence pointers without becoming a gap archive.

## Private UI baseline protection

When `UI=LOCKED`, the rebuildable UI source is frozen in an independent, Owner-controlled GitHub repository that remains `PRIVATE`, regardless of the product repository's visibility. Product and Integration Baselines pin its exact remote commit and content hash with visibility, remote-resolution, and recovery evidence. Each Slice compares the working UI to that immutable baseline before work and before acceptance; an approved Baseline Change Request is the only route to replace it.

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
