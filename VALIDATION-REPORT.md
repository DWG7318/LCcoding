# LCCoding 2.5.2 Validation Report

## Result

Local implementation candidate: **PASS**. Formal GitHub publication: **NOT ATTEMPTED**.

LCCoding 2.5.2 preserves one current-user NSIS installer contract for `lccoding-bi.exe`, a React + Vite packaged frontend, and one Rust read-only project projector. This source-level method update preserves the canonical mainline, four phases, 21 BI steps, eight protected reports, 300×480 client area, English-first/Chinese interaction, Pin, Refresh, Open/Back, visual tokens, and `status.json` authority. It does not claim that a new installer asset or GitHub Release exists; those remain formal-release workflow outputs.

## Fresh verification

- `python lc-coding/tests/run_tests.py`: PASS, 32 tests.
- `python lc-coding/scripts/validate_repository.py .`: PASS.
- `python lc-coding/tests/test_release_integrity.py`: PASS; release tree and SHA-256 manifest agree.
- `core.autocrlf=true --no-hardlinks` clone regression: PASS; `.gitattributes` keeps protected text at `i/lf w/lf attr/text=auto eol=lf`, workflow SHA-256 matches `FILE_HASHES.json`, and release-integrity passes inside the clone.
- React `typecheck`: PASS.
- Vitest DOM/accessibility/refresh tests: PASS, 71/71.
- Vite production build: PASS; production graph contains React only and no fixture selector or retired Vanilla runtime.
- Playwright installed-Chrome visual suite: PASS, 33/33 at the fixed 300×480 viewport, including bilingual, reduced-motion, error, boundary-name, Product Baseline, and Loop Governance coverage.
- Rust normal tests: PASS, 31/31 across binding, single-flight commands, `gix` exact-commit reads, bounded input, Loop adapters, and project projection.
- Rust optimized tests: PASS, the same 31/31.
- NSIS current-user packaging contract: source-validated with `embedBootstrapper`, exact safe basename `LCCoding-BI_2.5.2_x64-setup.exe`, installer SHA-256/overall-version/commit provenance requirements, and no independent BI version. A candidate build and published asset remain required before formal-release acceptance.
- Installed-tool smoke: PASS. The installed `lccoding-bi.exe --project` ran with no source or Node/npm/Rust/Python/Git CLI path, opened a 300×480 logical client, survived refresh, and left project bytes and mtimes unchanged.
- Uninstall smoke: PASS. Installation directory, exact user PATH entry, uninstall registration, and Start Menu shortcut were removed.
- `git diff --check`, JSON/Markdown/version consistency, secret/path scans, and scope inspection: PASS.

## Reproduction commands

Run from the extracted repository root in PowerShell. All dependencies, builds, screenshots, Cargo output, and installer artifacts stay outside the release tree:

```powershell
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
$repo = (Resolve-Path .).Path
$tmp = Join-Path ([IO.Path]::GetTempPath()) "lccoding-bi-250-fresh-verification"
if (Test-Path $tmp) { throw "choose an empty external verification directory" }
New-Item -ItemType Directory -Path $tmp | Out-Null
$sourceFilesBefore = @(Get-ChildItem -LiteralPath $repo -Recurse -Force -File | ForEach-Object {
  [IO.Path]::GetRelativePath($repo, $_.FullName)
} | Sort-Object)
$archive = Join-Path $tmp "source.zip"
$runner = Join-Path $tmp "runner"
git archive --format=zip --output=$archive HEAD
if ($LASTEXITCODE -ne 0) { throw "git archive failed" }
Expand-Archive -LiteralPath $archive -DestinationPath $runner
$runnerBi = Join-Path $runner "lc-coding/bi"
$runnerTauri = Join-Path $runnerBi "src-tauri"

Push-Location $runnerBi
npm ci --ignore-scripts
$env:LCCODING_BI_DIST = (Join-Path $tmp "dist").Replace("\", "/")
npm run typecheck
npm test
npm run build
$env:BI_OWNER_REVIEW_DIR = Join-Path $tmp "visual-candidates"
npm run visual:candidates
Pop-Location

$relativeDist = [IO.Path]::GetRelativePath($runnerTauri, (Join-Path $tmp "dist")).Replace("\", "/")
$env:TAURI_CONFIG = @{ build = @{ frontendDist = $relativeDist } } | ConvertTo-Json -Compress
$env:CARGO_TARGET_DIR = (Join-Path $tmp "cargo-target").Replace("\", "/")
Push-Location $runnerTauri
cargo test
cargo test --release
Pop-Location

& lc-coding/bi/scripts/package-release.ps1 -OutputRoot (Join-Path $tmp "candidate-package") -AllowUnreleasedLoopCandidates
$env:PYTHONDONTWRITEBYTECODE = "1"
python lc-coding/tests/run_tests.py
python lc-coding/scripts/validate_repository.py .
& lc-coding/bi/tests/packaging/nsis-contract.ps1
python lc-coding/tests/test_release_integrity.py
git diff --check
$sourceFilesAfter = @(Get-ChildItem -LiteralPath $repo -Recurse -Force -File | ForEach-Object {
  [IO.Path]::GetRelativePath($repo, $_.FullName)
} | Sort-Object)
if (@(Compare-Object $sourceFilesBefore $sourceFilesAfter).Count -ne 0) {
  throw "source tree physical file set changed"
}
if (git status --porcelain=v1) { throw "source worktree changed" }
```

The candidate command deliberately writes `build_mode=LOCAL_BLOCKED_CANDIDATE` and `loop_release_dependency_gate=BLOCKED_CANDIDATE_IDENTITIES`. A formal package omits `-AllowUnreleasedLoopCandidates`; it first runs the mechanical Loop release verifier and then requires a GitHub Actions workflow/run identity bound to the exact source commit and target triple.

## Formal GitHub Windows release run

After the workflow candidate is accepted and fast-forwarded to `main`, dispatch it on the exact remote `main` commit. The commands below identify the new run without confusing it with an earlier attempt, wait for success, download only its named artifact, and verify the formal build identity and installer hash:

```powershell
$ErrorActionPreference = "Stop"
$repo = "DWG7318/LCcoding"
$releaseCommit = (gh api "repos/$repo/commits/main" --jq .sha).Trim()
$before = @(gh run list -R $repo --workflow release-bi.yml --event workflow_dispatch --limit 50 --json databaseId | ConvertFrom-Json | ForEach-Object { [string]$_.databaseId })
gh workflow run release-bi.yml --ref main -R $repo
do {
  Start-Sleep -Seconds 5
  $matches = @(gh run list -R $repo --workflow release-bi.yml --branch main --event workflow_dispatch --limit 20 --json databaseId,headSha,status,conclusion,url | ConvertFrom-Json | Where-Object {
    $_.headSha -eq $releaseCommit -and $before -notcontains [string]$_.databaseId
  })
} until ($matches.Count -eq 1)
$runId = [string]$matches[0].databaseId
gh run watch $runId -R $repo --exit-status
$run = gh run view $runId -R $repo --json attempt,conclusion,headSha,url | ConvertFrom-Json
if ($run.conclusion -ne "success" -or $run.headSha -ne $releaseCommit) { throw "formal workflow identity failed" }
$artifactName = "lccoding-bi-formal-$releaseCommit-$runId-$($run.attempt)"
$download = Join-Path ([IO.Path]::GetTempPath()) "lccoding-bi-formal-download-$runId"
if (Test-Path $download) { throw "choose an empty download directory" }
gh run download $runId -R $repo --name $artifactName --dir $download
$provenance = Get-Content (Join-Path $download "provenance.json") -Raw | ConvertFrom-Json
$installer = Join-Path $download "LCCoding-BI_2.5.2_x64-setup.exe"
$sha256 = (Get-FileHash $installer -Algorithm SHA256).Hash.ToLowerInvariant()
if ($provenance.commit -ne $releaseCommit -or $provenance.build_mode -ne "FORMAL_GITHUB_ACTIONS" -or $provenance.build_run_id -ne $runId -or $provenance.sha256 -ne $sha256) { throw "formal provenance failed" }
if ((Get-Content (Join-Path $download "installer.sha256") -Raw).Trim() -ne "$sha256  LCCoding-BI_2.5.2_x64-setup.exe") { throw "formal checksum failed" }
```

