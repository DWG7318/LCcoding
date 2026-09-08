# LCCoding 3.0.0 to 4.0.0 Migration

- Source status schema: 3.0.0
- Target status schema: 4.0.0
- Candidate construction: COPY_ON_WRITE_EXTERNAL_TARGET
- Source preservation: ORIGINAL_3_0_INPUTS_BYTES_AND_MTIMES_UNCHANGED
- Historical status treatment: PRESERVED_UNDER_.lccoding/history/3.0.0
- Required publication behavior: ATOMIC_TARGET_ABSENT_ON_FAILURE
- Accepted direct-browser classification: PLATFORM_COMPLETION
- Migrated Service Route Map state: DRAFT
- Personal Agent delivery: PERSONAL_AGENT_NOT_CLAIMED
- Service Center delivery: SERVICE_CENTER_NOT_CLAIMED
- Current release promotion: NOT_PERFORMED
- Global Skill deployment: NOT_PERFORMED

The migration accepts only a separate, nonexistent output path. It validates the
exact 3.0 source, constructs and validates a staged 4.0 candidate, and publishes
the target only after `validate_phase_status.py` and `validate_project.py` both
pass. Failure leaves the target absent and never changes the source tree.

An accepted 3.0 screenshot-backed browser journey supports only a conservative
`PLATFORM_COMPLETION` classification. The copied candidate receives a DRAFT
direct-product route with 4.0 delivery still `UNPROVED`; it does not infer a
Personal Agent route, Service Center route, or Agent delivery from API/MCP
existence. Its prior 3.0 status and phase view remain historical evidence, and
the unchanged browser artifacts remain evidence of what 3.0 accepted—not a 4.0
route-faithful PASS.

Because an accepted 3.0 Product Baseline has no adopted 4.0 Service Route Map or
route-bound formation evidence, the copied candidate reopens Product Formation.
The 4.0 Product Baseline, integration, journey, security, and delivery states are
unproved/pending until their required evidence exists. An unaccepted project at
Initial or Product Formation remains unclassified and is not retroactively
declared unsuitable.

The JSON migration report is deterministic and contains no timestamp, random
stage identifier, or claim of Personal Agent or Service Center delivery.

```powershell
python .\lc-coding\scripts\migrate_project_300_to_400.py `
  --project <source-3.0-project> `
  --output <new-4.0-candidate>
```
