from pathlib import Path
import copy
import importlib.util
import json


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "lc-coding/contracts/runtime-adapter-attestation.json"
RUNTIME_TEMPLATE = ROOT / "lc-coding/templates/RUNTIME-ADAPTER-ATTESTATION.json"
IMPACT_TEMPLATE = ROOT / "lc-coding/templates/IMPACT-ANALYSIS.md"
SIMULATION_TEMPLATE = ROOT / "lc-coding/templates/SIMULATION-WORLD.md"
VALIDATOR = ROOT / "lc-coding/scripts/validate_agent_native.py"
RUNTIME_TEST = ROOT / "lc-coding/tests/test_runtime_adapter_attestation_280.py"

FAILURE_STATES = [
    "HEALTHY", "DEGRADED", "UNAVAILABLE", "KILLED", "RECOVERING", "REPLACED",
]
FAILURE_KINDS = [
    "NONE", "MODEL_UNAVAILABLE", "MODEL_DRIFT", "RUNTIME_ADAPTER_FAILURE",
    "TOOL_FAILURE", "AUTHORIZATION_DENIAL", "TELEMETRY_LOSS",
    "MEMORY_ISOLATION_FAILURE", "ACTION_FAILURE", "ROLLBACK_FAILURE",
    "AUDIT_FAILURE",
]
FAILURE_FIELDS = [
    "failure_id", "failure_kind", "lifecycle_state", "agent_role", "agent_id",
    "product_classification", "calabash_basis_id", "calabash_basis_hash",
    "candidate_id", "candidate_hash", "configuration_baseline_id",
    "configuration_baseline_hash", "production_topology_id",
    "production_topology_hash", "runtime_adapter_id", "runtime_adapter_version",
    "runtime_adapter_digest", "visible_impact", "core_business_continuity",
    "fallback_mode", "fallback_id", "fallback_evidence_path",
    "fallback_evidence_hash", "authority_result", "agent_separation_result",
    "scorpion_result", "credential_currentness", "audit_result",
    "proposal_action_boundary", "control_authority_id", "control_authority_hash",
    "root_authority_id", "root_authority_hash", "replacement_identity_id",
    "replacement_identity_hash", "material_identity_effect", "recovery_evidence_id",
    "recovery_evidence_path", "recovery_evidence_hash", "verification_evidence_id",
    "verification_evidence_path", "verification_evidence_hash", "audit_event_id",
    "audit_event_path", "audit_event_hash", "alert_evidence_id",
    "alert_evidence_path", "alert_evidence_hash", "affected_evidence_ids",
    "unaffected_core_evidence_ids", "evidence_currentness", "result",
]
DOCUMENT_FIELDS = [
    "schema_version", "artifact_role", "candidate_id", "candidate_hash",
    "configuration_baseline_id", "configuration_baseline_hash",
    "production_topology_id", "production_topology_hash", "runtime_adapter_id",
    "runtime_adapter_version", "runtime_adapter_digest",
    "failure_recovery_attestations",
]
IMPACT_HEADING = "## Agent failure impact evidence"
SIMULATION_HEADING = "## Agent failure simulation evidence"


contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
assert contract["failure_recovery_fields"] == FAILURE_FIELDS
assert contract["failure_document_fields"] == DOCUMENT_FIELDS
assert contract["failure_states"] == FAILURE_STATES
assert contract["failure_kinds"] == FAILURE_KINDS
assert "failure_recovery_attestations" in contract["top_level_fields"]
impact_template = IMPACT_TEMPLATE.read_text(encoding="utf-8")
simulation_template = SIMULATION_TEMPLATE.read_text(encoding="utf-8")
assert impact_template.count(IMPACT_HEADING) == 1
assert simulation_template.count(SIMULATION_HEADING) == 1


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_module("agent_failure_recovery_validator", VALIDATOR)
runtime_fixture = load_module("agent_failure_recovery_runtime_fixture", RUNTIME_TEST)
assert hasattr(validator, "validate_agent_failure_recovery")


def section_text(template, heading, record):
    marker = heading + "\n\n```json\n"
    assert template.count(marker) == 1
    start = template.index(marker) + len(marker)
    end = template.index("\n```", start)
    return template[:start] + json.dumps(record, indent=2) + template[end:]


