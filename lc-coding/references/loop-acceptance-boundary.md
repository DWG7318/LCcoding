# Loop Owner Acceptance Boundary

## Incremental acceptance belongs inside the Loop

Every normal SLK, CLK, or GLK Run completes through:

```text
D3 PASS
  ↓
LOOP_OWNER_ACCEPTANCE_READY
  ↓
Supervisor-guided Loop Owner Acceptance
  ↓
LOOP_OWNER_ACCEPTED or routed rework/change
```

This acceptance must not be replaced by one large LCCoding acceptance at the end of several Runs.

A Feature Slice with multiple Runs therefore produces multiple small Owner Acceptance receipts. This keeps Owner workload bounded and product direction visible throughout construction.

## Supervisor duty

The Loop Supervisor prepares:

- exact candidate identity;
- entry, account, role, and scenario;
- concise acceptance steps;
- visible product questions;
- D3 receipt and invisible risks already verified;
- known limitations and product-learning route.

The Owner judges the product result. The Owner is not asked to repeat technical checks already covered by valid receipts.

## Accepted aggregate

Only after every required normal Run has `LOOP_OWNER_ACCEPTED` may LCCoding issue:

```text
ALL_REQUIRED_RUNS_ACCEPTED
```

This aggregate accepted candidate then enters the centralized vulnerability audit.

## Security remediation exception

Security remediation Runs are technical correction Runs created after the centralized audit. Their human acceptance is intentionally consolidated into the one `POST_SECURITY_OWNER_ACCEPTANCE`, because the Security Auditor independently re-verifies the fixes and the Owner should review the combined product delta once, not every vulnerability fix separately.
