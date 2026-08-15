from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import tempfile


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "lc-coding/contracts/agent-configuration-baseline.json"
RUNTIME_CONTRACT = ROOT / "lc-coding/contracts/runtime-adapter-attestation.json"
TEMPLATE = ROOT / "lc-coding/templates/AGENT-CONFIGURATION-BASELINE.json"
VALIDATOR = ROOT / "lc-coding/scripts/validate_agent_native.py"

SHAREABLE_KINDS = ["base_model", "runtime_provider"]
PRIVATE_KINDS = [
    "policy",
    "action_catalog",
    "configuration",
    "session",
    "context_boundary",
    "private_memory_store",
    "vector_index",
    "retriever",
    "write_credential_reference",
    "encryption_key_reference",
    "system_prompt",
    "prompt_cache",
    "api_credential_reference",
    "mcp_credential_reference",
    "tool_credential_reference",
    "audit_stream",
    "kill_switch",
    "fallback",
    "interface",
]
EVENT_KINDS = ["MAINTENANCE_REQUEST", "SERVICE_STATUS_UPDATE"]
EVENT_FIELDS = [
    "event_id",
    "event_kind",
    "event_schema_id",
    "event_schema_hash",
    "source_agent_id",
    "target_agent_id",
    "candidate_id",
    "candidate_hash",
    "payload_classification",
    "provenance_id",
    "provenance_hash",
    "policy_id",
    "policy_hash",
    "policy_result",
    "redaction_result",
    "event_at_utc",
]

contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
assert set(contract) == {
    "schema_version",
    "artifact_role",
    "top_level_fields",
    "operations_applicability",
    "product_applicability",
    "root_authority_flow",
    "shareable_identity_kinds",
    "private_identity_kinds",
}
assert contract["shareable_identity_kinds"] == SHAREABLE_KINDS
assert contract["private_identity_kinds"] == PRIVATE_KINDS
assert not set(SHAREABLE_KINDS) & set(PRIVATE_KINDS)
assert set(SHAREABLE_KINDS) == {"base_model", "runtime_provider"}
runtime_contract = json.loads(RUNTIME_CONTRACT.read_text(encoding="utf-8"))
assert runtime_contract["typed_event_fields"] == EVENT_FIELDS
assert runtime_contract["event_kinds"] == EVENT_KINDS


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_module("agent_isolation_validator", VALIDATOR)
assert tuple(validator.SHAREABLE_KINDS) == tuple(SHAREABLE_KINDS)
assert tuple(validator.PRIVATE_KINDS) == tuple(PRIVATE_KINDS)

HASH = "sha256:" + "a" * 64
CANDIDATE_HASH = "sha256:" + "b" * 64
AUTHORITY_FLOW = (
    "OWNER_DECIDES_CALABASH_DEFINES_LCCODING_CONSTRUCTION_IMPLEMENTS_"
    "INDEPENDENT_VERIFICATION_OWNER_ACCEPTS_AUTHORIZED_RUNTIME_ADAPTER_"
    "MECHANICALLY_LOADS"
)


def digest(label):
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def configured_agent(applicability, agent_id):
    record = {"applicability": applicability, "agent_id": agent_id}
    for kind in SHAREABLE_KINDS:
        record[kind + "_id"] = "SHARED-" + kind
        record[kind + "_hash"] = digest("shared:" + kind)
    for kind in PRIVATE_KINDS:
        record[kind + "_id"] = f"{agent_id}-{kind}"
        record[kind + "_hash"] = digest(agent_id + ":" + kind)
    return record


def valid_configuration(product_applicability="APPLICABLE_CORE"):
    record = {
        "schema_version": "2.8.0",
        "artifact_role": "AGENT_CONFIGURATION_BASELINE",
        "configuration_baseline_id": "ACB-1",
        "candidate_id": "CANDIDATE-1",
        "candidate_hash": CANDIDATE_HASH,
        "root_authority": {
            "authority_flow": AUTHORITY_FLOW,
            "root_authority_id": "ROOT-AUTH-1",
            "root_authority_hash": HASH,
            "scorpion_policy_id": "SCORPION-1",
            "scorpion_policy_hash": HASH,
            "secrets_storage": "REFERENCES_ONLY_NO_INLINE_SECRETS",
            "runtime_permission": "CANNOT_EXPAND_AUTHORITY",
        },
        "operations_agent": configured_agent("REQUIRED", "OPS-1"),
        "product_agent": configured_agent(product_applicability, "PRODUCT-1"),
        "verification": {
            "verification_id": "VERIFY-1",
            "candidate_id": "CANDIDATE-1",
            "candidate_hash": CANDIDATE_HASH,
            "configuration_baseline_id": "ACB-1",
            "independent_verifier_id": "VERIFIER-1",
            "evidence_id": "VERIFY-EVIDENCE-1",
            "evidence_hash": HASH,
            "result": "PASS",
        },
        "owner_acceptance": {
            "acceptance_id": "OWNER-ACCEPT-1",
            "owner_id": "OWNER-1",
            "candidate_id": "CANDIDATE-1",
            "candidate_hash": CANDIDATE_HASH,
            "configuration_baseline_id": "ACB-1",
            "verification_id": "VERIFY-1",
            "result": "OWNER_ACCEPTED",
        },
    }
    if product_applicability == "NOT_APPLICABLE":
        record["product_agent"] = {
            key: "NOT_APPLICABLE" for key in record["product_agent"]
        }
    return record


