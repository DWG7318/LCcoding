from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import tempfile


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "lc-coding/contracts/agent-action-catalog.json"
TEMPLATE = ROOT / "lc-coding/templates/AGENT-ACTION-CATALOG.json"
VALIDATOR = ROOT / "lc-coding/scripts/validate_agent_native.py"

assert CONTRACT.is_file(), "Agent Action Catalog contract is absent"
assert TEMPLATE.is_file(), "Agent Action Catalog template is absent"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_module("agent_action_catalog_validator", VALIDATOR)
assert hasattr(validator, "validate_action_catalog")
assert hasattr(validator, "validate_action_catalog_file")

TOP = [
    "schema_version", "artifact_role", "catalog_id", "candidate_id",
    "candidate_hash", "configuration_baseline_id", "actions",
]
ACTION = [
    "action_id", "action_version", "action_hash", "definition_authority",
    "risk", "bounded_target", "operation", "input_schema", "preconditions",
    "authority", "adapter_operation", "postconditions", "verification",
    "rollback", "audit_events", "timeout_seconds", "max_retries",
]
AUDIT_EVENTS = [
    "ACTION_PROPOSED", "AUTHORIZATION_VERIFIED", "ACTION_STARTED",
    "ACTION_RESULT_VERIFIED", "ROLLBACK_COMPLETED_OR_NOT_REQUIRED",
]
contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
assert set(contract) == {
    "schema_version", "artifact_role", "top_level_fields", "action_fields",
    "target_fields", "input_schema_fields", "condition_fields",
    "authority_fields", "adapter_operation_fields", "verification_fields",
    "rollback_fields", "authority_modes", "risk_levels", "audit_events",
    "content_hash_scope",
}
assert contract["schema_version"] == "2.8.0"
assert contract["artifact_role"] == "AGENT_ACTION_CATALOG_CONTRACT"
assert contract["top_level_fields"] == TOP
assert contract["action_fields"] == ACTION
assert contract["authority_modes"] == [
    "OWNER_APPROVAL_REQUIRED", "CALABASH_PREAUTHORIZED_BOUNDED",
]
assert contract["audit_events"] == AUDIT_EVENTS
assert contract["content_hash_scope"] == "EXACT_STRICT_UTF8_FILE_BYTES"

HASH = "sha256:" + "a" * 64
CANDIDATE_HASH = "sha256:" + "b" * 64
SHAREABLE_KINDS = tuple(validator.SHAREABLE_KINDS)
PRIVATE_KINDS = tuple(validator.PRIVATE_KINDS)


def identity_hash(label):
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def evidence(name):
    return {
        "condition_id": name,
        "evidence_schema_id": name + "-SCHEMA",
        "evidence_schema_hash": HASH,
        "result_required": "PASS",
    }


def authority(mode="OWNER_APPROVAL_REQUIRED"):
    if mode == "OWNER_APPROVAL_REQUIRED":
        return {
            "mode": mode,
            "author_kind": "OWNER",
            "item_id": "OWNER-AUTH-ITEM-1",
            "evidence_id": "OWNER-AUTH-EVIDENCE-1",
            "evidence_hash": HASH,
            "target_id": "SERVICE-1",
            "scope_id": "INSTANCE-1",
            "expires_at": "NOT_APPLICABLE",
            "result": "OWNER_APPROVED",
        }
    return {
        "mode": mode,
        "author_kind": "CALABASH",
        "item_id": "CALABASH-ITEM-1",
        "evidence_id": "CALABASH-EVIDENCE-1",
        "evidence_hash": HASH,
        "target_id": "SERVICE-1",
        "scope_id": "INSTANCE-1",
        "expires_at": "2099-01-01T00:00:00Z",
        "result": "CALABASH_PREAUTHORIZED",
    }


def action(mode="OWNER_APPROVAL_REQUIRED"):
    return {
        "action_id": "RESTART-SERVICE-1",
        "action_version": "1.0.0",
        "action_hash": HASH,
        "definition_authority": "CALABASH",
        "risk": "LOW",
        "bounded_target": {
            "target_id": "SERVICE-1",
            "target_kind": "SERVICE_INSTANCE",
            "scope_id": "INSTANCE-1",
        },
        "operation": "RESTART_SERVICE",
        "input_schema": {
            "schema_id": "RESTART-INPUT-1",
            "schema_hash": HASH,
        },
        "preconditions": [evidence("SERVICE-UNHEALTHY")],
        "authority": authority(mode),
        "adapter_operation": {
            "operation_id": "ADAPTER-RESTART-SERVICE",
            "determinism": "DETERMINISTIC",
        },
        "postconditions": [evidence("SERVICE-HEALTHY")],
        "verification": {
            "verification_id": "VERIFY-RESTART-1",
            "evidence_schema_id": "HEALTH-CHECK-SCHEMA-1",
            "evidence_schema_hash": HASH,
            "result_required": "PASS",
        },
        "rollback": {
            "operation_id": "ADAPTER-RESTORE-SERVICE",
            "trigger": "VERIFICATION_FAIL",
            "result": "AVAILABLE",
        },
        "audit_events": AUDIT_EVENTS,
        "timeout_seconds": 60,
        "max_retries": 1,
    }


