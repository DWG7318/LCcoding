from pathlib import Path
import copy
import hashlib
import json
import subprocess
import sys
import tempfile


root = Path(__file__).resolve().parents[2]
validator = root / "lc-coding/scripts/validate_vulnerability_closure.py"
CANDIDATE_ID = "CANDIDATE-1"
CANDIDATE_HASH = "sha256:" + "a" * 64
SURFACES = ["SURFACE-AUTH", "SURFACE-API", "SURFACE-DATA", "SURFACE-INSTALLER"]


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


def valid_receipt():
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
    return {
        "schema_version": "2.7.0",
        "artifact_role": "VULNERABILITY_CLOSURE_RECEIPT",
        "closure_id": "VC-270",
        "candidate_id": CANDIDATE_ID,
        "candidate_hash": CANDIDATE_HASH,
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

print("PASS: vulnerability closure is candidate- and surface-bound")
