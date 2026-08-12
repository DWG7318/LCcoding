from pathlib import Path
import copy
import re


root = Path(__file__).resolve().parents[2]
start_path = root / "lc-coding/templates/RUN-HANDOFF.md"
receipt_path = root / "lc-coding/templates/LOOP-OWNER-ACCEPTANCE.md"

PHASES = {
    "INITIAL",
    "PRODUCT_FORMATION",
    "ENGINEERING_RUNS",
    "DELIVERY_PREPARATION",
}
START_ROLE = "RUN_START_CONTRACT"
RECEIPT_ROLE = "LOOP_OWNER_ACCEPTANCE_RECEIPT"
START_REQUIRED = {
    "Artifact role",
    "Start Contract ID",
    "Start Contract SHA-256",
    "Run ID",
    "LCCoding phase scope",
    "Phase-owned objective",
    "Calling phase authority / contract reference(s)",
    "Frozen Run scope",
    "Explicit exclusions",
    "Selected execution method ID",
    "Selected execution method version",
    "Selected execution method exact hash",
    "Selected execution method canonical interface / contract reference",
    "Phase-appropriate input evidence / prerequisites",
    "Evidence return target in calling phase",
    "D0-D3 evidence / verification condition",
    "Loop Owner Acceptance condition / route",
    "Risk / depth decision",
    "Readiness result",
    "Blocker evidence",
}
PHASE3_INPUTS = {
    "Product Baseline trace (ENGINEERING_RUNS only)",
    "Feature Slice ID / version (ENGINEERING_RUNS only)",
    "Applicable UI / Integration Baseline (ENGINEERING_RUNS only)",
}
START_FORBIDDEN = {
    "D3 Receipt",
    "D3 receipt",
    "Candidate ID / hash",
    "Final candidate verdict / result",
    "Owner result",
    "Accepted at",
    "Acceptance timestamp",
    "Gap status",
    "Gap closure result / status",
    "Delta re-verification receipt",
    "Delta Owner re-acceptance receipt",
    "Terminal acceptance status",
    "Status",
}
RECEIPT_REQUIRED = {
    "Artifact role",
    "Acceptance ID",
    "Run ID",
    "Run-start contract ID",
    "Run-start contract SHA-256",
    "LCCoding phase scope",
    "Phase-owned objective",
    "Candidate ID / hash",
    "D3 Receipt",
    "Entry / role / account",
    "Scenario IDs",
    "Acceptance steps",
    "Product questions",
    "Prior accepted dependencies reused",
    "Invisible risks already verified",
    "Known limits",
    "Evidence return target in the calling phase",
    "Calling phase gate remains independently evaluated",
    "Owner result",
    "Owner Gap ID (blank when accepted)",
    "Gap source Acceptance ID",
    "Gap source candidate / scenario",
    "Gap route",
    "Impact / definition reference",
    "Correction Run IDs",
    "Affected D0-D3 receipts",
    "Delta re-verification receipt",
    "Delta Owner re-acceptance receipt",
    "Gap status",
    "Product learning / route (may be blank; only consequential learning that changes a future decision, constraint, check, template, or reuse rule; update one existing canonical artifact)",
    "Accepted at",
}
RECEIPT_FORBIDDEN = {
    "Calling phase authority / contract reference(s)",
    "Frozen Run scope",
    "Explicit exclusions",
    "Selected execution method ID",
    "Selected execution method version",
    "Selected execution method exact hash",
    "Selected execution method canonical interface / contract reference",
    "Phase-appropriate input evidence / prerequisites",
    "Readiness result",
    "Blocker evidence",
    "Phase advancement",
    "Current phase",
}
ADDITIONAL_RECEIPT_START_AUTHORITY = {
    "Product Baseline trace (ENGINEERING_RUNS only)",
    "Feature Slice ID / version (ENGINEERING_RUNS only)",
    "Applicable UI / Integration Baseline (ENGINEERING_RUNS only)",
    "D0-D3 evidence / verification condition",
    "Loop Owner Acceptance condition / route",
    "Risk / depth decision",
}


def parse_fields(text):
    fields = {}
    for line in text.splitlines():
        if line.startswith("- ") and ":" in line:
            key, value = line[2:].split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


def present(value):
    return str(value or "").strip().upper() not in {
        "",
        "PENDING",
        "UNKNOWN",
        "NONE",
        "NOT_APPLICABLE",
    }