def document(role, attestation):
    return {
        "schema_version": "2.8.0",
        "artifact_role": role,
        "candidate_id": attestation["candidate_id"],
        "candidate_hash": attestation["candidate_hash"],
        "configuration_baseline_id": attestation["configuration_baseline"][
            "configuration_baseline_id"
        ],
        "configuration_baseline_hash": attestation["configuration_baseline"][
            "configuration_baseline_hash"
        ],
        "production_topology_id": attestation["production_topology"][
            "production_topology_id"
        ],
        "production_topology_hash": attestation["production_topology"][
            "production_topology_hash"
        ],
        "runtime_adapter_id": attestation["runtime_adapter"]["adapter_id"],
        "runtime_adapter_version": attestation["runtime_adapter"]["adapter_version"],
        "runtime_adapter_digest": attestation["runtime_adapter"]["adapter_digest"],
        "failure_recovery_attestations": copy.deepcopy(
            attestation["failure_recovery_attestations"]
        ),
    }


configuration = runtime_fixture.valid_configuration()
attestation = runtime_fixture.valid_attestation(configuration)
cases = attestation["failure_recovery_attestations"]
assert [case["failure_kind"] for case in cases] == FAILURE_KINDS
assert set(case["lifecycle_state"] for case in cases) == set(FAILURE_STATES)
impact_record = document("AGENT_FAILURE_IMPACT_EVIDENCE", attestation)
simulation_record = document("AGENT_FAILURE_SIMULATION_EVIDENCE", attestation)
impact = section_text(impact_template, IMPACT_HEADING, impact_record)
simulation = section_text(simulation_template, SIMULATION_HEADING, simulation_record)
validate_args = (
    configuration,
    runtime_fixture.CONFIG_HASH,
    "TOPOLOGY-1",
    runtime_fixture.HASH_D,
    runtime_fixture.AS_OF,
)
assert validator.validate_agent_failure_recovery(
    impact, simulation, attestation, *validate_args
) == []

def synchronized_materials(changed_attestation):
    changed_impact = document("AGENT_FAILURE_IMPACT_EVIDENCE", changed_attestation)
    changed_simulation = document("AGENT_FAILURE_SIMULATION_EVIDENCE", changed_attestation)
    return (
        section_text(impact_template, IMPACT_HEADING, changed_impact),
        section_text(simulation_template, SIMULATION_HEADING, changed_simulation),
    )


def semantic_errors(changed_attestation):
    changed_impact, changed_simulation = synchronized_materials(changed_attestation)
    errors = validator.validate_agent_failure_recovery(
        changed_impact, changed_simulation, changed_attestation, *validate_args
    )
    assert not any("failure cases disagree" in error for error in errors), errors
    return errors


def assert_semantic_rejection(changed_attestation, marker):
    errors = semantic_errors(changed_attestation)
    assert any(marker in error for error in errors), errors


for index in range(len(cases)):
    changed = copy.deepcopy(attestation)
    changed["failure_recovery_attestations"][index].pop(
        FAILURE_FIELDS[index % len(FAILURE_FIELDS)]
    )
    assert_semantic_rejection(changed, "missing fields")

semantic_mutations = []


def mutate_case(kind, field, value, marker):
    changed = copy.deepcopy(attestation)
    case = next(
        item for item in changed["failure_recovery_attestations"]
        if item["failure_kind"] == kind
    )
    case[field] = value
    semantic_mutations.append((changed, marker))


mutate_case("NONE", "unknown", "x", "unknown fields")
mutate_case("MODEL_UNAVAILABLE", "candidate_id", "CANDIDATE-2", "candidate/configuration/topology/Adapter identity disagrees")
mutate_case("MODEL_DRIFT", "configuration_baseline_hash", runtime_fixture.HASH_A, "candidate/configuration/topology/Adapter identity disagrees")
mutate_case("RUNTIME_ADAPTER_FAILURE", "production_topology_hash", runtime_fixture.HASH_A, "candidate/configuration/topology/Adapter identity disagrees")
mutate_case("TOOL_FAILURE", "runtime_adapter_digest", runtime_fixture.HASH_A, "candidate/configuration/topology/Adapter identity disagrees")
mutate_case("AUTHORIZATION_DENIAL", "core_business_continuity", "CORE_CAPABILITY_BLOCKED", "Operations failure must not default-stop core business")
for field, value in (
    ("authority_result", "AGENT_SELF_AUTHORIZED"),
    ("agent_separation_result", "MERGED_AGENTS"),
    ("scorpion_result", "BYPASSED"),
    ("credential_currentness", "STALE_CREDENTIALS"),
    ("audit_result", "DISABLED"),
    ("proposal_action_boundary", "PROPOSAL_EXECUTED"),
):
    mutate_case("TOOL_FAILURE", field, value, "fallback expands authority or weakens safety boundaries")
