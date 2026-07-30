# Migration from 2.1.0 to 2.2.0

LCCoding 2.2.0 keeps the 2.1.0 mainline and adds two narrow contracts.

## Existing project takeover and status

- Keep EXISTING inside Project Initialization.
- Add takeover readiness as `READY`, `BLOCKED`, or `NOT_CONTINUING`; an incomplete 2.1 intake migrates to `BLOCKED`, never guessed `READY`.
- Use `status.json` as the single authoritative project status.
- Mark Project Health as assessment evidence and `PHASE-STATUS.json` as a view derived from `status.json`; reconcile conflicts toward status while preserving cited assessment evidence.
- Do not migrate session, Agent, process, queue, retry, model, hook, or orchestration state into LCCoding.

## Active Feature Slices and Owner gaps

- Before the next execution handoff, update each active Slice with Execution Coverage Preflight fields and obtain `PASS`.
- For `HIGH/UNKNOWN` complexity, record deeper evidence or smaller independently verifiable Run boundaries.
- Require a first production-quality proving Run only where cross-layer connection evidence is still unproven.
- Assign stable IDs to open Owner rework, definition-change, or deferred gaps. Keep only their open index and evidence pointers in `status.json`; retain full lineage in existing Acceptance, Impact/Calabash, Run, and verification artifacts.
- Do not retrofit closed 2.1 Runs with invented receipts. Reuse trustworthy evidence and leave unavailable facts `UNKNOWN`.

No Takeover phase, UAT phase, state database, gap directory, tracer task type, Loop internals, runtime kernel, tag, or release operation is introduced by this migration.
