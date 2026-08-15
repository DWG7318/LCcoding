# LCCoding BI Single-Build Formal Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make both Windows workflows use one reusable standard-user smoke parent, and make the formal workflow build, smoke, and upload one byte-identical installer lineage.

**Architecture:** Extract only the GitHub-hosted Windows account/ACL/process/evidence orchestration from `validate.yml` into one PowerShell parent that calls the accepted child launcher. Keep Validate as an ordinary candidate check; make `release-bi.yml` package once, smoke that exact release directory, re-hash the same installer path, upload the three formal files unchanged, and upload smoke evidence separately.

**Tech Stack:** GitHub Actions YAML, Windows PowerShell 5.1/pwsh syntax contracts, Python repository contract tests, SHA-256 release identity.

---

## Locked scope and boundaries

Stage 1 changes exactly these non-mechanical files:

- Create: `lc-coding/bi/tests/packaging/run-standard-user-install-smoke.ps1`
- Modify: `.github/workflows/validate.yml`
- Modify: `.github/workflows/release-bi.yml`
- Modify: `lc-coding/tests/test_windows_ci_path_roundtrip_280.py`
- Modify: `lc-coding/tests/test_bi_release_workflow_251.py`
- Modify: `lc-coding/tests/test_bi_subtree_loop_241.py`
- Mechanical: `FILE_HASHES.json`

The existing `standard-user-install-smoke.ps1`, original `install-smoke.ps1`, NSIS/product files, version carriers, BI UI/Runtime, and lifecycle/Agent artifacts do not change. `test_bi_250_contract.py`, `test_bi_release_asset_name_251.py`, `test_checkout_lf_policy.py`, release integrity, and repository validation are regression consumers only.

Run `31913444348` stays rejected and unpublished. No workflow dispatch, push, merge, tag, Release, installation, global Skill deployment, local user creation, UAC, Windows Sandbox, or Docker operation is part of Stage 1.

### Task 1: Lock the reusable-parent and single-build workflow contracts RED

**Files:**
- Modify: `lc-coding/tests/test_windows_ci_path_roundtrip_280.py`
- Modify: `lc-coding/tests/test_bi_release_workflow_251.py`

- [ ] **Step 1: Write the reusable-parent contract before creating it**

In `test_windows_ci_path_roundtrip_280.py`, distinguish the new parent from the unchanged child and require both workflows to call the parent exactly once:

```python
PARENT = ROOT / "lc-coding/bi/tests/packaging/run-standard-user-install-smoke.ps1"
CHILD = ROOT / "lc-coding/bi/tests/packaging/standard-user-install-smoke.ps1"
RELEASE_WORKFLOW = ROOT / ".github/workflows/release-bi.yml"

assert PARENT.is_file(), "reusable standard-user smoke parent is missing"
assert CHILD.is_file(), "accepted standard-user smoke child is missing"
assert windows_job.count("run-standard-user-install-smoke.ps1") == 1
assert release_workflow.count("run-standard-user-install-smoke.ps1") == 1
for inline_parent_primitive in (
    "New-LocalUser", "Add-LocalGroupMember", "Start-Process",
    "Remove-LocalUser", "[Management.Automation.PSCredential]",
):
    assert inline_parent_primitive not in windows_job
```

Require the parent itself to own exactly one temporary-user lifecycle, well-known group SIDs, minimum ACL loop, credentialed child launch, null-aware process/result join, closed evidence fields, atomic result, and cleanup verification. Require `RUNNER_ENVIRONMENT=github-hosted`, `GITHUB_ACTIONS=true`, and absence of UAC, Sandbox, Docker, scheduled-task, PsExec, `runas`, local formal substitution, and secrets in arguments/evidence.

- [ ] **Step 2: Write the formal single-build contract before changing the workflow**

In `test_bi_release_workflow_251.py`, require this ordered relationship:

