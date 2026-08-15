from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import tempfile


ROOT = Path(__file__).resolve().parents[2]
FEATURE_TEMPLATE = ROOT / "lc-coding/templates/FEATURE-SLICE.md"
FINAL_TEMPLATE = ROOT / "lc-coding/templates/FINAL-FEATURE-VERIFICATION.md"
BASELINE_TEMPLATE = ROOT / "lc-coding/templates/INTEGRATION-BASELINE.md"
VALIDATOR = ROOT / "lc-coding/scripts/validate_agent_native.py"

COMMON_FIELDS = [
    "Agent Slice schema version",
    "Agent Slice ID",
    "Agent Slice class",
    "Agent Slice route ID",
    "Agent Slice candidate ID / exact hash",
    "Agent Slice Product Baseline identity",
    "Agent Slice Configuration Baseline identity",
    "Agent Slice Production Topology identity",
    "Agent Slice Runtime Adapter Attestation identity",
    "Agent Slice Impact Analysis identity",
    "Agent Slice route proof identity",
    "Agent Slice D0-D3 verification evidence",
    "Agent Slice Owner acceptance evidence",
    "Agent Slice evidence currentness",
    "Agent Slice Product Agent applicability",
    "Agent Slice actor kind",
    "Agent Slice actor ID",
]
PRODUCT_FIELDS = [
    "Agent Slice Product Workflow capability ID",
    "Agent Slice Product API capability ID",
    "Agent Slice Product MCP capability ID",
    "Agent Slice Product governed integration boundary evidence",
    "Agent Slice Product API-backed Workflow evidence",
    "Agent Slice Product MCP-backed Workflow evidence",
    "Agent Slice Product real state/data/side-effect evidence",
    "Agent Slice Product visible actor result evidence",
    "Agent Slice Product Simulation exception/recovery evidence",
]
OPERATIONS_FIELDS = [
    "Agent Slice Operations telemetry/log/typed event evidence",
    "Agent Slice Operations deterministic action ID",
    "Agent Slice Operations Policy authorization evidence",
    "Agent Slice Operations authorization mode",
    "Agent Slice Operations authorization actor ID",
    "Agent Slice Operations deterministic catalog action evidence",
    "Agent Slice Operations postcondition verification evidence",
    "Agent Slice Operations rollback/fallback evidence",
    "Agent Slice Operations append-only audit evidence",
    "Agent Slice Operations visible status evidence",
]
FINAL_FIELDS = [
    "Agent Slice Verification route evidence kind",
    "Agent Slice Verification class isolation",
    "Agent Slice Verification result",
]
BASELINE_FIELDS = [
    "Agent Slice Baseline accepted class set",
    "Agent Slice Baseline accepted PRODUCT Slice IDs",
    "Agent Slice Baseline accepted OPERATIONS Slice IDs",
    "Agent Slice Baseline required Operations Slice ID",
    "Agent Slice Baseline required Operations acceptance evidence",
    "Agent Slice Baseline Product Agent Slice ID",
    "Agent Slice Baseline Product Agent acceptance evidence",
    "Agent Slice Baseline class isolation",
    "Agent Slice Baseline result",
]
BASELINE_CANDIDATE_FIELDS = [
    "Agent Slice schema version",
    "Agent Slice candidate ID / exact hash",
    "Agent Slice Product Baseline identity",
    "Agent Slice Configuration Baseline identity",
    "Agent Slice Production Topology identity",
    "Agent Slice Runtime Adapter Attestation identity",
    "Agent Slice Impact Analysis identity",
    "Agent Slice evidence currentness",
    "Agent Slice Product Agent applicability",
]
BASELINE_FORBIDDEN_SLICE_FIELDS = {
    "Agent Slice ID",
    "Agent Slice class",
    "Agent Slice route ID",
    "Agent Slice route proof identity",
    "Agent Slice D0-D3 verification evidence",
    "Agent Slice Owner acceptance evidence",
    "Agent Slice actor kind",
    "Agent Slice actor ID",
}


def markdown_fields(text):
    fields = {}
    for line in text.splitlines():
        if line.startswith("- ") and ":" in line:
            name, value = line[2:].split(":", 1)
            assert name not in fields
            fields[name] = value.strip()
    return fields


