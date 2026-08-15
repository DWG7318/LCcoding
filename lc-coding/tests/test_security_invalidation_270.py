from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile


root = Path(__file__).resolve().parents[2]
validator = root / "lc-coding/scripts/validate_vulnerability_closure.py"
project_validator_path = root / "lc-coding/scripts/validate_project.py"
delivery_decision_validator = root / "lc-coding/scripts/validate_delivery_decision.py"
project_spec = importlib.util.spec_from_file_location(
    "validate_project_security_270", project_validator_path
)
project_validator = importlib.util.module_from_spec(project_spec)
project_spec.loader.exec_module(project_validator)
CANDIDATE_ID = "CANDIDATE-1"
CANDIDATE_HASH = "sha256:" + "a" * 64
SURFACES = ["SURFACE-AUTH", "SURFACE-API", "SURFACE-DATA", "SURFACE-INSTALLER"]
AGENT_SURFACE_KINDS = [
    "PROMPT_INJECTION_INSTRUCTION_BOUNDARY",
    "PRIVILEGE_AUTHORIZATION",
    "DUAL_AGENT_MEMORY_ISOLATION",
    "SESSION_CONTEXT_RETRIEVER_VECTOR_PROMPT_CACHE",
    "CREDENTIAL_KEY_TOOL_SECRET",
    "MODEL_DRIFT_UNAVAILABILITY",
    "RUNTIME_ADAPTER_DRIFT_REPLACEMENT",
    "POLICY_ACTION_CATALOG_BYPASS",
    "TYPED_EVENT_REDACTION_PROVENANCE",
    "FALLBACK_ROLLBACK_AUDIT_KILL_SWITCH",
]
SECURITY_CONTRACT = json.loads(
    (root / "lc-coding/contracts/vulnerability-closure.json").read_text(encoding="utf-8")
)
assert SECURITY_CONTRACT["agent_surface_kinds"] == AGENT_SURFACE_KINDS


def evidence(evidence_id, surfaces, candidate_id=CANDIDATE_ID, candidate_hash=CANDIDATE_HASH):
    return {
        "evidence_id": evidence_id,
        "candidate_id": candidate_id,
        "candidate_hash": candidate_hash,
        "surface_ids": list(surfaces),
    }


def auditor(prefix, prior_roles=None):
    return {
        "agent_id": prefix + "-AGENT",
        "context_id": prefix + "-CONTEXT",
        "workspace_id": prefix + "-WORKSPACE",
        "independent": True,
        "prior_roles": list(prior_roles or []),
    }


def surface(surface_id, category, audit_id, check_id, disposition="INCLUDED"):
    return {
        "surface_id": surface_id,
        "category": category,
        "candidate_id": CANDIDATE_ID,
        "candidate_hash": CANDIDATE_HASH,
        "coverage_status": "COMPLETE",
        "audit_evidence_ids": [audit_id],
        "current_check_ids": [check_id],
        "disposition": disposition,
        "exclusion_evidence_id": (
            "E-INSTALLER-NOT-APPLICABLE"
            if disposition == "EXCLUDED_NOT_APPLICABLE"
            else "NONE"
        ),
    }


def relation(source, target, suffix, candidate_id=CANDIDATE_ID, candidate_hash=CANDIDATE_HASH):
    return {
        "source_surface_id": source,
        "target_surface_id": target,
        "candidate_id": candidate_id,
        "candidate_hash": candidate_hash,
        "evidence_id": "E-REL-" + suffix,
        "reason_id": "R-REL-" + suffix,
    }


def not_applicable_agent_binding():
    return {
        field: "NOT_APPLICABLE"
        for field in SECURITY_CONTRACT["agent_security_binding_fields"]
    }


def bound_agent_binding():
    return {
        "state": "BOUND",
        "candidate_id": CANDIDATE_ID,
        "candidate_hash": CANDIDATE_HASH,
        "configuration_baseline_id": "ACB-1",
        "configuration_baseline_hash": "sha256:" + "c" * 64,
        "production_topology_id": "TOPOLOGY-1",
        "production_topology_hash": "sha256:" + "d" * 64,
        "runtime_adapter_attestation_id": "RAA-1",
        "runtime_adapter_attestation_hash": "sha256:" + "e" * 64,
        "runtime_adapter_id": "RUNTIME-ADAPTER-1",
        "runtime_adapter_version": "1.2.3",
        "runtime_adapter_digest": "sha256:" + "f" * 64,
        "product_agent_applicability": "APPLICABLE_CORE",
        "product_agent_id": "PRODUCT-AGENT-1",
        "operations_agent_id": "OPERATIONS-AGENT-1",
        "identity_status": "CURRENT",
    }


def agent_surface_bindings(binding):
    records = []
    for index, kind in enumerate(AGENT_SURFACE_KINDS, 1):
        role = SECURITY_CONTRACT["agent_surface_kind_roles"][kind]
        agent_ids = (
            [binding["runtime_adapter_id"]] if role == "RUNTIME_ADAPTER"
            else [binding["operations_agent_id"]] if role == "OPERATIONS_AGENT"
            else [binding["product_agent_id"], binding["operations_agent_id"]]
        )
        records.append({
            "binding_id": f"AGENT-SURFACE-BINDING-{index}",
            "agent_surface_kind": kind,
            "security_surface_id": "SURFACE-AUTH",
            "agent_role": role,
            "agent_ids": agent_ids,
            "candidate_id": binding["candidate_id"],
            "candidate_hash": binding["candidate_hash"],
            "configuration_baseline_id": binding["configuration_baseline_id"],
            "configuration_baseline_hash": binding["configuration_baseline_hash"],
            "production_topology_id": binding["production_topology_id"],
            "production_topology_hash": binding["production_topology_hash"],
            "runtime_adapter_id": binding["runtime_adapter_id"],
            "runtime_adapter_version": binding["runtime_adapter_version"],
            "runtime_adapter_digest": binding["runtime_adapter_digest"],
            "audit_evidence_id": "E-AUTH-AUDIT",
            "current_check_id": "E-AUTH-CHECK",
            "remediation_evidence_id": "E-REMEDIATION-1",
            "reaudit_evidence_id": "SA-REAUDIT-1",
            "result": "PASS",
        })
    return records


def valid_receipt(agent_bound=False):
    checks = [
        evidence("E-AUTH-AUDIT", ["SURFACE-AUTH"]),
        evidence("E-AUTH-CHECK", ["SURFACE-AUTH"]),
        evidence("E-API-AUDIT", ["SURFACE-API"]),
        evidence("E-API-CHECK", ["SURFACE-API"]),
        evidence("E-DATA-CHECK", ["SURFACE-DATA"]),
        evidence("E-INSTALLER-SCOPE", ["SURFACE-INSTALLER"]),
        evidence("E-INSTALLER-CHECK", ["SURFACE-INSTALLER"]),
        evidence("E-INSTALLER-NOT-APPLICABLE", ["SURFACE-INSTALLER"]),
    ]
    binding = bound_agent_binding() if agent_bound else not_applicable_agent_binding()
    return {
        "schema_version": "2.7.0",
        "artifact_role": "VULNERABILITY_CLOSURE_RECEIPT",
        "closure_id": "VC-270",
        "candidate_id": CANDIDATE_ID,
        "candidate_hash": CANDIDATE_HASH,
        "agent_security_binding": binding,
        "agent_surface_bindings": agent_surface_bindings(binding) if agent_bound else [],
        "pre_audit_loop_owner_acceptance_receipts": [
            evidence("OA-PRE-1", SURFACES)
        ],
        "security_auditor": auditor("PRIMARY"),
        "audit_scope": {
            "scope": "FINAL_ACCEPTED_CANDIDATE",
            **evidence("E-AUDIT-SCOPE", SURFACES),
        },
        "coverage": {
            "status": "COMPLETE",
            **evidence("E-COVERAGE", SURFACES),
        },
        "required_surface_ids": list(SURFACES),
        "security_surfaces": [
            surface(
                "SURFACE-AUTH",
                "AUTHENTICATION_AUTHORIZATION",
                "E-AUTH-AUDIT",
                "E-AUTH-CHECK",
            ),
            surface(
                "SURFACE-API", "API_EXPOSURE", "E-API-AUDIT", "E-API-CHECK"
            ),
            surface(
                "SURFACE-DATA",
                "DATA_HANDLING_ISOLATION",
                "E-DATA-REUSED",
                "E-DATA-CHECK",
            ),
            surface(
                "SURFACE-INSTALLER",
                "INSTALLER_RUNTIME",
                "E-INSTALLER-SCOPE",
                "E-INSTALLER-CHECK",
                "EXCLUDED_NOT_APPLICABLE",
            ),
        ],
        "transitive_relations": [
            relation("SURFACE-AUTH", "SURFACE-API", "AUTH-API"),
            relation("SURFACE-API", "SURFACE-DATA", "API-DATA"),
        ],
        "reused_security_evidence": [
            evidence("E-DATA-REUSED", ["SURFACE-DATA"])
        ],
        "new_checks": checks,
        "findings": [
            {
                "finding_id": "F-AUTH-1",
                "candidate_id": CANDIDATE_ID,
                "candidate_hash": CANDIDATE_HASH,
                "surface_ids": ["SURFACE-AUTH"],
                "severity": "HIGH",
                "category": "AUTHENTICATION_BYPASS",
                "status": "MITIGATED",
                "evidence_id": "E-FINDING-AUTH-1",
            }
        ],
        "remediation_runs": [
            {
                "run_id": "SEC-RUN-1",
                "candidate_id": CANDIDATE_ID,
                "candidate_hash": CANDIDATE_HASH,
                "surface_ids": ["SURFACE-AUTH"],
                "evidence_id": "E-REMEDIATION-1",
                "implementer_id": "REMEDIATOR-1",
            }
        ],
        "residual_risks": [],
        "affected_receipts": [evidence("OA-AFFECTED-1", ["SURFACE-AUTH"])],
        "reaudit": {
            "status": "COMPLETE",
            "auditor": auditor("REAUDIT"),
            "covered_surface_ids": ["SURFACE-AUTH", "SURFACE-API", "SURFACE-DATA"],
            "receipt_evidence": [
                evidence(
                    "SA-REAUDIT-1",
                    ["SURFACE-AUTH", "SURFACE-API", "SURFACE-DATA"],
                )
            ],
        },
        "verdict": {
            "result": "VULNERABILITY_CLOSED",
            **evidence("E-CLOSURE-VERDICT", SURFACES),
        },
        "issued_at": "2026-08-12T00:00:00Z",
    }


