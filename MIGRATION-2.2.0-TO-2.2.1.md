# Migration from 2.2.0 to 2.2.1

LCCoding 2.2.1 keeps the 2.2.0 canonical mainline, phases, states, gates, runtime boundary, and lower-method responsibilities unchanged.

## Existing Workflow Maps

- During the existing Workflow/UI/Simulation stage, progressively realize Workflow business lines as real, runnable capability; plans, shells, mocks, and simulation-only results do not substitute for implementation.
- Add one `Classification (CORE/EXTRA)` column to the existing single Workflow Map; do not split Workflow into parallel maps or stages.
- Classify each business line through Calabash and Owner confirmation. `CORE` is required product capability; `EXTRA` is an enhancement from Calabash extension space, external research, or comparable-product analysis.
- Do not reclassify CORE as EXTRA to pass Product Baseline. Any classification change returns to Calabash and requires Owner confirmation.
- Before Product Baseline, implement every CORE business line as real, runnable behavior and prove it feasible. An incomplete or infeasible CORE remains blocking.
- Attempt EXTRA, but technically difficult or infeasible EXTRA may remain conceptual, deferred, or infeasible without blocking Product Baseline. Unimplemented EXTRA must not be claimed as existing product capability.

## Active Feature Slices

- Reference and reuse all implemented and verified CORE and EXTRA Workflow capabilities.
- Continue any necessary Workflow improvement through the existing Impact Analysis and `CONTROLLED_MUTABLE` rules.

No Workflow Core/Extra phase, state, gate, second status source, runtime mechanism, or new lower-method responsibility is introduced.
