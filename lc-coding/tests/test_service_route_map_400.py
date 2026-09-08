from pathlib import Path
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "lc-coding/contracts/service-topology.json"
TEMPLATE_PATH = ROOT / "lc-coding/templates/SERVICE-ROUTE-MAP.json"
VALIDATOR_PATH = ROOT / "lc-coding/scripts/validate_service_topology.py"
STATUS_TEMPLATE_PATH = ROOT / "lc-coding/templates/STATUS.json"

assert CONTRACT_PATH.is_file(), "service topology contract is missing"
assert TEMPLATE_PATH.is_file(), "Service Route Map template is missing"
assert VALIDATOR_PATH.is_file(), "Service Route Map validator is missing"

validator_spec = importlib.util.spec_from_file_location(
    "validate_service_topology", VALIDATOR_PATH
)
validator = importlib.util.module_from_spec(validator_spec)
validator_spec.loader.exec_module(validator)

bootstrap_path = ROOT / "lc-coding/scripts/bootstrap_lccoding.py"
bootstrap_spec = importlib.util.spec_from_file_location("bootstrap_lccoding", bootstrap_path)
bootstrap = importlib.util.module_from_spec(bootstrap_spec)
bootstrap_spec.loader.exec_module(bootstrap)

project_validator_path = ROOT / "lc-coding/scripts/validate_project.py"
project_validator_spec = importlib.util.spec_from_file_location(
    "validate_project", project_validator_path
)
project_validator = importlib.util.module_from_spec(project_validator_spec)
project_validator_spec.loader.exec_module(project_validator)


MAP_FIELDS = (
    "record_role",
    "service_topology_schema_version",
    "map_id",
    "project_id",
    "state",
    "primary_strategy",
    "required_coexisting_strategies",
    "service_center_applicability",
    "journeys",
)
JOURNEY_FIELDS = (
    "journey_id",
    "journey_class",
    "delivery_state",
    "business_capability_id",
    "shared_capability_implementation_id",
    "routes",
)
ROUTE_FIELDS = (
    "route_id",
    "route_kind",
    "support_state",
    "delivery_state",
    "human_beneficiary_id",
    "actor_id",
    "actor_kind",
    "capability_id",
    "capability_implementation_id",
    "promised_entry",
    "human_observable_outcome",
    "authority",
    "consent",
    "adapter_or_surface_id",
    "acceptance_evidence_ids",
    "audit_event_ids",
)
AUTHORITY_FIELDS = ("action_id", "resource_id", "delegation_basis_id")
CONSENT_FIELDS = ("requirement", "policy_id")
STATUS_SUMMARY_FIELDS = (
    "lccoding_applicability",
    "product_service_strategy",
    "service_route_map",
)

contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
assert contract == {
    "schema_version": "4.0.0",
    "artifact_role": "SERVICE_TOPOLOGY_CONTRACT",
    "map_fields": list(MAP_FIELDS),
    "journey_fields": list(JOURNEY_FIELDS),
    "route_fields": list(ROUTE_FIELDS),
    "authority_fields": list(AUTHORITY_FIELDS),
    "consent_fields": list(CONSENT_FIELDS),
    "map_states": ["PENDING", "DRAFT", "ADOPTED"],
    "primary_strategies": ["PLATFORM_COMPLETION", "AGENT_COLLABORATIVE"],
    "route_kinds": ["DIRECT_PRODUCT", "PERSONAL_AGENT", "SERVICE_CENTER"],
    "route_actor_kinds": {
        "DIRECT_PRODUCT": ["HUMAN_PRINCIPAL"],
        "PERSONAL_AGENT": ["PERSONAL_AGENT"],
        "SERVICE_CENTER": ["SERVICE_CENTER_ACTOR"],
    },
    "external_actor_kinds": [
        "HUMAN_PRINCIPAL",
        "PERSONAL_AGENT",
        "SERVICE_CENTER_ACTOR",
    ],
    "internal_actor_kinds": ["PRODUCT_AGENT", "OPERATIONS_AGENT"],
    "service_center_applicability_values": [
        "PENDING",
        "APPLICABLE",
        "NOT_APPLICABLE",
    ],
    "journey_classes": ["CORE", "EXTRA"],
    "journey_delivery_states": ["PLANNED", "DELIVERED"],
    "route_support_states": ["REQUIRED", "UNSUPPORTED", "FUTURE"],
    "route_delivery_states": ["UNPROVED", "DELIVERED", "NOT_CLAIMED"],
    "consent_requirements": [
        "NOT_REQUIRED",
        "REQUIRED",
        "HUMAN_CONFIRMATION_REQUIRED",
    ],
    "status_summary_fields": list(STATUS_SUMMARY_FIELDS),
    "status_summary_initial": {
        "lccoding_applicability": "PENDING",
        "product_service_strategy": "PENDING",
        "service_route_map": "PENDING",
    },
    "shared_capability_system": "WORKFLOW_BACKEND_CORE",
}
assert not (
    set(contract["external_actor_kinds"]) & set(contract["internal_actor_kinds"])
), "external and internal actor kinds must be disjoint"