def command(path, *, candidate_id=CANDIDATE_ID, candidate_hash=CANDIDATE_HASH, surfaces=SURFACES):
    result = [sys.executable, str(validator), str(path)]
    if candidate_id is not None:
        result += ["--expected-candidate-id", candidate_id]
    if candidate_hash is not None:
        result += ["--expected-candidate-hash", candidate_hash]
    if surfaces is not None:
        for surface_id in surfaces:
            result += ["--required-surface-id", surface_id]
    return result


def run_bytes(path, raw, **options):
    path.write_bytes(raw)
    before = path.read_bytes()
    before_hash = hashlib.sha256(before).hexdigest()
    result = subprocess.run(command(path, **options), capture_output=True, text=True)
    after = path.read_bytes()
    assert after == before
    assert hashlib.sha256(after).hexdigest() == before_hash
    return result


def run(path, receipt, **options):
    return run_bytes(
        path,
        (json.dumps(receipt, ensure_ascii=False, separators=(",", ":")) + "\n").encode(),
        **options,
    )


def must_fail(path, mutate, label, **options):
    receipt = valid_receipt()
    mutate(receipt)
    result = run(path, receipt, **options)
    assert result.returncode != 0, label


def rewrite_identity(value, candidate_id, candidate_hash):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "candidate_id":
                value[key] = candidate_id
            elif key == "candidate_hash":
                value[key] = candidate_hash
            else:
                rewrite_identity(item, candidate_id, candidate_hash)
    elif isinstance(value, list):
        for item in value:
            rewrite_identity(item, candidate_id, candidate_hash)


