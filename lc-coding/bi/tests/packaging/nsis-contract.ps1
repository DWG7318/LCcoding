$ErrorActionPreference = "Stop"

$bi = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$hooks = Join-Path $bi "src-tauri/windows/hooks.nsh"
$driver = Join-Path $bi "scripts/package-release.ps1"
$releaseGate = Join-Path $bi "scripts/verify-loop-releases.ps1"
$releaseIdentity = Join-Path $bi "release/loop-contract-identities.json"

if (-not (Test-Path -LiteralPath $hooks -PathType Leaf)) { throw "missing NSIS hooks" }
if (-not (Test-Path -LiteralPath $driver -PathType Leaf)) { throw "missing release driver" }
if (-not (Test-Path -LiteralPath $releaseGate -PathType Leaf)) { throw "missing mechanical Loop release gate" }
if (-not (Test-Path -LiteralPath $releaseIdentity -PathType Leaf)) { throw "missing production Loop release identity contract" }

$hookText = [IO.File]::ReadAllText($hooks)
foreach ($marker in @(
    "NSIS_HOOK_POSTINSTALL",
    "NSIS_HOOK_PREUNINSTALL",
    'HKCU "Environment" "Path"',
    'SendMessage ${HWND_BROADCAST} ${WM_SETTINGCHANGE}'
)) {
    if (-not $hookText.Contains($marker)) { throw "missing hook marker: $marker" }
}
if ($hookText -match "\.cmd|HKLM|allUsers") { throw "forbidden installer scope" }

$driverText = [IO.File]::ReadAllText($driver)
foreach ($marker in @(
    "npm ci --ignore-scripts",
    "tauri build",
    "installer.sha256",
    "provenance.json",
    "CARGO_TARGET_DIR",
    "LCCODING_BI_DIST",
    "verify-loop-releases.ps1",
    "LOCAL_BLOCKED_CANDIDATE",
    "VERIFIED_FORMAL_RELEASES",
    "build_workflow",
    "build_run_id",
    "build_run_attempt",
    "build_run_url",
    "target_triple",
    "loop_release_dependencies",
    "expectedProvenanceKeys",
    "BI_FORMAL_SOURCE_MUST_BE_CLEAN",
    "stagedTauriRoot",
    'Join-Path $frontend "src-tauri"'
)) {
    if (-not $driverText.Contains($marker)) { throw "missing driver marker: $marker" }
}
if ($driverText.Contains("LCCODING_LOOP_RELEASES_VERIFIED")) {
    throw "formal release gate must not trust an environment assertion"
}
if ($driverText -match 'Push-Location\s+\$bi') {
    throw "Tauri packaging must not run in the source BI tree"
}

$releaseGateText = [IO.File]::ReadAllText($releaseGate)
if ($releaseGateText.Contains("tests/fixtures")) {
    throw "formal release gate must not read a test fixture"
}
foreach ($marker in @(
    "release/loop-contract-identities.json",
    "DWG7318/small-loop-skill",
    "DWG7318/chain-loop-skill",
    "DWG7318/large-loop-skill",
    "v2.5.0",
    "v3.1.0",
    "git/ref/heads/main",
    "git/ref/tags",
    "gh release view",
    "manifest_sha256",
    "schema_sha256",
    "template_sha256"
)) {
    if (-not $releaseGateText.Contains($marker)) { throw "missing release gate marker: $marker" }
}

Write-Output "PASS: NSIS current-user packaging contract"
