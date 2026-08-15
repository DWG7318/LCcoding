from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import tempfile


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "lc-coding/contracts/production-execution-topology.json"
TEMPLATE = ROOT / "lc-coding/templates/PRODUCTION-EXECUTION-TOPOLOGY.json"
VALIDATOR = ROOT / "lc-coding/scripts/validate_agent_native.py"

assert CONTRACT.is_file(), "Production Execution Topology contract is absent"
assert TEMPLATE.is_file(), "Production Execution Topology template is absent"

TOP_LEVEL_FIELDS = [
    "schema_version",
    "artifact_role",
    "topology_id",
    "candidate_id",
    "candidate_hash",
    "product_baseline",
    "configuration_baseline",
    "discovered_members",
    "dispositions",
    "dependencies",
    "logical_authorities",
    "routes",
    "evidence",
    "verification",
]
MEMBER_FIELDS = ["member_id", "member_kind", "identity_hash"]
DISPOSITION_FIELDS = ["member_id", "disposition"]
DEPENDENCY_FIELDS = ["source_member_id", "target_member_id", "edge_kind"]
AUTHORITY_FIELDS = ["domain", "authority_member_id"]
ROUTE_FIELDS = [
    "route_kind",
    "agent_id",
    "configuration_id",
    "configuration_hash",
    "candidate_id",
    "candidate_hash",
    "calling_authority_member_id",
    "member_path",
]
EVIDENCE_FIELDS = [
    "evidence_id",
    "evidence_path",
    "evidence_hash",
    "producer_kind",
    "independence",
    "result",
]
VERIFICATION_FIELDS = [
    "verification_id",
    "candidate_id",
    "candidate_hash",
    "topology_id",
    "independent_verifier_id",
    "evidence_ids",
    "result",
]
AUTHORITY_DOMAINS = [
    "behavior",
    "state",
    "data",
    "identity",
    "permission",
    "consistency",
    "failure_recovery",
    "calling",
]
DISPOSITIONS = ["SELECT", "COMPOSE", "FEDERATE", "RETIRE"]
ROUTE_KINDS = ["PRODUCT", "OPERATIONS"]

contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
assert set(contract) == {
    "schema_version",
    "artifact_role",
    "top_level_fields",
    "product_baseline_fields",
    "configuration_fields",
    "member_fields",
    "member_kinds",
    "disposition_fields",
    "dispositions",
    "dependency_fields",
    "edge_kinds",
    "authority_fields",
    "authority_domains",
    "route_fields",
    "route_kinds",
    "evidence_fields",
    "verification_fields",
}
assert contract["schema_version"] == "2.8.0"
assert contract["artifact_role"] == "PRODUCTION_EXECUTION_TOPOLOGY_CONTRACT"
assert contract["top_level_fields"] == TOP_LEVEL_FIELDS
assert contract["product_baseline_fields"] == [
    "product_baseline_id",
    "product_baseline_hash",
]
assert contract["configuration_fields"] == [
    "configuration_baseline_id",
    "configuration_baseline_hash",
]
assert contract["member_fields"] == MEMBER_FIELDS
assert contract["member_kinds"] == ["BACKEND", "SERVICE"]
assert contract["disposition_fields"] == DISPOSITION_FIELDS
assert contract["dispositions"] == DISPOSITIONS
assert contract["dependency_fields"] == DEPENDENCY_FIELDS
assert contract["edge_kinds"] == ["CALLS", "DEPENDS_ON"]
assert contract["authority_fields"] == AUTHORITY_FIELDS
assert contract["authority_domains"] == AUTHORITY_DOMAINS
assert contract["route_fields"] == ROUTE_FIELDS
assert contract["route_kinds"] == ROUTE_KINDS
assert contract["evidence_fields"] == EVIDENCE_FIELDS
assert contract["verification_fields"] == VERIFICATION_FIELDS
assert not {"CORE", "EXTRA"} & set(contract["member_kinds"])
assert not {"CORE", "EXTRA"} & set(contract["dispositions"])


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_module("production_topology_validator", VALIDATOR)
HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64
HASH_D = "sha256:" + "d" * 64
CONFIG_HASH = "sha256:" + "e" * 64
PRODUCT_BASELINE_HASH = "sha256:" + "f" * 64
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
AUTHORITY_FLOW = (
    "OWNER_DECIDES_CALABASH_DEFINES_LCCODING_CONSTRUCTION_IMPLEMENTS_"
    "INDEPENDENT_VERIFICATION_OWNER_ACCEPTS_AUTHORIZED_RUNTIME_ADAPTER_"
    "MECHANICALLY_LOADS"
)


