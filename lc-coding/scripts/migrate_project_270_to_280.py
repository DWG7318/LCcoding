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
    "lccoding_migration_phase_validation", PHASE_VALIDATOR_PATH
)
PHASE_VALIDATOR = importlib.util.module_from_spec(PHASE_SPEC)
PHASE_SPEC.loader.exec_module(PHASE_VALIDATOR)

SOURCE_SCHEMA = "2.7.0"
TARGET_SCHEMA = "2.8.0"
SOURCE_PHASES = (
    "INITIAL",
    "PRODUCT_FORMATION",
    "ENGINEERING_RUNS",
    "DELIVERY_PREPARATION",
)
TARGET_PHASES = (
    "INITIAL",
    "PRODUCT_FORMATION",
    "REAL_PRODUCT_INTEGRATION",
    "DELIVERY_PREPARATION",
)
PHASE_GATES = {
    "INITIAL_READY",
    "CALABASH_UPGRADE_READY",
    "ALL_REQUIRED_RUNS_ACCEPTED",
    "DELIVERY_READY",
}
GENERATED_COMPONENTS = {
    "gen",
    "node_modules",
    "dist",
    "target",
    "test-results",
    "playwright-report",
}
HISTORICAL_DIRECTORIES = ("runs", "reviews")
HISTORICAL_RECEIPTS = (
    "VULNERABILITY-CLOSURE.json",
    "POST-SECURITY-OWNER-ACCEPTANCE.md",
)
HISTORY_ROOT = Path("history/2.7.0")
REPORT_REFERENCE = "MIGRATION-2.7.0-TO-2.8.0.json"
AGENT_PRODUCT_FORMATION_FIELD = "agent_product_formation"
BLOCKERS = [
    "AGENT_CONFIGURATION_BASELINE_UNPROVED",
    "AGENT_SECURITY_EVIDENCE_UNPROVED",
    "OPERATIONS_AGENT_INTEGRATION_UNPROVED",
    "PRODUCT_OPERATIONS_AGENT_ISOLATION_UNPROVED",
    "PRODUCTION_EXECUTION_TOPOLOGY_UNPROVED",
    "RUNTIME_ADAPTER_ATTESTATION_UNPROVED",
]
MIGRATION_REPORT = {
    "artifact_role": "LCCODING_2_8_MIGRATION_EVIDENCE",
    "source_status_schema": SOURCE_SCHEMA,
    "target_status_schema": TARGET_SCHEMA,
    "phase_identity": {
        "source": "ENGINEERING_RUNS",
        "target": "REAL_PRODUCT_INTEGRATION",
        "result": "MAPPED_WITHOUT_COMPLETION",
    },
    "required_evidence": {
        "agent_configuration_baseline": "UNPROVED",
        "agent_security_evidence": "UNPROVED",
        "operations_agent_integration": "UNPROVED",
        "product_operations_agent_isolation": "UNPROVED",
        "production_execution_topology": "UNPROVED",
        "runtime_adapter_attestation": "UNPROVED",
    },
    "topology_dispositions": ["SELECT", "COMPOSE", "FEDERATE", "RETIRE"],
    "historical_evidence": {
        "root": ".lccoding/history/2.7.0",
        "treatment": "HISTORICAL_ONLY_NOT_CURRENT",
    },
    "new_lifecycle_gates": [],
    "new_lifecycle_steps": [],
    "result": "MIGRATED_CANDIDATE_REQUIRES_REPROOF",
}
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
            path.read_text(encoding="utf-8"),
            object_pairs_hook=no_duplicate_object,
            parse_constant=reject_constant,
        )
    except MigrationError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise MigrationError("project record is malformed") from error


def write_json(path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def is_reparse(path):
    try:
        status = path.lstat()
    except OSError:
        return False
    return path.is_symlink() or bool(
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
    for component in root.parts:
        if component.casefold() in GENERATED_COMPONENTS:
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
    destination_parent = destination.parent
    if not destination_parent.exists() or not destination_parent.is_dir():
        raise MigrationError("destination parent must be an existing directory")
    destination_parent = destination_parent.resolve(strict=True)
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
            str(project / ".lccoding/PHASE-STATUS.json"),
        ],
        capture_output=True,
        text=True,
    )