with tempfile.TemporaryDirectory(prefix="lccoding-security-270-") as temporary:
    receipt_path = Path(temporary) / "VULNERABILITY-CLOSURE.json"
    valid = valid_receipt()
    valid_result = run(receipt_path, valid)
    assert valid_result.returncode == 0, valid_result.stdout + valid_result.stderr

    review_bypasses = []
    absolute_residual = valid_receipt()
    absolute_residual["findings"][0]["status"] = "ACCEPTED_RESIDUAL"
    if run(receipt_path, absolute_residual).returncode == 0:
        review_bypasses.append("ABSOLUTE_ACCEPTED_RESIDUAL")

    duplicate_reaudit = valid_receipt()
    duplicate_reaudit["reaudit"]["receipt_evidence"].append(
        copy.deepcopy(duplicate_reaudit["reaudit"]["receipt_evidence"][0])
    )
    if run(receipt_path, duplicate_reaudit).returncode == 0:
        review_bypasses.append("DUPLICATE_REAUDIT_RECEIPT")

    missing_affected = valid_receipt()
    missing_affected["affected_receipts"] = []
    if run(receipt_path, missing_affected).returncode == 0:
        review_bypasses.append("MISSING_AFFECTED_RECEIPT")

    assert not review_bypasses, (
        "vulnerability closure accepted independent review bypasses: "
        + ", ".join(review_bypasses)
    )

    contract = json.loads(
        (root / "lc-coding/contracts/vulnerability-closure.json").read_text(encoding="utf-8")
    )
    template = json.loads(
        (root / "lc-coding/templates/VULNERABILITY-CLOSURE.json").read_text(encoding="utf-8")
    )
    assert set(template) == set(contract["top_level_fields"])
    assert template["schema_version"] == "2.7.0"
    assert template["artifact_role"] == "VULNERABILITY_CLOSURE_RECEIPT"
    assert template["agent_security_binding"] == not_applicable_agent_binding()
    assert template["agent_surface_bindings"] == []

    agent_valid = valid_receipt(agent_bound=True)
    result = run(receipt_path, agent_valid)
    assert result.returncode == 0, result.stdout + result.stderr

    def reject_agent(mutate, marker):
        changed = valid_receipt(agent_bound=True)
        mutate(changed)
        rejected = run(receipt_path, changed)
        assert rejected.returncode != 0, marker
        assert marker in rejected.stdout + rejected.stderr, rejected.stdout + rejected.stderr

    reject_agent(
        lambda item: item["agent_surface_bindings"].pop(),
        "Agent security surface kinds are missing, extra, duplicated, unknown, or unordered",
    )
    reject_agent(
        lambda item: item["agent_surface_bindings"].append(
            {**copy.deepcopy(item["agent_surface_bindings"][0]),
             "binding_id": "AGENT-SURFACE-BINDING-EXTRA",
             "agent_surface_kind": "UNKNOWN_AGENT_SURFACE"}
        ),
        "Agent security surface kinds are missing, extra, duplicated, unknown, or unordered",
    )
    reject_agent(
        lambda item: item["agent_surface_bindings"][0].__setitem__(
            "agent_ids", ["OPERATIONS-AGENT-1"]
        ),
        "Agent identities disagree with Agent security binding",
    )
    reject_agent(
        lambda item: item["agent_security_binding"].__setitem__(
            "candidate_hash", "sha256:" + "b" * 64
        ),
        "Agent security binding must bind the exact current candidate",
    )
    reject_agent(
        lambda item: item["agent_security_binding"].__setitem__(
            "identity_status", "REPLACED"
        ),
        "Agent security binding requires current non-replaced identities",
    )
    reject_agent(
        lambda item: item["agent_surface_bindings"][1].__setitem__(
            "binding_id", item["agent_surface_bindings"][0]["binding_id"]
        ),
        "Agent security surface binding IDs must be unique",
    )
    reject_agent(
        lambda item: item["agent_surface_bindings"][0].__setitem__(
            "audit_evidence_id", "PASS"
        ),
        "audit evidence does not map to the security surface",
    )
    reject_agent(
        lambda item: item["agent_surface_bindings"][0].__setitem__(
            "security_surface_id", "SURFACE-MISSING"
        ),
        "must map to an INCLUDED required security surface",
    )
    reject_agent(
        lambda item: item["agent_surface_bindings"][0].__setitem__(
            "remediation_evidence_id", "E-MISSING"
        ),
        "lacks exact remediation evidence",
    )
    reject_agent(
        lambda item: item["agent_surface_bindings"][0].__setitem__(
            "reaudit_evidence_id", "E-MISSING"
        ),
        "lacks exact transitive re-audit evidence",
    )
    reject_agent(
        lambda item: item.update({
            "agent_security_binding": not_applicable_agent_binding(),
        }),
        "NOT_APPLICABLE Agent security binding requires empty Agent surfaces",
    )

    accepted_residual = valid_receipt()
    accepted_residual["findings"][0].update(
        {
            "severity": "MEDIUM",
            "category": "CONFIGURATION",
            "status": "ACCEPTED_RESIDUAL",
        }
    )
    accepted_residual["remediation_runs"] = []
    accepted_residual["affected_receipts"] = []
    residual_result = run(receipt_path, accepted_residual)
    assert residual_result.returncode == 0, residual_result.stdout + residual_result.stderr

    absolute_false_positive = valid_receipt()
    absolute_false_positive["findings"][0]["status"] = "FALSE_POSITIVE"
    absolute_false_positive["remediation_runs"] = []
    absolute_false_positive["affected_receipts"] = []
    false_positive_result = run(receipt_path, absolute_false_positive)
    assert false_positive_result.returncode == 0, (
        false_positive_result.stdout + false_positive_result.stderr
    )

    no_security_change = valid_receipt()
    no_security_change["findings"] = []
    no_security_change["remediation_runs"] = []
    no_security_change["affected_receipts"] = []
    no_change_result = run(receipt_path, no_security_change)
    assert no_change_result.returncode == 0, no_change_result.stdout + no_change_result.stderr

    # Current closure cannot be claimed without a complete expected-current binding.
    for options, label in (
        ({"candidate_id": None}, "missing expected candidate ID"),
        ({"candidate_hash": None}, "missing expected candidate hash"),
        ({"surfaces": None}, "missing expected surface set"),
        ({"candidate_hash": "abc"}, "malformed expected candidate hash"),
        ({"candidate_id": "CANDIDATE-OLD"}, "stale expected candidate ID"),
        ({"candidate_hash": "sha256:" + "b" * 64}, "stale expected candidate hash"),
        ({"surfaces": SURFACES[:-1]}, "incomplete expected surface set"),
        ({"surfaces": SURFACES + ["SURFACE-EXTRA"]}, "extra expected surface"),
    ):
        assert run(receipt_path, valid, **options).returncode != 0, label

    for field, value, label in (
        ("candidate_hash", "abc", "malformed candidate hash"),
        ("candidate_hash", "sha256:" + "A" * 64, "uppercase candidate hash"),
        ("candidate_hash", "sha256:" + "b" * 64, "stale candidate hash"),
        ("candidate_id", "PENDING", "generic candidate ID"),
        ("candidate_id", "CANDIDATE-OLD", "stale candidate ID"),
        ("schema_version", "2.6.0", "legacy schema claim"),
        ("artifact_role", "SECURITY_REPORT", "wrong artifact role"),
    ):
        must_fail(receipt_path, lambda item, f=field, v=value: item.__setitem__(f, v), label)

    must_fail(
        receipt_path,
        lambda item: item["audit_scope"].__setitem__("candidate_hash", "sha256:" + "b" * 64),
        "mixed audit-scope candidate",
    )
    must_fail(
        receipt_path,
        lambda item: rewrite_identity(item, "CANDIDATE-OLD", "sha256:" + "b" * 64),
        "synchronized stale receipt against current expected identity",
    )
    must_fail(
        receipt_path,
        lambda item: item["new_checks"][0].pop("candidate_hash"),
        "old ID-only evidence",
    )
    must_fail(
        receipt_path,
        lambda item: item["reused_security_evidence"][0].__setitem__("candidate_id", "CANDIDATE-OLD"),
        "reused evidence mixed candidate",
    )
    must_fail(
        receipt_path,
        lambda item: item["security_surfaces"][0].__setitem__("candidate_hash", "sha256:" + "b" * 64),
        "security surface mixed candidate",
    )
    must_fail(
        receipt_path,
        lambda item: item["findings"][0].__setitem__("candidate_id", "CANDIDATE-OLD"),
        "finding mixed candidate",
    )
    must_fail(
        receipt_path,
        lambda item: item["reaudit"]["receipt_evidence"][0].__setitem__("candidate_hash", "sha256:" + "b" * 64),
        "re-audit receipt mixed candidate",
    )
    must_fail(
        receipt_path,
        lambda item: item["verdict"].__setitem__("candidate_id", "CANDIDATE-OLD"),
        "verdict mixed candidate",
    )
    must_fail(receipt_path, lambda item: item.pop("issued_at"), "missing top-level field")
    must_fail(receipt_path, lambda item: item.__setitem__("shadow", "x"), "unknown top-level field")
    must_fail(
        receipt_path,
        lambda item: item["security_auditor"].pop("context_id"),
        "missing nested field",
    )
    must_fail(
        receipt_path,
        lambda item: item["security_auditor"].__setitem__("shadow", "x"),
        "unknown nested field",
    )

    valid_text = json.dumps(valid, separators=(",", ":"))
    duplicate_top = valid_text.replace(
        '"candidate_id":"CANDIDATE-1"',
        '"candidate_id":"CANDIDATE-1","candidate_id":"CANDIDATE-OTHER"',
        1,
    )
    assert run_bytes(receipt_path, (duplicate_top + "\n").encode()).returncode != 0
    duplicate_nested = valid_text.replace(
        '"agent_id":"PRIMARY-AGENT"',
        '"agent_id":"PRIMARY-AGENT","agent_id":"SHADOW-AGENT"',
        1,
    )
    assert run_bytes(receipt_path, (duplicate_nested + "\n").encode()).returncode != 0

    must_fail(
        receipt_path,
        lambda item: item["security_surfaces"][0].__setitem__("surface_id", ""),
        "empty surface ID",
    )
    must_fail(
        receipt_path,
        lambda item: item["security_surfaces"][0].__setitem__("surface_id", "PENDING"),
        "generic surface ID",
    )
    must_fail(
        receipt_path,
        lambda item: item["security_surfaces"].append(copy.deepcopy(item["security_surfaces"][0])),
        "duplicate surface ID",
    )
    for field, value, label in (
        ("category", "NETWORK", "unknown surface category"),
        ("coverage_status", "PENDING", "incomplete surface"),
        ("disposition", "SKIPPED", "unknown surface disposition"),
    ):
        must_fail(
            receipt_path,
            lambda item, f=field, v=value: item["security_surfaces"][0].__setitem__(f, v),
            label,
        )
    must_fail(
        receipt_path,
        lambda item: item["security_surfaces"][3].__setitem__("exclusion_evidence_id", "NONE"),
        "bare exclusion",
    )
    must_fail(
        receipt_path,
        lambda item: item["security_surfaces"][0].__setitem__("audit_evidence_ids", ["OA-PRE-1"]),
        "Owner receipt cannot substitute for security audit evidence",
    )
    must_fail(
        receipt_path,
        lambda item: item["security_surfaces"][0].__setitem__("current_check_ids", ["OA-AFFECTED-1"]),
        "affected receipt cannot substitute for a current security check",
    )
    must_fail(
        receipt_path,
        lambda item: item["required_surface_ids"].pop(),
        "missing required surface",
    )
    must_fail(
        receipt_path,
        lambda item: item["required_surface_ids"].append("SURFACE-EXTRA"),
        "extra required surface",
    )
    must_fail(
        receipt_path,
        lambda item: item["required_surface_ids"].append(SURFACES[0]),
        "duplicate required surface",
    )

    relation_mutations = (
        (lambda item: item["transitive_relations"][0].__setitem__("target_surface_id", "SURFACE-MISSING"), "missing transitive target"),
        (lambda item: item["transitive_relations"][0].__setitem__("source_surface_id", "SURFACE-MISSING"), "unknown relation source"),
        (lambda item: item["transitive_relations"].append(copy.deepcopy(item["transitive_relations"][0])), "duplicate relation"),
        (lambda item: item["transitive_relations"][0].__setitem__("target_surface_id", "SURFACE-AUTH"), "self relation"),
        (lambda item: item["transitive_relations"][0].__setitem__("candidate_hash", "sha256:" + "b" * 64), "wrong relation candidate"),
        (lambda item: item["transitive_relations"][0].__setitem__("evidence_id", "PASS"), "generic relation evidence"),
        (lambda item: item["transitive_relations"][0].__setitem__("reason_id", "PENDING"), "generic relation reason"),
        (lambda item: item["transitive_relations"].append(relation("SURFACE-DATA", "SURFACE-AUTH", "DATA-AUTH")), "cyclic relation"),
    )
    for mutate, label in relation_mutations:
        must_fail(receipt_path, mutate, label)

    must_fail(
        receipt_path,
        lambda item: item["findings"][0].__setitem__("surface_ids", ["SURFACE-MISSING"]),
        "finding references unknown surface",
    )
    must_fail(
        receipt_path,
        lambda item: item["findings"].append(copy.deepcopy(item["findings"][0])),
        "duplicate finding ID",
    )
    for severity, category in (
        ("HIGH", "INJECTION"),
        ("CRITICAL", "CONFIGURATION"),
        ("MEDIUM", "SECRET_EXPOSURE"),
    ):
        def open_finding(item, severity=severity, category=category):
            item["findings"][0]["severity"] = severity
            item["findings"][0]["category"] = category
            item["findings"][0]["status"] = "OPEN"
        must_fail(receipt_path, open_finding, "open blocking finding")
    for absolute_category in contract["absolute_blockers"]:
        def accepted_absolute(item, category=absolute_category):
            item["findings"][0]["category"] = category
            item["findings"][0]["severity"] = "HIGH"
            item["findings"][0]["status"] = "ACCEPTED_RESIDUAL"
        must_fail(
            receipt_path,
            accepted_absolute,
            absolute_category + " cannot be accepted residual",
        )
    must_fail(
        receipt_path,
        lambda item: item["findings"][0].__setitem__("severity", "SEVERE"),
        "unknown finding severity",
    )
    must_fail(
        receipt_path,
        lambda item: item["findings"][0].__setitem__("status", "WAIVED"),
        "unknown finding status",
    )

    must_fail(
        receipt_path,
        lambda item: item["remediation_runs"][0].__setitem__("candidate_id", "CANDIDATE-OLD"),
        "wrong remediation candidate",
    )
    must_fail(
        receipt_path,
        lambda item: item["remediation_runs"][0].__setitem__("surface_ids", ["SURFACE-MISSING"]),
        "remediation unknown surface",
    )
    must_fail(
        receipt_path,
        lambda item: item.__setitem__("remediation_runs", []),
        "mitigated finding missing remediation Run",
    )
    must_fail(
        receipt_path,
        lambda item: item["affected_receipts"][0].__setitem__("candidate_hash", "sha256:" + "b" * 64),
        "affected receipt wrong candidate",
    )
    must_fail(
        receipt_path,
        lambda item: item["affected_receipts"].append(copy.deepcopy(item["affected_receipts"][0])),
        "duplicate affected receipt",
    )
    must_fail(
        receipt_path,
        lambda item: item["affected_receipts"][0].__setitem__("evidence_id", "PASS"),
        "generic affected receipt ID",
    )
    must_fail(
        receipt_path,
        lambda item: item["affected_receipts"][0].__setitem__("surface_ids", ["SURFACE-MISSING"]),
        "affected receipt unknown surface",
    )
    def incomplete_direct_affected_receipts(item):
        item["findings"][0]["surface_ids"] = ["SURFACE-AUTH", "SURFACE-API"]
        item["remediation_runs"][0]["surface_ids"] = ["SURFACE-AUTH", "SURFACE-API"]
        item["affected_receipts"][0]["surface_ids"] = ["SURFACE-AUTH"]
    must_fail(
        receipt_path,
        incomplete_direct_affected_receipts,
        "affected receipts miss one directly remediated surface",
    )
    must_fail(
        receipt_path,
        lambda item: item["reaudit"].__setitem__("covered_surface_ids", ["SURFACE-AUTH"]),
        "reaudit misses transitive affected surfaces",
    )
    must_fail(
        receipt_path,
        lambda item: item["reaudit"]["covered_surface_ids"].append("SURFACE-MISSING"),
        "reaudit references unknown surface",
    )
    must_fail(
        receipt_path,
        lambda item: item["security_surfaces"][2].__setitem__("coverage_status", "PENDING"),
        "transitively affected target is incomplete",
    )
    must_fail(
        receipt_path,
        lambda item: item["reaudit"]["receipt_evidence"][0].__setitem__("evidence_id", "PASS"),
        "generic re-audit receipt",
    )
    must_fail(
        receipt_path,
        lambda item: item["reaudit"]["receipt_evidence"].append(
            {
                **copy.deepcopy(item["reaudit"]["receipt_evidence"][0]),
                "surface_ids": ["SURFACE-AUTH"],
            }
        ),
        "conflicting duplicate re-audit receipt ID",
    )
    must_fail(
        receipt_path,
        lambda item: item["findings"][0].__setitem__(
            "evidence_id", item["reaudit"]["receipt_evidence"][0]["evidence_id"]
        ),
        "finding and re-audit receipt share an evidence ID",
    )
    must_fail(
        receipt_path,
        lambda item: item["verdict"].__setitem__(
            "evidence_id", item["findings"][0]["evidence_id"]
        ),
        "verdict and finding share an evidence ID",
    )
    must_fail(
        receipt_path,
        lambda item: item["reaudit"]["auditor"].__setitem__("prior_roles", ["REMEDIATION_IMPLEMENTER"]),
        "forbidden re-auditor prior role",
    )
    must_fail(
        receipt_path,
        lambda item: item["security_auditor"].__setitem__("prior_roles", ["REMEDIATION_IMPLEMENTER"]),
        "forbidden primary auditor prior role",
    )
    must_fail(
        receipt_path,
        lambda item: item["remediation_runs"][0].__setitem__("implementer_id", "PRIMARY-AGENT"),
        "auditor self-implemented remediation",
    )
    must_fail(
        receipt_path,
        lambda item: item["reaudit"].__setitem__("auditor", copy.deepcopy(item["security_auditor"])),
        "re-audit identity is not independent",
    )
    must_fail(
        receipt_path,
        lambda item: item["coverage"].__setitem__("status", "PENDING"),
        "closed verdict cannot override incomplete coverage",
    )

    legacy_bytes = (
        '{"closure_id":"VC-OLD","candidate_id":"CANDIDATE-1",'
        '"candidate_hash":"abc","pre_audit_loop_owner_acceptance_receipts":["OA-1"],'
        '"security_auditor":{"agent_id":"SEC-1","context_id":"CTX-1",'
        '"workspace_id":"WS-1","independent":true,"prior_roles":[]},'
        '"audit_scope":"FINAL_ACCEPTED_CANDIDATE","coverage":{"status":"COMPLETE",'
        '"attack_surfaces":["auth"],"exclusions":[]},"findings":[],"remediation_runs":[],'
        '"reaudit":{"status":"COMPLETE","receipt_ids":["SA-1"]},'
        '"verdict":"VULNERABILITY_CLOSED"}\n'
    ).encode()
    assert run_bytes(receipt_path, legacy_bytes).returncode != 0


