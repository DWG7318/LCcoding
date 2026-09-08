# Real User Journey Acceptance

## Candidate identity

- Acceptance ID: <RUJA-ID>
- Project ID: <PROJECT-ID>
- Candidate ID: <CANDIDATE-ID>
- Candidate SHA-256: <lowercase-sha256>
- Repository / commit: <repository> / <40-char-lowercase-commit>
- Status schema version: <3.0.0-or-4.0.0>
- Service Route Map ID / exact hash: <map-id> / sha256:<lowercase-sha256> (required only for 4.0.0)

## Acceptance environment and viewport

- Environment ID / version: <ENVIRONMENT-ID> / <version>
- Product entry URL or location: <HOME-PAGE-OR-PRODUCT-ENTRY>
- Browser / surface: <BROWSER-OR-VISIBLE-SURFACE>
- Viewport width × height / DPR: <width> × <height> / <dpr>
- Owner viewport-only assistance: NOT_REQUIRED / RIGHT_PANEL_FULL_WIDTH_AND_F11
- Test actor and safe-data set: <ACTOR-ID> / <SAFE-DATA-ID>

## Journey coverage

| Journey ID | Actor / permission | Start | Preconditions / safe data | Ordered visible actions | Expected visible results / outcome | Exception / recovery routes | Calabash / Simulation / Workflow / UI / Slice / Run trace | Applicability |
|---|---|---|---|---|---|---|---|---|
| JOURNEY-001 | <actor / permission> | <home page or product entry> | <preconditions / data> | <Step IDs> | <results / outcome> | <routes> | <trace> | REQUIRED / NOT_APPLICABLE |

## Acceptance rounds

| Round | Candidate ID / SHA-256 | Started from home entry | Required / passed / failed / N/A | First and last evidence | Defect IDs | Result |
|---|---|---|---|---|---|---|
| 1 | <candidate-id> / <sha256> | YES | <n> / <n> / <n> / <n> | <evidence refs> | NONE / 40001,... | PASS / REWORK / BLOCKED |

Every post-repair round starts again from the home page or defined product entry and executes the complete required journey graph. Earlier-round screenshots remain history and are not current-round PASS evidence.

## Evidence digests

| Round | Journey ID | Step ID | Action | Expected / observed visible result | Visible location | Viewport | Screenshot path | Screenshot SHA-256 | Result |
|---|---|---|---|---|---|---|---|---|---|
| 1 | JOURNEY-001 | STEP-001 | <meaningful visible action> | <expected / observed> | <URL or visible location> | <width>x<height>@<dpr> | .lccoding/evidence/real-user-journey/round-001/JOURNEY-001/STEP-001.png | <lowercase-sha256> | PASS / DEFECT / BLOCKED_BY_DEFECT / NOT_APPLICABLE |

The two tables above are the exact `3.0.0` browser baseline. A `3.0.0` record keeps screenshot evidence after every meaningful visible action and does not use the 4.0 tables below.

## Route-faithful 4.0 journey coverage

For `4.0.0`, use this table instead of the browser-only Journey coverage table. Include exactly every `REQUIRED` + `DELIVERED` route in the adopted Service Route Map. Counts in the status summary and acceptance rounds count these journey-route requirements. `DIRECT_PRODUCT`, `PERSONAL_AGENT`, and `SERVICE_CENTER` remain route kinds, not new phases.

| Journey ID | Service Route ID | Route kind | Actor ID / kind | Authority action / resource / delegation | Actual external entry | Expected human-observable outcome | Adopted acceptance evidence IDs | Applicability |
|---|---|---|---|---|---|---|---|---|
| JOURNEY-001 | <route-id> | DIRECT_PRODUCT / PERSONAL_AGENT / SERVICE_CENTER | <actor-id> / <actor-kind> | <action-id> / <resource-id> / <delegation-basis-id-or-NOT_APPLICABLE> | <real route entry> | <outcome understandable by the human beneficiary> | <comma-separated exact adopted IDs> | REQUIRED |

