# LCCoding BI GitHub Windows Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one manual, read-only Windows GitHub Actions channel that produces the three formal LCCoding BI 2.5.0 release assets on an exact reviewed `main` commit.

**Architecture:** A closed Python contract guards one narrow workflow. The workflow validates the source and formal Loop dependencies, builds through the existing package driver in `$RUNNER_TEMP`, verifies exact provenance and asset contents, then uploads only the three-file release directory without creating tags or Releases.

**Tech Stack:** GitHub Actions YAML, Windows PowerShell, Python 3.12, Node 24, Rust 1.96.0, Tauri 2/NSIS.

---

### Task 1: Commit the approved release-channel documents

**Files:**
- Create: `docs/superpowers/specs/2026-08-06-lccoding-bi-github-windows-release-design.md`
- Create: `docs/superpowers/plans/2026-08-06-lccoding-bi-github-windows-release.md`
- Modify: `FILE_HASHES.json`

- [ ] Add only the approved manual Windows build design and this implementation plan.
- [ ] Regenerate `FILE_HASHES.json`, run `test_release_integrity.py`, scan both documents for unfinished markers and contradictions, and run `git diff --check`.
- [ ] Commit the three-file documentation slice with `docs: define BI Windows release channel`.

### Task 2: Drive the workflow contract RED to GREEN

**Files:**
- Create: `lc-coding/tests/test_bi_release_workflow_250.py`
- Create: `.github/workflows/release-bi.yml`
- Modify: `VALIDATION-REPORT.md`
- Modify: `FILE_HASHES.json`

- [ ] Write a failing Python contract that requires `workflow_dispatch` as the only trigger, `permissions: contents: read`, `windows-latest`, exact `${{ github.sha }}` checkout, `refs/heads/main`, explicit Python/Node/Rust toolchains, external `$RUNNER_TEMP` output, the unflagged formal package command, exact provenance checks, and three explicit upload paths.
- [ ] In the same test, reject `push`, `pull_request`, `schedule`, `release`, `-AllowDirty`, `-AllowUnreleasedLoopCandidates`, repository-local output, broad `cargo-target`/`frontend`/`dist` upload, write permissions, `git push`, `git tag`, `gh release`, or release-creation actions.
- [ ] Run `python lc-coding/tests/test_bi_release_workflow_250.py`; expect failure because `.github/workflows/release-bi.yml` is absent.
- [ ] Add the minimal workflow described by the design. The build step must be exactly the existing formal package driver with `GH_TOKEN=${{ github.token }}` and no candidate flags.
- [ ] Add a short validation-report section containing the dispatch, run-watch, artifact-download, provenance/SHA, installation, and post-install cleanup commands used after approval; do not claim a run exists before dispatch.
- [ ] Regenerate `FILE_HASHES.json`; rerun the focused test and expect PASS.

### Task 3: Verify and commit the local workflow candidate

**Files:**
- Verify only the Task 2 paths and existing release contracts.

- [ ] Run `python lc-coding/tests/run_tests.py` and require the updated total with zero failures.
- [ ] Run `python lc-coding/scripts/validate_repository.py .`, `lc-coding/bi/tests/packaging/nsis-contract.ps1`, and `lc-coding/bi/scripts/verify-loop-releases.ps1`.
- [ ] Run `git diff --check`, scan for secrets and forbidden candidate flags in the workflow, confirm no `src-tauri/gen/schemas` files exist, and confirm the original seven-file dirty checkout is unchanged.
- [ ] Stage only the workflow, its contract test, validation report, and hash manifest; commit with `ci: add formal BI Windows packaging channel`.
- [ ] Re-run the same gates on the clean commit and stop for Supervisor review without push, merge, tag, or Release.
