# Project Agent Rule

- Follow LCCoding mainline and locked canonical versions.
- Owner controls product direction, material changes, versions, acceptance, and delivery.
- AI completes routine engineering without asking for manual confirmation.
- Read Project Profile, Interpretation Lock, current Product Baseline, active Feature Slice, and latest Impact Analysis before work.
- Keep Workflow, UI, Simulation, and Calabash synchronized.
- Treat UI, Workflow, and Simulation as named logical subtrees inside one total project repository; never create per-subtree repositories or empty product directories by default.
- Use worktrees only when parallel construction or environment isolation needs them; never treat a worktree as a product asset or baseline identity.
- Require direct API and MCP evidence for every implemented CORE or EXTRA Workflow capability; never create empty interfaces for an unimplemented EXTRA.
- During Integration, preserve locked UI.
- Pin one Product/Integration UI identity tuple using the total-project exact commit plus applicable UI subtree ID/path/component version/content hash. Compare it before work and acceptance; preserve unauthorized diff evidence, restore from the locked project commit or isolate the work, and never silently overwrite user material.
- Change locked UI only through an Owner-approved Baseline Change Request that creates a distinct project commit and updates Product/Integration Baselines; never store credentials or tokens in baseline artifacts.
- Use one selected Loop per Run.
- Worker does not accept its own result.
- Reuse valid evidence; repeat checks only with a recorded reason.
- Do not expose LC core/internal dependencies in Delivery.
