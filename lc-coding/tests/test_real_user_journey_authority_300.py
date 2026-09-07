from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[2]
SPEC = (ROOT / "SPEC.md").read_text(encoding="utf-8")
PHASES = json.loads(
    (ROOT / "lc-coding/contracts/phases.json").read_text(encoding="utf-8")
)

EXPECTED = [
    "INITIAL",
    "PRODUCT_FORMATION",
    "REAL_PRODUCT_INTEGRATION",
    "REAL_USER_JOURNEY_ACCEPTANCE",
    "DELIVERY_PREPARATION",
]
assert [phase["id"] for phase in PHASES["phases"]] == EXPECTED
for clause in [
    "LC-PHASE-004",
    "LC-PHASE-005",
    "LC-JOURNEY-001",
    "LC-JOURNEY-002",
    "LC-JOURNEY-003",
]:
    assert f'id="{clause.lower()}"' in SPEC
for marker in [
    "real rendered feedback",
    "40001",
    "restart from the home page",
    "UI → Workflow → Backend/Core",
    "REAL_USER_JOURNEY_ACCEPTED",
]:
    assert marker in SPEC
assert SPEC.index("### LC-PHASE-004") < SPEC.index("### LC-PHASE-005")
print("PASS: LCCoding 3.0 defines one real-user journey acceptance phase")
