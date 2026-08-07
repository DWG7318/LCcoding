from pathlib import Path
import json
import tomllib


root = Path(__file__).resolve().parents[2]
current = "2.5.2"

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
assert '"LCCoding 2.5.2 derived BI"' in snapshot_model
assert (root / "MIGRATION-2.5.1-TO-2.5.2.md").is_file()
changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
assert changelog.index("## 2.5.2") < changelog.index("## 2.5.1")

package_driver = (bi_root / "scripts/package-release.ps1").read_text(encoding="utf-8")
assert 'schema = "LCCoding 2.5.2 installer provenance"' in package_driver
assert '$releaseInstallerName = "LCCoding-BI_2.5.2_x64-setup.exe"' in package_driver
workflow = (root / ".github/workflows/release-bi.yml").read_text(encoding="utf-8")
assert 'VERSION -Raw).Trim() -ne "2.5.2"' in workflow
assert "LCCoding-BI_2.5.2_x64-setup.exe" in workflow

loop_identities = json.loads(
    (bi_root / "release/loop-contract-identities.json").read_text(encoding="utf-8")
)
assert loop_identities["slk"]["version"] == "2.5.0"
assert loop_identities["clk"]["version"] == "2.5.0"
assert loop_identities["glk"]["version"] == "3.1.0"

print("PASS: LCCoding 2.5.2 version is consistent across release artifacts")