agent_project_spec = importlib.util.spec_from_file_location(
    "security_agent_project_fixture",
    root / "lc-coding/tests/test_agent_product_formation_280.py",
)
agent_project_fixture = importlib.util.module_from_spec(agent_project_spec)
agent_project_spec.loader.exec_module(agent_project_fixture)


def bind_receipt_to_agent_status(receipt, binding):
    receipt["agent_security_binding"] = copy.deepcopy(binding)
    for surface_binding in receipt["agent_surface_bindings"]:
        for field in (
            "candidate_id", "candidate_hash", "configuration_baseline_id",
            "configuration_baseline_hash", "production_topology_id",
            "production_topology_hash", "runtime_adapter_id",
            "runtime_adapter_version", "runtime_adapter_digest",
        ):
            surface_binding[field] = binding[field]
        if surface_binding["agent_role"] == "RUNTIME_ADAPTER":
            surface_binding["agent_ids"] = [binding["runtime_adapter_id"]]
        elif surface_binding["agent_role"] == "OPERATIONS_AGENT":
            surface_binding["agent_ids"] = [binding["operations_agent_id"]]
        else:
            surface_binding["agent_ids"] = [
                binding["product_agent_id"], binding["operations_agent_id"]
            ]


with tempfile.TemporaryDirectory(prefix="lccoding-agent-security-280-") as temporary:
    lc, agent_status = agent_project_fixture.build_agent_slice_status_project(
        Path(temporary) / "project"
    )
    (lc / "status.json").write_text(json.dumps(agent_status), encoding="utf-8")
    expected_binding, binding_errors = project_validator._expected_agent_security_binding(
        lc, agent_status
    )
    assert binding_errors == []
    current_receipt = valid_receipt(agent_bound=True)
    agent_candidate = (
        agent_status["canonical_candidate"]["candidate_id"],
        agent_status["canonical_candidate"]["candidate_hash"],
    )
    rewrite_identity(current_receipt, *agent_candidate)
    bind_receipt_to_agent_status(current_receipt, expected_binding)
    closure_path = lc / "VULNERABILITY-CLOSURE.json"
    closure_path.write_text(json.dumps(current_receipt), encoding="utf-8")
    _, errors = project_validator.load_vulnerability_reference(
        lc, "VULNERABILITY-CLOSURE.json", "VC-270",
        agent_candidate, expected_binding,
    )
    assert errors == [], errors
    for field, value in (
        ("configuration_baseline_hash", "sha256:" + "1" * 64),
        ("production_topology_hash", "sha256:" + "2" * 64),
        ("runtime_adapter_attestation_hash", "sha256:" + "3" * 64),
        ("runtime_adapter_id", "RUNTIME-ADAPTER-OTHER"),
        ("runtime_adapter_digest", "sha256:" + "4" * 64),
        ("product_agent_id", "PRODUCT-AGENT-OTHER"),
        ("operations_agent_id", "OPERATIONS-AGENT-OTHER"),
    ):
        changed = copy.deepcopy(current_receipt)
        changed_binding = changed["agent_security_binding"]
        changed_binding[field] = value
        bind_receipt_to_agent_status(changed, changed_binding)
        closure_path.write_text(json.dumps(changed), encoding="utf-8")
        _, errors = project_validator.load_vulnerability_reference(
            lc, "VULNERABILITY-CLOSURE.json", "VC-270",
            agent_candidate, expected_binding,
        )
        assert any(
            "Agent security binding disagrees with authoritative Agent Slice status" in error
            for error in errors
        ), errors


status = json.loads((root / "lc-coding/templates/STATUS.json").read_text(encoding="utf-8"))
phase_status = json.loads(
    (root / "lc-coding/templates/PHASE-STATUS.json").read_text(encoding="utf-8")
)
health = json.loads(
    (root / "lc-coding/templates/PROJECT-HEALTH.json").read_text(encoding="utf-8")
)
status["current_phase"] = "DELIVERY_PREPARATION"
status["phase_gates"].update(
    {
        "INITIAL_READY": "READY",
        "CALABASH_UPGRADE_READY": "PASS",
        "ALL_REQUIRED_RUNS_ACCEPTED": "ALL_REQUIRED_RUNS_ACCEPTED",
        "DELIVERY_READY": "DELIVERY_READY",
    }
)
status["product_baseline"] = "ACCEPTED"
status["canonical_candidate"] = {
    "repository": "owner/project",
    "version": "1.0.1",
    "commit": "b" * 40,
    "candidate_id": "CANDIDATE-2",
    "candidate_hash": "sha256:" + "b" * 64,
}
status["vulnerability_closure"] = {
    "state": "VULNERABILITY_CLOSED",
    "candidate_id": "CANDIDATE-1",
    "candidate_hash": CANDIDATE_HASH,
    "current_receipt_id": "VC-270",
    "current_receipt_reference": "VULNERABILITY-CLOSURE.json",
    "superseded_receipt_id": "NOT_APPLICABLE",
    "superseded_receipt_reference": "NOT_APPLICABLE",
    "superseded_candidate_id": "NOT_APPLICABLE",
    "superseded_candidate_hash": "NOT_APPLICABLE",
}
status["post_security_owner_acceptance"] = {
    "state": "POST_SECURITY_OWNER_ACCEPTED",
    "candidate_id": "CANDIDATE-1",
    "candidate_hash": CANDIDATE_HASH,
    "current_acceptance_id": "PSOA-1",
    "current_acceptance_reference": "POST-SECURITY-OWNER-ACCEPTANCE.md",
    "vulnerability_closure_receipt_id": "VC-270",
    "vulnerability_closure_receipt_reference": "VULNERABILITY-CLOSURE.json",
    "superseded_acceptance_id": "NOT_APPLICABLE",
    "superseded_acceptance_reference": "NOT_APPLICABLE",
    "superseded_candidate_id": "NOT_APPLICABLE",
    "superseded_candidate_hash": "NOT_APPLICABLE",
}
status["last_material_change"] = "IA-SEC-1 / IMPACT-ANALYSIS.md"
phase_status["current_phase"] = "DELIVERY_PREPARATION"
phase_status["phases"]["INITIAL"].update({"status": "COMPLETE", "exit_gate": "READY"})
phase_status["phases"]["PRODUCT_FORMATION"].update(
    {"status": "COMPLETE", "exit_evidence": "ACCEPTED"}
)
phase_status["phases"]["REAL_PRODUCT_INTEGRATION"].update(
    {"status": "COMPLETE", "aggregate_exit_gate": "ALL_REQUIRED_RUNS_ACCEPTED"}
)
phase_status["phases"]["DELIVERY_PREPARATION"].update(
    {"status": "ACTIVE", "exit_gate": "DELIVERY_READY"}
)
authority_errors = project_validator.validate_status_authority(status, phase_status, health)
assert any("security" in error.lower() for error in authority_errors), (
    "post-closure material candidate change left closure, Owner acceptance, and "
    "DELIVERY_READY green: " + repr(authority_errors)
)


CURRENT_ID = "CANDIDATE-2"
CURRENT_HASH = "sha256:" + "b" * 64
MATERIAL_CATEGORIES = (
    "PRODUCT_BEHAVIOR",
    "DEPENDENCIES_SUPPLY_CHAIN",
    "CONFIGURATION",
    "AUTHENTICATION_AUTHORIZATION",
    "PRIVILEGE_BOUNDARIES",
    "DATA_HANDLING_ISOLATION",
    "API_EXPOSURE",
    "CLIENT_EXPOSURE",
    "INSTALLER_RUNTIME",
    "MIGRATION_RECOVERY_LOGGING_OBSERVABILITY",
    "OTHER_DECLARED_SECURITY_SURFACE",
)


def markdown_fields(fields):
    return "# Evidence\n\n" + "\n".join(f"- {key}: {value}" for key, value in fields.items()) + "\n"


