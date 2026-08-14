# Run Start Contract

- Artifact role: RUN_START_CONTRACT
- Start Contract ID:
- Start Contract SHA-256:
- Run ID:
- Status schema version: 2.8.0
- LCCoding phase scope: INITIAL / PRODUCT_FORMATION / REAL_PRODUCT_INTEGRATION / DELIVERY_PREPARATION
- Phase-owned objective:
- Calling phase authority / contract reference(s):
- Frozen Run scope:
- Explicit exclusions:
- Selected execution method ID:
- Selected execution method version:
- Selected execution method exact hash:
- Selected execution method canonical interface / contract reference:
- Phase-appropriate input evidence / prerequisites:
- Meaning impact classification: MEANING_CHANGING / MEANING_NEUTRAL
- Definition basis / neutral Impact Analysis reference:
- Applicable Snake / Scorpion disposition evidence reference:
- Product Baseline trace (REAL_PRODUCT_INTEGRATION only):
- Feature Slice ID / version (REAL_PRODUCT_INTEGRATION only):
- Applicable UI / Integration Baseline (REAL_PRODUCT_INTEGRATION only):
- Evidence return target in calling phase:
- D0-D3 evidence / verification condition:
- Loop Owner Acceptance condition / route:
- Risk / depth decision:
- Readiness result: READY / BLOCKED
- Blocker evidence:

The `Start Contract SHA-256` freezes this contract's canonical UTF-8 bytes with that field's value empty, before the digest is inserted. The terminal receipt must repeat the resulting contract ID, digest, status schema, and phase identity exactly. Omit the three `REAL_PRODUCT_INTEGRATION only` fields for Runs called by another phase; cite that phase's own source contracts under phase-appropriate inputs instead. Meaning-changing work cites a valid current Definition Handoff and governed update route through its Impact Analysis. Meaning-neutral work cites validated phase/evidence rationale and must not fabricate a Definition Baseline. The Snake/Scorpion field cites disposition evidence without reconstructing those dimensions. `READY` requires no blocker (`NONE`); `BLOCKED` requires specific blocker evidence. This contract records future D0-D3 and Owner-acceptance conditions only; completing a Run returns evidence and never advances its calling phase by itself.
