[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$SourceRepository,
  [Parameter(Mandatory = $true)][string]$PackageDirectory,
  [Parameter(Mandatory = $true)][string]$EvidenceDirectory,
  [Parameter(Mandatory = $true)][string]$ExpectedCommit,
  [Parameter(Mandatory = $true)][string]$ExpectedHooksSha256
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExpectedInstallSmokeSha256 = "012f256f33f5ca089b6e269879e7568d6691a67576eb37f1a92e4b1c994ae132"
$ExpectedInstallerName = "LCCoding-BI_2.8.0_x64-setup.exe"
$InstallRoot = "D:\LCcoding\.codex\.tmp\lccoding-260-install-smoke\installed-current-user"
$BaselineMarker = "TASK22_WIN_CI_BASELINE_PATH"
$BaselinePath = 'C:\Task22\Alpha;;%USERPROFILE%\Task22Bin;C:\Task22\MixedCase;'
$ResultPath = Join-Path $EvidenceDirectory "result.json"
$env:GIT_CONFIG_COUNT = "1"
$env:GIT_CONFIG_KEY_0 = "core.autocrlf"
$env:GIT_CONFIG_VALUE_0 = "false"

function Get-Utf16Sha256 {
  param([AllowNull()][string]$Value)
  if ($null -eq $Value) { return "NOT_APPLICABLE" }
  $algorithm = [Security.Cryptography.SHA256]::Create()
  try {
    $bytes = [Text.Encoding]::Unicode.GetBytes($Value)
    return ([BitConverter]::ToString($algorithm.ComputeHash($bytes))).Replace("-", "").ToLowerInvariant()
  } finally {
    $algorithm.Dispose()
  }
}

function Get-RawUserPathState {
  $key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey("Environment", $false)
  if ($null -eq $key) {
    return [pscustomobject]@{ exists = $false; registry_kind = "NOT_APPLICABLE"; raw_value = $null }
  }
  try {
    $exists = @($key.GetValueNames() | Where-Object {
      $_.Equals("Path", [StringComparison]::OrdinalIgnoreCase)
    }).Count -eq 1
    if (-not $exists) {
      return [pscustomobject]@{ exists = $false; registry_kind = "NOT_APPLICABLE"; raw_value = $null }
    }
    $raw = [string]$key.GetValue(
      "Path",
      $null,
      [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames
    )
    return [pscustomobject]@{
      exists = $true
      registry_kind = $key.GetValueKind("Path").ToString()
      raw_value = $raw
    }
  } finally {
    $key.Dispose()
  }
}

function Set-BaselineUserPath {
  $key = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey("Environment")
  if ($null -eq $key) { throw "TASK22_WIN_CI_ENVIRONMENT_KEY_UNAVAILABLE" }
  try {
    $key.SetValue("Path", $BaselinePath, [Microsoft.Win32.RegistryValueKind]::ExpandString)
    $key.Flush()
  } finally {
    $key.Dispose()
  }
}

function Convert-PathEvidence {
  param([pscustomobject]$State)
  return [ordered]@{
    exists = [bool]$State.exists
    registry_kind = [string]$State.registry_kind
    raw_length = if ($null -eq $State.raw_value) { $null } else { $State.raw_value.Length }
    raw_sha256 = Get-Utf16Sha256 $State.raw_value
  }
}

function Test-RawExact {
  param([pscustomobject]$Before, [pscustomobject]$After)
  if ($Before.exists -ne $After.exists) { return $false }
  if (-not $Before.exists) { return $true }
  if ($Before.registry_kind -cne $After.registry_kind) { return $false }
  return $Before.raw_value.Equals($After.raw_value, [StringComparison]::Ordinal)
}

function Get-LccodingResidue {
  $uninstallRoot = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall"
  $entries = @()
  if (Test-Path -LiteralPath $uninstallRoot) {
    $entries = @(
      Get-ChildItem -LiteralPath $uninstallRoot -ErrorAction Stop | ForEach-Object {
        Get-ItemProperty -LiteralPath $_.PSPath -ErrorAction Stop
      } | Where-Object { $_.DisplayName -ceq "LCCoding BI" }
    )
  }
  $shortcut = Join-Path ([Environment]::GetFolderPath([Environment+SpecialFolder]::Programs)) "LCCoding BI.lnk"
  return [ordered]@{
    uninstall_record_count = $entries.Count
    install_root_exists = Test-Path -LiteralPath $InstallRoot
    shortcut_exists = Test-Path -LiteralPath $shortcut
    product_process_count = @(Get-Process -Name "lccoding-bi" -ErrorAction SilentlyContinue).Count
  }
}

function Assert-ZeroResidue {
  param([Collections.IDictionary]$Residue, [string]$Label)
  if ($Residue.uninstall_record_count -ne 0 -or
      $Residue.install_root_exists -or
      $Residue.shortcut_exists -or
      $Residue.product_process_count -ne 0) {
    throw "TASK22_WIN_CI_${Label}_RESIDUE"
  }
}

function Write-AtomicJson {
  param([string]$Path, [Collections.IDictionary]$Value)
  $parent = Split-Path $Path -Parent
  if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
    throw "TASK22_WIN_CI_EVIDENCE_DIRECTORY_MISSING"
  }
  if (Test-Path -LiteralPath $Path) { throw "TASK22_WIN_CI_RESULT_PREEXISTS" }
  $temporary = "$Path.tmp-$PID"
  $json = $Value | ConvertTo-Json -Depth 8
  [IO.File]::WriteAllText($temporary, "$json`n", [Text.UTF8Encoding]::new($false))
  [IO.File]::Move($temporary, $Path)
}

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
$result = [ordered]@{
  schema = "LCCoding Task22 Windows standard-user PATH roundtrip evidence"
  status = "PENDING"
  baseline_marker = $BaselineMarker
  expected_commit = $ExpectedCommit
  actual_commit = $null
  user_name = $identity.Name
  user_sid = $identity.User.Value
  administrator = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  session_id = (Get-Process -Id $PID).SessionId
  hooks_sha256 = $null
  provenance_commit = $null
  provenance_build_mode = $null
  before_path = $null
  after_path = $null
  exact_raw_match = $false
  exact_kind_match = $false
  process_exit_code = $null
  uninstall_parent_exit_code = $null
  residue_before = $null
  residue_after = $null
  smoke_output = @()
  error = $null
}
$exitCode = 1

try {
  if ($result.administrator) { throw "TASK22_WIN_CI_STANDARD_USER_REQUIRED" }
  if (Test-Path -LiteralPath $ResultPath) { throw "TASK22_WIN_CI_RESULT_PREEXISTS" }

  $localRoot = Join-Path $env:USERPROFILE "Task22WinCI"
  $localRepository = Join-Path $localRoot "repo"
  $localPackage = Join-Path $localRoot "package"
  if (Test-Path -LiteralPath $localRoot) { throw "TASK22_WIN_CI_LOCAL_ROOT_PREEXISTS" }
  New-Item -ItemType Directory -Path $localRepository -Force | Out-Null
  $null = & robocopy.exe $SourceRepository $localRepository /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /NFL /NDL /NJH /NJS /NP
  $copyExit = $LASTEXITCODE
  if ($copyExit -gt 7) { throw "TASK22_WIN_CI_REPOSITORY_COPY_FAILED_$copyExit" }

  $actualCommit = (& git -C $localRepository rev-parse HEAD).Trim()
  if ($LASTEXITCODE -ne 0 -or $actualCommit -cne $ExpectedCommit) {
    throw "TASK22_WIN_CI_REPOSITORY_COMMIT_INVALID"
  }
  if (& git -C $localRepository status --porcelain=v1) {
    throw "TASK22_WIN_CI_REPOSITORY_DIRTY"
  }
  $result.actual_commit = $actualCommit

  $hooks = Join-Path $localRepository "lc-coding/bi/src-tauri/windows/hooks.nsh"
  $hooksSha256 = (Get-FileHash -LiteralPath $hooks -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($hooksSha256 -cne $ExpectedHooksSha256) { throw "TASK22_WIN_CI_HOOKS_IDENTITY_INVALID" }
  $result.hooks_sha256 = $hooksSha256

  $smokeScript = Join-Path $localRepository "lc-coding/bi/tests/packaging/install-smoke.ps1"
  $smokeSha256 = (Get-FileHash -LiteralPath $smokeScript -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($smokeSha256 -cne $ExpectedInstallSmokeSha256) { throw "TASK22_WIN_CI_INSTALL_SMOKE_IDENTITY_INVALID" }

  New-Item -ItemType Directory -Path $localPackage -Force | Out-Null
  foreach ($file in @(Get-ChildItem -LiteralPath $PackageDirectory -File)) {
    Copy-Item -LiteralPath $file.FullName -Destination (Join-Path $localPackage $file.Name)
  }
  $expectedPackageFiles = @($ExpectedInstallerName, "installer.sha256", "provenance.json") | Sort-Object
  $actualPackageFiles = @(Get-ChildItem -LiteralPath $localPackage -File | ForEach-Object Name | Sort-Object)
  if (@(Compare-Object $expectedPackageFiles $actualPackageFiles).Count -ne 0) {
    throw "TASK22_WIN_CI_PACKAGE_SET_INVALID"
  }
  $provenance = Get-Content -LiteralPath (Join-Path $localPackage "provenance.json") -Raw | ConvertFrom-Json
  if ($provenance.commit -cne $ExpectedCommit -or $provenance.build_mode -cne "FORMAL_GITHUB_ACTIONS") {
    throw "TASK22_WIN_CI_PROVENANCE_INVALID"
  }
  $result.provenance_commit = [string]$provenance.commit
  $result.provenance_build_mode = [string]$provenance.build_mode

  $residueBefore = Get-LccodingResidue
  $result.residue_before = $residueBefore
  Assert-ZeroResidue $residueBefore "PREEXISTING"

  Set-BaselineUserPath
  $before = Get-RawUserPathState
  if (-not $before.exists -or $before.registry_kind -cne "ExpandString" -or
      -not $before.raw_value.Equals($BaselinePath, [StringComparison]::Ordinal)) {
    throw "TASK22_WIN_CI_BASELINE_PATH_INVALID"
  }
  $result.before_path = Convert-PathEvidence $before

  $installer = Join-Path $localPackage $ExpectedInstallerName
  $smokeOutput = @(
    & $smokeScript -Installer $installer -ExpectedVersion "2.8.0" 2>&1 |
      ForEach-Object { [string]$_ }
  )
  $result.smoke_output = $smokeOutput
  $passMarker = "PASS: BI current-user install smoke is clean, fixed-window, and source-immutable"
  if (@($smokeOutput | Where-Object { $_ -ceq $passMarker }).Count -ne 1) {
    throw "TASK22_WIN_CI_SMOKE_PASS_MARKER_MISSING"
  }
  $parentExitMarker = "INSTALL_SMOKE_UNINSTALL_PARENT_EXITCODE=0"
  if (@($smokeOutput | Where-Object { $_ -ceq $parentExitMarker }).Count -lt 1) {
    throw "TASK22_WIN_CI_UNINSTALL_PARENT_EXIT_INVALID"
  }
  $result.uninstall_parent_exit_code = 0

  $after = Get-RawUserPathState
  $result.after_path = Convert-PathEvidence $after
  $result.exact_raw_match = Test-RawExact $before $after
  $result.exact_kind_match = $before.registry_kind -ceq $after.registry_kind
  if (-not $result.exact_raw_match -or -not $result.exact_kind_match) {
    throw "TASK22_WIN_CI_PATH_ROUNDTRIP_INVALID"
  }

  $residueAfter = Get-LccodingResidue
  $result.residue_after = $residueAfter
  Assert-ZeroResidue $residueAfter "POSTFLIGHT"
  $result.status = "PASS"
  $exitCode = 0
} catch {
  $result.status = "FAIL"
  $result.error = [string]$_.Exception.Message
  try {
    $result.after_path = Convert-PathEvidence (Get-RawUserPathState)
    $result.residue_after = Get-LccodingResidue
  } catch {
    if ($null -eq $result.error) { $result.error = [string]$_.Exception.Message }
  }
} finally {
  $result.process_exit_code = $exitCode
  Write-AtomicJson $ResultPath $result
}

exit $exitCode
