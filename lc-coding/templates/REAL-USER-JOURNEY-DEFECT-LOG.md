# Real User Journey Defect Log

This is the append-only Phase-4 defect history for one project. The first legal defect ID is `40001`. IDs increase monotonically and are never recycled after rejection, merge, defer, exemption, reopening, or shared-root-cause discovery.

- Status schema version: 3.0.0 / 4.0.0
- Normal repair priority: USER_SERVICE_BOUNDARY -> WORKFLOW_ORCHESTRATION -> BACKEND_CORE

## Defect register

| Defect ID | Discovery time / candidate / round / Journey / Step | Screenshot SHA-256 | Expected / observed | Severity / reachability / blocking scope | Visible layer / root cause | Affected surfaces | Correction identity / engineering re-verification | Retest round | State | Exemption authority / impact / recovery |
|---|---|---|---|---|---|---|---|---|---|---|
| 40001 | <timestamp> / <candidate> / <round> / <Journey> / <Step> | <lowercase-sha256> | <expected / observed> | <severity / reachability / scope> | UI / WORKFLOW / BACKEND_CORE / <root cause> | <surfaces> | <change or Run> / <D0-D3 or other evidence> | <round> | OPEN / FIXED_VERIFIED / OWNER_EXEMPTED / DEFERRED / MERGED_INTO / REOPENED | NOT_APPLICABLE or <Owner evidence / impact / recovery condition> |

The table above remains the exact `3.0.0` browser defect shape and preserves its `UI -> WORKFLOW -> BACKEND_CORE` repair priority.

## Route-faithful defect register

For `4.0.0`, use the table below instead. The normal order remains user-experience-first: `USER_SERVICE_BOUNDARY -> WORKFLOW_ORCHESTRATION -> BACKEND_CORE`. Boundary evidence identifies the concrete route surface as `UI / AGENT_SERVICE / ASSISTED_SERVICE`; a direct route uses UI, while a Personal-Agent or Service-Center route uses its Agent/assisted surface or the human-facing UI where the defect was observed. A coherent root cause may still justify one cross-layer correction, but it does not weaken the normal repair priority.

| Defect ID | Discovery time / candidate / round / Journey / Route / Step | Evidence ID / kind / SHA-256 | Expected / observed | Severity / reachability / blocking scope | Affected layer / root cause | Boundary surface / evidence | Affected routes | Correction identity / engineering re-verification | Retest round | State | Exemption authority / impact / recovery |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 40001 | <timestamp> / <candidate> / <round> / <Journey> / <route> / <Step> | <evidence-id> / <evidence-kind> / <lowercase-sha256> | <expected / observed> | <severity / reachability / scope> | <USER_SERVICE_BOUNDARY-or-WORKFLOW_ORCHESTRATION-or-BACKEND_CORE> / <root cause> | <UI-or-AGENT_SERVICE-or-ASSISTED_SERVICE> / <evidence-id>, or NOT_APPLICABLE | <route IDs> | <change or Run> / <D0-D3 or other evidence> | <round> | OPEN / FIXED_VERIFIED / OWNER_EXEMPTED / DEFERRED / MERGED_INTO / REOPENED | NOT_APPLICABLE or <Owner evidence / impact / recovery condition> |

## State history

| Defect ID | Event time | Prior state | New state | Candidate ID / SHA-256 | Evidence / reason |
|---|---|---|---|---|---|
| 40001 | <timestamp> | OPEN | <new state> | <candidate-id> / <sha256> | <evidence / reason> |

Every 4.0 defect has complete append-only state history beginning `NOT_APPLICABLE -> OPEN` and ending at the current register state. Owner exemption retains explicit authority, human impact, and recovery condition; correction retains its identity and a later complete-round retest.
