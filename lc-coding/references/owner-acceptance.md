# Owner Acceptance

LCCoding uses two distinct Owner Acceptance boundaries.

## 1. Loop Owner Acceptance

- owned by the selected SLK, CLK, or GLK Run;
- occurs after that Run's D3;
- incremental and mandatory for every normal product Run;
- keeps Owner review small and continuous;
- produces `LOOP_OWNER_ACCEPTANCE_RECEIPT`.

## 2. Post-Security Owner Acceptance

Occurs only after:

```text
ALL_REQUIRED_RUNS_ACCEPTED
→ centralized independent vulnerability audit
→ security remediation
→ Security Auditor re-audit
→ VULNERABILITY_CLOSED
```

It is not a repeat of every Loop acceptance. It reuses all Loop Owner Acceptance receipts and checks:

- UI/Workflow surfaces changed by security remediation;
- affected Feature Slice behavior;
- critical end-to-end smoke route;
- final candidate identity;
- security closure status and remaining disclosed limits.

If the security audit caused no candidate change, the Owner performs a minimal candidate-identity and critical-route confirmation.

Valid results:

```text
POST_SECURITY_OWNER_ACCEPTED
POST_SECURITY_PRODUCT_REWORK
POST_SECURITY_OWNER_DEFERRED
```

Delivery Method Q&A cannot begin until `POST_SECURITY_OWNER_ACCEPTED`.
