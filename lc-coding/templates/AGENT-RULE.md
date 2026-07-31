# Project Agent Rule

- Follow LCCoding mainline and locked canonical versions.
- Owner controls product direction, material changes, versions, acceptance, and delivery.
- AI completes routine engineering without asking for manual confirmation.
- Read Project Profile, Interpretation Lock, current Product Baseline, active Feature Slice, and latest Impact Analysis before work.
- Keep Workflow, UI, Simulation, and Calabash synchronized.
- During Integration, preserve locked UI.
- Treat UI lock as an exact source baseline in an independent Owner-controlled GitHub repository that remains PRIVATE; product repository visibility never relaxes it.
- Pin one Product/Integration UI identity tuple and compare its remote commit SHA and deterministic content hash before work and acceptance. Before acceptance, re-prove Owner control, Private visibility, and remote resolution. Preserve unauthorized diff evidence, restore from the Private remote or isolate the work, and never silently overwrite user material.
- Change UI only through an Owner-approved Baseline Change Request that pushes a new Private remote commit and updates Product/Integration Baselines; never store credentials or tokens in baseline artifacts.
- Use one selected Loop per Run.
- Worker does not accept its own result.
- Reuse valid evidence; repeat checks only with a recorded reason.
- Do not expose LC core/internal dependencies in Delivery.
