# Migration: LCCoding 2.4.0 to 2.4.1

## Scope

This migration changes only the built-in BI's closed, read-only projection contract. The canonical mainline, four phases, 21 steps, Gates, `status.json` authority, Product Formation rules, Product Baseline method contract, Feature Slice, Loop ownership, security closure, and Delivery remain unchanged.

## Required updates

1. Update the overall LCCoding version carriers from `2.4.0` to `2.4.1`; there is no independent BI version.
2. Replace the synthetic sanitized Snapshot fixtures atomically with schema `LCCoding 2.4.1 derived BI`.
3. Keep all 21 Step IDs and their order. Set only `PRODUCT_BASELINE.report` to `baseline` and `LOOP_RUN_D0_D3.report` to `loop_governance`.
4. Use the closed metric value `{kind,status,completed,total,interval_minutes}` for subtree, Baseline, and Loop-governance rows. Reject unknown fields, invalid counts, `completed > total`, and Heartbeat intervals outside `10`, `15`, or `30` minutes. Missing facts remain `UNKNOWN` or `NOT_RECORDED` with no numeric claim.
5. Keep the existing two native Pin commands and static fixture Snapshot source. Do not add `get_snapshot`, a Markdown/YAML parser, a Python BI runtime, project-file access, or lower-method control.

## Verification

- Confirm four phases, 21 steps, 300×480 layout, visual tokens, 32 accepted golden targets, and existing keyboard behavior are unchanged.
- Confirm eight fixed protected reports, complete English/Chinese labels, path-free rendering, internal scrolling, and strict DTO rejection.
- Run the complete Python, repository/hash/version, TypeScript/DOM/Vite, Playwright focused report, and Rust boundary suites.

Real project Maps/Handoff and SLK/CLK/GLK artifact integration is not part of this migration and must not be claimed as complete.