def digest(label):
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def agent(applicability, agent_id):
    record = {"applicability": applicability, "agent_id": agent_id}
    for kind in SHAREABLE_KINDS:
        record[kind + "_id"] = "SHARED-" + kind
        record[kind + "_hash"] = digest("shared:" + kind)
    for kind in PRIVATE_KINDS:
        record[kind + "_id"] = f"{agent_id}-{kind}"
        record[kind + "_hash"] = digest(agent_id + ":" + kind)
    return record


def valid_configuration():
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
        "product_agent": agent("APPLICABLE_CORE", "PRODUCT-1"),
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


def member(member_id, kind, number):
    return {
        "member_id": member_id,
        "member_kind": kind,
        "identity_hash": digest(f"member:{number}"),
    }


def route(kind, agent_record, path, calling_member):
    return {
        "route_kind": kind,
        "agent_id": agent_record["agent_id"],
        "configuration_id": agent_record["configuration_id"],
        "configuration_hash": agent_record["configuration_hash"],
        "candidate_id": "CANDIDATE-1",
        "candidate_hash": HASH_B,
        "calling_authority_member_id": calling_member,
        "member_path": path,
    }


def valid_topology(mode="MONOLITH"):
    configuration = valid_configuration()
    if mode == "MONOLITH":
        members = [
            member("PRIMARY-BACKEND", "BACKEND", 1),
            member("LEGACY-SERVICE", "SERVICE", 2),
        ]
        dispositions = [
            {"member_id": "PRIMARY-BACKEND", "disposition": "SELECT"},
            {"member_id": "LEGACY-SERVICE", "disposition": "RETIRE"},
        ]
        dependencies = []
        active = ["PRIMARY-BACKEND"]
    elif mode == "COMPOSED":
        members = [
            member("API-SERVICE", "SERVICE", 1),
            member("STATE-SERVICE", "SERVICE", 2),
            member("LEGACY-SERVICE", "SERVICE", 3),
        ]
        dispositions = [
            {"member_id": "API-SERVICE", "disposition": "COMPOSE"},
            {"member_id": "STATE-SERVICE", "disposition": "COMPOSE"},
            {"member_id": "LEGACY-SERVICE", "disposition": "RETIRE"},
        ]
        dependencies = [
            {
                "source_member_id": "API-SERVICE",
                "target_member_id": "STATE-SERVICE",
                "edge_kind": "CALLS",
            }
        ]
        active = ["API-SERVICE", "STATE-SERVICE"]
    else:
        members = [
            member("PRODUCT-FEDERATE", "BACKEND", 1),
            member("OPERATIONS-FEDERATE", "SERVICE", 2),
            member("LEGACY-SERVICE", "SERVICE", 3),
        ]
        dispositions = [
            {"member_id": "PRODUCT-FEDERATE", "disposition": "FEDERATE"},
            {"member_id": "OPERATIONS-FEDERATE", "disposition": "FEDERATE"},
            {"member_id": "LEGACY-SERVICE", "disposition": "RETIRE"},
        ]
        dependencies = [
            {
                "source_member_id": "PRODUCT-FEDERATE",
                "target_member_id": "OPERATIONS-FEDERATE",
                "edge_kind": "DEPENDS_ON",
            }
        ]
        active = ["PRODUCT-FEDERATE", "OPERATIONS-FEDERATE"]
    calling_member = active[0]
    authorities = [
        {
            "domain": domain,
            "authority_member_id": active[index % len(active)],
        }
        for index, domain in enumerate(AUTHORITY_DOMAINS)
    ]
    authorities[-1]["authority_member_id"] = calling_member
    member_path = list(active)
    evidence = [
        {
            "evidence_id": "TOPOLOGY-EVIDENCE-1",
            "evidence_path": "evidence/topology/member-dispositions.json",
            "evidence_hash": HASH_A,
            "producer_kind": "INDEPENDENT_VERIFIER",
            "independence": "INDEPENDENT",
            "result": "PASS",
        },
        {
            "evidence_id": "TOPOLOGY-EVIDENCE-2",
            "evidence_path": "evidence/topology/authority-routes.json",
            "evidence_hash": HASH_D,
            "producer_kind": "INDEPENDENT_VERIFIER",
            "independence": "INDEPENDENT",
            "result": "PASS",
        },
    ]
    return {
        "schema_version": "2.8.0",
        "artifact_role": "PRODUCTION_EXECUTION_TOPOLOGY",
        "topology_id": "PRODUCTION-TOPOLOGY-1",
        "candidate_id": "CANDIDATE-1",
        "candidate_hash": HASH_B,
        "product_baseline": {
            "product_baseline_id": "PRODUCT-BASELINE-1",
            "product_baseline_hash": PRODUCT_BASELINE_HASH,
        },
        "configuration_baseline": {
            "configuration_baseline_id": "ACB-1",
            "configuration_baseline_hash": CONFIG_HASH,
        },
        "discovered_members": members,
        "dispositions": dispositions,
        "dependencies": dependencies,
        "logical_authorities": authorities,
        "routes": [
            route("PRODUCT", configuration["product_agent"], member_path, calling_member),
            route(
                "OPERATIONS",
                configuration["operations_agent"],
                member_path,
                calling_member,
            ),
        ],
        "evidence": evidence,
        "verification": {
            "verification_id": "TOPOLOGY-VERIFY-1",
            "candidate_id": "CANDIDATE-1",
            "candidate_hash": HASH_B,
            "topology_id": "PRODUCTION-TOPOLOGY-1",
            "independent_verifier_id": "TOPOLOGY-VERIFIER-1",
            "evidence_ids": [item["evidence_id"] for item in evidence],
            "result": "PASS",
        },
    }


