from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile


root = Path(__file__).resolve().parents[2]
decision_validator = root / "lc-coding/scripts/validate_delivery_decision.py"
policy_path = root / "lc-coding/contracts/delivery-policy.json"
GROUPS = [
    "delivery_model", "assets", "source_and_modification_rights",
    "runtime_and_infrastructure", "data", "internal_dependencies",
    "license", "operations",
]
CANDIDATE_ID = "CANDIDATE-1"
CANDIDATE_HASH = "sha256:" + "a" * 64
NEXT_ID = "CANDIDATE-2"
NEXT_HASH = "sha256:" + "b" * 64
SURFACES = ["SURFACE-AUTH", "SURFACE-API"]
LOCKED_EXCLUSIONS = json.loads(policy_path.read_text(encoding="utf-8"))[
    "owner_locked_default_exclusions"
]
VULNERABILITY_TEMPLATE = json.loads(
    (root / "lc-coding/templates/VULNERABILITY-CLOSURE.json").read_text(encoding="utf-8")
)
DECISION_ANSWERS = {
    "delivery_model": "per-customer-package",
    "assets": "client-runtime-only",
    "source_and_modification_rights": "compiled-runtime-no-source",
    "runtime_and_infrastructure": "ubuntu-24.04",
    "data": "customer-owned-no-transfer",
    "internal_dependencies": "excluded-from-delivery",
    "license": "customer-license",
    "operations": "customer-operated",
}
AGENT_DECISION_ANSWERS = json.loads(policy_path.read_text(encoding="utf-8"))[
    "agent_delivery_decision_records"
]
AGENT_SURFACE_CONTRACT = json.loads(
    (root / "lc-coding/contracts/vulnerability-closure.json").read_text(
        encoding="utf-8"
    )
)
_AGENT_PROJECT_FIXTURES = None


def bound(evidence_id, surfaces, candidate_id, candidate_hash):
    return {
        "evidence_id": evidence_id,
        "candidate_id": candidate_id,
        "candidate_hash": candidate_hash,
        "surface_ids": list(surfaces),
    }


def auditor(prefix):
    return {
        "agent_id": prefix + "-AGENT",
        "context_id": prefix + "-CONTEXT",
        "workspace_id": prefix + "-WORKSPACE",
        "independent": True,
        "prior_roles": [],
    }


def closure_receipt(candidate_id=CANDIDATE_ID, candidate_hash=CANDIDATE_HASH):
    def evidence(evidence_id, surfaces):
        return bound(evidence_id, surfaces, candidate_id, candidate_hash)

    return {
        "schema_version": "2.7.0",
        "artifact_role": "VULNERABILITY_CLOSURE_RECEIPT",
        "closure_id": "VC-DELIVERY-1",
        "candidate_id": candidate_id,
        "candidate_hash": candidate_hash,
        "agent_security_binding": copy.deepcopy(
            VULNERABILITY_TEMPLATE["agent_security_binding"]
        ),
        "agent_surface_bindings": [],
        "pre_audit_loop_owner_acceptance_receipts": [evidence("OA-DELIVERY-1", SURFACES)],
        "security_auditor": auditor("PRIMARY"),
        "audit_scope": {"scope": "FINAL_ACCEPTED_CANDIDATE", **evidence("E-SCOPE", SURFACES)},
        "coverage": {"status": "COMPLETE", **evidence("E-COVERAGE", SURFACES)},
        "required_surface_ids": list(SURFACES),
        "security_surfaces": [
            {
                "surface_id": "SURFACE-AUTH",
                "category": "AUTHENTICATION_AUTHORIZATION",
                "candidate_id": candidate_id,
                "candidate_hash": candidate_hash,
                "coverage_status": "COMPLETE",
                "audit_evidence_ids": ["E-AUTH-AUDIT"],
                "current_check_ids": ["E-AUTH-CHECK"],
                "disposition": "INCLUDED",
                "exclusion_evidence_id": "NONE",
            },
            {
                "surface_id": "SURFACE-API",
                "category": "API_EXPOSURE",
                "candidate_id": candidate_id,
                "candidate_hash": candidate_hash,
                "coverage_status": "COMPLETE",
                "audit_evidence_ids": ["E-API-AUDIT"],
                "current_check_ids": ["E-API-CHECK"],
                "disposition": "INCLUDED",
                "exclusion_evidence_id": "NONE",
            },
        ],
        "transitive_relations": [
            {
                "source_surface_id": "SURFACE-AUTH",
                "target_surface_id": "SURFACE-API",
                "candidate_id": candidate_id,
                "candidate_hash": candidate_hash,
                "evidence_id": "E-REL-AUTH-API",
                "reason_id": "R-REL-AUTH-API",
            }
        ],
        "reused_security_evidence": [],
        "new_checks": [
            evidence("E-AUTH-AUDIT", ["SURFACE-AUTH"]),
            evidence("E-AUTH-CHECK", ["SURFACE-AUTH"]),
            evidence("E-API-AUDIT", ["SURFACE-API"]),
            evidence("E-API-CHECK", ["SURFACE-API"]),
        ],
        "findings": [],
        "remediation_runs": [],
        "residual_risks": [],
        "affected_receipts": [],
        "reaudit": {
            "status": "COMPLETE",
            "auditor": auditor("REAUDIT"),
            "covered_surface_ids": list(SURFACES),
            "receipt_evidence": [evidence("SA-DELIVERY-1", SURFACES)],
        },
        "verdict": {"result": "VULNERABILITY_CLOSED", **evidence("E-VERDICT", SURFACES)},
        "issued_at": "2026-08-13T00:00:00Z",
    }


