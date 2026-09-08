import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import zlib


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "lc-coding/scripts/validate_real_user_journey.py"
spec = importlib.util.spec_from_file_location("journey_validator_400", MODULE)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

CURRENT_ID = "CANDIDATE-400"
CURRENT_HASH = "4" * 64
OLD_ID = "CANDIDATE-399"
OLD_HASH = "3" * 64

def png_bytes(label):
    def chunk(kind, payload):
        return (
            struct.pack(">I", len(payload)) + kind + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    color = hashlib.sha256(label.encode("utf-8")).digest()[:4]
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"\x00" + color))
        + chunk(b"IEND", b"")
    )


def route(route_id, route_kind, actor_id, actor_kind, delegation, audits):
    return {
        "route_id": route_id,
        "route_kind": route_kind,
        "support_state": "REQUIRED",
        "delivery_state": "DELIVERED",
        "human_beneficiary_id": "HUMAN-1",
        "actor_id": actor_id,
        "actor_kind": actor_kind,
        "capability_id": "CAPABILITY-APPLICATION",
        "capability_implementation_id": "WORKFLOW-CAPABILITY-APPLICATION",
        "promised_entry": route_kind.lower() + " application entry",
        "human_observable_outcome": route_kind.lower() + " accepted result delivered to human",
        "authority": {
            "action_id": "ACTION-" + route_id,
            "resource_id": "RESOURCE-APPLICATION",
            "delegation_basis_id": delegation,
        },
        "consent": {
            "requirement": "NOT_REQUIRED" if route_kind == "DIRECT_PRODUCT" else "REQUIRED",
            "policy_id": "CONSENT-" + route_id,
        },
        "adapter_or_surface_id": "SURFACE-" + route_id,
        "acceptance_evidence_ids": ["ACCEPTANCE-" + route_id],
        "audit_event_ids": audits,
    }


ROUTES = [
    route(
        "ROUTE-DIRECT", "DIRECT_PRODUCT", "HUMAN-1", "HUMAN_PRINCIPAL",
        "NOT_APPLICABLE", [],
    ),
    route(
        "ROUTE-AGENT", "PERSONAL_AGENT", "PERSONAL-AGENT-1", "PERSONAL_AGENT",
        "DELEGATION-AGENT-1", ["AUDIT-AGENT-1"],
    ),
    route(
        "ROUTE-CENTER", "SERVICE_CENTER", "SERVICE-CENTER-1", "SERVICE_CENTER_ACTOR",
        "DELEGATION-CENTER-1", ["AUDIT-CENTER-1"],
    ),
]

SERVICE_MAP = {
    "record_role": "CALABASH_SERVICE_ROUTE_MAP",
    "service_topology_schema_version": "4.0.0",
    "map_id": "SERVICE-ROUTES-1",
    "project_id": "PROJECT-1",
    "state": "ADOPTED",
    "primary_strategy": "PLATFORM_COMPLETION",
    "required_coexisting_strategies": ["AGENT_COLLABORATIVE"],
    "service_center_applicability": "APPLICABLE",
    "journeys": [{
        "journey_id": "JOURNEY-001",
        "journey_class": "CORE",
        "delivery_state": "DELIVERED",
        "business_capability_id": "CAPABILITY-APPLICATION",
        "shared_capability_implementation_id": "WORKFLOW-CAPABILITY-APPLICATION",
        "routes": ROUTES,
    }],
}

# These are the actual steps used by this adopted candidate, not a route-wide
# mandate for every evidence kind supported by the project evidence contract.
EVIDENCE_PLAN = {
    "ROUTE-DIRECT": ["SCREENSHOT"],
    "ROUTE-AGENT": [
        "HUMAN_GOAL_MESSAGE", "AGENT_IDENTITY", "AUTHORIZATION_DECISION",
        "PLATFORM_EFFECT", "AUDIT_EVENT", "RESULT_DELIVERY",
    ],
    "ROUTE-CENTER": [
        "USER_REQUEST", "SERVICE_ACTOR_IDENTITY", "DELEGATION_BASIS",
        "AUTHORIZATION_DECISION", "ASSISTED_ACTION", "PLATFORM_EFFECT",
        "USER_COMMUNICATION", "AUDIT_EVENT", "RESULT_DELIVERY",
    ],
}

EVIDENCE_HEADERS = (
    "Round", "Journey ID", "Service Route ID", "Route kind", "Step ID",
    "Evidence ID", "Evidence kind", "Actor ID", "Authority action ID",
    "Authority resource ID", "Delegation basis ID", "Audit event ID", "Action",
    "Expected / observed visible result", "Visible location", "Viewport",
    "Screenshot path", "Screenshot SHA-256", "Native evidence path",
    "Native evidence SHA-256", "Human-observable outcome", "Result",
)

DEFECT_HEADERS = (
    "Defect ID", "Discovery time / candidate / round / Journey / Route / Step",
    "Evidence ID / kind / SHA-256", "Expected / observed",
    "Severity / reachability / blocking scope", "Affected layer / root cause",
    "Boundary surface / evidence", "Affected routes", "Repair sequence",
    "Priority exception justification", "Correction identity / engineering re-verification",
    "Retest round", "Retest evidence ID / kind / SHA-256", "State",
    "Exemption authority / impact / recovery",
)


def exact_candidate(candidate_id=CURRENT_ID, candidate_hash=CURRENT_HASH):
    return candidate_id + " / sha256:" + candidate_hash


def safe_suffix(route_id):
    return route_id.removeprefix("ROUTE-")


def markdown(title, fields):
    return "# " + title + "\n\n" + "\n".join(
        "- " + key + ": " + str(value) for key, value in fields.items()
    ) + "\n"


def write_markdown(path, title, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown(title, fields), encoding="utf-8", newline="\n")


def parse_markdown(path):
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("- ") and ":" in line:
            key, value = line[2:].split(":", 1)
            result[key.strip()] = value.strip()
    return result


def canonical_run_start_hash(text):
    canonical = []
    matches = 0
    for line in text.splitlines(keepends=True):
        ending = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
        body = line[:-len(ending)] if ending else line
        if body.startswith("- Start Contract SHA-256:"):
            body = "- Start Contract SHA-256:"
            matches += 1
        canonical.append(body + ending)
    assert matches == 1
    return "sha256:" + hashlib.sha256("".join(canonical).encode("utf-8")).hexdigest()


def citation(evidence_id, path, lc):
    return (
        evidence_id + " / sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        + " / " + path.relative_to(lc).as_posix()
    )


def bound(route_id, evidence_id):
    return "~".join((CURRENT_ID, CURRENT_HASH, route_id, evidence_id))


