# Integration Baseline Lock

## Purpose

Integration must converge toward a fixed product target. If UI and implementation are
both allowed to move, AI can avoid difficult work by changing the visible product,
making acceptance unstable and often degrading the design.

## Default Baseline

```text
UI = LOCKED
Workflow = CONTROLLED_MUTABLE
Simulation = VERSIONED_MUTABLE
Calabash = LIVING_WITH_IMPACT_TRACE
```

The lock sacrifices UI flexibility temporarily, not UI quality. UI is freely designed
and iterated before Integration. Once accepted for a Feature Slice, every in-scope
actor surface becomes the fixed target until that slice is connected and accepted.

## Lifecycle

```text
DESIGNING
→ OWNER_UI_ACCEPTED
→ BASELINE_CAPTURED
→ LOCKED_FOR_INTEGRATION
→ AI_VERIFIED
→ OWNER_ACCEPTED
→ ACCEPTED_BASELINE
```

Conflict path:

```text
LOCKED_FOR_INTEGRATION
→ BASELINE_CONFLICT
→ BASELINE_CHANGE_REQUEST
→ OWNER_APPROVED | OWNER_REJECTED
→ SUPERSEDED_BASELINE | RESUME_ORIGINAL_BASELINE
```

## Required Record

Use `templates/INTEGRATION-BASELINE.md`. Record:

- baseline and Slice IDs;
- UI artifact, route, screenshot set, design file, commit, and hash;
- locked actor surfaces, pages, components, copy, interaction, and states;
- explicitly editable regions;
- Workflow contract and controlled adjustment envelope;
- Simulation version and scenarios;
- Calabash version;
- Owner approval;
- branch/worktree and verification target.

## Controlled Workflow Change

Workflow can change during Integration when the change:

- preserves Owner-approved product meaning;
- does not remove required user capability;
- remains inside the declared adjustment envelope;
- receives impact analysis when it affects prior accepted work;
- updates Calabash and Simulation when product meaning changes.

A material Workflow product decision still belongs to the Owner.

## Violation

Any unapproved change to locked UI produces `BASELINE_LOCK_VIOLATION`.

The candidate is not eligible for AI Verification or Owner Acceptance until the UI is
restored or a superseding baseline is explicitly approved. Passing tests cannot waive a
lock violation.

This applies equally to customer-facing, staff, administrator, notification, audit, and
status surfaces when those surfaces are inside the active Feature Slice.
