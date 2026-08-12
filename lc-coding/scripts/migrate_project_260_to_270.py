#!/usr/bin/env python3
from pathlib import Path
import argparse
import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import uuid


SCRIPT_DIR = Path(__file__).resolve().parent
VALIDATOR_PATH = SCRIPT_DIR / "validate_project.py"
VALIDATOR_SPEC = importlib.util.spec_from_file_location(
    "lccoding_migration_validate_project", VALIDATOR_PATH
)
VALIDATOR = importlib.util.module_from_spec(VALIDATOR_SPEC)
VALIDATOR_SPEC.loader.exec_module(VALIDATOR)

SOURCE_SCHEMA = "2.6.0"
TARGET_SCHEMA = "2.7.0"
PHASES = (
    "INITIAL",
    "PRODUCT_FORMATION",
    "ENGINEERING_RUNS",
    "DELIVERY_PREPARATION",
)
PHASE_GATES = {
    "INITIAL_READY",
    "CALABASH_UPGRADE_READY",
    "ALL_REQUIRED_RUNS_ACCEPTED",
    "DELIVERY_READY",
}
STATUS_STATE_FIELDS = (
    "product_baseline",
    "proposal",
    "initialization",
    "calabash_draft",
    "workflow",
    "ui",
    "simulation",
    "mandatory_calabash_upgrade",
    "all_required_runs_accepted",
    "centralized_security_audit",
    "security_remediation",
    "vulnerability_closure",
    "post_security_owner_acceptance",
    "delivery_method_qa",
    "delivery",
)
FORMATION_COMPLETION_FIELDS = (
    "calabash_draft",
    "workflow",
    "ui",
    "simulation",
    "mandatory_calabash_upgrade",
)
DELIVERY_READY_PREREQUISITE_FIELDS = (
    "centralized_security_audit",
    "security_remediation",
    "vulnerability_closure",
    "post_security_owner_acceptance",
    "delivery_method_qa",
)
REPARSE_POINT = 0x400


class MigrationError(Exception):
    pass


def is_reparse(path):
    try:
        stat = path.lstat()
    except OSError:
        return False
    return path.is_symlink() or bool(getattr(stat, "st_file_attributes", 0) & REPARSE_POINT)


def existing_components(path):
    absolute = Path(os.path.abspath(path))
    components = list(reversed((absolute, *absolute.parents)))
    return [component for component in components if component.exists() or component.is_symlink()]


def reject_ambiguous_components(path, label):
    for component in existing_components(path):
        if is_reparse(component):
            raise MigrationError(f"{label} contains a symlink or reparse-point component")


def reject_ambiguous_tree(root):
    pending = [root]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                entry_path = Path(entry.path)
                attributes = getattr(entry.stat(follow_symlinks=False), "st_file_attributes", 0)
                if entry.is_symlink() or attributes & REPARSE_POINT:
                    raise MigrationError("source project contains a symlink or reparse point")
                if entry.is_dir(follow_symlinks=False):
                    pending.append(entry_path)


def is_within(path, parent):
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def resolve_paths(source_argument, destination_argument):
    source_raw = Path(source_argument)
    destination_raw = Path(destination_argument)
    reject_ambiguous_components(source_raw, "source")
    reject_ambiguous_components(destination_raw.parent, "destination parent")
    if not source_raw.exists() or not source_raw.is_dir():
        raise MigrationError("source project must be an existing directory")
    source = source_raw.resolve(strict=True)
    destination = destination_raw.resolve(strict=False)
    destination_parent = destination.parent
    if not destination_parent.exists() or not destination_parent.is_dir():
        raise MigrationError("destination parent must be an existing directory")
    if source == destination or is_within(destination, source) or is_within(source, destination):
        raise MigrationError("source and destination must be distinct non-overlapping trees")
    if destination.exists() or destination.is_symlink():
        raise MigrationError("destination already exists")
    reject_ambiguous_tree(source)
    return source, destination, destination_parent.resolve(strict=True)


