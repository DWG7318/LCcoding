from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile


root = Path(__file__).resolve().parents[2]
start_path = root / "lc-coding/templates/RUN-HANDOFF.md"
receipt_path = root / "lc-coding/templates/LOOP-OWNER-ACCEPTANCE.md"
validator_path = root / "lc-coding/scripts/validate_project.py"
validator_spec = importlib.util.spec_from_file_location(
    "lccoding_validate_project_run_contract", validator_path
)
validator_module = importlib.util.module_from_spec(validator_spec)
validator_spec.loader.exec_module(validator_module)

SCHEMA_PHASES = {
    "2.6.0": (
        "INITIAL",
        "PRODUCT_FORMATION",
        "ENGINEERING_RUNS",
        "DELIVERY_PREPARATION",
    ),
    "2.7.0": (
        "INITIAL",
        "PRODUCT_FORMATION",
        "ENGINEERING_RUNS",
        "DELIVERY_PREPARATION",
    ),
    "2.8.0": (
        "INITIAL",
        "PRODUCT_FORMATION",
        "REAL_PRODUCT_INTEGRATION",
        "DELIVERY_PREPARATION",
    ),
}
START_ROLE = "RUN_START_CONTRACT"
RECEIPT_ROLE = "LOOP_OWNER_ACCEPTANCE_RECEIPT"
START_REQUIRED = {
    "Artifact role",
    "Start Contract ID",
    "Start Contract SHA-256",
    "Run ID",
    "Status schema version",
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
    "Meaning impact classification",
    "Definition basis / neutral Impact Analysis reference",
    "Applicable Snake / Scorpion disposition evidence reference",
    "Evidence return target in calling phase",
    "D0-D3 evidence / verification condition",
    "Loop Owner Acceptance condition / route",
    "Risk / depth decision",
    "Readiness result",
    "Blocker evidence",
}
LEGACY_PHASE3_INPUTS = {
    "Product Baseline trace (ENGINEERING_RUNS only)",
    "Feature Slice ID / version (ENGINEERING_RUNS only)",
    "Applicable UI / Integration Baseline (ENGINEERING_RUNS only)",
}
CURRENT_PHASE3_INPUTS = {
    "Product Baseline trace (REAL_PRODUCT_INTEGRATION only)",
    "Feature Slice ID / version (REAL_PRODUCT_INTEGRATION only)",
    "Applicable UI / Integration Baseline (REAL_PRODUCT_INTEGRATION only)",
}
ALL_PHASE3_INPUTS = LEGACY_PHASE3_INPUTS | CURRENT_PHASE3_INPUTS
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
    "Status schema version",
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
    "Meaning impact classification",
    "Definition basis / neutral Impact Analysis reference",
    "Applicable Snake / Scorpion disposition evidence reference",
}
ADDITIONAL_RECEIPT_START_AUTHORITY = {
    *ALL_PHASE3_INPUTS,
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
    schema = fields.get("Status schema version")
    phases = SCHEMA_PHASES.get(schema)
    if phases is None:
        errors.append("invalid status schema version")
        phases = ()
    if fields.get("LCCoding phase scope") not in phases:
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
    phase3_id = phases[2] if phases else None
    expected_phase3 = (
        CURRENT_PHASE3_INPUTS if schema == "2.8.0" else LEGACY_PHASE3_INPUTS
    )
    phase3_present = ALL_PHASE3_INPUTS.intersection(fields)
    if fields.get("LCCoding phase scope") == phase3_id:
        if phase3_present != expected_phase3 or any(
            not present(fields.get(field)) for field in expected_phase3
        ):
            errors.append("schema-selected Phase 3 requires product integration inputs")
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
        "Status schema version": "Status schema version",
        "LCCoding phase scope": "LCCoding phase scope",
        "Phase-owned objective": "Phase-owned objective",
        "Evidence return target in the calling phase": "Evidence return target in calling phase",
    }
    for receipt_field, start_field in exact_bindings.items():
        if fields.get(receipt_field) != start.get(start_field):
            errors.append("receipt/start mismatch: " + receipt_field)
    schema = fields.get("Status schema version")
    phases = SCHEMA_PHASES.get(schema, ())
    if not phases:
        errors.append("invalid receipt status schema version")
    if fields.get("LCCoding phase scope") not in phases:
        errors.append("receipt phase does not match status schema")
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