def post_receipt(candidate_id=CANDIDATE_ID, candidate_hash=CANDIDATE_HASH):
    all_surfaces = "+".join(SURFACES)
    return {
        "Schema version": "2.7.0",
        "Artifact role": "POST_SECURITY_OWNER_ACCEPTANCE_RECEIPT",
        "Acceptance ID": "PSOA-DELIVERY-1",
        "Candidate ID / exact hash": f"{candidate_id} / {candidate_hash}",
        "Vulnerability Closure Receipt ID / reference": (
            "VC-DELIVERY-1 / VULNERABILITY-CLOSURE.json"
        ),
        "Vulnerability Closure candidate ID / exact hash": (
            f"{candidate_id} / {candidate_hash}"
        ),
        "Covered remediation surface IDs": "NONE",
        "Changed remediation surface IDs": "NONE",
        "Reused Loop Owner Acceptance Receipt IDs": (
            f"OA-DELIVERY-1@{candidate_id}@{candidate_hash}@{all_surfaces}"
        ),
        "Security Remediation Run IDs": "NONE",
        "Critical smoke / delta evidence": (
            f"E-AUTH-CHECK@{candidate_id}@{candidate_hash}@SURFACE-AUTH"
        ),
        "Owner result": "POST_SECURITY_OWNER_ACCEPTED",
        "Supersession status": "CURRENT",
        "Superseded by Acceptance ID / reference": "NOT_APPLICABLE",
        "Accepted at": "2026-08-13T00:30:00Z",
    }


def markdown(fields):
    return "# Evidence\n\n" + "\n".join(
        f"- {key}: {value}" for key, value in fields.items()
    ) + "\n"


def impact_fields(kind, prior_id, prior_hash, current_id, current_hash, result="PASS"):
    if kind == "NEUTRAL":
        classification = "PROVEN_SECURITY_SURFACE_NEUTRAL"
        preservation = (
            f"MODE@NEUTRAL;EVIDENCE@E-DELIVERY-NEUTRAL;"
            f"PRIOR@{prior_id}@{prior_hash};CURRENT@{current_id}@{current_hash}"
        )
    else:
        classification = "EVIDENCE_EQUIVALENT_PACKAGING_TRANSFORMATION"
        preservation = (
            f"MODE@PACKAGING_EQUIVALENCE;TRANSFORMATION@E-DELIVERY-PACKAGE;"
            f"SECURITY_EQUIVALENCE@E-DELIVERY-EQUIVALENCE;"
            f"PRIOR@{prior_id}@{prior_hash};CURRENT@{current_id}@{current_hash}"
        )
    return {
        "Artifact role": "IMPACT_ANALYSIS",
        "Analysis ID / version": "IA-DELIVERY / 1.0.0",
        "Trigger / proposed change": "delivery candidate relationship",
        "Meaning impact classification": "MEANING_NEUTRAL",
        "Calling phase contract / authority": "DELIVERY_PREPARATION / LC-SECURITY-001",
        "Neutral rationale / evidence": "E-DELIVERY-MEANING-NEUTRAL",
        "Definition Baseline ID / exact hash": "NONE",
        "Affected Definition clause references": "NONE",
        "Definition invalidation effect": "NO_DEFINITION_INVALIDATION",
        "Governed Calabash update route / Owner authority": "NOT_APPLICABLE",
        "Snake / Scorpion applicability and effect references": "NONE_IDENTIFIED:E-REVIEW",
        "Security change timing": "AFTER_POST_SECURITY_OWNER_ACCEPTED",
        "Prior candidate ID / exact hash": f"{prior_id} / {prior_hash}",
        "Current candidate ID / exact hash": f"{current_id} / {current_hash}",
        "Security change classification": classification,
        "Changed security surface categories": "NONE",
        "Affected security surface IDs": "NONE",
        "Transitive affected surface IDs / evidence": "NONE",
        "Prior Vulnerability Closure Receipt ID / reference": (
            "VC-DELIVERY-1 / VULNERABILITY-CLOSURE.json"
        ),
        "Prior Post-Security Owner Acceptance ID / reference": (
            "PSOA-DELIVERY-1 / POST-SECURITY-OWNER-ACCEPTANCE.md"
        ),
        "Security neutral / preservation evidence": preservation,
        "Security invalidation evidence": "NOT_APPLICABLE",
        "Required security action": "PRESERVE_EXACT_CLOSURE",
        "Impact result": result,
    }


