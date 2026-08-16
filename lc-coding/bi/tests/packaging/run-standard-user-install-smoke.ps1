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

$ExpectedRepository = "DWG7318/LCcoding"
$ExpectedInstallerName = "LCCoding-BI_2.8.0_x64-setup.exe"
$ExpectedChildSha256 = "f78032b7b309b62e2f8e95da82270e44c3aeb8a17e280422a143670bad47013a"
$ChildRelativePath = "lc-coding/bi/tests/packaging/standard-user-install-smoke.ps1"
$SmokeParent = "D:\LCcoding\.codex\.tmp"
$ResultPath = Join-Path $EvidenceDirectory "orchestrator-result.json"
$ChildResultPath = Join-Path $EvidenceDirectory "result.json"

function Write-AtomicJson {
  param([string]$Path, [Collections.IDictionary]$Value)
  $parent = Split-Path $Path -Parent
  if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
    throw "TASK22_WIN_CI_EVIDENCE_DIRECTORY_MISSING"
  }
  if (Test-Path -LiteralPath $Path) { throw "TASK22_WIN_CI_PARENT_RESULT_PREEXISTS" }
  $temporary = "$Path.tmp-$PID"
  $json = $Value | ConvertTo-Json -Depth 10
  [IO.File]::WriteAllText($temporary, "$json`n", [Text.UTF8Encoding]::new($false))
  [IO.File]::Move($temporary, $Path)
}