def post_receipt(
    candidate_id=CANDIDATE_ID,
    candidate_hash=CANDIDATE_HASH,
    supersession="CURRENT",
):
    all_surfaces = "+".join(SURFACES)
    return {
        "Schema version": "2.7.0",
        "Artifact role": "POST_SECURITY_OWNER_ACCEPTANCE_RECEIPT",
        "Acceptance ID": "PSOA-1",
        "Candidate ID / exact hash": f"{candidate_id} / {candidate_hash}",
        "Vulnerability Closure Receipt ID / reference": "VC-270 / VULNERABILITY-CLOSURE.json",
        "Vulnerability Closure candidate ID / exact hash": f"{candidate_id} / {candidate_hash}",
        "Covered remediation surface IDs": "SURFACE-AUTH",
        "Changed remediation surface IDs": "SURFACE-AUTH",
        "Reused Loop Owner Acceptance Receipt IDs": (
            f"OA-PRE-1@{candidate_id}@{candidate_hash}@{all_surfaces}"
        ),
        "Security Remediation Run IDs": (
            f"SEC-RUN-1@{candidate_id}@{candidate_hash}@SURFACE-AUTH@E-REMEDIATION-1"
        ),
        "Critical smoke / delta evidence": (
            f"E-AUTH-CHECK@{candidate_id}@{candidate_hash}@SURFACE-AUTH"
        ),
        "Owner result": "POST_SECURITY_OWNER_ACCEPTED",
        "Supersession status": supersession,
        "Superseded by Acceptance ID / reference": "NOT_APPLICABLE",
        "Accepted at": "2026-08-12T00:30:00Z",
    }


def impact_fields(
    classification,
    *,
    timing="AFTER_POST_SECURITY_OWNER_ACCEPTED",
    category="API_EXPOSURE",
    prior_id=CANDIDATE_ID,
    prior_hash=CANDIDATE_HASH,
    current_id=CURRENT_ID,
    current_hash=CURRENT_HASH,
):
    material = classification == "MATERIAL_SECURITY_SURFACE_CHANGE"
    neutral = classification == "PROVEN_SECURITY_SURFACE_NEUTRAL"
    packaging = classification == "EVIDENCE_EQUIVALENT_PACKAGING_TRANSFORMATION"
    if material:
        categories = category
        affected = "SURFACE-API"
        transitive = f"SURFACE-DATA@{current_id}@{current_hash}@E-TRANSITIVE-DATA"
        preservation = "NOT_APPLICABLE"
        invalidation = "E-SECURITY-INVALIDATION-1"
        action = "INVALIDATE_AND_RETURN_TO_AUDIT"
    elif neutral:
        categories = affected = transitive = "NONE"
        preservation = (
            f"MODE@NEUTRAL;EVIDENCE@E-SECURITY-NEUTRAL-1;"
            f"PRIOR@{prior_id}@{prior_hash};CURRENT@{current_id}@{current_hash}"
        )
        invalidation = "NOT_APPLICABLE"
        action = "PRESERVE_EXACT_CLOSURE"
    elif packaging:
        categories = affected = transitive = "NONE"
        preservation = (
            f"MODE@PACKAGING_EQUIVALENCE;TRANSFORMATION@E-PACKAGE-TRANSFORM-1;"
            f"SECURITY_EQUIVALENCE@E-SECURITY-EQUIVALENCE-1;"
            f"PRIOR@{prior_id}@{prior_hash};CURRENT@{current_id}@{current_hash}"
        )
        invalidation = "NOT_APPLICABLE"
        action = "PRESERVE_EXACT_CLOSURE"
    else:
        categories = affected = transitive = "NONE"
        preservation = invalidation = "NOT_APPLICABLE"
        action = "PRESERVE_EXACT_CLOSURE"
    return {
        "Analysis ID / version": "IA-SEC-1 / 1.0.0",
        "Trigger / proposed change": "post-closure candidate change",
        "Artifact role": "IMPACT_ANALYSIS",
        "Meaning impact classification": "MEANING_NEUTRAL",
        "Calling phase contract / authority": "DELIVERY_PREPARATION / LC-SECURITY-001",
        "Neutral rationale / evidence": "E-MEANING-NEUTRAL-1",
        "Definition Baseline ID / exact hash": "NONE",
        "Affected Definition clause references": "NONE",
        "Definition invalidation effect": "NO_DEFINITION_INVALIDATION",
        "Governed Calabash update route / Owner authority": "NOT_APPLICABLE",
        "Snake / Scorpion applicability and effect references": "CALABASH-UPGRADE-GATE.md",
        "Security change timing": timing,
        "Prior candidate ID / exact hash": f"{prior_id} / {prior_hash}",
        "Current candidate ID / exact hash": f"{current_id} / {current_hash}",
        "Security change classification": classification,
        "Changed security surface categories": categories,
        "Affected security surface IDs": affected,
        "Transitive affected surface IDs / evidence": transitive,
        "Prior Vulnerability Closure Receipt ID / reference": "VC-270 / VULNERABILITY-CLOSURE.json",
        "Prior Post-Security Owner Acceptance ID / reference": (
            "NOT_APPLICABLE"
            if timing == "AFTER_VULNERABILITY_CLOSED"
            else "PSOA-1 / POST-SECURITY-OWNER-ACCEPTANCE.md"
        ),
        "Security neutral / preservation evidence": preservation,
        "Security invalidation evidence": invalidation,
        "Required security action": action,
        "Impact result": "PASS",
    }


def security_record(state, candidate_id, candidate_hash, *, invalid=False):
    if invalid:
        return {
            "state": "INVALID",
            "candidate_id": candidate_id,
            "candidate_hash": candidate_hash,
            "current_receipt_id": "NOT_APPLICABLE",
            "current_receipt_reference": "NOT_APPLICABLE",
            "superseded_receipt_id": "VC-270",
            "superseded_receipt_reference": "VULNERABILITY-CLOSURE.json",
            "superseded_candidate_id": CANDIDATE_ID,
            "superseded_candidate_hash": CANDIDATE_HASH,
        }
    return {
        "state": state,
        "candidate_id": candidate_id,
        "candidate_hash": candidate_hash,
        "current_receipt_id": "VC-270",
        "current_receipt_reference": "VULNERABILITY-CLOSURE.json",
        "superseded_receipt_id": "NOT_APPLICABLE",
        "superseded_receipt_reference": "NOT_APPLICABLE",
        "superseded_candidate_id": "NOT_APPLICABLE",
        "superseded_candidate_hash": "NOT_APPLICABLE",
    }


def owner_security_record(state, candidate_id, candidate_hash, *, invalid=False, prior=True):
    if invalid:
        return {
            "state": "INVALID",
            "candidate_id": candidate_id,
            "candidate_hash": candidate_hash,
            "current_acceptance_id": "NOT_APPLICABLE",
            "current_acceptance_reference": "NOT_APPLICABLE",
            "vulnerability_closure_receipt_id": "NOT_APPLICABLE",
            "vulnerability_closure_receipt_reference": "NOT_APPLICABLE",
            "superseded_acceptance_id": "PSOA-1" if prior else "NOT_APPLICABLE",
            "superseded_acceptance_reference": (
                "POST-SECURITY-OWNER-ACCEPTANCE.md" if prior else "NOT_APPLICABLE"
            ),
            "superseded_candidate_id": CANDIDATE_ID if prior else "NOT_APPLICABLE",
            "superseded_candidate_hash": CANDIDATE_HASH if prior else "NOT_APPLICABLE",
        }
    return {
        "state": state,
        "candidate_id": candidate_id,
        "candidate_hash": candidate_hash,
        "current_acceptance_id": "PSOA-1",
        "current_acceptance_reference": "POST-SECURITY-OWNER-ACCEPTANCE.md",
        "vulnerability_closure_receipt_id": "VC-270",
        "vulnerability_closure_receipt_reference": "VULNERABILITY-CLOSURE.json",
        "superseded_acceptance_id": "NOT_APPLICABLE",
        "superseded_acceptance_reference": "NOT_APPLICABLE",
        "superseded_candidate_id": "NOT_APPLICABLE",
        "superseded_candidate_hash": "NOT_APPLICABLE",
    }


def security_status(candidate_id, candidate_hash, *, invalid=False, prior_acceptance=True):
    item = json.loads((root / "lc-coding/templates/STATUS.json").read_text(encoding="utf-8"))
    item["canonical_candidate"] = {
        "repository": "owner/project",
        "version": "1.0.1",
        "commit": "b" * 40,
        "candidate_id": candidate_id,
        "candidate_hash": candidate_hash,
    }
    item["vulnerability_closure"] = security_record(
        "VULNERABILITY_CLOSED", candidate_id, candidate_hash, invalid=invalid
    )
    item["post_security_owner_acceptance"] = owner_security_record(
        "POST_SECURITY_OWNER_ACCEPTED", candidate_id, candidate_hash,
        invalid=invalid, prior=prior_acceptance,
    )
    item["phase_gates"]["DELIVERY_READY"] = "INVALID" if invalid else "DELIVERY_READY"
    if invalid:
        item["last_material_change"] = "IA-SEC-1 / IMPACT-ANALYSIS.md"
        pointers = ["IMPACT-ANALYSIS.md", "VULNERABILITY-CLOSURE.json"]
        if prior_acceptance:
            pointers.append("POST-SECURITY-OWNER-ACCEPTANCE.md")
        item["evidence_pointers"] = pointers
        item["blockers"] = ["SECURITY_EVIDENCE_INVALIDATED:IA-SEC-1"]
        item["next_action"] = (
            "FRESH_INDEPENDENT_SECURITY_REAUDIT_THEN_NEW_CLOSURE_"
            "THEN_FOCUSED_POST_SECURITY_OWNER_ACCEPTANCE"
        )
    else:
        item["last_material_change"] = ""
        item["evidence_pointers"] = [
            "VULNERABILITY-CLOSURE.json",
            "POST-SECURITY-OWNER-ACCEPTANCE.md",
        ]
        item["blockers"] = []
        item["next_action"] = ""
    return item