def no_duplicate_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise MigrationError("JSON record contains a duplicate key")
        result[key] = value
    return result


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicate_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise MigrationError("project record is malformed") from error


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def validate_source_shape(source):
    lc = source / ".lccoding"
    for relative in (*VALIDATOR.REQUIRED,):
        path = lc / relative
        if not path.exists() or not path.is_file():
            raise MigrationError("source is not a complete LCCoding project")
    if not (source / "VERSION").is_file():
        raise MigrationError("source project VERSION is missing")
    status = read_json(lc / "status.json")
    phase_status = read_json(lc / "PHASE-STATUS.json")
    health = read_json(lc / "PROJECT-HEALTH.json")
    if status.get("record_role") != "AUTHORITATIVE_PROJECT_STATUS":
        raise MigrationError("source status.json is not the sole authority")
    if status.get("status_schema_version") != SOURCE_SCHEMA:
        raise MigrationError("unsupported source status schema")
    if phase_status.get("record_role") != "DERIVED_VIEW" or phase_status.get("derived_from") != "status.json":
        raise MigrationError("source PHASE-STATUS is not a derived view")
    if health.get("record_role") != "ASSESSMENT_EVIDENCE":
        raise MigrationError("source Project Health role is invalid")
    gates = status.get("phase_gates")
    if not isinstance(gates, dict) or set(gates) != PHASE_GATES:
        raise MigrationError("source phase gate set is unsupported")
    for value in gates.values():
        if VALIDATOR.normalize_lifecycle_state(value) is None:
            raise MigrationError("source contains an unknown lifecycle state")
    for field in STATUS_STATE_FIELDS:
        if VALIDATOR.normalize_lifecycle_state(status.get(field)) is None:
            raise MigrationError("source contains an unknown lifecycle state")
    if VALIDATOR.nested_forbidden_fields(status, VALIDATOR.RUNTIME_STATUS_FIELDS):
        raise MigrationError("source status contains runtime fields")
    if VALIDATOR.nested_forbidden_fields(status, {"product_baseline_ready"}):
        raise MigrationError("source contains PRODUCT_BASELINE_READY")
    if status.get("current_phase") not in PHASES:
        raise MigrationError("source current phase is invalid")
    source_phases = phase_status.get("phases")
    if (
        phase_status.get("current_phase") not in PHASES
        or not isinstance(source_phases, dict)
        or set(source_phases) != set(PHASES)
    ):
        raise MigrationError("source phase view is malformed")
    for phase, record in source_phases.items():
        if not isinstance(record, dict) or record.get("status") not in VALIDATOR.COMPLETED_PHASE_STATES.union(
            {"PENDING", "ACTIVE", "BLOCKED", "INVALID"}
        ):
            raise MigrationError("source phase view is malformed")
    return status, phase_status, health


def referenced_acceptance_records(stage, status):
    acceptance_ids = status.get("loop_owner_acceptances")
    if not isinstance(acceptance_ids, list):
        raise MigrationError("authoritative acceptance index must be a list")
    normalized_ids = []
    for value in acceptance_ids:
        if not isinstance(value, str) or not value.strip():
            raise MigrationError("authoritative acceptance index contains an invalid ID")
        normalized_ids.append(value.strip())
    if len(normalized_ids) != len(set(normalized_ids)):
        raise MigrationError("authoritative acceptance index contains duplicate IDs")
    records = []
    reviews = stage / ".lccoding/reviews"
    for acceptance_id in normalized_ids:
        matches = [] if not reviews.is_dir() else [
            path
            for path in reviews.rglob("*.md")
            if str(VALIDATOR.parse_markdown_fields(path).get("Acceptance ID", "")).strip()
            == acceptance_id
        ]
        if len(matches) != 1:
            raise MigrationError("authoritative acceptance index does not resolve exactly")
        records.append((acceptance_id, VALIDATOR.parse_markdown_fields(matches[0])))
    return records


def phase3_acceptance_ids(stage, status):
    return [
        acceptance_id
        for acceptance_id, fields in referenced_acceptance_records(stage, status)
        if str(fields.get("LCCoding phase scope", "")).strip()
        == "ENGINEERING_RUNS"
    ]


