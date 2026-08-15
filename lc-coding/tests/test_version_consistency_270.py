from pathlib import Path
import json
import tomllib


root = Path(__file__).resolve().parents[2]
release_current = "2.7.0"
prepared_schema = "2.8.0"

assert (root / "VERSION").read_text(encoding="utf-8").strip() == release_current
release_manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
assert release_manifest["version"] == release_current

for relative in [
    "lc-coding/contracts/delivery-policy.json",
    "lc-coding/contracts/verification-receipt.json",
    "lc-coding/contracts/version-policy.json",
    "lc-coding/contracts/vulnerability-closure.json",
]:
    assert json.loads((root / relative).read_text(encoding="utf-8"))["version"] == release_current

lifecycle = json.loads(
    (root / "lc-coding/contracts/lifecycle.json").read_text(encoding="utf-8")
)
phases = json.loads(
    (root / "lc-coding/contracts/phases.json").read_text(encoding="utf-8")
)
assert lifecycle["version"] == prepared_schema
assert phases["version"] == prepared_schema
prepared_phase_ids = [phase["id"] for phase in phases["phases"]]
assert prepared_phase_ids == [
    "INITIAL",
    "PRODUCT_FORMATION",
    "REAL_PRODUCT_INTEGRATION",
    "DELIVERY_PREPARATION",
]
release_phase_ids = [
    "INITIAL",
    "PRODUCT_FORMATION",
    "ENGINEERING_RUNS",
    "DELIVERY_PREPARATION",
]
assert release_manifest["phase_overlay"] == release_phase_ids
assert release_manifest["execution_method_overlay"]["available_in_phases"] == release_phase_ids
assert prepared_phase_ids != release_phase_ids

canonical = json.loads(
    (root / "lc-coding/templates/CANONICAL-MANIFEST.json").read_text(encoding="utf-8")
)
assert canonical["lccoding"]["version"] == release_current
status = json.loads((root / "lc-coding/templates/STATUS.json").read_text(encoding="utf-8"))
phase_status = json.loads(
    (root / "lc-coding/templates/PHASE-STATUS.json").read_text(encoding="utf-8")
)
assert status["status_schema_version"] == prepared_schema
assert phase_status["status_schema_version"] == prepared_schema
assert list(phase_status["phases"]) == prepared_phase_ids

bi_root = root / "lc-coding/bi"
assert json.loads((bi_root / "package.json").read_text(encoding="utf-8"))["version"] == release_current
assert json.loads((bi_root / "package-lock.json").read_text(encoding="utf-8"))["version"] == release_current
assert tomllib.loads((bi_root / "src-tauri/Cargo.toml").read_text(encoding="utf-8"))[
    "package"
]["version"] == release_current
assert f'name = "lccoding"\nversion = "{release_current}"' in (
    bi_root / "src-tauri/Cargo.lock"
).read_text(encoding="utf-8")
assert json.loads(
    (bi_root / "src-tauri/tauri.conf.json").read_text(encoding="utf-8")
)["version"] == release_current

for relative in [
    "README.md",
    "README.zh-CN.md",
    "CONSTITUTION.md",
    "SPEC.md",
    "lc-coding/SKILL.md",
    "VALIDATION-REPORT.md",
    "PUBLISH-TO-GITHUB.md",
    "lc-coding/scripts/validate_repository.py",
]:
    assert release_current in (root / relative).read_text(encoding="utf-8"), relative

snapshot_model = (bi_root / "src/model/snapshot.ts").read_text(encoding="utf-8")
assert '"LCCoding 2.7.0 derived BI"' in snapshot_model
assert '"LCCoding 2.6.0 derived BI"' in snapshot_model
projection = (bi_root / "src-tauri/src/projection.rs").read_text(encoding="utf-8")
assert 'schema: "LCCoding 2.7.0 derived BI"' in projection
assert (root / "MIGRATION-2.5.2-TO-2.6.0.md").is_file()
changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
release_heading = "## 2.7.0"
next_heading = "## 2.6.0"
assert changelog.startswith("# Changelog\n\n")
assert changelog.count("\n" + release_heading + "\n") == 1
assert changelog.count("\n" + next_heading + "\n") == 1
release_start = changelog.index("\n" + release_heading + "\n") + 1
release_end = changelog.index("\n" + next_heading + "\n")
assert release_start < release_end
release_section = changelog[release_start:release_end]
for marker in [
    "copy-on-write",
    "current repository and BI release carriers are finalized for 2.7.0",
    "global installed Skill deployment remains a separate post-release action",
    "only after the formal release is independently accepted",
]:
    assert marker in release_section
for stale_claim in [
    "Unreleased - 2.7.0 candidate",
    "not a release",
    "no formal tag or GitHub Release exists yet",
    "prepared for 2.7.0",
    "does not change VERSION, BI",
]:
    assert stale_claim not in release_section

package_driver = (bi_root / "scripts/package-release.ps1").read_text(encoding="utf-8")
assert 'schema = "LCCoding 2.7.0 installer provenance"' in package_driver
assert '$releaseInstallerName = "LCCoding-BI_2.7.0_x64-setup.exe"' in package_driver
workflow = (root / ".github/workflows/release-bi.yml").read_text(encoding="utf-8")
assert 'VERSION -Raw).Trim() -ne "2.7.0"' in workflow
assert "LCCoding-BI_2.7.0_x64-setup.exe" in workflow

loop_identities = json.loads(
    (bi_root / "release/loop-contract-identities.json").read_text(encoding="utf-8")
)
assert loop_identities["asset_schema"] == "LCCODING_BI_COMPATIBILITY_V2"
assert set(loop_identities) == {"asset_schema", "status_adapters", "execution_methods"}
assert set(loop_identities["status_adapters"]) == {"2.6.0", "2.7.0", "2.8.0"}
assert loop_identities["status_adapters"]["2.6.0"]["compatibility_status"] == "SUPPORTED_LEGACY"
assert loop_identities["status_adapters"]["2.7.0"]["compatibility_status"] == "CURRENT"
assert loop_identities["status_adapters"]["2.8.0"]["compatibility_status"] == "PREPARED"
assert loop_identities["status_adapters"]["2.8.0"]["minimum_bi_version"] == prepared_schema
assert list(loop_identities["status_adapters"]["2.8.0"]["phase_steps"]) == prepared_phase_ids
methods = loop_identities["execution_methods"]
assert set(methods) == {"slk", "clk", "glk"}
assert methods["slk"]["version"] == "2.6.0"
assert methods["clk"]["version"] == "2.5.0"
assert methods["glk"]["version"] == "3.1.0"
assert not {"slk", "clk", "glk"}.intersection(loop_identities)

release_verifier = (bi_root / "scripts/verify-loop-releases.ps1").read_text(
    encoding="utf-8"
)
assert ".execution_methods" in release_verifier
assert '$tag = "v$($identity.version)"' in release_verifier
contracts = release_verifier.split("$contracts =", 1)[1].split("$verified =", 1)[0]
assert "version =" not in contracts
assert "tag =" not in contracts
for identity in methods.values():
    assert identity["candidate_commit"] not in release_verifier
    for field in ["manifest_sha256", "schema_sha256", "template_sha256"]:
        assert identity[field] not in release_verifier
assert "calabash" not in release_verifier.lower()
for powershell7_only in ["Text.Json", "HashData", "ToHexString"]:
    assert powershell7_only not in release_verifier

print("PASS: 2.7 release carriers and prepared 2.8 method schema are consistent")
