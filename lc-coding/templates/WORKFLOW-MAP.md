# Workflow Map

For EXISTING intake, reconstruct Workflow from Owner-visible entries through state, data, permissions, exceptions, and recovery. Unknown behavior remains UNKNOWN until independently evidenced.

- Primary product mainline ID:

| Workflow ID | Classification (CORE/EXTRA) | Implementation status | Subtree path | Component version | Content hash | Actors | Trigger | States / rules | Data / permissions | Failure / recovery | API contract / evidence | MCP contract / evidence | UI subtree references | Simulation subtree references | Evidence / attestation | Calabash trace | Primary mainline |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Every implemented CORE or EXTRA row is one real Workflow capability subtree and requires both API and MCP evidence backed by that Workflow. Component version uses `MAJOR.MINOR.PATCH`; Primary mainline is exactly `YES` or `NO`. An unimplemented EXTRA remains a registry row with `NOT_APPLICABLE` for subtree path, component version, content hash, API, and MCP; it is not an empty capability. CORE/EXTRA is business necessity, not a technical layer.
