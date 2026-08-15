from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import tempfile
from datetime import datetime, timedelta, timezone


ROOT = Path(__file__).resolve().parents[2]
RULE_TEMPLATE = ROOT / "lc-coding/templates/AGENT-RULE.md"
HANDOFF_TEMPLATE = ROOT / "lc-coding/templates/PRODUCT-BASELINE-HANDOFF.md"
STATUS_TEMPLATE = ROOT / "lc-coding/templates/STATUS.json"
VALIDATOR = ROOT / "lc-coding/scripts/validate_agent_native.py"
PROJECT_VALIDATOR = ROOT / "lc-coding/scripts/validate_project.py"

RULE_FIELDS = {
    "Agent Product applicability authority": "CALABASH_DEFINITION_HANDOFF",
    "Agent Product CORE proof": "REAL_RUNNABLE_WORKFLOW_API_MCP_SIMULATION",
    "Agent Product mock/prompt/demo substitution": "FORBIDDEN",
    "Agent Construction substitution": "FORBIDDEN",
    "Agent Operations Product Formation maximum": "PREPARED_NOT_INTEGRATED",
    "Agent Operations integration / execution / Slice claim": "FORBIDDEN",
    "Agent identity alias": "FORBIDDEN",
    "Agent lifecycle effect": "NO_NEW_GATE",
}
HANDOFF_FIELDS = {
    "Agent Product Formation candidate ID / exact hash",
    "Product Agent applicability",
    "Product Agent applicability Calabash basis",
    "Agent Configuration Baseline ID / exact hash",
    "Product Agent ID",
    "Product Agent capability state",
    "Product Agent proof actor kind",
    "Product Agent Workflow Capability ID",
    "Product Agent runnable evidence",
    "Product Agent API evidence",
    "Product Agent MCP evidence",
    "Product Agent Simulation scenario/recovery evidence",
    "Product Agent Product Baseline ID / exact hash",
    "Operations Agent ID",
    "Operations Agent Product Formation state",
    "Operations Agent prepared configuration evidence",
    "Operations Agent prepared Action Catalog evidence",
    "Operations Agent telemetry evidence",
    "Operations Agent audit evidence",
    "Operations Agent fallback evidence",
    "Operations Agent Kill Switch evidence",
    "Operations Agent Runtime Adapter requirement evidence",
    "Agent Product Formation result",
}
STATUS_FIELDS = {
    "state", "product_agent_applicability",
    "calabash_definition_handoff_id", "calabash_definition_handoff_hash",
    "configuration_baseline_id", "configuration_baseline_hash",
    "product_agent_capability_state", "operations_agent_state",
}
UNPROVED_STATUS = {
    "state": "UNPROVED",
    "product_agent_applicability": "UNPROVED",
    "calabash_definition_handoff_id": "NOT_APPLICABLE",
    "calabash_definition_handoff_hash": "NOT_APPLICABLE",
    "configuration_baseline_id": "NOT_APPLICABLE",
    "configuration_baseline_hash": "NOT_APPLICABLE",
    "product_agent_capability_state": "UNPROVED",
    "operations_agent_state": "UNPROVED",
}
AGENT_SLICE_INTEGRATION_FIELDS = {
    "state", "candidate_id", "candidate_hash",
    "product_baseline_id", "product_baseline_hash",
    "configuration_baseline_id", "configuration_baseline_hash",
    "production_topology_id", "production_topology_hash",
    "runtime_adapter_attestation_id", "runtime_adapter_attestation_hash",
    "runtime_adapter_id", "runtime_adapter_version",
    "dual_agent_isolation_state", "product_agent_applicability",
    "product_integration_state", "product_agent_integration_state",
    "operations_agent_integration_state", "accepted_product_slice_ids",
    "accepted_operations_slice_ids", "required_operations_slice_id",
    "current_product_slice_reference", "product_verification_reference",
    "current_operations_slice_reference", "operations_verification_reference",
    "integration_baseline_reference",
}
UNPROVED_AGENT_SLICE_INTEGRATION = {
    "state": "UNPROVED",
    "candidate_id": "NOT_APPLICABLE",
    "candidate_hash": "NOT_APPLICABLE",
    "product_baseline_id": "NOT_APPLICABLE",
    "product_baseline_hash": "NOT_APPLICABLE",
    "configuration_baseline_id": "NOT_APPLICABLE",
    "configuration_baseline_hash": "NOT_APPLICABLE",
    "production_topology_id": "NOT_APPLICABLE",
    "production_topology_hash": "NOT_APPLICABLE",
    "runtime_adapter_attestation_id": "NOT_APPLICABLE",
    "runtime_adapter_attestation_hash": "NOT_APPLICABLE",
    "runtime_adapter_id": "NOT_APPLICABLE",
    "runtime_adapter_version": "NOT_APPLICABLE",
    "dual_agent_isolation_state": "UNPROVED",
    "product_agent_applicability": "UNPROVED",
    "product_integration_state": "UNPROVED",
    "product_agent_integration_state": "UNPROVED",
    "operations_agent_integration_state": "UNPROVED",
    "accepted_product_slice_ids": [],
    "accepted_operations_slice_ids": [],
    "required_operations_slice_id": "NOT_APPLICABLE",
    "current_product_slice_reference": "NOT_APPLICABLE",
    "product_verification_reference": "NOT_APPLICABLE",
    "current_operations_slice_reference": "NOT_APPLICABLE",
    "operations_verification_reference": "NOT_APPLICABLE",
    "integration_baseline_reference": "NOT_APPLICABLE",
}


