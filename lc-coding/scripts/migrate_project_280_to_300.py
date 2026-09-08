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
PROJECT_VALIDATOR_PATH = SCRIPT_DIR / "validate_project.py"
PHASE_VALIDATOR_PATH = SCRIPT_DIR / "validate_phase_status.py"
STATUS_TEMPLATE_PATH = SCRIPT_DIR.parent / "templates/STATUS.json"
PHASE_SPEC = importlib.util.spec_from_file_location(
    "lccoding_migration_300_phase_validation", PHASE_VALIDATOR_PATH
)
PHASE_VALIDATOR = importlib.util.module_from_spec(PHASE_SPEC)
PHASE_SPEC.loader.exec_module(PHASE_VALIDATOR)

SOURCE_SCHEMA = "2.8.0"
TARGET_SCHEMA = "3.0.0"
SOURCE_PHASES = (
    "INITIAL",
    "PRODUCT_FORMATION",
    "REAL_PRODUCT_INTEGRATION",
    "DELIVERY_PREPARATION",
)
TARGET_PHASES = (
    "INITIAL",
    "PRODUCT_FORMATION",
    "REAL_PRODUCT_INTEGRATION",
    "REAL_USER_JOURNEY_ACCEPTANCE",
    "DELIVERY_PREPARATION",
)
SOURCE_GATES = {
    "INITIAL_READY",
    "CALABASH_UPGRADE_READY",
    "ALL_REQUIRED_RUNS_ACCEPTED",
    "DELIVERY_READY",
}
TARGET_GATES = (
    "INITIAL_READY",
    "CALABASH_UPGRADE_READY",
    "ALL_REQUIRED_RUNS_ACCEPTED",
    "REAL_USER_JOURNEY_ACCEPTED",
    "DELIVERY_READY",
)
GENERATED_COMPONENTS = {
    "gen",
    "node_modules",
    "dist",
    "target",
    "test-results",
    "playwright-report",
}
HISTORY_ROOT = Path("history/2.8.0")
REPORT_REFERENCE = "MIGRATION-2.8.0-TO-3.0.0.json"
JOURNEY_FIELD = "real_user_journey_acceptance"
JOURNEY_BLOCKER = "REAL_USER_JOURNEY_ACCEPTANCE_UNPROVED"
REPARSE_POINT = 0x400


class MigrationError(Exception):
    pass


def reject_constant(_value):
    raise MigrationError("JSON record contains a non-finite number")


def no_duplicate_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise MigrationError("JSON record contains a duplicate key")
        result[key] = value
    return result


def read_json(path):
    try:
        return json.loads(
            Path(path).read_text(encoding="utf-8"),
            object_pairs_hook=no_duplicate_object,
            parse_constant=reject_constant,
        )
    except MigrationError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise MigrationError("project record is malformed") from error


def write_json(path, value):
    Path(path).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def is_reparse(path):
    try:
        status = Path(path).lstat()
    except OSError:
        return False
    return Path(path).is_symlink() or bool(
        getattr(status, "st_file_attributes", 0) & REPARSE_POINT
    )


def existing_components(path):
    absolute = Path(os.path.abspath(path))
    return [
        component
        for component in reversed((absolute, *absolute.parents))
        if component.exists() or component.is_symlink()
    ]


def reject_ambiguous_components(path, label):
    for component in existing_components(path):
        if is_reparse(component):
            raise MigrationError(f"{label} contains a symlink or reparse point")


def reject_ambiguous_or_generated_tree(root):
    if any(part.casefold() in GENERATED_COMPONENTS for part in root.parts):
        raise MigrationError("generated output cannot be a migration input")
    pending = [root]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                path = Path(entry.path)
                attributes = getattr(
                    entry.stat(follow_symlinks=False), "st_file_attributes", 0
                )
                if entry.is_symlink() or attributes & REPARSE_POINT:
                    raise MigrationError("source contains a symlink or reparse point")
                if entry.name.casefold() in GENERATED_COMPONENTS:
                    raise MigrationError("generated output cannot be a migration input")
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)


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
        raise MigrationError("source must be an existing project directory")
    source = source_raw.resolve(strict=True)
    destination = destination_raw.resolve(strict=False)
    if not destination.parent.exists() or not destination.parent.is_dir():
        raise MigrationError("destination parent must be an existing directory")
    destination_parent = destination.parent.resolve(strict=True)
    if source == destination or is_within(destination, source) or is_within(source, destination):
        raise MigrationError("source and destination must be distinct non-overlapping trees")
    if destination.exists() or destination.is_symlink():
        raise MigrationError("destination already exists")
    reject_ambiguous_or_generated_tree(source)
    return source, destination, destination_parent


def run_project_validator(project):
    return subprocess.run(
        [sys.executable, str(PROJECT_VALIDATOR_PATH), str(project)],
        capture_output=True,
        text=True,
    )


