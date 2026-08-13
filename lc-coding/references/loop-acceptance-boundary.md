# Owner Terminal Decision Boundaries

`SPEC.md` alone defines Owner terminal-decision semantics.

<a id="per-run-terminal-decision"></a>
## Per-Run terminal decision

Source clauses: [LC-ACCEPT-001](../../SPEC.md#lc-accept-001)

Each normal Run follows `D3 PASS` → `LOOP_OWNER_ACCEPTANCE_READY` → its own receipt. Several Runs produce several small decisions; accepted Required Integration Runs may contribute to `ALL_REQUIRED_RUNS_ACCEPTED`.

The Supervisor prepares candidate, scenario, route, D3 evidence, risks, and limits. The Owner judges; the decision does not repeat valid technical checks. A Verifier or Supervisor never substitutes its verdict for `LOOP_OWNER_ACCEPTED`, rework, definition change, or defer. `RUN-HANDOFF.md` is start input; `LOOP-OWNER-ACCEPTANCE.md` is terminal and never advances the calling-phase gate.

<a id="owner-gap-lineage"></a>
## Owner gap lineage

Source clauses: [LC-ACCEPT-002](../../SPEC.md#lc-accept-002)

Rework, definition change, or defer gets one stable Owner gap ID. Definition change returns through Calabash; other correction follows the Impact/Run route. Keep candidate, scenario, correction, re-verification, and re-acceptance lineage in existing artifacts. `status.json` only indexes open gaps and evidence pointers. Close only after affected evidence and the new Owner decision are current.

<a id="post-security-terminal-decision"></a>
## Post-Security terminal decision

Source clauses: [LC-ACCEPT-003](../../SPEC.md#lc-accept-003)

After `VULNERABILITY_CLOSED`, Post-Security Owner Acceptance judges the current remediated candidate. It reuses current Loop Owner Acceptance receipts and reviews affected product surfaces, final identity, closure, and critical smoke; it does not repeat unchanged acceptance.

This differs from each Per-Run decision. Delivery stays blocked until the current candidate is `POST_SECURITY_OWNER_ACCEPTED`; its terminal record is `POST-SECURITY-OWNER-ACCEPTANCE.md`.
