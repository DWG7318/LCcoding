$ErrorActionPreference = "Stop"

$bi = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$hooks = Join-Path $bi "src-tauri/windows/hooks.nsh"
$driver = Join-Path $bi "scripts/package-release.ps1"

if (-not (Test-Path -LiteralPath $hooks -PathType Leaf)) { throw "missing NSIS hooks" }
if (-not (Test-Path -LiteralPath $driver -PathType Leaf)) { throw "missing release driver" }

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
    "LCCODING_BI_DIST"
)) {
    if (-not $driverText.Contains($marker)) { throw "missing driver marker: $marker" }
}

Write-Output "PASS: NSIS current-user packaging contract"