feature_template_fields = markdown_fields(FEATURE_TEMPLATE.read_text(encoding="utf-8"))
final_template_fields = markdown_fields(FINAL_TEMPLATE.read_text(encoding="utf-8"))
baseline_template_fields = markdown_fields(BASELINE_TEMPLATE.read_text(encoding="utf-8"))
assert {key for key in feature_template_fields if key.startswith("Agent Slice ")} == set(
    COMMON_FIELDS + PRODUCT_FIELDS + OPERATIONS_FIELDS
)
assert {key for key in final_template_fields if key.startswith("Agent Slice ")} == set(
    COMMON_FIELDS + FINAL_FIELDS
)
assert {key for key in baseline_template_fields if key.startswith("Agent Slice ")} == set(
    BASELINE_CANDIDATE_FIELDS + BASELINE_FIELDS
)
assert not BASELINE_FORBIDDEN_SLICE_FIELDS & set(baseline_template_fields)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_module("agent_slice_validator", VALIDATOR)
HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64
HASH_D = "sha256:" + "d" * 64
CONFIG_HASH = "sha256:" + "e" * 64
PRODUCT_BASELINE_HASH = "sha256:" + "f" * 64
TOPOLOGY_HASH = "sha256:" + "1" * 64
ADAPTER_HASH = "sha256:" + "2" * 64
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


def valid_configuration(product_applicability="APPLICABLE_CORE"):
    product = agent(product_applicability, "PRODUCT-1")
    if product_applicability == "NOT_APPLICABLE":
        product = {key: "NOT_APPLICABLE" for key in product}
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


def evidence_ref(identity, exact_hash, name):
    return f"{identity} / {exact_hash} / evidence/slices/{name}.json"


def markdown_record(title, fields):
    return "# " + title + "\n\n" + "\n".join(
        f"- {key}: {value}" for key, value in fields.items()
    ) + "\n"


def common_fields(slice_class, configuration, actor_kind=None):
    slice_id = "PRODUCT-SLICE-1" if slice_class == "PRODUCT" else "OPERATIONS-SLICE-1"
    actor_kind = actor_kind or ("PRODUCT_AGENT" if slice_class == "PRODUCT" else "OPERATIONS_AGENT")
    if actor_kind == "PRODUCT_AGENT":
        actor_id = configuration["product_agent"]["agent_id"]
    elif actor_kind == "OPERATIONS_AGENT":
        actor_id = configuration["operations_agent"]["agent_id"]
    else:
        actor_id = "UI-ACTOR-1"
    return {
        "Agent Slice schema version": "2.8.0",
        "Agent Slice ID": slice_id,
        "Agent Slice class": slice_class,
        "Agent Slice route ID": slice_id + "-ROUTE",
        "Agent Slice candidate ID / exact hash": "CANDIDATE-1 / " + HASH_B,
        "Agent Slice Product Baseline identity": evidence_ref(
            "PRODUCT-BASELINE-1", PRODUCT_BASELINE_HASH, "product-baseline"
        ),
        "Agent Slice Configuration Baseline identity": evidence_ref(
            "ACB-1", CONFIG_HASH, "agent-configuration"
        ),
        "Agent Slice Production Topology identity": evidence_ref(
            "PRODUCTION-TOPOLOGY-1", TOPOLOGY_HASH, "production-topology"
        ),
        "Agent Slice Runtime Adapter Attestation identity": evidence_ref(
            "ADAPTER-ATTESTATION-1", ADAPTER_HASH, "runtime-adapter"
        ),
        "Agent Slice Impact Analysis identity": evidence_ref(
            "IMPACT-1", HASH_A, "impact-analysis"
        ),
        "Agent Slice route proof identity": evidence_ref(
            slice_id + "-PROOF", HASH_C, slice_id.lower() + "-route-proof"
        ),
        "Agent Slice D0-D3 verification evidence": evidence_ref(
            slice_id + "-D0-D3", HASH_D, slice_id.lower() + "-d0-d3"
        ),
        "Agent Slice Owner acceptance evidence": evidence_ref(
            slice_id + "-OWNER", HASH_A, slice_id.lower() + "-owner"
        ),
        "Agent Slice evidence currentness": "UNCHANGED_CURRENT",
        "Agent Slice Product Agent applicability": configuration["product_agent"][
            "applicability"
        ],
        "Agent Slice actor kind": actor_kind,
        "Agent Slice actor ID": actor_id,
    }


