from copy import deepcopy
from pathlib import Path
import json


root = Path(__file__).resolve().parents[2]
lifecycle = json.loads(
    (root / "lc-coding/contracts/lifecycle.json").read_text(encoding="utf-8")
)
phase_contract = json.loads(
    (root / "lc-coding/contracts/phases.json").read_text(encoding="utf-8")
)

EXPECTED_MAINLINE = [
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
EXPECTED_PHASE_IDS = [
    "INITIAL",
    "PRODUCT_FORMATION",
    "REAL_PRODUCT_INTEGRATION",
    "REAL_USER_JOURNEY_ACCEPTANCE",
    "DELIVERY_PREPARATION",
]
EXPECTED_AGGREGATE_EXCLUDES = {
    "INITIAL_RUNS",
    "PRODUCT_FORMATION_RUNS",
    "REAL_USER_JOURNEY_ACCEPTANCE_RUNS",
    "DELIVERY_PREPARATION_RUNS",
    "OPTIONAL_RUNS",
    "SUPERSEDED_RUNS",
    "INVALIDATED_RUNS",
}


def phase_by_id(contract: dict, phase_id: str) -> dict:
    matches = [phase for phase in contract.get("phases", []) if phase.get("id") == phase_id]
    if len(matches) != 1:
        return {}
    return matches[0]


def validate_phase_semantics(current_lifecycle: dict, current_phases: dict) -> set[str]:
    errors: set[str] = set()

    if current_lifecycle.get("version") != "3.0.0" or current_phases.get("version") != "3.0.0":
        errors.add("VERSION_CARRIER_CHANGED_EARLY")

    mainline = current_lifecycle.get("mainline")
    if mainline != EXPECTED_MAINLINE:
        errors.add("MAINLINE_ORDER_CHANGED")
    if current_lifecycle.get("mainline_scope") != (
        "WHOLE_PRODUCT_FIT_OR_BOUNDED_PRODUCT_FIT_ADMITTED_PATH"
    ):
        errors.add("MAINLINE_SCOPE_WRONG")
    expected_transitions = dict(zip(EXPECTED_MAINLINE[1:], EXPECTED_MAINLINE[2:]))
    if current_lifecycle.get("required_transitions") != expected_transitions:
        errors.add("MAINLINE_TRANSITIONS_CHANGED")
    if "LCCODING_APPLICABILITY_ASSESSMENT" in current_lifecycle.get(
        "required_transitions", {}
    ):
        errors.add("APPLICABILITY_BECAME_UNCONDITIONAL")
    routing = current_lifecycle.get("applicability_routing", {})
    outcomes = routing.get("outcomes", {})
    if set(outcomes) != {
        "WHOLE_PRODUCT_FIT",
        "BOUNDED_PRODUCT_FIT",
        "OTHER_METHOD_RECOMMENDED",
    }:
        errors.add("APPLICABILITY_OUTCOMES_WRONG")
    for admitted in ("WHOLE_PRODUCT_FIT", "BOUNDED_PRODUCT_FIT"):
        route = outcomes.get(admitted, {})
        if route.get("lccoding_lifecycle_admitted") is not True or route.get(
            "next"
        ) != "PROPOSAL_READINESS":
            errors.add("APPLICABILITY_ADMISSION_WRONG")
    terminal = outcomes.get("OTHER_METHOD_RECOMMENDED", {})
    if (
        terminal.get("disposition") != "TERMINAL_ASSESSMENT"
        or terminal.get("lccoding_lifecycle_admitted") is not False
        or terminal.get("next") is not None
    ):
        errors.add("APPLICABILITY_TERMINAL_WRONG")
    incomplete = routing.get("insufficient_facts", {})
    if (
        incomplete.get("disposition") != "PROPOSAL_INCOMPLETE"
        or incomplete.get("applicability_outcome") is not None
        or incomplete.get("next") is not None
    ):
        errors.add("APPLICABILITY_INCOMPLETE_WRONG")

    phase_ids = [phase.get("id") for phase in current_phases.get("phases", [])]
    if phase_ids != EXPECTED_PHASE_IDS:
        errors.add("PHASE_IDS_CHANGED")
    if current_phases.get("mainline_unchanged") is not False:
        errors.add("MAINLINE_CHANGE_NOT_DECLARED")

    serialized = json.dumps(
        {"lifecycle": current_lifecycle, "phases": current_phases},
        sort_keys=True,
    )
    if "PRODUCT_BASELINE_READY" in serialized:
        errors.add("INVENTED_PRODUCT_BASELINE_GATE")

    formation = phase_by_id(current_phases, "PRODUCT_FORMATION")
    if formation.get("start") != "CALABASH_DRAFT":
        errors.add("FORMATION_START_WRONG")
    if formation.get("end_after") != "PRODUCT_BASELINE":
        errors.add("FORMATION_END_WRONG")
    if "exit_gate" in formation:
        errors.add("FORMATION_HAS_PHASE_EXIT_GATE")
    exit_evidence = formation.get("exit_evidence", {})
    if exit_evidence.get("artifact") != "PRODUCT_BASELINE_HANDOFF":
        errors.add("FORMATION_EXIT_ARTIFACT_WRONG")
    if exit_evidence.get("mechanical_validation") != "PASS":
        errors.add("FORMATION_EXIT_NOT_VALIDATED")
    if exit_evidence.get("owner_acceptance") != "ACCEPTED":
        errors.add("FORMATION_EXIT_NOT_ACCEPTED")
    readiness = formation.get("internal_readiness", {})
    if readiness.get("id") != "CALABASH_UPGRADE_READY":
        errors.add("CALABASH_READINESS_MISSING")
    if readiness.get("meaning") != "READY_TO_BEGIN_MANDATORY_CALABASH_UPGRADE":
        errors.add("CALABASH_READINESS_MEANING_WRONG")
    if readiness.get("compatibility_readable") is not True:
        errors.add("CALABASH_READINESS_NOT_READABLE")
    if readiness.get("phase_exit") is not False:
        errors.add("CALABASH_READINESS_IS_PHASE_EXIT")
    for phase in current_phases.get("phases", []):
        if phase.get("exit_gate") == "CALABASH_UPGRADE_READY":
            errors.add("CALABASH_READINESS_USED_AS_EXIT_GATE")
    fine_milestones = formation.get("fine_milestones")
    if (
        not isinstance(fine_milestones, list)
        or len(fine_milestones) < 3
        or fine_milestones[2] != "WORKFLOW_ROUTE_SURFACES_SIMULATION"
    ):
        errors.add("FORMATION_ROUTE_SURFACE_MILESTONE_WRONG")
    surface_contract = formation.get("formation_surface_contract", {})
    if surface_contract.get("selection_scope") != "PER_DELIVERED_JOURNEY":
        errors.add("FORMATION_SURFACE_SCOPE_WRONG")
    if surface_contract.get("graphical_ui_required") != "ONLY_WHEN_PROMISED_BY_ROUTE":
        errors.add("FORMATION_UI_CONDITION_WRONG")
    if surface_contract.get("artificial_ui_forbidden") is not True:
        errors.add("FORMATION_ARTIFICIAL_UI_ALLOWED")

    integration = phase_by_id(current_phases, "REAL_PRODUCT_INTEGRATION")
    if integration.get("display_meaning") != "REAL_PRODUCT_INTEGRATION":
        errors.add("PHASE_3_DISPLAY_WRONG")
    if integration.get("start") != "FEATURE_SLICE":
        errors.add("PHASE_3_START_WRONG")
    if "entry_gate" in integration:
        errors.add("PHASE_3_HAS_ENTRY_GATE")
    admission = integration.get("slice_run_admission", {})
    if admission.get("relation") != "FEATURE_SLICE_EXECUTION_COVERAGE_PASS":
        errors.add("SLICE_RUN_ADMISSION_MISSING")
    if admission.get("scope") != ["PER_SLICE", "PER_INTEGRATION_RUN"]:
        errors.add("SLICE_RUN_ADMISSION_SCOPE_WRONG")
    if admission.get("phase_entry") is not False:
        errors.add("SLICE_RUN_ADMISSION_BECAME_PHASE_GATE")

    if integration.get("aggregate_exit_gate") != "ALL_REQUIRED_RUNS_ACCEPTED":
        errors.add("PHASE_3_AGGREGATE_GATE_WRONG")
    if integration.get("aggregate_exit_scope") != "REQUIRED_PHASE_3_INTEGRATION_RUNS":
        errors.add("PHASE_3_AGGREGATE_SCOPE_WRONG")
    if set(integration.get("aggregate_excludes", [])) != EXPECTED_AGGREGATE_EXCLUDES:
        errors.add("PHASE_3_AGGREGATE_EXCLUSIONS_WRONG")

    journey = phase_by_id(current_phases, "REAL_USER_JOURNEY_ACCEPTANCE")
    if journey.get("start_after") != "ALL_REQUIRED_RUNS_ACCEPTED":
        errors.add("PHASE_4_START_WRONG")
    if journey.get("complete_round_starts_at") != "ACTUAL_REQUIRED_ROUTE_ENTRY":
        errors.add("PHASE_4_ROUND_START_WRONG")
    if journey.get("repair_priority") != [
        "USER_SERVICE_BOUNDARY",
        "WORKFLOW_ORCHESTRATION",
        "BACKEND_CORE",
    ]:
        errors.add("PHASE_4_REPAIR_PRIORITY_WRONG")
    if journey.get("nonvisual_agent_first_hand_evidence") != [
        "MESSAGE",
        "TASK_TRANSITION",
        "ARTIFACT",
        "AUTHORIZATION_DECISION",
        "PLATFORM_EFFECT",
        "RESULT_DELIVERY",
        "AUDIT_EVENT",
    ]:
        errors.add("PHASE_4_AGENT_EVIDENCE_WRONG")
    if journey.get("exit_gate") != "REAL_USER_JOURNEY_ACCEPTED":
        errors.add("PHASE_4_EXIT_WRONG")
    delivery_phase = phase_by_id(current_phases, "DELIVERY_PREPARATION")
    if delivery_phase.get("start_after") != "REAL_USER_JOURNEY_ACCEPTED":
        errors.add("PHASE_5_START_WRONG")

    bindings = current_lifecycle.get("semantic_bindings", {})
    if "CALABASH_UPGRADE_READY_IS_INTERNAL_READINESS_TO_BEGIN" not in bindings.get(
        "MANDATORY_CALABASH_UPGRADE", []
    ):
        errors.add("LIFECYCLE_CALABASH_READINESS_RELATION_MISSING")
    if "PRODUCT_BASELINE_HANDOFF_VALIDATED_AND_ACCEPTED" not in bindings.get(
        "PRODUCT_BASELINE", []
    ):
        errors.add("LIFECYCLE_BASELINE_EXIT_EVIDENCE_MISSING")
    feature_slice = bindings.get("FEATURE_SLICE", [])
    if "REAL_PRODUCT_INTEGRATION_PHASE_ENTRY_NODE" not in feature_slice:
        errors.add("LIFECYCLE_PHASE_3_ENTRY_RELATION_MISSING")
    if "EXECUTION_COVERAGE_PREFLIGHT_PER_SLICE_OR_INTEGRATION_RUN" not in feature_slice:
        errors.add("LIFECYCLE_PREFLIGHT_SCOPE_RELATION_MISSING")
    feature_integration = bindings.get("FEATURE_INTEGRATION", [])
    if "ALL_REQUIRED_PHASE_3_INTEGRATION_RUNS_ACCEPTED" not in feature_integration:
        errors.add("LIFECYCLE_AGGREGATE_SCOPE_RELATION_MISSING")
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
    if feature_integration[: len(route_chain)] != route_chain:
        errors.add("FEATURE_INTEGRATION_ROUTE_CHAIN_WRONG")
    legacy_relations = {
        "REAL_WORKFLOW_UI_SIMULATION_CONNECTION": "APPLICABLE_ROUTE_ADAPTER_OR_PRODUCT_SURFACE",
        "REAL_API_MCP_BACKED_CAPABILITY": "REAL_WORKFLOW_BACKEND_CORE_EFFECTS",
        "REAL_STATE_DATA_SIDE_EFFECT": "AUTHORITATIVE_STATE_DATA_SIDE_EFFECT",
        "VISIBLE_UI_RESULT": "HUMAN_OBSERVABLE_BUSINESS_OUTCOME",
        "INTEGRATION_AND_END_TO_END_PROOF": "ROUTE_SPECIFIC_INTEGRATION_AND_END_TO_END_PROOF",
    }
    if set(feature_integration) & set(legacy_relations):
        errors.add("FEATURE_INTEGRATION_UI_COMPATIBILITY_GOVERNS_ACTIVE")
    aliases = current_lifecycle.get("compatibility_aliases", {})
    for legacy, canonical in legacy_relations.items():
        alias = aliases.get(legacy, {})
        if (
            alias.get("canonical") != canonical
            or alias.get("read_only") is not True
            or alias.get("governs_route_aware_writes") is not False
        ):
            errors.add("FEATURE_INTEGRATION_COMPATIBILITY_ALIAS_WRONG")
    for relation in (
        "ROUTE_FAITHFUL_REQUIRED_JOURNEY_GRAPH",
        "REAL_VISIBLE_BROWSER_OPERATION_FOR_VISIBLE_ACTIONS",
        "SCREENSHOT_AFTER_MEANINGFUL_VISIBLE_ACTION",
        "CANDIDATE_BOUND_MESSAGE_TASK_ARTIFACT_AUTHORIZATION_PLATFORM_EFFECT_RESULT_DELIVERY_AUDIT_EVIDENCE_FOR_NONVISUAL_AGENT_STEPS",
        "FINAL_HUMAN_OBSERVABLE_OUTCOME_REQUIRED",
        "DEFECT_IDENTITY_40001_PLUS",
        "USER_SERVICE_BOUNDARY_WORKFLOW_ORCHESTRATION_BACKEND_CORE_CORRECTION_PRIORITY",
        "COMPLETE_ROUND_RESTARTS_FROM_ACTUAL_ROUTE_ENTRY",
        "REAL_USER_JOURNEY_ACCEPTED",
    ):
        if relation not in bindings.get("REAL_USER_JOURNEY_ACCEPTANCE", []):
            errors.add(f"JOURNEY_RELATION_MISSING:{relation}")

    delivery_preparation = bindings.get("DELIVERY_PREPARATION", [])
    for relation in (
        "DELIVERY_METHOD_QA",
        "DELIVERY_PACKAGE_GUARD",
        "DELIVERY_READY_IS_PHASE_EXIT_EVIDENCE",
    ):
        if relation not in delivery_preparation:
            errors.add(f"DELIVERY_PREPARATION_RELATION_MISSING:{relation}")
    delivery = bindings.get("DELIVERY", [])
    if "ACTUAL_DELIVERY_AFTER_DELIVERY_READY" not in delivery:
        errors.add("ACTUAL_DELIVERY_RELATION_MISSING")
    if "DELIVERY_METHOD_QA" in delivery or "DELIVERY_PACKAGE_GUARD" in delivery:
        errors.add("DELIVERY_OWNS_PREPARATION_WORK")
    if set(delivery) != {"ACTUAL_DELIVERY_AFTER_DELIVERY_READY"}:
        errors.add("DELIVERY_BINDING_NOT_POST_GATE_ONLY")

    return errors


errors = validate_phase_semantics(lifecycle, phase_contract)
assert not errors, f"phase relationship errors: {sorted(errors)}"


def assert_mutation_rejected(code: str, mutate) -> None:
    changed_lifecycle = deepcopy(lifecycle)
    changed_phases = deepcopy(phase_contract)
    mutate(changed_lifecycle, changed_phases)
    assert code in validate_phase_semantics(changed_lifecycle, changed_phases), code


assert_mutation_rejected(
    "PHASE_IDS_CHANGED",
    lambda _, phases: phases["phases"].append(
        {"id": "WORKFLOW_REALIZATION", "start": "FEATURE_SLICE"}
    ),
)
assert_mutation_rejected(
    "FORMATION_END_WRONG",
    lambda _, phases: phase_by_id(phases, "PRODUCT_FORMATION").update(
        {"end_after": "MANDATORY_CALABASH_UPGRADE"}
    ),
)
assert_mutation_rejected(
    "INVENTED_PRODUCT_BASELINE_GATE",
    lambda _, phases: phase_by_id(phases, "PRODUCT_FORMATION").update(
        {"exit_gate": "PRODUCT_BASELINE_READY"}
    ),
)
assert_mutation_rejected(
    "CALABASH_READINESS_IS_PHASE_EXIT",
    lambda _, phases: phase_by_id(phases, "PRODUCT_FORMATION")[
        "internal_readiness"
    ].update({"phase_exit": True}),
)
assert_mutation_rejected(
    "CALABASH_READINESS_USED_AS_EXIT_GATE",
    lambda _, phases: phase_by_id(phases, "PRODUCT_FORMATION").update(
        {"exit_gate": "CALABASH_UPGRADE_READY"}
    ),
)
assert_mutation_rejected(
    "PHASE_3_START_WRONG",
    lambda _, phases: phase_by_id(phases, "REAL_PRODUCT_INTEGRATION").update(
        {"start": "MANDATORY_CALABASH_UPGRADE"}
    ),
)
assert_mutation_rejected(
    "PHASE_3_DISPLAY_WRONG",
    lambda _, phases: phase_by_id(phases, "REAL_PRODUCT_INTEGRATION").update(
        {"display_meaning": "Engineering Runs"}
    ),
)
assert_mutation_rejected(
    "PHASE_3_HAS_ENTRY_GATE",
    lambda _, phases: phase_by_id(phases, "REAL_PRODUCT_INTEGRATION").update(
        {"entry_gate": "FEATURE_SLICE_EXECUTION_COVERAGE_PASS"}
    ),
)
assert_mutation_rejected(
    "SLICE_RUN_ADMISSION_BECAME_PHASE_GATE",
    lambda _, phases: phase_by_id(phases, "REAL_PRODUCT_INTEGRATION")[
        "slice_run_admission"
    ].update({"phase_entry": True}),
)
assert_mutation_rejected(
    "PHASE_3_AGGREGATE_SCOPE_WRONG",
    lambda _, phases: phase_by_id(phases, "REAL_PRODUCT_INTEGRATION").update(
        {"aggregate_exit_scope": "ALL_RUNS_ALL_PHASES"}
    ),
)
assert_mutation_rejected(
    "PHASE_3_AGGREGATE_EXCLUSIONS_WRONG",
    lambda _, phases: phase_by_id(phases, "REAL_PRODUCT_INTEGRATION").update(
        {"aggregate_excludes": ["OPTIONAL_RUNS"]}
    ),
)
assert_mutation_rejected(
    "PHASE_4_ROUND_START_WRONG",
    lambda _, phases: phase_by_id(phases, "REAL_USER_JOURNEY_ACCEPTANCE").update(
        {"complete_round_starts_at": "FAILED_STEP"}
    ),
)
assert_mutation_rejected(
    "PHASE_4_REPAIR_PRIORITY_WRONG",
    lambda _, phases: phase_by_id(phases, "REAL_USER_JOURNEY_ACCEPTANCE").update(
        {"repair_priority": ["BACKEND_CORE", "WORKFLOW", "UI"]}
    ),
)
assert_mutation_rejected(
    "PHASE_5_START_WRONG",
    lambda _, phases: phase_by_id(phases, "DELIVERY_PREPARATION").update(
        {"start_after": "ALL_REQUIRED_RUNS_ACCEPTED"}
    ),
)
assert_mutation_rejected(
    "MAINLINE_ORDER_CHANGED",
    lambda life, _: life["mainline"].reverse(),
)


def move_preparation_work_to_delivery(changed_lifecycle: dict, _: dict) -> None:
    bindings = changed_lifecycle["semantic_bindings"]
    for relation in ("DELIVERY_METHOD_QA", "DELIVERY_PACKAGE_GUARD"):
        bindings["DELIVERY_PREPARATION"].remove(relation)
        bindings["DELIVERY"].append(relation)


assert_mutation_rejected(
    "DELIVERY_OWNS_PREPARATION_WORK",
    move_preparation_work_to_delivery,
)


def omit_post_gate_delivery(changed_lifecycle: dict, _: dict) -> None:
    changed_lifecycle["semantic_bindings"]["DELIVERY"].remove(
        "ACTUAL_DELIVERY_AFTER_DELIVERY_READY"
    )


assert_mutation_rejected(
    "ACTUAL_DELIVERY_RELATION_MISSING",
    omit_post_gate_delivery,
)

print("PASS: five-phase lifecycle relationships reject boundary and aggregate drift")
