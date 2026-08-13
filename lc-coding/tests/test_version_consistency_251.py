from pathlib import Path
import json
import tomllib


root = Path(__file__).resolve().parents[2]
current = "2.6.0"

assert (root / "VERSION").read_text(encoding="utf-8").strip() == current
assert json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))["version"] == current

for relative in [
    "lc-coding/contracts/delivery-policy.json",
    "lc-coding/contracts/lifecycle.json",
    "lc-coding/contracts/phases.json",
    "lc-coding/contracts/verification-receipt.json",
    "lc-coding/contracts/version-policy.json",
    "lc-coding/contracts/vulnerability-closure.json",
]:
    assert json.loads((root / relative).read_text(encoding="utf-8"))["version"] == current

canonical = json.loads(
    (root / "lc-coding/templates/CANONICAL-MANIFEST.json").read_text(encoding="utf-8")
)
assert canonical["lccoding"]["version"] == current
status = json.loads((root / "lc-coding/templates/STATUS.json").read_text(encoding="utf-8"))
assert status["status_schema_version"] == current

bi_root = root / "lc-coding/bi"
assert json.loads((bi_root / "package.json").read_text(encoding="utf-8"))["version"] == current
assert json.loads((bi_root / "package-lock.json").read_text(encoding="utf-8"))["version"] == current
assert tomllib.loads((bi_root / "src-tauri/Cargo.toml").read_text(encoding="utf-8"))[
    "package"
]["version"] == current
assert f'name = "lccoding"\nversion = "{current}"' in (
    bi_root / "src-tauri/Cargo.lock"
).read_text(encoding="utf-8")
assert json.loads(
    (bi_root / "src-tauri/tauri.conf.json").read_text(encoding="utf-8")
)["version"] == current

for relative in [
    "README.md",
    "README.zh-CN.md",
    "CONSTITUTION.md",
    "SPEC.md",
    "lc-coding/SKILL.md",
    "lc-coding/references/built-in-bi.md",
    "VALIDATION-REPORT.md",
    "PUBLISH-TO-GITHUB.md",
    "lc-coding/scripts/validate_repository.py",
]:
    assert current in (root / relative).read_text(encoding="utf-8"), relative

snapshot_model = (bi_root / "src/model/snapshot.ts").read_text(encoding="utf-8")
assert '"LCCoding 2.6.0 derived BI"' in snapshot_model
assert (root / "MIGRATION-2.5.2-TO-2.6.0.md").is_file()
changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
assert changelog.index("## 2.6.0") < changelog.index("## 2.5.2")

package_driver = (bi_root / "scripts/package-release.ps1").read_text(encoding="utf-8")
assert 'schema = "LCCoding 2.6.0 installer provenance"' in package_driver
assert '$releaseInstallerName = "LCCoding-BI_2.6.0_x64-setup.exe"' in package_driver
workflow = (root / ".github/workflows/release-bi.yml").read_text(encoding="utf-8")
assert 'VERSION -Raw).Trim() -ne "2.6.0"' in workflow
assert "LCCoding-BI_2.6.0_x64-setup.exe" in workflow

loop_identities = json.loads(
    (bi_root / "release/loop-contract-identities.json").read_text(encoding="utf-8")
)
assert loop_identities["asset_schema"] == "LCCODING_BI_COMPATIBILITY_V1"
assert set(loop_identities) == {"asset_schema", "status_adapters", "execution_methods"}
assert set(loop_identities["status_adapters"]) == {"2.6.0", "2.7.0"}
assert loop_identities["status_adapters"]["2.6.0"]["compatibility_status"] == "SUPPORTED_LEGACY"
assert loop_identities["status_adapters"]["2.7.0"]["compatibility_status"] == "CURRENT"
methods = loop_identities["execution_methods"]
assert set(methods) == {"slk", "clk", "glk"}
assert methods["slk"]["version"] == "2.5.0"
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

print("PASS: LCCoding 2.6.0 version is consistent across release artifacts")