function Get-LowerSha256 {
  param([string]$Path)
  return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Assert-ExactFields {
  param([pscustomobject]$Value, [string[]]$Expected, [string]$ErrorId)
  $actual = @($Value.PSObject.Properties.Name | Sort-Object)
  $closed = @($Expected | Sort-Object)
  if (@(Compare-Object $closed $actual).Count -ne 0) { throw $ErrorId }
}

function Get-PackageIdentity {
  param([string]$Directory)
  if (-not (Test-Path -LiteralPath $Directory -PathType Container)) {
    throw "TASK22_WIN_CI_PACKAGE_DIRECTORY_MISSING"
  }
  $expectedFiles = @($ExpectedInstallerName, "installer.sha256", "provenance.json") | Sort-Object
  $actualFiles = @(Get-ChildItem -LiteralPath $Directory -File | ForEach-Object Name | Sort-Object)
  if (@(Compare-Object $expectedFiles $actualFiles).Count -ne 0) {
    throw "TASK22_WIN_CI_PACKAGE_SET_INVALID"
  }
  $installer = [IO.Path]::GetFullPath((Join-Path $Directory $ExpectedInstallerName))
  $sha256 = Get-LowerSha256 $installer
  $checksumText = (Get-Content -LiteralPath (Join-Path $Directory "installer.sha256") -Raw).Trim()
  $checksumMatch = [regex]::Match($checksumText, "^([0-9a-f]{64})  ([A-Za-z0-9][A-Za-z0-9._-]*)$")
  if (-not $checksumMatch.Success -or
      $checksumMatch.Groups[1].Value -cne $sha256 -or
      $checksumMatch.Groups[2].Value -cne $ExpectedInstallerName) {
    throw "TASK22_WIN_CI_PACKAGE_CHECKSUM_INVALID"
  }
  $provenance = Get-Content -LiteralPath (Join-Path $Directory "provenance.json") -Raw | ConvertFrom-Json
  if ($provenance.asset -cne $ExpectedInstallerName -or
      $provenance.sha256 -cne $sha256 -or
      $provenance.commit -cne $ExpectedCommit -or
      $provenance.build_mode -cne "FORMAL_GITHUB_ACTIONS" -or
      $provenance.build_repository -cne $env:GITHUB_REPOSITORY -or
      $provenance.build_ref -cne $env:GITHUB_REF -or
      $provenance.build_workflow -cne $env:GITHUB_WORKFLOW -or
      $provenance.build_run_id -cne $env:GITHUB_RUN_ID -or
      $provenance.build_run_attempt -ne [int]$env:GITHUB_RUN_ATTEMPT) {
    throw "TASK22_WIN_CI_PACKAGE_PROVENANCE_INVALID"
  }
  return [ordered]@{
    installer = $installer
    sha256 = $sha256
    checksum_sha256 = $checksumMatch.Groups[1].Value
    provenance_sha256 = [string]$provenance.sha256
  }
}

$result = [ordered]@{
  schema = "LCCoding BI standard-user smoke orchestration evidence 2.8.0"
  status = "PENDING"
  repository = [string]$env:GITHUB_REPOSITORY
  commit = $ExpectedCommit
  workflow = [string]$env:GITHUB_WORKFLOW
  workflow_run_id = [string]$env:GITHUB_RUN_ID
  workflow_run_attempt = [string]$env:GITHUB_RUN_ATTEMPT
  workflow_ref = [string]$env:GITHUB_REF
  installer_basename = $ExpectedInstallerName
  installer_path = $null
  pre_smoke_sha256 = $null
  smoked_installer_sha256 = $null
  post_smoke_sha256 = $null
  checksum_sha256 = $null
  provenance_sha256 = $null
  child_script_path = $ChildRelativePath
  child_script_sha256 = $null
  child_result_path = "result.json"
  child_result_sha256 = $null
  observed_child_exit_code = "UNAVAILABLE_BY_CROSS_CREDENTIAL_API"
  child_process_exit_code = $null
  child_status = "UNPROVED"
  standard_user_sid = $null
  administrator = $null
  session_id = $null
  exact_raw_match = $false
  exact_kind_match = $false
  uninstall_parent_exit_code = $null
  residue_after = $null
  temporary_user_cleanup = "PENDING"
  error = $null
}

$userName = $null
$executionPassed = $false
$exitCode = 1

try {
  if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw "TASK22_WIN_CI_WINDOWS_REQUIRED"
  }
  if ($env:GITHUB_ACTIONS -cne "true") { throw "TASK22_WIN_CI_GITHUB_ACTIONS_REQUIRED" }
  if ($env:RUNNER_ENVIRONMENT -cne "github-hosted") { throw "TASK22_WIN_CI_GITHUB_HOSTED_REQUIRED" }
  if ($env:GITHUB_REPOSITORY -cne "DWG7318/LCcoding") { throw "TASK22_WIN_CI_REPOSITORY_INVALID" }
  foreach ($name in @("GITHUB_SHA", "GITHUB_WORKFLOW", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "GITHUB_REF")) {
    if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name))) {
      throw "TASK22_WIN_CI_IDENTITY_MISSING:$name"
    }
  }
  if ($env:GITHUB_SHA -cne $ExpectedCommit) { throw "TASK22_WIN_CI_COMMIT_ENV_INVALID" }
  if ($ExpectedCommit -cnotmatch "^[0-9a-f]{40}$" -or
      $ExpectedHooksSha256 -cnotmatch "^[0-9a-f]{64}$") {
    throw "TASK22_WIN_CI_EXPECTED_IDENTITY_INVALID"
  }
  if (-not (Test-Path -LiteralPath $SourceRepository -PathType Container)) {
    throw "TASK22_WIN_CI_SOURCE_MISSING"
  }
  $resolvedSource = (Resolve-Path -LiteralPath $SourceRepository).Path
  $resolvedWorkspace = (Resolve-Path -LiteralPath $env:GITHUB_WORKSPACE).Path
  if ($resolvedSource -cne $resolvedWorkspace) { throw "TASK22_WIN_CI_SOURCE_NOT_WORKSPACE" }
  $actualCommit = (& git -C $resolvedSource rev-parse HEAD).Trim()
  if ($LASTEXITCODE -ne 0 -or $actualCommit -cne $ExpectedCommit) {
    throw "TASK22_WIN_CI_SOURCE_COMMIT_INVALID"
  }
  if (& git -C $resolvedSource status --porcelain=v1) { throw "TASK22_WIN_CI_SOURCE_DIRTY" }
  if (Test-Path -LiteralPath $EvidenceDirectory) { throw "TASK22_WIN_CI_EVIDENCE_PREEXISTS" }
  New-Item -ItemType Directory -Path $EvidenceDirectory | Out-Null
  if (-not (Test-Path -LiteralPath $SmokeParent -PathType Container)) {
    New-Item -ItemType Directory -Path $SmokeParent -Force | Out-Null
  }

  $package = Get-PackageIdentity $PackageDirectory
  $result.installer_path = $package.installer
  $result.pre_smoke_sha256 = $package.sha256
  $result.checksum_sha256 = $package.checksum_sha256
  $result.provenance_sha256 = $package.provenance_sha256

  $childScript = Join-Path $resolvedSource $ChildRelativePath
  $childScriptSha256 = Get-LowerSha256 $childScript
  if ($childScriptSha256 -cne $ExpectedChildSha256) { throw "TASK22_WIN_CI_CHILD_IDENTITY_INVALID" }
  $result.child_script_sha256 = $childScriptSha256

  $randomName = New-Object byte[] 6
  $generator = [Security.Cryptography.RandomNumberGenerator]::Create()
  try { $generator.GetBytes($randomName) } finally { $generator.Dispose() }
  $userName = "LcSmoke" + ([BitConverter]::ToString($randomName)).Replace("-", "")
  [Array]::Clear($randomName, 0, $randomName.Length)
  if (Get-LocalUser -Name $userName -ErrorAction SilentlyContinue) { throw "TASK22_WIN_CI_USER_PREEXISTS" }

  $randomPassword = New-Object byte[] 32
  $passwordGenerator = [Security.Cryptography.RandomNumberGenerator]::Create()
  try { $passwordGenerator.GetBytes($randomPassword) } finally { $passwordGenerator.Dispose() }
  $plainPassword = [Convert]::ToBase64String($randomPassword) + "aA1!"
  [Array]::Clear($randomPassword, 0, $randomPassword.Length)
  $securePassword = ConvertTo-SecureString $plainPassword -AsPlainText -Force
  $credential = [Management.Automation.PSCredential]::new(".\$userName", $securePassword)
  $plainPassword = $null

  New-LocalUser -Name $userName -Password $securePassword -AccountNeverExpires -UserMayNotChangePassword | Out-Null
  $localUser = Get-LocalUser -Name $userName -ErrorAction Stop
  $usersSid = [Security.Principal.SecurityIdentifier]::new("S-1-5-32-545")
  $administratorsSid = [Security.Principal.SecurityIdentifier]::new("S-1-5-32-544")
  Add-LocalGroupMember -SID $usersSid -Member $localUser -ErrorAction Stop
  $users = @(Get-LocalGroupMember -SID $usersSid -ErrorAction Stop | Where-Object SID -eq $localUser.SID)
  $administrators = @(Get-LocalGroupMember -SID $administratorsSid -ErrorAction Stop | Where-Object SID -eq $localUser.SID)
  if ($users.Count -ne 1 -or $administrators.Count -ne 0) { throw "TASK22_WIN_CI_USER_ROLE_INVALID" }

  foreach ($grant in @(
    [pscustomobject]@{ path = $resolvedSource; rights = "RX" },
    [pscustomobject]@{ path = $PackageDirectory; rights = "RX" },
    [pscustomobject]@{ path = $EvidenceDirectory; rights = "M" },
    [pscustomobject]@{ path = $SmokeParent; rights = "M" }
  )) {
    & icacls.exe $grant.path /grant "${userName}:(OI)(CI)$($grant.rights)" /T /C | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "TASK22_WIN_CI_ACL_FAILED" }
  }

  $arguments = @(
    "-NoLogo", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
    "-File", ('"{0}"' -f $childScript),
    "-SourceRepository", ('"{0}"' -f $resolvedSource),
    "-PackageDirectory", ('"{0}"' -f $PackageDirectory),
    "-EvidenceDirectory", ('"{0}"' -f $EvidenceDirectory),
    "-ExpectedCommit", $ExpectedCommit,
    "-ExpectedHooksSha256", $ExpectedHooksSha256
  )
  $process = Start-Process -FilePath "powershell.exe" -ArgumentList $arguments -Credential $credential -LoadUserProfile -WindowStyle Hidden -PassThru
  if (-not $process.WaitForExit(1200000)) {
    Stop-Process -Id $process.Id -Force
    throw "TASK22_WIN_CI_STANDARD_USER_TIMEOUT"
  }
  $process.Refresh()
  if ($null -ne $process.ExitCode) { $result.observed_child_exit_code = [int]$process.ExitCode }
  $process.Dispose()

  if (-not (Test-Path -LiteralPath $ChildResultPath -PathType Leaf)) { throw "TASK22_WIN_CI_CHILD_RESULT_MISSING" }
  $childResult = Get-Content -LiteralPath $ChildResultPath -Raw | ConvertFrom-Json
  $expectedChildFields = @(
    "schema", "status", "baseline_marker", "expected_commit", "actual_commit",
    "user_name", "user_sid", "administrator", "session_id", "hooks_sha256",
    "provenance_commit", "provenance_build_mode", "before_path", "after_path",
    "exact_raw_match", "exact_kind_match", "process_exit_code",
    "uninstall_parent_exit_code", "residue_before", "residue_after",
    "smoke_output", "error"
  )
  Assert-ExactFields $childResult $expectedChildFields "TASK22_WIN_CI_CHILD_SCHEMA_INVALID"
  $result.child_result_sha256 = Get-LowerSha256 $ChildResultPath
  $result.child_process_exit_code = $childResult.process_exit_code
  $result.child_status = [string]$childResult.status
  $result.standard_user_sid = [string]$childResult.user_sid
  $result.administrator = [bool]$childResult.administrator
  $result.session_id = [int]$childResult.session_id
  $result.exact_raw_match = [bool]$childResult.exact_raw_match
  $result.exact_kind_match = [bool]$childResult.exact_kind_match
  $result.uninstall_parent_exit_code = $childResult.uninstall_parent_exit_code
  $result.residue_after = $childResult.residue_after

  if ($result.observed_child_exit_code -is [int] -and
      $result.observed_child_exit_code -ne $childResult.process_exit_code) {
    throw "TASK22_WIN_CI_PROCESS_EXIT_MISMATCH"
  }
  if ($childResult.status -cne "PASS" -or
      $childResult.process_exit_code -ne 0 -or
      $childResult.expected_commit -cne $ExpectedCommit -or
      $childResult.actual_commit -cne $ExpectedCommit -or
      $childResult.hooks_sha256 -cne $ExpectedHooksSha256 -or
      $childResult.provenance_commit -cne $ExpectedCommit -or
      $childResult.provenance_build_mode -cne "FORMAL_GITHUB_ACTIONS" -or
      $childResult.user_sid -cne $localUser.SID.Value -or
      $childResult.administrator -ne $false -or
      $childResult.session_id -lt 1 -or
      $childResult.exact_raw_match -ne $true -or
      $childResult.exact_kind_match -ne $true -or
      $childResult.uninstall_parent_exit_code -ne 0 -or
      $childResult.residue_after.uninstall_record_count -ne 0 -or
      $childResult.residue_after.install_root_exists -or
      $childResult.residue_after.shortcut_exists -or
      $childResult.residue_after.product_process_count -ne 0) {
    throw "TASK22_WIN_CI_CHILD_RESULT_INVALID"
  }

  $profiles = @(Get-CimInstance -ClassName Win32_UserProfile | Where-Object SID -ceq $localUser.SID.Value)
  if ($profiles.Count -ne 1 -or [string]::IsNullOrWhiteSpace([string]$profiles[0].LocalPath)) {
    throw "TASK22_WIN_CI_STANDARD_USER_PROFILE_INVALID"
  }
  $smokedInstaller = Join-Path $profiles[0].LocalPath "Task22WinCI\package\$ExpectedInstallerName"
  if (-not (Test-Path -LiteralPath $smokedInstaller -PathType Leaf)) {
    throw "TASK22_WIN_CI_SMOKED_INSTALLER_MISSING"
  }
  $smokedSha256 = Get-LowerSha256 $smokedInstaller
  $result.smoked_installer_sha256 = $smokedSha256
  if ($smokedSha256 -cne $result.pre_smoke_sha256) {
    throw "TASK22_WIN_CI_SMOKED_INSTALLER_IDENTITY_INVALID"
  }

  $postSha256 = Get-LowerSha256 $package.installer
  $result.post_smoke_sha256 = $postSha256
  if ($postSha256 -cne $result.pre_smoke_sha256 -or
      $postSha256 -cne $result.checksum_sha256 -or
      $postSha256 -cne $result.provenance_sha256) {
    throw "TASK22_WIN_CI_INSTALLER_CHANGED_BY_SMOKE"
  }
  $executionPassed = $true
} catch {
  $result.error = [string]$_.Exception.Message
} finally {
  try {
    if ($null -ne $userName -and (Get-LocalUser -Name $userName -ErrorAction SilentlyContinue)) {
      Remove-LocalUser -Name $userName
    }
    if ($null -ne $userName -and (Get-LocalUser -Name $userName -ErrorAction SilentlyContinue)) {
      throw "TASK22_WIN_CI_USER_CLEANUP_FAILED"
    }
    $result.temporary_user_cleanup = "PASS"
  } catch {
    $result.temporary_user_cleanup = "FAIL"
    $result.error = [string]$_.Exception.Message
    $executionPassed = $false
  }
  if ($executionPassed -and $result.temporary_user_cleanup -ceq "PASS") {
    $result.status = "PASS"
    $exitCode = 0
  } else {
    $result.status = "FAIL"
  }
  if (Test-Path -LiteralPath $EvidenceDirectory -PathType Container) {
    Write-AtomicJson $ResultPath $result
  }
}

exit $exitCode
