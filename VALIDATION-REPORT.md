# LCCoding 4.0.0 Candidate Validation Report

## Result

Local source implementation candidate: **PASS**.

The independently verified source, archive runner, and local installer candidate are bound to commit `3dad6223f792553aa78d486777d4adee7fa504bd`. The closing commit that contains this report and the mechanically refreshed `FILE_HASHES.json` is intentionally not embedded in the files it commits; it changes only those two evidence-record files and does not relabel the already-built package provenance.

Formal installer publication and persistent installation: **NOT ATTEMPTED**. The package is a local blocked candidate, not a GitHub Actions artifact or GitHub Release asset.

## Verification environment

- Source worktree: `D:\LCcoding\.worktrees\LCcoding-main-252`
- Verified source HEAD: `3dad6223f792553aa78d486777d4adee7fa504bd`
- Source branch recorded by package provenance: `design/lccoding-4.0-service-topology`
- External task root: `D:\LCcoding\.codex\.tmp\task11-verify-3dad6223-codex11`
- Fresh runner: `D:\LCcoding\.codex\.tmp\task11-verify-3dad6223-codex11\runner`
- Archive SHA-256: `c9a9d39bcfe867f149c5089cff2adc6ab7cc881edc62d0ac079a303d1bae8ddb`
- Archive closure: 304 Git-tracked paths and exactly 304 extracted files.
- Node.js `v24.13.1`; npm `11.8.0`.
- Rust `rustc 1.96.0 (ac68faa20 2026-05-25)`; Cargo `1.96.0 (30a34c682 2026-05-25)`; target `x86_64-pc-windows-msvc`.
- The shell initially omitted `C:\Users\DWG\.cargo\bin` from `PATH`. The already-installed toolchain was added only to the verification process environment; no toolchain was installed and no persistent environment setting changed.

## Source and contract verification

The formal source gate was run from the clean source worktree with `PYTHONDONTWRITEBYTECODE=1`:

```powershell
python lc-coding/tests/run_tests.py
python lc-coding/scripts/validate_repository.py .
python lc-coding/tests/test_release_integrity.py
python lc-coding/tests/test_checkout_lf_policy.py
git diff --check main...HEAD
```

Results:

- Python repository suite: PASS, 76/76 test files.
- Repository structure/mainline/acceptance/security validator: PASS.
- Release tree and `FILE_HASHES.json` integrity: PASS before and after report closure; final manifest scope is 303 payload rows.
- LF checkout policy under the protected checkout contract: PASS.
- `git diff --check main...HEAD`: PASS with no output.
- Read-only NSIS contract check, `lc-coding/bi/tests/packaging/nsis-contract.ps1`: PASS.

One earlier full-suite attempt emitted PASS output through `test_route_faithful_journey_validation_400.py` and then its Python parent returned `-1 (0xFFFFFFFF)` before the next child produced output. This anomaly was not hidden:

- `python -X faulthandler lc-coding/tests/test_run_contract_270.py`: PASS, exit 0, expected stdout, empty stderr, 58.2 seconds.
- One serial diagnostic wrapper recorded every child: PASS, 76/76 exits were 0, 773.86 seconds.
- The exact formal source command was then rerun from clean state: PASS, 76 tests.

The `-1` did not reproduce and no production file was changed to obtain the passing results.

## Fresh external BI verification

The runner was created exclusively with `git archive HEAD`. Dependencies and all generated outputs stayed below the external task root; the source worktree contained no `node_modules`, `dist`, `target`, `test-results`, or `playwright-report` directory before or after verification.

Commands:

```powershell
git archive --format=zip --output=<external>\source.zip HEAD
Expand-Archive -LiteralPath <external>\source.zip -DestinationPath <external>\runner

Set-Location <external>\runner\lc-coding\bi
npm ci --ignore-scripts
npm run typecheck
npm run test:dom -- --run
$env:LCCODING_BI_DIST = '<external>/outputs/dist'
$env:BI_OWNER_REVIEW_DIR = '<external>\outputs\visual'
npm run visual:candidates

$env:TAURI_CONFIG = '{"build":{"frontendDist":"../../../../outputs/dist"}}'
$env:CARGO_TARGET_DIR = '<external>/outputs/cargo-target'
Set-Location <external>\runner
cargo test --manifest-path lc-coding/bi/src-tauri/Cargo.toml
cargo test --release --manifest-path lc-coding/bi/src-tauri/Cargo.toml
```

Results:

- `npm ci --ignore-scripts`: PASS; 129 packages installed in the external runner.
- TypeScript `tsc --noEmit`: PASS.
- Vitest DOM suite: PASS, 4/4 files and 98/98 tests.
- Vite production build: PASS; output was external.
- Playwright installed-Chrome visual suite: PASS, 37/37 with one worker; screenshots, test results, and HTML report were external.
- Rust debug suite: PASS, 46 tests across all targets, 0 failed/ignored.
- Rust release suite: PASS, 46 tests across all targets, 0 failed/ignored.