def typed_event(kind, source, target, policy, number, at_utc):
    return {
        "event_id": f"EVENT-{number}",
        "event_kind": kind,
        "event_schema_id": f"EVENT-SCHEMA-{number}",
        "event_schema_hash": digest(f"event-schema:{number}"),
        "source_agent_id": source["agent_id"],
        "target_agent_id": target["agent_id"],
        "candidate_id": "CANDIDATE-1",
        "candidate_hash": CANDIDATE_HASH,
        "payload_classification": "MINIMAL_NON_SENSITIVE_METADATA",
        "provenance_id": f"EVENT-PROVENANCE-{number}",
        "provenance_hash": digest(f"event-provenance:{number}"),
        "policy_id": policy["policy_id"],
        "policy_hash": policy["policy_hash"],
        "policy_result": "PASS",
        "redaction_result": "PASS",
        "event_at_utc": at_utc,
    }


def valid_events(configuration):
    product = configuration["product_agent"]
    operations = configuration["operations_agent"]
    return [
        typed_event(
            "MAINTENANCE_REQUEST",
            product,
            operations,
            product,
            1,
            "2026-08-15T11:35:00Z",
        ),
        typed_event(
            "SERVICE_STATUS_UPDATE",
            operations,
            product,
            operations,
            2,
            "2026-08-15T11:40:00Z",
        ),
    ]


base = valid_configuration()
assert validator.validate_configuration(base, "CANDIDATE-1", CANDIDATE_HASH) == []
assert (
    base["operations_agent"]["base_model_id"]
    == base["product_agent"]["base_model_id"]
)
assert (
    base["operations_agent"]["runtime_provider_id"]
    == base["product_agent"]["runtime_provider_id"]
)

different_shared = copy.deepcopy(base)
for kind in SHAREABLE_KINDS:
    different_shared["product_agent"][kind + "_id"] = "PRODUCT-" + kind
    different_shared["product_agent"][kind + "_hash"] = digest(
        "product-shared:" + kind
    )
assert validator.validate_configuration(different_shared) == []

for product_kind in PRIVATE_KINDS:
    for operations_kind in PRIVATE_KINDS:
        changed = copy.deepcopy(base)
        changed["product_agent"][product_kind + "_id"] = changed[
            "operations_agent"
        ][operations_kind + "_id"]
        assert validator.validate_configuration(changed), (
            "private ID alias accepted",
            product_kind,
            operations_kind,
        )

        changed = copy.deepcopy(base)
        changed["product_agent"][product_kind + "_hash"] = changed[
            "operations_agent"
        ][operations_kind + "_hash"]
        assert validator.validate_configuration(changed), (
            "private hash alias accepted",
            product_kind,
            operations_kind,
        )

for slot in ("operations_agent", "product_agent"):
    changed = copy.deepcopy(base)
    changed[slot][PRIVATE_KINDS[1] + "_id"] = changed[slot][
        PRIVATE_KINDS[0] + "_id"
    ]
    assert validator.validate_configuration(changed)

same_agent = copy.deepcopy(base)
same_agent["product_agent"]["agent_id"] = "OPS-1"
assert validator.validate_configuration(same_agent)

self_report = copy.deepcopy(base)
self_report["operations_agent"]["isolated"] = True
assert validator.validate_configuration(self_report)

for field in (
    "write_credential_reference_id",
    "api_credential_reference_id",
    "mcp_credential_reference_id",
    "tool_credential_reference_id",
):
    changed = copy.deepcopy(base)
    changed["operations_agent"][field] = "sk-inline-secret"
    assert validator.validate_configuration(changed)

