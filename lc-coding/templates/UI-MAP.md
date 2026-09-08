# UI Map

For EXISTING intake, runnable UI is the first Owner-visible cognition anchor, not completion evidence. Record observed behavior and trace every visible entry to Workflow and independent evidence for invisible behavior.

- Primary product mainline ID:

| UI ID | Subtree path | Component version | Content hash | Actor | Surface / state | Actions / feedback | Workflow subtree references | Simulation subtree references | Evidence / attestation | Lock status | Primary mainline | UI change authority | Baseline Change Request |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

UI relationships are closed, reciprocal peer-subtree ID references. They allow many-to-many Workflow and Simulation relations but never encode directory nesting. Every realized UI is a safe non-root logical path in the one total project repository. Component version uses `MAJOR.MINOR.PATCH`; Primary mainline is exactly `YES` or `NO`. UI change authority is exactly `OWNER_ONLY`; Baseline Change Request is `NONE` for an unchanged lock or `<Request ID> / <contained BCR path>` for an Owner-governed change.

## 4.0 service surface trace

| Service Route ID | Service Surface ID | Service Surface Kind | Workflow Capability ID |
|---|---|---|---|

Allowed kinds are `DIRECT_PRODUCT`, `AGENT_SERVICE`, `HUMAN_RESULT_CONSENT_EXCEPTION`, and `ASSISTED_SERVICE`. A direct route records only `DIRECT_PRODUCT`; a Personal Agent route records `AGENT_SERVICE` plus `HUMAN_RESULT_CONSENT_EXCEPTION`; and a Service Center route records `ASSISTED_SERVICE` plus `HUMAN_RESULT_CONSENT_EXCEPTION`. Direct and human result surfaces cite their realized UI IDs; Agent or assisted-service surfaces do not become artificial UI merely because their route identities are traced here.