def validate_start(fields):
    errors = []
    missing = START_REQUIRED - set(fields)
    if missing:
        errors.append("missing start fields: " + ", ".join(sorted(missing)))
    forbidden = START_FORBIDDEN.intersection(fields)
    if forbidden:
        errors.append("terminal fields at start: " + ", ".join(sorted(forbidden)))
    if fields.get("Artifact role") != START_ROLE:
        errors.append("invalid start artifact role")
    for field in START_REQUIRED - {"Artifact role", "Blocker evidence"}:
        if field in fields and not present(fields[field]):
            errors.append("empty start field: " + field)
    if fields.get("LCCoding phase scope") not in PHASES:
        errors.append("invalid calling phase")
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", fields.get("Selected execution method version", "")):
        errors.append("invalid method version")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", fields.get("Selected execution method exact hash", "")):
        errors.append("invalid method hash")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", fields.get("Start Contract SHA-256", "")):
        errors.append("invalid start contract hash")
    readiness = fields.get("Readiness result")
    if readiness not in {"READY", "BLOCKED"}:
        errors.append("readiness must be READY or BLOCKED")
    if readiness == "READY" and fields.get("Blocker evidence") != "NONE":
        errors.append("READY requires Blocker evidence NONE")
    if readiness == "BLOCKED" and not present(fields.get("Blocker evidence")):
        errors.append("BLOCKED requires blocker evidence")
    phase3_present = PHASE3_INPUTS.intersection(fields)
    if fields.get("LCCoding phase scope") == "ENGINEERING_RUNS":
        if phase3_present != PHASE3_INPUTS or any(
            not present(fields.get(field)) for field in PHASE3_INPUTS
        ):
            errors.append("ENGINEERING_RUNS requires product integration inputs")
    elif phase3_present:
        errors.append("non-Phase-3 Run fabricates product integration inputs")
    return errors


def validate_receipt(fields, start):
    errors = []
    missing = RECEIPT_REQUIRED - set(fields)
    if missing:
        errors.append("missing receipt fields: " + ", ".join(sorted(missing)))
    duplicates = RECEIPT_FORBIDDEN.union(
        ADDITIONAL_RECEIPT_START_AUTHORITY
    ).intersection(fields)
    if duplicates:
        errors.append("receipt redefines start authority: " + ", ".join(sorted(duplicates)))
    if fields.get("Artifact role") != RECEIPT_ROLE:
        errors.append("invalid receipt artifact role")
    for field in RECEIPT_REQUIRED - {
        "Artifact role",
        "Owner Gap ID (blank when accepted)",
        "Gap source Acceptance ID",
        "Gap source candidate / scenario",
        "Gap route",
        "Impact / definition reference",
        "Correction Run IDs",
        "Affected D0-D3 receipts",
        "Delta re-verification receipt",
        "Delta Owner re-acceptance receipt",
        "Gap status",
        "Product learning / route (may be blank; only consequential learning that changes a future decision, constraint, check, template, or reuse rule; update one existing canonical artifact)",
        "Product questions",
        "Prior accepted dependencies reused",
        "Known limits",
    }:
        if field in fields and not present(fields[field]):
            errors.append("empty receipt field: " + field)
    exact_bindings = {
        "Run ID": "Run ID",
        "Run-start contract ID": "Start Contract ID",
        "Run-start contract SHA-256": "Start Contract SHA-256",
        "LCCoding phase scope": "LCCoding phase scope",
        "Phase-owned objective": "Phase-owned objective",
        "Evidence return target in the calling phase": "Evidence return target in calling phase",
    }
    for receipt_field, start_field in exact_bindings.items():
        if fields.get(receipt_field) != start.get(start_field):
            errors.append("receipt/start mismatch: " + receipt_field)
    if fields.get("Calling phase gate remains independently evaluated") != "YES":
        errors.append("Run acceptance cannot pass the calling phase gate")
    if fields.get("Owner result") not in {
        "LOOP_OWNER_ACCEPTED",
        "LOOP_PRODUCT_REWORK",
        "LOOP_PRODUCT_DEFINITION_CHANGE",
        "LOOP_OWNER_DEFERRED",
    }:
        errors.append("invalid Owner result")
    return errors


def valid_start(phase):
    fields = {
        "Artifact role": START_ROLE,
        "Start Contract ID": "SC-001",
        "Start Contract SHA-256": "sha256:" + "1" * 64,
        "Run ID": "RUN-001",
        "LCCoding phase scope": phase,
        "Phase-owned objective": "return bounded evidence to the calling phase",
        "Calling phase authority / contract reference(s)": f"LC-PHASE / {phase}",
        "Frozen Run scope": "one bounded work item",
        "Explicit exclusions": "no phase advancement",
        "Selected execution method ID": "SLK",
        "Selected execution method version": "2.6.0",
        "Selected execution method exact hash": "sha256:" + "2" * 64,
        "Selected execution method canonical interface / contract reference": "CANONICAL-MANIFEST / SLK",
        "Phase-appropriate input evidence / prerequisites": f"{phase}-INPUT-1",
        "Evidence return target in calling phase": f"{phase}-RETURN-1",
        "D0-D3 evidence / verification condition": "D0 through D3 must pass",
        "Loop Owner Acceptance condition / route": "D3 PASS then normal Loop Owner Acceptance",
        "Risk / depth decision": "bounded / proportional",
        "Readiness result": "READY",
        "Blocker evidence": "NONE",
    }
    if phase == "ENGINEERING_RUNS":
        fields.update(
            {
                "Product Baseline trace (ENGINEERING_RUNS only)": "PB-1",
                "Feature Slice ID / version (ENGINEERING_RUNS only)": "FS-1 / 1.0.0",
                "Applicable UI / Integration Baseline (ENGINEERING_RUNS only)": "UI-1 / IB-1",
            }
        )
    return fields


