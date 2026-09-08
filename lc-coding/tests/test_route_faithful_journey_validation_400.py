import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "lc-coding/scripts/validate_real_user_journey.py"
spec = importlib.util.spec_from_file_location("journey_validator_400", MODULE)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

HASH = "4" * 64
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUB"
    "AScY42YAAAAASUVORK5CYII="
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
        "acceptance_evidence_ids": ["ADOPTED-EVIDENCE-" + route_id],
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

EVIDENCE_KINDS = {
    "ROUTE-DIRECT": ["SCREENSHOT"],
    "ROUTE-AGENT": [
        "HUMAN_GOAL_MESSAGE", "AGENT_IDENTITY", "REQUEST_MESSAGE", "TASK_TRANSITION",
        "AUTHORIZATION_DECISION", "RESULT_ARTIFACT", "PLATFORM_EFFECT", "AGENT_RESPONSE",
        "AUDIT_EVENT", "RESULT_DELIVERY",
    ],
    "ROUTE-CENTER": [
        "USER_REQUEST", "SERVICE_ACTOR_IDENTITY", "DELEGATION_BASIS", "ASSISTED_ACTION",
        "PLATFORM_EFFECT", "USER_COMMUNICATION", "AUDIT_EVENT", "RESULT_DELIVERY",
    ],
}


def base_status(round_number=1):
    status = json.loads((ROOT / "lc-coding/templates/STATUS.json").read_text(encoding="utf-8"))
    status.update({
        "status_schema_version": "4.0.0",
        "project_id": "PROJECT-1",
        "lccoding_applicability": "WHOLE_PRODUCT_FIT",
        "product_service_strategy": "MIXED",
        "service_route_map": "ADOPTED",
        "canonical_candidate": {"candidate_id": "CANDIDATE-400", "candidate_hash": HASH},
        "current_phase": "REAL_USER_JOURNEY_ACCEPTANCE",
    })
    status["phase_gates"]["REAL_USER_JOURNEY_ACCEPTED"] = "REAL_USER_JOURNEY_ACCEPTED"
    status["real_user_journey_acceptance"] = {
        "state": "REAL_USER_JOURNEY_ACCEPTED",
        "candidate_id": "CANDIDATE-400",
        "candidate_hash": HASH,
        "coverage_state": "COMPLETE",
        "acceptance_environment_state": "VERIFIED",
        "current_round": round_number,
        "complete_round_count": 1,
        "required_journey_count": 3,
        "passed_journey_count": 3,
        "failed_journey_count": 0,
        "not_applicable_journey_count": 0,
        "open_defect_ids": [],
        "fixed_verified_defect_ids": [],
        "exempted_defect_ids": [],
        "deferred_defect_ids": [],
        "reopened_defect_ids": [],
        "acceptance_record_reference": "REAL-USER-JOURNEY-ACCEPTANCE.md",
        "defect_log_reference": "REAL-USER-JOURNEY-DEFECT-LOG.md",
        "owner_result": "REAL_USER_JOURNEY_ACCEPTED",
    }
    return status


def base_phase_status(round_number=1):
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


