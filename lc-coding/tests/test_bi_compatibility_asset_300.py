import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ASSET_PATH = ROOT / "lc-coding/bi/release/loop-contract-identities.json"

INITIAL = ["PROPOSAL_READINESS", "PROJECT_INITIALIZATION", "INITIAL_READY"]
FORMATION = [
    "CALABASH_DRAFT",
    "SIMULATION_WORLD_FOUNDATION",
    "WORKFLOW_CAPABILITY_END",
    "UI_PRODUCT_SURFACE_END",
    "CALABASH_UPGRADE_READY",
    "MANDATORY_CALABASH_UPGRADE",
    "PRODUCT_BASELINE",
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

raw = ASSET_PATH.read_bytes()
asset = json.loads(raw.decode("utf-8"))
assert asset["asset_schema"] == "LCCODING_BI_COMPATIBILITY_V4"
assert tuple(asset["status_adapters"]) == (
    "2.6.0", "2.7.0", "2.8.0", "3.0.0", "4.0.0",
)
assert [
    adapter["compatibility_status"] for adapter in asset["status_adapters"].values()
] == [
    "SUPPORTED_LEGACY", "SUPPORTED_LEGACY", "SUPPORTED_LEGACY",
    "SUPPORTED_LEGACY", "CURRENT",
]

adapter_300 = asset["status_adapters"]["3.0.0"]
assert adapter_300["minimum_bi_version"] == "3.0.0"
assert adapter_300["phase_steps"] == {
    "INITIAL": INITIAL,
    "PRODUCT_FORMATION": FORMATION,
    "REAL_PRODUCT_INTEGRATION": INTEGRATION,
    "REAL_USER_JOURNEY_ACCEPTANCE": JOURNEY,
    "DELIVERY_PREPARATION": DELIVERY,
}
assert tuple(map(len, adapter_300["phase_steps"].values())) == (3, 7, 5, 5, 6)
steps = [step for phase in adapter_300["phase_steps"].values() for step in phase]
assert len(steps) == len(set(steps)) == 26

# The 3.0 adapter extends 2.8 only by inserting the journey-acceptance phase.
legacy = asset["status_adapters"]["2.8.0"]
assert legacy["phase_steps"] == {
    key: value for key, value in adapter_300["phase_steps"].items()
    if key != "REAL_USER_JOURNEY_ACCEPTANCE"
}

# Updating status compatibility must not silently rewrite method release identities.
start = raw.index(b'  "execution_methods": {')
fragment = raw[start:raw.rfind(b"\n  }\n}") + len(b"\n  }")]
assert hashlib.sha256(fragment).hexdigest() == (
    "904a0f8ce8eea72e5d1774b95acaa5239d9a4f1a5b39214eb1c5f91c3b7d054b"
)

print("PASS: BI compatibility V4 preserves the exact 3.0 journey adapter")
