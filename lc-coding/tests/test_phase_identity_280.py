from copy import deepcopy
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile


root = Path(__file__).resolve().parents[2]
validator_path = root / "lc-coding/scripts/validate_phase_status.py"
spec = importlib.util.spec_from_file_location("phase_identity_280", validator_path)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

CURRENT_SCHEMA = "2.8.0"
LEGACY_SCHEMAS = ("2.6.0", "2.7.0")
CURRENT_PHASES = (
    "INITIAL",
    "PRODUCT_FORMATION",
    "REAL_PRODUCT_INTEGRATION",
    "DELIVERY_PREPARATION",
)
LEGACY_PHASES = (
    "INITIAL",
    "PRODUCT_FORMATION",
    "ENGINEERING_RUNS",
    "DELIVERY_PREPARATION",
)
MAINLINE = [
    "PROPOSAL_READINESS",
    "PROJECT_INITIALIZATION",
    "CALABASH_DRAFT",
    "WORKFLOW_UI_SIMULATION",
    "MANDATORY_CALABASH_UPGRADE",
    "PRODUCT_BASELINE",
    "FEATURE_SLICE",
    "FEATURE_INTEGRATION",
    "FINAL_VERIFICATION",
    "OWNER_ACCEPTANCE",
    "DELIVERY",
]
GATES = {
    "INITIAL_READY",
    "CALABASH_UPGRADE_READY",
    "LOOP_OWNER_ACCEPTANCE_READY",
    "ALL_REQUIRED_RUNS_ACCEPTED",
    "CENTRALIZED_VULNERABILITY_AUDIT",
    "SECURITY_REMEDIATION",
    "INDEPENDENT_SECURITY_REAUDIT",
    "VULNERABILITY_CLOSURE",
    "POST_SECURITY_OWNER_ACCEPTANCE",
    "DELIVERY_METHOD_QA",
    "DELIVERY_PACKAGE_GUARD",
    "DELIVERY_READY",
}


def load_json(relative: str) -> dict:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def phase_view(schema: str, phase3_id: str) -> dict:
    return {
        "record_role": "DERIVED_VIEW",
        "status_schema_version": schema,
        "derived_from": "status.json",
        "current_phase": "INITIAL",
        "phases": {
            "INITIAL": {"status": "ACTIVE", "exit_gate": "PENDING"},
            "PRODUCT_FORMATION": {
                "status": "PENDING",
                "exit_evidence": "PENDING",
            },
            phase3_id: {
                "status": "PENDING",
                "per_run_acceptances": [],
                "aggregate_exit_gate": "PENDING",
            },
            "DELIVERY_PREPARATION": {
                "status": "PENDING",
                "exit_gate": "PENDING",
            },
        },
        "updated_at": "",
        "evidence": [],
        "blockers": [],
    }


def assert_rejected(record: dict, marker: str) -> None:
    errors = validator.validate_phase_status(record)
    assert errors, f"mutation unexpectedly accepted: {marker}"
    assert any(marker in error for error in errors), (marker, errors)


