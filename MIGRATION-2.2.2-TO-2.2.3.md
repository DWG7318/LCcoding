# Migration from 2.2.2 to 2.2.3

LCCoding 2.2.3 keeps the 2.2.2 canonical mainline, `WORKFLOW_UI_SIMULATION` lifecycle node, four phases, states, gates, Feature Slice, UI lock, runtime boundary, and lower-method responsibilities unchanged.

## Existing Product Formation work

- Before starting actual Workflow or UI construction, create or cite a minimal, real, runnable, versioned and resettable Simulation World foundation.
- Treat the foundation as an initial common product world, not a complete Simulation or frozen gate artifact. Keep it `VERSIONED_MUTABLE` and extend it through versioned scenario and fidelity deltas.
- Once the foundation exists, advance Workflow and UI as equal but independent product ends. They may proceed concurrently, but each must yield a real, runnable, inspectable result; plans, shells, mocks, screenshots, and simulation-only output do not replace either end.
- Continue synchronizing consequential product meaning and shared scenario IDs. Do not require early Workflow-to-UI wiring or three-way joint integration inside Product Formation.
- Keep cross-layer connection and end-to-end proof in the existing Feature Slice and UI-locked Integration boundaries. Feature Slice still inherits and reuses verified Workflow and may supplement, adjust, or improve it under existing rules.
- Preserve existing Workflow business-line realization, CORE/EXTRA classification and Product Baseline hard gate, as well as the independent Private GitHub UI baseline and immutable Integration lock.

No Simulation foundation phase, lifecycle node, gate, state, readiness verdict, runtime mechanism, Agent/session control, CLI, service, or lower-method responsibility is introduced.