def feature_fields(slice_class, configuration, actor_kind=None):
    fields = common_fields(slice_class, configuration, actor_kind)
    fields.update({key: "NOT_APPLICABLE" for key in PRODUCT_FIELDS + OPERATIONS_FIELDS})
    if slice_class == "PRODUCT":
        capability = "WORKFLOW-CAPABILITY-1"
        fields.update(
            {
                "Agent Slice Product Workflow capability ID": capability,
                "Agent Slice Product API capability ID": capability,
                "Agent Slice Product MCP capability ID": capability,
                "Agent Slice Product governed integration boundary evidence": evidence_ref(
                    "PRODUCT-BOUNDARY-1", HASH_A, "product-boundary"
                ),
                "Agent Slice Product API-backed Workflow evidence": evidence_ref(
                    "PRODUCT-API-1", HASH_C, "product-api"
                ),
                "Agent Slice Product MCP-backed Workflow evidence": evidence_ref(
                    "PRODUCT-MCP-1", HASH_D, "product-mcp"
                ),
                "Agent Slice Product real state/data/side-effect evidence": evidence_ref(
                    "PRODUCT-STATE-1", HASH_A, "product-state-effect"
                ),
                "Agent Slice Product visible actor result evidence": evidence_ref(
                    "PRODUCT-VISIBLE-1", HASH_C, "product-visible-result"
                ),
                "Agent Slice Product Simulation exception/recovery evidence": evidence_ref(
                    "PRODUCT-SIMULATION-1", HASH_D, "product-simulation-recovery"
                ),
            }
        )
    else:
        operations = configuration["operations_agent"]
        fields.update(
            {
                "Agent Slice Operations telemetry/log/typed event evidence": evidence_ref(
                    "OPS-TELEMETRY-1", HASH_A, "operations-telemetry"
                ),
                "Agent Slice Operations deterministic action ID": "MAINTENANCE-ACTION-1",
                "Agent Slice Operations Policy authorization evidence": evidence_ref(
                    operations["policy_id"], operations["policy_hash"], "operations-policy"
                ),
                "Agent Slice Operations authorization mode": "OWNER_APPROVAL_REQUIRED",
                "Agent Slice Operations authorization actor ID": "OWNER-1",
                "Agent Slice Operations deterministic catalog action evidence": evidence_ref(
                    operations["action_catalog_id"],
                    operations["action_catalog_hash"],
                    "operations-action-catalog",
                ),
                "Agent Slice Operations postcondition verification evidence": evidence_ref(
                    "OPS-POSTCONDITION-1", HASH_C, "operations-postcondition"
                ),
                "Agent Slice Operations rollback/fallback evidence": evidence_ref(
                    operations["fallback_id"], operations["fallback_hash"], "operations-fallback"
                ),
                "Agent Slice Operations append-only audit evidence": evidence_ref(
                    operations["audit_stream_id"],
                    operations["audit_stream_hash"],
                    "operations-audit",
                ),
                "Agent Slice Operations visible status evidence": evidence_ref(
                    "OPS-VISIBLE-STATUS-1", HASH_D, "operations-visible-status"
                ),
            }
        )
    return fields


def final_fields(feature):
    fields = {key: feature[key] for key in COMMON_FIELDS}
    route_kind = (
        "PRODUCT_ROUTE_PROOF"
        if feature["Agent Slice class"] == "PRODUCT"
        else "OPERATIONS_ROUTE_PROOF"
    )
    fields.update(
        {
            "Agent Slice Verification route evidence kind": route_kind,
            "Agent Slice Verification class isolation": "NO_CROSS_CLASS_EVIDENCE",
            "Agent Slice Verification result": "PASS",
        }
    )
    return fields


