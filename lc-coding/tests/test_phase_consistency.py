from pathlib import Path
import json

root = Path(__file__).resolve().parents[2]
manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
phase_contract = json.loads(
    (root / "lc-coding/contracts/phases.json").read_text(encoding="utf-8")
)
canonical_ids = [phase["id"] for phase in phase_contract["phases"]]

assert manifest["phase_overlay"] == canonical_ids

migration = (root / "MIGRATION-1.1.1-TO-2.0.0.md").read_text(encoding="utf-8")
assert "ENGINEERING_CLOSURE" not in migration
for phase_id in canonical_ids:
    assert phase_id in migration

print("PASS: phase identifiers are consistent across release artifacts")
