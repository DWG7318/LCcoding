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
PROJECT_VALIDATOR = ROOT / "lc-coding/scripts/validate_project.py"

assert CONTRACT.is_file(), "Agent Configuration Baseline contract is absent"
assert TEMPLATE.is_file(), "Agent Configuration Baseline template is absent"
assert VALIDATOR.is_file(), "Agent-native validator is absent"

TOP_LEVEL_FIELDS = [
    "schema_version", "artifact_role", "configuration_baseline_id",
    "candidate_id", "candidate_hash", "root_authority", "operations_agent",
    "product_agent", "verification", "owner_acceptance",
]
SHAREABLE_KINDS = ["base_model", "runtime_provider"]
PRIVATE_KINDS = [
    "policy", "action_catalog", "configuration", "session",
    "context_boundary", "private_memory_store", "vector_index", "retriever",
    "write_credential_reference", "encryption_key_reference", "system_prompt",
    "prompt_cache", "api_credential_reference", "mcp_credential_reference",
    "tool_credential_reference", "audit_stream", "kill_switch", "fallback",
    "interface",
]
IDENTITY_KINDS = SHAREABLE_KINDS + PRIVATE_KINDS
AUTHORITY_FLOW = (
    "OWNER_DECIDES_CALABASH_DEFINES_LCCODING_CONSTRUCTION_IMPLEMENTS_"
    "INDEPENDENT_VERIFICATION_OWNER_ACCEPTS_AUTHORIZED_RUNTIME_ADAPTER_"
    "MECHANICALLY_LOADS"
)
contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
assert set(contract) == {
    "schema_version", "artifact_role", "top_level_fields",
    "operations_applicability", "product_applicability",
    "root_authority_flow", "shareable_identity_kinds", "private_identity_kinds",
}
assert contract["schema_version"] == "2.8.0"
assert contract["artifact_role"] == "AGENT_CONFIGURATION_BASELINE_CONTRACT"
assert contract["top_level_fields"] == TOP_LEVEL_FIELDS
assert contract["operations_applicability"] == ["REQUIRED"]
assert contract["product_applicability"] == [
    "APPLICABLE_CORE", "APPLICABLE_EXTRA", "NOT_APPLICABLE",
]
assert contract["shareable_identity_kinds"] == SHAREABLE_KINDS
assert contract["private_identity_kinds"] == PRIVATE_KINDS
assert contract["root_authority_flow"] == AUTHORITY_FLOW


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_module("agent_native_validator", VALIDATOR)
project_validator = load_module("agent_native_project_validator", PROJECT_VALIDATOR)
HASH = "sha256:" + "a" * 64
CANDIDATE_HASH = "sha256:" + "b" * 64


def identity_hash(label):
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def agent(applicability, agent_id):
    record = {"applicability": applicability, "agent_id": agent_id}
    for name in SHAREABLE_KINDS:
        record[name + "_id"] = "SHARED-" + name
        record[name + "_hash"] = identity_hash("shared:" + name)
    for name in PRIVATE_KINDS:
        record[name + "_id"] = f"{agent_id}-{name}"
        record[name + "_hash"] = identity_hash(agent_id + ":" + name)
    return record


