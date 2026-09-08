from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "lc-coding/templates"

status = json.loads((TEMPLATES / "STATUS.json").read_text(encoding="utf-8"))
phase_status = json.loads(
    (TEMPLATES / "PHASE-STATUS.json").read_text(encoding="utf-8")
)
acceptance = (TEMPLATES / "REAL-USER-JOURNEY-ACCEPTANCE.md").read_text(
    encoding="utf-8"
)
defect_log = (TEMPLATES / "REAL-USER-JOURNEY-DEFECT-LOG.md").read_text(
    encoding="utf-8"
)

assert status["status_schema_version"] == "3.0.0"
assert tuple(status["phase_gates"]) == (
    "INITIAL_READY",
    "CALABASH_UPGRADE_READY",
    "ALL_REQUIRED_RUNS_ACCEPTED",
    "REAL_USER_JOURNEY_ACCEPTED",
    "DELIVERY_READY",
)
summary = status["real_user_journey_acceptance"]
assert tuple(summary) == (
    "state",
    "candidate_id",
    "candidate_hash",
    "coverage_state",
    "acceptance_environment_state",
    "current_round",
    "complete_round_count",
    "required_journey_count",
    "passed_journey_count",
    "failed_journey_count",
    "not_applicable_journey_count",
    "open_defect_ids",
    "fixed_verified_defect_ids",
    "exempted_defect_ids",
    "deferred_defect_ids",
    "reopened_defect_ids",
    "acceptance_record_reference",
    "defect_log_reference",
    "owner_result",
)
assert summary["state"] == "UNPROVED"
assert summary["candidate_id"] == "NOT_APPLICABLE"
assert summary["candidate_hash"] == "NOT_APPLICABLE"
assert summary["current_round"] == 0
assert summary["complete_round_count"] == 0
assert summary["open_defect_ids"] == []
assert summary["owner_result"] == "PENDING"

assert phase_status["status_schema_version"] == "3.0.0"
assert tuple(phase_status["phases"]) == (
    "INITIAL",
    "PRODUCT_FORMATION",
    "REAL_PRODUCT_INTEGRATION",
    "REAL_USER_JOURNEY_ACCEPTANCE",
    "DELIVERY_PREPARATION",
)
journey_phase = phase_status["phases"]["REAL_USER_JOURNEY_ACCEPTANCE"]
assert journey_phase == {
    "status": "PENDING",
    "acceptance_record": "NOT_APPLICABLE",
    "defect_log": "NOT_APPLICABLE",
    "complete_rounds": 0,
    "exit_gate": "PENDING",
}

assert acceptance.startswith("# Real User Journey Acceptance\n")
for heading in (
    "## Candidate identity",
    "## Acceptance environment and viewport",
    "## Journey coverage",
    "## Acceptance rounds",
    "## Evidence digests",
    "## Defect pointers",
    "## Recommendation and Owner result",
    "## Invalidation history",
):
    assert acceptance.count(heading) == 1, heading

for heading in (
    "## Route-faithful 4.0 journey coverage",
    "## Route-faithful 4.0 evidence digests",
):
    assert acceptance.count(heading) == 1, heading
for token in (
    "DIRECT_PRODUCT",
    "PERSONAL_AGENT",
    "SERVICE_CENTER",
    "SCREENSHOT",
    "Human-observable outcome",
    "Task5 acceptance receipt citations",
    "Task5 Run ID / D3 Receipt",
    "Task5 Final Verification / D3 citations",
    "FINAL_FEATURE_VERIFICATION",
    '"layer": "D3"',
    "Attempted route IDs",
    "Unattempted route dispositions",
    "Action",
    "Visible location",
    "Viewport",
    "Screenshot path",
    "Screenshot SHA-256",
    "Native evidence path",
    "Native evidence SHA-256",
    "REAL_USER_JOURNEY_EVIDENCE",
    "event_or_result",
    "authenticated/matched identity",
    "performed/success",
    "SERVICE_TO_HUMAN",
    "canonical verification contract",
    "reused or new evidence",
    "structured or empty `repeated_checks`",
):
    assert token in acceptance, token

assert defect_log.startswith("# Real User Journey Defect Log\n")
assert "The first legal defect ID is `40001`" in defect_log
assert "IDs increase monotonically and are never recycled" in defect_log
for column in (
    "Defect ID",
    "Screenshot SHA-256",
    "Expected / observed",
    "Visible layer / root cause",
    "Correction identity",
    "Retest round",
    "State",
    "Exemption authority / impact / recovery",
    "Repair sequence",
    "Priority exception justification",
    "Retest evidence ID / kind / SHA-256",
):
    assert column in defect_log, column
for token in (
    "USER_SERVICE_BOUNDARY",
    "WORKFLOW_ORCHESTRATION",
    "BACKEND_CORE",
    "UI / AGENT_SERVICE / ASSISTED_SERVICE",
    "## Route-faithful defect register",
    "REAL_USER_JOURNEY_DEFECT_EXEMPTION",
    "REAL_USER_JOURNEY_REPAIR_PRIORITY_EXCEPTION",
    "| Round |",
    "GLOBAL_BOUNDARY",
    "omitted route",
):
    assert token in defect_log, token

print("PASS: 3.0 journey acceptance templates are closed and unproved by default")