configuration = valid_configuration()
validate = validator.validate_production_topology
validate_args = (
    configuration,
    CONFIG_HASH,
    "PRODUCT-BASELINE-1",
    PRODUCT_BASELINE_HASH,
)
for mode in ("MONOLITH", "COMPOSED", "FEDERATED"):
    assert validate(valid_topology(mode), *validate_args) == [], mode

base = valid_topology("COMPOSED")
mutations = []
for field in TOP_LEVEL_FIELDS:
    changed = copy.deepcopy(base)
    changed.pop(field)
    mutations.append(changed)
changed = copy.deepcopy(base); changed["unknown"] = "x"; mutations.append(changed)

for section in (
    "product_baseline",
    "configuration_baseline",
    "verification",
):
    changed = copy.deepcopy(base); changed[section].pop(next(iter(changed[section]))); mutations.append(changed)
    changed = copy.deepcopy(base); changed[section]["unknown"] = "x"; mutations.append(changed)
for section in (
    "discovered_members",
    "dispositions",
    "dependencies",
    "logical_authorities",
    "routes",
    "evidence",
):
    changed = copy.deepcopy(base); changed[section][0].pop(next(iter(changed[section][0]))); mutations.append(changed)
    changed = copy.deepcopy(base); changed[section][0]["unknown"] = "x"; mutations.append(changed)