def fields(text):
    result = {}
    for line in text.splitlines():
        if line.startswith("- ") and ":" in line:
            name, value = line[2:].split(":", 1)
            assert name not in result, f"duplicate field {name}"
            result[name] = value.strip()
    return result


def replace_field(text, name, value):
    prefix = f"- {name}:"
    matches = [line for line in text.splitlines() if line.startswith(prefix)]
    assert len(matches) == 1, (name, matches)
    return text.replace(matches[0], f"{prefix} {value}", 1)


rule_template = RULE_TEMPLATE.read_text(encoding="utf-8")
rule_fields = fields(rule_template)
assert {name: rule_fields.get(name) for name in RULE_FIELDS} == RULE_FIELDS
handoff_template = HANDOFF_TEMPLATE.read_text(encoding="utf-8")
assert HANDOFF_FIELDS <= set(fields(handoff_template))
status_template = json.loads(STATUS_TEMPLATE.read_text(encoding="utf-8"))
assert set(status_template["agent_product_formation"]) == STATUS_FIELDS
assert status_template["agent_product_formation"] == UNPROVED_STATUS
assert set(status_template["agent_slice_integration"]) == AGENT_SLICE_INTEGRATION_FIELDS
assert status_template["agent_slice_integration"] == UNPROVED_AGENT_SLICE_INTEGRATION


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_module("agent_product_formation_validator", VALIDATOR)
project_validator = load_module("agent_product_formation_project_validator", PROJECT_VALIDATOR)
assert hasattr(validator, "validate_product_formation")
assert hasattr(validator, "validate_product_formation_files")
assert hasattr(project_validator, "validate_agent_slice_status")

assert project_validator.validate_security_status_shape(status_template) == []
missing_current = copy.deepcopy(status_template)
missing_current.pop("agent_product_formation")
assert project_validator.validate_security_status_shape(missing_current)
unknown_current = copy.deepcopy(status_template)
unknown_current["unknown_status_authority"] = "PENDING"
assert project_validator.validate_security_status_shape(unknown_current)
legacy_status = copy.deepcopy(status_template)
assert legacy_status["agent_slice_integration"] == UNPROVED_AGENT_SLICE_INTEGRATION
legacy_status.pop("agent_slice_integration")
legacy_status["status_schema_version"] = "2.7.0"
legacy_status.pop("agent_product_formation")
assert project_validator.validate_security_status_shape(legacy_status) == []
hybrid_legacy = copy.deepcopy(legacy_status)
hybrid_legacy["agent_product_formation"] = copy.deepcopy(UNPROVED_STATUS)
assert project_validator.validate_security_status_shape(hybrid_legacy)
hybrid_slice_legacy = copy.deepcopy(legacy_status)
hybrid_slice_legacy["agent_slice_integration"] = copy.deepcopy(
    UNPROVED_AGENT_SLICE_INTEGRATION
)
assert project_validator.validate_security_status_shape(hybrid_slice_legacy)
missing_legacy = copy.deepcopy(legacy_status)
missing_legacy.pop("next_action")
assert project_validator.validate_security_status_shape(missing_legacy)

