# Loop Method Selection

Select the smallest truthful topology:

- SLK: one serial execution stream.
- CLK: fixed Chains, ordered Stages, full barriers.
- GLK: real GO-to-GO graph.

One normal Run uses one method. A method change requires governed stop/migration.

Every selected method binds the same exact [`Loop Control Contract`](loop-control-contract.md). It controls common operational policy but is not a topology and does not let a Loop copy or override another Loop's internal authority.

LCCoding owns the Feature Slice boundary. The selected Loop owns GO/CELL execution, D0–D3 topology, and incremental Loop Owner Acceptance.

LCCoding hands off only after Slice Execution Coverage Preflight passes. The handoff contains product/baseline identity, the total-project exact commit and applicable UI subtree path/version/hash scope, Product/Integration identity match and Slice/Run-start comparison, Primary product mainline, Required Run scope, proportional-depth response, scenarios, D0–D3 and acceptance conditions, any first proving Run requirement, and open Owner gap IDs. It never copies the selected Loop's tasks, waves, roles, retries, Chains, Stages, or graph internals.

A normal Run completes only after:

```text
D3 PASS
→ LOOP_OWNER_ACCEPTANCE_READY
→ LOOP_OWNER_ACCEPTED
```

Security remediation Runs created after the centralized audit are technical correction Runs; their product changes are consolidated into Post-Security Owner Acceptance.
