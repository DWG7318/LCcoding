from pathlib import Path
import json
import tomllib


root = Path(__file__).resolve().parents[2]
current = "2.4.1"

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
assert tomllib.loads((bi_root / "src-tauri/Cargo.toml").read_text(encoding="utf-8"))[
    "package"
]["version"] == current
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
assert '"LCCoding 2.4.1 derived BI"' in snapshot_model
assert (root / "MIGRATION-2.4.0-TO-2.4.1.md").is_file()
changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
assert changelog.index("## 2.4.1") < changelog.index("## 2.4.0")

print("PASS: LCCoding 2.4.1 version is consistent across release artifacts")