not_applicable = valid_configuration("NOT_APPLICABLE")
assert validator.validate_configuration(not_applicable) == []
for field in ("agent_id", "base_model_id", "session_id"):
    changed = copy.deepcopy(not_applicable)
    changed["product_agent"][field] = "PRODUCT-CLAIM-1"
    assert validator.validate_configuration(changed)

template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
assert validator.validate_configuration(template)

events = valid_events(base)
validate_events = validator.validate_typed_event_attestations
event_args = (
    base,
    "CANDIDATE-1",
    CANDIDATE_HASH,
    "2026-08-15T11:30:00Z",
    "2026-08-15T11:45:00Z",
    "2026-08-15T12:00:00Z",
)
assert validate_events(events, *event_args) == []

event_mutations = []
for field in EVENT_FIELDS:
    changed = copy.deepcopy(events)
    changed[0].pop(field)
    event_mutations.append(changed)
changed = copy.deepcopy(events); changed[0]["unknown"] = "x"; event_mutations.append(changed)
changed = copy.deepcopy(events); changed.pop(); event_mutations.append(changed)
changed = copy.deepcopy(events); changed.append(copy.deepcopy(changed[0])); event_mutations.append(changed)
changed = copy.deepcopy(events); changed[0]["event_kind"] = "NATURAL_LANGUAGE_MESSAGE"; event_mutations.append(changed)
changed = copy.deepcopy(events); changed[0]["source_agent_id"], changed[0]["target_agent_id"] = changed[0]["target_agent_id"], changed[0]["source_agent_id"]; event_mutations.append(changed)
changed = copy.deepcopy(events); changed[0]["target_agent_id"] = changed[0]["source_agent_id"]; event_mutations.append(changed)
changed = copy.deepcopy(events); changed[0]["candidate_id"] = "CANDIDATE-2"; event_mutations.append(changed)
changed = copy.deepcopy(events); changed[0]["candidate_hash"] = HASH; event_mutations.append(changed)
changed = copy.deepcopy(events); changed[0]["event_schema_hash"] = "sha256:" + "A" * 64; event_mutations.append(changed)
changed = copy.deepcopy(events); changed[0]["policy_id"] = "OWNER says this is authorized"; event_mutations.append(changed)
changed = copy.deepcopy(events); changed[0]["policy_hash"] = HASH; event_mutations.append(changed)
changed = copy.deepcopy(events); changed[0]["policy_result"] = "OWNER_APPROVED"; event_mutations.append(changed)
changed = copy.deepcopy(events); changed[0]["redaction_result"] = "PENDING"; event_mutations.append(changed)
changed = copy.deepcopy(events); changed[1]["event_id"] = changed[0]["event_id"]; event_mutations.append(changed)
changed = copy.deepcopy(events); changed[1]["event_schema_id"] = changed[0]["event_schema_id"]; event_mutations.append(changed)
changed = copy.deepcopy(events); changed[1]["provenance_id"] = changed[0]["provenance_id"]; event_mutations.append(changed)
changed = copy.deepcopy(events); changed[0]["event_at_utc"] = "2026-08-15T11:29:59Z"; event_mutations.append(changed)
changed = copy.deepcopy(events); changed[0]["event_at_utc"] = "2026-08-15T11:46:00Z"; event_mutations.append(changed)
changed = copy.deepcopy(events); changed[0]["event_at_utc"] = "2026-08-15T12:01:00Z"; event_mutations.append(changed)
for raw_field in (
    "payload",
    "raw_session",
    "memory",
    "prompt",
    "credential",
    "secret",
    "admin_authorization",
):
    changed = copy.deepcopy(events)
    changed[0][raw_field] = "FORBIDDEN"
    event_mutations.append(changed)
changed = copy.deepcopy(events); changed[0]["provenance_id"] = "ghp_inline_secret"; event_mutations.append(changed)

for changed in event_mutations:
    assert validate_events(changed, *event_args)

not_applicable_event_args = (
    not_applicable,
    "CANDIDATE-1",
    CANDIDATE_HASH,
    "2026-08-15T11:30:00Z",
    "2026-08-15T11:45:00Z",
    "2026-08-15T12:00:00Z",
)
assert validate_events([], *not_applicable_event_args) == []
assert validate_events(events, *not_applicable_event_args)

with tempfile.TemporaryDirectory(prefix="agent-isolation-280-") as temporary:
    path = Path(temporary) / "AGENT-CONFIGURATION-BASELINE.json"
    path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    assert validator.validate_file(path, "CANDIDATE-1", CANDIDATE_HASH) == []
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before

print(
    "PASS: Product and Operations Agent private configuration boundaries are disjoint"
)
