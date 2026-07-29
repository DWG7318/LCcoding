# Loop Method Selection

Select the smallest truthful topology:

- SLK: one serial execution stream.
- CLK: fixed Chains, ordered Stages, full barriers.
- GLK: real GO-to-GO graph.

One normal Run uses one method. A method change requires governed stop/migration.

LCCoding owns the Feature Slice boundary. The selected Loop owns GO/CELL execution, D0–D3 topology, and incremental Loop Owner Acceptance.

A normal Run completes only after:

```text
D3 PASS
→ LOOP_OWNER_ACCEPTANCE_READY
→ LOOP_OWNER_ACCEPTED
```

Security remediation Runs created after the centralized audit are technical correction Runs; their product changes are consolidated into Post-Security Owner Acceptance.