def current_status(status_id, status_hash, receipt_id, receipt_hash, impact=None):
    status = json.loads(
        (root / "lc-coding/templates/STATUS.json").read_text(encoding="utf-8")
    )
    assert status["agent_product_formation"]["state"] == "UNPROVED"
    assert status["agent_slice_integration"]["state"] == "UNPROVED"
    status.pop("agent_product_formation")
    status.pop("agent_slice_integration")
    status["status_schema_version"] = "2.7.0"
    status["canonical_candidate"] = {
        "repository": "owner/project",
        "version": "1.0.0",
        "commit": "a" * 40,
        "candidate_id": status_id,
        "candidate_hash": status_hash,
    }
    status["vulnerability_closure"] = {
        "state": "VULNERABILITY_CLOSED",
        "candidate_id": status_id,
        "candidate_hash": status_hash,
        "current_receipt_id": "VC-DELIVERY-1",
        "current_receipt_reference": "VULNERABILITY-CLOSURE.json",
        "superseded_receipt_id": "NOT_APPLICABLE",
        "superseded_receipt_reference": "NOT_APPLICABLE",
        "superseded_candidate_id": "NOT_APPLICABLE",
        "superseded_candidate_hash": "NOT_APPLICABLE",
    }
    status["post_security_owner_acceptance"] = {
        "state": "POST_SECURITY_OWNER_ACCEPTED",
        "candidate_id": status_id,
        "candidate_hash": status_hash,
        "current_acceptance_id": "PSOA-DELIVERY-1",
        "current_acceptance_reference": "POST-SECURITY-OWNER-ACCEPTANCE.md",
        "vulnerability_closure_receipt_id": "VC-DELIVERY-1",
        "vulnerability_closure_receipt_reference": "VULNERABILITY-CLOSURE.json",
        "superseded_acceptance_id": "NOT_APPLICABLE",
        "superseded_acceptance_reference": "NOT_APPLICABLE",
        "superseded_candidate_id": "NOT_APPLICABLE",
        "superseded_candidate_hash": "NOT_APPLICABLE",
    }
    status["phase_gates"]["DELIVERY_READY"] = "DELIVERY_READY"
    status["delivery_method_qa"] = "DELIVERY_METHOD_CONFIRMED"
    status["evidence_pointers"] = [
        "VULNERABILITY-CLOSURE.json", "POST-SECURITY-OWNER-ACCEPTANCE.md"
    ]
    if impact is not None:
        status["last_material_change"] = "IA-DELIVERY / IMPACT-ANALYSIS.md"
        status["evidence_pointers"].insert(0, "IMPACT-ANALYSIS.md")
        status["next_action"] = "PRESERVE_EXACT_SECURITY_CLOSURE"
    return status


def good_decision(candidate_id=CANDIDATE_ID, candidate_hash=CANDIDATE_HASH):
    return {
        "delivery_decision_id": "DD-1",
        "delivery_id": "D-1",
        "customer": "Customer A",
        "candidate_id": f"{candidate_id} / {candidate_hash}",
        "owner_policy_version": "1.0.0",
        "locked_exclusions": list(LOCKED_EXCLUSIONS),
        "decisions": {
            group: {"selected": DECISION_ANSWERS[group]} for group in GROUPS
        },
        "qa_status": "COMPLETE",
        "owner_confirmed": True,
        "confirmed_at": "2026-08-13T01:00:00Z",
    }


