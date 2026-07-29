# Verification De-duplication

## Distinct engineering questions

| Layer | Question | New evidence |
|---|---|---|
| D0 | Did the implementation behave as intended locally? | focused implementation evidence |
| D1 | Does this CELL satisfy its local frozen contract? | independent boundary and local acceptance |
| D2 | Do accepted CELLs compose into the GO outcome? | GO composition, outcome, affected regression |
| D3 | Do verified results compose into the Run/Stage/Final claim? | seams, end-to-end, locked UI, invisible system behavior |

## Independence

- D1 is independent from Worker production context.
- D2 is independent from Worker and CELL Checker.
- D3 uses the fresh independent topology required by the selected Loop.
- The Run Supervisor provisions and consumes Verification but cannot author its verdict.

## Receipt reuse

A higher layer cites lower receipts and does not rerun their commands when candidate identity, contract, environment, authority, and evidence remain valid.

Repeat only for changed candidate, stale/contradictory evidence, material environment difference, composition-sensitive result, expanded affected regression, or a named risk.

## Owner acceptance reuse

- Every normal Run has its own Loop Owner Acceptance after D3.
- A later Run must not ask the Owner to reaccept unchanged prior Runs.
- Post-Security Owner Acceptance reuses all Loop Owner Acceptance receipts and checks only remediation-affected product surfaces plus critical smoke paths.

## Centralized security

Formal vulnerability audit is not distributed across D0–D3. Local security checks may be reused, but only the independent centralized Security Auditor may issue the final vulnerability closure verdict.