def write_project(root, *, round_number=1, restart="YES"):
    lc = root / ".lccoding"
    lc.mkdir()
    map_path = lc / "SERVICE-ROUTE-MAP.json"
    map_path.write_text(json.dumps(SERVICE_MAP, indent=2) + "\n", encoding="utf-8", newline="\n")
    map_hash = hashlib.sha256(map_path.read_bytes()).hexdigest()

    coverage_rows = []
    evidence_rows = []
    evidence_number = 1
    for route_record in ROUTES:
        route_id = route_record["route_id"]
        authority = route_record["authority"]
        coverage_rows.append(
            "| JOURNEY-001 | {route_id} | {route_kind} | {actor_id} / {actor_kind} | "
            "{action_id} / {resource_id} / {delegation} | {entry} | {outcome} | {adopted} | REQUIRED |".format(
                route_id=route_id,
                route_kind=route_record["route_kind"],
                actor_id=route_record["actor_id"],
                actor_kind=route_record["actor_kind"],
                action_id=authority["action_id"],
                resource_id=authority["resource_id"],
                delegation=authority["delegation_basis_id"],
                entry=route_record["promised_entry"],
                outcome=route_record["human_observable_outcome"],
                adopted=",".join(route_record["acceptance_evidence_ids"]),
            )
        )
        for evidence_kind in EVIDENCE_KINDS[route_id]:
            step_id = f"STEP-{evidence_number:03d}"
            evidence_id = f"RUJE-{evidence_number:03d}"
            directory = lc / f"evidence/real-user-journey/round-{round_number:03d}/JOURNEY-001/{route_id}"
            directory.mkdir(parents=True, exist_ok=True)
            is_screenshot = evidence_kind == "SCREENSHOT"
            suffix = ".png" if is_screenshot else ".txt"
            evidence_path = directory / (step_id + suffix)
            final = (
                route_record["route_kind"] == "DIRECT_PRODUCT" and is_screenshot
            ) or evidence_kind == "RESULT_DELIVERY"
            human_outcome = route_record["human_observable_outcome"] if final else "NOT_APPLICABLE"
            audit_id = (
                route_record["audit_event_ids"][0]
                if evidence_kind == "AUDIT_EVENT" else "NOT_APPLICABLE"
            )
            if is_screenshot:
                evidence_path.write_bytes(PNG)
            else:
                evidence_path.write_text(
                    evidence_kind.lower().replace("_", " ") + " actual first-hand evidence\n",
                    encoding="utf-8",
                    newline="\n",
                )
            relative = evidence_path.relative_to(lc).as_posix()
            if is_screenshot:
                relative = ".lccoding/" + relative
            digest = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
            evidence_rows.append(
                f"| {round_number} | JOURNEY-001 | {route_id} | {route_record['route_kind']} | "
                f"{step_id} | {evidence_id} | {'VISIBLE' if is_screenshot else 'NONVISUAL'} | "
                f"{evidence_kind} | {route_record['actor_id']} | {authority['action_id']} | "
                f"{authority['delegation_basis_id']} | {audit_id} | EXPECTED / OBSERVED | "
                f"{relative} | {digest} | {human_outcome} | PASS |"
            )
            evidence_number += 1

    (lc / "REAL-USER-JOURNEY-ACCEPTANCE.md").write_text(
        f"""# Real User Journey Acceptance

## Candidate identity

- Acceptance ID: RUJA-400-001
- Candidate ID: CANDIDATE-400
- Candidate SHA-256: {HASH}
- Status schema version: 4.0.0
- Service Route Map ID / exact hash: SERVICE-ROUTES-1 / sha256:{map_hash}

## Route-faithful 4.0 journey coverage

| Journey ID | Service Route ID | Route kind | Actor ID / kind | Authority action / resource / delegation | Actual external entry | Expected human-observable outcome | Adopted acceptance evidence IDs | Applicability |
|---|---|---|---|---|---|---|---|---|
{chr(10).join(coverage_rows)}

## Acceptance rounds

| Round | Candidate ID / SHA-256 | Started from every actual route entry | Required routes / passed / failed | First and last evidence | Defect IDs | Result |
|---|---|---|---|---|---|---|
| {round_number} | CANDIDATE-400 / {HASH} | {restart} | 3 / 3 / 0 | RUJE-001 / RUJE-{evidence_number - 1:03d} | NONE | PASS |

## Route-faithful 4.0 evidence digests

| Round | Journey ID | Service Route ID | Route kind | Step ID | Evidence ID | Step mode | Evidence kind | Actor ID | Authority action ID | Delegation basis ID | Audit event ID | Expected / observed route result | Evidence path | Evidence SHA-256 | Human-observable outcome | Result |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
{chr(10).join(evidence_rows)}
""",
        encoding="utf-8",
        newline="\n",
    )
    (lc / "REAL-USER-JOURNEY-DEFECT-LOG.md").write_text(
        """# Real User Journey Defect Log

- Status schema version: 4.0.0
- Normal repair priority: USER_SERVICE_BOUNDARY -> WORKFLOW_ORCHESTRATION -> BACKEND_CORE

## Route-faithful defect register

| Defect ID | Discovery time / candidate / round / Journey / Route / Step | Evidence ID / kind / SHA-256 | Expected / observed | Severity / reachability / blocking scope | Affected layer / root cause | Boundary surface / evidence | Affected routes | Correction identity / engineering re-verification | Retest round | State | Exemption authority / impact / recovery |
|---|---|---|---|---|---|---|---|---|---|---|---|

## State history

| Defect ID | Event time | Prior state | New state | Candidate ID / SHA-256 | Evidence / reason |
|---|---|---|---|---|---|
""",
        encoding="utf-8",
        newline="\n",
    )
    return lc


