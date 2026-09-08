from pathlib import Path
import json
import re


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


def clause_body(clause_id: str) -> str:
    match = re.search(
        rf"(?ms)^### {re.escape(clause_id)} — .*?\n\n(.*?)(?=^<a id=|^## |\Z)",
        SPEC,
    )
    assert match, clause_id
    return match.group(1)


journey_authority = clause_body("LC-JOURNEY-001")
for marker in [
    "actual external route entry",
    "captures a screenshot",
    "first-hand route evidence",
    "platform effects",
    "result delivery",
    "final human-observable outcome",
]:
    assert marker in journey_authority, marker

correction_authority = clause_body("LC-JOURNEY-002")
for marker in [
    "`40001`",
    "`USER_SERVICE_BOUNDARY` → `WORKFLOW_ORCHESTRATION` → `BACKEND_CORE`",
    "restart from each actual required route entry",
]:
    assert marker in correction_authority, marker

journey = {phase["id"]: phase for phase in PHASES["phases"]}[
    "REAL_USER_JOURNEY_ACCEPTANCE"
]
assert journey["route_faithful"] is True
assert journey["visible_actions_require_screenshots"] is True
assert journey["complete_round_starts_at"] == "ACTUAL_REQUIRED_ROUTE_ENTRY"
assert journey["repair_priority"] == [
    "USER_SERVICE_BOUNDARY",
    "WORKFLOW_ORCHESTRATION",
    "BACKEND_CORE",
]
assert journey["final_human_observable_outcome_required"] is True
assert "REAL_USER_JOURNEY_ACCEPTED" in journey["owner_results"]
assert SPEC.index("### LC-PHASE-004") < SPEC.index("### LC-PHASE-005")
print("PASS: LCCoding defines one route-faithful real-user journey acceptance phase")
