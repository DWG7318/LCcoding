import hashlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[2]
ASSET_PATH = ROOT / "lc-coding/bi/release/loop-contract-identities.json"
PHASE_TEMPLATE_PATH = ROOT / "lc-coding/templates/PHASE-STATUS.json"
VALIDATOR_PATH = ROOT / "lc-coding/scripts/validate_phase_status.py"

PHASES = (
    "INITIAL",
    "PRODUCT_FORMATION",
    "REAL_PRODUCT_INTEGRATION",
    "REAL_USER_JOURNEY_ACCEPTANCE",
    "DELIVERY_PREPARATION",
)
INITIAL_300 = ["PROPOSAL_READINESS", "PROJECT_INITIALIZATION", "INITIAL_READY"]
INITIAL_400 = [
    "LCCODING_APPLICABILITY_ASSESSMENT",
    "PROPOSAL_READINESS",
    "PRODUCT_SERVICE_STRATEGY",
    "PROJECT_INITIALIZATION",
    "INITIAL_READY",
]
FORMATION_300 = [
    "CALABASH_DRAFT",
    "SIMULATION_WORLD_FOUNDATION",
    "WORKFLOW_CAPABILITY_END",
    "UI_PRODUCT_SURFACE_END",
    "CALABASH_UPGRADE_READY",
    "MANDATORY_CALABASH_UPGRADE",
    "PRODUCT_BASELINE",
]
FORMATION_400 = [
    "CALABASH_DRAFT",
    "SERVICE_ROUTE_MAP_READY",
    *FORMATION_300[1:],
]
INTEGRATION = [
    "FEATURE_SLICE_EXECUTION_COVERAGE",
    "UI_LOCKED_INTEGRATION_BASELINE",
    "LOOP_RUN_D0_D3",
    "LOOP_OWNER_ACCEPTANCE",
    "ALL_REQUIRED_RUNS_ACCEPTED",
]
JOURNEY = [
    "JOURNEY_COVERAGE_READY",
    "ACCEPTANCE_ENVIRONMENT_READY",
    "REAL_USER_JOURNEY_ROUND",
    "JOURNEY_DEFECT_CLOSURE",
    "REAL_USER_JOURNEY_OWNER_ACCEPTANCE",
]
DELIVERY = [
    "CENTRALIZED_VULNERABILITY_AUDIT",
    "SECURITY_REMEDIATION",
    "SECURITY_REAUDIT_VULNERABILITY_CLOSURE",
    "POST_SECURITY_OWNER_ACCEPTANCE",
    "DELIVERY_METHOD_QA",
    "DELIVERY_PACKAGE_GUARD_READY",
]
EXPECTED_400 = {
    "INITIAL": INITIAL_400,
    "PRODUCT_FORMATION": FORMATION_400,
    "REAL_PRODUCT_INTEGRATION": INTEGRATION,
    "REAL_USER_JOURNEY_ACCEPTANCE": JOURNEY,
    "DELIVERY_PREPARATION": DELIVERY,
}
METHOD_FRAGMENT_SHA256 = (
    "904a0f8ce8eea72e5d1774b95acaa5239d9a4f1a5b39214eb1c5f91c3b7d054b"
)


raw = ASSET_PATH.read_bytes()
asset = json.loads(raw.decode("utf-8"))
assert asset["asset_schema"] == "LCCODING_BI_COMPATIBILITY_V4"
assert tuple(asset["status_adapters"]) == (
    "2.6.0",
    "2.7.0",
    "2.8.0",
    "3.0.0",
    "4.0.0",
)
assert [
    adapter["compatibility_status"] for adapter in asset["status_adapters"].values()
] == [
    "SUPPORTED_LEGACY",
    "SUPPORTED_LEGACY",
    "SUPPORTED_LEGACY",
    "SUPPORTED_LEGACY",
    "CURRENT",
]

legacy_300 = asset["status_adapters"]["3.0.0"]
assert legacy_300["minimum_bi_version"] == "3.0.0"
assert legacy_300["phase_steps"] == {
    "INITIAL": INITIAL_300,
    "PRODUCT_FORMATION": FORMATION_300,
    "REAL_PRODUCT_INTEGRATION": INTEGRATION,
    "REAL_USER_JOURNEY_ACCEPTANCE": JOURNEY,
    "DELIVERY_PREPARATION": DELIVERY,
}

