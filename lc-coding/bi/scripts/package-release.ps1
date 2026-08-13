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
$sourceTauriRoot = Join-Path $bi "src-tauri"

function Get-RelativeForwardPath {
  param(
    [Parameter(Mandatory = $true)][string]$BaseDirectory,
    [Parameter(Mandatory = $true)][string]$TargetPath
  )
  try {
    $base = [IO.Path]::GetFullPath($BaseDirectory).TrimEnd([IO.Path]::DirectorySeparatorChar)
    $target = [IO.Path]::GetFullPath($TargetPath)
    if (-not (Test-Path -LiteralPath $base -PathType Container) -or
        -not (Test-Path -LiteralPath $target -PathType Container)) {
      throw "missing path"
    }
    $baseUri = [Uri]::new($base + [IO.Path]::DirectorySeparatorChar)
    $targetUri = [Uri]::new($target)
    if ($baseUri.Scheme -cne "file" -or $targetUri.Scheme -cne "file" -or
        $baseUri.Host -cne $targetUri.Host) {
      throw "non-file path"
    }
    $relative = [Uri]::UnescapeDataString($baseUri.MakeRelativeUri($targetUri).ToString()).Replace("\", "/")
    if ([string]::IsNullOrWhiteSpace($relative) -or
        [Uri]::IsWellFormedUriString($relative, [UriKind]::Absolute) -or
        $relative -match '^[A-Za-z]:[\\/]' -or
        $relative -match '^[A-Za-z][A-Za-z0-9+.-]*:' -or
        $relative.StartsWith("//", [StringComparison]::Ordinal) -or
        $relative.StartsWith("\\", [StringComparison]::Ordinal)) {
      throw "absolute result"
    }
    return $relative
  } catch {
    throw "BI_RELATIVE_FRONTEND_DIST_INVALID"
  }
}

$output = [IO.Path]::GetFullPath($OutputRoot)
$repoPrefix = $repo.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if ($output.StartsWith($repoPrefix, [StringComparison]::OrdinalIgnoreCase)) {
  throw "BI_PACKAGE_OUTPUT_MUST_BE_EXTERNAL"
}

if ($AllowDirty -and -not $AllowUnreleasedLoopCandidates) {
  throw "BI_FORMAL_SOURCE_MUST_BE_CLEAN"
}

if (-not $AllowDirty) {
  $dirty = (& git -C $repo status --porcelain=v1)
  if ($LASTEXITCODE -ne 0 -or $dirty) { throw "BI_PACKAGE_SOURCE_NOT_CLEAN" }
}

$version = [IO.File]::ReadAllText((Join-Path $repo "VERSION")).Trim()
$releaseInstallerName = "LCCoding-BI_2.7.0_x64-setup.exe"
$safeAssetPattern = '^[A-Za-z0-9][A-Za-z0-9._-]*$'
if ($version -ne "2.7.0" -or $releaseInstallerName -notmatch $safeAssetPattern) {
  throw "BI_RELEASE_ASSET_NAME_UNSAFE"
}
$commit = (& git -C $repo rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $commit -notmatch '^[0-9a-f]{40}$') {
  throw "BI_PROVENANCE_COMMIT_INVALID"
}
$rustVersion = @(& rustc -vV 2>$null)
$targetLine = @($rustVersion | Where-Object { $_ -match '^host: ' })
if ($LASTEXITCODE -ne 0 -or $targetLine.Count -ne 1) {
  throw "BI_PROVENANCE_TARGET_INVALID"
}
$targetTriple = $targetLine[0].Substring(6)
if ($targetTriple -notmatch '^[a-z0-9_]+-[a-z0-9_]+-[a-z0-9_.-]+$') {
  throw "BI_PROVENANCE_TARGET_INVALID"
}

if ($AllowUnreleasedLoopCandidates) {
  $loopGate = "BLOCKED_CANDIDATE_IDENTITIES"
  $loopReleaseProof = $null
  $buildMode = "LOCAL_BLOCKED_CANDIDATE"
  $buildWorkflow = "local-manual"
  $buildRunId = "local-$([guid]::NewGuid().ToString('D'))"
  $buildRunAttempt = $null
  $buildRepository = "LOCAL"
  $buildRef = (& git -C $repo branch --show-current).Trim()
  $buildRunUrl = $null
} else {
  $releaseVerifier = Join-Path $PSScriptRoot "verify-loop-releases.ps1"
  $formalRelease = & $releaseVerifier
  if ($formalRelease.status -ne "VERIFIED_FORMAL_RELEASES") {
    throw "BI_LOOP_RELEASE_DEPENDENCY_BLOCKED"
  }
  $loopGate = "VERIFIED_FORMAL_RELEASES"
  $loopReleaseProof = $formalRelease.methods
  if (
    $env:GITHUB_ACTIONS -ne "true" -or
    $env:GITHUB_REPOSITORY -ne "DWG7318/LCcoding" -or
    $env:GITHUB_SHA -ne $commit -or
    $env:GITHUB_RUN_ID -notmatch '^[1-9][0-9]*$' -or
    $env:GITHUB_RUN_ATTEMPT -notmatch '^[1-9][0-9]*$' -or
    [string]::IsNullOrWhiteSpace($env:GITHUB_WORKFLOW) -or
    [string]::IsNullOrWhiteSpace($env:GITHUB_REF)
  ) {
    throw "BI_FORMAL_BUILD_IDENTITY_INVALID"
  }
  $buildMode = "FORMAL_GITHUB_ACTIONS"
  $buildWorkflow = $env:GITHUB_WORKFLOW
  $buildRunId = $env:GITHUB_RUN_ID
  $buildRunAttempt = [int]$env:GITHUB_RUN_ATTEMPT
  $buildRepository = $env:GITHUB_REPOSITORY
  $buildRef = $env:GITHUB_REF
  $buildRunUrl = "https://github.com/$($env:GITHUB_REPOSITORY)/actions/runs/$($env:GITHUB_RUN_ID)"
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
$stagedTauriRoot = Join-Path $frontend "src-tauri"
Copy-Item -LiteralPath $sourceTauriRoot -Destination $stagedTauriRoot -Recurse -Force
$stagedRelease = Join-Path $frontend "release"
[IO.Directory]::CreateDirectory($stagedRelease) | Out-Null
Copy-Item -LiteralPath (Join-Path $bi "release/loop-contract-identities.json") -Destination (Join-Path $stagedRelease "loop-contract-identities.json") -Force

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
$relativeDist = Get-RelativeForwardPath $stagedTauriRoot $dist
$env:CARGO_TARGET_DIR = $cargoTarget.Replace("\", "/")
$env:TAURI_CONFIG = @{ build = @{ frontendDist = $relativeDist } } | ConvertTo-Json -Compress
$tauriConfigPath = Join-Path $output "tauri-build-config.json"
[IO.File]::WriteAllText($tauriConfigPath, $env:TAURI_CONFIG, [Text.UTF8Encoding]::new($false))
$tauriCli = Join-Path $frontend "node_modules/@tauri-apps/cli/tauri.js"

Push-Location $frontend
try {
  # tauri build uses the pinned CLI from the external runner.
  & node $tauriCli build --bundles nsis --ci --config $tauriConfigPath
  if ($LASTEXITCODE -ne 0) { throw "BI_TAURI_BUILD_FAILED" }
} finally {
  Pop-Location
}

$installers = @(Get-ChildItem -LiteralPath (Join-Path $cargoTarget "release/bundle/nsis") -Filter "*-setup.exe" -File)
if ($installers.Count -ne 1) { throw "BI_INSTALLER_COUNT_INVALID" }
$release = Join-Path $output "release"
[IO.Directory]::CreateDirectory($release) | Out-Null
$installer = Join-Path $release $releaseInstallerName
[IO.File]::Copy($installers[0].FullName, $installer, $true)
$installerHash = (Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant()
[IO.File]::WriteAllText(
  (Join-Path $release "installer.sha256"),
  "$installerHash  $([IO.Path]::GetFileName($installer))`n",
  [Text.UTF8Encoding]::new($false)
)

$provenance = [ordered]@{
  schema = "LCCoding 2.7.0 installer provenance"
  overall_version = $version
  commit = $commit
  asset = [IO.Path]::GetFileName($installer)
  sha256 = $installerHash
  package_lock_sha256 = (Get-FileHash -LiteralPath (Join-Path $bi "package-lock.json") -Algorithm SHA256).Hash.ToLowerInvariant()
  cargo_lock_sha256 = (Get-FileHash -LiteralPath (Join-Path $sourceTauriRoot "Cargo.lock") -Algorithm SHA256).Hash.ToLowerInvariant()
  build_mode = $buildMode
  build_workflow = $buildWorkflow
  build_run_id = $buildRunId
  build_run_attempt = $buildRunAttempt
  build_repository = $buildRepository
  build_ref = $buildRef
  build_run_url = $buildRunUrl
  target_triple = $targetTriple
  loop_release_dependency_gate = $loopGate
  loop_release_dependencies = $loopReleaseProof
  installer_scope = "current_user"
  webview2_mode = "embedBootstrapper"
}
$expectedProvenanceKeys = @(
  "schema",
  "overall_version",
  "commit",
  "asset",
  "sha256",
  "package_lock_sha256",
  "cargo_lock_sha256",
  "build_mode",
  "build_workflow",
  "build_run_id",
  "build_run_attempt",
  "build_repository",
  "build_ref",
  "build_run_url",
  "target_triple",
  "loop_release_dependency_gate",
  "loop_release_dependencies",
  "installer_scope",
  "webview2_mode"
)
if (@(Compare-Object $expectedProvenanceKeys @($provenance.Keys)).Count -ne 0) {
  throw "BI_PROVENANCE_SCHEMA_INVALID"
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
