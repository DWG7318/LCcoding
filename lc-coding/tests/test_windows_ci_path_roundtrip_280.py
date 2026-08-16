from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATE_WORKFLOW = ROOT / ".github/workflows/validate.yml"
RELEASE_WORKFLOW = ROOT / ".github/workflows/release-bi.yml"
PARENT = ROOT / "lc-coding/bi/tests/packaging/run-standard-user-install-smoke.ps1"
CHILD = ROOT / "lc-coding/bi/tests/packaging/standard-user-install-smoke.ps1"

assert VALIDATE_WORKFLOW.is_file(), "Validate LCCoding workflow is missing"
assert RELEASE_WORKFLOW.is_file(), "formal BI release workflow is missing"
assert PARENT.is_file(), "reusable standard-user smoke parent is missing"
assert CHILD.is_file(), "accepted standard-user smoke child is missing"

workflow = VALIDATE_WORKFLOW.read_text(encoding="utf-8")
release_workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")
parent = PARENT.read_text(encoding="utf-8")
child = CHILD.read_text(encoding="utf-8")

assert "on: [push, pull_request]" in workflow
assert "runs-on: ubuntu-latest" in workflow
job_marker = "  validate-windows-path-roundtrip:"
assert job_marker in workflow
windows_job = workflow[workflow.index(job_marker) :]

for marker in (
    "runs-on: windows-latest",
    "actions/checkout@v4",
    "fetch-depth: 0",
    "actions/setup-node@v4",
    'node-version: "24"',
    "dtolnay/rust-toolchain@stable",
    "toolchain: 1.96.0",
    "package-release.ps1 -OutputRoot $outputRoot",
    "run-standard-user-install-smoke.ps1",
    "FORMAL_GITHUB_ACTIONS",
    "actions/upload-artifact@v4",
    "if: always()",
    "task22-win-ci-evidence",
    "orchestrator-result.json",
    "result.json",
    "e25a7bd12d9921444d8fe51578a3fa67f48d67e5175a57bb5303b01c297f4a47",
):
    assert marker in windows_job, marker

assert windows_job.count("run-standard-user-install-smoke.ps1") == 1
assert release_workflow.count("run-standard-user-install-smoke.ps1") == 1
assert "standard-user-install-smoke.ps1" not in windows_job.replace(
    "run-standard-user-install-smoke.ps1", ""
)
for inline_parent_primitive in (
    "New-LocalUser",
    "Add-LocalGroupMember",
    "Get-LocalGroupMember",
    "Remove-LocalUser",
    "Start-Process",
    "[Management.Automation.PSCredential]",
):
    assert inline_parent_primitive not in windows_job, inline_parent_primitive

for marker in (
    "param(",
    "$SourceRepository",
    "$PackageDirectory",
    "$EvidenceDirectory",
    "$ExpectedCommit",
    "$ExpectedHooksSha256",
    '$env:GITHUB_ACTIONS -cne "true"',
    '$env:RUNNER_ENVIRONMENT -cne "github-hosted"',
    '$env:GITHUB_REPOSITORY -cne "DWG7318/LCcoding"',
    "New-LocalUser",
    "Add-LocalGroupMember",
    "Get-LocalGroupMember",
    'SecurityIdentifier]::new("S-1-5-32-545")',
    'SecurityIdentifier]::new("S-1-5-32-544")',
    "Add-LocalGroupMember -SID $usersSid -Member $localUser",
    "Get-LocalGroupMember -SID $usersSid",
    "Get-LocalGroupMember -SID $administratorsSid",
    "icacls.exe",
    "Start-Process",
    "-Credential $credential",
    "-LoadUserProfile",
    "standard-user-install-smoke.ps1",
    "orchestrator-result.json",
    "function Write-AtomicJson",
    "Get-FileHash",
    "pre_smoke_sha256",
    "smoked_installer_sha256",
    "post_smoke_sha256",
    "child_script_sha256",
    "child_result_sha256",
    "observed_child_exit_code",
    "child_process_exit_code",
    "standard_user_sid",
    "exact_raw_match",
    "exact_kind_match",
    "uninstall_parent_exit_code",
    "temporary_user_cleanup",
    'status = "PASS"',
    'temporary_user_cleanup = "PASS"',
    "Remove-LocalUser",
    "Win32_UserProfile",
    "$smokedSha256 -cne $result.pre_smoke_sha256",
):
    assert marker in parent, marker

assert parent.count("New-LocalUser") == 1
assert parent.count("Add-LocalGroupMember") == 1
assert parent.count("-Credential $credential") == 1
assert parent.count("standard-user-install-smoke.ps1") == 1
assert parent.index("New-LocalUser") < parent.index("Start-Process")
assert parent.index("Start-Process") < parent.index("Remove-LocalUser")
assert parent.index("Remove-LocalUser") < parent.index(
    'temporary_user_cleanup = "PASS"'
)

for forbidden in (
    "WindowsSandbox",
    ".wsb",
    "docker",
    "psexec",
    "Register-ScheduledTask",
    "runas",
    "Start-Process powershell.exe -Verb RunAs",
    "-Verb RunAs",
    "git push",
    "git tag",
    "gh release",
    'Get-LocalGroupMember -Group "Users"',
    'Get-LocalGroupMember -Group "Administrators"',
    "-AllowDirty",
    "-AllowUnreleasedLoopCandidates",
):
    assert forbidden.lower() not in parent.lower(), forbidden

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
    assert marker in child, marker

assert child.count("$env:GIT_CONFIG_COUNT") == 1
assert child.count("$env:GIT_CONFIG_KEY_0") == 1
assert child.count("$env:GIT_CONFIG_VALUE_0") == 1
assert child.index('$env:GIT_CONFIG_COUNT = "1"') < child.index(
    "git -C $localRepository"
)
assert child.index("$result.process_exit_code = $exitCode") < child.index(
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
    assert forbidden.lower() not in child.lower(), forbidden

assert "git -c " not in child

print("PASS: both Windows workflows use one closed standard-user smoke parent")