def baseline_fields(product_feature, operations_feature, configuration):
    fields = {key: product_feature[key] for key in BASELINE_CANDIDATE_FIELDS}
    product_ids = [product_feature["Agent Slice ID"]]
    operations_ids = [operations_feature["Agent Slice ID"]]
    product_applicability = configuration["product_agent"]["applicability"]
    if product_applicability == "NOT_APPLICABLE":
        product_agent_slice = "NOT_APPLICABLE"
        product_agent_evidence = "NOT_APPLICABLE"
    else:
        if product_feature["Agent Slice actor kind"] == "PRODUCT_AGENT":
            product_agent_slice = product_feature["Agent Slice ID"]
        else:
            product_agent_slice = "PRODUCT-AGENT-SLICE-OTHER"
            product_ids.append(product_agent_slice)
        product_agent_evidence = evidence_ref(
            "PRODUCT-AGENT-ACCEPT-1", HASH_C, "product-agent-acceptance"
        )
    fields.update(
        {
            "Agent Slice Baseline accepted class set": "PRODUCT|OPERATIONS",
            "Agent Slice Baseline accepted PRODUCT Slice IDs": ",".join(product_ids),
            "Agent Slice Baseline accepted OPERATIONS Slice IDs": ",".join(operations_ids),
            "Agent Slice Baseline required Operations Slice ID": operations_ids[0],
            "Agent Slice Baseline required Operations acceptance evidence": evidence_ref(
                "OPS-ACCEPT-1", HASH_D, "operations-slice-acceptance"
            ),
            "Agent Slice Baseline Product Agent Slice ID": product_agent_slice,
            "Agent Slice Baseline Product Agent acceptance evidence": product_agent_evidence,
            "Agent Slice Baseline class isolation": "TWO_BOUND_SLICES_NO_MIXED_ROUTE",
            "Agent Slice Baseline result": "PASS",
        }
    )
    return fields


def documents(slice_class, configuration=None, actor_kind=None):
    configuration = configuration or valid_configuration()
    product_actor = actor_kind if slice_class == "PRODUCT" else None
    operations_actor = actor_kind if slice_class == "OPERATIONS" else None
    product_feature = feature_fields("PRODUCT", configuration, product_actor)
    operations_feature = feature_fields("OPERATIONS", configuration, operations_actor)
    feature = product_feature if slice_class == "PRODUCT" else operations_feature
    final = final_fields(feature)
    baseline = baseline_fields(product_feature, operations_feature, configuration)
    return feature, final, baseline, configuration


def texts(records):
    feature, final, baseline, _ = records
    return (
        markdown_record("Feature Slice", feature),
        markdown_record("Final Feature Verification", final),
        markdown_record("Integration Baseline", baseline),
    )


def validate_records(records):
    feature, final, baseline, configuration = records
    return validator.validate_agent_slice(
        *texts(records),
        configuration,
        CONFIG_HASH,
        "PRODUCT-BASELINE-1",
        PRODUCT_BASELINE_HASH,
        "PRODUCTION-TOPOLOGY-1",
        TOPOLOGY_HASH,
        "ADAPTER-ATTESTATION-1",
        ADAPTER_HASH,
    )


product = documents("PRODUCT")
operations = documents("OPERATIONS")
not_applicable = documents("PRODUCT", valid_configuration("NOT_APPLICABLE"), "UI_ACTOR")
assert texts(product)[2].encode("utf-8") == texts(operations)[2].encode("utf-8")
assert validate_records(product) == []
assert validate_records(operations) == []
assert validate_records(not_applicable) == []

mutations = []
for index, allowed_fields in enumerate(
    (
        COMMON_FIELDS + PRODUCT_FIELDS + OPERATIONS_FIELDS,
        COMMON_FIELDS + FINAL_FIELDS,
        BASELINE_CANDIDATE_FIELDS + BASELINE_FIELDS,
    )
):
    for field in allowed_fields:
        changed = copy.deepcopy(product)
        changed[index].pop(field)
        mutations.append(changed)
    changed = copy.deepcopy(product)
    changed[index]["Agent Slice unknown field"] = "x"
    mutations.append(changed)