def validate_source(source):
    lc = source / ".lccoding"
    status_path = lc / "status.json"
    phase_path = lc / "PHASE-STATUS.json"
    if not status_path.is_file() or not phase_path.is_file():
        raise MigrationError("source lacks authoritative status records")
    status = read_json(status_path)
    phase_status = read_json(phase_path)
    target_template = read_json(STATUS_TEMPLATE_PATH)
    if target_template.get("status_schema_version") != TARGET_SCHEMA:
        raise MigrationError("installed target status template is not 2.8.0")
    agent_default = target_template.get(AGENT_PRODUCT_FORMATION_FIELD)
    if not isinstance(agent_default, dict) or agent_default.get("state") != "UNPROVED":
        raise MigrationError("installed target status template lacks unproved Agent state")
    source_fields = set(target_template) - {AGENT_PRODUCT_FORMATION_FIELD}
    if set(status) != source_fields:
        raise MigrationError("source status does not use the closed 2.7 status shape")
    if status.get("record_role") != "AUTHORITATIVE_PROJECT_STATUS":
        raise MigrationError("source status is not authoritative")
    if status.get("status_schema_version") != SOURCE_SCHEMA:
        raise MigrationError("source status schema must be exact 2.7.0")
    if status.get("current_phase") not in SOURCE_PHASES:
        raise MigrationError("source current phase is not a 2.7 phase identity")
    if set(status.get("phase_gates", {})) != PHASE_GATES:
        raise MigrationError("source phase gate set is not closed")
    if phase_status.get("status_schema_version") != SOURCE_SCHEMA:
        raise MigrationError("source derived phase schema must be exact 2.7.0")
    if phase_status.get("record_role") != "DERIVED_VIEW" or phase_status.get(
        "derived_from"
    ) != "status.json":
        raise MigrationError("source phase view is not derived from status.json")
    if phase_status.get("current_phase") != status.get("current_phase"):
        raise MigrationError("source status and phase view disagree")
    if tuple(phase_status.get("phases", {})) != SOURCE_PHASES:
        raise MigrationError("source phase identity is mixed, inferred, or unknown")
    if (lc / HISTORY_ROOT).exists():
        raise MigrationError("source already contains a 2.7 migration history target")
    validation = run_project_validator(source)
    if validation.returncode:
        raise MigrationError("source fails complete project validation")
    return status, phase_status, target_template


def archive_historical_evidence(stage):
    lc = stage / ".lccoding"
    history = lc / HISTORY_ROOT
    history.mkdir(parents=True)
    shutil.copy2(lc / "status.json", history / "status.json")
    shutil.copy2(lc / "PHASE-STATUS.json", history / "PHASE-STATUS.json")
    for name in HISTORICAL_DIRECTORIES:
        source = lc / name
        if source.exists():
            shutil.move(str(source), str(history / name))
    for name in HISTORICAL_RECEIPTS:
        source = lc / name
        if source.exists():
            shutil.move(str(source), str(history / name))


