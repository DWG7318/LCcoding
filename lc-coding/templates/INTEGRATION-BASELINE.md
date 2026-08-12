# Integration Baseline

- Artifact role: INTEGRATION_BASELINE
- Baseline ID:
- Feature Slice ID / version:
- Feature Slice reference: slices/<Slice ID>.md
- Integration Route ID:
- Integration candidate ID / exact hash:
- Integration candidate provenance: PROJECT_COMMIT:<exact frozen commit>; EVIDENCE:<candidate-id>~<sha256>~<route-id>~<evidence-id>
- Product Baseline identity / frozen commit:
- Primary product mainline ID:
- Applicable UI identity: ID:<UI ID>; PATH:<subtree path>; VERSION:<component semver>; HASH:<sha256>
- Workflow capability identity: WORKFLOW:<Workflow ID>; CAPABILITY:<Workflow Capability ID>
- Selected entry interface: TYPE:<API/MCP>; CAPABILITY:<same Capability ID>; CONTRACT:<Map contract ID>; MAP_EVIDENCE:<Map evidence ID>; INVOCATION:<candidate-id>~<sha256>~<route-id>~<evidence-id>
- Simulation scenario identity: SIMULATION:<Simulation ID>; SCENARIO:<Scenario ID>; VERSION:<scenario semver>
- Connected route evidence: UI_ACTION:<candidate-id>~<sha256>~<route-id>~<evidence-id>; WORKFLOW_RULES:<candidate-id>~<sha256>~<route-id>~<evidence-id>; STATE_TRANSITION:<candidate-id>~<sha256>~<route-id>~<evidence-id>; DATA_EFFECT:<candidate-id>~<sha256>~<route-id>~<evidence-id>; SIDE_EFFECT:<candidate-id>~<sha256>~<route-id>~<evidence-id>; VISIBLE_UI_RESULT:<candidate-id>~<sha256>~<route-id>~<evidence-id>; FAILURE_PATH:<candidate-id>~<sha256>~<route-id>~<evidence-id>; RECOVERY_RESULT:<candidate-id>~<sha256>~<route-id>~<evidence-id>
- Project repository identity:
- Project exact frozen commit SHA:
- Applicable UI subtree ID / path:
- UI component version:
- UI content hash:
- UI content hash scope / manifest evidence:
- Product Handoff identity match: MATCH: evidence / BLOCKED
- Branch / latest accepted: NO
- Locked actor surfaces:
- Lock authority: ONE_WAY_OWNER_AUTHORITY
- System autonomous UI modification: FORBIDDEN
- Owner-initiated / Owner-approved UI change route: BASELINE_CHANGE_REQUEST
- Explicitly editable regions:
- Workflow contract and controlled adjustment boundary:
- Simulation scenario versions:
- Real integration route / evidence:
- Calabash/Product Baseline reference:
- Owner approval:
- Lock time:

This record is the one canonical UI lock for the applicable UI subtree. Its total-project repository/commit plus subtree ID/path/version/hash tuple must match Product Baseline Handoff exactly; a branch, tag, `HEAD`, working tree, screenshot, export, or build artifact is insufficient.