def run_phase_validator(project):
    return subprocess.run(
        [
            sys.executable,
            str(PHASE_VALIDATOR_PATH),
            str(Path(project) / ".lccoding/PHASE-STATUS.json"),
        ],
        capture_output=True,
        text=True,
    )


def choose_target_phase(status, reopen_delivery_preparation=False):
    current = status.get("current_phase")
    if current == "DELIVERY_PREPARATION":
        if not reopen_delivery_preparation:
            raise MigrationError(
                "Delivery Preparation source requires explicit Phase-4 reopening"
            )
        return "REAL_USER_JOURNEY_ACCEPTANCE"
    if current == "REAL_PRODUCT_INTEGRATION" and PHASE_VALIDATOR.completed_evidence(
        status.get("phase_gates", {}).get("ALL_REQUIRED_RUNS_ACCEPTED")
    ):
        return "REAL_USER_JOURNEY_ACCEPTANCE"
    return current


def validate_source(source, reopen_delivery_preparation=False):
    lc = source / ".lccoding"
    status_path = lc / "status.json"
    phase_path = lc / "PHASE-STATUS.json"
    if not status_path.is_file() or not phase_path.is_file():
        raise MigrationError("source lacks authoritative status records")
    status = read_json(status_path)
    phase_status = read_json(phase_path)
    template = read_json(STATUS_TEMPLATE_PATH)
    if template.get("status_schema_version") == "4.0.0":
        template = copy.deepcopy(template)
        for field in (
            "lccoding_applicability",
            "product_service_strategy",
            "service_route_map",
        ):
            template.pop(field, None)
        template["status_schema_version"] = TARGET_SCHEMA
    if template.get("status_schema_version") != TARGET_SCHEMA:
        raise MigrationError("installed target status template is not 3.0.0")
    source_fields = set(template) - {JOURNEY_FIELD}
    if set(status) != source_fields:
        raise MigrationError("source status does not use the closed 2.8 status shape")
    if status.get("record_role") != "AUTHORITATIVE_PROJECT_STATUS":
        raise MigrationError("source status is not authoritative")
    if status.get("status_schema_version") != SOURCE_SCHEMA:
        raise MigrationError("source status schema must be exact 2.8.0")
    if status.get("current_phase") not in SOURCE_PHASES:
        raise MigrationError("source current phase is not a 2.8 phase identity")
    if set(status.get("phase_gates", {})) != SOURCE_GATES:
        raise MigrationError("source phase gate set is not closed")
    if phase_status.get("status_schema_version") != SOURCE_SCHEMA:
        raise MigrationError("source derived phase schema must be exact 2.8.0")
    if phase_status.get("record_role") != "DERIVED_VIEW" or phase_status.get(
        "derived_from"
    ) != "status.json":
        raise MigrationError("source phase view is not derived from status.json")
    if phase_status.get("current_phase") != status.get("current_phase"):
        raise MigrationError("source status and phase view disagree")
    if tuple(phase_status.get("phases", {})) != SOURCE_PHASES:
        raise MigrationError("source phase identity is mixed, inferred, or unknown")
    if (lc / HISTORY_ROOT).exists():
        raise MigrationError("source already contains a 2.8 migration history target")
    choose_target_phase(status, reopen_delivery_preparation)
    validation = run_project_validator(source)
    if validation.returncode:
        raise MigrationError("source fails complete project validation")
    return status, phase_status, template


def migrated_status(source, template, reopen_delivery_preparation=False):
    status = copy.deepcopy(template)
    for field, value in source.items():
        status[field] = copy.deepcopy(value)
    status["status_schema_version"] = TARGET_SCHEMA
    status["current_phase"] = choose_target_phase(source, reopen_delivery_preparation)
    source_gates = source["phase_gates"]
    status["phase_gates"] = {
        gate: (
            "PENDING"
            if gate in {"REAL_USER_JOURNEY_ACCEPTED", "DELIVERY_READY"}
            else copy.deepcopy(source_gates[gate])
        )
        for gate in TARGET_GATES
    }
    status[JOURNEY_FIELD] = copy.deepcopy(template[JOURNEY_FIELD])
    status["centralized_security_audit"] = "PENDING"
    status["security_remediation"] = "PENDING"
    status["vulnerability_closure"] = copy.deepcopy(template["vulnerability_closure"])
    status["post_security_owner_acceptance"] = copy.deepcopy(
        template["post_security_owner_acceptance"]
    )
    status["delivery_method_qa"] = "PENDING"
    status["delivery"] = "PENDING"
    status["last_material_change"] = ""
    status["next_action"] = "RUN_REAL_USER_JOURNEY_ACCEPTANCE"
    status["evidence_pointers"] = list(dict.fromkeys(
        [*source.get("evidence_pointers", []), REPORT_REFERENCE]
    ))
    status["blockers"] = list(dict.fromkeys(
        [*source.get("blockers", []), JOURNEY_BLOCKER]
    ))
    if set(status) != set(template):
        raise MigrationError("target status does not use the closed 3.0 status shape")
    return status