def valid_record():
    return {
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
        "operations_agent": agent("REQUIRED", "OPS-1"),
        "product_agent": agent("APPLICABLE_CORE", "PRODUCT-1"),
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


base = valid_record()
assert validator.validate_configuration(base, "CANDIDATE-1", CANDIDATE_HASH) == []
assert validator.validate_configuration(base, "OTHER", CANDIDATE_HASH)

mutations = []
for field in base:
    changed = copy.deepcopy(base); changed.pop(field); mutations.append(changed)
changed = copy.deepcopy(base); changed["unknown"] = "x"; mutations.append(changed)
for value in ("PENDING", "UNKNOWN", "TEST", "FAKE", "TEST-1", "PENDING_1"):
    changed = copy.deepcopy(base); changed["configuration_baseline_id"] = value; mutations.append(changed)
changed = copy.deepcopy(base); changed["configuration_baseline_id"] = 123; mutations.append(changed)
changed = copy.deepcopy(base); changed["candidate_hash"] = "sha256:" + "A" * 64; mutations.append(changed)
changed = copy.deepcopy(base); changed["operations_agent"]["applicability"] = "NOT_APPLICABLE"; mutations.append(changed)
changed = copy.deepcopy(base); changed["product_agent"]["applicability"] = "PENDING"; mutations.append(changed)
changed = copy.deepcopy(base); changed["product_agent"]["agent_id"] = "OPS-1"; mutations.append(changed)
changed = copy.deepcopy(base); changed["product_agent"]["agent_id"] = "ops-1"; mutations.append(changed)
changed = copy.deepcopy(base); changed["root_authority"]["authority_flow"] = "RUNTIME_DECIDES"; mutations.append(changed)
changed = copy.deepcopy(base); changed["verification"]["result"] = "PENDING"; mutations.append(changed)
changed = copy.deepcopy(base); changed["owner_acceptance"]["result"] = "SYSTEM_ACCEPTED"; mutations.append(changed)
changed = copy.deepcopy(base); changed["operations_agent"]["write_credential_reference_id"] = "sk-live-secret"; mutations.append(changed)
for section in ("root_authority", "operations_agent", "product_agent", "verification", "owner_acceptance"):
    changed = copy.deepcopy(base); changed[section].pop(next(iter(changed[section]))); mutations.append(changed)
    changed = copy.deepcopy(base); changed[section]["unknown"] = "x"; mutations.append(changed)
changed = copy.deepcopy(base); changed["verification"]["candidate_id"] = "CANDIDATE-2"; mutations.append(changed)
changed = copy.deepcopy(base); changed["owner_acceptance"]["candidate_hash"] = HASH; mutations.append(changed)
changed = copy.deepcopy(base); changed["verification"]["configuration_baseline_id"] = "ACB-2"; mutations.append(changed)
changed = copy.deepcopy(base); changed["verification"]["independent_verifier_id"] = "OPS-1"; mutations.append(changed)
for kind in PRIVATE_KINDS:
    changed = copy.deepcopy(base); changed["product_agent"][kind + "_id"] = changed["operations_agent"][kind + "_id"]; mutations.append(changed)
    changed = copy.deepcopy(base); changed["product_agent"][kind + "_hash"] = changed["operations_agent"][kind + "_hash"]; mutations.append(changed)
for changed in mutations:
    assert validator.validate_configuration(changed, "CANDIDATE-1", CANDIDATE_HASH)

not_applicable = valid_record()
not_applicable["product_agent"] = {
    key: ("NOT_APPLICABLE" if key != "applicability" else "NOT_APPLICABLE")
    for key in not_applicable["product_agent"]
}
assert validator.validate_configuration(not_applicable, "CANDIDATE-1", CANDIDATE_HASH) == []
applicable_extra = valid_record()
applicable_extra["product_agent"]["applicability"] = "APPLICABLE_EXTRA"
assert validator.validate_configuration(applicable_extra, "CANDIDATE-1", CANDIDATE_HASH) == []

template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
assert validator.validate_configuration(template)

with tempfile.TemporaryDirectory(prefix="agent-config-280-") as temporary:
    lc = Path(temporary) / ".lccoding"; lc.mkdir()
    path = lc / "AGENT-CONFIGURATION-BASELINE.json"
    path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    assert validator.validate_file(path, "CANDIDATE-1", CANDIDATE_HASH) == []
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before
    duplicate = path.read_text(encoding="utf-8").replace(
        '  "schema_version": "2.8.0",',
        '  "schema_version": "2.8.0",\n  "schema_version": "2.8.0",', 1,
    )
    path.write_text(duplicate, encoding="utf-8")
    duplicate_before = (path.read_bytes(), path.stat().st_mtime_ns)
    assert validator.validate_file(path)
    assert (path.read_bytes(), path.stat().st_mtime_ns) == duplicate_before

    path.write_bytes(b"\xff")
    invalid_utf8_before = (path.read_bytes(), path.stat().st_mtime_ns)
    assert validator.validate_file(path)
    assert (path.read_bytes(), path.stat().st_mtime_ns) == invalid_utf8_before

    path.write_text(json.dumps(base) + " trailing", encoding="utf-8")
    assert validator.validate_file(path)
    path.write_text(json.dumps({**base, "candidate_hash": float("nan")}), encoding="utf-8")
    assert validator.validate_file(path)

    status = {"status_schema_version": "2.8.0", "canonical_candidate": {
        "candidate_id": "CANDIDATE-1", "candidate_hash": CANDIDATE_HASH,
    }}
    path.write_text(json.dumps(base) + "\n", encoding="utf-8")
    assert project_validator.validate_agent_native_artifacts(lc, status) == []
    path.write_bytes(b"\xff")
    assert project_validator.validate_agent_native_artifacts(lc, {"status_schema_version": "2.7.0"}) == []
    path.unlink()
    assert project_validator.validate_agent_native_artifacts(lc, status) == []
    path.mkdir()
    assert project_validator.validate_agent_native_artifacts(lc, status)
    assert project_validator.validate_agent_native_artifacts(lc, {"status_schema_version": "2.7.0"}) == []
    path.rmdir()
    external = Path(temporary) / "external-agent-configuration.json"
    external.write_text(json.dumps(base) + "\n", encoding="utf-8")
    try:
        path.symlink_to(external)
    except OSError:
        pass
    else:
        assert project_validator.validate_agent_native_artifacts(lc, status)
        path.unlink()

print("PASS: Agent Configuration Baseline is closed, candidate-bound, and runtime-neutral")
