from pathlib import Path
import json
import runpy


root = Path(__file__).resolve().parents[2]
runpy.run_path(str(root / "lc-coding/tests/test_version_consistency_280.py"))

assert (root / "MIGRATION-2.8.0-TO-3.0.0.md").is_file()
assert (root / "lc-coding/scripts/migrate_project_280_to_300.py").is_file()
assert (root / "lc-coding/templates/REAL-USER-JOURNEY-ACCEPTANCE.md").is_file()
assert (root / "lc-coding/templates/REAL-USER-JOURNEY-DEFECT-LOG.md").is_file()

manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
phases = json.loads(
    (root / "lc-coding/contracts/phases.json").read_text(encoding="utf-8")
)
phase_ids = [phase["id"] for phase in phases["phases"]]
assert phase_ids == [
    "INITIAL",
    "PRODUCT_FORMATION",
    "REAL_PRODUCT_INTEGRATION",
    "REAL_USER_JOURNEY_ACCEPTANCE",
    "DELIVERY_PREPARATION",
]
assert manifest["phase_overlay"] == phase_ids
assert manifest["execution_method_overlay"]["available_in_phases"] == phase_ids
assert manifest["acceptance_model"]["journey_final"] == "REAL_USER_JOURNEY_ACCEPTANCE"

asset = json.loads(
    (root / "lc-coding/bi/release/loop-contract-identities.json").read_text(
        encoding="utf-8"
    )
)
adapter = asset["status_adapters"]["3.0.0"]
assert adapter["compatibility_status"] == "SUPPORTED_LEGACY"
assert sum(len(steps) for steps in adapter["phase_steps"].values()) == 26
assert list(adapter["phase_steps"])[3] == "REAL_USER_JOURNEY_ACCEPTANCE"
assert asset["status_adapters"]["4.0.0"]["compatibility_status"] == "CURRENT"

print("PASS: LCCoding 3.0 five-phase identity remains supported by BI V4")
