from pathlib import Path
import json

root = Path(__file__).resolve().parents[2]
assert (root / "VERSION").read_text(encoding="utf-8").strip() == "2.2.0"
assert json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))["version"] == "2.2.0"

for relative in [
    "lc-coding/contracts/delivery-policy.json",
    "lc-coding/contracts/lifecycle.json",
    "lc-coding/contracts/phases.json",
    "lc-coding/contracts/verification-receipt.json",
    "lc-coding/contracts/version-policy.json",
    "lc-coding/contracts/vulnerability-closure.json",
]:
    assert json.loads((root / relative).read_text(encoding="utf-8"))["version"] == "2.2.0"

canonical = json.loads(
    (root / "lc-coding/templates/CANONICAL-MANIFEST.json").read_text(encoding="utf-8")
)
assert canonical["lccoding"]["version"] == "2.2.0"
for relative in ["README.md", "README.zh-CN.md", "CONSTITUTION.md", "SPEC.md", "lc-coding/SKILL.md"]:
    assert "2.2.0" in (root / relative).read_text(encoding="utf-8")
assert (root / "MIGRATION-2.1.0-TO-2.2.0.md").is_file()

print("PASS: LCCoding 2.2.0 version is consistent across release artifacts")