changed = copy.deepcopy(base); changed["schema_version"] = "2.7.0"; mutations.append(changed)
changed = copy.deepcopy(base); changed["topology_id"] = "PENDING"; mutations.append(changed)
changed = copy.deepcopy(base); changed["candidate_id"] = "CANDIDATE-2"; mutations.append(changed)
changed = copy.deepcopy(base); changed["candidate_hash"] = HASH_A; mutations.append(changed)
changed = copy.deepcopy(base); changed["product_baseline"]["product_baseline_id"] = "PRODUCT-BASELINE-2"; mutations.append(changed)
changed = copy.deepcopy(base); changed["product_baseline"]["product_baseline_hash"] = HASH_A; mutations.append(changed)
changed = copy.deepcopy(base); changed["configuration_baseline"]["configuration_baseline_id"] = "ACB-2"; mutations.append(changed)
changed = copy.deepcopy(base); changed["configuration_baseline"]["configuration_baseline_hash"] = HASH_A; mutations.append(changed)

changed = copy.deepcopy(base); changed["discovered_members"] = []; mutations.append(changed)
changed = copy.deepcopy(base); changed["discovered_members"].append(copy.deepcopy(changed["discovered_members"][0])); mutations.append(changed)
changed = copy.deepcopy(base); changed["discovered_members"][1]["member_id"] = changed["discovered_members"][0]["member_id"]; mutations.append(changed)
changed = copy.deepcopy(base); changed["discovered_members"][1]["identity_hash"] = changed["discovered_members"][0]["identity_hash"]; mutations.append(changed)
changed = copy.deepcopy(base); changed["discovered_members"][0]["member_kind"] = "CORE"; mutations.append(changed)
changed = copy.deepcopy(base); changed["discovered_members"][0]["member_id"] = "BACKEND-SECRET"; mutations.append(changed)
changed = copy.deepcopy(base); changed["dispositions"].pop(); mutations.append(changed)
changed = copy.deepcopy(base); changed["dispositions"].append({"member_id": "UNKNOWN-SERVICE", "disposition": "RETIRE"}); mutations.append(changed)
changed = copy.deepcopy(base); changed["dispositions"].append(copy.deepcopy(changed["dispositions"][0])); mutations.append(changed)
changed = copy.deepcopy(base); changed["dispositions"][0]["disposition"] = "CORE"; mutations.append(changed)
changed = copy.deepcopy(base); changed["dispositions"][0]["disposition"] = "SELECT"; mutations.append(changed)
changed = copy.deepcopy(base); changed["dispositions"][1]["disposition"] = "RETIRE"; mutations.append(changed)

changed = copy.deepcopy(base); changed["dependencies"][0]["source_member_id"] = "UNKNOWN-SERVICE"; mutations.append(changed)
changed = copy.deepcopy(base); changed["dependencies"][0]["target_member_id"] = "LEGACY-SERVICE"; mutations.append(changed)
changed = copy.deepcopy(base); changed["dependencies"][0]["target_member_id"] = changed["dependencies"][0]["source_member_id"]; mutations.append(changed)
changed = copy.deepcopy(base); changed["dependencies"][0]["edge_kind"] = "DYNAMIC_DISCOVERY"; mutations.append(changed)
changed = copy.deepcopy(base); changed["dependencies"].append(copy.deepcopy(changed["dependencies"][0])); mutations.append(changed)
changed = copy.deepcopy(base); changed["dependencies"].append({"source_member_id": "STATE-SERVICE", "target_member_id": "API-SERVICE", "edge_kind": "CALLS"}); mutations.append(changed)

changed = copy.deepcopy(base); changed["logical_authorities"].pop(); mutations.append(changed)
changed = copy.deepcopy(base); changed["logical_authorities"].append(copy.deepcopy(changed["logical_authorities"][0])); mutations.append(changed)
changed = copy.deepcopy(base); changed["logical_authorities"][0]["domain"] = "backend_core"; mutations.append(changed)
changed = copy.deepcopy(base); changed["logical_authorities"][0]["authority_member_id"] = "UNKNOWN-SERVICE"; mutations.append(changed)
changed = copy.deepcopy(base); changed["logical_authorities"][0]["authority_member_id"] = "LEGACY-SERVICE"; mutations.append(changed)