def migrated_phase_status(status, source_phase_status):
    current = status["current_phase"]
    phases = copy.deepcopy(source_phase_status["phases"])
    if current == "REAL_USER_JOURNEY_ACCEPTANCE":
        phases["REAL_PRODUCT_INTEGRATION"]["status"] = "COMPLETE"
    journey = {
        "status": "ACTIVE" if current == "REAL_USER_JOURNEY_ACCEPTANCE" else "PENDING",
        "acceptance_record": "NOT_APPLICABLE",
        "defect_log": "NOT_APPLICABLE",
        "complete_rounds": 0,
        "exit_gate": "PENDING",
    }
    delivery = copy.deepcopy(phases["DELIVERY_PREPARATION"])
    delivery["status"] = "PENDING"
    delivery["exit_gate"] = "PENDING"
    ordered = {
        "INITIAL": phases["INITIAL"],
        "PRODUCT_FORMATION": phases["PRODUCT_FORMATION"],
        "REAL_PRODUCT_INTEGRATION": phases["REAL_PRODUCT_INTEGRATION"],
        "REAL_USER_JOURNEY_ACCEPTANCE": journey,
        "DELIVERY_PREPARATION": delivery,
    }
    return {
        "record_role": "DERIVED_VIEW",
        "status_schema_version": TARGET_SCHEMA,
        "derived_from": "status.json",
        "current_phase": current,
        "phases": ordered,
        "updated_at": source_phase_status.get("updated_at", ""),
        "evidence": list(dict.fromkeys(
            [*source_phase_status.get("evidence", []), REPORT_REFERENCE]
        )),
        "blockers": list(dict.fromkeys(
            [*source_phase_status.get("blockers", []), JOURNEY_BLOCKER]
        )),
    }


def migration_report(reopened):
    return {
        "artifact_role": "LCCODING_3_0_MIGRATION_EVIDENCE",
        "source_status_schema": SOURCE_SCHEMA,
        "target_status_schema": TARGET_SCHEMA,
        "phase_inserted": "REAL_USER_JOURNEY_ACCEPTANCE",
        "journey_evidence_state": "UNPROVED",
        "source_delivery_preparation_reopened": reopened,
        "historical_evidence": {
            "root": ".lccoding/history/2.8.0",
            "treatment": "HISTORICAL_ONLY_NOT_PHASE_4_PROOF",
        },
        "result": "MIGRATED_CANDIDATE_REQUIRES_REAL_USER_JOURNEY_ACCEPTANCE",
    }


def transform(stage, source_status, source_phase_status, template, reopened):
    lc = stage / ".lccoding"
    history = lc / HISTORY_ROOT
    history.mkdir(parents=True)
    shutil.copy2(lc / "status.json", history / "status.json")
    shutil.copy2(lc / "PHASE-STATUS.json", history / "PHASE-STATUS.json")
    status = migrated_status(source_status, template, reopened)
    phase_status = migrated_phase_status(status, source_phase_status)
    write_json(lc / "status.json", status)
    write_json(lc / "PHASE-STATUS.json", phase_status)
    write_json(lc / REPORT_REFERENCE, migration_report(reopened))
    if tuple(phase_status["phases"]) != TARGET_PHASES:
        raise MigrationError("target phase identity is not exact 3.0.0")


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

    shutil.rmtree(resolved, onerror=remove_readonly)


def migrate(source_argument, destination_argument, reopen_delivery_preparation=False):
    source, destination, destination_parent = resolve_paths(
        source_argument, destination_argument
    )
    source_status, source_phase_status, template = validate_source(
        source, reopen_delivery_preparation
    )
    stage = destination_parent / f".{destination.name}.lccoding-migrate-{uuid.uuid4().hex}"
    try:
        shutil.copytree(source, stage, copy_function=shutil.copy2)
        transform(
            stage,
            source_status,
            source_phase_status,
            template,
            reopen_delivery_preparation,
        )
        if run_phase_validator(stage).returncode:
            raise MigrationError("target phase view fails complete validation")
        if run_project_validator(stage).returncode:
            raise MigrationError("target project fails complete validation")
        stage.rename(destination)
    except Exception:
        safe_cleanup(stage, destination_parent, destination.name)
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Copy an exact LCCoding 2.8 project into a conservative 3.0 candidate."
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--reopen-delivery-preparation", action="store_true")
    arguments = parser.parse_args()
    try:
        migrate(
            arguments.project,
            arguments.output,
            arguments.reopen_delivery_preparation,
        )
    except MigrationError as error:
        print("FAIL")
        print(str(error))
        raise SystemExit(1)
    except Exception:
        print("FAIL")
        print("migration failed closed")
        raise SystemExit(1)
    print("PASS")


if __name__ == "__main__":
    main()