def receipt_fields(route_record, start_hash):
    suffix = safe_suffix(route_record["route_id"])
    acceptance_id = route_record["acceptance_evidence_ids"][0]
    authority = route_record["authority"]
    steps = [
        route_record["route_id"], route_record["actor_id"], authority["action_id"],
        authority["resource_id"],
    ]
    if authority["delegation_basis_id"] != "NOT_APPLICABLE":
        steps.append(authority["delegation_basis_id"])
    steps.extend((
        route_record["adapter_or_surface_id"],
        route_record["capability_implementation_id"],
        "D3-" + suffix,
        acceptance_id,
    ))
    return {
        "Artifact role": "LOOP_OWNER_ACCEPTANCE_RECEIPT",
        "Acceptance ID": acceptance_id,
        "Run ID": "RUN-" + suffix,
        "Run-start contract ID": "START-" + suffix,
        "Run-start contract SHA-256": start_hash,
        "Status schema version": "4.0.0",
        "LCCoding phase scope": "REAL_PRODUCT_INTEGRATION",
        "Phase-owned objective": route_record["human_observable_outcome"],
        "Candidate ID / hash": exact_candidate(),
        "D3 Receipt": "D3-" + suffix,
        "Entry / role / account": " / ".join((
            route_record["promised_entry"], route_record["actor_id"],
            authority["resource_id"],
        )),
        "Scenario IDs": "SCENARIO-" + suffix,
        "Acceptance steps": ", ".join(steps),
        "Product questions": "NONE",
        "Prior accepted dependencies reused": "NONE",
        "Invisible risks already verified": "RISK-" + suffix,
        "Known limits": "NONE",
        "Evidence return target in the calling phase": "FS-" + suffix,
        "Calling phase gate remains independently evaluated": "YES",
        "Owner result": "LOOP_OWNER_ACCEPTED",
        "Owner Gap ID (blank when accepted)": "",
        "Gap source Acceptance ID": "",
        "Gap source candidate / scenario": "",
        "Gap route": "",
        "Impact / definition reference": "",
        "Correction Run IDs": "",
        "Affected D0-D3 receipts": "",
        "Delta re-verification receipt": "",
        "Delta Owner re-acceptance receipt": "",
        "Gap status": "",
        "Product learning / route (may be blank; only consequential learning that changes a future decision, constraint, check, template, or reuse rule; update one existing canonical artifact)": "",
        "Accepted at": "2026-09-08T00:00:00Z",
    }


def write_task5_evidence(lc, route_record):
    suffix = safe_suffix(route_record["route_id"])
    run_path = lc / "runs" / ("RUN-" + suffix) / "RUN-HANDOFF.md"
    start = {
        "Artifact role": "RUN_START_CONTRACT",
        "Start Contract ID": "START-" + suffix,
        "Start Contract SHA-256": "PENDING",
        "Run ID": "RUN-" + suffix,
        "Status schema version": "4.0.0",
        "LCCoding phase scope": "REAL_PRODUCT_INTEGRATION",
        "Phase-owned objective": route_record["human_observable_outcome"],
        "Evidence return target in calling phase": "FS-" + suffix,
        "Service Route / Integration Baseline (REAL_PRODUCT_INTEGRATION only)": (
            route_record["route_id"] + " / IB-" + suffix
        ),
        "Readiness result": "READY",
        "Blocker evidence": "NONE",
    }
    write_markdown(run_path, "Run Handoff", start)
    start["Start Contract SHA-256"] = canonical_run_start_hash(
        run_path.read_text(encoding="utf-8")
    )
    write_markdown(run_path, "Run Handoff", start)
    receipt_path = lc / "reviews" / ("OA-" + suffix + ".md")
    receipt = receipt_fields(route_record, start["Start Contract SHA-256"])
    write_markdown(receipt_path, "Loop Owner Acceptance Receipt", receipt)
    d3_path = lc / "reviews" / ("D3-" + suffix + ".json")
    d3 = {
        "receipt_id": receipt["D3 Receipt"],
        "layer": "D3",
        "claim_id": route_record["capability_implementation_id"],
        "claim_version": "4.0.0",
        "candidate_id": CURRENT_ID,
        "candidate_hash": CURRENT_HASH,
        "environment_id": "ENV-TASK5-" + suffix,
        "authority": route_record["authority"]["action_id"],
        "reused_evidence": ["D2-" + suffix],
        "new_evidence": [],
        "repeated_checks": [],
        "coverage": [route_record["route_id"]],
        "risks_remaining": [],
        "verdict": "PASS",
        "issued_at": "2026-09-08T00:00:00Z",
        "executor_context_id": "EXECUTOR-" + suffix,
        "verification_context_id": "VERIFY-CONTEXT-" + suffix,
        "verification_workspace_id": "VERIFY-WORKSPACE-" + suffix,
        "model_binding_id": "MODEL-BINDING-" + suffix,
    }
    d3_path.write_text(json.dumps(d3, indent=2) + "\n", encoding="utf-8", newline="\n")
    final_path = lc / ("FINAL-FEATURE-VERIFICATION-" + suffix + ".md")
    final = {
        "Artifact role": "FINAL_FEATURE_VERIFICATION",
        "Verification ID": "VERIFY-" + suffix,
        "Integration candidate ID / exact hash": exact_candidate(),
        "Integration Route ID": route_record["route_id"],
        "Service Route ID": route_record["route_id"],
        "Human-observable outcome": route_record["human_observable_outcome"],
        "D3 / Loop Owner Acceptance evidence": (
            "D3:" + bound(route_record["route_id"], receipt["D3 Receipt"])
            + "; OWNER:" + bound(route_record["route_id"], receipt["Acceptance ID"])
        ),
        "Final verdict": "PASS",
    }
    write_markdown(final_path, "Final Feature Verification", final)
    artifacts = {
        "final_path": final_path,
        "d3_path": d3_path,
        "final_citation": citation(final["Verification ID"], final_path, lc),
        "d3_citation": citation(d3["receipt_id"], d3_path, lc),
    }
    return receipt_path, citation(receipt["Acceptance ID"], receipt_path, lc), receipt, artifacts


def payload_for(kind, evidence_id, route_record):
    if kind in {"HUMAN_GOAL_MESSAGE", "REQUEST_MESSAGE", "USER_REQUEST", "AGENT_RESPONSE", "USER_COMMUNICATION"}:
        return {
            "message_id": "MESSAGE-" + evidence_id,
            "direction": "HUMAN_TO_SERVICE" if kind in {"HUMAN_GOAL_MESSAGE", "USER_REQUEST"} else "SERVICE_TO_HUMAN",
            "content": (
                "DELIVERED_SUCCESS: result delivered to user"
                if kind == "USER_COMMUNICATION"
                else kind.lower().replace("_", " ") + " payload"
            ),
        }
    if kind in {"AGENT_IDENTITY", "SERVICE_ACTOR_IDENTITY"}:
        return {"subject_id": route_record["actor_id"], "verified_by": "IDENTITY-CHECK", "result": "VERIFIED"}
    if kind == "TASK_TRANSITION":
        return {"task_id": "TASK-" + evidence_id, "from_state": "READY", "to_state": "COMPLETE"}
    if kind == "AUTHORIZATION_DECISION":
        return {"decision_id": "DECISION-" + evidence_id, "decision": "ALLOW", "scope": route_record["authority"]["resource_id"]}
    if kind == "RESULT_ARTIFACT":
        return {"artifact_id": "ARTIFACT-" + evidence_id, "artifact_reference": "artifact://local", "result": "CREATED"}
    if kind == "PLATFORM_EFFECT":
        return {"effect_id": "EFFECT-" + evidence_id, "before_state": "PENDING", "after_state": "ACCEPTED"}
    if kind == "AUDIT_EVENT":
        return {"audit_event_id": route_record["audit_event_ids"][0], "event": "ROUTE_ACTION", "result": "RECORDED"}
    if kind == "RESULT_DELIVERY":
        return {"delivery_id": "DELIVERY-" + evidence_id, "recipient_id": route_record["human_beneficiary_id"], "result": route_record["human_observable_outcome"]}
    if kind == "DELEGATION_BASIS":
        return {"delegation_basis_id": route_record["authority"]["delegation_basis_id"], "delegated_by": "HUMAN-1", "scope": route_record["authority"]["resource_id"]}
    if kind == "ASSISTED_ACTION":
        return {"action_event_id": "ASSISTED-" + evidence_id, "action": "SUBMIT", "result": "COMPLETE"}
    raise AssertionError(kind)


