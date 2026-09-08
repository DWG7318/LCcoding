import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "lc-coding/scripts/validate_real_user_journey.py"
spec = importlib.util.spec_from_file_location("journey_validator", MODULE)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

HASH = "1" * 64


def base_status():
    status = json.loads((ROOT / "lc-coding/templates/STATUS.json").read_text(encoding="utf-8"))
    for field in ("lccoding_applicability", "product_service_strategy", "service_route_map"):
        status.pop(field)
    status["status_schema_version"] = "3.0.0"
    status["canonical_candidate"] = {"candidate_id": "CANDIDATE-300", "candidate_hash": HASH}
    status["current_phase"] = "REAL_USER_JOURNEY_ACCEPTANCE"
    status["phase_gates"]["INITIAL_READY"] = "PASS"
    status["phase_gates"]["CALABASH_UPGRADE_READY"] = "PASS"
    status["phase_gates"]["ALL_REQUIRED_RUNS_ACCEPTED"] = "ALL_REQUIRED_RUNS_ACCEPTED"
    status["real_user_journey_acceptance"] = {
        "state": "REAL_USER_JOURNEY_ACCEPTED",
        "candidate_id": "CANDIDATE-300",
        "candidate_hash": HASH,
        "coverage_state": "COMPLETE",
        "acceptance_environment_state": "VERIFIED",
        "current_round": 1,
        "complete_round_count": 1,
        "required_journey_count": 1,
        "passed_journey_count": 1,
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
    status["phase_gates"]["REAL_USER_JOURNEY_ACCEPTED"] = "REAL_USER_JOURNEY_ACCEPTED"
    return status


def base_phase_status():
    phase = json.loads((ROOT / "lc-coding/templates/PHASE-STATUS.json").read_text(encoding="utf-8"))
    phase["status_schema_version"] = "3.0.0"
    phase["current_phase"] = "REAL_USER_JOURNEY_ACCEPTANCE"
    for phase_id in ("INITIAL", "PRODUCT_FORMATION", "REAL_PRODUCT_INTEGRATION"):
        phase["phases"][phase_id]["status"] = "COMPLETE"
    phase["phases"]["INITIAL"]["exit_gate"] = "PASS"
    phase["phases"]["PRODUCT_FORMATION"]["exit_evidence"] = "ACCEPTED"
    phase["phases"]["REAL_PRODUCT_INTEGRATION"]["aggregate_exit_gate"] = "ALL_REQUIRED_RUNS_ACCEPTED"
    record = phase["phases"]["REAL_USER_JOURNEY_ACCEPTANCE"]
    record.update({
        "status": "COMPLETE",
        "acceptance_record": "REAL-USER-JOURNEY-ACCEPTANCE.md",
        "defect_log": "REAL-USER-JOURNEY-DEFECT-LOG.md",
        "complete_rounds": 1,
        "exit_gate": "REAL_USER_JOURNEY_ACCEPTED",
    })
    return phase


def write_project(root, *, screenshot=b"visible-result", round_number=1, start="YES"):
    lc = root / ".lccoding"
    evidence = lc / "evidence/real-user-journey/round-001/JOURNEY-001"
    evidence.mkdir(parents=True)
    shot = evidence / "STEP-001.png"
    shot.write_bytes(screenshot)
    digest = hashlib.sha256(screenshot).hexdigest()
    (lc / "REAL-USER-JOURNEY-ACCEPTANCE.md").write_text(
        f"""# Real User Journey Acceptance

## Candidate identity

- Acceptance ID: RUJA-001
- Candidate ID: CANDIDATE-300
- Candidate SHA-256: {HASH}

## Journey coverage

| Journey ID | Actor / permission | Start | Preconditions / safe data | Ordered visible actions | Expected visible results / outcome | Exception / recovery routes | Trace | Applicability |
|---|---|---|---|---|---|---|---|---|
| JOURNEY-001 | USER | HOME | READY | STEP-001 | RESULT | NONE | TRACE-001 | REQUIRED |

## Acceptance rounds

| Round | Candidate ID / SHA-256 | Started from home entry | Required / passed / failed / N/A | First and last evidence | Defect IDs | Result |
|---|---|---|---|---|---|---|
| {round_number} | CANDIDATE-300 / {HASH} | {start} | 1 / 1 / 0 / 0 | STEP-001 / STEP-001 | NONE | PASS |

## Evidence digests

| Round | Journey ID | Step ID | Action | Expected / observed visible result | Visible location | Viewport | Screenshot path | Screenshot SHA-256 | Result |
|---|---|---|---|---|---|---|---|---|---|
| {round_number} | JOURNEY-001 | STEP-001 | CLICK | RESULT / RESULT | HOME | 1280x720@1 | .lccoding/evidence/real-user-journey/round-001/JOURNEY-001/STEP-001.png | {digest} | PASS |

## Defect pointers

- Defect log reference: REAL-USER-JOURNEY-DEFECT-LOG.md
- Owner result: REAL_USER_JOURNEY_ACCEPTED
""",
        encoding="utf-8",
    )
    (lc / "REAL-USER-JOURNEY-DEFECT-LOG.md").write_text(
        """# Real User Journey Defect Log

## Defect register

| Defect ID | Discovery time / candidate / round / Journey / Step | Screenshot SHA-256 | Expected / observed | Severity / reachability / blocking scope | Visible layer / root cause | Affected surfaces | Correction identity / engineering re-verification | Retest round | State | Exemption authority / impact / recovery |
|---|---|---|---|---|---|---|---|---|---|---|

## State history

| Defect ID | Event time | Prior state | New state | Candidate ID / SHA-256 | Evidence / reason |
|---|---|---|---|---|---|
""",
        encoding="utf-8",
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
    # Exact 3.0 retains its byte/hash browser semantics; it does not retroactively
    # require an image codec signature introduced by route-faithful 4.0 evidence.
    assert validator.validate_acceptance_record(root, base_status()) == []

    duplicate = lc / "REAL-USER-JOURNEY-ACCEPTANCE.md"
    duplicate.write_text(duplicate.read_text(encoding="utf-8") + "\n- Owner result: PENDING\n", encoding="utf-8")
    assert any("duplicate Markdown field" in error for error in errors_for(root))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc = write_project(root)
    status = base_status()
    status["real_user_journey_acceptance"]["unknown"] = True
    assert any("unknown fields" in error for error in errors_for(root, status))

    status = base_status()
    status["real_user_journey_acceptance"]["candidate_hash"] = "2" * 64
    assert any("candidate identity" in error for error in errors_for(root, status))

    text = (lc / "REAL-USER-JOURNEY-ACCEPTANCE.md").read_text(encoding="utf-8")
    (lc / "REAL-USER-JOURNEY-ACCEPTANCE.md").write_text(text.replace("STEP-001", "bad step"), encoding="utf-8")
    assert any("Step ID" in error for error in errors_for(root))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc = write_project(root)
    record = lc / "REAL-USER-JOURNEY-ACCEPTANCE.md"
    text = record.read_text(encoding="utf-8")
    text = text.replace(
        ".lccoding/evidence/real-user-journey/round-001/JOURNEY-001/STEP-001.png",
        "../outside.png",
    )
    record.write_text(text, encoding="utf-8")
    assert any("screenshot path" in error for error in errors_for(root))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc = write_project(root)
    record = lc / "REAL-USER-JOURNEY-ACCEPTANCE.md"
    record.write_text(record.read_text(encoding="utf-8").replace(hashlib.sha256(b"visible-result").hexdigest(), "3" * 64), encoding="utf-8")
    assert any("screenshot digest" in error for error in errors_for(root))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc = write_project(root, round_number=2, start="NO")
    assert any("restart from home" in error for error in errors_for(root))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    lc = write_project(root)
    status = base_status()
    status["real_user_journey_acceptance"]["failed_journey_count"] = 1
    assert any("accepted journey state" in error for error in errors_for(root, status))

    phase = base_phase_status()
    phase["current_phase"] = "DELIVERY_PREPARATION"
    status = base_status()
    status["current_phase"] = "DELIVERY_PREPARATION"
    status["phase_gates"]["REAL_USER_JOURNEY_ACCEPTED"] = "PENDING"
    assert any("Delivery Preparation requires" in error for error in errors_for(root, status, phase))

print("PASS: real-user journey evidence fails closed on identity, screenshots, rounds, defects, and Phase 5")
