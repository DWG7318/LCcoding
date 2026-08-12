# Run Start Contract

- Artifact role: RUN_START_CONTRACT
- Start Contract ID:
- Start Contract SHA-256:
- Run ID:
- LCCoding phase scope: INITIAL / PRODUCT_FORMATION / ENGINEERING_RUNS / DELIVERY_PREPARATION
- Phase-owned objective:
- Calling phase authority / contract reference(s):
- Frozen Run scope:
- Explicit exclusions:
- Selected execution method ID:
- Selected execution method version:
- Selected execution method exact hash:
- Selected execution method canonical interface / contract reference:
- Phase-appropriate input evidence / prerequisites:
- Product Baseline trace (ENGINEERING_RUNS only):
- Feature Slice ID / version (ENGINEERING_RUNS only):
- Applicable UI / Integration Baseline (ENGINEERING_RUNS only):
- Evidence return target in calling phase:
- D0-D3 evidence / verification condition:
- Loop Owner Acceptance condition / route:
- Risk / depth decision:
- Readiness result: READY / BLOCKED
- Blocker evidence:

The `Start Contract SHA-256` freezes this contract's canonical UTF-8 bytes with that field's value empty, before the digest is inserted. The terminal receipt must repeat the resulting contract ID and digest exactly. Omit the three `ENGINEERING_RUNS only` fields for Runs called by another phase; cite that phase's own source contracts under phase-appropriate inputs instead. `READY` requires no blocker (`NONE`); `BLOCKED` requires specific blocker evidence. This contract records future D0-D3 and Owner-acceptance conditions only; completing a Run returns evidence and never advances its calling phase by itself.
