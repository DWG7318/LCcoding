# Integration Baseline Lock

Default:

```text
UI = LOCKED
Workflow = CONTROLLED_MUTABLE
Simulation = VERSIONED_MUTABLE
Calabash = LIVING_WITH_IMPACT_TRACE
```

The locked UI includes all affected customer, staff, operator, administrator, notification, approval, audit, and status surfaces.

The lock is an immutable, recoverable identity:

- the complete rebuildable UI source, styles, assets, design tokens, interaction states, and required build metadata live in a Git repository independent from the product repository;
- the remote is an Owner-controlled independent GitHub repository that remains Private regardless of product repository visibility;
- the Product Baseline Handoff records repository/path identity, Owner control, Private-visibility evidence, exact commit SHA, optional version/tag, content hash and scope, remote push/resolve evidence, and a recovery reference;
- the Integration Baseline pins the same Private remote/path, exact commit SHA, and content hash as one locked identity tuple;
- screenshots, exports, design links, previews, or build artifacts may support evidence but cannot replace recoverable source and immutable identity.

`PUBLIC or UNKNOWN visibility blocks` Product Baseline Handoff. A branch name or `latest` is not an immutable reference; neither are a tag, `HEAD`, a local-only commit, or an uncommitted working tree. The product repository identity must be known and comparable; otherwise repository independence is unproved and blocking. Existing independent UI repositories may be reused only when Owner-controlled, GitHub Private, remotely resolvable at the frozen commit, and fully recoverable. A Public repository must first be made Private or migrated to a new Private repository. LCCoding does not prescribe submodule, subtree, or another attachment technique.

The content hash is `sha256:<digest>` over a canonical tracked-file manifest for the declared baseline paths at the frozen commit. Each manifest entry contains the UTF-8 POSIX relative path, Git mode, and SHA-256 of the raw blob bytes; entries are sorted by path before the manifest bytes are hashed. Record the manifest and scope as evidence. Product Handoff, Integration Baseline, Feature Slice, and final verification all cite the same remote/path/SHA/hash tuple; a mismatch is blocking unless an approved Baseline Change Request replaced it.

Before Slice/Run work and before acceptance, compare current UI to the locked remote commit and content hash. Before acceptance, re-prove Owner control, Private visibility, and resolution of the exact remote commit. An unapproved delta or identity mismatch blocks work or acceptance. Preserve evidence, restore from the locked Private commit or isolate the delta, and never silently overwrite user material.

A Baseline Change Request is required for material layout, information architecture, interaction sequence, actions, fields, states, content meaning, or visual direction. It must explain why the original UI cannot be preserved, record Owner approval, create and push a distinct replacement commit in the independent Private GitHub repository, re-prove Owner control, visibility, and remote resolution, update Product and Integration Baseline SHA/hash/version references to the same new identity, and re-verify affected evidence. Do not put credentials, tokens, or passwords in baseline artifacts.
