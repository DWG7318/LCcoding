# Verification Evidence and Reuse

`SPEC.md` alone defines layered verification semantics.

<a id="layered-independent-verification"></a>
## Layered independent verification

Source clauses: [LC-VERIFY-001](../../SPEC.md#lc-verify-001)

D0 is Worker self-check; D1 independently checks the frozen CELL; D2 composes accepted CELL evidence into the GO outcome; fresh D3 verifies Stage/Run/Final seams, end-to-end behavior, locked UI, invisible behavior, and final candidate. Each depth asks a new engineering question. Worker, Checker, and Run Supervisor cannot author assigned higher verdicts.

<a id="receipt-reuse"></a>
## Receipt reuse

Source clauses: [LC-VERIFY-001](../../SPEC.md#lc-verify-001)

Reuse only when candidate identity, contract version, relevant environment, authority, currency/completeness, and no contradiction still match. Repeat for a changed candidate, stale/missing/contradictory evidence, material environment change, composition risk, affected regression, or named risk. Record source, reason, scope difference, risk, and result; rerun affected proof, not unchanged work.

<a id="acceptance-handoff-boundary"></a>
## Acceptance handoff boundary

Source clauses: [LC-VERIFY-001](../../SPEC.md#lc-verify-001)

A D3 receipt is engineering evidence for the Owner decision. A Verifier or Supervisor cannot author Owner result, and an Owner terminal receipt is not a D0–D3 technical verdict. Run-start input, verification evidence, and terminal acceptance remain distinct. Local security evidence may be reused, but it does not replace the centralized security verdict.