def catalog(mode="OWNER_APPROVAL_REQUIRED", catalog_id="OPS-CATALOG-1"):
    return {
        "schema_version": "2.8.0",
        "artifact_role": "AGENT_ACTION_CATALOG",
        "catalog_id": catalog_id,
        "candidate_id": "CANDIDATE-1",
        "candidate_hash": CANDIDATE_HASH,
        "configuration_baseline_id": "ACB-1",
        "actions": [action(mode)],
    }


def configured_agent(applicability, agent_id, catalog_id, catalog_hash):
    record = {"applicability": applicability, "agent_id": agent_id}
    for kind in SHAREABLE_KINDS:
        record[kind + "_id"] = "SHARED-" + kind
        record[kind + "_hash"] = identity_hash("shared:" + kind)
    for kind in PRIVATE_KINDS:
        record[kind + "_id"] = catalog_id if kind == "action_catalog" else f"{agent_id}-{kind}"
        record[kind + "_hash"] = (
            catalog_hash
            if kind == "action_catalog"
            else identity_hash(agent_id + ":" + kind)
        )
    return record


def configuration(operations_catalog_id, operations_catalog_hash):
    return {
        "schema_version": "2.8.0",
        "artifact_role": "AGENT_CONFIGURATION_BASELINE",
        "configuration_baseline_id": "ACB-1",
        "candidate_id": "CANDIDATE-1",
        "candidate_hash": CANDIDATE_HASH,
        "root_authority": {
            "authority_flow": validator.CONTRACT["root_authority_flow"],
            "root_authority_id": "ROOT-AUTH-1",
            "root_authority_hash": HASH,
            "scorpion_policy_id": "SCORPION-1",
            "scorpion_policy_hash": HASH,
            "secrets_storage": "REFERENCES_ONLY_NO_INLINE_SECRETS",
            "runtime_permission": "CANNOT_EXPAND_AUTHORITY",
        },
        "operations_agent": configured_agent(
            "REQUIRED", "OPS-1", operations_catalog_id, operations_catalog_hash,
        ),
        "product_agent": configured_agent(
            "APPLICABLE_CORE", "PRODUCT-1", "PRODUCT-CATALOG-1", HASH,
        ),
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


base = catalog()
assert validator.validate_action_catalog(
    base, "OPS-CATALOG-1", "CANDIDATE-1", CANDIDATE_HASH, "ACB-1",
) == []
assert validator.validate_action_catalog(
    catalog("CALABASH_PREAUTHORIZED_BOUNDED"),
    "OPS-CATALOG-1", "CANDIDATE-1", CANDIDATE_HASH, "ACB-1",
) == []

mutations = []
for field in base:
    changed = copy.deepcopy(base); changed.pop(field); mutations.append(changed)
changed = copy.deepcopy(base); changed["unknown"] = "x"; mutations.append(changed)
for field in base["actions"][0]:
    changed = copy.deepcopy(base); changed["actions"][0].pop(field); mutations.append(changed)
changed = copy.deepcopy(base); changed["actions"][0]["unknown"] = "x"; mutations.append(changed)
changed = copy.deepcopy(base); changed["actions"].append(copy.deepcopy(changed["actions"][0])); mutations.append(changed)
changed = copy.deepcopy(base); changed["actions"] = []; mutations.append(changed)
changed = copy.deepcopy(base); changed["catalog_id"] = "TEST-1"; mutations.append(changed)
changed = copy.deepcopy(base); changed["actions"][0]["action_id"] = "TEST-1"; mutations.append(changed)
changed = copy.deepcopy(base); changed["actions"][0]["action_id"] = 123; mutations.append(changed)
changed = copy.deepcopy(base); changed["actions"][0]["action_hash"] = "sha256:" + "A" * 64; mutations.append(changed)
changed = copy.deepcopy(base); changed["candidate_id"] = "CANDIDATE-2"; mutations.append(changed)
changed = copy.deepcopy(base); changed["configuration_baseline_id"] = "ACB-2"; mutations.append(changed)
for field, value in (
    ("operation", "RUN_SHELL"),
    ("operation", "DISCOVER_TOOLS"),
    ("operation", "TOOL_DISCOVERY"),
    ("definition_authority", "OPERATIONS_AGENT"),
):
    changed = copy.deepcopy(base); changed["actions"][0][field] = value; mutations.append(changed)
changed = copy.deepcopy(base); changed["actions"][0]["adapter_operation"]["operation_id"] = "EXEC_COMMAND"; mutations.append(changed)
changed = copy.deepcopy(base); changed["actions"][0]["authority"]["author_kind"] = "OPERATIONS_AGENT"; mutations.append(changed)
changed = copy.deepcopy(base); changed["actions"][0]["authority"]["result"] = "SELF_APPROVED"; mutations.append(changed)
for section in ("bounded_target", "input_schema", "authority", "adapter_operation", "verification", "rollback"):
    changed = copy.deepcopy(base); changed["actions"][0][section].pop(next(iter(changed["actions"][0][section]))); mutations.append(changed)
    changed = copy.deepcopy(base); changed["actions"][0][section]["unknown"] = "x"; mutations.append(changed)
for section in ("preconditions", "postconditions"):
    changed = copy.deepcopy(base); changed["actions"][0][section][0].pop("condition_id"); mutations.append(changed)
    changed = copy.deepcopy(base); changed["actions"][0][section][0]["unknown"] = "x"; mutations.append(changed)
changed = copy.deepcopy(base); changed["actions"][0]["timeout_seconds"] = True; mutations.append(changed)
changed = copy.deepcopy(base); changed["actions"][0]["max_retries"] = 4; mutations.append(changed)
changed = copy.deepcopy(base); changed["actions"][0]["bounded_target"]["scope_id"] = "ALL"; changed["actions"][0]["authority"]["scope_id"] = "ALL"; mutations.append(changed)
for changed in mutations:
    assert validator.validate_action_catalog(
        changed, "OPS-CATALOG-1", "CANDIDATE-1", CANDIDATE_HASH, "ACB-1",
    )

restricted = [
    "DELETE_DATA", "CHANGE_PERMISSION", "PUBLISH_RELEASE", "UPGRADE_SERVICE",
    "DATABASE_MIGRATION", "ROTATE_CREDENTIAL", "ROOT_CONFIGURATION_CHANGE",
    "KILL_SWITCH_DISABLE", "IRREVERSIBLE_ACTION", "DATABASE_MIGRATE",
    "CHANGE_PERMISSIONS", "ROTATE_CREDENTIALS",
]
for operation in restricted:
    changed = catalog("CALABASH_PREAUTHORIZED_BOUNDED")
    changed["actions"][0]["operation"] = operation
    assert validator.validate_action_catalog(
        changed, "OPS-CATALOG-1", "CANDIDATE-1", CANDIDATE_HASH, "ACB-1",
    )
for target in ("ALL", "ANY", "GLOBAL", "*"):
    changed = catalog("CALABASH_PREAUTHORIZED_BOUNDED")
    changed["actions"][0]["bounded_target"]["scope_id"] = target
    changed["actions"][0]["authority"]["scope_id"] = target
    assert validator.validate_action_catalog(
        changed, "OPS-CATALOG-1", "CANDIDATE-1", CANDIDATE_HASH, "ACB-1",
    )
for mutation in (
    lambda item: item["authority"].pop("expires_at"),
    lambda item: item["authority"].update({"evidence_id": "PENDING"}),
    lambda item: item.update({"risk": "MEDIUM"}),
    lambda item: item["authority"].update({"target_id": "SERVICE-2"}),
    lambda item: item["rollback"].update({"result": "NOT_AVAILABLE"}),
    lambda item: item.update({"audit_events": []}),
    lambda item: item["authority"].update({"expires_at": "2020-01-01T00:00:00Z"}),
):
    changed = catalog("CALABASH_PREAUTHORIZED_BOUNDED")
    mutation(changed["actions"][0])
    assert validator.validate_action_catalog(
        changed, "OPS-CATALOG-1", "CANDIDATE-1", CANDIDATE_HASH, "ACB-1",
    )

template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
assert validator.validate_action_catalog(template)

with tempfile.TemporaryDirectory(prefix="agent-action-catalog-280-") as temporary:
    path = Path(temporary) / "AGENT-ACTION-CATALOG.json"
    path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
    file_hash = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    config = configuration("OPS-CATALOG-1", file_hash)
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    assert validator.validate_action_catalog_file(path, config, "operations_agent") == []
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before
    assert validator.validate_action_catalog_file(path, [], "operations_agent")
    changed_config = copy.deepcopy(config)
    changed_config["operations_agent"]["action_catalog_hash"] = HASH
    failed_before = (path.read_bytes(), path.stat().st_mtime_ns)
    assert validator.validate_action_catalog_file(path, changed_config, "operations_agent")
    assert (path.read_bytes(), path.stat().st_mtime_ns) == failed_before

    product = catalog(catalog_id="PRODUCT-CATALOG-1")
    path.write_text(json.dumps(product, indent=2) + "\n", encoding="utf-8")
    product_hash = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    config["product_agent"]["action_catalog_hash"] = product_hash
    assert validator.validate_action_catalog_file(path, config, "product_agent") == []
    not_applicable = copy.deepcopy(config)
    not_applicable["product_agent"] = {
        key: "NOT_APPLICABLE" for key in not_applicable["product_agent"]
    }
    assert validator.validate_action_catalog_file(path, not_applicable, "product_agent")

    duplicate = path.read_text(encoding="utf-8").replace(
        '  "catalog_id": "PRODUCT-CATALOG-1",',
        '  "catalog_id": "PRODUCT-CATALOG-1",\n  "catalog_id": "PRODUCT-CATALOG-1",',
        1,
    )
    path.write_text(duplicate, encoding="utf-8")
    assert validator.validate_action_catalog_file(path, config, "product_agent")
    path.write_bytes(b"\xff")
    assert validator.validate_action_catalog_file(path, config, "product_agent")

print("PASS: Agent Action Catalog is closed, deterministic, and authorization-bound")
