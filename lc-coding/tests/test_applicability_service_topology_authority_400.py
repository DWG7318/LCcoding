from pathlib import Path
import json
import re


ROOT = Path(__file__).resolve().parents[2]
SPEC = (ROOT / "SPEC.md").read_text(encoding="utf-8")
LIFECYCLE = json.loads(
    (ROOT / "lc-coding/contracts/lifecycle.json").read_text(encoding="utf-8")
)
PHASES = json.loads(
    (ROOT / "lc-coding/contracts/phases.json").read_text(encoding="utf-8")
)


def clause_body(clause_id: str) -> str:
    match = re.search(
        rf"(?ms)^### {re.escape(clause_id)} — .*?\n\n(.*?)(?=^<a id=|^## |\Z)",
        SPEC,
    )
    assert match, clause_id
    return match.group(1)


applicability_clause = clause_body("LC-AUTH-003")
for marker in (
    "WHOLE_PRODUCT_FIT",
    "BOUNDED_PRODUCT_FIT",
    "OTHER_METHOD_RECOMMENDED",
    "PLATFORM_COMPLETION",
    "AGENT_COLLABORATIVE",
    "MIXED",
):
    assert marker in applicability_clause, marker

topology_clause = clause_body("LC-INTEG-005")
for marker in (
    "DIRECT_PRODUCT",
    "PERSONAL_AGENT",
    "SERVICE_CENTER",
    "Human Principal",
    "Personal Agent",
    "Product Agent",
    "Operations Agent",
    "Service Center actor",
    "USER_SERVICE_BOUNDARY",
):
    assert marker in topology_clause, marker

expected_mainline = [
    "LCCODING_APPLICABILITY_ASSESSMENT",
    "PROPOSAL_READINESS",
    "PRODUCT_SERVICE_STRATEGY",
    "PROJECT_INITIALIZATION",
    "CALABASH_DRAFT",
    "SERVICE_ROUTE_MAP",
    "WORKFLOW_ROUTE_SURFACES_SIMULATION",
    "MANDATORY_CALABASH_UPGRADE",
    "PRODUCT_BASELINE",
    "FEATURE_SLICE",
    "FEATURE_INTEGRATION",
    "REAL_USER_JOURNEY_ACCEPTANCE",
    "FINAL_VERIFICATION",
    "OWNER_ACCEPTANCE",
    "DELIVERY",
]
assert LIFECYCLE["mainline"] == expected_mainline
assert LIFECYCLE["mainline_scope"] == (
    "WHOLE_PRODUCT_FIT_OR_BOUNDED_PRODUCT_FIT_ADMITTED_PATH"
)
assert "WORKFLOW_UI_SIMULATION" not in LIFECYCLE["mainline"]
assert LIFECYCLE["required_transitions"] == dict(
    zip(expected_mainline[1:], expected_mainline[2:])
)

routing = LIFECYCLE["applicability_routing"]
assert routing["assessment"] == "LCCODING_APPLICABILITY_ASSESSMENT"
assert set(routing["outcomes"]) == {
    "WHOLE_PRODUCT_FIT",
    "BOUNDED_PRODUCT_FIT",
    "OTHER_METHOD_RECOMMENDED",
}
for outcome in ("WHOLE_PRODUCT_FIT", "BOUNDED_PRODUCT_FIT"):
    route = routing["outcomes"][outcome]
    assert route["lccoding_lifecycle_admitted"] is True
    assert route["next"] == "PROPOSAL_READINESS"
terminal = routing["outcomes"]["OTHER_METHOD_RECOMMENDED"]
assert terminal == {
    "disposition": "TERMINAL_ASSESSMENT",
    "lccoding_lifecycle_admitted": False,
    "underlying_project_rejected": False,
    "next": None,
}
incomplete = routing["insufficient_facts"]
assert incomplete == {
    "disposition": "PROPOSAL_INCOMPLETE",
    "applicability_outcome": None,
    "next": None,
    "resume_at": "LCCODING_APPLICABILITY_ASSESSMENT",
}
assert "LCCODING_APPLICABILITY_ASSESSMENT" not in LIFECYCLE["required_transitions"]

compatibility = LIFECYCLE["compatibility_aliases"]["WORKFLOW_UI_SIMULATION"]
assert compatibility["canonical"] == "WORKFLOW_ROUTE_SURFACES_SIMULATION"
assert compatibility["read_only"] is True