template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
assert tuple(template) == MAP_FIELDS
assert template == {
    "record_role": "CALABASH_SERVICE_ROUTE_MAP",
    "service_topology_schema_version": "4.0.0",
    "map_id": "",
    "project_id": "",
    "state": "PENDING",
    "primary_strategy": "PENDING",
    "required_coexisting_strategies": [],
    "service_center_applicability": "PENDING",
    "journeys": [],
}

# Task 10 activates the schema-selected 4.0 defaults without rewriting 3.0 reads.
current_status = json.loads(STATUS_TEMPLATE_PATH.read_text(encoding="utf-8"))
assert current_status["status_schema_version"] == "4.0.0"
assert {field: current_status[field] for field in STATUS_SUMMARY_FIELDS} == contract[
    "status_summary_initial"
]
assert bootstrap.service_topology_status_defaults(copy.deepcopy(current_status)) == current_status
legacy_status = {"status_schema_version": "3.0.0"}
assert bootstrap.service_topology_status_defaults(copy.deepcopy(legacy_status)) == legacy_status


def authority(label, delegation="NOT_APPLICABLE"):
    return {
        "action_id": "ACTION-" + label,
        "resource_id": "RESOURCE-APPLICATION",
        "delegation_basis_id": delegation,
    }


def consent(label, requirement):
    return {
        "requirement": requirement,
        "policy_id": "CONSENT-POLICY-" + label,
    }


def route(
    route_id,
    route_kind,
    actor_id,
    actor_kind,
    delegation,
    audit_events,
):
    return {
        "route_id": route_id,
        "route_kind": route_kind,
        "support_state": "REQUIRED",
        "delivery_state": "DELIVERED",
        "human_beneficiary_id": "HUMAN-1",
        "actor_id": actor_id,
        "actor_kind": actor_kind,
        "capability_id": "CAPABILITY-APPLICATION-SUBMISSION",
        "capability_implementation_id": "WORKFLOW-CAPABILITY-APPLICATION-SUBMISSION",
        "promised_entry": "application submission entry",
        "human_observable_outcome": "human sees the accepted application result",
        "authority": authority(route_kind, delegation),
        "consent": consent(
            route_kind,
            "NOT_REQUIRED" if route_kind == "DIRECT_PRODUCT" else "REQUIRED",
        ),
        "adapter_or_surface_id": "SURFACE-" + route_kind,
        "acceptance_evidence_ids": ["EVIDENCE-" + route_kind],
        "audit_event_ids": audit_events,
    }


