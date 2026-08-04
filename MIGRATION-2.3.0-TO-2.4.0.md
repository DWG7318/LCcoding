# Migration: LCCoding 2.3.0 to 2.4.0

LCCoding 2.4.0 keeps the canonical mainline and converts Product Formation identity from single-item assumptions and a mandatory per-UI repository into one total project repository with governed logical subtrees.

- Record one total project repository. Do not create a separate repository for each UI, Workflow, or Simulation.
- Register multiple UI, Workflow, and peer Simulation logical subtrees only when real product work exists. Peer Simulations never nest.
- Keep CORE / EXTRA as Workflow business-necessity classification; do not create a Workflow Core technical layer.
- For every CORE Workflow and every implemented EXTRA Workflow, record direct API and MCP contracts and evidence backed by the same capability. An unimplemented EXTRA has no empty subtree, API, or MCP claim.
- Select one Owner-confirmed Primary product mainline linking at least one Simulation, one CORE Workflow, and one UI. It sets proving and construction priority only; every other CORE remains mandatory.
- At Product Baseline, freeze the repository at an exact project commit and lock each realized subtree name, relative path, component version, content hash, ID relations, and Primary product mainline. Commit and content hash are authoritative; component version is the human-readable label.
- Record one Primary product mainline ID in all three Maps and use only `YES` / `NO` row markers. Use `MAJOR.MINOR.PATCH` component versions and non-empty evidence after `OWNER_CONFIRMED:`. Product Handoff rows must exactly match the canonical Maps.
- Recompute every UI, Workflow, and Simulation content hash from the frozen commit's tracked blobs with the single canonical manifest algorithm. A missing commit/tree, current-worktree substitute, forged digest, or Map/Handoff mismatch blocks Product Baseline.
- Replace the former independent Private UI repository tuple with the total-project commit plus applicable UI subtree ID/path/component version/content hash. Preserve `UI=LOCKED`, before-work and before-acceptance comparison, Baseline Change Request, and no-silent-overwrite protection.
- A worktree is optional parallel-construction or environment-isolation tooling, never product structure, a permanent asset, or baseline identity.

This migration adds no new phase, gate, state, runtime, or lower-method responsibility. Simulation-first Product Formation, Feature Slice, SLK/CLK/GLK ownership, D0-D3, Owner Acceptance, security closure, and Delivery remain unchanged.
