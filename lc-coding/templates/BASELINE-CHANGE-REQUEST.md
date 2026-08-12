# Baseline Change Request

- Artifact role: UI_BASELINE_CHANGE_REQUEST
- Request ID:
- Locked Integration Baseline ID:
- Requested UI change:
- Change authority: OWNER_INITIATED / OWNER_APPROVED
- Necessity / impact record:
- Prior accepted work affected:
- Owner decision / approval evidence:
- Project repository identity:
- Prior project commit SHA:
- New project commit SHA:
- New project commit differs from prior lock: YES
- Prior UI identity: REPOSITORY:<total repository>; COMMIT:<prior exact commit>; ID:<UI ID>; PATH:<subtree path>; VERSION:<semver>; HASH:<sha256>
- New UI identity: REPOSITORY:<same total repository>; COMMIT:<new exact commit>; ID:<UI ID>; PATH:<subtree path>; VERSION:<semver>; HASH:<sha256>
- Product Baseline Handoff update: REPOSITORY:<same total repository>; COMMIT:<new exact commit>; ID:<UI ID>; PATH:<subtree path>; VERSION:<semver>; HASH:<sha256>
- Integration Baseline update: REPOSITORY:<same total repository>; COMMIT:<new exact commit>; ID:<UI ID>; PATH:<subtree path>; VERSION:<semver>; HASH:<sha256>
- Affected evidence set:
- Affected evidence invalidation: <affected-link>:<candidate-id>~<sha256>~<route-id>~<invalidation-evidence-id>; <one exact record per affected link>
- Affected evidence re-verification: <affected-link>:<candidate-id>~<sha256>~<route-id>~<current connected-route evidence-id>; <one exact record per affected link>
- Unaffected evidence reuse basis: CANDIDATE:<Candidate ID / exact sha256>; ROUTE:<Route ID>; LINKS:<closed unchanged link IDs>; SCOPE:<candidate-id>~<sha256>~<route-id>~<evidence-id>; REASON:UNCHANGED_EQUIVALENT
- Preservation route: PRESERVE_HISTORY_NO_SILENT_OVERWRITE_NO_AUTOMATIC_RESTORE
- New baseline version:

The request remains evidence only. It cannot mutate or restore files. The prior commit must be a Git ancestor of the distinct new commit in the same total repository; both identities name the same UI ID/path, and the new frozen subtree hash and component version must actually advance. `New baseline version` equals that new UI component version. The current UI Map, Product Baseline Handoff, and Integration Baseline must already converge on this tuple. Both affected-evidence records contain exactly one candidate/full-hash/route-bound entry for every link in `Affected evidence set`; re-verification equals the current connected-route evidence for that link, while invalidation is distinct.
