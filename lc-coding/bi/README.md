# Built-in BI implementation navigation

Implementation class: BI_SUBTREE_GUIDANCE
Authority: NON_NORMATIVE_IMPLEMENTATION_NAVIGATION
Product contract: ../references/built-in-bi.md

This is the sole implementation entry for the built-in BI subtree. Product behavior, trust boundaries, and acceptance promises remain in the linked product contract and ultimately in `SPEC.md`; this page only routes maintainers to existing code, commands, tests, and automation.

## Modules

- `src/` contains the React/TypeScript application, including `src/model/snapshot.ts`, bilingual catalog, components, desktop bridge, and unchanged visual tokens.
- `src-tauri/` contains the Rust reader, strict records, Tauri command boundary, native window, and package configuration; the sanitized projection is in `src-tauri/src/projection.rs`.
- `tests/dom/`, `tests/visual/`, and `tests/packaging/` contain DOM, 300×480 visual, and package-contract verification. Rust integration tests are under `src-tauri/tests/`.
- `release/loop-contract-identities.json` is the one compatibility asset; implementation guidance does not replace it.

## Local verification

Construct an external runner from allowed tracked/Cell inputs only; reject generated inputs such as `node_modules`, `dist`, `target`, `test-results`, and `playwright-report`. Run dependency installation, checks, builds, and visuals only from that external runner, never from the source worktree:

```powershell
$runnerBi = '<external-runner>\lc-coding\bi'
Set-Location $runnerBi
npm ci --ignore-scripts
npm run typecheck
npm run test:dom
$env:LCCODING_BI_DIST = '<external-frontend-dist>'
$env:BI_OWNER_REVIEW_DIR = '<external-owner-review>'
npm run visual:candidates
```

Bind Rust to the same runner, a real external frontend dist, and an external Cargo target before running from the runner's `src-tauri/`:

```powershell
$runnerTauri = Join-Path $runnerBi 'src-tauri'
$externalDist = (Resolve-Path '<external-frontend-dist>').Path
$relativeDist = [IO.Path]::GetRelativePath($runnerTauri, $externalDist).Replace('\', '/')
$env:CARGO_TARGET_DIR = '<external-cargo-target>'
$env:TAURI_CONFIG = @{ build = @{ frontendDist = $relativeDist } } | ConvertTo-Json -Compress
Set-Location $runnerTauri
cargo test
cargo test --release
```

These generated directories and outputs must not be created in the source worktree and must not enter the release manifest.

## Package and release navigation

- `scripts/package-release.ps1` owns package construction into an external output root.
- `scripts/verify-loop-releases.ps1` owns the formal read-only Loop release identity gate.
- `tests/packaging/nsis-contract.ps1` verifies the package/release contract.
- `.github/workflows/release-bi.yml` is the existing formal release automation.

Those neighboring scripts, tests, workflow, and the compatibility asset are the executable release contract. This README neither duplicates their steps nor claims release readiness.