def phase_status_for(status, source_phase_status, stage):
    current = status["current_phase"]
    current_index = PHASES.index(current)
    gates = status["phase_gates"]
    boundaries = {
        "INITIAL": ("exit_gate", gates["INITIAL_READY"]),
        "PRODUCT_FORMATION": ("exit_evidence", status["product_baseline"]),
        "ENGINEERING_RUNS": (
            "aggregate_exit_gate",
            gates["ALL_REQUIRED_RUNS_ACCEPTED"],
        ),
        "DELIVERY_PREPARATION": ("exit_gate", gates["DELIVERY_READY"]),
    }
    records = {}
    for index, phase in enumerate(PHASES):
        field, boundary = boundaries[phase]
        if index < current_index:
            phase_state = "COMPLETE"
        elif index > current_index:
            phase_state = "PENDING"
            boundary = "PENDING"
        else:
            normalized = VALIDATOR.normalize_lifecycle_state(boundary)
            phase_state = "BLOCKED" if normalized == "error" else "ACTIVE"
        record = {"status": phase_state, field: boundary}
        if phase == "ENGINEERING_RUNS":
            record["per_run_acceptances"] = phase3_acceptance_ids(stage, status)
        records[phase] = record
    return {
        "record_role": "DERIVED_VIEW",
        "derived_from": "status.json",
        "current_phase": current,
        "phases": records,
        "updated_at": source_phase_status.get("updated_at", ""),
        "evidence": copy.deepcopy(source_phase_status.get("evidence", [])),
        "blockers": copy.deepcopy(source_phase_status.get("blockers", [])),
    }


def write_records(stage, status, source_phase_status):
    phase_status = phase_status_for(status, source_phase_status, stage)
    if phase_status["phases"]["ENGINEERING_RUNS"][
        "per_run_acceptances"
    ] != phase3_acceptance_ids(stage, status):
        raise MigrationError("derived Phase-3 acceptance view drifted from status.json")
    errors = VALIDATOR.validate_status_authority(
        status,
        phase_status,
        read_json(stage / ".lccoding/PROJECT-HEALTH.json"),
    )
    if errors:
        raise MigrationError("migrated status failed validation: " + "; ".join(errors))
    write_json(stage / ".lccoding/status.json", status)
    write_json(stage / ".lccoding/PHASE-STATUS.json", phase_status)
    return phase_status


def run_project_validator(stage):
    return subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), str(stage)],
        capture_output=True,
        text=True,
    )


def validate_without_handoff(stage, status, source_phase_status):
    lc = stage / ".lccoding"
    handoff = lc / "PRODUCT-BASELINE-HANDOFF.md"
    hidden = lc / ".PRODUCT-BASELINE-HANDOFF.migration-probe"
    if hidden.exists():
        raise MigrationError("migration probe path already exists")
    if handoff.exists():
        handoff.rename(hidden)
    try:
        write_records(stage, status, source_phase_status)
        result = run_project_validator(stage)
    finally:
        if hidden.exists():
            hidden.rename(handoff)
    if result.returncode:
        raise MigrationError("source project fails existing mechanical validation")


def handoff_is_valid(stage, source_status, source_phase_status):
    handoff = stage / ".lccoding/PRODUCT-BASELINE-HANDOFF.md"
    if not handoff.is_file():
        return False
    probe = copy.deepcopy(source_status)
    probe["status_schema_version"] = TARGET_SCHEMA
    probe["current_phase"] = "ENGINEERING_RUNS"
    probe["phase_gates"]["ALL_REQUIRED_RUNS_ACCEPTED"] = "PENDING"
    probe["phase_gates"]["DELIVERY_READY"] = "PENDING"
    probe["all_required_runs_accepted"] = "PENDING"
    write_records(stage, probe, source_phase_status)
    return run_project_validator(stage).returncode == 0


