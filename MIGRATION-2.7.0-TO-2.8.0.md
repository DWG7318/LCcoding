# LCCoding 2.7.0 to 2.8.0 candidate migration

This is a copy-on-write project migration contract, not a release, deployment,
or evidence-upgrade procedure. It creates a separate 2.8 candidate while the
authoritative 2.7 project remains byte- and mtime-identical.

## Closed migration contract

- Source status schema: 2.7.0
- Target status schema: 2.8.0
- Migration status: CANDIDATE_ONLY_NOT_A_RELEASE
- Candidate construction: COPY_ON_WRITE_EXTERNAL_TARGET
- Source preservation: ORIGINAL_2_7_INPUTS_BYTES_AND_MTIMES_UNCHANGED
- Generated output as migration input: FORBIDDEN
- Schema inference or mixed identity: FORBIDDEN
- Existing receipt treatment: HISTORICAL_ONLY_NOT_CURRENT
- Required 2.8 evidence state: EXPLICITLY_UNPROVED
- Synthetic lifecycle completion: FORBIDDEN
- Rollback treatment: ATOMIC_TARGET_ABSENT_ON_FAILURE
- BI compatibility: EXISTING_SINGLE_ASSET_DUAL_READ_ONLY
- BI modification in this migration: NONE
- Current release change: NONE
- Global Skill deployment: NOT_PERFORMED

The source must be a complete, mechanically valid 2.7 project with the exact
legacy phase identity `ENGINEERING_RUNS`. The candidate uses exact schema
`2.8.0` and exact phase identity `REAL_PRODUCT_INTEGRATION`. Missing, inferred,
hybrid, duplicate, unknown, or fifth-phase records fail closed.

## Copy-on-write execution

Use a target that does not exist, outside and non-overlapping with the source.
Neither argument may select generated input such as `gen`, `node_modules`,
`dist`, Cargo `target`, `test-results`, or `playwright-report`.

```powershell
$sourceProject = 'D:\Projects\authoritative-2.7.0'
$candidateProject = 'D:\Candidates\lccoding-2.8.0'
if (Test-Path -LiteralPath $candidateProject) {
    throw 'candidate output must start absent'
}
python .\lc-coding\scripts\migrate_project_270_to_280.py `
    --project $sourceProject `
    --output $candidateProject
```

The migrator validates the source, makes a metadata-preserving staged copy,
transforms only the staged records, runs the complete phase and project
validators, and atomically publishes the target. Any failure removes only the
contained stage and leaves the target absent. Rollback is therefore to discard
or isolate the unaccepted target and continue from the untouched 2.7 source;
2.8 state never flows back into 2.7.

## Phase identity and evidence boundary

The only phase-ID conversion is `ENGINEERING_RUNS` to
`REAL_PRODUCT_INTEGRATION`. The four phases, existing steps, and existing gates
remain unchanged. Migration adds no step, gate, Run completion, Owner
acceptance, security closure, or Delivery readiness.

Prior Run, Owner Acceptance, and security receipt bytes are retained beneath
`.lccoding/history/2.7.0` with their prior status and phase view. They remain
historical evidence only and are not indexed as current 2.8 acceptance.

The candidate explicitly records these requirements as `UNPROVED`:

- Operations Agent integration;
- Agent Configuration Baseline;
- final production execution topology;
- Runtime Adapter attestation;
- Product/Operations Agent isolation; and
- agent security evidence.

The final topology must later make an evidenced `SELECT / COMPOSE / FEDERATE / RETIRE`
disposition. Until those conditions are independently proved and accepted, the
candidate remains in Product Formation, with Phase 3, security, acceptance, and
Delivery claims pending.

## Compatibility and release boundary

The existing single BI compatibility asset continues to dual-read 2.7 and 2.8;
this migration neither modifies BI nor creates a second compatibility source.
It does not change repository `VERSION`, the current release, the installed
global Skill, or any Runtime. Formal version propagation, release, deployment,
and Runtime Adapter installation require their later independently accepted
tasks.