def valid_receipt(start):
    return {
        "Artifact role": RECEIPT_ROLE,
        "Acceptance ID": "OA-001",
        "Run ID": start["Run ID"],
        "Run-start contract ID": start["Start Contract ID"],
        "Run-start contract SHA-256": start["Start Contract SHA-256"],
        "LCCoding phase scope": start["LCCoding phase scope"],
        "Phase-owned objective": start["Phase-owned objective"],
        "Candidate ID / hash": "CANDIDATE-1 / sha256:" + "3" * 64,
        "D3 Receipt": "D3-001",
        "Entry / role / account": "Owner / Owner / owner-account",
        "Scenario IDs": "SCENARIO-1",
        "Acceptance steps": "STEP-1",
        "Product questions": "NONE",
        "Prior accepted dependencies reused": "NONE",
        "Invisible risks already verified": "D3-001",
        "Known limits": "NONE",
        "Evidence return target in the calling phase": start[
            "Evidence return target in calling phase"
        ],
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
        "Accepted at": "2026-08-12T00:00:00Z",
    }


start_template = parse_fields(start_path.read_text(encoding="utf-8"))
receipt_template = parse_fields(receipt_path.read_text(encoding="utf-8"))
assert start_template.get("Artifact role") == START_ROLE
assert START_REQUIRED.union(PHASE3_INPUTS).issubset(start_template)
assert not START_FORBIDDEN.intersection(start_template)
assert receipt_template.get("Artifact role") == RECEIPT_ROLE
assert RECEIPT_REQUIRED.issubset(receipt_template)
assert not RECEIPT_FORBIDDEN.union(ADDITIONAL_RECEIPT_START_AUTHORITY).intersection(
    receipt_template
)

for phase in PHASES:
    start = valid_start(phase)
    assert validate_start(start) == [], (phase, validate_start(start))
    receipt = valid_receipt(start)
    assert validate_receipt(receipt, start) == [], (phase, validate_receipt(receipt, start))

base_start = valid_start("ENGINEERING_RUNS")
for forbidden in START_FORBIDDEN:
    mutation = copy.deepcopy(base_start)
    mutation[forbidden] = "terminal value"
    assert validate_start(mutation), forbidden

for required in START_REQUIRED.union(PHASE3_INPUTS):
    mutation = copy.deepcopy(base_start)
    mutation.pop(required)
    assert validate_start(mutation), required

for invalid in ("", "PENDING", "PASS", "COMPLETE", "LOOP_OWNER_ACCEPTANCE_READY"):
    mutation = copy.deepcopy(base_start)
    mutation["Readiness result"] = invalid
    assert validate_start(mutation), invalid

for invalid_blocker in (
    "",
    "PENDING",
    "UNKNOWN",
    "NOT_APPLICABLE",
    "real unresolved blocker",
):
    mutation = copy.deepcopy(base_start)
    mutation["Blocker evidence"] = invalid_blocker
    assert validate_start(mutation), ("READY", invalid_blocker)

blocked_start = copy.deepcopy(base_start)
blocked_start["Readiness result"] = "BLOCKED"
blocked_start["Blocker evidence"] = "BLOCKER-1: unresolved prerequisite"
assert validate_start(blocked_start) == []
for invalid_blocker in ("", "NONE", "PENDING", "UNKNOWN", "NOT_APPLICABLE"):
    mutation = copy.deepcopy(blocked_start)
    mutation["Blocker evidence"] = invalid_blocker
    assert validate_start(mutation), ("BLOCKED", invalid_blocker)

base_receipt = valid_receipt(base_start)
for required in ("Run-start contract ID", "Run-start contract SHA-256"):
    mutation = copy.deepcopy(base_receipt)
    mutation.pop(required)
    assert validate_receipt(mutation, base_start), required
    mutation = copy.deepcopy(base_receipt)
    mutation[required] = "mismatch"
    assert validate_receipt(mutation, base_start), required

for duplicate in RECEIPT_FORBIDDEN:
    mutation = copy.deepcopy(base_receipt)
    mutation[duplicate] = "duplicate start authority"
    assert validate_receipt(mutation, base_start), duplicate

for duplicate in ADDITIONAL_RECEIPT_START_AUTHORITY:
    mutation = copy.deepcopy(base_receipt)
    mutation[duplicate] = "duplicate start authority"
    assert validate_receipt(mutation, base_start), duplicate

gate_claim = copy.deepcopy(base_receipt)
gate_claim["Calling phase gate remains independently evaluated"] = "NO"
assert validate_receipt(gate_claim, base_start)

print("PASS: Run start contract and Owner terminal receipt remain disjoint and bound")
