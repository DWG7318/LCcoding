# Integration Baseline Lock

Default:

```text
UI = LOCKED
Workflow = CONTROLLED_MUTABLE
Simulation = VERSIONED_MUTABLE
Calabash = LIVING_WITH_IMPACT_TRACE
```

The locked UI includes all affected customer, staff, operator, administrator, notification, approval, audit, and status surfaces.

The lock is an immutable, recoverable logical-subtree identity:

- the complete rebuildable UI source, styles, assets, design tokens, interaction states, and required build metadata live in an applicable UI logical subtree inside the one total project repository;
- Product Baseline Handoff records total-project repository/exact commit plus subtree ID/path/component version/content hash and scope;
- Integration Baseline pins the same project commit and applicable UI subtree identity tuple;
- screenshots, exports, design links, previews, or build artifacts may support evidence but cannot replace recoverable source and immutable identity.

A branch name or `latest` is not an immutable reference; neither are a tag, `HEAD`, an uncommitted working tree, or a worktree path. Here logical subtree means a product path in the total repository, not Git's external-repository subtree import mechanism. Repository visibility remains an Owner project decision and is not a substitute for exact commit/hash proof.

The one Product Baseline content-hash algorithm applies to every UI, Workflow, and Simulation subtree. At the frozen total-project commit, the declared path must resolve to a Git tree. Recursively enumerate its tracked blobs; each canonical entry is `path UTF-8 bytes + NUL + Git mode + NUL + lowercase blob SHA-256 hex + LF`, entries are byte-sorted by path, and the recorded value is `sha256:<lowercase SHA-256 of the concatenated manifest bytes>`. Read the commit tree and blobs from Git objects, never from the current worktree. Product Handoff, Integration Baseline, Feature Slice, and final verification cite the same project repository/commit/subtree path/version/hash tuple.

Before Slice/Run work and before acceptance, compare current UI subtree to the locked project commit and content hash. An unapproved delta or identity mismatch blocks work or acceptance. Preserve evidence, restore from the locked project commit or isolate the delta, and never silently overwrite user material.

A Baseline Change Request is required for material layout, information architecture, interaction sequence, actions, fields, states, content meaning, or visual direction. It must explain why the original UI cannot be preserved, record Owner approval, create a distinct total-project commit, update the affected UI subtree component version/hash in Product and Integration Baselines, and re-verify affected evidence. Do not put credentials, tokens, or passwords in baseline artifacts.
