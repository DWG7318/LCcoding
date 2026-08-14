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
EXPECTED_MAINLINE_BYTES = (
    b'["PROPOSAL_READINESS","PROJECT_INITIALIZATION","CALABASH_DRAFT",'
    b'"WORKFLOW_UI_SIMULATION","MANDATORY_CALABASH_UPGRADE",'
    b'"PRODUCT_BASELINE","FEATURE_SLICE","FEATURE_INTEGRATION",'
    b'"FINAL_VERIFICATION","OWNER_ACCEPTANCE","DELIVERY"]'
)
EXPECTED_PHASE_IDS = [
    "INITIAL",
    "PRODUCT_FORMATION",
    "REAL_PRODUCT_INTEGRATION",
    "DELIVERY_PREPARATION",
]
EXPECTED_AGGREGATE_EXCLUDES = {
    "INITIAL_RUNS",
    "PRODUCT_FORMATION_RUNS",
    "DELIVERY_PREPARATION_RUNS",
    "OPTIONAL_RUNS",
    "SUPERSEDED_RUNS",
    "INVALIDATED_RUNS",
}


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def phase_by_id(contract: dict, phase_id: str) -> dict:
    matches = [phase for phase in contract.get("phases", []) if phase.get("id") == phase_id]
    if len(matches) != 1:
        return {}
    return matches[0]


def validate_phase_semantics(current_lifecycle: dict, current_phases: dict) -> set[str]:
    errors: set[str] = set()

    if current_lifecycle.get("version") != "2.8.0" or current_phases.get("version") != "2.8.0":
        errors.add("VERSION_CARRIER_CHANGED_EARLY")

    mainline = current_lifecycle.get("mainline")
    if canonical_bytes(mainline) != EXPECTED_MAINLINE_BYTES:
        errors.add("MAINLINE_ORDER_CHANGED")
    expected_transitions = dict(zip(EXPECTED_MAINLINE, EXPECTED_MAINLINE[1:]))
    if current_lifecycle.get("required_transitions") != expected_transitions:
        errors.add("MAINLINE_TRANSITIONS_CHANGED")

    phase_ids = [phase.get("id") for phase in current_phases.get("phases", [])]
    if phase_ids != EXPECTED_PHASE_IDS:
        errors.add("PHASE_IDS_CHANGED")
    if current_phases.get("mainline_unchanged") is not True:
        errors.add("MAINLINE_NOT_DECLARED_UNCHANGED")

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
    if "ALL_REQUIRED_PHASE_3_INTEGRATION_RUNS_ACCEPTED" not in bindings.get(
        "FEATURE_INTEGRATION", []
    ):
        errors.add("LIFECYCLE_AGGREGATE_SCOPE_RELATION_MISSING")

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

print("PASS: four-phase lifecycle relationships reject boundary and aggregate drift")
