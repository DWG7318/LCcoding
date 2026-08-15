from pathlib import Path
import re
import shutil
import subprocess
import os


root = Path(__file__).resolve().parents[2]
script = root / "lc-coding/bi/tests/packaging/install-smoke.ps1"
assert script.is_file(), "current-user installer smoke script is absent"
text = script.read_text(encoding="utf-8")


parameter_match = re.search(r"(?ms)^param\(\s*(?P<body>.*?)^\)", text)
assert parameter_match, "smoke script must declare closed parameters"
parameters = parameter_match.group("body")
for marker in (
    "[Parameter(Mandatory = $true)]",
    "[string]$Installer",
    "[string]$ExpectedVersion",
):
    assert marker in parameters, f"missing closed smoke parameter: {marker}"

for marker in (
    '"LCCoding-BI_2.8.0_x64-setup.exe"',
    '"2.8.0"',
    '"LCCoding 2.8.0 installer provenance"',
    'D:\\LCcoding\\.codex\\.tmp\\lccoding-260-install-smoke',
    "Assert-ContainedPath",
    "Assert-ExternalToSource",
    "Get-TrackedSnapshot",
    "Assert-TrackedSnapshot",
    "installer.sha256",
    "provenance.json",
    "Get-FileHash",
    "CURRENT_USER_INSTALL_REQUIRED",
    "ProcessStartInfo",
    'Arguments = "/S /D=$InstallRoot"',
    "PATH",
    "GetClientRect",
    "300",
    "480",
    "WS_THICKFRAME",
    "HKCU:\\Environment",
    "CurrentVersion\\Uninstall",
    "SpecialFolder]::Programs",
    "UninstallString",
    "finally",
    "Remove-Item -LiteralPath $testProject -Recurse -Force",
):
    assert marker in text, f"missing installer-smoke contract: {marker}"

assert "GetWindowRect" not in text, (
    "Tauri 300x480 is the Win32 client area, not the decorated outer frame"
)

for forbidden in (
    "Start-Process -Verb RunAs",
    "node_modules",
    "cargo-target",
    "npm ci",
    "cargo test",
):
    assert forbidden not in text, f"smoke must not build or elevate: {forbidden}"
assert '$record.DisplayName' not in text, (
    "strict current-user uninstall enumeration must tolerate unrelated keys"
)
assert '$record.PSObject.Properties["DisplayName"]' in text
assert "(Get-LccodingUninstallEntries).Count" not in text, (
    "an empty uninstall-record enumeration must remain an explicit array"
)
assert "@(Get-LccodingUninstallEntries)" in text
for marker in (
    "function Convert-RegistryPath",
    "$installedBySmoke = $false",
    "$installedBySmoke = $true",
    "if ($installedBySmoke)",
):
    assert marker in text, f"missing preexisting-install preservation contract: {marker}"

uninstall_start = text.index("function Invoke-InstalledUninstall")
uninstall_end = text.index("$sourceRoot =", uninstall_start)
uninstall = text[uninstall_start:uninstall_end]
assert "Invoke-SilentExecutable $uninstaller" not in uninstall, (
    "the NSIS uninstaller must not be rejected solely by its parent exit code"
)
for marker in (
    "$UninstallCompletionTimeoutSeconds = 60",
    "$UninstallPollMilliseconds = 250",
    "function Wait-Until",
    "function Test-UninstallCompletion",
    "INSTALL_SMOKE_UNINSTALL_COMPLETION_TIMEOUT_",
    "INSTALL_SMOKE_UNINSTALL_PARENT_EXITCODE=",
    "Get-LccodingUninstallEntries",
    "Test-Path -LiteralPath $InstallRoot",
    "Test-Path -LiteralPath $Shortcut",
    "Test-NullableExact $OriginalUserPath (Get-ExactUserPathValue)",
):
    assert marker in text, f"missing bounded uninstall completion contract: {marker}"

for marker in (
    '$SmokeInstallRootName = "installed-current-user"',
    '$smokeInstallRoot = Assert-ContainedPath (Join-Path $smokeRoot $SmokeInstallRootName) $smokeRoot "SMOKE_INSTALL_ROOT"',
    "function Invoke-SilentInstaller",
    '$startInfo.Arguments = "/S /D=$InstallRoot"',
    "INSTALL_SMOKE_INSTALL_TARGET_INVALID",
    '$installRoot -cne $smokeInstallRoot',
):
    assert marker in text, f"missing fixed NSIS install target contract: {marker}"
assert "Invoke-SilentExecutable $installerPath" not in text, (
    "installer must use the fixed /D= smoke target"
)

package_release = (root / "lc-coding/bi/scripts/package-release.ps1").read_text(
    encoding="utf-8"
)
assert "[IO.Path]::GetRelativePath" not in package_release, (
    "package-release must not depend on the PowerShell 7-only GetRelativePath API"
)
for marker in (
    "function Get-RelativeForwardPath",
    "MakeRelativeUri",
    "UnescapeDataString",
    "BI_RELATIVE_FRONTEND_DIST_INVALID",
    "$relativeDist = Get-RelativeForwardPath $stagedTauriRoot $dist",
):
    assert marker in package_release, f"missing PowerShell 5.1 relative-path contract: {marker}"
assert 'frontendDist = $relativeDist' in package_release
assert '--config $env:TAURI_CONFIG' not in package_release, (
    "PowerShell 5.1 native argument parsing must not carry JSON directly"
)
for marker in (
    '$tauriConfigPath = Join-Path $output "tauri-build-config.json"',
    '[IO.File]::WriteAllText($tauriConfigPath, $env:TAURI_CONFIG',
    '--config $tauriConfigPath',
):
    assert marker in package_release, f"missing PowerShell 5.1 Tauri config-file contract: {marker}"
for marker in (
    '$stagedRelease = Join-Path $frontend "release"',
    'Join-Path $bi "release/loop-contract-identities.json"',
    'Join-Path $stagedRelease "loop-contract-identities.json"',
):
    assert marker in package_release, f"missing external compatibility-asset staging: {marker}"

available_hosts = tuple(
    (name, path)
    for name in ("pwsh", "powershell")
    if (path := shutil.which(name)) is not None
)
assert available_hosts, "at least one PowerShell host is required for parser validation"
assert tuple(name for name, _ in available_hosts) == tuple(
    name for name in ("pwsh", "powershell") if shutil.which(name) is not None
)
if os.name == "nt":
    assert any(name == "powershell" for name, _ in available_hosts), (
        "Windows PowerShell 5.1 is required on Windows"
    )
else:
    assert any(name == "pwsh" for name, _ in available_hosts), (
        "pwsh is required for parser validation outside Windows"
    )

for host_name, host_path in available_hosts:
    parse = subprocess.run(
        [
            host_path,
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "$errors = @(); [void][System.Management.Automation.Language.Parser]::ParseFile($env:INSTALL_SMOKE_SCRIPT, [ref]$null, [ref]$errors); if ($errors.Count) { $errors | ForEach-Object { $_.Message }; exit 1 }",
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "INSTALL_SMOKE_SCRIPT": str(script)},
    )
    assert parse.returncode == 0, host_name + "\n" + parse.stdout + parse.stderr

print("PASS: install smoke parser hosts=" + ",".join(name for name, _ in available_hosts))
print("PASS: BI current-user install smoke contract is closed and externally bounded")
