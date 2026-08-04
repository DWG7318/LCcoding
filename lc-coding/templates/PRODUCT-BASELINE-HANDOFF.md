# Product Baseline Handoff

- Baseline ID / version / hash:
- Project repository identity:
- Project frozen exact commit SHA:
- Calabash source:
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

| Subtree type | Subtree ID | Path | Component version | Content hash | Classification | API evidence | MCP evidence | Primary mainline | Related subtree IDs |
|---|---|---|---|---|---|---|---|---|---|

`COMPLETE` requires one total project repository, a full exact Git-resolvable commit, every realized UI / Workflow / Simulation subtree identity, and an Owner-confirmed Primary product mainline containing at least one Simulation, one CORE Workflow, and one UI. The confirmation requires non-empty evidence after `OWNER_CONFIRMED:`. Component version uses `MAJOR.MINOR.PATCH`; Primary mainline is exactly `YES` or `NO`. Locked identities, relations, mainline markers, and Workflow classification/API/MCP evidence must match their canonical Maps. The mainline ID must equal the ID recorded by all three Maps. The single canonical tracked-blob manifest algorithm is the same algorithm for UI, Workflow, and Simulation; it reads the frozen commit, not the worktree. Commit plus subtree content hash is authoritative; component version is the human-readable label. Unimplemented EXTRA remains only in the Workflow Map and is not claimed in this locked subtree table.
