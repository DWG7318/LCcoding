# Cross-Phase Execution Method Selection

Execution methods are a horizontal overlay, not a lifecycle node. A bounded work item in any LCCoding phase may select a method when its objective, authority, inputs, output, and evidence boundary are frozen enough for truthful execution.

Select the smallest truthful topology:

- SLK: one serial execution stream.
- CLK: fixed Chains, ordered Stages, full barriers.
- GLK: real GO-to-GO graph.
- another registered execution method when it fits the work better.

This list is not exhaustive. Another registered method is eligible only when it exposes a compatible evidence and acceptance interface for the calling LCCoding work contract. One method per Run owns the execution topology. A method change requires governed stop/migration, while separate Runs may choose different methods.

Every selected method binds the same exact [`Loop Control Contract`](loop-control-contract.md). It controls common operational policy but is not a topology and does not let a Loop copy or override another Loop's internal authority.

The calling LCCoding phase owns the phase-owned objective, meaning, required result, acceptance boundary, and phase gate. The selected Loop owns GO/CELL execution, D0–D3 topology, and incremental Loop Owner Acceptance for its bounded Run.

Every handoff records the current phase, phase-owned objective, authoritative phase contract, Run scope, selected method, evidence return target, D0–D3 and acceptance conditions, and applicable risk/depth response. Product Baseline, Feature Slice, UI identity, Integration Baseline, and first proving Run fields are required only for Product Integration work where they apply. Earlier or later phases provide their own frozen authoritative inputs. LCCoding never copies the selected method's tasks, waves, roles, retries, Chains, Stages, or graph internals.

Completing or accepting a Run returns evidence to the calling phase. It does not satisfy or advance the phase gate by itself. The phase evaluates that evidence together with every other required phase condition.

A normal Run completes only after:

```text
D3 PASS
→ LOOP_OWNER_ACCEPTANCE_READY
→ LOOP_OWNER_ACCEPTED
```

Security remediation Runs created after the centralized audit are Delivery Preparation work; their product changes are consolidated into Post-Security Owner Acceptance.
