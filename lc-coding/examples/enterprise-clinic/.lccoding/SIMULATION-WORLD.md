# Simulation World

- Primary product mainline ID: MAINLINE-APPT

## Simulation subtree registry

| Simulation ID | Subtree path | Component version | Content hash | Foundation status | Workflow subtree references | UI subtree references | Primary mainline |
|---|---|---|---|---|---|---|---|
| SIM-CLINIC | product/simulations/clinic | 3.0.0 | sha256:3333333333333333333333333333333333333333333333333333333333333333 | RUNNABLE | WF-APPT | UI-APPT | YES |

## Scenario registry

| Simulation ID | Scenario ID | Actors | Data/state/time | Path | Failure/recovery | Fidelity | Visible / invisible evidence | Used by Slice/Run/Acceptance | Scenario version |
|---|---|---|---|---|---|---|---|---|---|
| SIM-CLINIC | SCN-APPT-01 | staff/patient | realistic schedule | create appointment | slot conflict/retry | integrated | UI + state evidence | FS-001/RUN-001/Owner | 3 |
