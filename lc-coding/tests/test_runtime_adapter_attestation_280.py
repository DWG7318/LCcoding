from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import tempfile


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "lc-coding/contracts/runtime-adapter-attestation.json"
TEMPLATE = ROOT / "lc-coding/templates/RUNTIME-ADAPTER-ATTESTATION.json"
VALIDATOR = ROOT / "lc-coding/scripts/validate_agent_native.py"

assert CONTRACT.is_file(), "Runtime Adapter Attestation contract is absent"
assert TEMPLATE.is_file(), "Runtime Adapter Attestation template is absent"
assert VALIDATOR.is_file(), "Agent-native validator is absent"

TOP_LEVEL_FIELDS = [
    "schema_version",
    "artifact_role",
    "attestation_id",
    "candidate_id",
    "candidate_hash",
    "runtime_adapter",
    "runtime_provider",
    "configuration_baseline",
    "production_topology",
    "loaded_result",
    "capability_attestations",
    "authority_boundaries",
    "typed_event_attestations",
    "failure_recovery_attestations",
    "validity",
    "evidence",
    "fallback",
    "kill_switch",
    "conformance",
]
CONFORMANCE_CASES = [
    "REFERENCE_ADAPTER_POSITIVE",
    "REFERENCE_ADAPTER_NEGATIVE",
    "FAKE_ADAPTER_POSITIVE",
    "FAKE_ADAPTER_NEGATIVE",
]
contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
assert set(contract) == {
    "schema_version",
    "artifact_role",
    "top_level_fields",
    "runtime_adapter_fields",
    "runtime_provider_fields",
    "configuration_fields",
    "topology_fields",
    "capability_fields",
    "authority_boundary_fields",
    "typed_event_fields",
    "event_kinds",
    "failure_document_fields",
    "failure_recovery_fields",
    "failure_states",
    "failure_kinds",
    "validity_fields",
    "evidence_fields",
    "fallback_fields",
    "kill_switch_fields",
    "conformance_fields",
    "conformance_cases",
    "provider_kinds",
    "max_observation_age_seconds",
}
assert contract["schema_version"] == "2.8.0"
assert contract["artifact_role"] == "RUNTIME_ADAPTER_ATTESTATION_CONTRACT"
assert contract["top_level_fields"] == TOP_LEVEL_FIELDS
assert contract["runtime_adapter_fields"] == [
    "adapter_id", "adapter_version", "adapter_digest",
]
assert contract["runtime_provider_fields"] == [
    "provider_id", "provider_kind", "identity_evidence_id",
    "identity_evidence_hash", "verification_result",
]
assert contract["configuration_fields"] == [
    "configuration_baseline_id", "configuration_baseline_hash",
]
assert contract["topology_fields"] == [
    "production_topology_id", "production_topology_hash",
]
assert contract["capability_fields"] == [
    "agent_role", "agent_id", "capability_id", "policy_id", "policy_hash",
    "action_catalog_id", "action_catalog_hash", "configuration_id",
    "configuration_hash", "authorization_result",
]
assert contract["authority_boundary_fields"] == [
    "runtime_permission", "agent_separation", "scorpion_policy_id",
    "scorpion_policy_hash", "scorpion_result", "environment_fallback",
    "provider_authority", "secret_loading", "isolation_evidence_id",
    "isolation_evidence_hash", "private_boundary_result",
    "shared_execution_result",
]
EVENT_FIELDS = [
    "event_id", "event_kind", "event_schema_id", "event_schema_hash",
    "source_agent_id", "target_agent_id", "candidate_id", "candidate_hash",
    "payload_classification", "provenance_id", "provenance_hash", "policy_id",
    "policy_hash", "policy_result", "redaction_result", "event_at_utc",
]
EVENT_KINDS = ["MAINTENANCE_REQUEST", "SERVICE_STATUS_UPDATE"]
FAILURE_STATES = [
    "HEALTHY", "DEGRADED", "UNAVAILABLE", "KILLED", "RECOVERING", "REPLACED",
]
FAILURE_KINDS = [
    "NONE", "MODEL_UNAVAILABLE", "MODEL_DRIFT", "RUNTIME_ADAPTER_FAILURE",
    "TOOL_FAILURE", "AUTHORIZATION_DENIAL", "TELEMETRY_LOSS",
    "MEMORY_ISOLATION_FAILURE", "ACTION_FAILURE", "ROLLBACK_FAILURE",
    "AUDIT_FAILURE",
]
FAILURE_DOCUMENT_FIELDS = [
    "schema_version", "artifact_role", "candidate_id", "candidate_hash",
    "configuration_baseline_id", "configuration_baseline_hash",
    "production_topology_id", "production_topology_hash", "runtime_adapter_id",
    "runtime_adapter_version", "runtime_adapter_digest",
    "failure_recovery_attestations",
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
assert contract["typed_event_fields"] == EVENT_FIELDS
assert contract["event_kinds"] == EVENT_KINDS
assert contract["failure_document_fields"] == FAILURE_DOCUMENT_FIELDS
assert contract["failure_recovery_fields"] == FAILURE_FIELDS
assert contract["failure_states"] == FAILURE_STATES
assert contract["failure_kinds"] == FAILURE_KINDS
assert contract["validity_fields"] == [
    "observed_at_utc", "validated_at_utc", "expires_at_utc",
]
assert contract["evidence_fields"] == [
    "evidence_id", "evidence_path", "evidence_hash", "producer_kind",
    "independence", "result",
]
assert contract["fallback_fields"] == [
    "fallback_id", "evidence_path", "evidence_hash", "result",
]
assert contract["kill_switch_fields"] == [
    "kill_switch_id", "evidence_path", "evidence_hash", "result",
]
assert contract["conformance_fields"] == [
    "case_id", "harness_id", "evidence_id", "evidence_hash", "result",
]
assert contract["conformance_cases"] == CONFORMANCE_CASES
assert contract["provider_kinds"] == [
    "REFERENCE_RUNTIME", "EXTERNAL_RUNTIME", "OWNER_APPROVED_CUSTOM_RUNTIME",
]
assert contract["max_observation_age_seconds"] == 3600


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_module("runtime_adapter_attestation_validator", VALIDATOR)
HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64
HASH_D = "sha256:" + "d" * 64
CONFIG_HASH = "sha256:" + "e" * 64
AS_OF = "2026-08-15T12:00:00Z"
SHAREABLE_KINDS = ["base_model", "runtime_provider"]
PRIVATE_KINDS = [
    "policy", "action_catalog", "configuration", "session",
    "context_boundary", "private_memory_store", "vector_index", "retriever",
    "write_credential_reference", "encryption_key_reference", "system_prompt",
    "prompt_cache", "api_credential_reference", "mcp_credential_reference",
    "tool_credential_reference", "audit_stream", "kill_switch", "fallback",
    "interface",
]
AUTHORITY_FLOW = (
    "OWNER_DECIDES_CALABASH_DEFINES_LCCODING_CONSTRUCTION_IMPLEMENTS_"
    "INDEPENDENT_VERIFICATION_OWNER_ACCEPTS_AUTHORIZED_RUNTIME_ADAPTER_"
    "MECHANICALLY_LOADS"
)


def agent(applicability, agent_id):
    record = {"applicability": applicability, "agent_id": agent_id}
    for kind in SHAREABLE_KINDS:
        record[kind + "_id"] = "SHARED-" + kind
        record[kind + "_hash"] = "sha256:" + hashlib.sha256(
            ("shared:" + kind).encode("utf-8")
        ).hexdigest()
    for kind in PRIVATE_KINDS:
        record[kind + "_id"] = f"{agent_id}-{kind}"
        record[kind + "_hash"] = "sha256:" + hashlib.sha256(
            (agent_id + ":" + kind).encode("utf-8")
        ).hexdigest()
    return record


def valid_configuration(product_applicability="APPLICABLE_CORE"):
    product = agent(product_applicability, "PRODUCT-1")
    if product_applicability == "NOT_APPLICABLE":
        product = {
            key: "NOT_APPLICABLE" for key in product
        }
        product["applicability"] = "NOT_APPLICABLE"
    return {
        "schema_version": "2.8.0",
        "artifact_role": "AGENT_CONFIGURATION_BASELINE",
        "configuration_baseline_id": "ACB-1",
        "candidate_id": "CANDIDATE-1",
        "candidate_hash": HASH_B,
        "root_authority": {
            "authority_flow": AUTHORITY_FLOW,
            "root_authority_id": "ROOT-AUTH-1",
            "root_authority_hash": HASH_A,
            "scorpion_policy_id": "SCORPION-1",
            "scorpion_policy_hash": HASH_A,
            "secrets_storage": "REFERENCES_ONLY_NO_INLINE_SECRETS",
            "runtime_permission": "CANNOT_EXPAND_AUTHORITY",
        },
        "operations_agent": agent("REQUIRED", "OPS-1"),
        "product_agent": product,
        "verification": {
            "verification_id": "VERIFY-1",
            "candidate_id": "CANDIDATE-1",
            "candidate_hash": HASH_B,
            "configuration_baseline_id": "ACB-1",
            "independent_verifier_id": "VERIFIER-1",
            "evidence_id": "CONFIG-EVIDENCE-1",
            "evidence_hash": HASH_A,
            "result": "PASS",
        },
        "owner_acceptance": {
            "acceptance_id": "OWNER-ACCEPT-1",
            "owner_id": "OWNER-1",
            "candidate_id": "CANDIDATE-1",
            "candidate_hash": HASH_B,
            "configuration_baseline_id": "ACB-1",
            "verification_id": "VERIFY-1",
            "result": "OWNER_ACCEPTED",
        },
    }


def capability(role, agent_record, number):
    return {
        "agent_role": role,
        "agent_id": agent_record["agent_id"],
        "capability_id": f"CAPABILITY-{number}",
        "policy_id": agent_record["policy_id"],
        "policy_hash": agent_record["policy_hash"],
        "action_catalog_id": agent_record["action_catalog_id"],
        "action_catalog_hash": agent_record["action_catalog_hash"],
        "configuration_id": agent_record["configuration_id"],
        "configuration_hash": agent_record["configuration_hash"],
        "authorization_result": "AUTHORIZED_CONFIGURATION_BOUNDARY",
    }


def typed_events(configuration):
    if configuration["product_agent"]["applicability"] == "NOT_APPLICABLE":
        return []
    product = configuration["product_agent"]
    operations = configuration["operations_agent"]
    records = []
    for number, (kind, source, target, at_utc) in enumerate(
        (
            (
                "MAINTENANCE_REQUEST",
                product,
                operations,
                "2026-08-15T11:35:00Z",
            ),
            (
                "SERVICE_STATUS_UPDATE",
                operations,
                product,
                "2026-08-15T11:40:00Z",
            ),
        ),
        1,
    ):
        records.append(
            {
                "event_id": f"EVENT-{number}",
                "event_kind": kind,
                "event_schema_id": f"EVENT-SCHEMA-{number}",
                "event_schema_hash": "sha256:" + hashlib.sha256(
                    f"event-schema:{number}".encode("utf-8")
                ).hexdigest(),
                "source_agent_id": source["agent_id"],
                "target_agent_id": target["agent_id"],
                "candidate_id": configuration["candidate_id"],
                "candidate_hash": configuration["candidate_hash"],
                "payload_classification": "MINIMAL_NON_SENSITIVE_METADATA",
                "provenance_id": f"EVENT-PROVENANCE-{number}",
                "provenance_hash": "sha256:" + hashlib.sha256(
                    f"event-provenance:{number}".encode("utf-8")
                ).hexdigest(),
                "policy_id": source["policy_id"],
                "policy_hash": source["policy_hash"],
                "policy_result": "PASS",
                "redaction_result": "PASS",
                "event_at_utc": at_utc,
            }
        )
    return records


def failure_cases(configuration):
    states = {
        "NONE": "HEALTHY",
        "MODEL_UNAVAILABLE": "UNAVAILABLE",
        "MODEL_DRIFT": "DEGRADED",
        "RUNTIME_ADAPTER_FAILURE": "REPLACED",
        "TOOL_FAILURE": "DEGRADED",
        "AUTHORIZATION_DENIAL": "DEGRADED",
        "TELEMETRY_LOSS": "UNAVAILABLE",
        "MEMORY_ISOLATION_FAILURE": "KILLED",
        "ACTION_FAILURE": "DEGRADED",
        "ROLLBACK_FAILURE": "RECOVERING",
        "AUDIT_FAILURE": "DEGRADED",
    }
    root = configuration["root_authority"]
    operations = configuration["operations_agent"]
    product = configuration["product_agent"]
    records = []
    for index, kind in enumerate(FAILURE_KINDS, 1):
        state = states[kind]
        product_case = (
            kind == "MODEL_UNAVAILABLE"
            and product["applicability"] != "NOT_APPLICABLE"
        )
        agent_record = product if product_case else operations
        role = "PRODUCT_AGENT" if product_case else "OPERATIONS_AGENT"
        classification = "CORE" if product_case else "NOT_APPLICABLE"
        fallback_mode = (
            "NO_ACCEPTED_NON_AGENT_FALLBACK"
            if product_case else "BOUNDED_OPERATIONS_FALLBACK"
        )
        fallback_id = "NOT_APPLICABLE" if product_case else operations["fallback_id"]
        fallback_path = (
            "NOT_APPLICABLE"
            if product_case else f"evidence/failure/fallback-{index}.json"
        )
        fallback_hash = (
            "NOT_APPLICABLE" if product_case else operations["fallback_hash"]
        )
        killed = state == "KILLED"
        root_bound = state in {"RECOVERING", "REPLACED"}
        replaced = state == "REPLACED"
        identity_material = replaced or kind == "MODEL_DRIFT"
        healthy = state == "HEALTHY"
        records.append(
            {
                "failure_id": f"FAILURE-CASE-{index}",
                "failure_kind": kind,
                "lifecycle_state": state,
                "agent_role": role,
                "agent_id": agent_record["agent_id"],
                "product_classification": classification,
                "calabash_basis_id": "CALABASH-CORE-1" if product_case else "NOT_APPLICABLE",
                "calabash_basis_hash": HASH_A if product_case else "NOT_APPLICABLE",
                "candidate_id": "CANDIDATE-1",
                "candidate_hash": HASH_B,
                "configuration_baseline_id": "ACB-1",
                "configuration_baseline_hash": CONFIG_HASH,
                "production_topology_id": "TOPOLOGY-1",
                "production_topology_hash": HASH_D,
                "runtime_adapter_id": "RUNTIME-ADAPTER-1",
                "runtime_adapter_version": "1.2.3",
                "runtime_adapter_digest": HASH_C,
                "visible_impact": (
                    "NO_CURRENT_IMPACT" if healthy else
                    "VISIBLE_PRODUCT_DEGRADATION" if product_case else
                    "VISIBLE_DEGRADED_OPERATIONS"
                ),
                "core_business_continuity": (
                    "CORE_CAPABILITY_BLOCKED" if product_case else
                    "CORE_BUSINESS_CONTINUES"
                ),
                "fallback_mode": fallback_mode,
                "fallback_id": fallback_id,
                "fallback_evidence_path": fallback_path,
                "fallback_evidence_hash": fallback_hash,
                "authority_result": "OWNER_OR_CALABASH_POLICY_BOUND",
                "agent_separation_result": "DISTINCT_LOGICAL_AGENTS",
                "scorpion_result": "ENFORCED",
                "credential_currentness": "CURRENT_REFERENCES_ONLY",
                "audit_result": "APPEND_ONLY_ACTIVE",
                "proposal_action_boundary": "PROPOSAL_REQUIRES_AUTHORIZATION",
                "control_authority_id": root["root_authority_id"] if killed else "NOT_APPLICABLE",
                "control_authority_hash": root["root_authority_hash"] if killed else "NOT_APPLICABLE",
                "root_authority_id": root["root_authority_id"] if root_bound else "NOT_APPLICABLE",
                "root_authority_hash": root["root_authority_hash"] if root_bound else "NOT_APPLICABLE",
                "replacement_identity_id": "RUNTIME-ADAPTER-2" if replaced else "NOT_APPLICABLE",
                "replacement_identity_hash": HASH_D if replaced else "NOT_APPLICABLE",
                "material_identity_effect": (
                    "INVALIDATE_AFFECTED_EVIDENCE" if identity_material else
                    "NO_IDENTITY_CHANGE"
                ),
                "recovery_evidence_id": f"RECOVERY-EVIDENCE-{index}",
                "recovery_evidence_path": f"evidence/failure/recovery-{index}.json",
                "recovery_evidence_hash": HASH_A,
                "verification_evidence_id": f"VERIFICATION-EVIDENCE-{index}",
                "verification_evidence_path": f"evidence/failure/verification-{index}.json",
                "verification_evidence_hash": HASH_C,
                "audit_event_id": f"AUDIT-EVENT-{index}",
                "audit_event_path": f"evidence/failure/audit-{index}.json",
                "audit_event_hash": HASH_D,
                "alert_evidence_id": f"ALERT-EVIDENCE-{index}",
                "alert_evidence_path": f"evidence/failure/alert-{index}.json",
                "alert_evidence_hash": HASH_A,
                "affected_evidence_ids": [] if healthy else [f"AFFECTED-EVIDENCE-{index}"],
                "unaffected_core_evidence_ids": (
                    [] if product_case else [f"UNAFFECTED-CORE-{index}"]
                ),
                "evidence_currentness": (
                    "CURRENT" if healthy else "AFFECTED_EVIDENCE_INVALIDATED"
                ),
                "result": "PASS",
            }
        )
    return records


def valid_attestation(configuration):
    capabilities = [
        capability("OPERATIONS_AGENT", configuration["operations_agent"], 1),
    ]
    if configuration["product_agent"]["applicability"] != "NOT_APPLICABLE":
        capabilities.append(
            capability("PRODUCT_AGENT", configuration["product_agent"], 2)
        )
    return {
        "schema_version": "2.8.0",
        "artifact_role": "RUNTIME_ADAPTER_ATTESTATION",
        "attestation_id": "ADAPTER-ATTESTATION-1",
        "candidate_id": "CANDIDATE-1",
        "candidate_hash": HASH_B,
        "runtime_adapter": {
            "adapter_id": "RUNTIME-ADAPTER-1",
            "adapter_version": "1.2.3",
            "adapter_digest": HASH_C,
        },
        "runtime_provider": {
            "provider_id": "PROVIDER-1",
            "provider_kind": "EXTERNAL_RUNTIME",
            "identity_evidence_id": "PROVIDER-EVIDENCE-1",
            "identity_evidence_hash": HASH_D,
            "verification_result": "PASS",
        },
        "configuration_baseline": {
            "configuration_baseline_id": "ACB-1",
            "configuration_baseline_hash": CONFIG_HASH,
        },
        "production_topology": {
            "production_topology_id": "TOPOLOGY-1",
            "production_topology_hash": HASH_D,
        },
        "loaded_result": "PASS",
        "capability_attestations": capabilities,
        "authority_boundaries": {
            "runtime_permission": "CANNOT_EXPAND_AUTHORITY",
            "agent_separation": "DISTINCT_LOGICAL_AGENTS",
            "scorpion_policy_id": "SCORPION-1",
            "scorpion_policy_hash": HASH_A,
            "scorpion_result": "ENFORCED",
            "environment_fallback": "FORBIDDEN",
            "provider_authority": "NO_VENDOR_SELF_AUTHORITY",
            "secret_loading": "REFERENCES_ONLY_NO_INLINE_SECRETS",
            "isolation_evidence_id": "BOUNDARY-EVIDENCE-1",
            "isolation_evidence_hash": HASH_D,
            "private_boundary_result": "PASS",
            "shared_execution_result": "PASS",
        },
        "typed_event_attestations": typed_events(configuration),
        "failure_recovery_attestations": failure_cases(configuration),
        "validity": {
            "observed_at_utc": "2026-08-15T11:30:00Z",
            "validated_at_utc": "2026-08-15T11:45:00Z",
            "expires_at_utc": "2026-08-15T13:00:00Z",
        },
        "evidence": [
            {
                "evidence_id": "ADAPTER-EVIDENCE-1",
                "evidence_path": "evidence/runtime/adapter-load.json",
                "evidence_hash": HASH_A,
                "producer_kind": "INDEPENDENT_VERIFIER",
                "independence": "INDEPENDENT",
                "result": "PASS",
            },
            {
                "evidence_id": "BOUNDARY-EVIDENCE-1",
                "evidence_path": "evidence/runtime/authority-boundary.json",
                "evidence_hash": HASH_D,
                "producer_kind": "INDEPENDENT_VERIFIER",
                "independence": "INDEPENDENT",
                "result": "PASS",
            },
        ],
        "fallback": {
            "fallback_id": configuration["operations_agent"]["fallback_id"],
            "evidence_path": "evidence/runtime/fallback.json",
            "evidence_hash": configuration["operations_agent"]["fallback_hash"],
            "result": "PASS",
        },
        "kill_switch": {
            "kill_switch_id": configuration["operations_agent"]["kill_switch_id"],
            "evidence_path": "evidence/runtime/kill-switch.json",
            "evidence_hash": configuration["operations_agent"]["kill_switch_hash"],
            "result": "PASS",
        },
        "conformance": [
            {
                "case_id": case_id,
                "harness_id": "ADAPTER-HARNESS-1",
                "evidence_id": f"CONFORMANCE-{index}",
                "evidence_hash": HASH_A,
                "result": "PASS",
            }
            for index, case_id in enumerate(CONFORMANCE_CASES, 1)
        ],
    }


configuration = valid_configuration()
base = valid_attestation(configuration)
validate = validator.validate_runtime_adapter_attestation
assert validate(
    base, configuration, CONFIG_HASH, "TOPOLOGY-1", HASH_D, AS_OF
) == []

alternate_provider = copy.deepcopy(base)
alternate_provider["runtime_provider"]["provider_id"] = "REFERENCE-PROVIDER-2"
alternate_provider["runtime_provider"]["provider_kind"] = "REFERENCE_RUNTIME"
assert validate(
    alternate_provider, configuration, CONFIG_HASH, "TOPOLOGY-1", HASH_D, AS_OF
) == []

without_product = valid_configuration("NOT_APPLICABLE")
without_product_attestation = valid_attestation(without_product)
assert validate(
    without_product_attestation,
    without_product,
    CONFIG_HASH,
    "TOPOLOGY-1",
    HASH_D,
    AS_OF,
) == []

mutations = []
for field in base:
    changed = copy.deepcopy(base)
    changed.pop(field)
    mutations.append(changed)
changed = copy.deepcopy(base); changed["unknown"] = "x"; mutations.append(changed)

for section in (
    "runtime_adapter", "runtime_provider", "configuration_baseline",
    "production_topology", "authority_boundaries", "validity", "fallback",
    "kill_switch",
):
    changed = copy.deepcopy(base); changed[section].pop(next(iter(changed[section]))); mutations.append(changed)
    changed = copy.deepcopy(base); changed[section]["unknown"] = "x"; mutations.append(changed)
for section in (
    "capability_attestations", "typed_event_attestations",
    "failure_recovery_attestations", "evidence", "conformance",
):
    if not base[section]:
        continue
    changed = copy.deepcopy(base); changed[section][0].pop(next(iter(changed[section][0]))); mutations.append(changed)
    changed = copy.deepcopy(base); changed[section][0]["unknown"] = "x"; mutations.append(changed)

changed = copy.deepcopy(base); changed["schema_version"] = "2.7.0"; mutations.append(changed)
changed = copy.deepcopy(base); changed["attestation_id"] = "TEST-1"; mutations.append(changed)
changed = copy.deepcopy(base); changed["candidate_id"] = "CANDIDATE-2"; mutations.append(changed)
changed = copy.deepcopy(base); changed["candidate_hash"] = HASH_A; mutations.append(changed)
changed = copy.deepcopy(base); changed["runtime_adapter"]["adapter_version"] = "v1"; mutations.append(changed)
changed = copy.deepcopy(base); changed["runtime_adapter"]["adapter_digest"] = "sha256:" + "A" * 64; mutations.append(changed)
changed = copy.deepcopy(base); changed["runtime_provider"]["verification_result"] = "SELF_REPORTED"; mutations.append(changed)
changed = copy.deepcopy(base); changed["runtime_provider"]["identity_evidence_id"] = "ghp_inline_secret"; mutations.append(changed)
changed = copy.deepcopy(base); changed["runtime_provider"]["identity_evidence_id"] = "AKIAABCDEFGHIJKLMNOP"; mutations.append(changed)
changed = copy.deepcopy(base); changed["configuration_baseline"]["configuration_baseline_id"] = "ACB-2"; mutations.append(changed)
changed = copy.deepcopy(base); changed["configuration_baseline"]["configuration_baseline_hash"] = HASH_A; mutations.append(changed)
changed = copy.deepcopy(base); changed["production_topology"]["production_topology_id"] = "TOPOLOGY-2"; mutations.append(changed)
changed = copy.deepcopy(base); changed["production_topology"]["production_topology_hash"] = HASH_A; mutations.append(changed)
changed = copy.deepcopy(base); changed["loaded_result"] = True; mutations.append(changed)
changed = copy.deepcopy(base); changed["loaded_result"] = "SELF_REPORTED"; mutations.append(changed)
changed = copy.deepcopy(base); changed["capability_attestations"].pop(); mutations.append(changed)
changed = copy.deepcopy(base); changed["capability_attestations"].append(copy.deepcopy(changed["capability_attestations"][0])); mutations.append(changed)
changed = copy.deepcopy(base); changed["capability_attestations"][1]["agent_id"] = "OPS-1"; mutations.append(changed)
changed = copy.deepcopy(base); changed["capability_attestations"][0]["policy_id"] = "POLICY-OTHER"; mutations.append(changed)
changed = copy.deepcopy(base); changed["capability_attestations"][0]["action_catalog_hash"] = HASH_D; mutations.append(changed)
changed = copy.deepcopy(base); changed["capability_attestations"][0]["authorization_result"] = "AGENT_APPROVED"; mutations.append(changed)
changed = copy.deepcopy(base); changed["authority_boundaries"]["runtime_permission"] = "RUNTIME_MAY_EXPAND"; mutations.append(changed)
changed = copy.deepcopy(base); changed["authority_boundaries"]["agent_separation"] = "MERGED_AGENT"; mutations.append(changed)
changed = copy.deepcopy(base); changed["authority_boundaries"]["scorpion_result"] = "IGNORED"; mutations.append(changed)
changed = copy.deepcopy(base); changed["authority_boundaries"]["scorpion_policy_hash"] = HASH_D; mutations.append(changed)
changed = copy.deepcopy(base); changed["authority_boundaries"]["environment_fallback"] = "ALLOWED"; mutations.append(changed)
changed = copy.deepcopy(base); changed["authority_boundaries"]["provider_authority"] = "VENDOR_DECIDES"; mutations.append(changed)
changed = copy.deepcopy(base); changed["authority_boundaries"]["secret_loading"] = "INLINE_SECRET"; mutations.append(changed)
changed = copy.deepcopy(base); changed["authority_boundaries"]["isolation_evidence_id"] = "SELF-REPORT-1"; mutations.append(changed)
changed = copy.deepcopy(base); changed["authority_boundaries"]["isolation_evidence_hash"] = HASH_A; mutations.append(changed)
changed = copy.deepcopy(base); changed["authority_boundaries"]["private_boundary_result"] = "SELF_REPORTED"; mutations.append(changed)
changed = copy.deepcopy(base); changed["authority_boundaries"]["shared_execution_result"] = "PENDING"; mutations.append(changed)
changed = copy.deepcopy(base); changed["typed_event_attestations"] = changed["typed_event_attestations"][:-1]; mutations.append(changed)
changed = copy.deepcopy(base); changed["typed_event_attestations"][0]["candidate_id"] = "CANDIDATE-2"; mutations.append(changed)
changed = copy.deepcopy(base); changed["typed_event_attestations"][0]["policy_result"] = "SELF_REPORTED"; mutations.append(changed)
changed = copy.deepcopy(base); changed["typed_event_attestations"][0]["payload"] = "raw administrator authorization"; mutations.append(changed)
changed = copy.deepcopy(base); changed["validity"]["observed_at_utc"] = "2026-08-15T10:00:00Z"; mutations.append(changed)
changed = copy.deepcopy(base); changed["validity"]["observed_at_utc"] = "2026-08-15T12:01:00Z"; mutations.append(changed)
changed = copy.deepcopy(base); changed["validity"]["validated_at_utc"] = "2026-08-15T12:01:00Z"; mutations.append(changed)
changed = copy.deepcopy(base); changed["validity"]["expires_at_utc"] = "2026-08-15T11:59:59Z"; mutations.append(changed)
changed = copy.deepcopy(base); changed["validity"]["observed_at_utc"] = "2026-08-15 11:30:00"; mutations.append(changed)
changed = copy.deepcopy(base); changed["evidence"] = []; mutations.append(changed)
changed = copy.deepcopy(base); changed["evidence"][0]["evidence_id"] = "PENDING-1"; mutations.append(changed)
changed = copy.deepcopy(base); changed["evidence"][0]["evidence_path"] = "../outside.json"; mutations.append(changed)
changed = copy.deepcopy(base); changed["evidence"][0]["independence"] = "RUNTIME_SELF_REPORT"; mutations.append(changed)
changed = copy.deepcopy(base); changed["evidence"][0]["result"] = True; mutations.append(changed)
changed = copy.deepcopy(base); changed["fallback"]["result"] = "PENDING"; mutations.append(changed)
changed = copy.deepcopy(base); changed["fallback"]["fallback_id"] = "FALLBACK-OTHER"; mutations.append(changed)
changed = copy.deepcopy(base); changed["kill_switch"]["result"] = "SELF_REPORTED"; mutations.append(changed)
changed = copy.deepcopy(base); changed["kill_switch"]["kill_switch_id"] = "KILL-OTHER"; mutations.append(changed)
changed = copy.deepcopy(base); changed["conformance"] = changed["conformance"][:-1]; mutations.append(changed)
changed = copy.deepcopy(base); changed["conformance"][1]["result"] = "FAIL"; mutations.append(changed)
changed = copy.deepcopy(base); changed["conformance"][1]["case_id"] = "REFERENCE_ADAPTER_POSITIVE"; mutations.append(changed)

for changed in mutations:
    assert validate(
        changed, configuration, CONFIG_HASH, "TOPOLOGY-1", HASH_D, AS_OF
    )

merged_configuration = valid_configuration()
merged_configuration["product_agent"]["agent_id"] = "OPS-1"
assert validate(
    base, merged_configuration, CONFIG_HASH, "TOPOLOGY-1", HASH_D, AS_OF
)

template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
assert validator.validate_runtime_adapter_attestation(
    template, configuration, CONFIG_HASH, "TOPOLOGY-1", HASH_D, AS_OF
)

with tempfile.TemporaryDirectory(prefix="runtime-adapter-attestation-280-") as temporary:
    path = Path(temporary) / "RUNTIME-ADAPTER-ATTESTATION.json"
    path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    assert validator.validate_runtime_adapter_attestation_file(
        path, configuration, CONFIG_HASH, "TOPOLOGY-1", HASH_D, AS_OF
    ) == []
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before

    duplicate = path.read_text(encoding="utf-8").replace(
        '  "schema_version": "2.8.0",',
        '  "schema_version": "2.8.0",\n  "schema_version": "2.8.0",',
        1,
    )
    path.write_text(duplicate, encoding="utf-8")
    duplicate_before = (path.read_bytes(), path.stat().st_mtime_ns)
    assert validator.validate_runtime_adapter_attestation_file(
        path, configuration, CONFIG_HASH, "TOPOLOGY-1", HASH_D, AS_OF
    )
    assert (path.read_bytes(), path.stat().st_mtime_ns) == duplicate_before

    path.write_bytes(b"\xff")
    invalid_before = (path.read_bytes(), path.stat().st_mtime_ns)
    assert validator.validate_runtime_adapter_attestation_file(
        path, configuration, CONFIG_HASH, "TOPOLOGY-1", HASH_D, AS_OF
    )
    assert (path.read_bytes(), path.stat().st_mtime_ns) == invalid_before

    path.write_text(json.dumps(base) + " trailing", encoding="utf-8")
    assert validator.validate_runtime_adapter_attestation_file(
        path, configuration, CONFIG_HASH, "TOPOLOGY-1", HASH_D, AS_OF
    )
    path.write_text(
        json.dumps({**base, "loaded_result": float("nan")}), encoding="utf-8"
    )
    assert validator.validate_runtime_adapter_attestation_file(
        path, configuration, CONFIG_HASH, "TOPOLOGY-1", HASH_D, AS_OF
    )

print(
    "PASS: Runtime Adapter attestation is closed, current, runtime-neutral, and evidence-bound"
)