For a 4.0 acceptance round, replace the browser round table with the following route-round shape. A complete round starts from every actual required route entry, covers the exact candidate, and executes the complete adopted required-and-delivered route graph after correction.

| Round | Candidate ID / SHA-256 | Started from every actual route entry | Required routes / passed / failed | First and last evidence | Defect IDs | Result |
|---|---|---|---|---|---|---|
| 1 | <candidate-id> / <sha256> | YES | <n> / <n> / <n> | <evidence IDs> | NONE / 40001,... | PASS / REWORK / BLOCKED |

## Route-faithful 4.0 evidence digests

For a meaningful `VISIBLE` step, use `SCREENSHOT`; the referenced file remains under `.lccoding/evidence/real-user-journey/`, contains actual image bytes, and has its exact SHA-256. For a `NONVISUAL` step, do not fabricate or copy a screenshot. Resolve the native first-hand message, task, receipt, artifact, authorization, audit, platform-effect, or result-delivery evidence at its existing safe path inside `.lccoding` and record its exact hash; the candidate-bound round and route row provide the acceptance identity without introducing a second evidence protocol. Personal-Agent coverage includes human-goal/request messages, Agent identity, task transition, authorization, result artifact, platform effect, Agent response, applicable audit events, result delivery, and the final human-observable outcome. Service-Center coverage includes the user request, service actor identity, delegation basis, assisted action, platform effect, user communication, applicable audit events, result delivery, and final human-observable outcome.

| Round | Journey ID | Service Route ID | Route kind | Step ID | Evidence ID | Step mode | Evidence kind | Actor ID | Authority action ID | Delegation basis ID | Audit event ID | Expected / observed route result | Evidence path | Evidence SHA-256 | Human-observable outcome | Result |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | JOURNEY-001 | <route-id> | DIRECT_PRODUCT / PERSONAL_AGENT / SERVICE_CENTER | STEP-001 | <stable-evidence-id> | VISIBLE / NONVISUAL | SCREENSHOT / HUMAN_GOAL_MESSAGE / AGENT_IDENTITY / REQUEST_MESSAGE / TASK_TRANSITION / AUTHORIZATION_DECISION / RESULT_ARTIFACT / PLATFORM_EFFECT / AGENT_RESPONSE / AUDIT_EVENT / RESULT_DELIVERY / USER_REQUEST / SERVICE_ACTOR_IDENTITY / DELEGATION_BASIS / ASSISTED_ACTION / USER_COMMUNICATION | <actor-id> | <action-id> | <delegation-id-or-NOT_APPLICABLE> | <audit-id-or-NOT_APPLICABLE> | <expected / observed> | <screenshot project path or existing safe .lccoding-relative native evidence path> | <lowercase-sha256> | NOT_APPLICABLE / <exact adopted human outcome> | PASS / DEFECT / BLOCKED_BY_DEFECT |

## Defect pointers

- Defect log reference: REAL-USER-JOURNEY-DEFECT-LOG.md
- Open defect IDs: NONE
- Fixed and verified defect IDs: NONE
- Owner-exempted defect IDs: NONE
- Deferred defect IDs: NONE
- Reopened defect IDs: NONE

## Recommendation and Owner result

- Agent recommendation: ACCEPT / REWORK / DEFER
- Recommendation evidence: <round and defect summary>
- Owner result: REAL_USER_JOURNEY_ACCEPTED / REAL_USER_JOURNEY_REWORK / REAL_USER_JOURNEY_DEFERRED / PENDING
- Owner decision evidence: <OWNER-EVIDENCE-ID>
- Accepted candidate ID / SHA-256: <candidate-id> / <sha256>

## Invalidation history

| Event ID | Changed candidate / surface | Impact result | Reused journeys | Rerun journeys | Complete-round required | Current acceptance state |
|---|---|---|---|---|---|---|
| <EVENT-ID> | <candidate / surface> | UNAFFECTED / AFFECTED / BROAD_OR_UNKNOWN | <Journey IDs> | <Journey IDs> | YES / NO | CURRENT / INVALIDATED |