positive = {
    "record_role": "CALABASH_SERVICE_ROUTE_MAP",
    "service_topology_schema_version": "4.0.0",
    "map_id": "SERVICE-ROUTES-1",
    "project_id": "PROJECT-1",
    "state": "ADOPTED",
    "primary_strategy": "AGENT_COLLABORATIVE",
    "required_coexisting_strategies": ["PLATFORM_COMPLETION"],
    "service_center_applicability": "APPLICABLE",
    "journeys": [
        {
            "journey_id": "JOURNEY-APPLICATION",
            "journey_class": "CORE",
            "delivery_state": "DELIVERED",
            "business_capability_id": "CAPABILITY-APPLICATION-SUBMISSION",
            "shared_capability_implementation_id": (
                "WORKFLOW-CAPABILITY-APPLICATION-SUBMISSION"
            ),
            "routes": [
                route(
                    "ROUTE-DIRECT-APPLICATION",
                    "DIRECT_PRODUCT",
                    "HUMAN-1",
                    "HUMAN_PRINCIPAL",
                    "NOT_APPLICABLE",
                    [],
                ),
                route(
                    "ROUTE-PERSONAL-AGENT-APPLICATION",
                    "PERSONAL_AGENT",
                    "PERSONAL-AGENT-1",
                    "PERSONAL_AGENT",
                    "DELEGATION-PERSONAL-AGENT-1",
                    ["AUDIT-PERSONAL-AGENT-1"],
                ),
                route(
                    "ROUTE-SERVICE-CENTER-APPLICATION",
                    "SERVICE_CENTER",
                    "SERVICE-CENTER-ACTOR-1",
                    "SERVICE_CENTER_ACTOR",
                    "DELEGATION-SERVICE-CENTER-1",
                    ["AUDIT-SERVICE-CENTER-1"],
                ),
            ],
        }
    ],
}
positive_status = {
    "status_schema_version": "4.0.0",
    "project_id": "PROJECT-1",
    "lccoding_applicability": "WHOLE_PRODUCT_FIT",
    "product_service_strategy": "MIXED",
    "service_route_map": "ADOPTED",
}


def validate(record, status=None):
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        lc = root / ".lccoding"
        lc.mkdir()
        (lc / "SERVICE-ROUTE-MAP.json").write_text(
            json.dumps(record, indent=2), encoding="utf-8"
        )
        return validator.validate_service_route_map(
            root, copy.deepcopy(status or positive_status)
        )


def rejected(label, mutate, expected):
    changed = copy.deepcopy(positive)
    mutate(changed)
    errors = validate(changed)
    assert errors, label
    assert any(expected in error for error in errors), (label, errors)


assert validate(positive) == []

pending_fit_status = copy.deepcopy(positive_status)
pending_fit_status["lccoding_applicability"] = "PENDING"
pending_fit_errors = validate(positive, pending_fit_status)
assert any("decided LCCoding applicability" in error for error in pending_fit_errors), (
    pending_fit_errors
)

rejected(
    "closed map",
    lambda value: value.__setitem__("project_wide_permission", "ALL"),
    "unknown fields",
)
rejected(
    "closed route",
    lambda value: value["journeys"][0]["routes"][0].pop("promised_entry"),
    "missing fields",
)
for label, mutate in (
    ("strategy type", lambda value: value.__setitem__("primary_strategy", [])),
    (
        "coexisting strategy type",
        lambda value: value.__setitem__("required_coexisting_strategies", [{}]),
    ),
    (
        "journey identity type",
        lambda value: value["journeys"][0].__setitem__("journey_id", []),
    ),
    (
        "route kind type",
        lambda value: value["journeys"][0]["routes"][0].__setitem__(
            "route_kind", {}
        ),
    ),
):
    changed = copy.deepcopy(positive)
    mutate(changed)
    assert validate(changed), label
