# Workflow Map

For EXISTING intake, reconstruct Workflow from Owner-visible entries through state, data, permissions, exceptions, and recovery. Unknown behavior remains UNKNOWN until independently evidenced.

- Primary product mainline ID:

| Workflow ID | Classification (CORE/EXTRA) | Implementation status | Classification authority | Subtree path | Component version | Content hash | Workflow Capability ID | Actors | Trigger | Rules / state / side-effect trace | Data / permissions | Failure / recovery | API contract / evidence | MCP contract / evidence | UI subtree references | Simulation subtree references | Evidence / attestation | Primary mainline |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Every implemented CORE or EXTRA row is one real Workflow capability subtree. `Classification authority` is exactly `CLASSIFICATION:<CORE|EXTRA>; CALABASH:<evidence-id>; OWNER_CONFIRMED:<evidence-id>`. The Workflow capability is one safe ID. API and MCP are separately evidenced interfaces to that same capability, each encoded as `CAPABILITY:<same-id>; CONTRACT:<contract-id>; EVIDENCE:<evidence-id>`. The implementation trace is exactly `RULES:<evidence-id>; STATE:<evidence-id>; SIDE_EFFECTS:<evidence-id>`, and `Evidence / attestation` is exactly `IMPLEMENTATION:<evidence-id>; RUNNABLE:<evidence-id>`. Component version uses `MAJOR.MINOR.PATCH`; Primary mainline is exactly `YES` or `NO`. An unimplemented EXTRA remains a registry row with `NOT_APPLICABLE` for subtree path, component version, content hash, capability, implementation trace, API, MCP, and implementation evidence, `NONE` relations, and Primary `NO`; it is not an empty capability. CORE/EXTRA is business necessity, not a technical layer.
