# Product Baseline Handoff

- Baseline ID / version / hash:
- Project repository identity:
- Project frozen exact commit SHA:
- Calabash Definition Handoff ID / exact hash:
- Calabash Definition Handoff result: PASS
- Workflow Map:
- UI Map:
- Simulation World:
- Primary product mainline ID:
- Primary mainline Owner confirmation: OWNER_CONFIRMED: evidence
- Acceptance boundaries:
- Open Owner decisions:
- Engineering exclusions:
- Handoff status: BLOCKED / COMPLETE

## Locked logical subtrees

| Subtree type | Subtree ID | Path | Component version | Content hash | Classification | Classification authority | Workflow Capability ID | API evidence | MCP evidence | Primary mainline | Related subtree IDs |
|---|---|---|---|---|---|---|---|---|---|---|---|

`COMPLETE` requires a mechanically valid `PASS` Calabash Definition Handoff with a frozen `CALABASH_DEFINITION_BASELINE`, passing Upgrade Receipt, no Snake `OPEN`, no Scorpion `HIT`, and `OWNER` change authority. The cited Definition Handoff hash is SHA-256 over the exact UTF-8/LF bytes of `CALABASH-UPGRADE-GATE.md`; that handoff does not contain its own artifact hash, so the citation has no self-reference. Any handoff-byte change invalidates this citation. The Product Baseline identity above remains distinct from that Definition Baseline. It also requires one total project repository, a full exact Git-resolvable commit, every realized peer UI / Workflow / Simulation subtree identity, and an Owner-confirmed Primary product mainline containing one mutually linked Simulation, implemented CORE Workflow, and UI route. The confirmation requires non-empty evidence after `OWNER_CONFIRMED:`. Component version uses `MAJOR.MINOR.PATCH`; Primary mainline is exactly `YES` or `NO`. Locked identities, reciprocal relations, mainline markers, and the minimal Workflow classification authority, Capability ID, API evidence, and MCP evidence must match their canonical Maps. Non-Workflow rows use exact `NOT_APPLICABLE` for those Workflow-only facts. The mainline ID must equal the ID recorded by all three Maps. The single canonical tracked-blob manifest algorithm is the same algorithm for UI, Workflow, and Simulation; it reads the frozen commit, not the worktree. Commit plus subtree content hash is authoritative; component version is the human-readable label. Unimplemented EXTRA remains only in the Workflow Map and is not claimed in this locked subtree table. `BLOCKED` records incomplete Product Formation without claiming closure; it never satisfies an accepted `product_baseline` status.