feature_integration = LIFECYCLE["semantic_bindings"]["FEATURE_INTEGRATION"]
route_chain = [
    "PROMISED_REAL_ENTRY",
    "AUTHENTICATED_ACTOR_AND_VALID_AUTHORITY",
    "APPLICABLE_ROUTE_ADAPTER_OR_PRODUCT_SURFACE",
    "REAL_WORKFLOW_BACKEND_CORE_EFFECTS",
    "AUTHORITATIVE_STATE_DATA_SIDE_EFFECT",
    "ROUTE_RESULT",
    "HUMAN_OBSERVABLE_BUSINESS_OUTCOME",
    "ROUTE_SPECIFIC_INTEGRATION_AND_END_TO_END_PROOF",
]
assert feature_integration[: len(route_chain)] == route_chain
legacy_integration_relations = {
    "REAL_WORKFLOW_UI_SIMULATION_CONNECTION": "APPLICABLE_ROUTE_ADAPTER_OR_PRODUCT_SURFACE",
    "REAL_API_MCP_BACKED_CAPABILITY": "REAL_WORKFLOW_BACKEND_CORE_EFFECTS",
    "REAL_STATE_DATA_SIDE_EFFECT": "AUTHORITATIVE_STATE_DATA_SIDE_EFFECT",
    "VISIBLE_UI_RESULT": "HUMAN_OBSERVABLE_BUSINESS_OUTCOME",
    "INTEGRATION_AND_END_TO_END_PROOF": "ROUTE_SPECIFIC_INTEGRATION_AND_END_TO_END_PROOF",
}
assert not (set(feature_integration) & set(legacy_integration_relations))
for legacy, canonical in legacy_integration_relations.items():
    alias = LIFECYCLE["compatibility_aliases"][legacy]
    assert alias == {
        "canonical": canonical,
        "read_only": True,
        "scope": "3.0_DIRECT_PRODUCT_EVIDENCE_ONLY",
        "governs_route_aware_writes": False,
    }

phase_by_id = {item["id"]: item for item in PHASES["phases"]}
assert list(phase_by_id) == [
    "INITIAL",
    "PRODUCT_FORMATION",
    "REAL_PRODUCT_INTEGRATION",
    "REAL_USER_JOURNEY_ACCEPTANCE",
    "DELIVERY_PREPARATION",
]
initial = phase_by_id["INITIAL"]
assert initial["fine_milestone_path_condition"] == "LCCODING_LIFECYCLE_ADMITTED"
assert initial["applicability_admission"] == {
    "admitted_outcomes": ["WHOLE_PRODUCT_FIT", "BOUNDED_PRODUCT_FIT"],
    "terminal_outcome": "OTHER_METHOD_RECOMMENDED",
    "incomplete_disposition": "PROPOSAL_INCOMPLETE",
}
formation = phase_by_id["PRODUCT_FORMATION"]
assert formation["fine_milestones"][2] == "WORKFLOW_ROUTE_SURFACES_SIMULATION"
surface_contract = formation["formation_surface_contract"]
assert surface_contract["selection_scope"] == "PER_DELIVERED_JOURNEY"
assert surface_contract["graphical_ui_required"] == "ONLY_WHEN_PROMISED_BY_ROUTE"
assert surface_contract["artificial_ui_forbidden"] is True
assert set(surface_contract["conditional_surface_kinds"]) == {
    "DIRECT_PRODUCT",
    "PERSONAL_AGENT",
    "SERVICE_CENTER",
}

journey = phase_by_id["REAL_USER_JOURNEY_ACCEPTANCE"]
journey_clause = clause_body("LC-JOURNEY-001")
for marker in ("platform effects", "result delivery", "final human-observable outcome"):
    assert marker in journey_clause, marker
assert journey["nonvisual_agent_first_hand_evidence"] == [
    "MESSAGE",
    "TASK_TRANSITION",
    "ARTIFACT",
    "AUTHORIZATION_DECISION",
    "PLATFORM_EFFECT",
    "RESULT_DELIVERY",
    "AUDIT_EVENT",
]
assert journey["final_human_observable_outcome_required"] is True

print("PASS: LCCoding 4.0 applicability and service-topology authority")
