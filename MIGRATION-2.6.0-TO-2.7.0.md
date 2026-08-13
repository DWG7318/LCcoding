# LCCoding 2.6.0 to 2.7.0 candidate migration

This is a repository migration contract, not a release procedure. It creates a
separate 2.7.0 candidate from an authoritative 2.6.0 project; it does not
upgrade this repository, its BI release, or an installed global Skill.

## Closed migration contract

- Source version: 2.6.0
- Target candidate version: 2.7.0
- Migration status: CANDIDATE_ONLY_NOT_A_RELEASE
- Current repository release: 2.6.0
- Source preservation: ORIGINAL_2_6_INPUTS_UNCHANGED
- Candidate construction: COPY_ON_WRITE_EXTERNAL_TARGET
- Generated output as migration input: FORBIDDEN
- 2.6 status adapter: SUPPORTED_LEGACY
- 2.7 status adapter: CURRENT
- Adapter inference or mixed schema: FORBIDDEN
- Existing receipt treatment: PRESERVE_AS_HISTORICAL_EVIDENCE
- Current acceptance treatment: REPROVE_NEW_CONDITIONS
- Rollback treatment: DISCARD_OR_ISOLATE_UNACCEPTED_CANDIDATE
- Rollback authority: ORIGINAL_2_6_STATUS_AND_EVIDENCE_POINTERS
- 2.7 state backflow into 2.6: FORBIDDEN
- BI compatibility: EXISTING_SINGLE_ASSET_DUAL_READ_ONLY
- BI modification in this migration: NONE
- Global Skill deployment: POST_RELEASE_ONLY_WITH_EXACT_DIGEST
- Global Skill state: NOT_DEPLOYED_BY_MIGRATION

The only readable status schemas are exact `2.6.0` and exact `2.7.0`.
The former remains `SUPPORTED_LEGACY`; the latter is `CURRENT`. A missing,
mixed, inferred, or other schema is not a migration result.

## Copy-on-write execution

Run the existing migrator from a clean tooling checkout. Set the candidate
outside the source tree and outside the repository worktree; the source and
candidate must be distinct non-overlapping trees. Do not point either argument
at generated output: generated output is never an input.

```powershell
$sourceProject = 'D:\Projects\authoritative-2.6.0'
$candidateProject = 'D:\Candidates\lccoding-2.7.0'
$sourceFull = [System.IO.Path]::GetFullPath($sourceProject)
$candidateFull = [System.IO.Path]::GetFullPath($candidateProject)
if ($sourceFull -eq $candidateFull -or
    $candidateFull.StartsWith($sourceFull + [System.IO.Path]::DirectorySeparatorChar) -or
    $sourceFull.StartsWith($candidateFull + [System.IO.Path]::DirectorySeparatorChar)) {
    throw 'source and candidate must be distinct non-overlapping trees'
}
if (Test-Path -LiteralPath $candidateProject) {
    throw 'candidate output must not already exist'
}
python .\lc-coding\scripts\migrate_project_260_to_270.py --project $sourceProject --output $candidateProject
```

The migrator validates the 2.6 source, copies it to a contained temporary
stage, validates the candidate, and only then creates the target. It never
overwrites the original 2.6 authoritative project.

## Exact phase boundary map

```json
{
  "source": {
    "version": "2.6.0",
    "phase_step_counts": [3, 5, 7, 6],
    "MANDATORY_CALABASH_UPGRADE": "ENGINEERING_RUNS",
    "PRODUCT_BASELINE": "ENGINEERING_RUNS"
  },
  "target": {
    "version": "2.7.0",
    "phase_step_counts": [3, 7, 5, 6],
    "MANDATORY_CALABASH_UPGRADE": "PRODUCT_FORMATION",
    "PRODUCT_BASELINE": "PRODUCT_FORMATION"
  },
  "same_exact_21_step_set": true,
  "new_lifecycle_gates": [],
  "new_steps": [],
  "synthetic_progress": "FORBIDDEN"
}
```

The two named steps are the only relocation. No lifecycle gate, step, or
progress is created by migration.

## Evidence, rollback, and later release

Historical Run evidence, Owner Acceptance, security receipts, and evidence
pointers remain byte-preserved evidence for their original conditions. They
are neither forged nor promoted to current 2.7 acceptance. Any 2.7 condition
that needs current evidence must be proved again under its current contract.

If the candidate is not accepted, discard or isolate that candidate and
continue from the original 2.6 authoritative status and evidence pointers.
Rollback does not fabricate a receipt or acceptance, and never writes 2.7
state back into the 2.6 project.

BI compatibility remains the existing single compatibility asset's dual-read
protocol; this migration changes no BI asset or implementation. Deployment and
verification of the installed global `lc-coding` Skill happen only after an
independently accepted formal 2.7 release, using that release's exact digest.