The repository has no `test:visual` npm script. The BI README and `package.json` designate `npm run visual:candidates` as the visual verification command, so that existing canonical command was used for the Task 11 visual gate.

## Local candidate package

Exactly one package build was run from the clean source worktree:

```powershell
& lc-coding/bi/scripts/package-release.ps1 -OutputRoot 'D:\LCcoding\.codex\.tmp\task11-verify-3dad6223-codex11\candidate-package' -AllowUnreleasedLoopCandidates
```

The release directory contains exactly:

1. `LCCoding-BI_4.0.0_x64-setup.exe`
2. `installer.sha256`
3. `provenance.json`

Installer evidence:

- Size: 3,489,211 bytes.
- First two bytes: `MZ` (`0x4d 0x5a`), confirming the PE header.
- SHA-256: `b382bc16915e7c43787a26d69f3df7a099a58dfabbf06f922d16c5e151b73793`.
- `installer.sha256`: exact lowercase digest plus exact asset basename.
- `provenance.json`: exact 19-key schema; package-lock and Cargo-lock hashes match current source bytes.
- Schema: `LCCoding 4.0.0 installer provenance`.
- Overall version: `4.0.0`.
- Commit: `3dad6223f792553aa78d486777d4adee7fa504bd`.
- Build mode: `LOCAL_BLOCKED_CANDIDATE`.
- Build workflow/repository: `local-manual` / `LOCAL`.
- Build run ID: `local-e006ec2a-e46e-4e50-9d75-2eb2e7ed0fa6`.
- Target: `x86_64-pc-windows-msvc`.
- Installer scope/WebView2 mode: `current_user` / `embedBootstrapper`.
- Loop release dependency gate: `BLOCKED_CANDIDATE_IDENTITIES`; `loop_release_dependencies` is `null`, as required for this non-formal candidate mode.

## Loop method identity

The source and staged `loop-contract-identities.json` bytes match SHA-256 `5b2f441514b23abcbfdf715454139c701215b414f6f2657854c093c751166138`. The asset schema is exactly `LCCODING_BI_COMPATIBILITY_V4`, contains only `slk`, `clk`, and `glk`, and each method is `CURRENT` with the exact seven-field normalization mapping. Rust adapter identity tests passed 8/8 in both debug and release suites.

- SLK 2.6.0: commit `fa75bcf1c0819c8499d3b6c4ee9ec251dae62ae5`; manifest `b1191453bbedc5b1b8af8327176776602a392913507583bb60bd8ff643a1c339`; schema `ee3978e0b408e67d69d7f78d94bd31c43d68af2a6d0c7a56966dd9ef93f412c5`; template `3d9e7f640b6bb0ad2ea168267d7c38fb41e47e098bca4aaae113603352038e73`.
- CLK 2.5.0: commit `6043ce6011b7bb162f8ff6a169b144f4a24fe342`; manifest `64bbaa4964a56fcafb26eeaed3a912707a20b2ece989cb1a33bdc4240b720b9d`; schema `c292658717e383dd4c95b54403a0fd2b51a590311cf94f4ef28dc6ddef227867`; template `b582d667b46eda1b468033c399a38f380a4a291f1aaf5301af749246ebfea5eb`.
- GLK 3.1.0: commit `2cbbd20167376e4ce57cd0e3a201e5fdb323c43f`; manifest `c8d7789f0aa6792379873dc62edb2f6142842cbf2600c079002f44d7755551d7`; schema `21f33235666394e3c50df3311795cd73093f0b25954e4c40a3d67d1c58a3057b`; template `0b24cec677f7e008d0959201c9c3117a278378e4c1bf05f0aec6ca7a2dcb46ab`.

## Expected skip and exclusions

- Expected skip: external canonical Calabash repository verification was not run because `LCCODING_CALABASH_REPOSITORY` was unset. The committed exact Calabash method-baseline bytes were still validated.
- Formal Loop main/tag/Release identity resolution was not run; local candidate mode deliberately records the blocked dependency gate and cannot be treated as a formal package.
- No GitHub Actions workflow, formal artifact download, tag, GitHub Release, push, deployment, global Skill installation, or Docker action was attempted.
- No persistent BI installation, launch-from-installed-path smoke, standard-user install smoke, uninstall smoke, PATH mutation, Start Menu verification, or uninstall-registration verification was attempted.
- No package or source artifact was written to the Desktop.

## Completion boundary

This report supports only a clean local LCCoding 4.0.0 source candidate and one external local blocked installer candidate. It does not claim a formal release, published Loop dependency closure, or installed-user acceptance.