def write_security_fixture(lc, impact, post=None, receipt=None):
    lc.mkdir(parents=True, exist_ok=True)
    receipt_data = valid_receipt() if receipt is None else receipt
    closure_path = lc / "VULNERABILITY-CLOSURE.json"
    closure_path.write_text(
        json.dumps(receipt_data, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    if impact is not None:
        (lc / "IMPACT-ANALYSIS.md").write_text(markdown_fields(impact), encoding="utf-8")
    elif (lc / "IMPACT-ANALYSIS.md").exists():
        (lc / "IMPACT-ANALYSIS.md").unlink()
    if post is not None:
        (lc / "POST-SECURITY-OWNER-ACCEPTANCE.md").write_text(
            markdown_fields(post), encoding="utf-8"
        )
    elif (lc / "POST-SECURITY-OWNER-ACCEPTANCE.md").exists():
        (lc / "POST-SECURITY-OWNER-ACCEPTANCE.md").unlink()
    return closure_path


def validate_security_unchanged(lc, item):
    before = {path: path.read_bytes() for path in lc.rglob("*") if path.is_file()}
    errors = project_validator.validate_security_invalidation(lc, item)
    after = {path: path.read_bytes() for path in lc.rglob("*") if path.is_file()}
    assert after == before, "security validation modified immutable evidence bytes"
    return errors


# An untouched template is a legal not-started record. Its placeholder option
# strings do not create a security decision while authoritative security state
# is PENDING and last_material_change is empty.
with tempfile.TemporaryDirectory(prefix="lccoding-security-unstarted-270-") as temporary:
    unstarted_lc = Path(temporary) / ".lccoding"
    unstarted_lc.mkdir()
    (unstarted_lc / "IMPACT-ANALYSIS.md").write_bytes(
        (root / "lc-coding/templates/IMPACT-ANALYSIS.md").read_bytes()
    )
    unstarted_status = json.loads(
        (root / "lc-coding/templates/STATUS.json").read_text(encoding="utf-8")
    )
    assert project_validator.validate_security_invalidation(
        unstarted_lc, unstarted_status
    ) == [], "untouched Impact template activated security validation"


with tempfile.TemporaryDirectory(prefix="lccoding-security-invalidation-270-") as temporary:
    lc = Path(temporary) / ".lccoding"
    current_post = post_receipt()

    # A closed candidate with exact current receipts remains valid.
    write_security_fixture(lc, None, current_post)
    current = security_status(CANDIDATE_ID, CANDIDATE_HASH)
    assert validate_security_unchanged(lc, current) == []

    completed_without_security_delta = impact_fields(
        "PROVEN_SECURITY_SURFACE_NEUTRAL",
        prior_id=CANDIDATE_ID,
        prior_hash=CANDIDATE_HASH,
        current_id=CANDIDATE_ID,
        current_hash=CANDIDATE_HASH,
    )
    for security_field in project_validator.SECURITY_IMPACT_FIELDS:
        completed_without_security_delta.pop(security_field)
    write_security_fixture(lc, completed_without_security_delta, current_post)
    assert validate_security_unchanged(lc, current), (
        "started completed Impact escaped by deleting the entire security delta group"
    )
    write_security_fixture(lc, None, current_post)

    focused_post = copy.deepcopy(current_post)
    focused_post["Covered remediation surface IDs"] = "SURFACE-AUTH"
    write_security_fixture(lc, None, focused_post)
    assert validate_security_unchanged(lc, current) == [], (
        "focused Post-Security acceptance was expanded to every audit surface"
    )

    no_remediation_receipt = valid_receipt()
    no_remediation_receipt["findings"] = []
    no_remediation_receipt["remediation_runs"] = []
    no_remediation_receipt["affected_receipts"] = []
    no_remediation_post = copy.deepcopy(current_post)
    no_remediation_post["Covered remediation surface IDs"] = "NONE"
    no_remediation_post["Changed remediation surface IDs"] = "NONE"
    no_remediation_post["Security Remediation Run IDs"] = "NONE"
    write_security_fixture(lc, None, no_remediation_post, no_remediation_receipt)
    assert validate_security_unchanged(lc, current) == [], (
        "no-remediation closure could not express a closed NONE focused scope"
    )
    write_security_fixture(lc, None, current_post)

    independent_review_bypasses = []
    superseded_current_post = copy.deepcopy(current_post)
    superseded_current_post["Supersession status"] = "SUPERSEDED"
    superseded_current_post[
        "Superseded by Acceptance ID / reference"
    ] = "PSOA-2 / MISSING-NEXT.md"
    write_security_fixture(lc, None, superseded_current_post)
    if not validate_security_unchanged(lc, current):
        independent_review_bypasses.append("SUPERSEDED_RECEIPT_USED_AS_CURRENT")

    blocked_neutral_impact = impact_fields(
        "PROVEN_SECURITY_SURFACE_NEUTRAL",
        prior_id=CANDIDATE_ID,
        prior_hash=CANDIDATE_HASH,
        current_id=CANDIDATE_ID,
        current_hash=CANDIDATE_HASH,
    )
    blocked_neutral_impact["Impact result"] = "BLOCKED"
    blocked_neutral_status = security_status(CANDIDATE_ID, CANDIDATE_HASH)
    blocked_neutral_status["last_material_change"] = "IA-SEC-1 / IMPACT-ANALYSIS.md"
    blocked_neutral_status["evidence_pointers"].insert(0, "IMPACT-ANALYSIS.md")
    blocked_neutral_status["next_action"] = "PRESERVE_EXACT_SECURITY_CLOSURE"
    write_security_fixture(lc, blocked_neutral_impact, current_post)
    if not validate_security_unchanged(lc, blocked_neutral_status):
        independent_review_bypasses.append("BLOCKED_IMPACT_PRESERVED_SECURITY")

    fake_post = copy.deepcopy(current_post)
    fake_post["Covered remediation surface IDs"] = "SURFACE-AUTH"
    fake_post["Reused Loop Owner Acceptance Receipt IDs"] = "FAKE-OWNER"
    fake_post["Security Remediation Run IDs"] = "FAKE-RUN"
    fake_post["Critical smoke / delta evidence"] = "FAKE-SMOKE"
    write_security_fixture(lc, None, fake_post)
    if not validate_security_unchanged(lc, current):
        independent_review_bypasses.append("UNBOUND_POST_SECURITY_EVIDENCE")

    silent_security_delta = impact_fields("PROVEN_SECURITY_SURFACE_NEUTRAL")
    silent_security_delta.update(
        {
            "Security change timing": (
                "BEFORE_SECURITY_CLOSURE / AFTER_VULNERABILITY_CLOSED / "
                "AFTER_POST_SECURITY_OWNER_ACCEPTED"
            ),
            "Prior candidate ID / exact hash": "",
            "Current candidate ID / exact hash": "",
            "Security change classification": (
                "MATERIAL_SECURITY_SURFACE_CHANGE / PROVEN_SECURITY_SURFACE_NEUTRAL / "
                "EVIDENCE_EQUIVALENT_PACKAGING_TRANSFORMATION"
            ),
            "Required security action": (
                "PRESERVE_EXACT_CLOSURE / INVALIDATE_AND_RETURN_TO_AUDIT"
            ),
        }
    )
    silent_record, silent_errors = project_validator.validate_security_impact_fields(
        silent_security_delta
    )
    if silent_record is None and not silent_errors:
        independent_review_bypasses.append("COMPLETED_IMPACT_SKIPPED_SECURITY_DELTA")

    assert not independent_review_bypasses, (
        "Task13 accepted independent review bypasses: "
        + ", ".join(independent_review_bypasses)
    )
    write_security_fixture(lc, None, current_post)
    ambiguous_current = copy.deepcopy(current)
    ambiguous_current["vulnerability_closure"].update(
        {
            "superseded_receipt_id": "VC-OLD",
            "superseded_receipt_reference": "VULNERABILITY-CLOSURE.json",
            "superseded_candidate_id": CANDIDATE_ID,
            "superseded_candidate_hash": CANDIDATE_HASH,
        }
    )
    assert validate_security_unchanged(lc, ambiguous_current), (
        "current closure also claimed a superseded receipt"
    )
    pending_claim = json.loads(
        (root / "lc-coding/templates/STATUS.json").read_text(encoding="utf-8")
    )
    pending_claim["vulnerability_closure"]["current_receipt_id"] = "VC-270"
    pending_claim["vulnerability_closure"][
        "current_receipt_reference"
    ] = "VULNERABILITY-CLOSURE.json"
    assert project_validator.validate_security_status_shape(pending_claim), (
        "pending security status claimed a current receipt"
    )
    before_owner_acceptance = copy.deepcopy(current)
    before_owner_acceptance["post_security_owner_acceptance"] = copy.deepcopy(
        pending_claim["post_security_owner_acceptance"]
    )
    before_owner_acceptance["phase_gates"]["DELIVERY_READY"] = "PENDING"
    before_owner_acceptance["evidence_pointers"] = ["VULNERABILITY-CLOSURE.json"]
    (lc / "POST-SECURITY-OWNER-ACCEPTANCE.md").unlink()
    assert validate_security_unchanged(lc, before_owner_acceptance) == []
    (lc / "POST-SECURITY-OWNER-ACCEPTANCE.md").write_text(
        markdown_fields(current_post), encoding="utf-8"
    )

    # Material changes after either closure boundary require all three outcomes
    # to become INVALID and preserve the exact superseded evidence references.
    material = impact_fields("MATERIAL_SECURITY_SURFACE_CHANGE")
    write_security_fixture(lc, material, current_post)
    invalid = security_status(CURRENT_ID, CURRENT_HASH, invalid=True)
    assert validate_security_unchanged(lc, invalid) == []
    blocked_material = copy.deepcopy(material)
    blocked_material["Impact result"] = "BLOCKED"
    write_security_fixture(lc, blocked_material, current_post)
    assert validate_security_unchanged(lc, invalid) == [], (
        "material BLOCKED Impact must retain fail-closed INVALID status"
    )
    before_acceptance_impact = impact_fields(
        "MATERIAL_SECURITY_SURFACE_CHANGE",
        timing="AFTER_VULNERABILITY_CLOSED",
    )
    write_security_fixture(lc, before_acceptance_impact, None)
    invalid_before_acceptance = security_status(
        CURRENT_ID, CURRENT_HASH, invalid=True, prior_acceptance=False
    )
    assert validate_security_unchanged(lc, invalid_before_acceptance) == []

    # Every material surface category must reject silent green preservation.
    stale_green = security_status(CURRENT_ID, CURRENT_HASH)
    for material_category in MATERIAL_CATEGORIES:
        write_security_fixture(
            lc,
            impact_fields(
                "MATERIAL_SECURITY_SURFACE_CHANGE", category=material_category
            ),
            current_post,
        )
        assert validate_security_unchanged(lc, stale_green), material_category

    write_security_fixture(lc, material, current_post)
    for field in ("vulnerability_closure", "post_security_owner_acceptance"):
        partial = copy.deepcopy(invalid)
        partial[field] = copy.deepcopy(stale_green[field])
        assert validate_security_unchanged(lc, partial), field
    partial_gate = copy.deepcopy(invalid)
    partial_gate["phase_gates"]["DELIVERY_READY"] = "DELIVERY_READY"
    assert validate_security_unchanged(lc, partial_gate)
    green_with_superseded_history = copy.deepcopy(invalid)
    green_with_superseded_history["vulnerability_closure"].update(
        {
            "state": "VULNERABILITY_CLOSED",
            "current_receipt_id": "VC-270",
            "current_receipt_reference": "VULNERABILITY-CLOSURE.json",
        }
    )
    green_with_superseded_history["post_security_owner_acceptance"].update(
        {
            "state": "POST_SECURITY_OWNER_ACCEPTED",
            "current_acceptance_id": "PSOA-1",
            "current_acceptance_reference": "POST-SECURITY-OWNER-ACCEPTANCE.md",
            "vulnerability_closure_receipt_id": "VC-270",
            "vulnerability_closure_receipt_reference": "VULNERABILITY-CLOSURE.json",
        }
    )
    green_with_superseded_history["phase_gates"]["DELIVERY_READY"] = "DELIVERY_READY"
    assert validate_security_unchanged(lc, green_with_superseded_history), (
        "material change preserved all three green outcomes by retaining superseded pointers"
    )

    # Impact identity, surface sets, transitive binding and superseded evidence
    # are all exact and cannot be replaced by generic/duplicate/current facts.
    def impact_mutation(mutator):
        changed = impact_fields("MATERIAL_SECURITY_SURFACE_CHANGE")
        mutator(changed)
        write_security_fixture(lc, changed, current_post)
        return validate_security_unchanged(lc, invalid)

    assert impact_mutation(lambda item: item.__setitem__("Security invalidation evidence", "PASS"))
    assert impact_mutation(lambda item: item.__setitem__("Changed security surface categories", "API_EXPOSURE, API_EXPOSURE"))
    assert impact_mutation(lambda item: item.__setitem__("Changed security surface categories", "UNKNOWN_SURFACE"))
    assert impact_mutation(lambda item: item.__setitem__("Affected security surface IDs", "SURFACE-API, SURFACE-API"))
    assert impact_mutation(lambda item: item.__setitem__("Transitive affected surface IDs / evidence", f"SURFACE-DATA@{CANDIDATE_ID}@{CANDIDATE_HASH}@E-WRONG"))
    assert impact_mutation(lambda item: item.pop("Security change classification"))
    assert impact_mutation(lambda item: item.__setitem__("Prior Vulnerability Closure Receipt ID / reference", "VC-270 / ../escape.json"))
    generic_candidate_impact = impact_fields("MATERIAL_SECURITY_SURFACE_CHANGE")
    generic_candidate_impact["Current candidate ID / exact hash"] = (
        "PASS / " + CURRENT_HASH
    )
    generic_candidate_impact["Transitive affected surface IDs / evidence"] = (
        "SURFACE-DATA@PASS@" + CURRENT_HASH + "@E-TRANSITIVE-DATA"
    )
    write_security_fixture(lc, generic_candidate_impact, current_post)
    generic_candidate_status = copy.deepcopy(invalid)
    generic_candidate_status["canonical_candidate"]["candidate_id"] = "PASS"
    generic_candidate_status["vulnerability_closure"]["candidate_id"] = "PASS"
    generic_candidate_status["post_security_owner_acceptance"]["candidate_id"] = "PASS"
    assert validate_security_unchanged(lc, generic_candidate_status), (
        "generic candidate ID was accepted as current security identity"
    )

    wrong_change = copy.deepcopy(invalid)
    wrong_change["last_material_change"] = "IA-WRONG / IMPACT-ANALYSIS.md"
    assert validate_security_unchanged(lc, wrong_change)
    no_prior_closure = copy.deepcopy(invalid)
    no_prior_closure["vulnerability_closure"]["superseded_receipt_id"] = "NOT_APPLICABLE"
    assert validate_security_unchanged(lc, no_prior_closure)
    wrong_prior_candidate = copy.deepcopy(invalid)
    wrong_prior_candidate["vulnerability_closure"]["superseded_candidate_id"] = CURRENT_ID
    wrong_prior_candidate["vulnerability_closure"]["superseded_candidate_hash"] = CURRENT_HASH
    assert validate_security_unchanged(lc, wrong_prior_candidate)
    current_substitution = copy.deepcopy(invalid)
    current_substitution["vulnerability_closure"]["current_receipt_id"] = "VC-270"
    current_substitution["vulnerability_closure"]["current_receipt_reference"] = "VULNERABILITY-CLOSURE.json"
    assert validate_security_unchanged(lc, current_substitution)
    no_prior_acceptance = copy.deepcopy(invalid)
    no_prior_acceptance["post_security_owner_acceptance"]["superseded_acceptance_id"] = "NOT_APPLICABLE"
    no_prior_acceptance["post_security_owner_acceptance"]["superseded_acceptance_reference"] = "NOT_APPLICABLE"
    assert validate_security_unchanged(lc, no_prior_acceptance)

    # Deleted or byte-altered prior evidence cannot be silently substituted.
    closure_path = lc / "VULNERABILITY-CLOSURE.json"
    original_closure = closure_path.read_bytes()
    closure_path.unlink()
    assert validate_security_unchanged(lc, invalid)
    closure_path.write_bytes(original_closure.replace(b'"VC-270"', b'"VC-OLD"'))
    assert validate_security_unchanged(lc, invalid)
    closure_path.write_bytes(original_closure)

    # Explicit neutral preservation requires unchanged security identity and NONE
    # surfaces. Packaging preservation requires both exact evidence records.
    neutral_impact = impact_fields(
        "PROVEN_SECURITY_SURFACE_NEUTRAL",
        prior_id=CANDIDATE_ID,
        prior_hash=CANDIDATE_HASH,
        current_id=CANDIDATE_ID,
        current_hash=CANDIDATE_HASH,
    )
    write_security_fixture(lc, neutral_impact, current_post)
    neutral = security_status(CANDIDATE_ID, CANDIDATE_HASH)
    neutral["last_material_change"] = "IA-SEC-1 / IMPACT-ANALYSIS.md"
    neutral["evidence_pointers"].insert(0, "IMPACT-ANALYSIS.md")
    neutral["next_action"] = "PRESERVE_EXACT_SECURITY_CLOSURE"
    assert validate_security_unchanged(lc, neutral) == []
    for result in ("BLOCKED", "PENDING"):
        denied_preservation = copy.deepcopy(neutral_impact)
        denied_preservation["Impact result"] = result
        write_security_fixture(lc, denied_preservation, current_post)
        assert validate_security_unchanged(lc, neutral), result
    assert impact_mutation(lambda item: item.__setitem__("Security change classification", "PROVEN_SECURITY_SURFACE_NEUTRAL"))
    bad_neutral = copy.deepcopy(neutral_impact)
    bad_neutral["Affected security surface IDs"] = "SURFACE-API"
    write_security_fixture(lc, bad_neutral, current_post)
    assert validate_security_unchanged(lc, neutral)
    bad_neutral = copy.deepcopy(neutral_impact)
    bad_neutral["Security neutral / preservation evidence"] = "PASS"
    write_security_fixture(lc, bad_neutral, current_post)
    assert validate_security_unchanged(lc, neutral)

    packaging_impact = impact_fields("EVIDENCE_EQUIVALENT_PACKAGING_TRANSFORMATION")
    write_security_fixture(lc, packaging_impact, current_post)
    packaging = security_status(CURRENT_ID, CURRENT_HASH)
    packaging["last_material_change"] = "IA-SEC-1 / IMPACT-ANALYSIS.md"
    packaging["evidence_pointers"].insert(0, "IMPACT-ANALYSIS.md")
    packaging["next_action"] = "PRESERVE_EXACT_SECURITY_CLOSURE"
    assert validate_security_unchanged(lc, packaging) == []
    for fragment in ("TRANSFORMATION@E-PACKAGE-TRANSFORM-1", "SECURITY_EQUIVALENCE@E-SECURITY-EQUIVALENCE-1"):
        broken = copy.deepcopy(packaging_impact)
        broken["Security neutral / preservation evidence"] = broken[
            "Security neutral / preservation evidence"
        ].replace(fragment + ";", "")
        write_security_fixture(lc, broken, current_post)
        assert validate_security_unchanged(lc, packaging)

    # Post-Security receipt is a closed candidate-bound terminal receipt.
    write_security_fixture(lc, None, current_post)
    current_with_pointer = copy.deepcopy(current_post)
    current_with_pointer[
        "Superseded by Acceptance ID / reference"
    ] = "PSOA-2 / MISSING-NEXT.md"
    (lc / "POST-SECURITY-OWNER-ACCEPTANCE.md").write_text(
        markdown_fields(current_with_pointer), encoding="utf-8"
    )
    assert validate_security_unchanged(lc, current)
    superseded_with_missing_next = copy.deepcopy(current_post)
    superseded_with_missing_next["Supersession status"] = "SUPERSEDED"
    superseded_with_missing_next[
        "Superseded by Acceptance ID / reference"
    ] = "PSOA-2 / MISSING-NEXT.md"
    (lc / "POST-SECURITY-OWNER-ACCEPTANCE.md").write_text(
        markdown_fields(superseded_with_missing_next), encoding="utf-8"
    )
    assert validate_security_unchanged(lc, current)
    bad_post = copy.deepcopy(current_post)
    bad_post["Candidate ID / exact hash"] = f"{CURRENT_ID} / {CURRENT_HASH}"
    (lc / "POST-SECURITY-OWNER-ACCEPTANCE.md").write_text(markdown_fields(bad_post), encoding="utf-8")
    assert validate_security_unchanged(lc, current)
    bad_post = copy.deepcopy(current_post)
    bad_post["Unexpected field"] = "E-UNEXPECTED"
    (lc / "POST-SECURITY-OWNER-ACCEPTANCE.md").write_text(markdown_fields(bad_post), encoding="utf-8")
    assert validate_security_unchanged(lc, current)
    duplicated = markdown_fields(current_post) + "- Acceptance ID: PSOA-SHADOW\n"
    (lc / "POST-SECURITY-OWNER-ACCEPTANCE.md").write_text(duplicated, encoding="utf-8")
    assert validate_security_unchanged(lc, current)
    generic_post = copy.deepcopy(current_post)
    generic_post["Critical smoke / delta evidence"] = "PASS"
    (lc / "POST-SECURITY-OWNER-ACCEPTANCE.md").write_text(
        markdown_fields(generic_post), encoding="utf-8"
    )
    assert validate_security_unchanged(lc, current), (
        "generic Post-Security evidence ID was accepted"
    )
    unknown_surface_post = copy.deepcopy(current_post)
    unknown_surface_post["Covered remediation surface IDs"] += ", SURFACE-MISSING"
    unknown_surface_post["Changed remediation surface IDs"] += ", SURFACE-MISSING"
    (lc / "POST-SECURITY-OWNER-ACCEPTANCE.md").write_text(
        markdown_fields(unknown_surface_post), encoding="utf-8"
    )
    assert validate_security_unchanged(lc, current), (
        "Post-Security receipt claimed a surface absent from Vulnerability Closure"
    )
    focused_undercoverage = copy.deepcopy(current_post)
    focused_undercoverage["Covered remediation surface IDs"] = "NONE"
    (lc / "POST-SECURITY-OWNER-ACCEPTANCE.md").write_text(
        markdown_fields(focused_undercoverage), encoding="utf-8"
    )
    assert validate_security_unchanged(lc, current)
    focused_overclaim = copy.deepcopy(current_post)
    focused_overclaim[
        "Covered remediation surface IDs"
    ] = "SURFACE-AUTH, SURFACE-API"
    (lc / "POST-SECURITY-OWNER-ACCEPTANCE.md").write_text(
        markdown_fields(focused_overclaim), encoding="utf-8"
    )
    assert validate_security_unchanged(lc, current)
    critical_undercoverage = copy.deepcopy(focused_post)
    critical_undercoverage["Critical smoke / delta evidence"] = (
        f"E-API-CHECK@{CANDIDATE_ID}@{CANDIDATE_HASH}@SURFACE-API"
    )
    (lc / "POST-SECURITY-OWNER-ACCEPTANCE.md").write_text(
        markdown_fields(critical_undercoverage), encoding="utf-8"
    )
    assert validate_security_unchanged(lc, current)
    for field,old,new in (
        (
            "Reused Loop Owner Acceptance Receipt IDs",
            f"@{CANDIDATE_ID}@{CANDIDATE_HASH}@",
            f"@{CURRENT_ID}@{CURRENT_HASH}@",
        ),
        (
            "Reused Loop Owner Acceptance Receipt IDs",
            "+SURFACE-INSTALLER",
            "",
        ),
        (
            "Security Remediation Run IDs",
            "@E-REMEDIATION-1",
            "@E-WRONG-REMEDIATION",
        ),
        (
            "Critical smoke / delta evidence",
            "E-AUTH-CHECK",
            "E-MISSING-CHECK",
        ),
    ):
        drifted_post = copy.deepcopy(current_post)
        drifted_post[field] = drifted_post[field].replace(old, new)
        (lc / "POST-SECURITY-OWNER-ACCEPTANCE.md").write_text(
            markdown_fields(drifted_post), encoding="utf-8"
        )
        assert validate_security_unchanged(lc, current), (field, old, new)

    # A second invalidation/status authority or runtime/session record fails.
    write_security_fixture(lc, material, current_post)
    second_ledger = copy.deepcopy(invalid)
    second_ledger["security_invalidation_ledger"] = []
    assert validate_security_unchanged(lc, second_ledger)
    runtime_status = copy.deepcopy(invalid)
    runtime_status["session_id"] = "RUNTIME-SESSION"
    assert validate_security_unchanged(lc, runtime_status)

    # Task 14 RED: a Delivery Decision for the changed candidate must not pass
    # while its closure and Post-Security receipts still belong to the prior
    # candidate. The legacy decision validator accepted this self-report.
    groups = [
        "delivery_model", "assets", "source_and_modification_rights",
        "runtime_and_infrastructure", "data", "internal_dependencies",
        "license", "operations",
    ]
    stale_decision = {
        "delivery_decision_id": "DD-STALE-1",
        "delivery_id": "DELIVERY-1",
        "customer": "Customer A",
        "candidate_id": f"{CURRENT_ID} / {CURRENT_HASH}",
        "owner_policy_version": "1.0.0",
        "locked_exclusions": json.loads(
            (root / "lc-coding/contracts/delivery-policy.json").read_text(
                encoding="utf-8"
            )
        )["owner_locked_default_exclusions"],
        "decisions": {
            group: {"selected": "customer-choice-" + group} for group in groups
        },
        "qa_status": "COMPLETE",
        "owner_confirmed": True,
        "confirmed_at": "2026-08-13T00:00:00Z",
    }
    stale_decision_path = lc / "DELIVERY-DECISION.json"
    stale_decision_path.write_text(json.dumps(stale_decision), encoding="utf-8")
    stale_delivery_status = copy.deepcopy(stale_green)
    stale_delivery_status["delivery_method_qa"] = "DELIVERY_METHOD_CONFIRMED"
    (lc / "status.json").write_text(
        json.dumps(stale_delivery_status), encoding="utf-8"
    )
    write_security_fixture(lc, material, current_post)
    stale_delivery_result = subprocess.run(
        [sys.executable, str(delivery_decision_validator), str(stale_decision_path)],
        capture_output=True, text=True,
    )
    assert stale_delivery_result.returncode != 0, (
        "Delivery Decision accepted stale prior-candidate security evidence: "
        + stale_delivery_result.stdout + stale_delivery_result.stderr
    )


# validate_project's formal path must invoke the Task-13 relationship validator.
# The minimal fixture may have unrelated bootstrap gaps, but the stale-security
# relationship must itself be reported by the CLI and cannot be skipped.
with tempfile.TemporaryDirectory(prefix="lccoding-security-project-entry-270-") as temporary:
    project = Path(temporary)
    lc = project / ".lccoding"
    lc.mkdir()
    (project / "VERSION").write_text("0.0.1\n", encoding="utf-8")
    for name in ("OWNER-POLICY.md", "PROJECT-PROFILE.md", "AGENT-RULE.md"):
        (lc / name).write_text("fixture\n", encoding="utf-8")
    (lc / "PROJECT-START.json").write_text(
        json.dumps({"initialization_mode": "NEW", "repository": "owner/project"}),
        encoding="utf-8",
    )
    for name in (
        "PROJECT-FINGERPRINT.json", "PROJECT-HEALTH.json",
        "CANONICAL-MANIFEST.json", "INTERPRETATION-LOCK.json",
        "WORKFLOW-MAP.md", "UI-MAP.md", "SIMULATION-WORLD.md", "PHASE-STATUS.json",
    ):
        source = root / "lc-coding/templates" / name
        (lc / name).write_bytes(source.read_bytes())
    (lc / "status.json").write_text(json.dumps(stale_green), encoding="utf-8")
    write_security_fixture(lc, material, current_post)
    formal = subprocess.run(
        [sys.executable, str(project_validator_path), str(project)],
        capture_output=True, text=True,
    )
    assert formal.returncode != 0
    assert "security" in formal.stdout.lower(), formal.stdout + formal.stderr

    incomplete_completed_impact = impact_fields("PROVEN_SECURITY_SURFACE_NEUTRAL")
    incomplete_completed_impact.update(
        {
            "Security change timing": (
                "BEFORE_SECURITY_CLOSURE / AFTER_VULNERABILITY_CLOSED / "
                "AFTER_POST_SECURITY_OWNER_ACCEPTED"
            ),
            "Prior candidate ID / exact hash": "",
            "Current candidate ID / exact hash": "",
            "Security change classification": (
                "MATERIAL_SECURITY_SURFACE_CHANGE / PROVEN_SECURITY_SURFACE_NEUTRAL / "
                "EVIDENCE_EQUIVALENT_PACKAGING_TRANSFORMATION"
            ),
            "Required security action": (
                "PRESERVE_EXACT_CLOSURE / INVALIDATE_AND_RETURN_TO_AUDIT"
            ),
        }
    )
    (lc / "status.json").write_text(
        json.dumps(blocked_neutral_status), encoding="utf-8"
    )
    write_security_fixture(lc, incomplete_completed_impact, current_post)
    formal_incomplete = subprocess.run(
        [sys.executable, str(project_validator_path), str(project)],
        capture_output=True, text=True,
    )
    assert formal_incomplete.returncode != 0
    assert "Security change timing is invalid" in formal_incomplete.stdout, (
        formal_incomplete.stdout + formal_incomplete.stderr
    )

    (lc / "status.json").write_text(json.dumps(current), encoding="utf-8")
    write_security_fixture(lc, completed_without_security_delta, current_post)
    formal_missing_group = subprocess.run(
        [sys.executable, str(project_validator_path), str(project)],
        capture_output=True, text=True,
    )
    assert formal_missing_group.returncode != 0
    assert "requires a closed security delta" in formal_missing_group.stdout, (
        formal_missing_group.stdout + formal_missing_group.stderr
    )

print("PASS: vulnerability closure is candidate- and surface-bound")