def load_agent_project_fixtures():
    global _AGENT_PROJECT_FIXTURES
    if _AGENT_PROJECT_FIXTURES is None:
        path = root / "lc-coding/tests/test_agent_product_formation_280.py"
        spec = importlib.util.spec_from_file_location("delivery_agent_project_fixture", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _AGENT_PROJECT_FIXTURES = module
    return _AGENT_PROJECT_FIXTURES


def bound_agent_closure(binding):
    receipt = closure_receipt(binding["candidate_id"], binding["candidate_hash"])
    receipt["agent_security_binding"] = copy.deepcopy(binding)
    receipt["findings"] = [{
        "finding_id": "F-DELIVERY-AUTH-1",
        "candidate_id": binding["candidate_id"],
        "candidate_hash": binding["candidate_hash"],
        "surface_ids": ["SURFACE-AUTH"],
        "severity": "HIGH",
        "category": "AUTHENTICATION_BYPASS",
        "status": "MITIGATED",
        "evidence_id": "E-FINDING-DELIVERY-AUTH",
    }]
    receipt["remediation_runs"] = [{
        "run_id": "SEC-DELIVERY-RUN-1",
        "candidate_id": binding["candidate_id"],
        "candidate_hash": binding["candidate_hash"],
        "surface_ids": ["SURFACE-AUTH"],
        "evidence_id": "E-DELIVERY-REMEDIATION-1",
        "implementer_id": "DELIVERY-REMEDIATOR-1",
    }]
    receipt["affected_receipts"] = [bound(
        "OA-DELIVERY-AFFECTED-1", ["SURFACE-AUTH"],
        binding["candidate_id"], binding["candidate_hash"],
    )]
    active_agents = [binding["operations_agent_id"]]
    if binding["product_agent_applicability"] != "NOT_APPLICABLE":
        active_agents.insert(0, binding["product_agent_id"])
    surface_bindings = []
    for index, kind in enumerate(AGENT_SURFACE_CONTRACT["agent_surface_kinds"], 1):
        role = AGENT_SURFACE_CONTRACT["agent_surface_kind_roles"][kind]
        agent_ids = (
            [binding["runtime_adapter_id"]] if role == "RUNTIME_ADAPTER"
            else [binding["operations_agent_id"]] if role == "OPERATIONS_AGENT"
            else list(active_agents)
        )
        surface_bindings.append({
            "binding_id": f"AGENT-DELIVERY-SURFACE-{index}",
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
            "remediation_evidence_id": "E-DELIVERY-REMEDIATION-1",
            "reaudit_evidence_id": "SA-DELIVERY-1",
            "result": "PASS",
        })
    receipt["agent_surface_bindings"] = surface_bindings
    return receipt


def build_agent_delivery_project(project, applicability="APPLICABLE_CORE"):
    agent_fixtures = load_agent_project_fixtures()
    lc, status = agent_fixtures.build_agent_slice_status_project(
        Path(project), applicability
    )
    status["current_phase"] = "DELIVERY_PREPARATION"
    status["phase_gates"]["DELIVERY_READY"] = "DELIVERY_READY"
    status["delivery_method_qa"] = "DELIVERY_METHOD_CONFIRMED"
    expected_binding, binding_errors = (
        agent_fixtures.project_validator._expected_agent_security_binding(lc, status)
    )
    assert binding_errors == [], binding_errors
    closure = bound_agent_closure(expected_binding)
    closure_path = lc / "VULNERABILITY-CLOSURE.json"
    closure_path.write_text(json.dumps(closure), encoding="utf-8")
    post = post_receipt(expected_binding["candidate_id"], expected_binding["candidate_hash"])
    post["Covered remediation surface IDs"] = "SURFACE-AUTH"
    post["Changed remediation surface IDs"] = "SURFACE-AUTH"
    post["Security Remediation Run IDs"] = (
        f"SEC-DELIVERY-RUN-1@{expected_binding['candidate_id']}@"
        f"{expected_binding['candidate_hash']}@SURFACE-AUTH@E-DELIVERY-REMEDIATION-1"
    )
    post_path = lc / "POST-SECURITY-OWNER-ACCEPTANCE.md"
    post_path.write_text(markdown(post), encoding="utf-8")
    status["vulnerability_closure"] = {
        "state": "VULNERABILITY_CLOSED",
        "candidate_id": expected_binding["candidate_id"],
        "candidate_hash": expected_binding["candidate_hash"],
        "current_receipt_id": closure["closure_id"],
        "current_receipt_reference": closure_path.name,
        "superseded_receipt_id": "NOT_APPLICABLE",
        "superseded_receipt_reference": "NOT_APPLICABLE",
        "superseded_candidate_id": "NOT_APPLICABLE",
        "superseded_candidate_hash": "NOT_APPLICABLE",
    }
    status["post_security_owner_acceptance"] = {
        "state": "POST_SECURITY_OWNER_ACCEPTED",
        "candidate_id": expected_binding["candidate_id"],
        "candidate_hash": expected_binding["candidate_hash"],
        "current_acceptance_id": post["Acceptance ID"],
        "current_acceptance_reference": post_path.name,
        "vulnerability_closure_receipt_id": closure["closure_id"],
        "vulnerability_closure_receipt_reference": closure_path.name,
        "superseded_acceptance_id": "NOT_APPLICABLE",
        "superseded_acceptance_reference": "NOT_APPLICABLE",
        "superseded_candidate_id": "NOT_APPLICABLE",
        "superseded_candidate_hash": "NOT_APPLICABLE",
    }
    status["evidence_pointers"] = sorted(set(status.get("evidence_pointers", [])) | {
        closure_path.name, post_path.name,
    })
    (lc / "status.json").write_text(json.dumps(status), encoding="utf-8")
    decision = good_decision(expected_binding["candidate_id"], expected_binding["candidate_hash"])
    for group, value in AGENT_DECISION_ANSWERS.items():
        decision["decisions"][group] = {"selected": value}
    (lc / "DELIVERY-DECISION.json").write_text(json.dumps(decision), encoding="utf-8")
    return lc, decision, status


def build_delivery_project(
    project,
    *,
    status_id=CANDIDATE_ID,
    status_hash=CANDIDATE_HASH,
    receipt_id=None,
    receipt_hash=None,
    preservation=None,
    impact_result="PASS",
):
    lc = Path(project) / ".lccoding"
    lc.mkdir(parents=True)
    receipt_id = receipt_id or status_id
    receipt_hash = receipt_hash or status_hash
    impact = None
    if preservation:
        impact = impact_fields(
            preservation, receipt_id, receipt_hash, status_id, status_hash,
            result=impact_result,
        )
        (lc / "IMPACT-ANALYSIS.md").write_text(markdown(impact), encoding="utf-8")
    status = current_status(status_id, status_hash, receipt_id, receipt_hash, impact)
    (lc / "status.json").write_text(json.dumps(status), encoding="utf-8")
    (lc / "VULNERABILITY-CLOSURE.json").write_text(
        json.dumps(closure_receipt(receipt_id, receipt_hash)), encoding="utf-8"
    )
    (lc / "POST-SECURITY-OWNER-ACCEPTANCE.md").write_text(
        markdown(post_receipt(receipt_id, receipt_hash)), encoding="utf-8"
    )
    decision = good_decision(status_id, status_hash)
    (lc / "DELIVERY-DECISION.json").write_text(json.dumps(decision), encoding="utf-8")
    return lc, decision, status


def run_decision(path):
    return subprocess.run(
        [sys.executable, str(decision_validator), str(path)],
        capture_output=True, text=True,
    )


def snapshot(path):
    return {
        item.relative_to(path).as_posix(): (
            item.read_bytes(), item.stat().st_mtime_ns
        )
        for item in path.rglob("*") if item.is_file()
    }


def execute_tests():
    with tempfile.TemporaryDirectory(prefix="lccoding-delivery-qa-270-") as temporary:
        base = Path(temporary)
        project = base / "fresh"
        lc, decision, status = build_delivery_project(project)
        before = snapshot(project)
        result = run_decision(lc / "DELIVERY-DECISION.json")
        assert result.returncode == 0, result.stdout + result.stderr
        assert snapshot(project) == before

        def case(name):
            target = base / name
            shutil.copytree(project, target)
            return target / ".lccoding"

        unbound_agent = case("unbound-agent-280")
        unbound_status = json.loads((unbound_agent / "status.json").read_text())
        current_template = json.loads(
            (root / "lc-coding/templates/STATUS.json").read_text(encoding="utf-8")
        )
        unbound_status["status_schema_version"] = "2.8.0"
        unbound_status["agent_product_formation"] = current_template[
            "agent_product_formation"
        ]
        unbound_status["agent_slice_integration"] = current_template[
            "agent_slice_integration"
        ]
        (unbound_agent / "status.json").write_text(json.dumps(unbound_status))
        unbound_result = run_decision(unbound_agent / "DELIVERY-DECISION.json")
        assert unbound_result.returncode != 0
        assert "Agent-native Delivery requires accepted Agent Slice integration" in (
            unbound_result.stdout + unbound_result.stderr
        )

        agent_project = base / "agent-bound-280"
        agent_lc, agent_decision, _ = build_agent_delivery_project(agent_project)
        agent_before = snapshot(agent_project)
        agent_result = run_decision(agent_lc / "DELIVERY-DECISION.json")
        assert agent_result.returncode == 0, agent_result.stdout + agent_result.stderr
        assert snapshot(agent_project) == agent_before
        for group in AGENT_DECISION_ANSWERS:
            changed = copy.deepcopy(agent_decision)
            changed["decisions"][group]["selected"] = "customer-responsibility-recorded"
            path = agent_lc / "DELIVERY-DECISION.json"
            path.write_text(json.dumps(changed), encoding="utf-8")
            result = run_decision(path)
            assert result.returncode != 0
            assert f"Agent-native Delivery Q&A record mismatch: {group}" in (
                result.stdout + result.stderr
            )
        (agent_lc / "DELIVERY-DECISION.json").write_text(
            json.dumps(agent_decision), encoding="utf-8"
        )

        same_id_wrong_hash = case("same-id-wrong-hash")
        changed = copy.deepcopy(decision)
        changed["candidate_id"] = f"{CANDIDATE_ID} / {NEXT_HASH}"
        (same_id_wrong_hash / "DELIVERY-DECISION.json").write_text(
            json.dumps(changed), encoding="utf-8"
        )
        assert run_decision(same_id_wrong_hash / "DELIVERY-DECISION.json").returncode != 0

        for name, mutate in (
            ("qa-incomplete", lambda item: item.__setitem__("qa_status", "PENDING")),
            ("owner-missing", lambda item: item.__setitem__("owner_confirmed", False)),
            ("group-missing", lambda item: item["decisions"].pop("license")),
            ("policy-exclusion-missing", lambda item: item["locked_exclusions"].pop()),
            ("customer-pending", lambda item: item.__setitem__("customer", "PENDING")),
            ("customer-pass", lambda item: item.__setitem__("customer", "PASS")),
            ("customer-invalid", lambda item: item.__setitem__("customer", "INVALID")),
            ("customer-rejected", lambda item: item.__setitem__("customer", "REJECTED")),
            ("customer-fake", lambda item: item.__setitem__("customer", "FAKE")),
            ("customer-test", lambda item: item.__setitem__("customer", "TEST")),
            ("customer-mock", lambda item: item.__setitem__("customer", "MOCK")),
            ("customer-stub", lambda item: item.__setitem__("customer", "STUB")),
            ("decision-id-test", lambda item: item.__setitem__(
                "delivery_decision_id", "TEST"
            )),
            ("decision-id-invalid", lambda item: item.__setitem__(
                "delivery_decision_id", "INVALID"
            )),
            ("decision-id-pass-prefixed", lambda item: item.__setitem__(
                "delivery_decision_id", "PASS-1"
            )),
            ("decision-id-invalid-prefixed", lambda item: item.__setitem__(
                "delivery_decision_id", "INVALID-1"
            )),
            ("decision-id-approved-prefixed", lambda item: item.__setitem__(
                "delivery_decision_id", "APPROVED-1"
            )),
            ("decision-id-multitoken-status-prefixed", lambda item: item.__setitem__(
                "delivery_decision_id", "NOT_APPLICABLE-1"
            )),
            ("delivery-id-mock", lambda item: item.__setitem__("delivery_id", "MOCK")),
            ("policy-version-pending", lambda item: item.__setitem__(
                "owner_policy_version", "PENDING"
            )),
            ("policy-version-invalid", lambda item: item.__setitem__(
                "owner_policy_version", "1.0"
            )),
            ("confirmed-at-pending", lambda item: item.__setitem__(
                "confirmed_at", "PENDING"
            )),
            ("confirmed-at-offset", lambda item: item.__setitem__(
                "confirmed_at", "2026-08-13T01:00:00+08:00"
            )),
            ("confirmed-at-impossible", lambda item: item.__setitem__(
                "confirmed_at", "2026-02-30T01:00:00Z"
            )),
            ("answer-placeholder", lambda item: item["decisions"].__setitem__(
                "license", {"selected": "PENDING"}
            )),
            ("answer-unknown", lambda item: item["decisions"].__setitem__(
                "license", {"selected": "UNKNOWN"}
            )),
            ("answer-todo", lambda item: item["decisions"].__setitem__(
                "license", {"selected": "TODO"}
            )),
            ("answer-tbd", lambda item: item["decisions"].__setitem__(
                "license", {"selected": "TBD"}
            )),
            ("answer-pass", lambda item: item["decisions"].__setitem__(
                "license", {"selected": "PASS"}
            )),
            ("answer-complete", lambda item: item["decisions"].__setitem__(
                "license", {"selected": "COMPLETE"}
            )),
            ("answer-confirmed", lambda item: item["decisions"].__setitem__(
                "license", {"selected": "CONFIRMED"}
            )),
            ("answer-approved", lambda item: item["decisions"].__setitem__(
                "license", {"selected": "APPROVED"}
            )),
            ("answer-generic", lambda item: item["decisions"].__setitem__(
                "license", {"selected": "GENERIC"}
            )),
            ("answer-placeholder-word", lambda item: item["decisions"].__setitem__(
                "license", {"selected": "PLACEHOLDER"}
            )),
            ("answer-missing", lambda item: item["decisions"].__setitem__(
                "license", {}
            )),
            ("answer-unknown-field", lambda item: item["decisions"].__setitem__(
                "license", {"selected": "customer-license", "shadow": "override"}
            )),
            ("answer-wrong-type", lambda item: item["decisions"].__setitem__(
                "license", {"selected": ["customer-license"]}
            )),
        ):
            lc_case = case(name)
            item = copy.deepcopy(decision); mutate(item)
            (lc_case / "DELIVERY-DECISION.json").write_text(json.dumps(item), encoding="utf-8")
            assert run_decision(lc_case / "DELIVERY-DECISION.json").returncode != 0

        duplicate = case("duplicate-key")
        raw = json.dumps(decision).replace(
            '"candidate_id":', '"candidate_id":"SHADOW", "candidate_id":', 1
        )
        (duplicate / "DELIVERY-DECISION.json").write_text(raw, encoding="utf-8")
        duplicate_result = run_decision(duplicate / "DELIVERY-DECISION.json")
        assert duplicate_result.returncode != 0 and "Traceback" not in (
            duplicate_result.stdout + duplicate_result.stderr
        )

        nonfinite = case("nonfinite-answer")
        raw = json.dumps(decision).replace(
            '"selected": "per-customer-package"', '"selected": NaN', 1
        )
        (nonfinite / "DELIVERY-DECISION.json").write_text(raw, encoding="utf-8")
        nonfinite_result = run_decision(nonfinite / "DELIVERY-DECISION.json")
        assert nonfinite_result.returncode != 0 and "Traceback" not in (
            nonfinite_result.stdout + nonfinite_result.stderr
        )

        status_nonfinite = case("status-nonfinite")
        raw_status = (status_nonfinite / "status.json").read_text(encoding="utf-8")
        raw_status = raw_status.replace('"current_phase": "INITIAL"', '"current_phase": NaN')
        (status_nonfinite / "status.json").write_text(raw_status, encoding="utf-8")
        status_nonfinite_result = run_decision(
            status_nonfinite / "DELIVERY-DECISION.json"
        )
        assert status_nonfinite_result.returncode != 0 and "Traceback" not in (
            status_nonfinite_result.stdout + status_nonfinite_result.stderr
        )

        status_duplicate = case("status-duplicate")
        raw_status = (status_duplicate / "status.json").read_text(encoding="utf-8")
        raw_status = raw_status.replace(
            '"current_phase": "INITIAL"',
            '"current_phase": "INITIAL", "current_phase": "DELIVERY_PREPARATION"',
            1,
        )
        (status_duplicate / "status.json").write_text(raw_status, encoding="utf-8")
        status_duplicate_result = run_decision(
            status_duplicate / "DELIVERY-DECISION.json"
        )
        assert status_duplicate_result.returncode != 0 and "Traceback" not in (
            status_duplicate_result.stdout + status_duplicate_result.stderr
        )

        trailing = case("decision-trailing")
        raw_decision = (trailing / "DELIVERY-DECISION.json").read_text(encoding="utf-8")
        (trailing / "DELIVERY-DECISION.json").write_text(
            raw_decision + "\n{}", encoding="utf-8"
        )
        trailing_result = run_decision(trailing / "DELIVERY-DECISION.json")
        assert trailing_result.returncode != 0 and "Traceback" not in (
            trailing_result.stdout + trailing_result.stderr
        )

        non_utf8 = case("decision-non-utf8")
        (non_utf8 / "DELIVERY-DECISION.json").write_bytes(b"{\xff}")
        non_utf8_result = run_decision(non_utf8 / "DELIVERY-DECISION.json")
        assert non_utf8_result.returncode != 0 and "Traceback" not in (
            non_utf8_result.stdout + non_utf8_result.stderr
        )

        decision_spec = importlib.util.spec_from_file_location(
            "delivery_decision_strict_json_test", decision_validator
        )
        decision_module = importlib.util.module_from_spec(decision_spec)
        decision_spec.loader.exec_module(decision_module)
        fake_policy = base / "policy-nonfinite.json"
        fake_policy.write_text('{"owner_locked_default_exclusions": [NaN]}')
        try:
            decision_module.strict_json(fake_policy)
        except ValueError:
            pass
        else:
            raise AssertionError("strict policy JSON parser accepted NaN")
        fake_policy.write_text('{"x": 1, "x": 2}', encoding="utf-8")
        try:
            decision_module.strict_json(fake_policy)
        except ValueError:
            pass
        else:
            raise AssertionError("strict policy JSON parser accepted duplicate keys")
        fake_policy.write_text('{"x": 1e999}', encoding="utf-8")
        try:
            decision_module.strict_json(fake_policy)
        except ValueError:
            pass
        else:
            raise AssertionError("strict policy JSON parser accepted non-finite float")

        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        original_policy_path = decision_module.POLICY_PATH
        try:
            decision_module.POLICY_PATH = fake_policy
            for field in (
                "configuration_baseline_hash",
                "runtime_adapter_digest",
                "operations_base_model_hash",
                "isolation_evidence_hash",
                "fallback_evidence_hash",
                "kill_switch_evidence_hash",
                "audit_evidence_hash",
                "vulnerability_closure_hash",
                "post_security_acceptance_hash",
            ):
                changed_policy = copy.deepcopy(policy)
                changed_policy["agent_delivery_certification_fields"].remove(field)
                changed_policy["agent_delivery_manifest_fields"].remove(field)
                fake_policy.write_text(json.dumps(changed_policy), encoding="utf-8")
                _, policy_errors = decision_module.load_policy()
                assert "Delivery policy Agent certification fields are invalid" in (
                    policy_errors
                ), (field, policy_errors)
            certification_fields = set(policy["agent_delivery_certification_fields"])
            for field in (
                set(policy["agent_delivery_manifest_fields"]) - certification_fields
            ):
                changed_policy = copy.deepcopy(policy)
                changed_policy["agent_delivery_manifest_fields"].remove(field)
                fake_policy.write_text(json.dumps(changed_policy), encoding="utf-8")
                _, policy_errors = decision_module.load_policy()
                assert "Delivery policy Agent manifest fields are invalid" in (
                    policy_errors
                ), (field, policy_errors)
            for term in policy["agent_delivery_forbidden_asset_terms"]:
                changed_policy = copy.deepcopy(policy)
                changed_policy["agent_delivery_forbidden_asset_terms"].remove(term)
                fake_policy.write_text(json.dumps(changed_policy), encoding="utf-8")
                _, policy_errors = decision_module.load_policy()
                assert "Delivery policy forbidden Agent asset terms are invalid" in (
                    policy_errors
                ), (term, policy_errors)
        finally:
            decision_module.POLICY_PATH = original_policy_path

        missing_receipt = case("missing-receipt")
        (missing_receipt / "VULNERABILITY-CLOSURE.json").unlink()
        assert run_decision(missing_receipt / "DELIVERY-DECISION.json").returncode != 0

        escaped_receipt = case("escaped-receipt")
        item = json.loads((escaped_receipt / "status.json").read_text())
        item["vulnerability_closure"]["current_receipt_reference"] = "../escape.json"
        (escaped_receipt / "status.json").write_text(json.dumps(item))
        assert run_decision(escaped_receipt / "DELIVERY-DECISION.json").returncode != 0

        fake_post = case("fake-post")
        post = post_receipt(); post["Acceptance ID"] = "PSOA-FAKE"
        (fake_post / "POST-SECURITY-OWNER-ACCEPTANCE.md").write_text(markdown(post))
        assert run_decision(fake_post / "DELIVERY-DECISION.json").returncode != 0

        superseded = case("superseded-post")
        post = post_receipt(); post["Supersession status"] = "SUPERSEDED"
        post["Superseded by Acceptance ID / reference"] = "PSOA-2 / MISSING.md"
        (superseded / "POST-SECURITY-OWNER-ACCEPTANCE.md").write_text(markdown(post))
        assert run_decision(superseded / "DELIVERY-DECISION.json").returncode != 0

        invalid = case("invalid-security")
        item = json.loads((invalid / "status.json").read_text())
        item["vulnerability_closure"]["state"] = "INVALID"
        item["post_security_owner_acceptance"]["state"] = "INVALID"
        item["phase_gates"]["DELIVERY_READY"] = "INVALID"
        (invalid / "status.json").write_text(json.dumps(item))
        assert run_decision(invalid / "DELIVERY-DECISION.json").returncode != 0

        partial = case("partial-security")
        item = json.loads((partial / "status.json").read_text())
        item["post_security_owner_acceptance"]["state"] = "INVALID"
        (partial / "status.json").write_text(json.dumps(item))
        assert run_decision(partial / "DELIVERY-DECISION.json").returncode != 0

        for name, qa_state in (
            ("authoritative-qa-pending", "PENDING"),
            ("authoritative-qa-invalid", "INVALID"),
            ("authoritative-qa-other", "COMPLETE"),
        ):
            qa_case = case(name)
            item = json.loads((qa_case / "status.json").read_text())
            item["delivery_method_qa"] = qa_state
            (qa_case / "status.json").write_text(json.dumps(item), encoding="utf-8")
            assert run_decision(qa_case / "DELIVERY-DECISION.json").returncode != 0

        neutral = base / "neutral"
        neutral_lc, _, _ = build_delivery_project(neutral, preservation="NEUTRAL")
        assert run_decision(neutral_lc / "DELIVERY-DECISION.json").returncode == 0
        blocked = base / "neutral-blocked"
        blocked_lc, _, _ = build_delivery_project(
            blocked, preservation="NEUTRAL", impact_result="BLOCKED"
        )
        assert run_decision(blocked_lc / "DELIVERY-DECISION.json").returncode != 0

        packaging = base / "packaging"
        packaging_lc, _, _ = build_delivery_project(
            packaging,
            status_id=NEXT_ID,
            status_hash=NEXT_HASH,
            receipt_id=CANDIDATE_ID,
            receipt_hash=CANDIDATE_HASH,
            preservation="PACKAGING",
        )
        assert run_decision(packaging_lc / "DELIVERY-DECISION.json").returncode == 0


if __name__ == "__main__":
    execute_tests()
    print("PASS: delivery Q&A is exact-candidate and current-security bound")
