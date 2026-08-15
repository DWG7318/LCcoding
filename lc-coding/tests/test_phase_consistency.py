from pathlib import Path
import json

root = Path(__file__).resolve().parents[2]
manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
phase_contract = json.loads(
    (root / "lc-coding/contracts/phases.json").read_text(encoding="utf-8")
)
canonical_ids = [phase["id"] for phase in phase_contract["phases"]]
current_ids = [
    "INITIAL",
    "PRODUCT_FORMATION",
    "REAL_PRODUCT_INTEGRATION",
    "DELIVERY_PREPARATION",
]
legacy_ids = [
    "INITIAL",
    "PRODUCT_FORMATION",
    "ENGINEERING_RUNS",
    "DELIVERY_PREPARATION",
]

assert phase_contract["version"] == "2.8.0"
assert canonical_ids == current_ids
assert manifest["version"] == "2.8.0"
assert manifest["phase_overlay"] == current_ids
assert manifest["execution_method_overlay"]["available_in_phases"] == current_ids
assert manifest["phase_overlay"] == canonical_ids
assert phase_contract["execution_methods"]["phase_ids"] == canonical_ids
assert phase_contract["execution_methods"]["available_in_all_phases"] is True
assert phase_contract["execution_methods"]["method_completion_advances_phase"] is False
integration = next(
    phase
    for phase in phase_contract["phases"]
    if phase["id"] == "REAL_PRODUCT_INTEGRATION"
)
assert integration["display_meaning"] == "REAL_PRODUCT_INTEGRATION"
assert integration["start"] == "FEATURE_SLICE"
assert "entry_gate" not in integration

migration = (root / "MIGRATION-1.1.1-TO-2.0.0.md").read_text(encoding="utf-8")
assert "ENGINEERING_CLOSURE" not in migration
for phase_id in legacy_ids:
    assert phase_id in migration

print("PASS: phase identifiers are consistent across release artifacts")