HASH = "sha256:" + "a" * 64
CANDIDATE_HASH = "sha256:" + "b" * 64
CALABASH_HASH = "sha256:" + "c" * 64
PRODUCT_BASELINE_HASH = "sha256:" + "d" * 64


def configured_agent(applicability, agent_id):
    record = {"applicability": applicability, "agent_id": agent_id}
    for kind in validator.SHAREABLE_KINDS:
        record[kind + "_id"] = "SHARED-" + kind
        record[kind + "_hash"] = "sha256:" + hashlib.sha256(
            ("shared:" + kind).encode("utf-8")
        ).hexdigest()
    for kind in validator.PRIVATE_KINDS:
        record[kind + "_id"] = f"{agent_id}-{kind}"
        record[kind + "_hash"] = "sha256:" + hashlib.sha256(
            (agent_id + ":" + kind).encode("utf-8")
        ).hexdigest()
    return record


def configuration(applicability):
    record = {
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
        "operations_agent": configured_agent("REQUIRED", "OPS-1"),
        "product_agent": configured_agent(applicability, "PRODUCT-1"),
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
    if applicability == "NOT_APPLICABLE":
        record["product_agent"] = {
            key: "NOT_APPLICABLE" for key in record["product_agent"]
        }
    return record


def identity(agent, kind):
    return f"{agent[kind + '_id']} / {agent[kind + '_hash']}"


def fixture(applicability):
    config = configuration(applicability)
    config_bytes = (json.dumps(config, indent=2) + "\n").encode()
    config_hash = "sha256:" + hashlib.sha256(config_bytes).hexdigest()
    handoff = handoff_template
    values = {
        "Baseline ID / version / hash": f"PB-1 / 1.0.0 / {PRODUCT_BASELINE_HASH}",
        "Calabash Definition Handoff ID / exact hash": f"CDH-1 / {CALABASH_HASH}",
        "Calabash Definition Handoff result": "PASS",
        "Handoff status": "COMPLETE",
        "Agent Product Formation candidate ID / exact hash": f"CANDIDATE-1 / {CANDIDATE_HASH}",
        "Product Agent applicability": applicability,
        "Product Agent applicability Calabash basis": f"CDH-1 / {CALABASH_HASH}",
        "Agent Configuration Baseline ID / exact hash": f"ACB-1 / {config_hash}",
        "Operations Agent ID": "OPS-1",
        "Operations Agent Product Formation state": "PREPARED_NOT_INTEGRATED",
        "Operations Agent prepared configuration evidence": identity(config["operations_agent"], "configuration"),
        "Operations Agent prepared Action Catalog evidence": identity(config["operations_agent"], "action_catalog"),
        "Operations Agent telemetry evidence": identity(config["operations_agent"], "interface"),
        "Operations Agent audit evidence": identity(config["operations_agent"], "audit_stream"),
        "Operations Agent fallback evidence": identity(config["operations_agent"], "fallback"),
        "Operations Agent Kill Switch evidence": identity(config["operations_agent"], "kill_switch"),
        "Operations Agent Runtime Adapter requirement evidence": f"RUNTIME-ADAPTER-REQ-1 / {HASH}",
        "Agent Product Formation result": "PASS",
    }
    if applicability == "APPLICABLE_CORE":
        capability_state = "REAL_RUNNABLE_CORE"
        product_values = {
            "Product Agent ID": "PRODUCT-1",
            "Product Agent capability state": capability_state,
            "Product Agent proof actor kind": "PRODUCT_AGENT",
            "Product Agent Workflow Capability ID": "CAPABILITY-1",
            "Product Agent runnable evidence": f"CAPABILITY-1 @ RUNNABLE-1 / {HASH}",
            "Product Agent API evidence": f"CAPABILITY-1 @ API-1 / {HASH}",
            "Product Agent MCP evidence": f"CAPABILITY-1 @ MCP-1 / {HASH}",
            "Product Agent Simulation scenario/recovery evidence": f"CAPABILITY-1 @ SCENARIO-1 @ RECOVERY-1 / {HASH}",
            "Product Agent Product Baseline ID / exact hash": f"PB-1 / {PRODUCT_BASELINE_HASH}",
        }
    elif applicability == "APPLICABLE_EXTRA":
        capability_state = "UNIMPLEMENTED_EXTRA"
        product_values = {
            "Product Agent ID": "PRODUCT-1",
            "Product Agent capability state": capability_state,
            "Product Agent proof actor kind": "NOT_APPLICABLE",
            "Product Agent Workflow Capability ID": "NOT_APPLICABLE",
            "Product Agent runnable evidence": "NOT_APPLICABLE",
            "Product Agent API evidence": "NOT_APPLICABLE",
            "Product Agent MCP evidence": "NOT_APPLICABLE",
            "Product Agent Simulation scenario/recovery evidence": "NOT_APPLICABLE",
            "Product Agent Product Baseline ID / exact hash": "NOT_APPLICABLE",
        }
    else:
        capability_state = "NOT_APPLICABLE"
        product_values = {
            name: "NOT_APPLICABLE" for name in (
                "Product Agent ID", "Product Agent proof actor kind",
                "Product Agent Workflow Capability ID", "Product Agent runnable evidence",
                "Product Agent API evidence", "Product Agent MCP evidence",
                "Product Agent Simulation scenario/recovery evidence",
                "Product Agent Product Baseline ID / exact hash",
            )
        }
        product_values["Product Agent capability state"] = capability_state
    values.update(product_values)
    for name, value in values.items():
        handoff = replace_field(handoff, name, value)
    status = copy.deepcopy(status_template)
    status["canonical_candidate"] = {
        "repository": "https://example.invalid/repository",
        "version": "1.0.0",
        "commit": "a" * 40,
        "candidate_id": "CANDIDATE-1",
        "candidate_hash": CANDIDATE_HASH,
    }
    status["agent_product_formation"] = {
        "state": "PRODUCT_FORMATION_AGENT_BOUND",
        "product_agent_applicability": applicability,
        "calabash_definition_handoff_id": "CDH-1",
        "calabash_definition_handoff_hash": CALABASH_HASH,
        "configuration_baseline_id": "ACB-1",
        "configuration_baseline_hash": config_hash,
        "product_agent_capability_state": capability_state,
        "operations_agent_state": "PREPARED_NOT_INTEGRATED",
    }
    return rule_template, handoff, status, config, config_hash


for classification in ("NOT_APPLICABLE", "APPLICABLE_EXTRA", "APPLICABLE_CORE"):
    values = fixture(classification)
    assert validator.validate_product_formation(*values) == [], classification

rule, handoff, status, config, config_hash = fixture("APPLICABLE_CORE")
mutations = []
changed = copy.deepcopy(status); changed["agent_product_formation"]["product_agent_applicability"] = "PENDING"; mutations.append((rule, handoff, changed, config, config_hash))
changed = copy.deepcopy(status); changed["agent_product_formation"].pop("product_agent_applicability"); mutations.append((rule, handoff, changed, config, config_hash))
changed = copy.deepcopy(status); changed["agent_product_formation"]["unknown"] = "x"; mutations.append((rule, handoff, changed, config, config_hash))
mutations.append((rule, replace_field(handoff, "Product Agent applicability Calabash basis", f"PENDING / {CALABASH_HASH}"), status, config, config_hash))
mutations.append((rule, replace_field(handoff, "Product Agent capability state", "MOCK_ONLY"), status, config, config_hash))
mutations.append((rule, replace_field(handoff, "Product Agent proof actor kind", "CONSTRUCTION_AGENT"), status, config, config_hash))
mutations.append((rule, replace_field(handoff, "Operations Agent Product Formation state", "INTEGRATED"), status, config, config_hash))
mutations.append((rule, replace_field(handoff, "Agent Product Formation candidate ID / exact hash", f"CANDIDATE-2 / {CANDIDATE_HASH}"), status, config, config_hash))
mutations.append((rule, replace_field(handoff, "Agent Configuration Baseline ID / exact hash", f"ACB-2 / {config_hash}"), status, config, config_hash))
changed = copy.deepcopy(config); changed["product_agent"]["agent_id"] = "OPS-1"; mutations.append((rule, handoff, status, changed, config_hash))
mutations.append((rule.replace("- Agent lifecycle effect: NO_NEW_GATE", "- Agent lifecycle effect: AGENT_READY_GATE"), handoff, status, config, config_hash))
mutations.append((rule, replace_field(handoff, "Product Agent API evidence", "NOT_APPLICABLE"), status, config, config_hash))
mutations.append((rule, handoff, status, [], config_hash))
construction_config = copy.deepcopy(config)
construction_config["product_agent"]["agent_id"] = "CONSTRUCTION-1"
construction_bytes = (json.dumps(construction_config, indent=2) + "\n").encode()
construction_hash = "sha256:" + hashlib.sha256(construction_bytes).hexdigest()
construction_handoff = replace_field(handoff, "Product Agent ID", "CONSTRUCTION-1")
construction_handoff = replace_field(
    construction_handoff,
    "Agent Configuration Baseline ID / exact hash",
    f"ACB-1 / {construction_hash}",
)
construction_status = copy.deepcopy(status)
construction_status["agent_product_formation"]["configuration_baseline_hash"] = construction_hash
mutations.append((
    rule, construction_handoff, construction_status,
    construction_config, construction_hash,
))
for values in mutations:
    assert validator.validate_product_formation(*values)

rule, extra_handoff, extra_status, extra_config, extra_hash = fixture("APPLICABLE_EXTRA")
assert validator.validate_product_formation(rule, extra_handoff, extra_status, extra_config, extra_hash) == []
extra_claim = replace_field(extra_handoff, "Product Agent API evidence", f"CAPABILITY-1 @ API-1 / {HASH}")
assert validator.validate_product_formation(rule, extra_claim, extra_status, extra_config, extra_hash)
rule, na_handoff, na_status, na_config, na_hash = fixture("NOT_APPLICABLE")
na_claim = replace_field(na_handoff, "Product Agent ID", "PRODUCT-1")
assert validator.validate_product_formation(rule, na_claim, na_status, na_config, na_hash)

with tempfile.TemporaryDirectory(prefix="agent-product-formation-280-") as temporary:
    root = Path(temporary)
    rule_path = root / "AGENT-RULE.md"
    handoff_path = root / "PRODUCT-BASELINE-HANDOFF.md"
    status_path = root / "status.json"
    config_path = root / "AGENT-CONFIGURATION-BASELINE.json"
    rule_path.write_text(rule, encoding="utf-8", newline="\n")
    handoff_path.write_text(handoff, encoding="utf-8", newline="\n")
    status_path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8", newline="\n")
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8", newline="\n")
    before = {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in (rule_path, handoff_path, status_path, config_path)
    }
    file_errors = validator.validate_product_formation_files(
        rule_path, handoff_path, status_path, config_path,
    )
    assert file_errors == [], file_errors
    assert before == {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in (rule_path, handoff_path, status_path, config_path)
    }
    status_path.write_text(
        status_path.read_text(encoding="utf-8").replace(
            '  "status_schema_version": "2.8.0",',
            '  "status_schema_version": "2.8.0",\n  "status_schema_version": "2.8.0",',
            1,
        ),
        encoding="utf-8",
    )
    assert validator.validate_product_formation_files(
        rule_path, handoff_path, status_path, config_path,
    )

assert project_validator.validate_agent_slice_status(Path("."), status_template) == []

slice_fixtures = load_module(
    "agent_slice_status_slice_fixtures",
    ROOT / "lc-coding/tests/test_agent_slices_280.py",
)
topology_fixtures = load_module(
    "agent_slice_status_topology_fixtures",
    ROOT / "lc-coding/tests/test_production_topology_280.py",
)
runtime_fixtures = load_module(
    "agent_slice_status_runtime_fixtures",
    ROOT / "lc-coding/tests/test_runtime_adapter_attestation_280.py",
)


def json_bytes(value):
    return (json.dumps(value, indent=2) + "\n").encode("utf-8")


def exact_file_hash(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def build_agent_slice_status_project(root, applicability="APPLICABLE_CORE"):
    lc = root / ".lccoding"
    slices = lc / "slices"
    slices.mkdir(parents=True)
    config = configuration(applicability)
    config_raw = json_bytes(config)
    config_hash = exact_file_hash(config_raw)
    (lc / "AGENT-CONFIGURATION-BASELINE.json").write_bytes(config_raw)

    topology = topology_fixtures.valid_topology("MONOLITH")
    topology["configuration_baseline"]["configuration_baseline_hash"] = config_hash
    for route in topology["routes"]:
        agent_slot = "product_agent" if route["route_kind"] == "PRODUCT" else "operations_agent"
        agent_record = config[agent_slot]
        for field in ("agent_id", "configuration_id", "configuration_hash"):
            route[field] = agent_record[field]
    topology_raw = json_bytes(topology)
    topology_hash = exact_file_hash(topology_raw)
    (lc / "PRODUCTION-EXECUTION-TOPOLOGY.json").write_bytes(topology_raw)

    attestation = runtime_fixtures.valid_attestation(config)
    attestation["configuration_baseline"]["configuration_baseline_hash"] = config_hash
    attestation["production_topology"] = {
        "production_topology_id": topology["topology_id"],
        "production_topology_hash": topology_hash,
    }
    for failure in attestation["failure_recovery_attestations"]:
        failure["candidate_id"] = attestation["candidate_id"]
        failure["candidate_hash"] = attestation["candidate_hash"]
        failure["configuration_baseline_id"] = attestation["configuration_baseline"][
            "configuration_baseline_id"
        ]
        failure["configuration_baseline_hash"] = attestation["configuration_baseline"][
            "configuration_baseline_hash"
        ]
        failure["production_topology_id"] = attestation["production_topology"][
            "production_topology_id"
        ]
        failure["production_topology_hash"] = attestation["production_topology"][
            "production_topology_hash"
        ]
        failure["runtime_adapter_id"] = attestation["runtime_adapter"]["adapter_id"]
        failure["runtime_adapter_version"] = attestation["runtime_adapter"][
            "adapter_version"
        ]
        failure["runtime_adapter_digest"] = attestation["runtime_adapter"][
            "adapter_digest"
        ]
    now = datetime.now(timezone.utc).replace(microsecond=0)
    attestation["validity"] = {
        "observed_at_utc": (now - timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "validated_at_utc": (now - timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expires_at_utc": (now + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    for index, event in enumerate(attestation["typed_event_attestations"], 1):
        event["event_at_utc"] = (now - timedelta(minutes=25 - index)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    attestation_raw = json_bytes(attestation)
    attestation_hash = exact_file_hash(attestation_raw)
    (lc / "RUNTIME-ADAPTER-ATTESTATION.json").write_bytes(attestation_raw)

    actor_kind = "UI_ACTOR" if applicability == "NOT_APPLICABLE" else None
    product = slice_fixtures.documents("PRODUCT", config, actor_kind)
    operations = slice_fixtures.documents("OPERATIONS", config)
    identities = {
        "Agent Slice Configuration Baseline identity": slice_fixtures.evidence_ref(
            "ACB-1", config_hash, "agent-configuration"
        ),
        "Agent Slice Production Topology identity": slice_fixtures.evidence_ref(
            topology["topology_id"], topology_hash, "production-topology"
        ),
        "Agent Slice Runtime Adapter Attestation identity": slice_fixtures.evidence_ref(
            attestation["attestation_id"], attestation_hash, "runtime-adapter"
        ),
    }
    for records in (product, operations):
        for record in records[:3]:
            for field, value in identities.items():
                record[field] = value
    product_texts = slice_fixtures.texts(product)
    operations_texts = slice_fixtures.texts(operations)
    assert product_texts[2].encode("utf-8") == operations_texts[2].encode("utf-8")
    paths = {
        "current_product_slice_reference": "slices/PRODUCT-FEATURE.md",
        "product_verification_reference": "slices/PRODUCT-FINAL.md",
        "current_operations_slice_reference": "slices/OPERATIONS-FEATURE.md",
        "operations_verification_reference": "slices/OPERATIONS-FINAL.md",
        "integration_baseline_reference": "INTEGRATION-BASELINE.md",
    }
    for name, text in (
        (paths["current_product_slice_reference"], product_texts[0]),
        (paths["product_verification_reference"], product_texts[1]),
        (paths["current_operations_slice_reference"], operations_texts[0]),
        (paths["operations_verification_reference"], operations_texts[1]),
        (paths["integration_baseline_reference"], product_texts[2]),
    ):
        target = lc / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")

    status = fixture(applicability)[2]
    status["product_baseline"] = "ACCEPTED"
    status["agent_slice_integration"] = {
        "state": "AGENT_SLICES_ACCEPTED",
        "candidate_id": "CANDIDATE-1",
        "candidate_hash": CANDIDATE_HASH,
        "product_baseline_id": "PRODUCT-BASELINE-1",
        "product_baseline_hash": slice_fixtures.PRODUCT_BASELINE_HASH,
        "configuration_baseline_id": "ACB-1",
        "configuration_baseline_hash": config_hash,
        "production_topology_id": topology["topology_id"],
        "production_topology_hash": topology_hash,
        "runtime_adapter_attestation_id": attestation["attestation_id"],
        "runtime_adapter_attestation_hash": attestation_hash,
        "runtime_adapter_id": attestation["runtime_adapter"]["adapter_id"],
        "runtime_adapter_version": attestation["runtime_adapter"]["adapter_version"],
        "dual_agent_isolation_state": "VERIFIED",
        "product_agent_applicability": applicability,
        "product_integration_state": "ACCEPTED",
        "product_agent_integration_state": (
            "NOT_APPLICABLE" if applicability == "NOT_APPLICABLE" else "ACCEPTED"
        ),
        "operations_agent_integration_state": "ACCEPTED",
        "accepted_product_slice_ids": ["PRODUCT-SLICE-1"],
        "accepted_operations_slice_ids": ["OPERATIONS-SLICE-1"],
        "required_operations_slice_id": "OPERATIONS-SLICE-1",
        **paths,
    }
    return lc, status


with tempfile.TemporaryDirectory(prefix="agent-slice-status-280-") as temporary:
    root = Path(temporary)
    lc, accepted_status = build_agent_slice_status_project(root / "applicable")
    assert project_validator.validate_agent_slice_status(lc, accepted_status) == []
    lc_na, na_slice_status = build_agent_slice_status_project(
        root / "not-applicable", "NOT_APPLICABLE"
    )
    assert project_validator.validate_agent_slice_status(lc_na, na_slice_status) == []

    status_mutations = []
    for field in AGENT_SLICE_INTEGRATION_FIELDS:
        changed = copy.deepcopy(accepted_status)
        changed["agent_slice_integration"].pop(field)
        status_mutations.append(changed)
    changed = copy.deepcopy(accepted_status)
    changed["agent_slice_integration"]["unknown"] = "x"
    status_mutations.append(changed)
    changed = copy.deepcopy(status_template)
    changed["agent_slice_integration"]["candidate_id"] = "CANDIDATE-1"
    status_mutations.append(changed)
    for field, value in (
        ("candidate_hash", HASH),
        ("configuration_baseline_hash", HASH),
        ("production_topology_hash", HASH),
        ("runtime_adapter_attestation_hash", HASH),
        ("product_agent_applicability", "NOT_APPLICABLE"),
        ("product_integration_state", "UNPROVED"),
        ("operations_agent_integration_state", "UNPROVED"),
    ):
        changed = copy.deepcopy(accepted_status)
        changed["agent_slice_integration"][field] = value
        status_mutations.append(changed)
    changed = copy.deepcopy(accepted_status)
    changed["agent_slice_integration"]["accepted_product_slice_ids"] = []
    status_mutations.append(changed)
    changed = copy.deepcopy(accepted_status)
    changed["agent_slice_integration"]["accepted_operations_slice_ids"] = []
    status_mutations.append(changed)
    changed = copy.deepcopy(accepted_status)
    changed["agent_slice_integration"]["accepted_product_slice_ids"] = [
        "PRODUCT-SLICE-1", "PRODUCT-SLICE-1"
    ]
    status_mutations.append(changed)
    changed = copy.deepcopy(accepted_status)
    changed["agent_slice_integration"]["accepted_operations_slice_ids"] = [
        "PRODUCT-SLICE-1"
    ]
    status_mutations.append(changed)
    changed = copy.deepcopy(accepted_status)
    changed["agent_slice_integration"]["required_operations_slice_id"] = "OPS-UNKNOWN"
    status_mutations.append(changed)
    changed = copy.deepcopy(accepted_status)
    changed["agent_slice_integration"]["current_product_slice_reference"] = (
        changed["agent_slice_integration"]["current_operations_slice_reference"]
    )
    status_mutations.append(changed)
    changed = copy.deepcopy(accepted_status)
    changed["agent_slice_integration"]["operations_verification_reference"] = "../outside.md"
    status_mutations.append(changed)
    changed = copy.deepcopy(accepted_status)
    changed["agent_slice_integration"]["operations_integration_baseline_reference"] = (
        "OTHER-INTEGRATION-BASELINE.md"
    )
    status_mutations.append(changed)
    for changed in status_mutations:
        assert project_validator.validate_agent_slice_status(lc, changed)

print("PASS: Product Formation binds exact Agent applicability without claiming Operations integration")
