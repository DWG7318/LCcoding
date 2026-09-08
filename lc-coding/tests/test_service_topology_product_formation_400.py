from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import tempfile


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "lc-coding/scripts/validate_project.py"

spec = importlib.util.spec_from_file_location("validate_project", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


FORMATION_FILES = {
    "lc-coding/references/product-formation.md": (
        "required service route",
        "same Workflow capability",
        "API or MCP presence alone",
    ),
    "lc-coding/templates/WORKFLOW-MAP.md": (
        "| Service Route ID | Workflow ID | Workflow Capability ID |",
    ),
    "lc-coding/templates/UI-MAP.md": (
        "| Service Route ID | Service Surface ID | Service Surface Kind | Workflow Capability ID |",
        "HUMAN_RESULT_CONSENT_EXCEPTION",
    ),
    "lc-coding/templates/SIMULATION-WORLD.md": (
        "| Service Route ID | Simulation ID | Workflow Capability ID | Scenario IDs | Audit event IDs |",
    ),
    "lc-coding/templates/PRODUCT-BASELINE-HANDOFF.md": (
        "- Service Route Map ID / exact hash:",
        "| Service Route ID | Workflow Capability ID | Service Surface IDs | Simulation Scenario IDs | Audit event IDs |",
    ),
}
for relative, markers in FORMATION_FILES.items():
    text = (ROOT / relative).read_text(encoding="utf-8")
    for marker in markers:
        assert marker in text, (relative, marker)

assert hasattr(validator, "validate_service_topology_product_formation"), (
    "4.0 Product Baseline route join validator is missing"
)


def route(
    route_id,
    route_kind,
    actor_id,
    actor_kind,
    delegation,
    surface_id,
    audit_ids,
    *,
    capability="CAP-APPLICATION",
    support="REQUIRED",
    delivery="UNPROVED",
):
    return {
        "route_id": route_id,
        "route_kind": route_kind,
        "support_state": support,
        "delivery_state": delivery,
        "human_beneficiary_id": "HUMAN-1",
        "actor_id": actor_id,
        "actor_kind": actor_kind,
        "capability_id": "BUSINESS-APPLICATION",
        "capability_implementation_id": capability,
        "promised_entry": "application submission entry",
        "human_observable_outcome": "human sees the application result",
        "authority": {
            "action_id": "ACTION-" + route_id,
            "resource_id": "RESOURCE-APPLICATION",
            "delegation_basis_id": delegation,
        },
        "consent": {
            "requirement": (
                "NOT_REQUIRED" if route_kind == "DIRECT_PRODUCT" else "REQUIRED"
            ),
            "policy_id": "POLICY-" + route_id,
        },
        "adapter_or_surface_id": surface_id,
        "acceptance_evidence_ids": ["EVIDENCE-" + route_id]
        if support == "REQUIRED"
        else [],
        "audit_event_ids": audit_ids,
    }


SERVICE_MAP = {
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
            "delivery_state": "PLANNED",
            "business_capability_id": "BUSINESS-APPLICATION",
            "shared_capability_implementation_id": "CAP-APPLICATION",
            "routes": [
                route(
                    "ROUTE-DIRECT",
                    "DIRECT_PRODUCT",
                    "HUMAN-1",
                    "HUMAN_PRINCIPAL",
                    "NOT_APPLICABLE",
                    "UI-DIRECT",
                    [],
                ),
                route(
                    "ROUTE-AGENT",
                    "PERSONAL_AGENT",
                    "PERSONAL-AGENT-1",
                    "PERSONAL_AGENT",
                    "DELEGATION-AGENT-1",
                    "AGENT-SERVICE-APPLICATION",
                    ["AUDIT-AGENT"],
                ),
                route(
                    "ROUTE-CENTER",
                    "SERVICE_CENTER",
                    "SERVICE-CENTER-ACTOR-1",
                    "SERVICE_CENTER_ACTOR",
                    "DELEGATION-CENTER-1",
                    "SERVICE-CENTER-APPLICATION",
                    ["AUDIT-CENTER"],
                ),
            ],
        },
        {
            "journey_id": "JOURNEY-FUTURE",
            "journey_class": "EXTRA",
            "delivery_state": "PLANNED",
            "business_capability_id": "BUSINESS-APPLICATION",
            "shared_capability_implementation_id": "CAP-APPLICATION",
            "routes": [
                route(
                    "ROUTE-FUTURE",
                    "PERSONAL_AGENT",
                    "PERSONAL-AGENT-2",
                    "PERSONAL_AGENT",
                    "DELEGATION-AGENT-2",
                    "AGENT-SERVICE-FUTURE",
                    [],
                    support="FUTURE",
                    delivery="NOT_CLAIMED",
                )
            ],
        },
    ],
}

STATUS_400 = {
    "status_schema_version": "4.0.0",
    "project_id": "PROJECT-1",
    "product_baseline": "ACCEPTED",
    "lccoding_applicability": "WHOLE_PRODUCT_FIT",
    "product_service_strategy": "MIXED",
    "service_route_map": "ADOPTED",
}