```python
assert text.count("package-release.ps1 -OutputRoot $outputRoot") == 1
build = text.index("package-release.ps1 -OutputRoot $outputRoot")
pre_hash = text.index("BI_RELEASE_PRE_SMOKE_SHA256")
smoke = text.index("run-standard-user-install-smoke.ps1")
post_hash = text.index("BI_RELEASE_POST_SMOKE_SHA256")
formal_upload = text.index("Upload formal three-file asset set")
assert build < pre_hash < smoke < post_hash < formal_upload
assert text.count("actions/upload-artifact@v4") == 2
assert "Upload formal smoke evidence" in text
assert "if: always()" in text[text.index("Upload formal smoke evidence") :]
```

Also require the exact release root and installer basename before smoke, after smoke, and in the formal upload; exact pre/post/checksum/provenance equality; one separate evidence artifact; default success gating on the formal upload; no Validate artifact download or second copy/build; and the exact three formal upload paths only.

- [ ] **Step 3: Run the focused tests and record meaningful RED**

Run:

```powershell
python lc-coding/tests/test_windows_ci_path_roundtrip_280.py
python lc-coding/tests/test_bi_release_workflow_251.py
```

Expected: both fail because the reusable parent does not exist and `release-bi.yml` has neither the parent call nor the post-smoke/evidence-upload sequence. A syntax error or unrelated assertion is not an acceptable RED.

### Task 2: Add the reusable parent and migrate Validate

**Files:**
- Create: `lc-coding/bi/tests/packaging/run-standard-user-install-smoke.ps1`
- Modify: `.github/workflows/validate.yml`
- Test: `lc-coding/tests/test_windows_ci_path_roundtrip_280.py`

- [ ] **Step 1: Implement the narrow parent interface**

Use this closed parameter surface:

```powershell
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$SourceRepository,
  [Parameter(Mandatory = $true)][string]$PackageDirectory,
  [Parameter(Mandatory = $true)][string]$EvidenceDirectory,
  [Parameter(Mandatory = $true)][string]$ExpectedCommit,
  [Parameter(Mandatory = $true)][string]$ExpectedHooksSha256
)
```

Before account creation, require Windows, `GITHUB_ACTIONS=true`, `RUNNER_ENVIRONMENT=github-hosted`, repository `DWG7318/LCcoding`, exact `GITHUB_SHA`, and non-empty workflow/run/attempt/ref identity. Require the package directory to contain exactly `LCCoding-BI_2.8.0_x64-setup.exe`, `installer.sha256`, and `provenance.json`; bind checksum/provenance to the pre-smoke SHA and current GitHub identity.

The parent creates one random-name local user, resolves Users/Administrators by `S-1-5-32-545`/`S-1-5-32-544`, adds only Users membership, grants only RX to repository/package and M to evidence/smoke roots, and launches the unchanged child with a loaded profile and in-memory credential. It validates the child's exact key set below, computes the child script/result hashes, and treats a missing cross-credential `Process.ExitCode` as unavailable rather than PASS; `result.process_exit_code` remains authoritative and must be zero.

```text
schema, status, baseline_marker, expected_commit, actual_commit,
user_name, user_sid, administrator, session_id, hooks_sha256,
provenance_commit, provenance_build_mode, before_path, after_path,
exact_raw_match, exact_kind_match, process_exit_code,
uninstall_parent_exit_code, residue_before, residue_after,
smoke_output, error
```

Write `orchestrator-result.json` atomically with this closed top-level set:

```text
schema, status, repository, commit, workflow, workflow_run_id,
workflow_run_attempt, workflow_ref, installer_basename, installer_path,
pre_smoke_sha256, post_smoke_sha256, checksum_sha256, provenance_sha256,
child_script_path, child_script_sha256, child_result_path,
child_result_sha256, observed_child_exit_code, child_process_exit_code,
child_status, standard_user_sid, administrator, session_id,
exact_raw_match, exact_kind_match, uninstall_parent_exit_code,
residue_after, temporary_user_cleanup, error
```

Do not include a password or raw PATH. In `finally`, remove the temporary user if created, verify it no longer exists, set `temporary_user_cleanup=PASS`, and only then permit overall `PASS`. A child, hash, identity, residue, PATH, or cleanup failure writes bounded FAIL evidence and returns nonzero.