def valid_start(phase, schema="2.8.0"):
    fields = {
        "Artifact role": START_ROLE,
        "Start Contract ID": "SC-001",
        "Start Contract SHA-256": "sha256:" + "1" * 64,
        "Run ID": "RUN-001",
        "Status schema version": schema,
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
        "Meaning impact classification": "MEANING_NEUTRAL",
        "Definition basis / neutral Impact Analysis reference": "IMPACT-ANALYSIS.md",
        "Applicable Snake / Scorpion disposition evidence reference": "CALABASH-UPGRADE-GATE.md",
        "Evidence return target in calling phase": f"{phase}-RETURN-1",
        "D0-D3 evidence / verification condition": "D0 through D3 must pass",
        "Loop Owner Acceptance condition / route": "D3 PASS then normal Loop Owner Acceptance",
        "Risk / depth decision": "bounded / proportional",
        "Readiness result": "READY",
        "Blocker evidence": "NONE",
    }
    phase3_id = SCHEMA_PHASES[schema][2]
    if phase == phase3_id:
        suffix = "REAL_PRODUCT_INTEGRATION" if schema == "2.8.0" else "ENGINEERING_RUNS"
        fields.update(
            {
                f"Product Baseline trace ({suffix} only)": "PB-1",
                f"Feature Slice ID / version ({suffix} only)": "FS-1 / 1.0.0",
                f"Applicable UI / Integration Baseline ({suffix} only)": "UI-1 / IB-1",
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
        "Status schema version": start["Status schema version"],
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
assert start_template.get("Status schema version") == "2.8.0"
assert "REAL_PRODUCT_INTEGRATION" in start_template.get("LCCoding phase scope", "")
assert "ENGINEERING_RUNS" not in start_template.get("LCCoding phase scope", "")
assert START_REQUIRED.union(CURRENT_PHASE3_INPUTS).issubset(start_template)
assert not START_FORBIDDEN.intersection(start_template)
assert receipt_template.get("Artifact role") == RECEIPT_ROLE
assert receipt_template.get("Status schema version") == "2.8.0"
assert "REAL_PRODUCT_INTEGRATION" in receipt_template.get("LCCoding phase scope", "")
assert "ENGINEERING_RUNS" not in receipt_template.get("LCCoding phase scope", "")
assert RECEIPT_REQUIRED.issubset(receipt_template)
assert not RECEIPT_FORBIDDEN.union(ADDITIONAL_RECEIPT_START_AUTHORITY).intersection(
    receipt_template
)

for schema, phases in SCHEMA_PHASES.items():
    for phase in phases:
        start = valid_start(phase, schema)
        assert validate_start(start) == [], (schema, phase, validate_start(start))
        receipt = valid_receipt(start)
        assert validate_receipt(receipt, start) == [], (
            schema,
            phase,
            validate_receipt(receipt, start),
        )

cross_280 = valid_start("REAL_PRODUCT_INTEGRATION", "2.8.0")
cross_280["LCCoding phase scope"] = "ENGINEERING_RUNS"
assert validate_start(cross_280)
cross_270 = valid_start("ENGINEERING_RUNS", "2.7.0")
cross_270["LCCoding phase scope"] = "REAL_PRODUCT_INTEGRATION"
assert validate_start(cross_270)

missing_schema = valid_start("REAL_PRODUCT_INTEGRATION", "2.8.0")
missing_schema.pop("Status schema version")
assert validate_start(missing_schema)

base_start = valid_start("REAL_PRODUCT_INTEGRATION", "2.8.0")
for forbidden in START_FORBIDDEN:
    mutation = copy.deepcopy(base_start)
    mutation[forbidden] = "terminal value"
    assert validate_start(mutation), forbidden

for required in START_REQUIRED.union(CURRENT_PHASE3_INPUTS):
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
cross_receipt = copy.deepcopy(base_receipt)
cross_receipt["Status schema version"] = "2.7.0"
cross_receipt["LCCoding phase scope"] = "REAL_PRODUCT_INTEGRATION"
assert validate_receipt(cross_receipt, base_start)
for required in (
    "Run-start contract ID",
    "Run-start contract SHA-256",
    "Status schema version",
):
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


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def git(repo, *arguments, text=True):
    return subprocess.run(
        ["git", *arguments], cwd=repo, capture_output=True, text=text, check=True
    ).stdout


def subtree_hash(repo, commit, subtree):
    listing = git(
        repo,
        "ls-tree",
        "-r",
        "-z",
        "--full-tree",
        commit,
        "--",
        f":(literal){subtree}",
        text=False,
    )
    entries = []
    for record in listing.split(b"\0"):
        if not record:
            continue
        metadata, path = record.split(b"\t", 1)
        mode, kind, object_id = metadata.split(b" ")
        assert kind == b"blob"
        blob = git(repo, "cat-file", "blob", object_id.decode("ascii"), text=False)
        entries.append((path, mode, hashlib.sha256(blob).hexdigest().encode("ascii")))
    manifest = b"".join(
        path + b"\0" + mode + b"\0" + digest + b"\n"
        for path, mode, digest in sorted(entries)
    )
    return "sha256:" + hashlib.sha256(manifest).hexdigest()


METHOD = {
    "method_id": "METHOD-ONE",
    "version": "1.2.3",
    "exact_hash": "sha256:" + "4" * 64,
    "canonical_contract_reference": "methods/METHOD-ONE.md#run-contract",
    "run_evidence_mapping": "RUN_START_CONTRACT -> D0-D3",
    "owner_acceptance_mapping": "LOOP_OWNER_ACCEPTANCE_RECEIPT",
    "required_control_binding": "LCCODING_LOOP_CONTROL",
    "compatibility_result": "PASS",
}


def manifest_record(methods=None):
    return {
        "lccoding": {"version": "2.6.0", "hash": ""},
        "calabash": {"version": "", "hash": ""},
        "slk": {"version": "", "hash": ""},
        "clk": {"version": "", "hash": ""},
        "glk": {"version": "", "hash": ""},
        "execution_methods": copy.deepcopy([METHOD] if methods is None else methods),
        "compatibility": "PASS",
        "load_order": [
            "LCCoding",
            "Project Agent Rule",
            "Calabash",
            "Per-Run Execution Method",
            "Project Artifacts",
            "Repository",
        ],
    }


def write_manifest_and_lock(project, manifest, *, lock_hash=None, validated=None):
    lc = project / ".lccoding"
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode()
    (lc / "CANONICAL-MANIFEST.json").write_bytes(manifest_bytes)
    exact_hash = "sha256:" + hashlib.sha256(manifest_bytes).hexdigest()
    lock = {
        "project_id": "run-contract-fixture",
        "issued_at": "2026-08-12T00:00:00Z",
        "agent_platform": "fixture",
        "manifest_reference": "CANONICAL-MANIFEST.json",
        "manifest_hash": exact_hash if lock_hash is None else lock_hash,
        "validated_execution_method_ids": (
            [METHOD["method_id"]] if validated is None else validated
        ),
        "knowledge_test": "PASS",
        "execution_test": "PASS",
        "compatibility": "PASS",
        "status": "VALID",
        "invalidated_by": [],
    }
    write(lc / "INTERPRETATION-LOCK.json", json.dumps(lock, indent=2) + "\n")


def canonical_start_text(fields):
    lines = ["# Run Start Contract", ""]
    for key, value in fields.items():
        lines.append(f"- {key}: {value}" if value else f"- {key}:")
    return "\n".join(lines) + "\n"


def freeze_start(fields):
    fields = copy.deepcopy(fields)
    fields["Start Contract SHA-256"] = ""
    empty = canonical_start_text(fields)
    fields["Start Contract SHA-256"] = "sha256:" + hashlib.sha256(
        empty.encode("utf-8")
    ).hexdigest()
    return canonical_start_text(fields), fields


def terminal_receipt(start_fields, *, acceptance_id, candidate, **changes):
    fields = valid_receipt(start_fields)
    fields["Acceptance ID"] = acceptance_id
    fields["Candidate ID / hash"] = candidate
    fields.update(changes)
    return "# Loop Owner Acceptance Receipt\n\n" + "\n".join(
        f"- {key}: {value}" for key, value in fields.items()
    ) + "\n"


def definition_evidence(project):
    lc = project / ".lccoding"
    write(
        lc / "CALABASH-UPGRADE-GATE.md",
        f"""# Calabash Definition Handoff

- Artifact role: CALABASH_DEFINITION_HANDOFF
- Definition Handoff ID: CDH-RUN
- Definition Baseline kind: CALABASH_DEFINITION_BASELINE
- Definition Baseline ID: DB-RUN
- Definition Baseline semantic version: 1.0.0
- Definition Baseline exact hash: sha256:{'7' * 64}
- Calabash standard version: 2.5.0
- Baseline status: FROZEN
- Applicable Definition clause references: baseline:/grandpa/product, baseline:/product_architecture/journey, baseline:/ontology/order
- Snake review status: NONE_IDENTIFIED
- Snake review scope: Grandpa, Product Architecture, Ontology
- Snake review evidence refs: E-SNAKE-REVIEW
- Scorpion review status: NONE_IDENTIFIED
- Scorpion review scope: Grandpa, Product Architecture, Ontology
- Scorpion review evidence refs: E-SCORPION-REVIEW
- Meaning-change / invalidation rules reference: CAL-CHANGE-1
- Upgrade Receipt ID: UPGRADE-RUN
- Upgrade Receipt exact hash: sha256:{'8' * 64}
- Upgrade verdict: CALABASH_UPGRADE_PASS
- Owner change authority: OWNER
- Handoff result: PASS

## Snake records

| Snake ID | Disposition | Guard / verification reference | Evidence refs | Affected Definition clause refs |
|---|---|---|---|---|

## Scorpion records

| Scorpion ID | Status | Blocking semantics | Hit condition reference | Evidence refs | Affected Definition clause refs |
|---|---|---|---|---|---|
""",
    )
    write(
        lc / "IMPACT-ANALYSIS.md",
        """# Impact Analysis

- Artifact role: IMPACT_ANALYSIS
- Analysis ID / version: IA-RUN / 1.0.0
- Trigger / proposed change: bounded implementation
- Meaning impact classification: MEANING_NEUTRAL
- Calling phase contract / authority: LC-PHASE
- Neutral rationale / evidence: E-NEUTRAL-RUN
- Definition Baseline ID / exact hash: NONE
- Affected Definition clause references: NONE
- Definition invalidation effect: NO_DEFINITION_INVALIDATION
- Governed Calabash update route / Owner authority: NOT_APPLICABLE
- Snake / Scorpion applicability and effect references: NONE_IDENTIFIED: E-REVIEW
- Impact result: PASS
""",
    )


def maps_and_handoff(project, commit):
    lc = project / ".lccoding"
    hashes = {
        "UI": subtree_hash(project, commit, "product/ui"),
        "WORKFLOW": subtree_hash(project, commit, "product/workflow"),
        "SIMULATION": subtree_hash(project, commit, "product/simulation"),
    }
    write(
        lc / "WORKFLOW-MAP.md",
        f"""# Workflow Map

- Primary product mainline ID: MAINLINE-1

| Workflow ID | Classification (CORE/EXTRA) | Implementation status | Subtree path | Component version | Content hash | Actors | Trigger | States / rules | Data / permissions | Failure / recovery | API contract / evidence | MCP contract / evidence | UI subtree references | Simulation subtree references | Evidence / attestation | Calabash trace | Primary mainline |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| WF-1 | CORE | IMPLEMENTED | product/workflow | 1.0.0 | {hashes['WORKFLOW']} | Owner | Invoke | Defined | Defined | Defined | API-1 | MCP-1 | UI-1 | SIM-1 | D2-WF | CAL-1 | YES |
""",
    )
    write(
        lc / "UI-MAP.md",
        f"""# UI Map

- Primary product mainline ID: MAINLINE-1

| UI ID | Subtree path | Component version | Content hash | Actor | Surface / state | Actions / feedback | Workflow subtree references | Simulation subtree references | Evidence / attestation | Lock status | Primary mainline |
|---|---|---|---|---|---|---|---|---|---|---|---|
| UI-1 | product/ui | 1.0.0 | {hashes['UI']} | Owner | Main | Invoke | WF-1 | SIM-1 | D2-UI | LOCKED | YES |
""",
    )
    write(
        lc / "SIMULATION-WORLD.md",
        f"""# Simulation World

- Primary product mainline ID: MAINLINE-1

## Simulation subtree registry

| Simulation ID | Subtree path | Component version | Content hash | Foundation status | Workflow subtree references | UI subtree references | Primary mainline |
|---|---|---|---|---|---|---|---|
| SIM-1 | product/simulation | 1.0.0 | {hashes['SIMULATION']} | RUNNABLE | WF-1 | UI-1 | YES |
""",
    )
    write(
        lc / "PRODUCT-BASELINE-HANDOFF.md",
        f"""# Product Baseline Handoff

- Baseline ID / version / hash: PB-1 / 1.0.0 / E-PB
- Project repository identity: github.com/example/run-contract
- Project frozen exact commit SHA: {commit}
- Calabash Definition Handoff ID / exact hash: CDH-RUN / sha256:{hashlib.sha256((lc / 'CALABASH-UPGRADE-GATE.md').read_bytes()).hexdigest()}
- Calabash Definition Handoff result: PASS
- Primary product mainline ID: MAINLINE-1
- Primary mainline Owner confirmation: OWNER_CONFIRMED: OA-PB
- Handoff status: COMPLETE

| Subtree type | Subtree ID | Path | Component version | Content hash | Classification | API evidence | MCP evidence | Primary mainline | Related subtree IDs |
|---|---|---|---|---|---|---|---|---|---|
| UI | UI-1 | product/ui | 1.0.0 | {hashes['UI']} | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | YES | WF-1, SIM-1 |
| WORKFLOW | WF-1 | product/workflow | 1.0.0 | {hashes['WORKFLOW']} | CORE | API-1 | MCP-1 | YES | UI-1, SIM-1 |
| SIMULATION | SIM-1 | product/simulation | 1.0.0 | {hashes['SIMULATION']} | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | YES | WF-1, UI-1 |
""",
    )
    return hashes


def slice_text(commit, ui_hash, *, required="R1, R2", optional="", superseded="", invalidated=""):
    return f"""# Feature Slice

- Slice ID / version: FS-1 / 1.0.0
- Actor intent: invoke product
- Product outcome: visible result
- Product Baseline trace: PB-1
- Accepted integration candidate / baseline identity: CANDIDATE-1 / sha256:{'5' * 64}
- Workflow references: WF-1
- UI references: UI-1
- Primary product mainline ID / Owner confirmation: MAINLINE-1 / OWNER_CONFIRMED
- Project repository / exact baseline commit: github.com/example/run-contract :: {commit}
- Applicable UI subtree ID / path: UI-1 :: product/ui
- UI component version: 1.0.0
- UI content hash: {ui_hash}
- UI content hash scope / manifest evidence: HASH_SCOPE: frozen subtree
- UI Product / Integration Baseline identity: MATCH: IB-1
- UI subtree comparison before Slice / Run: MATCH: E-UI
- UI comparison before acceptance route: REQUIRED
- Scenario IDs / versions: SCN-1 / 1.0.0
- State / data / permission trace: E-STATE
- Exception / recovery trace: E-RECOVERY
- Impact Analysis ID: IA-1
- Integration Baseline ID: IB-1
- Required Run IDs: {required}
- Optional Run IDs: {optional}
- Superseded Run IDs: {superseded}
- Invalidated Run IDs: {invalidated}
- D0-D3 evidence plan: D0-D3
- Normal Loop Owner Acceptance route(s): OA
- Execution Coverage Preflight: PASS
- Coverage gaps / unknowns: NONE
- Cross-layer connection evidence: PROVEN: D3-E2E
- First Proving Run requirement: NOT_REQUIRED
- Failure expansion rule: HALT_EXPANSION
- Fingerprint depth response: CONCISE_TRUTHFUL
"""


def build_cli_project(project, *, aggregate=True, run_phases=None, schema="2.6.0"):
    project.mkdir()
    git(project, "init", "--quiet")
    git(project, "config", "user.email", "run-contract@example.invalid")
    git(project, "config", "user.name", "Run Contract Test")
    for relative in ("product/ui/index.html", "product/workflow/run.py", "product/simulation/world.json"):
        write(project / relative, relative + "\n")
    git(project, "add", "product")
    git(project, "commit", "--quiet", "-m", "freeze product")
    commit = git(project, "rev-parse", "HEAD").strip()
    lc = project / ".lccoding"
    for name in ("OWNER-POLICY.md", "PROJECT-PROFILE.md", "AGENT-RULE.md"):
        write(lc / name, "# fixture\n")
    write(project / "VERSION", "1.0.0\n")
    write(lc / "PROJECT-START.json", json.dumps({"initialization_mode": "NEW", "repository": "github.com/example/run-contract"}) + "\n")
    factors = {name: "LOW" for name in ("product_uncertainty", "system_coupling", "real_risk", "irreversibility", "novelty")}
    write(lc / "PROJECT-FINGERPRINT.json", json.dumps({"complexity": factors, "depth": {}}) + "\n")
    write(lc / "PROJECT-HEALTH.json", json.dumps({"record_role": "ASSESSMENT_EVIDENCE", "initialization_mode": "NEW"}) + "\n")
    definition_evidence(project)
    hashes = maps_and_handoff(project, commit)
    write_manifest_and_lock(project, manifest_record())

    status = json.loads((root / "lc-coding/templates/STATUS.json").read_text(encoding="utf-8"))
    status["status_schema_version"] = schema
    status["initialization_mode"] = "NEW"
    status["current_phase"] = "DELIVERY_PREPARATION" if aggregate else "INITIAL"
    status["phase_gates"]["INITIAL_READY"] = "PASS"
    status["phase_gates"]["CALABASH_UPGRADE_READY"] = "PASS"
    status["product_baseline"] = "ACCEPTED" if aggregate else "PENDING"
    status["active_slice"] = "FS-1" if aggregate else None
    if aggregate:
        status["phase_gates"]["ALL_REQUIRED_RUNS_ACCEPTED"] = "ALL_REQUIRED_RUNS_ACCEPTED"
        status["all_required_runs_accepted"] = "ALL_REQUIRED_RUNS_ACCEPTED"
    phases = json.loads((root / "lc-coding/templates/PHASE-STATUS.json").read_text(encoding="utf-8"))
    phases["status_schema_version"] = schema
    phase3_id = SCHEMA_PHASES[schema][2]
    if schema in {"2.6.0", "2.7.0"}:
        records = phases["phases"]
        phases["phases"] = {
            "INITIAL": records["INITIAL"],
            "PRODUCT_FORMATION": records["PRODUCT_FORMATION"],
            "ENGINEERING_RUNS": records["REAL_PRODUCT_INTEGRATION"],
            "DELIVERY_PREPARATION": records["DELIVERY_PREPARATION"],
        }
    phases["current_phase"] = status["current_phase"]
    phases["phases"]["INITIAL"] = {"status": "COMPLETE", "exit_gate": "PASS"}
    if aggregate:
        phases["phases"]["PRODUCT_FORMATION"] = {"status": "COMPLETE", "exit_evidence": "ACCEPTED"}
        phases["phases"][phase3_id] = {"status": "COMPLETE", "per_run_acceptances": ["OA-R1", "OA-R2"], "aggregate_exit_gate": "ALL_REQUIRED_RUNS_ACCEPTED"}
        phases["phases"]["DELIVERY_PREPARATION"] = {"status": "ACTIVE", "exit_gate": "PENDING"}
    write(lc / "status.json", json.dumps(status, indent=2) + "\n")
    write(lc / "PHASE-STATUS.json", json.dumps(phases, indent=2) + "\n")
    write(lc / "slices/FS-1.md", slice_text(commit, hashes["UI"]))

    phases_by_run = (
        {"R1": phase3_id, "R2": phase3_id}
        if run_phases is None
        else run_phases
    )
    for run_id, phase in phases_by_run.items():
        start = valid_start(phase, schema)
        start["Start Contract ID"] = "SC-" + run_id
        start["Run ID"] = run_id
        start["Selected execution method ID"] = METHOD["method_id"]
        start["Selected execution method version"] = METHOD["version"]
        start["Selected execution method exact hash"] = METHOD["exact_hash"]
        start["Selected execution method canonical interface / contract reference"] = METHOD["canonical_contract_reference"]
        start["Evidence return target in calling phase"] = "FS-1 / accepted integration evidence"
        if phase == phase3_id:
            suffix = "REAL_PRODUCT_INTEGRATION" if schema == "2.8.0" else "ENGINEERING_RUNS"
            start[f"Product Baseline trace ({suffix} only)"] = "PB-1"
            start[f"Feature Slice ID / version ({suffix} only)"] = "FS-1 / 1.0.0"
            start[f"Applicable UI / Integration Baseline ({suffix} only)"] = "UI-1 / IB-1"
        text, frozen = freeze_start(start)
        write(lc / "runs" / run_id / "RUN-HANDOFF.md", text)
        write(
            lc / "reviews" / f"OA-{run_id}.md",
            terminal_receipt(
                frozen,
                acceptance_id=f"OA-{run_id}",
                candidate="CANDIDATE-1 / sha256:" + "5" * 64,
            ),
        )
    status["loop_owner_acceptances"] = [f"OA-{run_id}" for run_id in phases_by_run]
    write(lc / "status.json", json.dumps(status, indent=2) + "\n")
    return commit


def validate_cli(project):
    return subprocess.run(
        [sys.executable, str(root / "lc-coding/scripts/validate_project.py"), str(project)],
        capture_output=True,
        text=True,
    )


def mutate_fields(path, changes):
    fields = parse_fields(path.read_text(encoding="utf-8"))
    fields.update(changes)
    title = "# Run Start Contract" if fields.get("Artifact role") == START_ROLE else "# Loop Owner Acceptance Receipt"
    write(path, title + "\n\n" + "\n".join(f"- {key}: {value}" for key, value in fields.items()) + "\n")


def rewrite_start_and_receipt(project, changes, run="R1"):
    start = project / ".lccoding/runs" / run / "RUN-HANDOFF.md"
    receipt = project / ".lccoding/reviews" / f"OA-{run}.md"
    fields = parse_fields(start.read_text(encoding="utf-8"))
    fields.update(changes)
    text, frozen = freeze_start(fields)
    write(start, text)
    mutate_fields(
        receipt,
        {
            "Run ID": frozen["Run ID"],
            "Run-start contract ID": frozen["Start Contract ID"],
            "Run-start contract SHA-256": frozen["Start Contract SHA-256"],
        },
    )
    return frozen


with tempfile.TemporaryDirectory(prefix="lccoding-run-contract-") as temporary:
    base = Path(temporary)
    seed = base / "seed"
    build_cli_project(seed)
    result = validate_cli(seed)
    assert result.returncode == 0, result.stdout + result.stderr

    current_280 = base / "current-280"
    build_cli_project(current_280, schema="2.8.0")
    current_before = {
        path.relative_to(current_280): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in current_280.rglob("*")
        if path.is_file()
    }
    result = validate_cli(current_280)
    assert result.returncode == 0, result.stdout + result.stderr
    for relative, (expected_bytes, expected_mtime) in current_before.items():
        path = current_280 / relative
        assert path.read_bytes() == expected_bytes
        assert path.stat().st_mtime_ns == expected_mtime

    stale_280 = base / "stale-phase-280"
    shutil.copytree(current_280, stale_280)
    rewrite_start_and_receipt(
        stale_280, {"LCCoding phase scope": "ENGINEERING_RUNS"}
    )
    mutate_fields(
        stale_280 / ".lccoding/reviews/OA-R1.md",
        {"LCCoding phase scope": "ENGINEERING_RUNS"},
    )
    assert validate_cli(stale_280).returncode != 0

    crossed_270 = base / "crossed-phase-270"
    build_cli_project(crossed_270, schema="2.7.0")
    result = validate_cli(crossed_270)
    assert result.returncode == 0, result.stdout + result.stderr
    rewrite_start_and_receipt(
        crossed_270, {"LCCoding phase scope": "REAL_PRODUCT_INTEGRATION"}
    )
    mutate_fields(
        crossed_270 / ".lccoding/reviews/OA-R1.md",
        {"LCCoding phase scope": "REAL_PRODUCT_INTEGRATION"},
    )
    assert validate_cli(crossed_270).returncode != 0

    def case(name):
        target = base / name
        shutil.copytree(seed, target)
        return target

    start_path_for = lambda project, run="R1": project / ".lccoding/runs" / run / "RUN-HANDOFF.md"
    receipt_path_for = lambda project, run="R1": project / ".lccoding/reviews" / f"OA-{run}.md"

    review_failures = []

    project = case("generic-aggregate-without-evidence")
    shutil.rmtree(project / ".lccoding/runs")
    shutil.rmtree(project / ".lccoding/reviews")
    if validate_cli(project).returncode == 0:
        review_failures.append("generic aggregate accepted without Run starts/receipts")

    project = base / "missing-indexed-receipt"
    build_cli_project(project, aggregate=False, run_phases={})
    status_path = project / ".lccoding/status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    status["loop_owner_acceptances"] = ["OA-MISSING"]
    write(status_path, json.dumps(status, indent=2) + "\n")
    if validate_cli(project).returncode == 0:
        review_failures.append("missing receipt from authoritative acceptance index was accepted")

    unfinished = base / "unfinished-cross-phase-run"
    build_cli_project(unfinished, aggregate=False, run_phases={"RX": "INITIAL"})
    (unfinished / ".lccoding/reviews/OA-RX.md").unlink()
    unfinished_status_path = unfinished / ".lccoding/status.json"
    unfinished_status = json.loads(unfinished_status_path.read_text(encoding="utf-8"))
    unfinished_status["loop_owner_acceptances"] = []
    write(unfinished_status_path, json.dumps(unfinished_status, indent=2) + "\n")
    result = validate_cli(unfinished)
    if result.returncode != 0:
        review_failures.append("unfinished cross-phase Run with zero receipts rejected: " + result.stdout.strip())

    two_receipts = base / "two-receipts-cross-phase"
    build_cli_project(two_receipts, aggregate=False, run_phases={"RX": "INITIAL"})
    first_receipt = two_receipts / ".lccoding/reviews/OA-RX.md"
    second_receipt = two_receipts / ".lccoding/reviews/OA-2.md"
    shutil.copyfile(first_receipt, second_receipt)
    mutate_fields(second_receipt, {"Acceptance ID": "OA-2"})
    status_path = two_receipts / ".lccoding/status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    status["loop_owner_acceptances"] = ["OA-RX", "OA-2"]
    write(status_path, json.dumps(status, indent=2) + "\n")
    result = validate_cli(two_receipts)
    if result.returncode == 0:
        review_failures.append("one cross-phase Run accepted two current formal receipts")

    duplicate_receipt = base / "duplicate-acceptance-id"
    build_cli_project(duplicate_receipt, aggregate=False, run_phases={"RX": "INITIAL"})
    shutil.copyfile(
        duplicate_receipt / ".lccoding/reviews/OA-RX.md",
        duplicate_receipt / ".lccoding/reviews/OA-DUPLICATE.md",
    )
    result = validate_cli(duplicate_receipt)
    if result.returncode == 0 or "duplicate Loop Owner Acceptance ID OA-RX" not in result.stdout:
        review_failures.append("duplicate formal receipt Acceptance ID did not fail closed")

    for name, malformed_index in (
        ("string", "OA-1"),
        ("object", {"id": "OA-1"}),
        ("null", None),
    ):
        project = base / ("malformed-index-" + name)
        build_cli_project(project, aggregate=False, run_phases={})
        status_path = project / ".lccoding/status.json"
        status = json.loads(status_path.read_text(encoding="utf-8"))
        status["loop_owner_acceptances"] = malformed_index
        write(status_path, json.dumps(status, indent=2) + "\n")
        result = validate_cli(project)
        output = result.stdout + result.stderr
        if result.returncode == 0 or "status acceptance index must be a list" not in output:
            review_failures.append("malformed authoritative acceptance index accepted: " + name)

    for name, malformed_item in (
        ("blank", ""),
        ("unsafe", "../OA-1"),
        ("non-string", {"id": "OA-1"}),
    ):
        project = base / ("malformed-index-item-" + name)
        build_cli_project(project, aggregate=False, run_phases={})
        status_path = project / ".lccoding/status.json"
        status = json.loads(status_path.read_text(encoding="utf-8"))
        status["loop_owner_acceptances"] = [malformed_item]
        write(status_path, json.dumps(status, indent=2) + "\n")
        result = validate_cli(project)
        output = result.stdout + result.stderr
        if result.returncode == 0 or "status acceptance index contains invalid Acceptance ID" not in output or "Traceback" in output:
            review_failures.append("invalid acceptance index item did not fail cleanly: " + name)

    unindexed_receipt = base / "unindexed-formal-receipt"
    build_cli_project(unindexed_receipt, aggregate=False, run_phases={"RX": "INITIAL"})
    status_path = unindexed_receipt / ".lccoding/status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    status["loop_owner_acceptances"] = []
    write(status_path, json.dumps(status, indent=2) + "\n")
    result = validate_cli(unindexed_receipt)
    if result.returncode == 0 or "terminal receipt is absent from status acceptance index" not in result.stdout:
        review_failures.append("unindexed formal receipt was accepted")

    bootstrap = base / "empty-generic-bootstrap"
    build_cli_project(bootstrap, aggregate=False, run_phases={})
    write_manifest_and_lock(bootstrap, manifest_record([]), validated=[])
    result = validate_cli(bootstrap)
    if result.returncode != 0:
        review_failures.append("empty no-Run bootstrap rejected: " + result.stdout.strip())

    legacy = base / "legacy-dual-read"
    build_cli_project(legacy, aggregate=False, run_phases={"R-INITIAL": "INITIAL"})
    legacy_manifest = manifest_record([])
    legacy_manifest.pop("execution_methods")
    legacy_manifest["slk"] = {
        "version": "2.6.0",
        "hash": "sha256:" + "6" * 64,
    }
    write_manifest_and_lock(legacy, legacy_manifest, validated=[])
    rewrite_start_and_receipt(
        legacy,
        {
            "Selected execution method ID": "SLK",
            "Selected execution method version": "2.6.0",
            "Selected execution method exact hash": "sha256:" + "6" * 64,
            "Selected execution method canonical interface / contract reference": "LEGACY_SLK_RUN_CONTRACT",
        },
        run="R-INITIAL",
    )
    result = validate_cli(legacy)
    if result.returncode != 0:
        review_failures.append("legacy 2.6 dual-read fixture rejected: " + result.stdout.strip())

    project = case("blocked-required-run")
    rewrite_start_and_receipt(
        project,
        {
            "Readiness result": "BLOCKED",
            "Blocker evidence": "B1: unresolved prerequisite",
        },
    )
    if validate_cli(project).returncode == 0:
        review_failures.append("BLOCKED Required Run counted as accepted")

    mandatory_semantic_fields = (
        "Start Contract ID",
        "Run ID",
        "Phase-owned objective",
        "Calling phase authority / contract reference(s)",
        "Frozen Run scope",
        "Explicit exclusions",
        "Phase-appropriate input evidence / prerequisites",
        "Evidence return target in calling phase",
        "D0-D3 evidence / verification condition",
        "Loop Owner Acceptance condition / route",
        "Risk / depth decision",
    )
    direct_project = base / "direct-start-validation"
    definition_evidence(direct_project)
    direct_root = direct_project / ".lccoding/runs"
    for index, field in enumerate(mandatory_semantic_fields):
        fields = valid_start("ENGINEERING_RUNS", "2.7.0")
        fields["Selected execution method ID"] = METHOD["method_id"]
        fields["Selected execution method version"] = METHOD["version"]
        fields["Selected execution method exact hash"] = METHOD["exact_hash"]
        fields[
            "Selected execution method canonical interface / contract reference"
        ] = METHOD["canonical_contract_reference"]
        fields[field] = ""
        text, frozen = freeze_start(fields)
        path = direct_root / str(index) / "RUN-HANDOFF.md"
        write(path, text)
        errors = validator_module.validate_run_start_record(
            path,
            frozen,
            {METHOD["method_id"]: METHOD},
            manifest_record(),
            {},
        )
        if not errors:
            review_failures.append("empty mandatory start fact accepted: " + field)

    for index, (field, value) in enumerate(
        (("Start Contract ID", "../SC-1"), ("Run ID", "RUN 1")),
        start=len(mandatory_semantic_fields),
    ):
        fields = valid_start("ENGINEERING_RUNS", "2.7.0")
        fields["Selected execution method ID"] = METHOD["method_id"]
        fields["Selected execution method version"] = METHOD["version"]
        fields["Selected execution method exact hash"] = METHOD["exact_hash"]
        fields[
            "Selected execution method canonical interface / contract reference"
        ] = METHOD["canonical_contract_reference"]
        fields[field] = value
        text, frozen = freeze_start(fields)
        path = direct_root / str(index) / "RUN-HANDOFF.md"
        write(path, text)
        if not validator_module.validate_run_start_record(
            path,
            frozen,
            {METHOD["method_id"]: METHOD},
            manifest_record(),
            {},
        ):
            review_failures.append("unsafe stable Run identity accepted: " + field)

    for name, value in (
        ("integration-substring", "UI-1 / XIB-1Y"),
        ("integration-extra-token", "UI-1 / IB-1 / EXTRA"),
        ("integration-wrong-ui", "UI-X / IB-1"),
    ):
        project = case(name)
        rewrite_start_and_receipt(
            project,
            {"Applicable UI / Integration Baseline (ENGINEERING_RUNS only)": value},
        )
        if validate_cli(project).returncode == 0:
            review_failures.append("malformed UI / Integration Baseline accepted: " + value)

    manifest_path = seed / ".lccoding/CANONICAL-MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    lock_path = seed / ".lccoding/INTERPRETATION-LOCK.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock_mutations = (
        ("status", "PENDING"),
        ("knowledge_test", "PENDING"),
        ("execution_test", "PENDING"),
        ("compatibility", "PENDING"),
        ("manifest_reference", "OTHER.json"),
        ("manifest_hash", "sha256:" + "0" * 64),
        ("validated_execution_method_ids", []),
    )
    for field, value in lock_mutations:
        mutation = copy.deepcopy(lock)
        mutation[field] = value
        _, eligible, _ = validator_module.validate_execution_method_registry(
            manifest, mutation, manifest_path
        )
        if eligible:
            review_failures.append("non-current Interpretation Lock made method eligible: " + field)

    project = case("malformed-candidate-identity")
    slice_path = project / ".lccoding/slices/FS-1.md"
    mutate_fields(
        slice_path,
        {"Accepted integration candidate / baseline identity": "CANDIDATE-1 / not-a-hash"},
    )
    mutate_fields(receipt_path_for(project, "R1"), {"Candidate ID / hash": "CANDIDATE-1 / not-a-hash"})
    mutate_fields(receipt_path_for(project, "R2"), {"Candidate ID / hash": "CANDIDATE-1 / not-a-hash"})
    if validate_cli(project).returncode == 0:
        review_failures.append("malformed accepted candidate identity was accepted")

    _, unsafe_set_errors = validator_module.parse_closed_id_set("../R1, R2", "Required Run IDs")
    if not unsafe_set_errors:
        review_failures.append("unsafe Required Run ID was accepted")

    assert not review_failures, "\n".join(review_failures)

    for name, field, value in (
        ("unknown-method", "Selected execution method ID", "UNREGISTERED"),
        ("version-mismatch", "Selected execution method version", "9.9.9"),
        ("hash-mismatch", "Selected execution method exact hash", "sha256:" + "9" * 64),
        ("interface-mismatch", "Selected execution method canonical interface / contract reference", "wrong/interface"),
    ):
        project = case(name)
        fields = parse_fields(start_path_for(project).read_text(encoding="utf-8"))
        fields[field] = value
        text, fields = freeze_start(fields)
        write(start_path_for(project), text)
        mutate_fields(receipt_path_for(project), {"Run-start contract SHA-256": fields["Start Contract SHA-256"]})
        assert validate_cli(project).returncode != 0, name

    for name, methods in (
        ("incomplete-registry", [{key: value for key, value in METHOD.items() if key != "exact_hash"}]),
        ("duplicate-registry", [METHOD, METHOD]),
        ("runtime-registry", [{**METHOD, "session_id": "runtime"}]),
    ):
        project = case(name)
        write_manifest_and_lock(project, manifest_record(methods))
        assert validate_cli(project).returncode != 0, name

    project = case("lock-mismatch")
    write_manifest_and_lock(project, manifest_record(), lock_hash="sha256:" + "0" * 64)
    assert validate_cli(project).returncode != 0

    project = case("forged-start")
    mutate_fields(start_path_for(project), {"Start Contract SHA-256": "sha256:" + "0" * 64})
    assert validate_cli(project).returncode != 0

    for name, changes in (
        ("receipt-run", {"Run ID": "WRONG"}),
        ("receipt-start", {"Run-start contract ID": "WRONG"}),
        ("receipt-candidate", {"Candidate ID / hash": "WRONG / sha256:" + "5" * 64}),
        ("receipt-phase", {"LCCoding phase scope": "PRODUCT_FORMATION"}),
        ("receipt-return", {"Evidence return target in the calling phase": "WRONG"}),
        ("receipt-no-d3", {"D3 Receipt": ""}),
        ("receipt-rejected", {"Owner result": "LOOP_PRODUCT_REWORK"}),
        ("receipt-auto-advance", {"Phase advancement": "DELIVERY_PREPARATION"}),
    ):
        project = case(name)
        mutate_fields(receipt_path_for(project), changes)
        assert validate_cli(project).returncode != 0, name

    project = case("non-phase3-counted")
    mutate_fields(start_path_for(project), {"LCCoding phase scope": "PRODUCT_FORMATION"})
    mutate_fields(receipt_path_for(project), {"LCCoding phase scope": "PRODUCT_FORMATION"})
    assert validate_cli(project).returncode != 0

    for name, required, optional, superseded, invalidated in (
        ("missing-required", "R1, R2, R3", "", "", ""),
        ("extra-unclassified", "R1", "", "", ""),
        ("duplicate-required", "R1, R1", "R2", "", ""),
        ("required-optional", "R1, R2", "R1", "", ""),
        ("required-superseded", "R1, R2", "", "R1", ""),
        ("required-invalidated", "R1, R2", "", "", "R1"),
    ):
        project = case(name)
        slice_path = project / ".lccoding/slices/FS-1.md"
        fields = parse_fields(slice_path.read_text(encoding="utf-8"))
        fields.update({"Required Run IDs": required, "Optional Run IDs": optional, "Superseded Run IDs": superseded, "Invalidated Run IDs": invalidated})
        write(slice_path, "# Feature Slice\n\n" + "\n".join(f"- {key}: {value}" for key, value in fields.items()) + "\n")
        assert validate_cli(project).returncode != 0, name

    project = case("open-gap")
    status_path = project / ".lccoding/status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    status["open_owner_gaps"] = [{"gap_id": "GAP-1", "state": "OPEN", "source_acceptance": "OA-R1", "evidence_pointers": ["reviews/OA-R1.md"]}]
    write(status_path, json.dumps(status, indent=2) + "\n")
    assert validate_cli(project).returncode != 0

    cross_phase = base / "cross-phase"
    build_cli_project(cross_phase, aggregate=False, run_phases={"R-INITIAL": "INITIAL"})
    status_before = (cross_phase / ".lccoding/status.json").read_bytes()
    result = validate_cli(cross_phase)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (cross_phase / ".lccoding/status.json").read_bytes() == status_before

print("PASS: Run start contract and Owner terminal receipt remain disjoint and bound")