changed = copy.deepcopy(base); changed["routes"].pop(); mutations.append(changed)
changed = copy.deepcopy(base); changed["routes"].append(copy.deepcopy(changed["routes"][0])); mutations.append(changed)
changed = copy.deepcopy(base); changed["routes"][0]["route_kind"] = "ADMIN"; mutations.append(changed)
changed = copy.deepcopy(base); changed["routes"][0]["agent_id"] = "OPS-1"; mutations.append(changed)
changed = copy.deepcopy(base); changed["routes"][0]["candidate_id"] = "CANDIDATE-2"; mutations.append(changed)
changed = copy.deepcopy(base); changed["routes"][0]["configuration_hash"] = HASH_A; mutations.append(changed)
changed = copy.deepcopy(base); changed["routes"][0]["calling_authority_member_id"] = "STATE-SERVICE"; mutations.append(changed)
changed = copy.deepcopy(base); changed["routes"][0]["member_path"] = ["LEGACY-SERVICE"]; mutations.append(changed)
changed = copy.deepcopy(base); changed["routes"][0]["member_path"] = ["UNKNOWN-SERVICE"]; mutations.append(changed)
changed = copy.deepcopy(base); changed["routes"][0]["member_path"] = ["STATE-SERVICE", "API-SERVICE"]; mutations.append(changed)

changed = copy.deepcopy(base); changed["evidence"] = []; changed["verification"]["evidence_ids"] = []; mutations.append(changed)
changed = copy.deepcopy(base); changed["evidence"][0]["evidence_id"] = "PENDING"; mutations.append(changed)
changed = copy.deepcopy(base); changed["evidence"][0].pop("evidence_path"); mutations.append(changed)
changed = copy.deepcopy(base); changed["evidence"][0]["evidence_path"] = "../outside.json"; mutations.append(changed)
changed = copy.deepcopy(base); changed["evidence"][0]["identity_hash"] = HASH_A; mutations.append(changed)
changed = copy.deepcopy(base); changed["evidence"][0]["producer_kind"] = "RUNTIME_SELF_REPORT"; mutations.append(changed)
changed = copy.deepcopy(base); changed["evidence"][0]["result"] = "SELF_REPORTED"; mutations.append(changed)
changed = copy.deepcopy(base); changed["verification"]["candidate_id"] = "CANDIDATE-2"; mutations.append(changed)
changed = copy.deepcopy(base); changed["verification"]["topology_id"] = "TOPOLOGY-OTHER"; mutations.append(changed)
changed = copy.deepcopy(base); changed["verification"]["evidence_ids"] = changed["verification"]["evidence_ids"][:-1]; mutations.append(changed)
changed = copy.deepcopy(base); changed["verification"]["result"] = "SELF_REPORTED"; mutations.append(changed)

for changed in mutations:
    assert validate(changed, *validate_args)

same_agent_configuration = valid_configuration()
same_agent_configuration["product_agent"]["agent_id"] = "OPS-1"
assert validate(base, same_agent_configuration, *validate_args[1:])

template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
assert validate(template, *validate_args)

with tempfile.TemporaryDirectory(prefix="production-topology-280-") as temporary:
    path = Path(temporary) / "PRODUCTION-EXECUTION-TOPOLOGY.json"
    path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    assert validator.validate_production_topology_file(path, *validate_args) == []
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before

    duplicate = path.read_text(encoding="utf-8").replace(
        '  "schema_version": "2.8.0",',
        '  "schema_version": "2.8.0",\n  "schema_version": "2.8.0",',
        1,
    )
    path.write_text(duplicate, encoding="utf-8")
    duplicate_before = (path.read_bytes(), path.stat().st_mtime_ns)
    assert validator.validate_production_topology_file(path, *validate_args)
    assert (path.read_bytes(), path.stat().st_mtime_ns) == duplicate_before

    path.write_bytes(b"\xff")
    invalid_before = (path.read_bytes(), path.stat().st_mtime_ns)
    assert validator.validate_production_topology_file(path, *validate_args)
    assert (path.read_bytes(), path.stat().st_mtime_ns) == invalid_before

print(
    "PASS: Production execution topology is exhaustive, acyclic, authority-bound, and architecture-neutral"
)
