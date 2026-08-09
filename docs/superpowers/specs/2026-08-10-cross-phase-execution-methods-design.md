# Cross-Phase Execution Methods Design

## Decision

LCCoding lifecycle and engineering execution are two independent axes.

- The four LCCoding phases define **what product condition must be formed next**.
- SLK, CLK, GLK, and other suitable methods define **how one bounded item of work is organized and executed**.

SLK, CLK, and GLK are removed from the canonical mainline as a fixed node. They remain available in any phase when the current work can truthfully be organized through a bounded Run and its GO/CELL structure. They are important registered methods, not an exhaustive list of all methods LCCoding may use.

## Lifecycle axis

The four phases remain compatible and keep their existing machine identifiers.

1. `INITIAL` establishes proposal readiness, project identity, continuity, and initialization evidence.
2. `PRODUCT_FORMATION` creates Workflow, UI, and Simulation as separate runnable product ends. They coordinate through Owner meaning, Calabash, and shared scenarios, but are not yet required to be tightly connected.
3. `ENGINEERING_RUNS` is normatively the **real product integration phase**. It connects Workflow, UI, and Simulation through real API/MCP-backed capability, real state/data/side effects, visible UI results, and integration/end-to-end testing.
4. `DELIVERY_PREPARATION` performs centralized security closure, post-security Owner acceptance, delivery decisions, and packaging governance.

The stable `ENGINEERING_RUNS` identifier is retained for compatibility, but its human meaning is Product Integration, not “the only phase where engineering methods may run.” The existing `ALL_REQUIRED_RUNS_ACCEPTED` field remains a compatibility identifier whose scope is the required third-phase integration work, not every method invocation across the project.

## Execution-method axis

Any bounded work item in any phase may use an execution method. The work item records its current LCCoding phase and phase-owned objective inside the existing scope/contract rather than creating a new lifecycle or status system.

Examples include:

- `INITIAL`: takeover reconstruction, repository validation, or initialization repair;
- `PRODUCT_FORMATION`: one Workflow line, one UI product surface, one Simulation scenario family, or Calabash evidence work;
- `ENGINEERING_RUNS`: real cross-layer Feature integration and integration proof;
- `DELIVERY_PREPARATION`: security remediation, packaging repair, or delivery verification.

One Run selects one topology. Different Runs, including Runs in the same or different phases, may select different methods. SLK fits a strict serial sequence, CLK fits fixed Chains with ordered full barriers, and GLK fits a real GO graph. LCCoding may also select another registered method when it fits better.

## Authority and evidence return

The calling LCCoding phase owns the work meaning, required outcome, acceptance boundary, and phase gate. The selected execution method owns only its internal decomposition, topology, role/evidence rules, and bounded completion proof.

A method result returns evidence to the calling phase. Completing or accepting a Run does not automatically advance the phase. The phase advances only when its own gate is satisfied by the accumulated evidence.

Phase-appropriate authority replaces the old assumption that every method call must begin after Product Baseline:

- before Calabash exists, authority may come from frozen Owner statements, Proposal Readiness, or Project Initialization contracts;
- during Product Formation, authority may come from the current Calabash Draft, scenario contracts, and the specific product-end contract;
- during Product Integration, authority comes from Product Baseline, Feature Slice, Integration Baseline, and related evidence;
- during Delivery Preparation, authority comes from the accepted candidate, security findings, delivery decisions, and package contract.

This does not weaken a method's topology admission rules, role separation, evidence requirements, or one-method-per-Run rule.

## Mainline and BI

The canonical mainline becomes:

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

The BI remains a read-only lifecycle projection. Its third-phase wording must describe real product integration and proof, not imply that SLK/CLK/GLK belong only there. Cross-phase method activity is phase-local evidence and does not add a lifecycle phase, BI control, or global runtime state.

## Compatibility and scope

- Keep the four phase IDs and existing stable gate/status identifiers.
- Remove project-global “Selected Loop” assumptions; method selection is per bounded Run/work item.
- Keep `LCCODING_LOOP_CONTROL` bound whenever an SLK/CLK/GLK Run is selected, regardless of phase.
- Do not modify SLK, CLK, or GLK internal topology in this LCCoding change.
- Publish separate method-repository updates later only where their trigger wording incorrectly assumes a third-phase-only handoff.
