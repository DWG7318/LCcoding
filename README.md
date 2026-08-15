# LCCoding 2.8.0

Owner-led, AI-executed enterprise product development with visible incremental acceptance and centralized independent security closure.

## Method at a glance

Source clauses: [LC-PHASE-001](SPEC.md#lc-phase-001), [LC-PHASE-002](SPEC.md#lc-phase-002), [LC-PHASE-003](SPEC.md#lc-phase-003), [LC-PHASE-004](SPEC.md#lc-phase-004)

```text
Proposal Readiness
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

The four phases are Initial (`INITIAL`), Product Formation (`PRODUCT_FORMATION`), Real Product Integration (compatibility state ID `ENGINEERING_RUNS`), and Delivery Preparation (`DELIVERY_PREPARATION`). `ENGINEERING_RUNS` preserves machine compatibility and is not the human phase name.

## Product and execution summary

Source clauses: [LC-FORM-001](SPEC.md#lc-form-001), [LC-FORM-002](SPEC.md#lc-form-002), [LC-FORM-003](SPEC.md#lc-form-003), [LC-INTEG-001](SPEC.md#lc-integ-001), [LC-RUN-001](SPEC.md#lc-run-001), [LC-RUN-003](SPEC.md#lc-run-003)

A minimal, real, runnable, versioned Simulation World foundation comes first. Workflow and UI then advance independently as real product ends; Feature Slice and UI-locked Integration own the later cross-layer connection and proof.

SLK, CLK, GLK, and compatible registered methods form a cross-phase execution axis, not a lifecycle node or an exhaustive method list. A Run returns evidence to its calling phase; lifecycle meaning remains in the specification.

## Personal origin, adaptable use, and contribution

Source clauses: [LC-AUTH-001](SPEC.md#lc-auth-001), [LC-AUTH-002](SPEC.md#lc-auth-002)

LCCoding originates in its Owner's personal ability, knowledge structure, and recurring project practice. Others may study and adapt LCCoding to their abilities, knowledge range, product domains, and working conditions.

Discussion and contributions are welcome. The Owner-maintained repository remains the canonical mainline; adaptations are contributions or documented variants, not silent replacements for canonical meaning.

## Canonical and focused navigation

Source clauses: [LC-AUTH-002](SPEC.md#lc-auth-002)

- Authority: [SPEC](SPEC.md), [Constitution](CONSTITUTION.md), [operator Skill](lc-coding/SKILL.md).
- Orientation: [fixed lifecycle and proportional depth](SPEC.md#lc-auth-002), [proposal readiness](lc-coding/references/proposal-readiness.md), [project initialization](lc-coding/references/project-initialization.md).
- Product work: [Feature Slice and integration](lc-coding/references/feature-slice-and-integration.md), [execution-method selection](lc-coding/references/loop-method-selection.md).
- Agent-native integration: [focused operator guidance](lc-coding/references/agent-native-integration.md).
- Evidence and delivery: [Loop Owner Acceptance](lc-coding/references/loop-acceptance-boundary.md), [vulnerability closure](lc-coding/references/vulnerability-closure.md), [delivery governance](lc-coding/references/delivery-governance.md).
- Built-in BI: [method/product contract](lc-coding/references/built-in-bi.md); [implementation, build, and test navigation](lc-coding/bi/README.md).
- Language: [完整中文导航](README.zh-CN.md).

## Validate

Source clauses: [LC-AUTH-002](SPEC.md#lc-auth-002)

Run `python lc-coding/tests/run_tests.py` and `python lc-coding/scripts/validate_repository.py .` from the repository root.