def nonvisual_record(evidence_id, kind, route_record, round_number, step_id, candidate_id, candidate_hash):
    authority = route_record["authority"]
    return {
        "record_role": "REAL_USER_JOURNEY_EVIDENCE",
        "evidence_schema_version": "4.0.0",
        "evidence_id": evidence_id,
        "evidence_kind": kind,
        "candidate_id": candidate_id,
        "candidate_hash": candidate_hash,
        "round": round_number,
        "journey_id": "JOURNEY-001",
        "route_id": route_record["route_id"],
        "step_id": step_id,
        "actor_id": route_record["actor_id"],
        "authority_action_id": authority["action_id"],
        "authority_resource_id": authority["resource_id"],
        "delegation_basis_id": authority["delegation_basis_id"],
        "event_or_result": payload_for(kind, evidence_id, route_record),
    }


def row_line(values):
    return "| " + " | ".join(str(value) for value in values) + " |"


def evidence_row(
    lc, route_record, round_number, step_number, kind, candidate_id, candidate_hash,
    *, result="PASS", screenshot_bytes=None,
):
    step_id = f"STEP-{step_number:03d}"
    evidence_id = f"RUJE-{round_number:03d}-{step_number:03d}"
    authority = route_record["authority"]
    directory = lc / f"evidence/real-user-journey/round-{round_number:03d}/JOURNEY-001/{route_record['route_id']}"
    directory.mkdir(parents=True, exist_ok=True)
    screenshot_path = screenshot_hash = native_path = native_hash = "NOT_APPLICABLE"
    action = visible_result = location = viewport = "NOT_APPLICABLE"
    final = kind == "RESULT_DELIVERY" or (
        route_record["route_kind"] == "DIRECT_PRODUCT" and kind == "SCREENSHOT" and result == "PASS"
    )
    human_outcome = route_record["human_observable_outcome"] if final else "NOT_APPLICABLE"
    if kind == "SCREENSHOT":
        path = directory / (step_id + ".png")
        path.write_bytes(
            screenshot_bytes if screenshot_bytes is not None
            else png_bytes(f"round-{round_number}-{route_record['route_id']}-{step_id}")
        )
        screenshot_path = ".lccoding/" + path.relative_to(lc).as_posix()
        screenshot_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        action = "CLICK_SUBMIT"
        visible_result = "application submitted / application result rendered"
        location = "/application"
        viewport = "1280x720@1"
    else:
        path = directory / (step_id + ".json")
        path.write_text(
            json.dumps(nonvisual_record(
                evidence_id, kind, route_record, round_number, step_id,
                candidate_id, candidate_hash,
            ), indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        native_path = path.relative_to(lc).as_posix()
        native_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    audit_id = route_record["audit_event_ids"][0] if kind == "AUDIT_EVENT" else "NOT_APPLICABLE"
    values = (
        round_number, "JOURNEY-001", route_record["route_id"], route_record["route_kind"],
        step_id, evidence_id, kind, route_record["actor_id"], authority["action_id"],
        authority["resource_id"], authority["delegation_basis_id"], audit_id, action,
        visible_result, location, viewport, screenshot_path, screenshot_hash,
        native_path, native_hash, human_outcome, result,
    )
    return row_line(values), {
        "id": evidence_id,
        "kind": kind,
        "path": path,
        "hash": screenshot_hash if kind == "SCREENSHOT" else native_hash,
        "step": step_id,
        "route": route_record["route_id"],
        "round": round_number,
    }


def base_status(current_round=1, fixed=()):
    status = json.loads((ROOT / "lc-coding/templates/STATUS.json").read_text(encoding="utf-8"))
    status.update({
        "status_schema_version": "4.0.0",
        "project_id": "PROJECT-1",
        "lccoding_applicability": "WHOLE_PRODUCT_FIT",
        "product_service_strategy": "MIXED",
        "service_route_map": "ADOPTED",
        "canonical_candidate": {"candidate_id": CURRENT_ID, "candidate_hash": CURRENT_HASH},
        "current_phase": "REAL_USER_JOURNEY_ACCEPTANCE",
        "loop_owner_acceptances": [route_record["acceptance_evidence_ids"][0] for route_record in ROUTES],
    })
    status["phase_gates"]["REAL_USER_JOURNEY_ACCEPTED"] = "REAL_USER_JOURNEY_ACCEPTED"
    status["real_user_journey_acceptance"] = {
        "state": "REAL_USER_JOURNEY_ACCEPTED",
        "candidate_id": CURRENT_ID,
        "candidate_hash": CURRENT_HASH,
        "coverage_state": "COMPLETE",
        "acceptance_environment_state": "VERIFIED",
        "current_round": current_round,
        "complete_round_count": 1,
        "required_journey_count": 3,
        "passed_journey_count": 3,
        "failed_journey_count": 0,
        "not_applicable_journey_count": 0,
        "open_defect_ids": [],
        "fixed_verified_defect_ids": list(fixed),
        "exempted_defect_ids": [],
        "deferred_defect_ids": [],
        "reopened_defect_ids": [],
        "acceptance_record_reference": "REAL-USER-JOURNEY-ACCEPTANCE.md",
        "defect_log_reference": "REAL-USER-JOURNEY-DEFECT-LOG.md",
        "owner_result": "REAL_USER_JOURNEY_ACCEPTED",
    }
    return status


def base_phase_status(current_round=1):
    phase = json.loads((ROOT / "lc-coding/templates/PHASE-STATUS.json").read_text(encoding="utf-8"))
    phase["status_schema_version"] = "4.0.0"
    phase["phases"]["REAL_USER_JOURNEY_ACCEPTANCE"].update({
        "status": "COMPLETE",
        "acceptance_record": "REAL-USER-JOURNEY-ACCEPTANCE.md",
        "defect_log": "REAL-USER-JOURNEY-DEFECT-LOG.md",
        "complete_rounds": 1,
        "exit_gate": "REAL_USER_JOURNEY_ACCEPTED",
    })
    return phase


def empty_defect_log():
    return f"""# Real User Journey Defect Log

- Status schema version: 4.0.0
- Normal repair priority: USER_SERVICE_BOUNDARY -> WORKFLOW_ORCHESTRATION -> BACKEND_CORE

## Route-faithful defect register

{row_line(DEFECT_HEADERS)}
{row_line(['---'] * len(DEFECT_HEADERS))}

## State history

| Defect ID | Event time | Prior state | New state | Candidate ID / SHA-256 | Round | Evidence / reason |
|---|---|---|---|---|---|---|
"""


def fixed_history_defect(context):
    old = context["old_defect"]
    retest = context["evidence"][(2, "ROUTE-DIRECT", "SCREENSHOT")]
    defect = row_line((
        40001,
        f"2026-09-08T00:00:00Z / {OLD_ID} / 1 / JOURNEY-001 / ROUTE-DIRECT / {old['step']}",
        f"{old['id']} / {old['kind']} / {old['hash']}",
        "submit should render / submit was blocked",
        "HIGH / YES / ROUTE-DIRECT,ROUTE-AGENT,ROUTE-CENTER",
        "USER_SERVICE_BOUNDARY / blocked submit feedback",
        "UI / " + old["id"],
        "ROUTE-DIRECT,ROUTE-AGENT,ROUTE-CENTER", 1, "NOT_APPLICABLE",
        "FIX-40001 / D0-D3-REVERIFIED", 2,
        f"{retest['id']} / {retest['kind']} / {retest['hash']}",
        "FIXED_VERIFIED", "NOT_APPLICABLE",
    ))
    open_citation = citation(old["id"], old["path"], context["lc"])
    fixed_citation = citation(retest["id"], retest["path"], context["lc"])
    history = "\n".join((
        row_line((40001, "2026-09-08T00:00:00Z", "NOT_APPLICABLE", "OPEN", f"{OLD_ID} / {OLD_HASH}", 1, open_citation)),
        row_line((40001, "2026-09-08T00:01:00Z", "OPEN", "FIXED_VERIFIED", f"{CURRENT_ID} / {CURRENT_HASH}", 2, fixed_citation)),
    ))
    return defect, history


def write_project(root, *, historical=False):
    current_round = 2 if historical else 1
    lc = root / ".lccoding"
    lc.mkdir()
    route_map = copy.deepcopy(SERVICE_MAP)
    map_path = lc / "SERVICE-ROUTE-MAP.json"
    map_path.write_text(json.dumps(route_map, indent=2) + "\n", encoding="utf-8", newline="\n")
    map_hash = hashlib.sha256(map_path.read_bytes()).hexdigest()

    coverage_rows = []
    receipts = {}
    task5_artifacts = {}
    for route_record in ROUTES:
        receipt_path, receipt_citation, receipt, artifacts = write_task5_evidence(
            lc, route_record
        )
        receipts[route_record["route_id"]] = receipt_path
        task5_artifacts[route_record["route_id"]] = artifacts
        authority = route_record["authority"]
        coverage_rows.append(row_line((
            "JOURNEY-001", route_record["route_id"], route_record["route_kind"],
            route_record["actor_id"] + " / " + route_record["actor_kind"],
            " / ".join((authority["action_id"], authority["resource_id"], authority["delegation_basis_id"])),
            route_record["promised_entry"], route_record["human_observable_outcome"],
            ",".join(route_record["acceptance_evidence_ids"]), receipt_citation,
            receipt["Run ID"] + " / " + receipt["D3 Receipt"],
            "FINAL:" + artifacts["final_citation"] + "; D3:" + artifacts["d3_citation"],
            "REQUIRED",
        )))

    evidence = {}
    current_rows = []
    step_number = 1
    for route_record in ROUTES:
        for kind in EVIDENCE_PLAN[route_record["route_id"]]:
            row, item = evidence_row(
                lc, route_record, current_round, step_number, kind,
                CURRENT_ID, CURRENT_HASH,
            )
            current_rows.append(row)
            evidence[(current_round, route_record["route_id"], kind)] = item
            step_number += 1

    round_rows = []
    old_row = None
    old_defect = None
    if historical:
        old_row, old_defect = evidence_row(
            lc, ROUTES[0], 1, 900, "SCREENSHOT", OLD_ID, OLD_HASH,
            result="DEFECT", screenshot_bytes=png_bytes("round-old-defect"),
        )
        round_rows.append(row_line((
            1, f"{OLD_ID} / {OLD_HASH}", "YES", "ROUTE-DIRECT",
            "; ".join(
                route_id + " / DEPENDENCY_BLOCKED / " + old_defect["id"] + " / 40001"
                for route_id in ("ROUTE-AGENT", "ROUTE-CENTER")
            ), "3 / 0 / 1",
            old_defect["id"] + " / " + old_defect["id"], "40001", "REWORK",
        )))
    first_current = next(iter(evidence.values()))["id"]
    last_current = list(evidence.values())[-1]["id"]
    round_rows.append(row_line((
        current_round, f"{CURRENT_ID} / {CURRENT_HASH}", "YES",
        ",".join(route_record["route_id"] for route_record in ROUTES),
        "NONE", "3 / 3 / 0", first_current + " / " + last_current, "NONE", "PASS",
    )))

    acceptance = f"""# Real User Journey Acceptance

## Candidate identity

- Acceptance ID: RUJA-400-001
- Candidate ID: {CURRENT_ID}
- Candidate SHA-256: {CURRENT_HASH}
- Status schema version: 4.0.0
- Service Route Map ID / exact hash: SERVICE-ROUTES-1 / sha256:{map_hash}

## Route-faithful 4.0 journey coverage

| Journey ID | Service Route ID | Route kind | Actor ID / kind | Authority action / resource / delegation | Actual external entry | Expected human-observable outcome | Adopted acceptance evidence IDs | Task5 acceptance receipt citations | Task5 Run ID / D3 Receipt | Task5 Final Verification / D3 citations | Applicability |
|---|---|---|---|---|---|---|---|---|---|---|---|
{chr(10).join(coverage_rows)}

## Acceptance rounds

| Round | Candidate ID / SHA-256 | Started from each attempted actual route entry | Attempted route IDs | Unattempted route dispositions | Required routes / passed / failed | First and last evidence | Defect IDs | Result |
|---|---|---|---|---|---|---|---|---|
{chr(10).join(round_rows)}

## Route-faithful 4.0 evidence digests

{row_line(EVIDENCE_HEADERS)}
{row_line(['---'] * len(EVIDENCE_HEADERS))}
{old_row + chr(10) if old_row else ''}{chr(10).join(current_rows)}
"""
    (lc / "REAL-USER-JOURNEY-ACCEPTANCE.md").write_text(
        acceptance, encoding="utf-8", newline="\n"
    )
    context = {
        "lc": lc,
        "map": map_path,
        "receipts": receipts,
        "task5_artifacts": task5_artifacts,
        "evidence": evidence,
        "old_defect": old_defect,
    }
    defect_log = empty_defect_log()
    if historical:
        defect, history = fixed_history_defect(context)
        defect_log = defect_log.replace(
            row_line(["---"] * len(DEFECT_HEADERS)),
            row_line(["---"] * len(DEFECT_HEADERS)) + "\n" + defect,
            1,
        )
        defect_log += history + "\n"
    (lc / "REAL-USER-JOURNEY-DEFECT-LOG.md").write_text(
        defect_log, encoding="utf-8", newline="\n"
    )
    status = base_status(current_round, fixed=(40001,) if historical else ())
    phase = base_phase_status(current_round)
    return lc, status, phase, context


def errors_for(root, status, phase):
    try:
        errors = validator.validate_real_user_journey(root, status, phase)
    except Exception as error:
        raise AssertionError("validator raised instead of returning deterministic errors") from error
    assert isinstance(errors, list)
    return errors


def cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def mutate_table(path, header_first, row_contains, column, value):
    lines = path.read_text(encoding="utf-8").splitlines()
    headers = None
    for index, line in enumerate(lines):
        current = cells(line) if line.startswith("|") else []
        if current and current[0] == header_first and column in current:
            headers = current
            continue
        if headers and line.startswith("|") and row_contains in line and not all(
            set(item) <= {"-", ":"} for item in current
        ):
            current[headers.index(column)] = value
            lines[index] = row_line(current)
            path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
            return
        if headers and line and not line.startswith("|"):
            headers = None
    raise AssertionError((header_first, row_contains, column))


def remove_table_row(path, row_contains):
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.startswith("|") and row_contains in line:
            del lines[index]
            path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
            return
    raise AssertionError(row_contains)


def mutate_json_evidence(lc, evidence_id, mutate):
    record_path = lc / "REAL-USER-JOURNEY-ACCEPTANCE.md"
    line = next(line for line in record_path.read_text(encoding="utf-8").splitlines() if f"| {evidence_id} |" in line)
    row = dict(zip(EVIDENCE_HEADERS, cells(line)))
    path = lc / row["Native evidence path"]
    record = json.loads(path.read_text(encoding="utf-8"))
    mutate(record)
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    mutate_table(
        record_path, "Round", evidence_id, "Native evidence SHA-256",
        hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def mutate_receipt(lc, route_id, mutate, *, update_run_d3=False):
    acceptance_path = lc / "REAL-USER-JOURNEY-ACCEPTANCE.md"
    receipt_path = lc / "reviews" / ("OA-" + safe_suffix(route_id) + ".md")
    fields = parse_markdown(receipt_path)
    old_citation = citation(fields["Acceptance ID"], receipt_path, lc)
    mutate(fields)
    write_markdown(receipt_path, "Loop Owner Acceptance Receipt", fields)
    new_citation = citation(fields["Acceptance ID"], receipt_path, lc)
    text = acceptance_path.read_text(encoding="utf-8").replace(old_citation, new_citation, 1)
    acceptance_path.write_text(text, encoding="utf-8", newline="\n")
    if update_run_d3:
        mutate_table(
            acceptance_path, "Journey ID", route_id, "Task5 Run ID / D3 Receipt",
            fields["Run ID"] + " / " + fields["D3 Receipt"],
        )


def mutate_map(lc, mutate):
    map_path = lc / "SERVICE-ROUTE-MAP.json"
    old_hash = hashlib.sha256(map_path.read_bytes()).hexdigest()
    record = json.loads(map_path.read_text(encoding="utf-8"))
    mutate(record)
    map_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    new_hash = hashlib.sha256(map_path.read_bytes()).hexdigest()
    acceptance = lc / "REAL-USER-JOURNEY-ACCEPTANCE.md"
    acceptance.write_text(
        acceptance.read_text(encoding="utf-8").replace(old_hash, new_hash, 1),
        encoding="utf-8",
        newline="\n",
    )


def make_exempted(lc, status):
    defect_log = lc / "REAL-USER-JOURNEY-DEFECT-LOG.md"
    mutate_table(
        defect_log, "Defect ID", "| 40001 |", "State", "OWNER_EXEMPTED"
    )
    mutate_table(
        defect_log, "Defect ID", "| 40001 |",
        "Correction identity / engineering re-verification", "NOT_APPLICABLE",
    )
    mutate_table(defect_log, "Defect ID", "| 40001 |", "Retest round", "NOT_APPLICABLE")
    mutate_table(
        defect_log, "Defect ID", "| 40001 |",
        "Retest evidence ID / kind / SHA-256", "NOT_APPLICABLE",
    )
    mutate_table(
        defect_log, "Defect ID", "| 40001 |",
        "Exemption authority / impact / recovery",
        "OWNER-1 / bounded impact / restore direct UI",
    )
    exemption = {
        "record_role": "REAL_USER_JOURNEY_DEFECT_EXEMPTION",
        "evidence_schema_version": "4.0.0",
        "evidence_id": "EXEMPTION-40001",
        "defect_id": 40001,
        "candidate_id": CURRENT_ID,
        "candidate_hash": CURRENT_HASH,
        "round": 2,
        "route_id": "ROUTE-DIRECT",
        "authority": "OWNER-1",
        "impact": "bounded impact",
        "recovery_condition": "restore direct UI",
        "decision": "OWNER_EXEMPTED",
    }
    exemption_path = lc / "evidence/real-user-journey/exemptions/40001.json"
    exemption_path.parent.mkdir(parents=True, exist_ok=True)
    exemption_path.write_text(
        json.dumps(exemption, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    mutate_table(
        defect_log, "Defect ID", "FIXED_VERIFIED", "New state", "OWNER_EXEMPTED"
    )
    mutate_table(
        defect_log, "Defect ID", "OWNER_EXEMPTED", "Evidence / reason",
        citation("EXEMPTION-40001", exemption_path, lc),
    )
    status["real_user_journey_acceptance"]["fixed_verified_defect_ids"] = []
    status["real_user_journey_acceptance"]["exempted_defect_ids"] = [40001]
    return exemption_path


def install_priority_inversion(lc, status, context, *, keep_fixed=False):
    acceptance = lc / "REAL-USER-JOURNEY-ACCEPTANCE.md"
    second_line, second = evidence_row(
        lc, ROUTES[0], 1, 901, "SCREENSHOT", OLD_ID, OLD_HASH,
        result="DEFECT", screenshot_bytes=png_bytes("second-old-defect"),
    )
    lines = acceptance.read_text(encoding="utf-8").splitlines()
    first_index = next(index for index, line in enumerate(lines) if "| STEP-900 |" in line)
    lines.insert(first_index + 1, second_line)
    acceptance.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    mutate_table(
        acceptance, "Round", f"{OLD_ID} / {OLD_HASH}", "First and last evidence",
        context["old_defect"]["id"] + " / " + second["id"],
    )
    mutate_table(
        acceptance, "Round", f"{OLD_ID} / {OLD_HASH}", "Defect IDs", "40001,40002",
    )

    defect_log = lc / "REAL-USER-JOURNEY-DEFECT-LOG.md"
    if not keep_fixed:
        mutate_table(defect_log, "Defect ID", "| 40001 |", "State", "OPEN")
    mutate_table(
        defect_log, "Defect ID", "| 40001 |", "Affected layer / root cause",
        "BACKEND_CORE / shared capability defect",
    )
    mutate_table(
        defect_log, "Defect ID", "| 40001 |", "Boundary surface / evidence",
        "NOT_APPLICABLE",
    )
    lines = defect_log.read_text(encoding="utf-8").splitlines()
    if not keep_fixed:
        mutate_table(
            defect_log, "Defect ID", "| 40001 |",
            "Correction identity / engineering re-verification", "NOT_APPLICABLE",
        )
        mutate_table(
            defect_log, "Defect ID", "| 40001 |", "Retest round", "NOT_APPLICABLE"
        )
        mutate_table(
            defect_log, "Defect ID", "| 40001 |",
            "Retest evidence ID / kind / SHA-256", "NOT_APPLICABLE",
        )
        lines = defect_log.read_text(encoding="utf-8").splitlines()
        lines = [line for line in lines if "| OPEN | FIXED_VERIFIED |" not in line]
    first_defect_index = next(index for index, line in enumerate(lines) if line.startswith("| 40001 | 2026") and len(cells(line)) == len(DEFECT_HEADERS))
    second_defect = row_line((
        40002,
        f"2026-09-08T00:00:01Z / {OLD_ID} / 1 / JOURNEY-001 / ROUTE-DIRECT / {second['step']}",
        f"{second['id']} / {second['kind']} / {second['hash']}",
        "submit should render / submit still blocked",
        "HIGH / YES / ROUTE-DIRECT",
        "USER_SERVICE_BOUNDARY / second blocked submit feedback",
        "UI / " + second["id"],
        "ROUTE-DIRECT", 2, "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE",
        "NOT_APPLICABLE", "OPEN", "NOT_APPLICABLE",
    ))
    lines.insert(first_defect_index + 1, second_defect)
    lines.append(row_line((
        40002, "2026-09-08T00:00:01Z", "NOT_APPLICABLE", "OPEN",
        f"{OLD_ID} / {OLD_HASH}", 1, citation(second["id"], second["path"], lc),
    )))
    defect_log.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    if not keep_fixed:
        status["real_user_journey_acceptance"]["fixed_verified_defect_ids"] = []
        status["real_user_journey_acceptance"]["open_defect_ids"] = [40001, 40002]
    else:
        status["real_user_journey_acceptance"]["open_defect_ids"] = [40002]


def write_priority_exception(lc):
    evidence_id = "PRIORITY-EXCEPTION-40001-40002"
    record = {
        "record_role": "REAL_USER_JOURNEY_REPAIR_PRIORITY_EXCEPTION",
        "evidence_schema_version": "4.0.0",
        "evidence_id": evidence_id,
        "candidate_id": CURRENT_ID,
        "candidate_hash": CURRENT_HASH,
        "earlier_defect_id": 40001,
        "earlier_repair_sequence": 1,
        "earlier_layer": "BACKEND_CORE",
        "later_defect_id": 40002,
        "later_repair_sequence": 2,
        "later_layer": "USER_SERVICE_BOUNDARY",
        "authority": "OWNER-1",
        "rationale": "shared-core correction unblocks both defects",
        "decision": "ALLOW_PRIORITY_EXCEPTION",
    }
    path = lc / "evidence/real-user-journey/priority-exceptions/40001-40002.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    mutate_table(
        lc / "REAL-USER-JOURNEY-DEFECT-LOG.md", "Defect ID", "| 40001 |",
        "Priority exception justification", citation(evidence_id, path, lc),
    )
    return path


def add_successful_route_to_failed_round(lc, route_record):
    acceptance = lc / "REAL-USER-JOURNEY-ACCEPTANCE.md"
    added = []
    for offset, kind in enumerate(EVIDENCE_PLAN[route_record["route_id"]], start=910):
        line, item = evidence_row(
            lc, route_record, 1, offset, kind, OLD_ID, OLD_HASH,
        )
        added.append((line, item))
    lines = acceptance.read_text(encoding="utf-8").splitlines()
    insertion = next(index for index, line in enumerate(lines) if "| STEP-900 |" in line) + 1
    lines[insertion:insertion] = [line for line, _ in added]
    acceptance.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    mutate_table(
        acceptance, "Round", f"{OLD_ID} / {OLD_HASH}", "Attempted route IDs",
        "ROUTE-DIRECT," + route_record["route_id"],
    )
    mutate_table(
        acceptance, "Round", f"{OLD_ID} / {OLD_HASH}",
        "Required routes / passed / failed", "3 / 1 / 1",
    )
    mutate_table(
        acceptance, "Round", f"{OLD_ID} / {OLD_HASH}",
        "Unattempted route dispositions",
        "ROUTE-CENTER / DEPENDENCY_BLOCKED / RUJE-001-900 / 40001",
    )
    mutate_table(
        acceptance, "Round", f"{OLD_ID} / {OLD_HASH}", "First and last evidence",
        "RUJE-001-900 / " + added[-1][1]["id"],
    )


# Positive route coverage includes only the adopted/applicable steps and resolves
# the real Task5 receipt/Run lineage.
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, _ = write_project(root)
    assert errors_for(root, status, phase) == [], errors_for(root, status, phase)

# Direct visible evidence retains the 3.0 action/location/viewport contract and
# validates actual image header plus non-zero dimensions.
for column, message in (
    ("Action", "visible Action"),
    ("Visible location", "Visible location"),
    ("Viewport", "Viewport"),
):
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        lc, status, phase, _ = write_project(root)
        mutate_table(
            lc / "REAL-USER-JOURNEY-ACCEPTANCE.md", "Round", "RUJE-001-001",
            column, "NOT_APPLICABLE",
        )
        assert any(message in error for error in errors_for(root, status, phase))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, context = write_project(root)
    screenshot = context["evidence"][(1, "ROUTE-DIRECT", "SCREENSHOT")]
    screenshot["path"].write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 24)
    mutate_table(
        lc / "REAL-USER-JOURNEY-ACCEPTANCE.md", "Round", screenshot["id"],
        "Screenshot SHA-256", hashlib.sha256(screenshot["path"].read_bytes()).hexdigest(),
    )
    assert any("actual screenshot" in error for error in errors_for(root, status, phase))

for corrupt in (
    lambda data: data[:-12],
    lambda data: data[:data.index(b"IDAT") + 5]
    + bytes([data[data.index(b"IDAT") + 5] ^ 1])
    + data[data.index(b"IDAT") + 6:],
):
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        lc, status, phase, context = write_project(root)
        screenshot = context["evidence"][(1, "ROUTE-DIRECT", "SCREENSHOT")]
        screenshot["path"].write_bytes(corrupt(screenshot["path"].read_bytes()))
        mutate_table(
            lc / "REAL-USER-JOURNEY-ACCEPTANCE.md", "Round", screenshot["id"],
            "Screenshot SHA-256", hashlib.sha256(screenshot["path"].read_bytes()).hexdigest(),
        )
        assert any(
            "structurally complete screenshot" in error
            for error in errors_for(root, status, phase)
        )

# Nonvisual evidence is a kind-specific project evidence record bound to every
# route/candidate/round/step identity. A generic log or drifted identity fails.
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, context = write_project(root)
    item = context["evidence"][(1, "ROUTE-AGENT", "HUMAN_GOAL_MESSAGE")]
    mutate_json_evidence(lc, item["id"], lambda record: record.update({
        "record_role": "GENERIC_TEST_LOG", "event_or_result": {"message": "looks good"},
    }))
    errors = errors_for(root, status, phase)
    assert any("project evidence record role" in error for error in errors)
    assert any("kind-specific" in error for error in errors)

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, context = write_project(root)
    item = context["evidence"][(1, "ROUTE-AGENT", "PLATFORM_EFFECT")]
    mutate_json_evidence(lc, item["id"], lambda record: record.__setitem__("candidate_hash", "0" * 64))
    assert any("exact candidate/route/round/step" in error for error in errors_for(root, status, phase))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, context = write_project(root)
    item = context["evidence"][(1, "ROUTE-AGENT", "HUMAN_GOAL_MESSAGE")]
    mutate_table(
        lc / "REAL-USER-JOURNEY-ACCEPTANCE.md", "Round", item["id"],
        "Evidence kind", "SERVICE_ACTOR_IDENTITY",
    )
    assert any("evidence kind is not applicable" in error for error in errors_for(root, status, phase))

for route_id, kind, message in (
    ("ROUTE-AGENT", "AGENT_IDENTITY", "Agent identity"),
    ("ROUTE-CENTER", "SERVICE_ACTOR_IDENTITY", "service actor identity"),
    ("ROUTE-CENTER", "ASSISTED_ACTION", "assisted action"),
    ("ROUTE-CENTER", "USER_COMMUNICATION", "user communication"),
):
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        lc, status, phase, context = write_project(root)
        item = context["evidence"][(1, route_id, kind)]
        remove_table_row(lc / "REAL-USER-JOURNEY-ACCEPTANCE.md", "| " + item["id"] + " |")
        assert any(message in error for error in errors_for(root, status, phase))

for route_id in ("ROUTE-AGENT", "ROUTE-CENTER"):
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        lc, status, phase, context = write_project(root)
        item = context["evidence"][(1, route_id, "AUTHORIZATION_DECISION")]
        mutate_json_evidence(
            lc, item["id"],
            lambda record: record["event_or_result"].__setitem__("decision", "DENY"),
        )
        assert any("affirmative authorization" in error for error in errors_for(root, status, phase))

for route_id, kind, field, value, message in (
    ("ROUTE-AGENT", "AGENT_IDENTITY", "result", "FAILED", "identity success"),
    ("ROUTE-AGENT", "AGENT_IDENTITY", "result", "NOT_AUTHENTICATED", "identity success"),
    ("ROUTE-CENTER", "SERVICE_ACTOR_IDENTITY", "result", "DENIED", "identity success"),
    ("ROUTE-CENTER", "ASSISTED_ACTION", "result", "FAILED", "assisted action success"),
    (
        "ROUTE-CENTER", "ASSISTED_ACTION", "result", "NOT_PERFORMED",
        "assisted action success",
    ),
    (
        "ROUTE-CENTER", "USER_COMMUNICATION", "direction", "HUMAN_TO_SERVICE",
        "user communication direction/result",
    ),
    (
        "ROUTE-CENTER", "USER_COMMUNICATION", "content", "DELIVERY_FAILED",
        "user communication direction/result",
    ),
):
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        lc, status, phase, context = write_project(root)
        item = context["evidence"][(1, route_id, kind)]
        mutate_json_evidence(
            lc, item["id"],
            lambda record, field=field, value=value: record["event_or_result"].__setitem__(
                field, value
            ),
        )
        assert any(message in error for error in errors_for(root, status, phase))

# Receipt citations are resolved; the authoritative acceptance index and
# candidate/route/Run/D3/start joins cannot be satisfied by matching strings.
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, _ = write_project(root)
    status["loop_owner_acceptances"].remove("ACCEPTANCE-ROUTE-AGENT")
    assert any("acceptance index" in error for error in errors_for(root, status, phase))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, _ = write_project(root)
    mutate_receipt(
        lc, "ROUTE-AGENT",
        lambda fields: fields.__setitem__("Candidate ID / hash", exact_candidate("WRONG-CANDIDATE", CURRENT_HASH)),
    )
    assert any("receipt candidate" in error for error in errors_for(root, status, phase))

for field, value, message in (
    ("D3 Receipt", "D3-WRONG", "D3 join"),
    ("Run ID", "RUN-WRONG", "Run join"),
):
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        lc, status, phase, _ = write_project(root)
        mutate_receipt(
            lc, "ROUTE-AGENT", lambda fields, field=field, value=value: fields.__setitem__(field, value),
            update_run_d3=True,
        )
        assert any(message in error for error in errors_for(root, status, phase))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, context = write_project(root)
    route_id = "ROUTE-AGENT"
    old_d3 = "D3-AGENT"
    renamed_d3 = "D3-RENAMED"
    mutate_receipt(
        lc, route_id,
        lambda fields: fields.update({
            "D3 Receipt": renamed_d3,
            "Acceptance steps": fields["Acceptance steps"].replace(old_d3, renamed_d3),
        }),
        update_run_d3=True,
    )
    artifacts = context["task5_artifacts"][route_id]
    final_fields = parse_markdown(artifacts["final_path"])
    final_fields["D3 / Loop Owner Acceptance evidence"] = final_fields[
        "D3 / Loop Owner Acceptance evidence"
    ].replace(old_d3, renamed_d3)
    write_markdown(artifacts["final_path"], "Final Feature Verification", final_fields)
    mutate_table(
        lc / "REAL-USER-JOURNEY-ACCEPTANCE.md", "Journey ID", route_id,
        "Task5 Final Verification / D3 citations",
        "FINAL:" + citation(final_fields["Verification ID"], artifacts["final_path"], lc)
        + "; D3:" + artifacts["d3_citation"],
    )
    assert any("actual Task5 D3 artifact" in error for error in errors_for(root, status, phase))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, context = write_project(root)
    route_id = "ROUTE-AGENT"
    artifacts = context["task5_artifacts"][route_id]
    d3 = json.loads(artifacts["d3_path"].read_text(encoding="utf-8"))
    d3.update({
        "reused_evidence": [],
        "new_evidence": ["ROUTE-SEAM-AGENT"],
        "repeated_checks": [{
            "source_layer": "D2",
            "reason": "environment materially differs",
            "scope_difference": "route seam",
            "risk": "runtime",
            "result": "PASS",
        }],
    })
    artifacts["d3_path"].write_text(
        json.dumps(d3, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    mutate_table(
        lc / "REAL-USER-JOURNEY-ACCEPTANCE.md", "Journey ID", route_id,
        "Task5 Final Verification / D3 citations",
        "FINAL:" + artifacts["final_citation"] + "; D3:"
        + citation(d3["receipt_id"], artifacts["d3_path"], lc),
    )
    assert errors_for(root, status, phase) == [], errors_for(root, status, phase)

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, context = write_project(root)
    receipt = context["receipts"]["ROUTE-AGENT"]
    receipt.write_text(receipt.read_text(encoding="utf-8") + "\nmutated\n", encoding="utf-8")
    assert any("receipt hash" in error for error in errors_for(root, status, phase))

# A prior candidate may own a failed round. The round stops at its real defect,
# then the current candidate restarts the complete graph and supplies retest evidence.
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, _ = write_project(root, historical=True)
    assert errors_for(root, status, phase) == [], errors_for(root, status, phase)

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, _ = write_project(root, historical=True)
    mutate_table(
        lc / "REAL-USER-JOURNEY-ACCEPTANCE.md", "Round", f"{OLD_ID} / {OLD_HASH}",
        "Unattempted route dispositions",
        "ROUTE-AGENT / DEPENDENCY_BLOCKED / RUJE-001-900 / 40001",
    )
    assert any("unattempted adopted route" in error for error in errors_for(root, status, phase))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, _ = write_project(root, historical=True)
    mutate_table(
        lc / "REAL-USER-JOURNEY-ACCEPTANCE.md", "Round", f"{OLD_ID} / {OLD_HASH}",
        "Unattempted route dispositions",
        "; ".join(
            route_id + " / DEPENDENCY_BLOCKED / MISSING-EVIDENCE / 40001"
            for route_id in ("ROUTE-AGENT", "ROUTE-CENTER")
        ),
    )
    assert any("blocking evidence" in error for error in errors_for(root, status, phase))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, _ = write_project(root, historical=True)
    defect_log = lc / "REAL-USER-JOURNEY-DEFECT-LOG.md"
    mutate_table(
        defect_log, "Defect ID", "| 40001 |",
        "Severity / reachability / blocking scope", "HIGH / YES / ROUTE-DIRECT",
    )
    mutate_table(
        defect_log, "Defect ID", "| 40001 |", "Affected routes", "ROUTE-DIRECT",
    )
    assert any("does not cover omitted route" in error for error in errors_for(root, status, phase))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, _ = write_project(root, historical=True)
    acceptance = lc / "REAL-USER-JOURNEY-ACCEPTANCE.md"
    mutate_table(
        acceptance, "Round", f"{OLD_ID} / {OLD_HASH}",
        "Unattempted route dispositions",
        "; ".join(
            route_id + " / GLOBAL_BLOCKED / RUJE-001-900 / 40001"
            for route_id in ("ROUTE-AGENT", "ROUTE-CENTER")
        ),
    )
    assert any("validated global boundary" in error for error in errors_for(root, status, phase))

# A failed round may contain another attempted route that passed. It stops only
# the failed route at its defect and does not falsely mark every attempt failed.
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, _ = write_project(root, historical=True)
    add_successful_route_to_failed_round(lc, ROUTES[1])
    assert errors_for(root, status, phase) == [], errors_for(root, status, phase)

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, _ = write_project(root, historical=True)
    remove_table_row(lc / "REAL-USER-JOURNEY-ACCEPTANCE.md", "| STEP-900 |")
    assert any("attempted route entry" in error for error in errors_for(root, status, phase))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, _ = write_project(root, historical=True)
    mutate_table(
        lc / "REAL-USER-JOURNEY-ACCEPTANCE.md", "Round", f"{OLD_ID} / {OLD_HASH}",
        "Defect IDs", "NONE",
    )
    assert any("REWORK/BLOCKED round defects" in error for error in errors_for(root, status, phase))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, context = write_project(root, historical=True)
    old = context["old_defect"]
    current = context["evidence"][(2, "ROUTE-DIRECT", "SCREENSHOT")]
    old["path"].write_bytes(current["path"].read_bytes())
    mutate_table(
        lc / "REAL-USER-JOURNEY-ACCEPTANCE.md", "Round", old["id"],
        "Screenshot SHA-256", current["hash"],
    )
    assert any("digest cannot be reused across rounds" in error for error in errors_for(root, status, phase))

# Defect discovery and FIXED history resolve the actual route evidence; stable
# strings with no matching row/file are insufficient.
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, _ = write_project(root, historical=True)
    mutate_table(
        lc / "REAL-USER-JOURNEY-DEFECT-LOG.md", "Defect ID", "| 40001 |",
        "Evidence ID / kind / SHA-256", "MISSING / SCREENSHOT / " + "0" * 64,
    )
    assert any("defect discovery evidence" in error for error in errors_for(root, status, phase))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, _ = write_project(root, historical=True)
    mutate_table(
        lc / "REAL-USER-JOURNEY-DEFECT-LOG.md", "Defect ID", "FIXED_VERIFIED",
        "Evidence / reason", "MISSING / sha256:" + "0" * 64 + " / reviews/missing.md",
    )
    assert any("FIXED_VERIFIED history evidence" in error for error in errors_for(root, status, phase))

for column, value in (
    ("Candidate ID / SHA-256", f"{CURRENT_ID} / {CURRENT_HASH}"),
    ("Round", "2"),
):
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        lc, status, phase, _ = write_project(root, historical=True)
        mutate_table(
            lc / "REAL-USER-JOURNEY-DEFECT-LOG.md", "Defect ID",
            "NOT_APPLICABLE | OPEN", column, value,
        )
        assert any("history candidate/round" in error for error in errors_for(root, status, phase))

# Owner exemption is a resolved project decision record whose authority, impact,
# recovery condition, candidate, route, and defect identity join the history.
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, _ = write_project(root, historical=True)
    make_exempted(lc, status)
    assert errors_for(root, status, phase) == [], errors_for(root, status, phase)

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, _ = write_project(root, historical=True)
    exemption_path = make_exempted(lc, status)
    exemption = json.loads(exemption_path.read_text(encoding="utf-8"))
    exemption["authority"] = "WRONG-OWNER"
    exemption_path.write_text(
        json.dumps(exemption, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    mutate_table(
        lc / "REAL-USER-JOURNEY-DEFECT-LOG.md", "Defect ID", "OWNER_EXEMPTED",
        "Evidence / reason", citation("EXEMPTION-40001", exemption_path, lc),
    )
    assert any("OWNER_EXEMPTED history evidence" in error for error in errors_for(root, status, phase))

# Scheduled defects normally follow service-boundary -> orchestration -> core.
# A recorded evidence-bearing justification permits an intentional inversion.
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, _, context = write_project(root, historical=True)
    install_priority_inversion(lc, status, context)
    errors = validator.validate_defect_log(root, status)
    assert any("repair priority order" in error for error in errors)
    mutate_table(
        lc / "REAL-USER-JOURNEY-DEFECT-LOG.md", "Defect ID", "| 40001 |",
        "Priority exception justification", "because it is easier",
    )
    assert any("repair priority order" in error for error in validator.validate_defect_log(root, status))
    write_priority_exception(lc)
    assert not any("repair priority order" in error for error in validator.validate_defect_log(root, status))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, _, context = write_project(root, historical=True)
    install_priority_inversion(lc, status, context, keep_fixed=True)
    assert any(
        "repair priority order" in error
        for error in validator.validate_defect_log(root, status)
    ), "a completed core repair bypassed the boundary-first order"
    path = write_priority_exception(lc)
    assert not any(
        "repair priority order" in error
        for error in validator.validate_defect_log(root, status)
    )
    record = json.loads(path.read_text(encoding="utf-8"))
    record["later_defect_id"] = 49999
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    mutate_table(
        lc / "REAL-USER-JOURNEY-DEFECT-LOG.md", "Defect ID", "| 40001 |",
        "Priority exception justification",
        citation("PRIORITY-EXCEPTION-40001-40002", path, lc),
    )
    assert any(
        "priority exception evidence" in error
        for error in validator.validate_defect_log(root, status)
    )

# Malformed status/map containers return deterministic validation errors instead
# of TypeError, including invalid counts, IDs, index members, and route lists.
malformed_cases = (
    lambda lc, status: status["real_user_journey_acceptance"].__setitem__("current_round", []),
    lambda lc, status: status["real_user_journey_acceptance"].__setitem__("passed_journey_count", []),
    lambda lc, status: status.__setitem__("loop_owner_acceptances", [[]]),
    lambda lc, status: mutate_map(lc, lambda record: record.__setitem__("map_id", [])),
    lambda lc, status: mutate_map(lc, lambda record: record["journeys"][0]["routes"][0].__setitem__("acceptance_evidence_ids", None)),
    lambda lc, status: mutate_map(lc, lambda record: record["journeys"][0].__setitem__("routes", [None])),
)
for mutate in malformed_cases:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        lc, status, phase, _ = write_project(root)
        mutate(lc, status)
        assert errors_for(root, status, phase), "malformed 4.0 input was accepted"

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, _ = write_project(root)
    status["phase_gates"] = []
    assert errors_for(root, status, phase)

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc, status, phase, _ = write_project(root)
    phase["phases"] = []
    assert errors_for(root, status, phase)

project_validator_source = (ROOT / "lc-coding/scripts/validate_project.py").read_text(encoding="utf-8")
assert "status.get('status_schema_version') in {'3.0.0','4.0.0'}" in project_validator_source

print("PASS: 4.0 journey acceptance resolves route-faithful first-hand evidence")