- [ ] **Step 2: Replace Validate's inline parent with one call**

Keep its candidate build step. Replace the large `New-LocalUser` block with:

```powershell
$parent = Join-Path $env:GITHUB_WORKSPACE "lc-coding/bi/tests/packaging/run-standard-user-install-smoke.ps1"
& $parent `
  -SourceRepository $env:GITHUB_WORKSPACE `
  -PackageDirectory (Join-Path $env:RUNNER_TEMP "lccoding-task22-win-ci-package/release") `
  -EvidenceDirectory (Join-Path $env:RUNNER_TEMP "lccoding-task22-win-ci-evidence") `
  -ExpectedCommit $env:GITHUB_SHA `
  -ExpectedHooksSha256 $env:EXPECTED_HOOKS_SHA256
if ($LASTEXITCODE -ne 0) { throw "TASK22_WIN_CI_PARENT_FAILED" }
```

Upload both `result.json` and `orchestrator-result.json` in the existing evidence artifact. Do not put account orchestration back into YAML.

- [ ] **Step 3: Verify the parent contract GREEN and both PowerShell parsers**

Run:

```powershell
python lc-coding/tests/test_windows_ci_path_roundtrip_280.py
pwsh -NoProfile -Command '$e=$null;$t=$null;[Management.Automation.Language.Parser]::ParseFile("lc-coding/bi/tests/packaging/run-standard-user-install-smoke.ps1",[ref]$t,[ref]$e)|Out-Null;if($e.Count){$e;exit 1}'
powershell -NoProfile -Command '$e=$null;$t=$null;[Management.Automation.Language.Parser]::ParseFile("lc-coding/bi/tests/packaging/run-standard-user-install-smoke.ps1",[ref]$t,[ref]$e)|Out-Null;if($e.Count){$e;exit 1}'
```

Expected: PASS with zero AST errors. Do not execute the parent locally.

### Task 3: Bind the formal workflow to one installer lineage

**Files:**
- Modify: `.github/workflows/release-bi.yml`
- Test: `lc-coding/tests/test_bi_release_workflow_251.py`

- [ ] **Step 1: Freeze the formal installer before smoke**

Keep the single existing package invocation and exact three-file verification. In the verification step compute the installer absolute path and SHA, compare it with checksum/provenance, then export only these stable values through `GITHUB_ENV`:

```powershell
"BI_RELEASE_DIRECTORY=$release" >> $env:GITHUB_ENV
"BI_RELEASE_INSTALLER=$installer" >> $env:GITHUB_ENV
"BI_RELEASE_PRE_SMOKE_SHA256=$sha256" >> $env:GITHUB_ENV
```

Reject pre-existing evidence/output roots and any path not equal to the fixed release directory and exact basename.

- [ ] **Step 2: Smoke that exact directory with the shared parent**

Invoke the same parent once with `PackageDirectory=$env:BI_RELEASE_DIRECTORY`, a new formal evidence directory, current GitHub identity, and the accepted hooks SHA. Do not copy or rename the installer.

- [ ] **Step 3: Re-hash and join all identities before formal upload**

After the parent returns PASS, re-read `orchestrator-result.json` and the two release metadata files. Require:

```powershell
$post = (Get-FileHash -LiteralPath $env:BI_RELEASE_INSTALLER -Algorithm SHA256).Hash.ToLowerInvariant()
if ($post -cne $env:BI_RELEASE_PRE_SMOKE_SHA256 -or
    $post -cne $evidence.pre_smoke_sha256 -or
    $post -cne $evidence.post_smoke_sha256 -or
    $post -cne $checksumSha256 -or
    $post -cne $provenance.sha256 -or
    $evidence.status -cne "PASS" -or
    $evidence.temporary_user_cleanup -cne "PASS") {
  throw "BI_RELEASE_POST_SMOKE_IDENTITY_INVALID"
}
"BI_RELEASE_POST_SMOKE_SHA256=$post" >> $env:GITHUB_ENV
```

The formal upload step keeps the same three literal paths and has no `if: always()`, so any preceding failure blocks it. Add a second `if: always()` upload containing only bounded smoke evidence; it is a CI diagnostic/evidence artifact, never a formal GitHub Release asset.

- [ ] **Step 4: Run the formal workflow contract GREEN**

Run:

```powershell
python lc-coding/tests/test_bi_release_workflow_251.py
python lc-coding/tests/test_bi_release_asset_name_251.py
python lc-coding/tests/test_checkout_lf_policy.py
```

Expected: PASS; one package invocation, two artifact uploads with distinct roles, one frozen installer path, and no second build/copy/download route.

### Task 4: Synchronize protected hashes and run the local release gates

**Files:**
- Modify: `lc-coding/tests/test_bi_subtree_loop_241.py`
- Modify: `FILE_HASHES.json`

- [ ] **Step 1: Update only direct mechanical consumers**

Add the reusable parent to `release_paths`, update the fixed SHA for `release-bi.yml`, and keep the existing package/verifier/NSIS hashes unchanged. Recompute `FILE_HASHES.json` only for the seven Stage 1 paths whose bytes changed or were created.

- [ ] **Step 2: Run focused contracts**

Run:

```powershell
python lc-coding/tests/test_windows_ci_path_roundtrip_280.py
python lc-coding/tests/test_bi_release_workflow_251.py
python lc-coding/tests/test_bi_subtree_loop_241.py
python lc-coding/tests/test_bi_250_contract.py
python lc-coding/tests/test_bi_release_asset_name_251.py
python lc-coding/tests/test_checkout_lf_policy.py
```

Expected: all PASS. Parse both changed workflows and all three packaging PowerShell scripts with pwsh and Windows PowerShell 5.1; require zero AST errors.

- [ ] **Step 3: Run the full local acceptance set**

Run:

```powershell
python lc-coding/tests/run_tests.py
python lc-coding/scripts/validate_repository.py .
python lc-coding/tests/test_release_integrity.py
git diff --check
```

Then verify LF, every physical file hash, exact seven-path Stage 1 scope, no generated source directories, and cached diff/check. Expected: Python suite and all validators PASS; worktree clean after commit.

- [ ] **Step 4: Commit the implementation candidate**

```powershell
git add -- .github/workflows/validate.yml .github/workflows/release-bi.yml lc-coding/bi/tests/packaging/run-standard-user-install-smoke.ps1 lc-coding/tests/test_windows_ci_path_roundtrip_280.py lc-coding/tests/test_bi_release_workflow_251.py lc-coding/tests/test_bi_subtree_loop_241.py FILE_HASHES.json
git commit -m "fix: smoke the formal BI release bytes"
```

Do not push or dispatch. Report the exact RED, GREEN counts, commit, scope, and any blocker for independent Supervisor acceptance.

### Task 5: Supervisor-gated formal CI, publication, and deployment

**Files:** none in the implementation worktree.

This task is explicitly deferred and must not run in Stage 1.

- [ ] **Step 1: Obtain independent implementation acceptance**

Require Supervisor review of the implementation commit, scope, TDD evidence, full local gates, and unchanged child/original smoke/NSIS bytes.

- [ ] **Step 2: Run the accepted remote release sequence once**

Under a separately authorized Release Cell, fast-forward and push only the accepted commit, require the exact main push Validate run to PASS, then dispatch `release-bi.yml` once for that exact main SHA. The formal run must show one build, shared-parent standard-user smoke PASS, cleanup PASS, matching pre/post/checksum/provenance/downloaded SHA, exactly three formal files, and a separate matching smoke evidence artifact.

- [ ] **Step 3: Publish only the proven bytes**

Only after independent evidence review may the Release Cell create the annotated `v2.8.0` tag and non-draft/non-prerelease GitHub Release with the exact three formal files. Run `31913444348` remains rejected and cannot be reused.

- [ ] **Step 4: Deploy separately**

Global Skill deployment remains a later, independently authorized Deployment Cell after formal Release verification. It must not be inferred from CI or publication success.