WORKFLOWS = [
    {
        "Workflow ID": "WF-APPLICATION",
        "Workflow Capability ID": "CAP-APPLICATION",
        "API contract / evidence": (
            "CAPABILITY:CAP-APPLICATION; CONTRACT:API-APPLICATION; EVIDENCE:E-API"
        ),
        "MCP contract / evidence": (
            "CAPABILITY:CAP-APPLICATION; CONTRACT:MCP-APPLICATION; EVIDENCE:E-MCP"
        ),
    }
]
WORKFLOW_ROUTES = [
    {
        "Service Route ID": route_id,
        "Workflow ID": "WF-APPLICATION",
        "Workflow Capability ID": "CAP-APPLICATION",
    }
    for route_id in ("ROUTE-DIRECT", "ROUTE-AGENT", "ROUTE-CENTER")
]
UI_ROWS = [{"UI ID": "UI-DIRECT"}, {"UI ID": "UI-HUMAN-RESULT"}]
SURFACES = [
    {
        "Service Route ID": "ROUTE-DIRECT",
        "Service Surface ID": "UI-DIRECT",
        "Service Surface Kind": "DIRECT_PRODUCT",
        "Workflow Capability ID": "CAP-APPLICATION",
    },
    {
        "Service Route ID": "ROUTE-AGENT",
        "Service Surface ID": "AGENT-SERVICE-APPLICATION",
        "Service Surface Kind": "AGENT_SERVICE",
        "Workflow Capability ID": "CAP-APPLICATION",
    },
    {
        "Service Route ID": "ROUTE-AGENT",
        "Service Surface ID": "UI-HUMAN-RESULT",
        "Service Surface Kind": "HUMAN_RESULT_CONSENT_EXCEPTION",
        "Workflow Capability ID": "CAP-APPLICATION",
    },
    {
        "Service Route ID": "ROUTE-CENTER",
        "Service Surface ID": "SERVICE-CENTER-APPLICATION",
        "Service Surface Kind": "SERVICE_CENTER_ASSISTED",
        "Workflow Capability ID": "CAP-APPLICATION",
    },
]
SIMULATIONS = [{"Simulation ID": "SIM-APPLICATION"}]
SCENARIOS = [
    {"Simulation ID": "SIM-APPLICATION", "Scenario ID": scenario_id}
    for scenario_id in ("SCENARIO-DIRECT", "SCENARIO-AGENT", "SCENARIO-CENTER")
]
SIMULATION_ROUTES = [
    {
        "Service Route ID": "ROUTE-DIRECT",
        "Simulation ID": "SIM-APPLICATION",
        "Workflow Capability ID": "CAP-APPLICATION",
        "Scenario IDs": "SCENARIO-DIRECT",
        "Audit event IDs": "NONE",
    },
    {
        "Service Route ID": "ROUTE-AGENT",
        "Simulation ID": "SIM-APPLICATION",
        "Workflow Capability ID": "CAP-APPLICATION",
        "Scenario IDs": "SCENARIO-AGENT",
        "Audit event IDs": "AUDIT-AGENT",
    },
    {
        "Service Route ID": "ROUTE-CENTER",
        "Simulation ID": "SIM-APPLICATION",
        "Workflow Capability ID": "CAP-APPLICATION",
        "Scenario IDs": "SCENARIO-CENTER",
        "Audit event IDs": "AUDIT-CENTER",
    },
]
HANDOFF_ROUTES = [
    {
        "Service Route ID": "ROUTE-DIRECT",
        "Workflow Capability ID": "CAP-APPLICATION",
        "Service Surface IDs": "UI-DIRECT",
        "Simulation Scenario IDs": "SCENARIO-DIRECT",
        "Audit event IDs": "NONE",
    },
    {
        "Service Route ID": "ROUTE-AGENT",
        "Workflow Capability ID": "CAP-APPLICATION",
        "Service Surface IDs": "AGENT-SERVICE-APPLICATION, UI-HUMAN-RESULT",
        "Simulation Scenario IDs": "SCENARIO-AGENT",
        "Audit event IDs": "AUDIT-AGENT",
    },
    {
        "Service Route ID": "ROUTE-CENTER",
        "Workflow Capability ID": "CAP-APPLICATION",
        "Service Surface IDs": "SERVICE-CENTER-APPLICATION",
        "Simulation Scenario IDs": "SCENARIO-CENTER",
        "Audit event IDs": "AUDIT-CENTER",
    },
]