def errors_for(root, status=None, phase=None):
    return validator.validate_real_user_journey(
        root, status or base_status(), phase or base_phase_status()
    )


with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc = write_project(root)
    assert errors_for(root) == [], errors_for(root)

    record = lc / "REAL-USER-JOURNEY-ACCEPTANCE.md"
    original = record.read_text(encoding="utf-8")
    direct_path = lc / "evidence/real-user-journey/round-001/JOURNEY-001/ROUTE-DIRECT/STEP-001.png"
    direct_path.unlink()
    assert any("screenshot" in error and "unreadable" in error for error in errors_for(root))

    direct_path.write_bytes(PNG)
    record.write_text(original.replace(hashlib.sha256(PNG).hexdigest(), "0" * 64, 1), encoding="utf-8")
    assert any("screenshot digest" in error for error in errors_for(root))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc = write_project(root)
    record = lc / "REAL-USER-JOURNEY-ACCEPTANCE.md"
    text = record.read_text(encoding="utf-8")
    text = text.replace("| NONVISUAL | HUMAN_GOAL_MESSAGE |", "| NONVISUAL | SCREENSHOT |", 1)
    record.write_text(text, encoding="utf-8")
    assert any("non-visual" in error and "screenshot" in error for error in errors_for(root))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc = write_project(root)
    record = lc / "REAL-USER-JOURNEY-ACCEPTANCE.md"
    text = record.read_text(encoding="utf-8")
    text = text.replace(
        "| NONVISUAL | HUMAN_GOAL_MESSAGE |",
        "| NONVISUAL | SERVICE_ACTOR_IDENTITY |",
        1,
    )
    record.write_text(text, encoding="utf-8")
    assert any("evidence kind is invalid for PERSONAL_AGENT" in error for error in errors_for(root))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc = write_project(root)
    record = lc / "REAL-USER-JOURNEY-ACCEPTANCE.md"
    record.write_text(
        record.read_text(encoding="utf-8").replace(
            "| EXPECTED / OBSERVED |", "| NOT_APPLICABLE / NOT_APPLICABLE |", 1
        ),
        encoding="utf-8",
    )
    assert any("expected and observed route result" in error for error in errors_for(root))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc = write_project(root)
    evidence_path = lc / "evidence/real-user-journey/round-001/JOURNEY-001/ROUTE-AGENT/STEP-002.txt"
    evidence_path.unlink()
    assert any("non-visual evidence" in error and "unreadable" in error for error in errors_for(root))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc = write_project(root)
    source = lc / "evidence/real-user-journey/round-001/JOURNEY-001/ROUTE-AGENT/STEP-002.txt"
    native = lc / "reviews/agent-goal.txt"
    native.parent.mkdir()
    source.replace(native)
    record = lc / "REAL-USER-JOURNEY-ACCEPTANCE.md"
    record.write_text(
        record.read_text(encoding="utf-8").replace(
            "evidence/real-user-journey/round-001/JOURNEY-001/ROUTE-AGENT/STEP-002.txt",
            "reviews/agent-goal.txt",
            1,
        ),
        encoding="utf-8",
    )
    assert errors_for(root) == [], errors_for(root)

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc = write_project(root)
    evidence_path = lc / "evidence/real-user-journey/round-001/JOURNEY-001/ROUTE-AGENT/STEP-002.txt"
    evidence_path.write_text("mutated first-hand evidence\n", encoding="utf-8")
    assert any("non-visual evidence digest" in error for error in errors_for(root))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc = write_project(root)
    record = lc / "REAL-USER-JOURNEY-ACCEPTANCE.md"
    lines = record.read_text(encoding="utf-8").splitlines()
    lines = [line for line in lines if not (line.startswith("| JOURNEY-001 | ROUTE-CENTER |"))]
    record.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert any("exactly cover" in error and "adopted" in error for error in errors_for(root))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc = write_project(root)
    record = lc / "REAL-USER-JOURNEY-ACCEPTANCE.md"
    text = record.read_text(encoding="utf-8")
    text = text.replace("CANDIDATE-400 / " + HASH, "WRONG-CANDIDATE / " + HASH, 1)
    record.write_text(text, encoding="utf-8")
    assert any("round candidate identity" in error for error in errors_for(root))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc = write_project(root)
    record = lc / "REAL-USER-JOURNEY-ACCEPTANCE.md"
    lines = record.read_text(encoding="utf-8").splitlines()
    first = next(line for line in lines if "| RUJE-002 |" in line)
    second_index = next(index for index, line in enumerate(lines) if "| RUJE-003 |" in line)
    first_cells = first.split("|")
    second_cells = lines[second_index].split("|")
    second_cells[6] = first_cells[6]
    second_cells[14] = first_cells[14]
    second_cells[15] = first_cells[15]
    lines[second_index] = "|".join(second_cells)
    record.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert any("unique evidence" in error for error in errors_for(root))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc = write_project(root)
    record = lc / "REAL-USER-JOURNEY-ACCEPTANCE.md"
    text = record.read_text(encoding="utf-8")
    outcome = ROUTES[1]["human_observable_outcome"]
    text = text.replace("| " + outcome + " | PASS |", "| NOT_APPLICABLE | PASS |", 1)
    record.write_text(text, encoding="utf-8")
    assert any("final human-observable outcome" in error for error in errors_for(root))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    write_project(root, round_number=2, restart="NO")
    assert any("restart from every actual route entry" in error for error in errors_for(
        root, base_status(2), base_phase_status(2)
    ))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc = write_project(root, round_number=2, restart="YES")
    record = lc / "REAL-USER-JOURNEY-ACCEPTANCE.md"
    text = record.read_text(encoding="utf-8")
    current_row = next(line for line in text.splitlines() if line.startswith("| 2 | CANDIDATE-400"))
    prior_row = current_row.replace("| 2 |", "| 1 |", 1)
    record.write_text(text.replace(current_row, prior_row + "\n" + current_row, 1), encoding="utf-8")
    status = base_status(2)
    status["real_user_journey_acceptance"]["complete_round_count"] = 2
    phase = base_phase_status(2)
    phase["phases"]["REAL_USER_JOURNEY_ACCEPTANCE"]["complete_rounds"] = 2
    assert any("complete round lacks route evidence" in error for error in errors_for(root, status, phase))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc = write_project(root)
    map_path = lc / "SERVICE-ROUTE-MAP.json"
    route_map = json.loads(map_path.read_text(encoding="utf-8"))
    route_map["journeys"][0]["routes"][1]["audit_event_ids"].append("AUDIT-AGENT-2")
    old_hash = hashlib.sha256(map_path.read_bytes()).hexdigest()
    map_path.write_text(json.dumps(route_map, indent=2) + "\n", encoding="utf-8", newline="\n")
    new_hash = hashlib.sha256(map_path.read_bytes()).hexdigest()
    record = lc / "REAL-USER-JOURNEY-ACCEPTANCE.md"
    record.write_text(record.read_text(encoding="utf-8").replace(old_hash, new_hash, 1), encoding="utf-8")
    assert any("exactly cover adopted audit" in error for error in errors_for(root))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc = write_project(root)
    defect_log = lc / "REAL-USER-JOURNEY-DEFECT-LOG.md"
    text = defect_log.read_text(encoding="utf-8")
    defect_row = (
        "| 40001 | 2026-09-08T00:00:00Z / CANDIDATE-399 / 1 / JOURNEY-001 / ROUTE-AGENT / STEP-002 | "
        "RUJE-002 / HUMAN_GOAL_MESSAGE / " + "1" * 64 + " | EXPECTED / OBSERVED | HIGH / YES / ROUTE-AGENT | "
        "USER_SERVICE_BOUNDARY / request rendering | AGENT_SERVICE / RUJE-002 | ROUTE-AGENT | NOT_APPLICABLE | "
        "NOT_APPLICABLE | OWNER_EXEMPTED | OWNER-1 / bounded impact / restore request surface |"
    )
    text = text.replace(
        "|---|---|---|---|---|---|---|---|---|---|---|---|\n\n## State history",
        "|---|---|---|---|---|---|---|---|---|---|---|---|\n" + defect_row + "\n\n## State history",
    )
    history_row = (
        "| 40001 | 2026-09-08T00:00:00Z | NOT_APPLICABLE | OPEN | CANDIDATE-399 / "
        + "3" * 64 + " | RUJE-002 |\n"
        "| 40001 | 2026-09-08T00:01:00Z | OPEN | OWNER_EXEMPTED | CANDIDATE-400 / "
        + HASH + " | OWNER-1 |"
    )
    history_header = (
        "## State history\n\n"
        "| Defect ID | Event time | Prior state | New state | Candidate ID / SHA-256 | Evidence / reason |\n"
        "|---|---|---|---|---|---|\n"
    )
    text = text.replace(history_header, history_header + history_row + "\n", 1)
    defect_log.write_text(text, encoding="utf-8")
    status = base_status()
    status["real_user_journey_acceptance"]["exempted_defect_ids"] = [40001]
    assert errors_for(root, status) == [], errors_for(root, status)

    defect_log.write_text(text.replace("AGENT_SERVICE / RUJE-002", "NOT_APPLICABLE", 1), encoding="utf-8")
    assert any("boundary evidence" in error for error in errors_for(root, status))

    defect_log.write_text(
        text.replace("AGENT_SERVICE / RUJE-002", "AGENT_SERVICE / MISSING-EVIDENCE", 1),
        encoding="utf-8",
    )
    assert any("boundary evidence" in error for error in errors_for(root, status))

    defect_log.write_text(
        text.replace("AGENT_SERVICE / RUJE-002", "UI / RUJE-002", 1),
        encoding="utf-8",
    )
    assert errors_for(root, status) == [], errors_for(root, status)

    defect_log.write_text(
        text.replace(
            "USER_SERVICE_BOUNDARY / request rendering",
            "UNKNOWN_LAYER / request rendering",
            1,
        ),
        encoding="utf-8",
    )
    assert any("affected layer" in error for error in errors_for(root, status))

    defect_log.write_text(text.replace("OWNER-1 / bounded impact / restore request surface", "NOT_APPLICABLE", 1), encoding="utf-8")
    assert any("Owner exemption" in error for error in errors_for(root, status))

    no_history = text.replace(history_row + "\n", "", 1)
    defect_log.write_text(no_history, encoding="utf-8")
    assert any("complete state history" in error for error in errors_for(root, status))

project_validator_source = (ROOT / "lc-coding/scripts/validate_project.py").read_text(encoding="utf-8")
assert "status.get('status_schema_version') in {'3.0.0','4.0.0'}" in project_validator_source

print("PASS: 4.0 journey acceptance is route-faithful and evidence-bound")