mutate_case("MEMORY_ISOLATION_FAILURE", "control_authority_id", "AGENT-SELF", "control_authority binding is invalid")
mutate_case("ROLLBACK_FAILURE", "root_authority_id", "OPS-1", "root_authority binding is invalid")
mutate_case("RUNTIME_ADAPTER_FAILURE", "replacement_identity_id", "NOT_APPLICABLE", "replacement lacks material identity invalidation")
mutate_case("RUNTIME_ADAPTER_FAILURE", "material_identity_effect", "PRESERVE_OLD_EVIDENCE", "replacement lacks material identity invalidation")
mutate_case("MODEL_DRIFT", "evidence_currentness", "CURRENT", "changed evidence currentness is invalid")
mutate_case("TOOL_FAILURE", "fallback_evidence_path", "../outside.json", "Operations fallback is not bounded to configuration")
mutate_case("TELEMETRY_LOSS", "affected_evidence_ids", [], "affected evidence must be a closed ID list")

changed = copy.deepcopy(attestation)
changed["failure_recovery_attestations"].append(
    copy.deepcopy(changed["failure_recovery_attestations"][0])
)
semantic_mutations.append((changed, "failure/recovery IDs must be unique"))

for changed_attestation, marker in semantic_mutations:
    assert_semantic_rejection(changed_attestation, marker)

for classification, fallback_mode, continuity in (
    ("CORE", "ACCEPTED_NON_AGENT_FALLBACK", "CORE_BUSINESS_CONTINUES"),
    ("EXTRA", "NO_ACCEPTED_NON_AGENT_FALLBACK", "CORE_BUSINESS_CONTINUES"),
):
    changed = copy.deepcopy(attestation)
    product_case = next(
        item for item in changed["failure_recovery_attestations"]
        if item["agent_role"] == "PRODUCT_AGENT"
    )
    product_case["product_classification"] = classification
    product_case["fallback_mode"] = fallback_mode
    product_case["core_business_continuity"] = continuity
    if fallback_mode == "ACCEPTED_NON_AGENT_FALLBACK":
        product_case["fallback_id"] = "PRODUCT-NON-AGENT-FALLBACK-1"
        product_case["fallback_evidence_path"] = "evidence/failure/product-fallback.json"
        product_case["fallback_evidence_hash"] = runtime_fixture.HASH_C
    changed_impact, changed_simulation = synchronized_materials(changed)
    assert validator.validate_agent_failure_recovery(
        changed_impact, changed_simulation, changed, *validate_args
    ) == []

changed_impact = copy.deepcopy(impact_record)
changed_impact["candidate_hash"] = runtime_fixture.HASH_A
errors = validator.validate_agent_failure_recovery(
    section_text(impact_template, IMPACT_HEADING, changed_impact),
    simulation,
    attestation,
    *validate_args,
)
assert any("AGENT_FAILURE_IMPACT_EVIDENCE candidate/configuration/topology/Adapter identity disagrees" in error for error in errors), errors
changed_simulation = copy.deepcopy(simulation_record)
changed_simulation["failure_recovery_attestations"][0]["visible_impact"] = "SILENT"
errors = validator.validate_agent_failure_recovery(
    impact,
    section_text(simulation_template, SIMULATION_HEADING, changed_simulation),
    attestation,
    *validate_args,
)
assert any("AGENT_FAILURE_SIMULATION_EVIDENCE failure cases disagree" in error for error in errors), errors

assert validator.validate_agent_failure_recovery(
    impact_template, simulation_template, json.loads(RUNTIME_TEMPLATE.read_text(encoding="utf-8")),
    *validate_args
)

print("PASS: Agent failure, degradation, fallback, recovery, and replacement are evidence-bound")
