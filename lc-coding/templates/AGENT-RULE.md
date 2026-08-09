# Project Agent Rule

- Follow LCCoding mainline and locked canonical versions.
- Owner controls product direction, material changes, versions, acceptance, and delivery.
- AI completes routine engineering without asking for manual confirmation.
- Read Project Profile, Interpretation Lock, current Product Baseline, active Feature Slice, and latest Impact Analysis before work.
- Keep Workflow, UI, Simulation, and Calabash synchronized.
- Treat UI, Workflow, and Simulation as named logical subtrees inside one total project repository; never create per-subtree repositories or empty product directories by default.
- Use worktrees only when parallel construction or environment isolation needs them; never treat a worktree as a product asset or baseline identity.
- Require direct API and MCP evidence for every implemented CORE or EXTRA Workflow capability; never create empty interfaces for an unimplemented EXTRA.
- During Integration, `UI = LOCKED` is one-way Owner authority: system actors must not autonomously modify a locked UI; the Owner may initiate or explicitly approve a change.
- Pin one Product/Integration UI identity tuple using the total-project exact commit plus applicable UI subtree ID/path/component version/content hash. Compare it before work and acceptance; preserve and isolate a delta without Owner evidence, never silently overwrite user material, and never automatically restore UI.
- Change locked UI only through an Owner-approved or Owner-initiated Baseline Change Request that creates a distinct project commit and updates Product/Integration Baselines; never store credentials or tokens in baseline artifacts.
- In Engineering Runs, require a real UI operation through an API/MCP-backed Workflow capability, real state/data/side effect, and visible UI result. Static UI, mock, stub, or manually staged state is Product Formation evidence only, not third-phase or D0-D3 proof.
- A bounded work item in any LCCoding phase may select SLK, CLK, GLK, or another registered execution method; these three methods are not an exhaustive list.
- Record the LCCoding phase scope and phase-owned objective for every Run. Use one selected topology per Run, return evidence to the calling phase, and never treat method completion as automatic phase advancement.
- Worker does not accept its own result.
- Reuse valid evidence; repeat checks only with a recorded reason.
- Do not expose LC core/internal dependencies in Delivery.
