[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$Installer,
  [Parameter(Mandatory = $true)]
  [string]$ExpectedVersion
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExpectedInstallerName = "LCCoding-BI_2.7.0_x64-setup.exe"
$ExpectedCurrentVersion = "2.7.0"
$SmokeRoot = "D:\LCcoding\.codex\.tmp\lccoding-260-install-smoke"
$TestProjectName = "test-project"
$SmokeInstallRootName = "installed-current-user"
$UninstallRegistry = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall"
$UserEnvironment = "HKCU:\Environment"
$WS_THICKFRAME = 0x00040000
$UninstallCompletionTimeoutSeconds = 60
$UninstallPollMilliseconds = 250
$UninstallParentExitTimeoutSeconds = 30

function Assert-ContainedPath {
  param([string]$Path, [string]$Root, [string]$Label)
  $fullPath = [IO.Path]::GetFullPath($Path)
  $fullRoot = [IO.Path]::GetFullPath($Root).TrimEnd([IO.Path]::DirectorySeparatorChar)
  $prefix = $fullRoot + [IO.Path]::DirectorySeparatorChar
  if (-not $fullPath.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "INSTALL_SMOKE_PATH_OUTSIDE_$Label"
  }
  return $fullPath
}

function Assert-ExternalToSource {
  param([string]$Path, [string]$SourceRoot, [string]$Label)
  $fullPath = [IO.Path]::GetFullPath($Path)
  $source = [IO.Path]::GetFullPath($SourceRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
  $prefix = $source + [IO.Path]::DirectorySeparatorChar
  if ($fullPath.Equals($source, [StringComparison]::OrdinalIgnoreCase) -or
      $fullPath.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "INSTALL_SMOKE_SOURCE_OVERLAP_$Label"
  }
  return $fullPath
}

function Get-TrackedSnapshot {
  param([string]$Repository)
  $tracked = @(& git -C $Repository ls-files)
  if ($LASTEXITCODE -ne 0 -or $tracked.Count -eq 0) {
    throw "INSTALL_SMOKE_SOURCE_TRACKING_INVALID"
  }
  $snapshot = @{}
  foreach ($relative in $tracked) {
    $path = Join-Path $Repository $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
      throw "INSTALL_SMOKE_TRACKED_FILE_MISSING"
    }
    $item = Get-Item -LiteralPath $path -Force
    $snapshot[$relative] = [pscustomobject]@{
      sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
      mtime_ticks = $item.LastWriteTimeUtc.Ticks
    }
  }
  return $snapshot
}

function Assert-TrackedSnapshot {
  param([string]$Repository, [hashtable]$Before)
  $after = Get-TrackedSnapshot $Repository
  if (@(Compare-Object @($Before.Keys) @($after.Keys)).Count -ne 0) {
    throw "INSTALL_SMOKE_SOURCE_TRACKED_PATHS_CHANGED"
  }
  foreach ($relative in $Before.Keys) {
    if ($Before[$relative].sha256 -cne $after[$relative].sha256 -or
        $Before[$relative].mtime_ticks -ne $after[$relative].mtime_ticks) {
      throw "INSTALL_SMOKE_SOURCE_BYTES_OR_MTIMES_CHANGED"
    }
  }
}

function Get-ExactUserPathValue {
  $value = Get-ItemProperty -LiteralPath $UserEnvironment -Name Path -ErrorAction SilentlyContinue
  if ($null -eq $value) { return $null }
  return [string]$value.Path
}

function Test-UserPathContains {
  param([AllowNull()][string]$PathValue, [string]$Directory)
  if ($null -eq $PathValue) { return $false }
  return @($PathValue.Split(';') | Where-Object {
    $_.TrimEnd([IO.Path]::DirectorySeparatorChar).Equals(
      $Directory.TrimEnd([IO.Path]::DirectorySeparatorChar),
      [StringComparison]::OrdinalIgnoreCase
    )
  }).Count -eq 1
}

function Assert-NullableExact {
  param([AllowNull()][string]$Expected, [AllowNull()][string]$Actual, [string]$Label)
  if ($null -eq $Expected -and $null -eq $Actual) { return }
  if ($null -eq $Expected -or $null -eq $Actual -or -not $Expected.Equals($Actual, [StringComparison]::Ordinal)) {
    throw "INSTALL_SMOKE_$Label"
  }
}

function Test-NullableExact {
  param([AllowNull()][string]$Expected, [AllowNull()][string]$Actual)
  if ($null -eq $Expected -and $null -eq $Actual) { return $true }
  if ($null -eq $Expected -or $null -eq $Actual) { return $false }
  return $Expected.Equals($Actual, [StringComparison]::Ordinal)
}

function Wait-Until {
  param([scriptblock]$Condition, [int]$TimeoutSeconds, [int]$PollMilliseconds, [string]$TimeoutError)
  $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
  do {
    if (& $Condition) { return }
    Start-Sleep -Milliseconds $PollMilliseconds
  } while ([DateTime]::UtcNow -lt $deadline)
  if (& $Condition) { return }
  throw $TimeoutError
}

function Get-OptionalRegistryText {
  param([object]$Record, [string]$Name)
  $property = $Record.PSObject.Properties[$Name]
  if ($null -eq $property) { return "" }
  return [string]$property.Value
}

function Convert-RegistryPath {
  param([string]$RawPath, [string]$Label)
  $value = $RawPath.Trim()
  if ($value.Length -ge 2 -and $value.StartsWith('"') -and $value.EndsWith('"')) {
    $value = $value.Substring(1, $value.Length - 2)
  }
  if ([string]::IsNullOrWhiteSpace($value) -or $value.Contains('"')) {
    throw "INSTALL_SMOKE_${Label}_PATH_INVALID"
  }
  try { return [IO.Path]::GetFullPath($value) } catch { throw "INSTALL_SMOKE_${Label}_PATH_INVALID" }
}

function Convert-DisplayIconPath {
  param([string]$RawPath)
  $match = [regex]::Match($RawPath.Trim(), '^"(?<path>[^"]+)"(?:,\d+)?$')
  if (-not $match.Success) {
    $match = [regex]::Match($RawPath.Trim(), '^(?<path>[^,"]+)(?:,\d+)?$')
  }
  if (-not $match.Success) { throw "INSTALL_SMOKE_DISPLAY_ICON_PATH_INVALID" }
  return Convert-RegistryPath $match.Groups["path"].Value "DISPLAY_ICON"
}

function Get-LccodingUninstallEntries {
  if (-not (Test-Path -LiteralPath $UninstallRegistry)) { return @() }
  return @(
    Get-ChildItem -LiteralPath $UninstallRegistry -ErrorAction Stop | ForEach-Object {
      $record = Get-ItemProperty -LiteralPath $_.PSPath -ErrorAction Stop
      $displayName = $record.PSObject.Properties["DisplayName"]
      if ($null -ne $displayName -and [string]$displayName.Value -ceq "LCCoding BI") {
        [pscustomobject]@{
          key = $_.PSPath
          display_name = [string]$displayName.Value
          display_version = Get-OptionalRegistryText $record "DisplayVersion"
          install_location = Get-OptionalRegistryText $record "InstallLocation"
          uninstall_string = Get-OptionalRegistryText $record "UninstallString"
          display_icon = Get-OptionalRegistryText $record "DisplayIcon"
        }
      }
    }
  )
}

function Test-UninstallCompletion {
  param([string]$InstallRoot, [string]$Shortcut, [AllowNull()][string]$OriginalUserPath)
  $entries = @(Get-LccodingUninstallEntries)
  return (
    $entries.Count -eq 0 -and
    -not (Test-Path -LiteralPath $InstallRoot) -and
    -not (Test-Path -LiteralPath $Shortcut) -and
    (Test-NullableExact $OriginalUserPath (Get-ExactUserPathValue))
  )
}

function Assert-NoPreexistingInstall {
  param([string]$Shortcut)
  $entries = @(Get-LccodingUninstallEntries)
  if ($entries.Count -ne 0) { throw "INSTALL_SMOKE_PREEXISTING_UNINSTALL_RECORD" }
  if (Test-Path -LiteralPath $Shortcut -PathType Leaf) { throw "INSTALL_SMOKE_PREEXISTING_SHORTCUT" }
}

function Assert-Artifact {
  param([string]$InstallerPath, [string]$Version, [string]$SourceRoot)
  if ($Version -cne $ExpectedCurrentVersion) { throw "INSTALL_SMOKE_VERSION_INVALID" }
  $fullInstaller = [IO.Path]::GetFullPath($InstallerPath)
  if ([IO.Path]::GetFileName($fullInstaller) -cne $ExpectedInstallerName -or
      -not (Test-Path -LiteralPath $fullInstaller -PathType Leaf)) {
    throw "INSTALL_SMOKE_INSTALLER_INVALID"
  }
  Assert-ExternalToSource $fullInstaller $SourceRoot "INSTALLER" | Out-Null
  $installerItem = Get-Item -LiteralPath $fullInstaller -Force
  if (($installerItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw "INSTALL_SMOKE_INSTALLER_REPARSE_POINT"
  }
  $release = Split-Path $fullInstaller -Parent
  $checksumPath = Join-Path $release "installer.sha256"
  $provenancePath = Join-Path $release "provenance.json"
  if (-not (Test-Path -LiteralPath $checksumPath -PathType Leaf) -or
      -not (Test-Path -LiteralPath $provenancePath -PathType Leaf)) {
    throw "INSTALL_SMOKE_RELEASE_EVIDENCE_MISSING"
  }
  $actualHash = (Get-FileHash -LiteralPath $fullInstaller -Algorithm SHA256).Hash.ToLowerInvariant()
  $checksum = [IO.File]::ReadAllText($checksumPath, [Text.UTF8Encoding]::new($false)).TrimEnd("`r", "`n")
  if ($checksum -cne "$actualHash  $ExpectedInstallerName") {
    throw "INSTALL_SMOKE_CHECKSUM_MISMATCH"
  }
  try { $provenance = [IO.File]::ReadAllText($provenancePath, [Text.UTF8Encoding]::new($false)) | ConvertFrom-Json -ErrorAction Stop } catch { throw "INSTALL_SMOKE_PROVENANCE_INVALID" }
  foreach ($property in @("schema", "overall_version", "asset", "sha256", "installer_scope")) {
    if ($null -eq $provenance.PSObject.Properties[$property]) { throw "INSTALL_SMOKE_PROVENANCE_INVALID" }
  }
  if ($provenance.schema -cne "LCCoding 2.7.0 installer provenance" -or
      $provenance.overall_version -cne $Version -or
      $provenance.asset -cne $ExpectedInstallerName -or
      $provenance.sha256 -cne $actualHash -or
      $provenance.installer_scope -cne "current_user") {
    throw "INSTALL_SMOKE_PROVENANCE_MISMATCH"
  }
  return $fullInstaller
}

function New-CanonicalTestProject {
  param([string]$Project)
  if (Test-Path -LiteralPath $Project) { throw "INSTALL_SMOKE_TEST_PROJECT_PREEXISTS" }
  New-Item -ItemType Directory -Path (Join-Path $Project ".lccoding") -Force | Out-Null
  [IO.File]::WriteAllText((Join-Path $Project "README.md"), "# Install smoke project`n", [Text.UTF8Encoding]::new($false))
  [IO.File]::WriteAllText((Join-Path $Project "VERSION"), "0.0.1`n", [Text.UTF8Encoding]::new($false))
  [IO.File]::WriteAllText((Join-Path $Project ".lccoding/status.json"), '{"record_role":"AUTHORITATIVE_PROJECT_STATUS","status_schema_version":"2.6.0","project_id":"install-smoke","current_phase":"INITIAL"}' + "`n", [Text.UTF8Encoding]::new($false))
  & git -C $Project init --quiet
  if ($LASTEXITCODE -ne 0) { throw "INSTALL_SMOKE_TEST_PROJECT_GIT_INIT_FAILED" }
  & git -C $Project config user.email "install-smoke@example.invalid"
  & git -C $Project config user.name "LCCoding Install Smoke"
  & git -C $Project add --all
  & git -C $Project commit --quiet -m "test: install smoke project"
  if ($LASTEXITCODE -ne 0) { throw "INSTALL_SMOKE_TEST_PROJECT_GIT_COMMIT_FAILED" }
}

function Invoke-SilentInstaller {
  param(
    [string]$FileName,
    [string]$WorkingDirectory,
    [string]$InstallRoot,
    [string]$AllowedSmokeRoot,
    [int]$TimeoutSeconds
  )
  try {
    $InstallRoot = Assert-ContainedPath $InstallRoot $AllowedSmokeRoot "INSTALL_TARGET"
  } catch {
    throw "INSTALL_SMOKE_INSTALL_TARGET_INVALID"
  }
  if (Test-Path -LiteralPath $InstallRoot) { throw "INSTALL_SMOKE_INSTALL_TARGET_INVALID" }
  $startInfo = [Diagnostics.ProcessStartInfo]::new()
  $startInfo.FileName = $FileName
  $startInfo.Arguments = "/S /D=$InstallRoot"
  $startInfo.WorkingDirectory = $WorkingDirectory
  $startInfo.UseShellExecute = $false
  $startInfo.CreateNoWindow = $true
  $process = [Diagnostics.Process]::Start($startInfo)
  if ($null -eq $process -or -not $process.WaitForExit($TimeoutSeconds * 1000)) {
    if ($null -ne $process) { $process.Kill() }
    throw "INSTALL_SMOKE_EXECUTABLE_TIMEOUT"
  }
  if ($process.ExitCode -ne 0) { throw "INSTALL_SMOKE_EXECUTABLE_FAILED" }
}

function Start-RestrictedLauncher {
  param([string]$Launcher, [string]$WorkingDirectory, [string]$SourceRoot)
  Assert-ExternalToSource $Launcher $SourceRoot "LAUNCHER" | Out-Null
  $startInfo = [Diagnostics.ProcessStartInfo]::new()
  $startInfo.FileName = $Launcher
  $startInfo.WorkingDirectory = $WorkingDirectory
  $startInfo.UseShellExecute = $false
  $startInfo.CreateNoWindow = $true
  $startInfo.EnvironmentVariables["PATH"] = "$env:WINDIR\System32;$env:WINDIR"
  $process = [Diagnostics.Process]::new()
  $process.StartInfo = $startInfo
  if (-not $process.Start()) { throw "INSTALL_SMOKE_LAUNCH_FAILED" }
  return $process
}

function Add-WindowInterop {
  if ($null -ne ("LccodingInstallSmoke.NativeWindow" -as [type])) { return }
  Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
namespace LccodingInstallSmoke {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
  public static class NativeWindow {
    [DllImport("user32.dll", SetLastError=true)] public static extern bool GetClientRect(IntPtr handle, out RECT rect);
    [DllImport("user32.dll", EntryPoint="GetWindowLongPtr", SetLastError=true)] public static extern IntPtr GetWindowLongPtr(IntPtr handle, int index);
  }
}
'@ -ErrorAction Stop
}

function Assert-FixedWindow {
  param([Diagnostics.Process]$Process)
  Add-WindowInterop
  $deadline = [DateTime]::UtcNow.AddSeconds(45)
  do {
    Start-Sleep -Milliseconds 500
    $Process.Refresh()
    $handle = $Process.MainWindowHandle
  } while ($handle -eq [IntPtr]::Zero -and [DateTime]::UtcNow -lt $deadline -and -not $Process.HasExited)
  if ($Process.HasExited -or $handle -eq [IntPtr]::Zero) { throw "INSTALL_SMOKE_WINDOW_NOT_FOUND" }
  $rect = [LccodingInstallSmoke.RECT]::new()
  if (-not [LccodingInstallSmoke.NativeWindow]::GetClientRect($handle, [ref]$rect)) { throw "INSTALL_SMOKE_WINDOW_RECT_UNAVAILABLE" }
  if (($rect.Right - $rect.Left) -ne 300 -or ($rect.Bottom - $rect.Top) -ne 480) {
    throw "INSTALL_SMOKE_WINDOW_SIZE_INVALID"
  }
  $style = [LccodingInstallSmoke.NativeWindow]::GetWindowLongPtr($handle, -16).ToInt64()
  if (($style -band $WS_THICKFRAME) -ne 0) { throw "INSTALL_SMOKE_WINDOW_RESIZABLE" }
}

function Stop-SmokeProcess {
  param([AllowNull()][Diagnostics.Process]$Process)
  if ($null -eq $Process) { return }
  try {
    if (-not $Process.HasExited) { [void]$Process.CloseMainWindow(); [void]$Process.WaitForExit(15000) }
    if (-not $Process.HasExited) { $Process.Kill(); [void]$Process.WaitForExit(15000) }
  } finally { $Process.Dispose() }
}

function Invoke-InstalledUninstall {
  param(
    [pscustomobject]$Entry,
    [string]$SourceRoot,
    [string]$UninstallWorkingDirectory,
    [string]$InstallRoot,
    [string]$Shortcut,
    [AllowNull()][string]$OriginalUserPath
  )
  if ([string]::IsNullOrWhiteSpace($Entry.uninstall_string)) { throw "INSTALL_SMOKE_UNINSTALL_STRING_MISSING" }
  $match = [regex]::Match($Entry.uninstall_string, '^\s*"?(?<path>[^"\s]+uninstall\.exe)"?', [Text.RegularExpressions.RegexOptions]::IgnoreCase)
  if (-not $match.Success) { throw "INSTALL_SMOKE_UNINSTALL_STRING_UNSAFE" }
  $uninstaller = Convert-RegistryPath $match.Groups["path"].Value "UNINSTALLER"
  Assert-ExternalToSource $uninstaller $SourceRoot "UNINSTALLER" | Out-Null
  Assert-ContainedPath $uninstaller $InstallRoot "UNINSTALLER" | Out-Null
  if (-not (Test-Path -LiteralPath $uninstaller -PathType Leaf)) { throw "INSTALL_SMOKE_UNINSTALLER_MISSING" }
  $workingDirectory = Assert-ContainedPath $UninstallWorkingDirectory "D:\LCcoding\.codex\.tmp" "UNINSTALL_WORKING_DIRECTORY"
  Assert-ExternalToSource $workingDirectory $SourceRoot "UNINSTALL_WORKING_DIRECTORY" | Out-Null
  $installPrefix = $InstallRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
  if ($workingDirectory.Equals($InstallRoot, [StringComparison]::OrdinalIgnoreCase) -or
      $workingDirectory.StartsWith($installPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "INSTALL_SMOKE_UNINSTALL_WORKING_DIRECTORY_OVERLAPS_INSTALL"
  }
  $startInfo = [Diagnostics.ProcessStartInfo]::new()
  $startInfo.FileName = $uninstaller
  $startInfo.Arguments = "/S"
  $startInfo.WorkingDirectory = $workingDirectory
  $startInfo.UseShellExecute = $false
  $startInfo.CreateNoWindow = $true
  $parent = [Diagnostics.Process]::Start($startInfo)
  if ($null -eq $parent) { throw "INSTALL_SMOKE_UNINSTALL_LAUNCH_FAILED" }
  $parentExitCode = "TIMEOUT"
  try {
    if ($parent.WaitForExit($UninstallParentExitTimeoutSeconds * 1000)) {
      $parentExitCode = [string]$parent.ExitCode
    }
  } finally {
    $parent.Dispose()
  }
  Write-Output "INSTALL_SMOKE_UNINSTALL_PARENT_EXITCODE=$parentExitCode"
  Wait-Until {
    Test-UninstallCompletion $InstallRoot $Shortcut $OriginalUserPath
  } $UninstallCompletionTimeoutSeconds $UninstallPollMilliseconds "INSTALL_SMOKE_UNINSTALL_COMPLETION_TIMEOUT_$parentExitCode"
}

$sourceRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "../../../.."))
$smokeRoot = [IO.Path]::GetFullPath($SmokeRoot)
$testProject = Assert-ContainedPath (Join-Path $smokeRoot $TestProjectName) $smokeRoot "SMOKE_ROOT"
$smokeInstallRoot = Assert-ContainedPath (Join-Path $smokeRoot $SmokeInstallRootName) $smokeRoot "SMOKE_INSTALL_ROOT"
$shortcut = Join-Path ([Environment]::GetFolderPath([Environment+SpecialFolder]::Programs)) "LCCoding BI.lnk"
$sourceSnapshot = Get-TrackedSnapshot $sourceRoot
$originalUserPath = Get-ExactUserPathValue
$launcherProcess = $null
$installedEntry = $null
$installedBySmoke = $false
$installRoot = $null

try {
  if ($ExpectedVersion -cne $ExpectedCurrentVersion) { throw "INSTALL_SMOKE_EXPECTED_VERSION_INVALID" }
  $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
  $principal = [Security.Principal.WindowsPrincipal]::new($identity)
  if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw "CURRENT_USER_INSTALL_REQUIRED" }
  $installerPath = Assert-Artifact $Installer $ExpectedVersion $sourceRoot
  Assert-ExternalToSource $smokeRoot $sourceRoot "SMOKE_ROOT" | Out-Null
  Assert-NoPreexistingInstall $shortcut
  if (Test-Path -LiteralPath $smokeRoot) {
    Assert-ContainedPath $smokeRoot "D:\LCcoding\.codex\.tmp" "SMOKE_ROOT" | Out-Null
    Remove-Item -LiteralPath $smokeRoot -Recurse -Force
  }
  New-CanonicalTestProject $testProject
  Invoke-SilentInstaller $installerPath $testProject $smokeInstallRoot $smokeRoot 180
  $entries = @(Get-LccodingUninstallEntries)
  if ($entries.Count -ne 1) { throw "INSTALL_SMOKE_UNINSTALL_RECORD_INVALID" }
  $installedEntry = $entries[0]
  if ($installedEntry.display_name -cne "LCCoding BI" -or $installedEntry.display_version -cne $ExpectedVersion -or
      [string]::IsNullOrWhiteSpace($installedEntry.install_location)) {
    throw "INSTALL_SMOKE_INSTALL_IDENTITY_INVALID"
  }
  $installRoot = Convert-RegistryPath $installedEntry.install_location "INSTALL_ROOT"
  if ($installRoot -cne $smokeInstallRoot) { throw "INSTALL_SMOKE_INSTALL_TARGET_INVALID" }
  Assert-ExternalToSource $installRoot $sourceRoot "INSTALL_ROOT" | Out-Null
  Assert-ContainedPath $installRoot $smokeRoot "INSTALL_ROOT" | Out-Null
  $installedBySmoke = $true
  if (-not (Test-UserPathContains (Get-ExactUserPathValue) $installRoot)) { throw "INSTALL_SMOKE_PATH_NOT_REGISTERED" }
  if (-not (Test-Path -LiteralPath $shortcut -PathType Leaf)) { throw "INSTALL_SMOKE_SHORTCUT_MISSING" }
  $launcher = Convert-DisplayIconPath $installedEntry.display_icon
  Assert-ContainedPath $launcher $installRoot "LAUNCHER" | Out-Null
  if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) { throw "INSTALL_SMOKE_LAUNCHER_MISSING" }
  $launcherProcess = Start-RestrictedLauncher $launcher $testProject $sourceRoot
  Assert-FixedWindow $launcherProcess
  Stop-SmokeProcess $launcherProcess
  $launcherProcess = $null
  Invoke-InstalledUninstall $installedEntry $sourceRoot $smokeRoot $installRoot $shortcut $originalUserPath
  Write-Output "PASS: BI current-user install smoke is clean, fixed-window, and source-immutable"
} finally {
  Stop-SmokeProcess $launcherProcess
  if ($installedBySmoke) {
    $remainingEntries = @(Get-LccodingUninstallEntries)
    if ($remainingEntries.Count -eq 1) {
      Invoke-InstalledUninstall $remainingEntries[0] $sourceRoot $smokeRoot $installRoot $shortcut $originalUserPath
    } elseif ($remainingEntries.Count -gt 1) {
      throw "INSTALL_SMOKE_MULTIPLE_UNINSTALL_RECORDS"
    } elseif (-not (Test-UninstallCompletion $installRoot $shortcut $originalUserPath)) {
      throw "INSTALL_SMOKE_UNINSTALL_CLEANUP_INCOMPLETE"
    }
  }
  if (Test-Path -LiteralPath $testProject) {
    Remove-Item -LiteralPath $testProject -Recurse -Force
  }
  if (Test-Path -LiteralPath $smokeRoot) {
    Assert-ContainedPath $smokeRoot "D:\LCcoding\.codex\.tmp" "SMOKE_ROOT" | Out-Null
    Remove-Item -LiteralPath $smokeRoot -Recurse -Force
  }
  Assert-TrackedSnapshot $sourceRoot $sourceSnapshot
}