def receipt_evidence_is_valid(stage, status):
    if status.get("open_owner_gaps") != []:
        return False
    lc = stage / ".lccoding"
    slice_path = VALIDATOR.resolve_active_slice(lc, status.get("active_slice"))
    if slice_path is None:
        return False
    slice_fields = VALIDATOR.parse_markdown_fields(slice_path)
    required_tokens = [
        token.strip()
        for token in str(slice_fields.get("Required Run IDs", "")).split(",")
        if token.strip() and token.strip().upper() != "NONE"
    ]
    if not required_tokens or len(required_tokens) != len(set(required_tokens)):
        return False
    required_runs = set(required_tokens)
    try:
        phase3_records = [
            (acceptance_id, fields)
            for acceptance_id, fields in referenced_acceptance_records(stage, status)
            if str(fields.get("LCCoding phase scope", "")).strip()
            == "ENGINEERING_RUNS"
        ]
    except MigrationError:
        return False
    if not phase3_records:
        return False
    slice_identity = str(slice_fields.get("Slice ID / version", "")).strip()
    baseline_trace = str(slice_fields.get("Product Baseline trace", "")).strip()
    if not VALIDATOR.present(slice_identity) or not VALIDATOR.present(baseline_trace):
        return False
    accepted_runs = []
    for acceptance_id, fields in phase3_records:
        run_id = str(fields.get("Run ID", "")).strip()
        candidate = str(fields.get("Candidate ID / hash", "")).strip()
        candidate_id, candidate_separator, candidate_hash = candidate.partition("/")
        gap_status = str(fields.get("Gap status", "")).strip()
        gap_route = str(fields.get("Gap route", "")).strip()
        if (
            str(fields.get("Acceptance ID", "")).strip() != acceptance_id
            or not run_id
            or str(fields.get("Feature Slice ID / version (when applicable)", "")).strip()
            != slice_identity
            or not VALIDATOR.present(candidate)
            or not candidate_separator
            or candidate_id.strip() != baseline_trace
            or not VALIDATOR.present(candidate_hash.strip())
            or not VALIDATOR.present(fields.get("D3 Receipt"))
            or not VALIDATOR.present(
                fields.get("Evidence return target in the calling phase")
            )
            or str(fields.get("Owner result", "")).strip()
            != "LOOP_OWNER_ACCEPTED"
            or str(
                fields.get("Calling phase gate remains independently evaluated", "")
            ).strip()
            != "YES"
            or not VALIDATOR.present(fields.get("Accepted at"))
            or gap_status in {"OPEN", "IN_CLOSURE"}
            or gap_route == "OWNER_DEFERRED"
        ):
            return False
        accepted_runs.append(run_id)
    return (
        len(accepted_runs) == len(set(accepted_runs))
        and set(accepted_runs) == required_runs
    )


def conservative_status(source_status, source_phase_status, stage):
    status = copy.deepcopy(source_status)
    status["status_schema_version"] = TARGET_SCHEMA
    initial_done = VALIDATOR.completed_evidence(status["phase_gates"]["INITIAL_READY"])
    original_baseline = status["product_baseline"]

    if not initial_done:
        status["current_phase"] = "INITIAL"
        status["product_baseline"] = "PENDING"
        status["phase_gates"]["ALL_REQUIRED_RUNS_ACCEPTED"] = "PENDING"
        status["all_required_runs_accepted"] = "PENDING"
        status["phase_gates"]["DELIVERY_READY"] = "PENDING"
        return status

    baseline_claimed = VALIDATOR.completed_evidence(original_baseline)
    formation_complete = all(
        VALIDATOR.completed_evidence(source_status.get(field))
        for field in FORMATION_COMPLETION_FIELDS
    )
    baseline_valid = (
        formation_complete
        and baseline_claimed
        and handoff_is_valid(stage, source_status, source_phase_status)
    )
    if not baseline_valid:
        status["current_phase"] = "PRODUCT_FORMATION"
        status["product_baseline"] = "BLOCKED" if baseline_claimed else original_baseline
        status["phase_gates"]["ALL_REQUIRED_RUNS_ACCEPTED"] = "PENDING"
        status["all_required_runs_accepted"] = "PENDING"
        status["phase_gates"]["DELIVERY_READY"] = "PENDING"
        return status

    status["current_phase"] = "ENGINEERING_RUNS"
    status["product_baseline"] = original_baseline
    gate_aggregate = source_status["phase_gates"]["ALL_REQUIRED_RUNS_ACCEPTED"]
    direct_aggregate = source_status["all_required_runs_accepted"]
    aggregate_claimed = VALIDATOR.completed_evidence(
        gate_aggregate
    ) or VALIDATOR.completed_evidence(direct_aggregate)
    aggregate_complete = (
        VALIDATOR.completed_evidence(gate_aggregate)
        and VALIDATOR.completed_evidence(direct_aggregate)
        and receipt_evidence_is_valid(stage, source_status)
    )
    source_delivery_gate = source_status["phase_gates"]["DELIVERY_READY"]
    if aggregate_complete:
        status["current_phase"] = "DELIVERY_PREPARATION"
        status["phase_gates"]["ALL_REQUIRED_RUNS_ACCEPTED"] = gate_aggregate
        status["all_required_runs_accepted"] = direct_aggregate
    elif aggregate_claimed:
        status["phase_gates"]["ALL_REQUIRED_RUNS_ACCEPTED"] = "BLOCKED"
        status["all_required_runs_accepted"] = "BLOCKED"
    delivery_gate_complete = VALIDATOR.completed_evidence(source_delivery_gate)
    actual_delivery_complete = VALIDATOR.completed_evidence(
        source_status.get("delivery")
    )
    if actual_delivery_complete and not delivery_gate_complete:
        raise MigrationError("actual Delivery completion precedes DELIVERY_READY")
    if delivery_gate_complete:
        later_evidence_complete = all(
            VALIDATOR.completed_evidence(source_status.get(field))
            for field in DELIVERY_READY_PREREQUISITE_FIELDS
        )
        if (
            not aggregate_complete
            or source_status.get("current_phase") != "DELIVERY_PREPARATION"
            or not later_evidence_complete
        ):
            raise MigrationError("completed Delivery boundary lacks current prerequisite evidence")
        status["phase_gates"]["DELIVERY_READY"] = source_delivery_gate
    elif aggregate_complete and source_status.get("current_phase") == "DELIVERY_PREPARATION":
        status["phase_gates"]["DELIVERY_READY"] = source_delivery_gate
    else:
        status["phase_gates"]["DELIVERY_READY"] = "PENDING"
    return status