Before creating a GitHub Release for `v2.5.2`, repeat the accepted current-user installation smoke with its workflow-produced installer: install without elevation, launch `lccoding-bi.exe --project` from an environment without source/build-tool paths, verify the 300×480 non-resizable window and real project projection, compare project bytes and mtimes before/after, then run the registered uninstaller and verify install directory, PATH entry, Start Menu shortcut, and uninstall registration are removed.

## Safety and authority

- CLI and native Folder Picker share the same Rust-owned canonical root validation and immutable one-project binding.
- `get_snapshot` accepts no path argument and joins one Rust-side in-flight projection; the React scheduler also joins one request and waits two seconds after settlement.
- The reader is bounded, no-follow/reparse-aware, strict-schema, network-disabled, and read-only. It uses `gix` rather than Git CLI for packaged project reads.
- Only allowlisted Snapshot fields cross IPC. Project paths, repositories, commits, hashes, evidence bodies, raw errors, URLs, secrets, and task identifiers do not reach the webview.
- Missing or unsupported evidence projects `UNKNOWN`, `NOT_RECORDED`, or a fixed path-free error. The BI never writes project state or controls Agent/runtime behavior.
- The Tauri ACL remains exactly `bind_project`, `choose_project`, `get_snapshot`, `is_pinned`, and `set_pinned`; no filesystem, shell, opener, HTTP, updater, or arbitrary path capability is enabled.

## Formal release dependency gate

The adapters and formal package verifier are locked to the published SLK 2.5.0, CLK 2.5.0, and GLK 3.1.0 contract identities. The following read-only commands reproduce the canonical checks:

```powershell
gh api repos/DWG7318/small-loop-skill/git/ref/heads/main --jq '.object.sha'
gh api repos/DWG7318/small-loop-skill/git/ref/tags/v2.5.0
gh release view v2.5.0 -R DWG7318/small-loop-skill
gh api repos/DWG7318/chain-loop-skill/git/ref/heads/main --jq '.object.sha'
gh api repos/DWG7318/chain-loop-skill/git/ref/tags/v2.5.0
gh release view v2.5.0 -R DWG7318/chain-loop-skill
gh api repos/DWG7318/large-loop-skill/git/ref/heads/main --jq '.object.sha'
gh api repos/DWG7318/large-loop-skill/git/ref/tags/v3.1.0
gh release view v3.1.0 -R DWG7318/large-loop-skill
```

The verified main/tag/Release commits are respectively `0153776c84b57fd6217259fd02832a6fdcea4ccb`, `6043ce6011b7bb162f8ff6a169b144f4a24fe342`, and `2cbbd20167376e4ce57cd0e3a201e5fdb323c43f`. Each published Release is non-draft and non-prerelease, and each exact Manifest/schema/template SHA-256 matches `lc-coding/bi/release/loop-contract-identities.json`. Therefore:

- the package driver ignores environment assertions and mechanically resolves canonical main/tag/Release identities plus the exact Manifest/schema/template bytes;
- formal package generation remains fail-closed unless all identities match and GitHub Actions supplies the exact repository/workflow/run/ref/commit identity;
- explicit local candidate builds remain visibly marked `BLOCKED_CANDIDATE_IDENTITIES` and cannot be published as formal assets.
