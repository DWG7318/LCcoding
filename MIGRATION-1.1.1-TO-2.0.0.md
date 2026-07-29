# Migration from 1.1.1 to 2.0.0

## Method continuity

The core method is not replaced. Existing Calabash, Workflow Map, UI Map, Simulation World, Feature Slice, integration lock, impact analysis, verification, and Owner Acceptance records remain valid when their identities and contracts are current.

## Required migration

1. Record the current Owner Policy and Project Profile.
2. Confirm repository visibility and version policy.
3. Generate or update the platform-specific Agents Rule.
4. Lock LCCoding, Calabash, SLK, CLK, and GLK versions/hashes.
5. Convert duplicated proposal questions into one PRC record.
6. Confirm Calabash Draft and Product Baseline are distinct.
7. Confirm Workflow, UI, and Simulation remain distinct LCCoding layers.
8. Add or refresh Mandatory Calabash Upgrade receipt.
9. Make each Feature Slice contract canonical; replace copied definitions with references.
10. Add Integration Baseline and UI lock to active Slices.
11. Convert repeated impact reports into one analysis plus deltas.
12. Convert verification outputs to D0/D1/D2/D3 receipts with evidence inheritance.
13. Add Supervisor-guided Owner Acceptance packet.
14. Classify internal dependencies and create Delivery rules.
15. Run repository and project validators.

## Do not migrate by

- swallowing Workflow/UI/Simulation into Calabash;
- treating LCCoding as only a Loop selector;
- removing independent Verification;
- converting every check into a full regression suite;
- exposing LC internal assets in customer delivery.


## Phase and closure normalization

- Group the unchanged mainline into INITIAL, PRODUCT_FORMATION, ENGINEERING_RUNS, and DELIVERY_PREPARATION.
- Preserve Loop Owner Acceptance inside every normal SLK/CLK/GLK Run; do not convert it into an Acceptance Handoff or one late aggregate acceptance.
- Require Vulnerability Closure before the distinct Post-Security Owner Acceptance.
- Require customer-specific Delivery Method Q&A before packaging and Delivery.
## Acceptance and security correction

Legacy or draft 2.0.0 artifacts that normalize Loop Human Acceptance into a Handoff must be migrated. Every normal SLK/CLK/GLK Run retains its Owner Acceptance. Formal vulnerability audit moves after all required normal Runs are Owner-accepted, uses an independent Security Auditor, and is followed by Post-Security Owner Acceptance.
