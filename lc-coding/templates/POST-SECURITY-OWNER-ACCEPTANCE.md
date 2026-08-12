# Post-Security Owner Acceptance

- Schema version: 2.7.0
- Artifact role: POST_SECURITY_OWNER_ACCEPTANCE_RECEIPT
- Acceptance ID:
- Candidate ID / exact hash:
- Vulnerability Closure Receipt ID / reference:
- Vulnerability Closure candidate ID / exact hash:
- Covered remediation surface IDs: NONE
- Changed remediation surface IDs: NONE
- Reused Loop Owner Acceptance Receipt IDs:
- Security Remediation Run IDs: NONE
- Critical smoke / delta evidence:
- Owner result: POST_SECURITY_OWNER_ACCEPTED / POST_SECURITY_PRODUCT_REWORK / POST_SECURITY_OWNER_DEFERRED
- Supersession status: CURRENT
- Superseded by Acceptance ID / reference: NOT_APPLICABLE
- Accepted at:

This terminal receipt binds one exact candidate and its exact Vulnerability Closure. Later invalidation or supersession is recorded only in authoritative `status.json` and the new Impact Analysis; this receipt remains `CURRENT` immutable evidence for the candidate it accepted. Reused acceptance, remediation Run, and critical smoke/delta fields use closed `ID@CANDIDATE_ID@sha256:<64 lowercase hex>@SURFACE_ID[+SURFACE_ID...]` records separated by `;`; remediation Run records append `@EVIDENCE_ID`.
