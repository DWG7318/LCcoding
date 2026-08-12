# Impact Analysis

- Analysis ID / version:
- Trigger / proposed change:
- Artifact role: IMPACT_ANALYSIS
- Meaning impact classification: MEANING_CHANGING / MEANING_NEUTRAL
- Calling phase contract / authority:
- Neutral rationale / evidence:
- Definition Baseline ID / exact hash:
- Affected Definition clause references:
- Definition invalidation effect: INVALIDATES / NO_DEFINITION_INVALIDATION
- Governed Calabash update route / Owner authority:
- Snake / Scorpion applicability and effect references:
- Owner Gap IDs / source Acceptance (if applicable):
- Baseline and Slice:
- Affected Calabash:
- Affected Workflow:
- Affected UI:
- Affected Simulation scenarios:
- Affected shared capabilities / data / APIs:
- Affected accepted Slices / Runs / evidence:
- Existing evidence reused / unknown / contradicted:
- Fingerprint complexity and proportional-depth response:
- Regression scope:
- Release / rollback:
- Delta history:
- Gap closure evidence pointers:
- Owner decision:
- Security change timing: BEFORE_SECURITY_CLOSURE / AFTER_VULNERABILITY_CLOSED / AFTER_POST_SECURITY_OWNER_ACCEPTED
- Prior candidate ID / exact hash:
- Current candidate ID / exact hash:
- Security change classification: MATERIAL_SECURITY_SURFACE_CHANGE / PROVEN_SECURITY_SURFACE_NEUTRAL / EVIDENCE_EQUIVALENT_PACKAGING_TRANSFORMATION
- Changed security surface categories: NONE
- Affected security surface IDs: NONE
- Transitive affected surface IDs / evidence: NONE
- Prior Vulnerability Closure Receipt ID / reference: NOT_APPLICABLE
- Prior Post-Security Owner Acceptance ID / reference: NOT_APPLICABLE
- Security neutral / preservation evidence: NOT_APPLICABLE
- Security invalidation evidence: NOT_APPLICABLE
- Required security action: PRESERVE_EXACT_CLOSURE / INVALIDATE_AND_RETURN_TO_AUDIT
- Impact result: PASS / BLOCKED

`MEANING_CHANGING` cites the current Calabash Definition Baseline, affected clauses, invalidation effect, and `CALABASH_UPDATE / OWNER`. `MEANING_NEUTRAL` cites phase authority and evidence-backed neutral rationale, records `NONE` for Definition identity/clauses, `NO_DEFINITION_INVALIDATION`, and `NOT_APPLICABLE` for the update route. Meaning-neutral work must not fabricate a Definition Baseline.

The security delta group is closed whenever any of its fields is used. A post-closure material security-surface change records the distinct exact candidates, affected surfaces, transitive evidence, superseded receipts, and `INVALIDATE_AND_RETURN_TO_AUDIT`. Preservation is never implicit: it requires either exact unchanged security identity with neutral evidence or an exact packaging transformation plus security-equivalence evidence.