changed = copy.deepcopy(product); changed[0]["Agent Slice class"] = "MIXED"; mutations.append(changed)
changed = copy.deepcopy(product); changed[0]["Agent Slice class"] = "UNKNOWN"; mutations.append(changed)
changed = copy.deepcopy(product); changed[0]["Agent Slice candidate ID / exact hash"] = "CANDIDATE-2 / " + HASH_B; mutations.append(changed)
changed = copy.deepcopy(product); changed[0]["Agent Slice candidate ID / exact hash"] = "CANDIDATE-1 / " + HASH_A; mutations.append(changed)
changed = copy.deepcopy(product); changed[0]["Agent Slice Product Baseline identity"] = evidence_ref("PRODUCT-BASELINE-1", HASH_A, "product-baseline"); mutations.append(changed)
changed = copy.deepcopy(product); changed[0]["Agent Slice Configuration Baseline identity"] = evidence_ref("ACB-2", CONFIG_HASH, "agent-configuration"); mutations.append(changed)
changed = copy.deepcopy(product); changed[0]["Agent Slice Configuration Baseline identity"] = evidence_ref("ACB-1", HASH_A, "agent-configuration"); mutations.append(changed)
changed = copy.deepcopy(product); changed[0]["Agent Slice Production Topology identity"] = evidence_ref("PRODUCTION-TOPOLOGY-2", TOPOLOGY_HASH, "production-topology"); mutations.append(changed)
changed = copy.deepcopy(product); changed[0]["Agent Slice Production Topology identity"] = evidence_ref("PRODUCTION-TOPOLOGY-1", HASH_A, "production-topology"); mutations.append(changed)
changed = copy.deepcopy(product); changed[0]["Agent Slice Runtime Adapter Attestation identity"] = evidence_ref("ADAPTER-ATTESTATION-2", ADAPTER_HASH, "runtime-adapter"); mutations.append(changed)
changed = copy.deepcopy(product); changed[0]["Agent Slice Runtime Adapter Attestation identity"] = evidence_ref("ADAPTER-ATTESTATION-1", HASH_A, "runtime-adapter"); mutations.append(changed)
changed = copy.deepcopy(product); changed[0]["Agent Slice Runtime Adapter Attestation identity"] = evidence_ref("STALE-ADAPTER-ATTESTATION", ADAPTER_HASH, "runtime-adapter"); mutations.append(changed)
changed = copy.deepcopy(product); changed[0]["Agent Slice Impact Analysis identity"] = "IMPACT-1"; mutations.append(changed)
changed = copy.deepcopy(product); changed[0]["Agent Slice Impact Analysis identity"] = evidence_ref("IMPACT-1", HASH_A, "../outside"); mutations.append(changed)
changed = copy.deepcopy(product); changed[0]["Agent Slice evidence currentness"] = "CHANGED_REUSED"; mutations.append(changed)
changed = copy.deepcopy(product); changed[0]["Agent Slice actor kind"] = "CONSTRUCTION_AGENT"; mutations.append(changed)
changed = copy.deepcopy(product); changed[0]["Agent Slice Product API capability ID"] = "OTHER-CAPABILITY"; mutations.append(changed)
changed = copy.deepcopy(product); changed[0]["Agent Slice Product API-backed Workflow evidence"] = evidence_ref("MOCK-PROOF-1", HASH_A, "mock-proof"); mutations.append(changed)
changed = copy.deepcopy(product); changed[0]["Agent Slice Product visible actor result evidence"] = changed[0]["Agent Slice Product API-backed Workflow evidence"]; mutations.append(changed)
changed = copy.deepcopy(product); changed[0][OPERATIONS_FIELDS[0]] = evidence_ref("OPS-CLAIM-1", HASH_A, "ops-claim"); mutations.append(changed)

changed = copy.deepcopy(not_applicable); changed[0]["Agent Slice actor kind"] = "PRODUCT_AGENT"; changed[0]["Agent Slice actor ID"] = "PRODUCT-1"; mutations.append(changed)

changed = copy.deepcopy(operations); changed[0]["Agent Slice Operations deterministic action ID"] = "FREE-FORM-SHELL-COMMAND"; mutations.append(changed)
changed = copy.deepcopy(operations); changed[0]["Agent Slice Operations authorization actor ID"] = "OPS-1"; mutations.append(changed)
changed = copy.deepcopy(operations); changed[0]["Agent Slice Operations Policy authorization evidence"] = evidence_ref("POLICY-OTHER", HASH_A, "operations-policy"); mutations.append(changed)
changed = copy.deepcopy(operations); changed[0]["Agent Slice Operations rollback/fallback evidence"] = "NOT_APPLICABLE"; mutations.append(changed)
changed = copy.deepcopy(operations); changed[0]["Agent Slice Operations append-only audit evidence"] = "NOT_APPLICABLE"; mutations.append(changed)
changed = copy.deepcopy(operations); changed[0]["Agent Slice Operations visible status evidence"] = "NOT_APPLICABLE"; mutations.append(changed)
changed = copy.deepcopy(operations); changed[0][PRODUCT_FIELDS[0]] = "WORKFLOW-CAPABILITY-1"; mutations.append(changed)

