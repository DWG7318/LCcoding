# LCCoding 2.8.0 to 3.0.0 Migration

- Source status schema: 2.8.0
- Target status schema: 3.0.0
- Candidate construction: COPY_ON_WRITE_EXTERNAL_TARGET
- Source preservation: ORIGINAL_2_8_INPUTS_BYTES_AND_MTIMES_UNCHANGED
- Historical status treatment: PRESERVED_UNDER_.lccoding/history/2.8.0
- Required 3.0 journey state: EXPLICITLY_UNPROVED
- Rollback treatment: ATOMIC_TARGET_ABSENT_ON_FAILURE
- BI modification in this migration: NONE
- Global Skill deployment: NOT_PERFORMED
- Current release change: NONE

This migration inserts `REAL_USER_JOURNEY_ACCEPTANCE` between
`REAL_PRODUCT_INTEGRATION` and `DELIVERY_PREPARATION`. A 2.8 project that has
completed `ALL_REQUIRED_RUNS_ACCEPTED` enters the new phase with an unproved
journey record. Earlier projects remain at their corresponding phase.

A project already in Delivery Preparation is rejected by default. Reopening is
an explicit operation using `--reopen-delivery-preparation`; it moves the copied
candidate back to Real User Journey Acceptance and resets later delivery
evidence to pending. The original project is never changed.

Old D3 evidence, Loop Owner Acceptance, Post-Security Owner acceptance, package
smoke evidence, and other code-level proof remain historical evidence. None of
them is renamed, inferred, or promoted into real-user journey acceptance.

```powershell
python .\lc-coding\scripts\migrate_project_280_to_300.py `
  --project <source-2.8-project> `
  --output <new-3.0-candidate>
```
