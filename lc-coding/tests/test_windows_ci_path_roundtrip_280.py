from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/validate.yml"
LAUNCHER = (
    ROOT
    / "lc-coding/bi/tests/packaging/standard-user-install-smoke.ps1"
)

assert WORKFLOW.is_file(), "Validate LCCoding workflow is missing"
assert LAUNCHER.is_file(), "standard-user install-smoke launcher is missing"

workflow = WORKFLOW.read_text(encoding="utf-8")
launcher = LAUNCHER.read_text(encoding="utf-8")

assert "on: [push, pull_request]" in workflow
assert "runs-on: ubuntu-latest" in workflow
job_marker = "  validate-windows-path-roundtrip:"
assert job_marker in workflow
windows_job = workflow[workflow.index(job_marker) :]
safe_failure_line = (
    'throw "TASK22_WIN_CI_STANDARD_USER_FAILED:'
    'observed=${childExitCode}:result=$($result.process_exit_code):'
    '$($result.error)"'
)
assert safe_failure_line in windows_job
assert (
    'TASK22_WIN_CI_STANDARD_USER_FAILED:$childExitCode:$($result.error)'
    not in windows_job
)

for marker in (
    "runs-on: windows-latest",
    "actions/checkout@v4",
    "fetch-depth: 0",
    "actions/setup-node@v4",
    'node-version: "24"',
    "dtolnay/rust-toolchain@stable",
    "toolchain: 1.96.0",
    "package-release.ps1 -OutputRoot $outputRoot",
    "New-LocalUser",
    "Add-LocalGroupMember",
    "Get-LocalGroupMember",
    'SecurityIdentifier]::new("S-1-5-32-545")',
    'SecurityIdentifier]::new("S-1-5-32-544")',
    "Add-LocalGroupMember -SID $usersSid -Member $localUser",
    "Get-LocalGroupMember -SID $usersSid",
    "Get-LocalGroupMember -SID $administratorsSid",
    "Start-Process",
    "-Credential $credential",
    "-LoadUserProfile",
    "standard-user-install-smoke.ps1",
    "FORMAL_GITHUB_ACTIONS",
    "actions/upload-artifact@v4",
    "if: always()",
    "task22-win-ci-evidence",
    "e25a7bd12d9921444d8fe51578a3fa67f48d67e5175a57bb5303b01c297f4a47",
    "$result.user_sid -ne $localUser.SID.Value",
    '$result.before_path.registry_kind -ne "ExpandString"',
    "$result.before_path.raw_sha256 -ne $result.after_path.raw_sha256",
    "$result.before_path.raw_length -ne $result.after_path.raw_length",
    "$result.residue_after.uninstall_record_count -ne 0",
    "$result.residue_after.install_root_exists",
    "$result.residue_after.shortcut_exists",
    "$result.residue_after.product_process_count -ne 0",
    "$null -ne $childExitCode",
    "$childExitCode -ne $result.process_exit_code",
    "$result.process_exit_code -ne 0",
):
    assert marker in windows_job, marker

assert windows_job.count("New-LocalUser") == 1
assert windows_job.count("Add-LocalGroupMember") == 1
assert windows_job.count("-Credential $credential") == 1
local_user_load = "Get-LocalUser -Name $userName -ErrorAction Stop"
assert windows_job.index("New-LocalUser") < windows_job.index(local_user_load)
assert windows_job.index(local_user_load) < windows_job.index("Add-LocalGroupMember")
assert windows_job.index("Add-LocalGroupMember") < windows_job.index(
    "Get-LocalGroupMember"
)
for forbidden in (
    "-AllowDirty",
    "WindowsSandbox",
    ".wsb",
    "docker",
    "psexec",
    "Register-ScheduledTask",
    "runas",
    "git push",
    "git tag",
    "gh release",
    'Get-LocalGroupMember -Group "Users"',
    'Get-LocalGroupMember -Group "Administrators"',
):
    assert forbidden.lower() not in windows_job.lower(), forbidden

for marker in (
    "function Get-RawUserPathState",
    "function Get-LccodingResidue",
    "function Write-AtomicJson",
    '$env:GIT_CONFIG_COUNT = "1"',
    '$env:GIT_CONFIG_KEY_0 = "core.autocrlf"',
    '$env:GIT_CONFIG_VALUE_0 = "false"',
    "param([Collections.IDictionary]$Residue, [string]$Label)",
    "param([string]$Path, [Collections.IDictionary]$Value)",
    "RegistryValueOptions]::DoNotExpandEnvironmentNames",
    'GetValueKind("Path")',
    "RegistryValueKind]::ExpandString",
    "TASK22_WIN_CI_BASELINE_PATH",
    "StringComparison]::Ordinal",
    'git -C $localRepository rev-parse HEAD',
    'git -C $localRepository status --porcelain=v1',
    "install-smoke.ps1",
    "012f256f33f5ca089b6e269879e7568d6691a67576eb37f1a92e4b1c994ae132",
    "PASS: BI current-user install smoke is clean, fixed-window, and source-immutable",
    "INSTALL_SMOKE_UNINSTALL_PARENT_EXITCODE=0",
    "FORMAL_GITHUB_ACTIONS",
    "raw_sha256",
    "registry_kind",
    "exact_raw_match",
    "exact_kind_match",
    "process_exit_code = $null",
    "$result.process_exit_code = $exitCode",
    'status = "PASS"',
):
    assert marker in launcher, marker

assert launcher.count("$env:GIT_CONFIG_COUNT") == 1
assert launcher.count("$env:GIT_CONFIG_KEY_0") == 1
assert launcher.count("$env:GIT_CONFIG_VALUE_0") == 1
assert launcher.index('$env:GIT_CONFIG_COUNT = "1"') < launcher.index(
    "git -C $localRepository"
)
assert launcher.index("$result.process_exit_code = $exitCode") < launcher.index(
    "Write-AtomicJson $ResultPath $result"
)

for forbidden in (
    "WindowsSandbox",
    ".wsb",
    "docker",
    "psexec",
    "Register-ScheduledTask",
    "runas",
    "safe.directory",
    "--global",
    "--system",
    "--local",
    "git config --global",
    "git config --system",
    "git config --local",
    "-AllowDirty",
    "-AllowUnreleasedLoopCandidates",
    "uninstall.exe /S",
):
    assert forbidden.lower() not in launcher.lower(), forbidden

assert "git -c " not in launcher

print("PASS: Windows CI proves standard-user raw PATH and registry-kind roundtrip")
