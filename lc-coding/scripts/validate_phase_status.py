#!/usr/bin/env python3
from pathlib import Path
import argparse
import json


LEGACY_PHASE_ORDER = (
    "INITIAL",
    "PRODUCT_FORMATION",
    "ENGINEERING_RUNS",
    "DELIVERY_PREPARATION",
)
CURRENT_PHASE_ORDER = (
    "INITIAL",
    "PRODUCT_FORMATION",
    "REAL_PRODUCT_INTEGRATION",
    "DELIVERY_PREPARATION",
)
SCHEMA_PHASE_ORDERS = {
    "2.6.0": LEGACY_PHASE_ORDER,
    "2.7.0": LEGACY_PHASE_ORDER,
    "2.8.0": CURRENT_PHASE_ORDER,
}
TOP_LEVEL_FIELDS = {
    "record_role",
    "status_schema_version",
    "derived_from",
    "current_phase",
    "phases",
    "updated_at",
    "evidence",
    "blockers",
}
DONE_STATES = {
    "ACCEPTED",
    "ALL_REQUIRED_RUNS_ACCEPTED",
    "CLOSED",
    "COMPLETE",
    "COMPLETED",
    "DELIVERED",
    "DELIVERY_READY",
    "DONE",
    "ESTABLISHED",
    "EVIDENCED",
    "INITIALIZED",
    "INVENTORIED",
    "LOCKED",
    "LOOP_OWNER_ACCEPTED",
    "PASS",
    "PASSED",
    "POST_SECURITY_OWNER_ACCEPTED",
    "READY",
    "RECONSTRUCTED",
    "VERIFIED",
    "VULNERABILITY_CLOSED",
}
ACTIVE_STATES = {
    "ACTIVE",
    "EXECUTING",
    "EXISTING_INTAKE_PENDING",
    "IN_PROGRESS",
    "RUNNING",
}
PENDING_STATES = {"PENDING"}
ERROR_STATES = {
    "BLOCKED",
    "ERROR",
    "FAIL",
    "FAILED",
    "INVALID",
    "NOT_CONTINUING",
    "REJECTED",
}
PHASE_STATES = {"PENDING", "ACTIVE", "COMPLETE", "DONE", "BLOCKED", "INVALID"}
COMPLETED_PHASE_STATES = {"COMPLETE", "DONE"}


def normalize_lifecycle_state(value):
    if not isinstance(value, str):
        return None
    if value in DONE_STATES:
        return "done"
    if value in ACTIVE_STATES:
        return "active"
    if value in PENDING_STATES:
        return "pending"
    if value in ERROR_STATES:
        return "error"
    return None


def completed_evidence(value):
    return normalize_lifecycle_state(value) == "done"


def _phase_fields(phase_id):
    if phase_id == "INITIAL":
        return {"status", "exit_gate"}, "exit_gate"
    if phase_id == "PRODUCT_FORMATION":
        return {"status", "exit_evidence"}, "exit_evidence"
    if phase_id in {"ENGINEERING_RUNS", "REAL_PRODUCT_INTEGRATION"}:
        return {
            "status",
            "per_run_acceptances",
            "aggregate_exit_gate",
        }, "aggregate_exit_gate"
    return {"status", "exit_gate"}, "exit_gate"


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def load_phase_status(path):
    text = Path(path).read_bytes().decode("utf-8")
    value = json.loads(text, object_pairs_hook=_strict_object)
    if not isinstance(value, dict):
        raise ValueError("phase status must be a JSON object")
    return value


def validate_phase_status(data):
    if not isinstance(data, dict):
        return ["phase status must be an object"]

    errors = []
    fields = set(data)
    missing = TOP_LEVEL_FIELDS - fields
    unknown = fields - TOP_LEVEL_FIELDS
    if missing:
        errors.append("missing top-level field " + ", ".join(sorted(missing)))
    if unknown:
        errors.append("unexpected top-level field " + ", ".join(sorted(unknown)))

    schema = data.get("status_schema_version")
    if "status_schema_version" not in data:
        errors.append("status_schema_version is required")
    order = SCHEMA_PHASE_ORDERS.get(schema)
    if order is None:
        errors.append("unsupported status_schema_version")

    if data.get("record_role") != "DERIVED_VIEW" or data.get("derived_from") != "status.json":
        errors.append("PHASE-STATUS must remain a status.json DERIVED_VIEW")
    if not isinstance(data.get("updated_at"), str):
        errors.append("updated_at must be a string")
    for field in ("evidence", "blockers"):
        if not isinstance(data.get(field), list):
            errors.append(field + " must be an array")

    current = data.get("current_phase")
    phases = data.get("phases")
    if not isinstance(phases, dict):
        return errors + ["phases must be an object"]
    if order is None:
        if not isinstance(current, str):
            errors.append("invalid current_phase")
        return errors

    if tuple(phases) != order:
        errors.append("phase identity does not match schema")
    if current not in order:
        errors.append("invalid current_phase")

    for phase_id in order:
        record = phases.get(phase_id)
        if not isinstance(record, dict):
            errors.append("invalid phase record: " + phase_id)
            continue
        expected_fields, boundary_field = _phase_fields(phase_id)
        record_fields = set(record)
        missing_fields = expected_fields - record_fields
        unknown_fields = record_fields - expected_fields
        if missing_fields:
            errors.append(
                "missing phase field "
                + phase_id
                + ": "
                + ", ".join(sorted(missing_fields))
            )
        if unknown_fields:
            errors.append(
                "unexpected phase field "
                + phase_id
                + ": "
                + ", ".join(sorted(unknown_fields))
            )
        phase_state = record.get("status")
        if phase_state not in PHASE_STATES:
            errors.append("invalid phase status: " + phase_id)
        if normalize_lifecycle_state(record.get(boundary_field)) is None:
            label = "exit evidence" if boundary_field == "exit_evidence" else "exit gate"
            errors.append(f"invalid {label} state: {phase_id}")
        if phase_id in {"ENGINEERING_RUNS", "REAL_PRODUCT_INTEGRATION"} and not isinstance(
            record.get("per_run_acceptances"), list
        ):
            errors.append("per_run_acceptances must be an array")

    formation = phases.get("PRODUCT_FORMATION", {})
    if isinstance(formation, dict) and "exit_gate" in formation:
        errors.append("Product Formation must derive exit evidence, not an exit gate")

    if current in order:
        idx = order.index(current)
        for prior in order[:idx]:
            record = phases.get(prior, {})
            _, boundary_field = _phase_fields(prior)
            if not completed_evidence(record.get(boundary_field)):
                errors.append("prior phase boundary not complete: " + prior)
            if record.get("status") not in COMPLETED_PHASE_STATES:
                errors.append("prior phase status not complete: " + prior)
        current_record = phases.get(current, {})
        if current_record.get("status") == "PENDING":
            errors.append("current phase status must not be PENDING: " + current)
        for future in order[idx + 1 :]:
            record = phases.get(future, {})
            if record.get("status") != "PENDING":
                errors.append("future phase status must be PENDING: " + future)
            _, boundary_field = _phase_fields(future)
            if normalize_lifecycle_state(record.get(boundary_field)) != "pending":
                errors.append("future phase boundary must be PENDING: " + future)
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("status")
    args = parser.parse_args()
    try:
        data = load_phase_status(args.status)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        print("FAIL")
        print(str(error))
        raise SystemExit(1)
    errors = validate_phase_status(data)
    if errors:
        print("FAIL")
        print("\n".join(errors))
        raise SystemExit(1)
    print("PASS")


if __name__ == "__main__":
    main()
