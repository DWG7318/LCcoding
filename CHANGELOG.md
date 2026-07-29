# Changelog

## 2.0.0

### Preserved

- Calabash / Workflow / UI three-layer product structure.
- Simulation World.
- Mandatory Calabash Upgrade and Product Baseline.
- Feature Slice and UI-locked Integration.
- SLK / CLK / GLK Loop Engineering.
- Independent Verification and Owner Acceptance.
- Protected Delivery.

### Simplified

- One canonical definition per concept.
- Proposal questions are asked only for real gaps.
- Initialization and canonical checks rerun only on change.
- Workflow/UI/Simulation share scenario identifiers.
- One Impact Analysis is updated by delta.
- Feature Slice definition is referenced rather than copied.
- Verification receipts are inherited upward.
- Final Feature Verification tests only new composition risk.
- Owner Acceptance reuses the accepted candidate and scenarios.
- Delivery reuses product Verification and checks only package deltas.

### Added to the complete repository

- Proposal Readiness templates and checker.
- Project bootstrap, capability manifest, Agents Rule, Fingerprint, Health, and Interpretation Lock.
- Full integration-lock and delivery-governance templates.
- Verification receipt contract and anti-duplication validator.
- Repository and project validation scripts.
- Enterprise example and GitHub Actions validation.

### Final phase and closure refinement

- Added a four-phase overlay without changing the mainline.
- Unified human product acceptance at LCCoding Owner Acceptance; Loop methods now hand off rather than duplicate acceptance.
- Added non-duplicative Vulnerability Detection and Closure before Owner Acceptance.
- Added mandatory customer-specific Delivery Method Q&A; defaults are recommendations rather than silent delivery choices.
- Added phase, vulnerability, delivery-decision contracts, templates, guards, and tests.
### Acceptance and security boundary correction

- Restored incremental Owner Acceptance inside every normal SLK/CLK/GLK Run.
- Removed the incorrect single late aggregate acceptance model.
- Moved formal vulnerability audit after all normal Loop Owner Acceptances.
- Required one fresh independent Security Auditor Agent.
- Separated audit from remediation implementation.
- Added Post-Security Owner Acceptance as a focused delta acceptance before Delivery.
