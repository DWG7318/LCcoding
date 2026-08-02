# Migration from 2.2.3 to 2.3.0

LCCoding 2.3.0 keeps the 2.2.3 canonical mainline, four phases, states, gates, Simulation-first Product Formation, Feature Slice, UI lock, Loop Owner Acceptance, centralized security closure, Post-Security Owner Acceptance, protected Delivery, and lower-method responsibilities unchanged.

## Built-in read-only BI

- The built-in BI projects the fixed `INITIAL`, `PRODUCT_FORMATION`, `ENGINEERING_RUNS`, and `DELIVERY_PREPARATION` phases together with fine-grained milestones, states, artifacts, and protected subreports.
- The standalone Windows window keeps the accepted compact 300×480 content design, starts in English, can switch to Chinese, and provides native Pin control for its actual always-on-top state.
- The desktop entry uses only the authorized sanitized static Snapshot. Browser preview inputs remain strictly allowlisted and fail closed.

## Authority and data boundary

- The BI is read-only and never becomes a second source of project truth; `status.json` remains authoritative.
- It does not read or mutate project files.
- It does not control Agent or runtime behavior.
- It does not claim that real project data integration is complete.
- It accepts no arbitrary path, network, shell, installer, or project-data capability in this release.

Existing 2.2.3 projects require no status migration. The 2.3.0 template version identifies the current LCCoding method and future compatibility boundary; it does not rewrite an existing project's declared version or evidence history.