rejected(
    "stable map id", lambda value: value.__setitem__("map_id", "bad map id"), "map_id"
)
rejected(
    "duplicate journey route pair",
    lambda value: value["journeys"][0]["routes"].append(
        copy.deepcopy(value["journeys"][0]["routes"][0])
    ),
    "duplicate journey/route pair",
)
rejected(
    "missing human outcome",
    lambda value: value["journeys"][0]["routes"][1].__setitem__(
        "human_observable_outcome", ""
    ),
    "human_observable_outcome",
)
rejected(
    "Personal Agent identity separation",
    lambda value: value["journeys"][0]["routes"][1].__setitem__(
        "actor_kind", "PRODUCT_AGENT"
    ),
    "actor_kind",
)
rejected(
    "no project-wide permission",
    lambda value: value["journeys"][0]["routes"][1]["authority"].__setitem__(
        "action_id", "ALL"
    ),
    "project-wide blanket permission",
)
rejected(
    "no permission scoped to the whole project identity",
    lambda value: value["journeys"][0]["routes"][1]["authority"].__setitem__(
        "resource_id", value["project_id"]
    ),
    "project-wide blanket permission",
)
rejected(
    "unsupported route cannot claim delivery",
    lambda value: value["journeys"][0]["routes"][0].__setitem__(
        "support_state", "UNSUPPORTED"
    ),
    "cannot claim DELIVERED",
)
rejected(
    "Service Center delegation",
    lambda value: value["journeys"][0]["routes"][2]["authority"].__setitem__(
        "delegation_basis_id", "NOT_APPLICABLE"
    ),
    "Service Center",
)
rejected(
    "Service Center audit",
    lambda value: value["journeys"][0]["routes"][2].__setitem__(
        "audit_event_ids", []
    ),
    "Service Center",
)
rejected(
    "one shared capability implementation",
    lambda value: value["journeys"][0]["routes"][2].__setitem__(
        "capability_implementation_id", "WORKFLOW-CAPABILITY-DUPLICATE"
    ),
    "shared capability implementation",
)
rejected(
    "selected strategy consistency",
    lambda value: value.__setitem__("required_coexisting_strategies", []),
    "selected strategy",
)


def remove_required_routes(value):
    for item in value["journeys"][0]["routes"]:
        item["support_state"] = "FUTURE"
        item["delivery_state"] = "NOT_CLAIMED"


rejected(
    "delivered journey support", remove_required_routes, "at least one required route"
)

not_applicable_service_center = copy.deepcopy(positive)
not_applicable_service_center["service_center_applicability"] = "NOT_APPLICABLE"
errors = validate(not_applicable_service_center)
assert any("Service Center applicability" in error for error in errors), errors

# The project validator dispatches only 4.0 records to the topology validator.
calls = []
original_validate = project_validator.validate_service_route_map
project_validator.validate_service_route_map = lambda root, status: calls.append(
    (root, status)
) or ["CALLED"]
try:
    assert project_validator.validate_service_topology_for_schema(
        Path("legacy"), {"status_schema_version": "3.0.0"}
    ) == []
    assert calls == []
    assert project_validator.validate_service_topology_for_schema(
        Path("current"), {"status_schema_version": "4.0.0"}
    ) == ["CALLED"]
    assert len(calls) == 1
finally:
    project_validator.validate_service_route_map = original_validate

# Bootstrap always copies the pending route-map template, while the active 3.0
# status remains exact until the planned 4.0 carrier promotion.
with tempfile.TemporaryDirectory() as temporary:
    cp = subprocess.run(
        [
            sys.executable,
            str(bootstrap_path),
            "--project",
            temporary,
            "--name",
            "Route Map Project",
            "--repository",
            "owner/route-map-project",
            "--visibility",
            "private",
        ],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 0, cp.stdout + cp.stderr
    bootstrapped = Path(temporary) / ".lccoding"
    assert (bootstrapped / "SERVICE-ROUTE-MAP.json").read_bytes() == (
        TEMPLATE_PATH.read_bytes()
    )
    bootstrapped_status = json.loads(
        (bootstrapped / "status.json").read_text(encoding="utf-8")
    )
    assert bootstrapped_status["status_schema_version"] == "4.0.0"
    assert {
        field: bootstrapped_status[field] for field in STATUS_SUMMARY_FIELDS
    } == contract["status_summary_initial"]

print("PASS: 4.0 Calabash Service Route Map contract and validation")
