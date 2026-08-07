# Migration 2.5.1 → 2.5.2

## What changed

- `UI=LOCKED` is clarified as one-way Owner authority. The Owner may initiate or explicitly approve a UI change through the existing Baseline Change Request; system actors must not autonomously change, overwrite, or restore locked UI material.
- Engineering Runs now require real product integration evidence: UI operation → API/MCP-backed Workflow capability → real state, data, or side effect → visible UI result. Simulation remains the capability/scenario grounding, but need not be the production backend.
- Static UI, mocks, stubs, and manually staged state remain valid Product Formation demonstrations only. They cannot prove third-phase integration, delivery readiness, or D0–D3 acceptance.
- The public README now states LCCoding's personal origin, its adaptable use by others, open discussion/contribution posture, and the Owner-maintained canonical mainline.

## Migration actions

1. Keep the existing four-phase mainline and existing `BASELINE-CHANGE-REQUEST` route; do not add a phase, runtime state, or BI control.
2. When an Owner changes UI during Engineering Runs, record `OWNER_INITIATED` or `OWNER_APPROVED`, bind the resulting exact project/component identity, update affected baseline records, and re-verify only affected evidence.
3. For each new or changed Feature Slice, record its real integration route and distinguish any Phase-2-only demonstration evidence from acceptance evidence.
4. Upgrade overall LCCoding carriers together to `2.5.2`. The BI remains part of LCCoding and keeps no independent version, tag, or release.

## Not changed

The canonical mainline, phase overlay, Product Baseline, Workflow/UI/Simulation topology, Loop responsibilities, BI read-only boundary, and formal installer-release gate remain unchanged.
