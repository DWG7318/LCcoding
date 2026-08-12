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
