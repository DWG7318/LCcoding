# Migration from 2.2.1 to 2.2.2

LCCoding 2.2.2 keeps the 2.2.1 canonical mainline, phases, states, gates, Feature Slice placement, runtime boundary, and lower-method responsibilities unchanged.

## Existing locked UI baselines

- Place the complete, rebuildable UI source, styles, assets, design tokens, interaction states, and required build metadata in a Git repository independent from the product repository. Screenshots, exports, previews, and build artifacts are evidence only and cannot replace that source baseline.
- Push the frozen UI commit to an Owner-controlled independent GitHub repository and confirm the repository is `PRIVATE`. Product-repository visibility does not change this requirement.
- Add to Product Baseline Handoff: UI repository identity and URL, Owner-control and Private-visibility evidence, exact remote commit SHA, version or tag when used, content hash and deterministic tracked-file manifest scope, proof that the remote resolves the frozen commit, and a recovery reference.
- Pin Integration Baseline to the same Private remote/path/exact-SHA/content-hash identity as Product Handoff. Do not use a branch name, `HEAD`, `latest`, or a mutable tag as the lock.
- Before each active Feature Slice or Run starts and before acceptance, compare the working UI with the locked remote commit and content hash. Before acceptance, re-prove Owner control, Private visibility, and exact-commit resolution. An unauthorized delta or identity mismatch blocks progress; retain its evidence and restore from the locked Private commit or handle it in isolation without silently overwriting Owner material.
- Route an absolutely necessary UI change through the existing Baseline Change Request. After Owner approval, create and push a distinct new commit in the Private UI repository, reconfirm Owner control, visibility, and remote resolution, update both baselines to the same new identity, and re-verify affected evidence.

An existing independent UI repository may be reused only when it is Owner-controlled, GitHub-hosted, `PRIVATE`, remotely resolvable at the locked commit, and fully recoverable. Convert an existing Public repository to Private or migrate it before completing the handoff.

No UI-baseline phase, state, gate, second status source, prescribed submodule/subtree integration, runtime mechanism, or lower-method responsibility is introduced.
