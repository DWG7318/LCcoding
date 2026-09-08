# Simulation World

- Primary product mainline ID:

## Simulation subtree registry

| Simulation ID | Subtree path | Component version | Content hash | Foundation status | Workflow subtree references | UI subtree references | Primary mainline |
|---|---|---|---|---|---|---|---|

Peer simulations do not nest inside any realized UI, Workflow, or other Simulation subtree. Relationships are closed reciprocal IDs, not directory structure, and many-to-many relations remain allowed. Every realized Simulation is `RUNNABLE` at Product Baseline. Component version uses `MAJOR.MINOR.PATCH`; Primary mainline is exactly `YES` or `NO`.

## Scenario registry

| Simulation ID | Scenario ID | Actors | Data/state/time | Path | Failure/recovery | Fidelity | Visible / invisible evidence | Used by Slice/Run/Acceptance | Scenario version |
|---|---|---|---|---|---|---|---|---|---|

Reuse Scenario IDs; increase fidelity/version instead of copying the scenario.

## 4.0 service route Simulation trace

| Service Route ID | Simulation ID | Workflow Capability ID | Scenario IDs | Audit event IDs |
|---|---|---|---|---|

For an accepted 4.0 Product Baseline, every required route names real Scenario IDs from the registry. Use exact `NONE` only when the adopted route has no audit event IDs. An applicable Service Center route requires both Simulation scenarios and the attributable audit event IDs from the adopted Service Route Map.

## Agent failure simulation evidence

```json
{
  "schema_version": "2.8.0",
  "artifact_role": "AGENT_FAILURE_SIMULATION_EVIDENCE",
  "candidate_id": "",
  "candidate_hash": "",
  "configuration_baseline_id": "",
  "configuration_baseline_hash": "",
  "production_topology_id": "",
  "production_topology_hash": "",
  "runtime_adapter_id": "",
  "runtime_adapter_version": "",
  "runtime_adapter_digest": "",
  "failure_recovery_attestations": []
}
```