current = asset["status_adapters"]["4.0.0"]
assert current == {
    "status_schema_version": "4.0.0",
    "compatibility_status": "CURRENT",
    "minimum_bi_version": "4.0.0",
    "phase_steps": EXPECTED_400,
}
assert tuple(current["phase_steps"]) == PHASES
assert tuple(map(len, current["phase_steps"].values())) == (5, 8, 5, 5, 6)
steps = [step for phase_steps in current["phase_steps"].values() for step in phase_steps]
assert len(steps) == len(set(steps)) == 29

# V4 changes only the two named Initial milestones and the one route-map milestone.
assert INITIAL_400[1] == INITIAL_300[0]
assert INITIAL_400[3:] == INITIAL_300[1:]
assert FORMATION_400[0] == FORMATION_300[0]
assert FORMATION_400[2:] == FORMATION_300[1:]
for phase_id in PHASES[2:]:
    assert current["phase_steps"][phase_id] == legacy_300["phase_steps"][phase_id]

# Status compatibility changes must not rewrite execution-method release identities.
start = raw.index(b'  "execution_methods": {')
fragment = raw[start : raw.rfind(b"\n  }\n}") + len(b"\n  }")]
assert hashlib.sha256(fragment).hexdigest() == METHOD_FRAGMENT_SHA256

phase_template = json.loads(PHASE_TEMPLATE_PATH.read_text(encoding="utf-8"))
assert phase_template["status_schema_version"] == "4.0.0"
assert tuple(phase_template["phases"]) == PHASES

spec = importlib.util.spec_from_file_location("phase_status_400", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)
assert validator.V4_INSERTED_MILESTONES == (
    ("INITIAL", 0, "LCCODING_APPLICABILITY_ASSESSMENT"),
    ("INITIAL", 2, "PRODUCT_SERVICE_STRATEGY"),
    ("PRODUCT_FORMATION", 1, "SERVICE_ROUTE_MAP_READY"),
)
assert validator.SCHEMA_PHASE_ORDERS["4.0.0"] == PHASES
assert validator.SCHEMA_PHASE_STEPS["4.0.0"] == {
    phase_id: tuple(steps) for phase_id, steps in EXPECTED_400.items()
}
assert validator.validate_phase_status(phase_template) == []
legacy_phase_status = deepcopy(phase_template)
legacy_phase_status["status_schema_version"] = "3.0.0"
assert validator.validate_phase_status(legacy_phase_status) == []


def production_loader_rejects(changed_asset):
    original = validator.COMPATIBILITY_ASSET_PATH
    try:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "loop-contract-identities.json"
            path.write_text(json.dumps(changed_asset), encoding="utf-8", newline="\n")
            validator.COMPATIBILITY_ASSET_PATH = path
            try:
                validator._load_compatibility_layout()
            except RuntimeError:
                return True
            return False
    finally:
        validator.COMPATIBILITY_ASSET_PATH = original


accepted_replacements = []
for phase_id, index, replacement in (
    ("INITIAL", 0, "UNKNOWN_APPLICABILITY_MILESTONE"),
    ("INITIAL", 2, "UNKNOWN_SERVICE_STRATEGY_MILESTONE"),
    ("PRODUCT_FORMATION", 1, "UNKNOWN_ROUTE_MAP_MILESTONE"),
):
    changed = deepcopy(asset)
    changed["status_adapters"]["4.0.0"]["phase_steps"][phase_id][index] = replacement
    if not production_loader_rejects(changed):
        accepted_replacements.append(replacement)
assert not accepted_replacements, accepted_replacements

# Task 10 atomically promotes the release and authoritative STATUS carriers.
assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "4.0.0"
assert json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))["version"] == "4.0.0"
assert json.loads(
    (ROOT / "lc-coding/templates/STATUS.json").read_text(encoding="utf-8")
)["status_schema_version"] == "4.0.0"

print("PASS: BI compatibility V4 exposes one exact current 4.0 phase adapter")
