[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$OutputRoot,
  [switch]$AllowDirty,
  [switch]$AllowUnreleasedLoopCandidates
)

$ErrorActionPreference = "Stop"
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "../../.."))
$bi = Join-Path $repo "lc-coding/bi"
$tauriRoot = Join-Path $bi "src-tauri"
$output = [IO.Path]::GetFullPath($OutputRoot)
$repoPrefix = $repo.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if ($output.StartsWith($repoPrefix, [StringComparison]::OrdinalIgnoreCase)) {
  throw "BI_PACKAGE_OUTPUT_MUST_BE_EXTERNAL"
}

if (-not $AllowDirty) {
  $dirty = (& git -C $repo status --porcelain=v1)
  if ($LASTEXITCODE -ne 0 -or $dirty) { throw "BI_PACKAGE_SOURCE_NOT_CLEAN" }
}

$loopGate = "VERIFIED_FORMAL_RELEASES"
if ($AllowUnreleasedLoopCandidates) {
  $loopGate = "BLOCKED_CANDIDATE_IDENTITIES"
} elseif ($env:LCCODING_LOOP_RELEASES_VERIFIED -ne "1") {
  throw "BI_LOOP_RELEASE_DEPENDENCY_BLOCKED"
}

foreach ($path in @(
  (Join-Path $output "frontend"),
  (Join-Path $output "dist"),
  (Join-Path $output "release")
)) {
  if ([IO.Directory]::Exists($path)) { [IO.Directory]::Delete($path, $true) }
}
[IO.Directory]::CreateDirectory($output) | Out-Null
$cargoTarget = Join-Path $output "cargo-target"
$bundleOutput = Join-Path $cargoTarget "release/bundle/nsis"
if ([IO.Directory]::Exists($bundleOutput)) { [IO.Directory]::Delete($bundleOutput, $true) }
$frontend = Join-Path $output "frontend"
[IO.Directory]::CreateDirectory($frontend) | Out-Null

foreach ($file in @(
  "index.html",
  "package.json",
  "package-lock.json",
  "playwright.config.ts",
  "tsconfig.json",
  "vite.config.ts"
)) {
  [IO.File]::Copy((Join-Path $bi $file), (Join-Path $frontend $file), $true)
}
foreach ($directory in @("src", "tests")) {
  Copy-Item -LiteralPath (Join-Path $bi $directory) -Destination $frontend -Recurse -Force
}

Push-Location $frontend
try {
  npm ci --ignore-scripts
  if ($LASTEXITCODE -ne 0) { throw "BI_NPM_CI_FAILED" }
  $env:LCCODING_BI_DIST = (Join-Path $output "dist").Replace("\", "/")
  npm run build
  if ($LASTEXITCODE -ne 0) { throw "BI_FRONTEND_BUILD_FAILED" }
} finally {
  Pop-Location
}

$dist = Join-Path $output "dist"
$relativeDist = [IO.Path]::GetRelativePath($tauriRoot, $dist).Replace("\", "/")
$env:CARGO_TARGET_DIR = $cargoTarget.Replace("\", "/")
$env:TAURI_CONFIG = @{ build = @{ frontendDist = $relativeDist } } | ConvertTo-Json -Compress
$tauriCli = Join-Path $frontend "node_modules/@tauri-apps/cli/tauri.js"

Push-Location $bi
try {
  # tauri build uses the pinned CLI from the external runner.
  & node $tauriCli build --bundles nsis --ci --config $env:TAURI_CONFIG
  if ($LASTEXITCODE -ne 0) { throw "BI_TAURI_BUILD_FAILED" }
} finally {
  Pop-Location
}

$installers = @(Get-ChildItem -LiteralPath (Join-Path $cargoTarget "release/bundle/nsis") -Filter "*-setup.exe" -File)
if ($installers.Count -ne 1) { throw "BI_INSTALLER_COUNT_INVALID" }
$release = Join-Path $output "release"
[IO.Directory]::CreateDirectory($release) | Out-Null
$installer = Join-Path $release $installers[0].Name
[IO.File]::Copy($installers[0].FullName, $installer, $true)
$installerHash = (Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant()
[IO.File]::WriteAllText(
  (Join-Path $release "installer.sha256"),
  "$installerHash  $([IO.Path]::GetFileName($installer))`n",
  [Text.UTF8Encoding]::new($false)
)

$version = [IO.File]::ReadAllText((Join-Path $repo "VERSION")).Trim()
$commit = (& git -C $repo rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $commit -notmatch '^[0-9a-f]{40}$') {
  throw "BI_PROVENANCE_COMMIT_INVALID"
}
$provenance = [ordered]@{
  schema = "LCCoding 2.5.0 installer provenance"
  overall_version = $version
  commit = $commit
  asset = [IO.Path]::GetFileName($installer)
  sha256 = $installerHash
  package_lock_sha256 = (Get-FileHash -LiteralPath (Join-Path $bi "package-lock.json") -Algorithm SHA256).Hash.ToLowerInvariant()
  cargo_lock_sha256 = (Get-FileHash -LiteralPath (Join-Path $tauriRoot "Cargo.lock") -Algorithm SHA256).Hash.ToLowerInvariant()
  loop_release_dependency_gate = $loopGate
  installer_scope = "current_user"
  webview2_mode = "embedBootstrapper"
}
$json = $provenance | ConvertTo-Json -Depth 4
[IO.File]::WriteAllText(
  (Join-Path $release "provenance.json"),
  "$json`n",
  [Text.UTF8Encoding]::new($false)
)

Write-Output $installer
Write-Output (Join-Path $release "installer.sha256")
Write-Output (Join-Path $release "provenance.json")
