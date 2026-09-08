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

For `4.0.0`, use the table below instead. The normal order remains user-experience-first: `USER_SERVICE_BOUNDARY -> WORKFLOW_ORCHESTRATION -> BACKEND_CORE`. Boundary evidence identifies the concrete route surface as `UI / AGENT_SERVICE / ASSISTED_SERVICE`; a direct route uses UI, while a Personal-Agent or Service-Center route uses its Agent/assisted surface or the human-facing UI where the defect was observed. Scheduled repairs follow that layer order. An intentional inversion records a meaningful `Priority exception justification` with its decision identity and rationale; it is not a new hard stop or a change to phase/runtime design.

| Defect ID | Discovery time / candidate / round / Journey / Route / Step | Evidence ID / kind / SHA-256 | Expected / observed | Severity / reachability / blocking scope | Affected layer / root cause | Boundary surface / evidence | Affected routes | Repair sequence | Priority exception justification | Correction identity / engineering re-verification | Retest round | Retest evidence ID / kind / SHA-256 | State | Exemption authority / impact / recovery |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 40001 | <timestamp> / <candidate> / <round> / <Journey> / <route> / <Step> | <evidence-id> / <evidence-kind> / <lowercase-sha256> | <expected / observed> | <severity / reachability / scope> | <USER_SERVICE_BOUNDARY-or-WORKFLOW_ORCHESTRATION-or-BACKEND_CORE> / <root cause> | <UI-or-AGENT_SERVICE-or-ASSISTED_SERVICE> / <evidence-id>, or NOT_APPLICABLE | <route IDs> | <positive integer> | NOT_APPLICABLE / <decision-id: rationale> | <change or Run> / <D0-D3 or other evidence> | <later round or NOT_APPLICABLE> | <evidence-id / kind / SHA-256 or NOT_APPLICABLE> | OPEN / FIXED_VERIFIED / OWNER_EXEMPTED / DEFERRED / MERGED_INTO / REOPENED | NOT_APPLICABLE or <Owner authority / impact / recovery condition> |

## State history

| Defect ID | Event time | Prior state | New state | Candidate ID / SHA-256 | Evidence / reason |
|---|---|---|---|---|---|
| 40001 | <timestamp> | OPEN | <new state> | <candidate-id> / <sha256> | <evidence / reason> |

Every discovery tuple—candidate, round, journey, route, step, evidence ID, evidence kind, and hash—joins one actual first-hand `DEFECT` or `BLOCKED_BY_DEFECT` evidence row/file. Every 4.0 defect has complete append-only state history beginning `NOT_APPLICABLE -> OPEN` and ending at the current register state. `FIXED_VERIFIED` cites an actual later-round passing retest row/file.

`OWNER_EXEMPTED` cites an exact-hash JSON project record with `record_role: REAL_USER_JOURNEY_DEFECT_EXEMPTION`, schema `4.0.0`, evidence and defect IDs, candidate ID/hash, route ID, Owner authority, human impact, recovery condition, and decision. The record binds the exemption history without defining an external runtime protocol.