def safe_cleanup(stage, destination_parent, destination_name):
    if not stage.exists():
        return
    resolved = stage.resolve(strict=True)
    expected_prefix = f".{destination_name}.lccoding-migrate-"
    if resolved.parent != destination_parent or not resolved.name.startswith(expected_prefix):
        raise MigrationError("refusing to clean an uncontained migration stage")
    def remove_readonly(function, path, _error):
        os.chmod(path, 0o700)
        function(path)

    shutil.rmtree(resolved, onexc=remove_readonly)


def migrate(source_argument, destination_argument):
    source, destination, destination_parent = resolve_paths(
        source_argument, destination_argument
    )
    source_status, source_phase_status, _ = validate_source_shape(source)
    stage = destination_parent / (
        f".{destination.name}.lccoding-migrate-{uuid.uuid4().hex}"
    )
    if stage.exists():
        raise MigrationError("migration stage already exists")
    try:
        shutil.copytree(source, stage, copy_function=shutil.copy2)
        probe = copy.deepcopy(source_status)
        probe["status_schema_version"] = TARGET_SCHEMA
        if VALIDATOR.completed_evidence(probe["phase_gates"]["INITIAL_READY"]):
            probe["current_phase"] = "PRODUCT_FORMATION"
            probe["product_baseline"] = "BLOCKED"
        else:
            probe["current_phase"] = "INITIAL"
            probe["product_baseline"] = "PENDING"
        probe["phase_gates"]["ALL_REQUIRED_RUNS_ACCEPTED"] = "PENDING"
        probe["all_required_runs_accepted"] = "PENDING"
        probe["phase_gates"]["DELIVERY_READY"] = "PENDING"
        validate_without_handoff(stage, probe, source_phase_status)

        migrated_status = conservative_status(source_status, source_phase_status, stage)
        write_records(stage, migrated_status, source_phase_status)
        final_validation = run_project_validator(stage)
        if final_validation.returncode:
            raise MigrationError("migrated project fails existing mechanical validation")
        stage.rename(destination)
    except Exception:
        safe_cleanup(stage, destination_parent, destination.name)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--output", required=True)
    arguments = parser.parse_args()
    try:
        migrate(arguments.project, arguments.output)
    except MigrationError as error:
        print("FAIL")
        print(str(error))
        raise SystemExit(1)
    print("PASS")


if __name__ == "__main__":
    main()
