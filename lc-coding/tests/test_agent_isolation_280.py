from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import tempfile


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "lc-coding/contracts/agent-configuration-baseline.json"
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

with tempfile.TemporaryDirectory(prefix="agent-isolation-280-") as temporary:
    path = Path(temporary) / "AGENT-CONFIGURATION-BASELINE.json"
    path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    assert validator.validate_file(path, "CANDIDATE-1", CANDIDATE_HASH) == []
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before

print(
    "PASS: Product and Operations Agent private configuration boundaries are disjoint"
)