def exact_hash(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def validate_fixture(
    *,
    service_map=None,
    status=None,
    workflow_routes=None,
    surfaces=None,
    simulation_routes=None,
    handoff_routes=None,
    mutate_handoff=None,
):
    with tempfile.TemporaryDirectory(prefix="service-formation-400-") as temporary:
        root = Path(temporary)
        lc = root / ".lccoding"
        lc.mkdir()
        map_path = lc / "SERVICE-ROUTE-MAP.json"
        map_path.write_text(
            json.dumps(service_map or SERVICE_MAP, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        handoff_fields = {
            "Calabash Definition Handoff ID / exact hash": (
                "CALABASH-HANDOFF-1 / sha256:" + "a" * 64
            ),
            "Service Route Map ID / exact hash": (
                "SERVICE-ROUTES-1 / " + exact_hash(map_path)
            ),
        }
        if mutate_handoff:
            mutate_handoff(handoff_fields)
        return validator.validate_service_topology_product_formation(
            root,
            copy.deepcopy(status or STATUS_400),
            handoff_fields,
            copy.deepcopy(WORKFLOWS),
            copy.deepcopy(workflow_routes if workflow_routes is not None else WORKFLOW_ROUTES),
            copy.deepcopy(UI_ROWS),
            copy.deepcopy(surfaces if surfaces is not None else SURFACES),
            copy.deepcopy(SIMULATIONS),
            copy.deepcopy(SCENARIOS),
            copy.deepcopy(
                simulation_routes if simulation_routes is not None else SIMULATION_ROUTES
            ),
            copy.deepcopy(handoff_routes if handoff_routes is not None else HANDOFF_ROUTES),
        )


assert validate_fixture() == []

# Exact 3.0 behavior is retained: no 4.0 formation join is required or inferred.
assert validator.validate_service_topology_product_formation(
    Path("missing"), {"status_schema_version": "3.0.0", "product_baseline": "ACCEPTED"},
    {}, [], [], [], [], [], [], [], [],
) == []


wrong_map_hash = validate_fixture(
    mutate_handoff=lambda fields: fields.__setitem__(
        "Service Route Map ID / exact hash",
        "SERVICE-ROUTES-1 / sha256:" + "0" * 64,
    )
)
assert any("Service Route Map identity/hash mismatch" in error for error in wrong_map_hash), wrong_map_hash

split_capability = copy.deepcopy(WORKFLOW_ROUTES)
split_capability[-1]["Workflow Capability ID"] = "CAP-DUPLICATE"
split_errors = validate_fixture(workflow_routes=split_capability)
assert any("same Workflow capability" in error for error in split_errors), split_errors

no_agent_service = [
    row for row in SURFACES if row["Service Surface Kind"] != "AGENT_SERVICE"
]
agent_service_errors = validate_fixture(surfaces=no_agent_service)
assert any("Agent service surface" in error for error in agent_service_errors), agent_service_errors

no_human_surface = [
    row
    for row in SURFACES
    if row["Service Surface Kind"] != "HUMAN_RESULT_CONSENT_EXCEPTION"
]
human_surface_errors = validate_fixture(surfaces=no_human_surface)
assert any(
    "human result/consent/exception surface" in error for error in human_surface_errors
), human_surface_errors

no_center_simulation = [
    row for row in SIMULATION_ROUTES if row["Service Route ID"] != "ROUTE-CENTER"
]
center_simulation_errors = validate_fixture(simulation_routes=no_center_simulation)
assert any("Service Center Simulation coverage" in error for error in center_simulation_errors), center_simulation_errors

no_center_audit = copy.deepcopy(SIMULATION_ROUTES)
no_center_audit[-1]["Audit event IDs"] = "NONE"
center_audit_errors = validate_fixture(simulation_routes=no_center_audit)
assert any("Service Center audit coverage" in error for error in center_audit_errors), center_audit_errors

unsupported_claim = copy.deepcopy(HANDOFF_ROUTES)
unsupported_claim.append(
    {
        "Service Route ID": "ROUTE-FUTURE",
        "Workflow Capability ID": "CAP-APPLICATION",
        "Service Surface IDs": "AGENT-SERVICE-FUTURE",
        "Simulation Scenario IDs": "SCENARIO-FUTURE",
        "Audit event IDs": "NONE",
    }
)
unsupported_errors = validate_fixture(handoff_routes=unsupported_claim)
assert any("unsupported or future route" in error for error in unsupported_errors), unsupported_errors

# Existing same-capability API/MCP evidence is not formation or delivery proof.
api_mcp_only_errors = validate_fixture(
    workflow_routes=[], surfaces=[], simulation_routes=[], handoff_routes=[]
)
for marker in (
    "Workflow route trace",
    "service surface",
    "Simulation coverage",
    "Product Baseline route trace",
):
    assert any(marker in error for error in api_mcp_only_errors), (
        marker,
        api_mcp_only_errors,
    )

handoff_surface_drift = copy.deepcopy(HANDOFF_ROUTES)
handoff_surface_drift[1]["Service Surface IDs"] = "AGENT-SERVICE-APPLICATION"
handoff_drift_errors = validate_fixture(handoff_routes=handoff_surface_drift)
assert any("handoff service surface identity mismatch" in error for error in handoff_drift_errors), handoff_drift_errors

print("PASS: 4.0 Product Formation binds required service routes to one shared capability")