def migrated_status(source, target_template):
    status = copy.deepcopy(source)
    status["status_schema_version"] = TARGET_SCHEMA
    status[AGENT_PRODUCT_FORMATION_FIELD] = copy.deepcopy(
        target_template[AGENT_PRODUCT_FORMATION_FIELD]
    )
    initial_complete = PHASE_VALIDATOR.completed_evidence(
        source["phase_gates"]["INITIAL_READY"]
    )
    status["current_phase"] = "PRODUCT_FORMATION" if initial_complete else "INITIAL"
    status["product_baseline"] = "PENDING"
    status["active_slice"] = None
    status["integration_baseline"] = None
    status["active_runs"] = []
    status["loop_owner_acceptances"] = []
    status["open_owner_gaps"] = []
    status["phase_gates"]["ALL_REQUIRED_RUNS_ACCEPTED"] = "PENDING"
    status["phase_gates"]["DELIVERY_READY"] = "PENDING"
    status["all_required_runs_accepted"] = "PENDING"
    status["centralized_security_audit"] = "PENDING"
    status["security_remediation"] = "PENDING"
    status["vulnerability_closure"] = copy.deepcopy(
        target_template["vulnerability_closure"]
    )
    status["post_security_owner_acceptance"] = copy.deepcopy(
        target_template["post_security_owner_acceptance"]
    )
    status["delivery_method_qa"] = "PENDING"
    status["delivery"] = "PENDING"
    status["last_material_change"] = ""
    status["next_action"] = "PROVE_2_8_AGENT_NATIVE_REQUIREMENTS"
    status["evidence_pointers"] = [REPORT_REFERENCE]
    status["blockers"] = list(BLOCKERS)
    if set(status) != set(target_template):
        raise MigrationError("target status does not use the closed 2.8 status shape")
    return status


def migrated_phase_status(status, source_phase_status):
    current = status["current_phase"]
    initial_status = "ACTIVE" if current == "INITIAL" else "COMPLETE"
    formation_status = "PENDING" if current == "INITIAL" else "ACTIVE"
    return {
        "record_role": "DERIVED_VIEW",
        "status_schema_version": TARGET_SCHEMA,
        "derived_from": "status.json",
        "current_phase": current,
        "phases": {
            "INITIAL": {
                "status": initial_status,
                "exit_gate": status["phase_gates"]["INITIAL_READY"],
            },
            "PRODUCT_FORMATION": {
                "status": formation_status,
                "exit_evidence": status["product_baseline"],
            },
            "REAL_PRODUCT_INTEGRATION": {
                "status": "PENDING",
                "per_run_acceptances": [],
                "aggregate_exit_gate": "PENDING",
            },
            "DELIVERY_PREPARATION": {
                "status": "PENDING",
                "exit_gate": "PENDING",
            },
        },
        "updated_at": source_phase_status.get("updated_at", ""),
        "evidence": [REPORT_REFERENCE],
        "blockers": list(BLOCKERS),
    }


def transform(stage, source_status, source_phase_status, target_template):
    lc = stage / ".lccoding"
    archive_historical_evidence(stage)
    status = migrated_status(source_status, target_template)
    phase_status = migrated_phase_status(status, source_phase_status)
    write_json(lc / "status.json", status)
    write_json(lc / "PHASE-STATUS.json", phase_status)
    write_json(lc / REPORT_REFERENCE, MIGRATION_REPORT)
    if read_json(lc / REPORT_REFERENCE) != MIGRATION_REPORT:
        raise MigrationError("migration evidence record is not closed")
    if tuple(phase_status["phases"]) != TARGET_PHASES:
        raise MigrationError("target phase identity is not exact 2.8.0")


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


def migrate(source_argument, destination_argument):
    source, destination, destination_parent = resolve_paths(
        source_argument, destination_argument
    )
    source_status, source_phase_status, target_template = validate_source(source)
    stage = destination_parent / (
        f".{destination.name}.lccoding-migrate-{uuid.uuid4().hex}"
    )
    if stage.exists():
        raise MigrationError("migration stage already exists")
    try:
        shutil.copytree(source, stage, copy_function=shutil.copy2)
        transform(stage, source_status, source_phase_status, target_template)
        phase_validation = run_phase_validator(stage)
        if phase_validation.returncode:
            raise MigrationError("target phase view fails complete validation")
        project_validation = run_project_validator(stage)
        if project_validation.returncode:
            raise MigrationError("target project fails complete validation")
        stage.rename(destination)
    except Exception:
        safe_cleanup(stage, destination_parent, destination.name)
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Copy an exact LCCoding 2.7 project into a conservative 2.8 candidate."
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--output", required=True)
    arguments = parser.parse_args()
    try:
        migrate(arguments.project, arguments.output)
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