def run_cli(text: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "PHASE-STATUS.json"
        path.write_bytes(text.encode("utf-8"))
        before_bytes = path.read_bytes()
        before_mtime = path.stat().st_mtime_ns
        result = subprocess.run(
            [sys.executable, str(validator_path), str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert path.read_bytes() == before_bytes
        assert path.stat().st_mtime_ns == before_mtime
        return result


phases_contract = load_json("lc-coding/contracts/phases.json")
lifecycle_contract = load_json("lc-coding/contracts/lifecycle.json")
status_template = load_json("lc-coding/templates/STATUS.json")
phase_template = load_json("lc-coding/templates/PHASE-STATUS.json")

assert phases_contract["version"] == CURRENT_SCHEMA
assert lifecycle_contract["version"] == CURRENT_SCHEMA
assert status_template["status_schema_version"] == CURRENT_SCHEMA
assert phase_template["status_schema_version"] == CURRENT_SCHEMA
assert status_template["current_phase"] == "INITIAL"
assert phase_template["current_phase"] == "INITIAL"

contract_ids = tuple(phase["id"] for phase in phases_contract["phases"])
assert contract_ids == CURRENT_PHASES
assert tuple(phases_contract["execution_methods"]["phase_ids"]) == CURRENT_PHASES
assert tuple(phase_template["phases"]) == CURRENT_PHASES
assert "ENGINEERING_RUNS" not in json.dumps(
    (phases_contract, lifecycle_contract, status_template, phase_template),
    sort_keys=True,
)

phase_by_id = {phase["id"]: phase for phase in phases_contract["phases"]}
formation = phase_by_id["PRODUCT_FORMATION"]
integration = phase_by_id["REAL_PRODUCT_INTEGRATION"]
delivery = phase_by_id["DELIVERY_PREPARATION"]
assert lifecycle_contract["mainline"] == MAINLINE
assert phases_contract["mainline_unchanged"] is True
assert formation["start"] == "CALABASH_DRAFT"
assert formation["end_after"] == "PRODUCT_BASELINE"
assert "exit_gate" not in formation
assert integration["display_meaning"] == "REAL_PRODUCT_INTEGRATION"
assert integration["start"] == "FEATURE_SLICE"
assert "entry_gate" not in integration
assert integration["slice_run_admission"]["phase_entry"] is False
assert integration["aggregate_exit_scope"] == "REQUIRED_PHASE_3_INTEGRATION_RUNS"
assert delivery["end_before"] == "DELIVERY"

actual_gates = {
    phase_by_id["INITIAL"]["exit_gate"],
    formation["internal_readiness"]["id"],
    integration["per_run_exit_gate"],
    integration["aggregate_exit_gate"],
    *delivery["required_subgates"],
    delivery["exit_gate"],
}
assert actual_gates == GATES

assert validator.validate_phase_status(phase_template) == []
current = phase_view(CURRENT_SCHEMA, "REAL_PRODUCT_INTEGRATION")
assert validator.validate_phase_status(current) == []
for schema in LEGACY_SCHEMAS:
    assert validator.validate_phase_status(phase_view(schema, "ENGINEERING_RUNS")) == []

cross_current = phase_view(CURRENT_SCHEMA, "ENGINEERING_RUNS")
assert_rejected(cross_current, "phase identity does not match schema")
cross_legacy = phase_view("2.7.0", "REAL_PRODUCT_INTEGRATION")
assert_rejected(cross_legacy, "phase identity does not match schema")

mixed = phase_view(CURRENT_SCHEMA, "REAL_PRODUCT_INTEGRATION")
mixed["phases"]["ENGINEERING_RUNS"] = deepcopy(
    mixed["phases"]["REAL_PRODUCT_INTEGRATION"]
)
assert_rejected(mixed, "phase identity does not match schema")

inferred = phase_view(CURRENT_SCHEMA, "REAL_PRODUCT_INTEGRATION")
del inferred["status_schema_version"]
assert_rejected(inferred, "status_schema_version is required")

unknown_schema = phase_view("2.9.0", "REAL_PRODUCT_INTEGRATION")
assert_rejected(unknown_schema, "unsupported status_schema_version")

fifth_phase = phase_view(CURRENT_SCHEMA, "REAL_PRODUCT_INTEGRATION")
fifth_phase["phases"]["AGENT_OPERATIONS"] = {
    "status": "PENDING",
    "exit_gate": "PENDING",
}
assert_rejected(fifth_phase, "phase identity does not match schema")

unknown_current = phase_view(CURRENT_SCHEMA, "REAL_PRODUCT_INTEGRATION")
unknown_current["current_phase"] = "PRODUCT_INTEGRATION"
assert_rejected(unknown_current, "invalid current_phase")

wrong_order = phase_view(CURRENT_SCHEMA, "REAL_PRODUCT_INTEGRATION")
wrong_order["phases"] = {
    key: wrong_order["phases"][key]
    for key in (
        "INITIAL",
        "REAL_PRODUCT_INTEGRATION",
        "PRODUCT_FORMATION",
        "DELIVERY_PREPARATION",
    )
}
assert_rejected(wrong_order, "phase identity does not match schema")

unknown_top = phase_view(CURRENT_SCHEMA, "REAL_PRODUCT_INTEGRATION")
unknown_top["phase_runtime"] = {}
assert_rejected(unknown_top, "unexpected top-level field")

unknown_nested = phase_view(CURRENT_SCHEMA, "REAL_PRODUCT_INTEGRATION")
unknown_nested["phases"]["REAL_PRODUCT_INTEGRATION"]["agent_gate"] = "PASS"
assert_rejected(unknown_nested, "unexpected phase field")

valid_text = json.dumps(current, separators=(",", ":"))
valid_result = run_cli(valid_text)
assert valid_result.returncode == 0, valid_result.stdout + valid_result.stderr
assert valid_result.stdout.strip() == "PASS"

duplicate_text = valid_text.replace(
    '"status_schema_version":"2.8.0"',
    '"status_schema_version":"2.8.0","status_schema_version":"2.8.0"',
    1,
)
duplicate_result = run_cli(duplicate_text)
assert duplicate_result.returncode != 0
assert "FAIL" in duplicate_result.stdout
assert "duplicate JSON key" in duplicate_result.stdout
assert "Traceback" not in duplicate_result.stderr

cross_result = run_cli(json.dumps(cross_current, separators=(",", ":")))
assert cross_result.returncode != 0
assert "phase identity does not match schema" in cross_result.stdout

print("PASS: exact schema selects one closed four-phase identity without new gates")