changed = copy.deepcopy(product); changed[1]["Agent Slice class"] = "OPERATIONS"; mutations.append(changed)
changed = copy.deepcopy(product); changed[1]["Agent Slice route proof identity"] = evidence_ref("OTHER-PROOF", HASH_A, "other-proof"); mutations.append(changed)
changed = copy.deepcopy(product); changed[1]["Agent Slice Verification route evidence kind"] = "OPERATIONS_ROUTE_PROOF"; mutations.append(changed)
changed = copy.deepcopy(product); changed[1]["Agent Slice Verification class isolation"] = "MIXED_EVIDENCE"; mutations.append(changed)

changed = copy.deepcopy(product); changed[2]["Agent Slice Baseline accepted class set"] = "PRODUCT|OPERATIONS|MIXED"; mutations.append(changed)
changed = copy.deepcopy(product); changed[2]["Agent Slice candidate ID / exact hash"] = "CANDIDATE-2 / " + HASH_B; mutations.append(changed)
changed = copy.deepcopy(product); changed[2]["Agent Slice Baseline accepted OPERATIONS Slice IDs"] = ""; mutations.append(changed)
changed = copy.deepcopy(product); changed[2]["Agent Slice Baseline accepted PRODUCT Slice IDs"] = ""; mutations.append(changed)
changed = copy.deepcopy(product); changed[2]["Agent Slice Baseline required Operations Slice ID"] = "OPS-UNKNOWN"; mutations.append(changed)
changed = copy.deepcopy(product); changed[2]["Agent Slice Baseline Product Agent Slice ID"] = "PRODUCT-UNKNOWN"; mutations.append(changed)
changed = copy.deepcopy(product); changed[2]["Agent Slice Baseline Product Agent acceptance evidence"] = changed[2]["Agent Slice Baseline required Operations acceptance evidence"]; mutations.append(changed)
changed = copy.deepcopy(product); changed[2]["Agent Slice Baseline class isolation"] = "ONE_MIXED_ROUTE"; mutations.append(changed)
changed = copy.deepcopy(product); changed[2]["Agent Slice ID"] = changed[0]["Agent Slice ID"]; mutations.append(changed)

ui_product = documents("PRODUCT", valid_configuration(), "UI_ACTOR")
changed = copy.deepcopy(ui_product)
changed[2]["Agent Slice Baseline Product Agent Slice ID"] = changed[0]["Agent Slice ID"]
mutations.append(changed)

for mutation_index, changed in enumerate(mutations):
    assert validate_records(changed), mutation_index

same_agent = documents("PRODUCT")
same_agent[3]["product_agent"]["agent_id"] = "OPS-1"
assert validate_records(same_agent)

template_records = (
    {key: value for key, value in feature_template_fields.items() if key.startswith("Agent Slice ")},
    {key: value for key, value in final_template_fields.items() if key.startswith("Agent Slice ")},
    {key: value for key, value in baseline_template_fields.items() if key.startswith("Agent Slice ")},
    valid_configuration(),
)
assert validate_records(template_records)

duplicate_feature = texts(product)[0] + "- Agent Slice ID: PRODUCT-SLICE-1\n"
assert validator.validate_agent_slice(
    duplicate_feature,
    texts(product)[1],
    texts(product)[2],
    product[3],
    CONFIG_HASH,
    "PRODUCT-BASELINE-1",
    PRODUCT_BASELINE_HASH,
    "PRODUCTION-TOPOLOGY-1",
    TOPOLOGY_HASH,
    "ADAPTER-ATTESTATION-1",
    ADAPTER_HASH,
)

with tempfile.TemporaryDirectory(prefix="agent-slices-280-") as temporary:
    paths = [Path(temporary) / name for name in ("FEATURE-SLICE.md", "FINAL-FEATURE-VERIFICATION.md", "INTEGRATION-BASELINE.md")]
    for path, text in zip(paths, texts(product)):
        path.write_text(text, encoding="utf-8")
    before = [(path.read_bytes(), path.stat().st_mtime_ns) for path in paths]
    assert validator.validate_agent_slice_files(
        *paths,
        product[3],
        CONFIG_HASH,
        "PRODUCT-BASELINE-1",
        PRODUCT_BASELINE_HASH,
        "PRODUCTION-TOPOLOGY-1",
        TOPOLOGY_HASH,
        "ADAPTER-ATTESTATION-1",
        ADAPTER_HASH,
    ) == []
    assert [(path.read_bytes(), path.stat().st_mtime_ns) for path in paths] == before

print("PASS: PRODUCT and OPERATIONS Feature Slices prove distinct real routes")
