from pathlib import Path
import re


root = Path(__file__).resolve().parents[2]
workflow = root / ".github/workflows/release-bi.yml"
assert workflow.is_file(), "formal Windows release workflow is missing"
text = workflow.read_text(encoding="utf-8")

trigger = re.search(r"(?ms)^on:\s*\n(?P<body>.*?)(?=^[^\s#])", text)
assert trigger, "workflow trigger block is missing"
events = set(re.findall(r"(?m)^  ([a-z_]+):\s*$", trigger.group("body")))
assert events == {"workflow_dispatch"}, events

permissions = re.search(r"(?ms)^permissions:\s*\n(?P<body>.*?)(?=^[^\s#])", text)
assert permissions
assert permissions.group("body").strip() == "contents: read"

required = [
    "runs-on: windows-latest",
    "actions/checkout@v4",
    "ref: ${{ github.sha }}",
    "fetch-depth: 0",
    "actions/setup-python@v5",
    'python-version: "3.12"',
    "actions/setup-node@v4",
    'node-version: "24"',
    "dtolnay/rust-toolchain@stable",
    "toolchain: 1.96.0",
    "refs/heads/main",
    "GITHUB_ACTIONS",
    "GITHUB_REPOSITORY",
    "GITHUB_SHA",
    "GITHUB_RUN_ID",
    "GITHUB_RUN_ATTEMPT",
    "GITHUB_WORKFLOW",
    "GITHUB_REF",
    "python lc-coding/tests/run_tests.py",
    "python lc-coding/scripts/validate_repository.py .",
    "test_release_integrity.py",
    "nsis-contract.ps1",
    "verify-loop-releases.ps1",
    '$outputRoot = Join-Path $env:RUNNER_TEMP "lccoding-bi-formal"',
    "package-release.ps1 -OutputRoot $outputRoot",
    "GH_TOKEN: ${{ github.token }}",
    "FORMAL_GITHUB_ACTIONS",
    "VERIFIED_FORMAL_RELEASES",
    "x86_64-pc-windows-msvc",
    "Get-FileHash",
    "BI_RELEASE_DIRECTORY",
    "BI_RELEASE_INSTALLER",
    "BI_RELEASE_PRE_SMOKE_SHA256",
    "run-standard-user-install-smoke.ps1",
    "orchestrator-result.json",
    "BI_RELEASE_POST_SMOKE_SHA256",
    "BI_RELEASE_POST_SMOKE_IDENTITY_INVALID",
    "Upload formal three-file asset set",
    "Upload formal smoke evidence",
    "actions/upload-artifact@v4",
    "if-no-files-found: error",
    "compression-level: 0",
]
for marker in required:
    assert marker in text, marker

assert text.count("package-release.ps1 -OutputRoot $outputRoot") == 1
assert text.count("run-standard-user-install-smoke.ps1") == 1
assert text.count("actions/upload-artifact@v4") == 2

build = text.index("package-release.ps1 -OutputRoot $outputRoot")
pre_hash = text.index("BI_RELEASE_PRE_SMOKE_SHA256")
smoke = text.index("run-standard-user-install-smoke.ps1")
post_hash = text.index("BI_RELEASE_POST_SMOKE_SHA256")
formal_upload = text.index("Upload formal three-file asset set")
evidence_upload = text.index("Upload formal smoke evidence")
assert build < pre_hash < smoke < post_hash < formal_upload < evidence_upload

formal_block = text[formal_upload:evidence_upload]
evidence_block = text[evidence_upload:]
assert "if: always()" not in formal_block
assert "if: always()" in evidence_block
assert "orchestrator-result.json" in evidence_block
assert "result.json" in evidence_block
assert "if-no-files-found: error" in evidence_block

release_root = "${{ runner.temp }}\\lccoding-bi-formal\\release\\"
uploads = {
    f"{release_root}LCCoding-BI_2.8.0_x64-setup.exe",
    f"{release_root}installer.sha256",
    f"{release_root}provenance.json",
}
for path in uploads:
    assert path in formal_block, path
assert formal_block.count(release_root) == 3
assert f"{release_root}*" not in text

for identity_join in (
    "$post -cne $env:BI_RELEASE_PRE_SMOKE_SHA256",
    "$post -cne $evidence.pre_smoke_sha256",
    "$post -cne $evidence.smoked_installer_sha256",
    "$post -cne $evidence.post_smoke_sha256",
    "$post -cne $checksumSha256",
    "$post -cne $provenance.sha256",
    '$evidence.status -cne "PASS"',
    '$evidence.temporary_user_cleanup -cne "PASS"',
):
    assert identity_join in text, identity_join

for forbidden in [
    "-AllowDirty",
    "-AllowUnreleasedLoopCandidates",
    "contents: write",
    "actions/create-release",
    "softprops/action-gh-release",
    "ncipollo/release-action",
    "gh release",
    "git push",
    "git tag",
    "actions/download-artifact",
    "Copy-Item",
    "Move-Item",
    "cargo-target",
    "\\frontend",
    "\\dist",
]:
    assert forbidden.lower() not in text.lower(), forbidden

report = (root / "VALIDATION-REPORT.md").read_text(encoding="utf-8")
for marker in [
    "gh workflow run release-bi.yml --ref main",
    "gh run watch",
    "gh run download",
    "FORMAL_GITHUB_ACTIONS",
    "Get-FileHash",
    "current-user installation smoke",
]:
    assert marker in report, marker
assert "required tag lookups returned HTTP 404" not in report
assert "must not be pushed, tagged, or released" not in report

print("PASS: formal BI workflow builds, smokes, and uploads one installer lineage")
