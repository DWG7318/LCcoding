# Workflow Map

- Primary product mainline ID: MAINLINE-APPT

| Workflow ID | Classification (CORE/EXTRA) | Implementation status | Subtree path | Component version | Content hash | Actors | Trigger | States / rules | Data / permissions | Failure / recovery | API contract / evidence | MCP contract / evidence | UI subtree references | Simulation subtree references | Evidence / attestation | Calabash trace | Primary mainline |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| WF-APPT | CORE | IMPLEMENTED | product/workflows/appointments | 1.0.0 | sha256:1111111111111111111111111111111111111111111111111111111111111111 | staff | create appointment | draft→confirmed | clinic schedule / staff role | slot failure/retry | API-WF-APPT-v1 / D2-API-001 | MCP-WF-APPT-v1 / D2-MCP-001 | UI-APPT | SIM-CLINIC | D3-RUN-001 | PB-001 | YES |
