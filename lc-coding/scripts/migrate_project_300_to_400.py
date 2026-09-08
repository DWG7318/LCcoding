#!/usr/bin/env python3
from pathlib import Path
import argparse
import copy
import hashlib
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
ROUTE_MAP_TEMPLATE_PATH = SCRIPT_DIR.parent / "templates/SERVICE-ROUTE-MAP.json"
PHASE_SPEC = importlib.util.spec_from_file_location(
    "lccoding_migration_400_phase_validation", PHASE_VALIDATOR_PATH
)
PHASE_VALIDATOR = importlib.util.module_from_spec(PHASE_SPEC)
PHASE_SPEC.loader.exec_module(PHASE_VALIDATOR)

SOURCE_SCHEMA = "3.0.0"
TARGET_SCHEMA = "4.0.0"
PHASES = (
    "INITIAL",
    "PRODUCT_FORMATION",
    "REAL_PRODUCT_INTEGRATION",
    "REAL_USER_JOURNEY_ACCEPTANCE",
    "DELIVERY_PREPARATION",
)
GATES = (
    "INITIAL_READY",
    "CALABASH_UPGRADE_READY",
    "ALL_REQUIRED_RUNS_ACCEPTED",
    "REAL_USER_JOURNEY_ACCEPTED",
    "DELIVERY_READY",
)
SUMMARY_FIELDS = {
    "lccoding_applicability",
    "product_service_strategy",
    "service_route_map",
}
GENERATED_COMPONENTS = {
    "gen",
    "node_modules",
    "dist",
    "target",
    "test-results",
    "playwright-report",
}
HISTORY_ROOT = Path("history/3.0.0")
REPORT_REFERENCE = "MIGRATION-3.0.0-TO-4.0.0.json"
ROUTE_REFORMATION_BLOCKER = "SERVICE_ROUTE_MAP_4_0_REQUIRES_ADOPTION"
JOURNEY_REVALIDATION_BLOCKER = "REAL_USER_JOURNEY_ACCEPTANCE_4_0_UNPROVED"
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


def direct_browser_accepted(status):
    summary = status.get("real_user_journey_acceptance")
    return (
        isinstance(summary, dict)
        and summary.get("state") == "REAL_USER_JOURNEY_ACCEPTED"
        and status.get("phase_gates", {}).get("REAL_USER_JOURNEY_ACCEPTED")
        == "REAL_USER_JOURNEY_ACCEPTED"
        and summary.get("complete_round_count", 0) > 0
        and summary.get("passed_journey_count", 0) > 0
    )


def route_reformation_required(status):
    current = status.get("current_phase")
    return PHASE_VALIDATOR.completed_evidence(status.get("product_baseline")) or (
        current in PHASES and PHASES.index(current) > PHASES.index("PRODUCT_FORMATION")
    )


def validate_source(source):
    lc = source / ".lccoding"
    status_path = lc / "status.json"
    phase_path = lc / "PHASE-STATUS.json"
    if not status_path.is_file() or not phase_path.is_file():
        raise MigrationError("source lacks authoritative status records")
    status = read_json(status_path)
    phase_status = read_json(phase_path)
    template = read_json(STATUS_TEMPLATE_PATH)
    route_template = read_json(ROUTE_MAP_TEMPLATE_PATH)
    if template.get("status_schema_version") not in {SOURCE_SCHEMA, TARGET_SCHEMA}:
        raise MigrationError("installed status template cannot derive the exact 3.0 shape")
    if route_template.get("service_topology_schema_version") != TARGET_SCHEMA:
        raise MigrationError("installed Service Route Map template is not exact 4.0.0")
    source_fields = set(template) - SUMMARY_FIELDS
    if set(status) != source_fields or SUMMARY_FIELDS.intersection(status):
        raise MigrationError("source status does not use the closed 3.0 status shape")
    if status.get("record_role") != "AUTHORITATIVE_PROJECT_STATUS":
        raise MigrationError("source status is not authoritative")
    if status.get("status_schema_version") != SOURCE_SCHEMA:
        raise MigrationError("source status schema must be exact 3.0.0")
    if status.get("current_phase") not in PHASES:
        raise MigrationError("source current phase is not a 3.0 phase identity")
    if tuple(status.get("phase_gates", {})) != GATES:
        raise MigrationError("source phase gate set is not closed")
    if phase_status.get("status_schema_version") != SOURCE_SCHEMA:
        raise MigrationError("source derived phase schema must be exact 3.0.0")
    if phase_status.get("record_role") != "DERIVED_VIEW" or phase_status.get(
        "derived_from"
    ) != "status.json":
        raise MigrationError("source phase view is not derived from status.json")
    if phase_status.get("current_phase") != status.get("current_phase"):
        raise MigrationError("source status and phase view disagree")
    if tuple(phase_status.get("phases", {})) != PHASES:
        raise MigrationError("source phase identity is mixed, inferred, or unknown")
    if (lc / HISTORY_ROOT).exists():
        raise MigrationError("source already contains a 3.0 migration history target")
    validation = run_project_validator(source)
    if validation.returncode:
        raise MigrationError("source fails complete project validation")
    return status, phase_status, template, route_template


def _deduplicated(values):
    return list(dict.fromkeys(values))


def migrated_status(source, template):
    status = copy.deepcopy(source)
    accepted_direct = direct_browser_accepted(source)
    reform = route_reformation_required(source)
    status["status_schema_version"] = TARGET_SCHEMA
    status.update(
        {
            "lccoding_applicability": (
                "WHOLE_PRODUCT_FIT" if accepted_direct else "PENDING"
            ),
            "product_service_strategy": (
                "PLATFORM_COMPLETION" if accepted_direct else "PENDING"
            ),
            "service_route_map": "DRAFT" if accepted_direct else "PENDING",
        }
    )
    status["evidence_pointers"] = _deduplicated(
        [*source.get("evidence_pointers", []), REPORT_REFERENCE]
    )
    if reform:
        status["current_phase"] = "PRODUCT_FORMATION"
        status["phase_gates"] = {
            gate: (
                copy.deepcopy(source["phase_gates"][gate])
                if gate == "INITIAL_READY"
                else "PENDING"
            )
            for gate in GATES
        }
        status["product_baseline"] = "PENDING"
        status["agent_product_formation"] = copy.deepcopy(
            template["agent_product_formation"]
        )
        status["agent_slice_integration"] = copy.deepcopy(
            template["agent_slice_integration"]
        )
        status["active_slice"] = None
        status["integration_baseline"] = None
        status["active_runs"] = []
        status["loop_owner_acceptances"] = []
        status["open_owner_gaps"] = []
        status["all_required_runs_accepted"] = "PENDING"
        status["real_user_journey_acceptance"] = copy.deepcopy(
            template["real_user_journey_acceptance"]
        )
        status["centralized_security_audit"] = "PENDING"
        status["security_remediation"] = "PENDING"
        status["vulnerability_closure"] = copy.deepcopy(template["vulnerability_closure"])
        status["post_security_owner_acceptance"] = copy.deepcopy(
            template["post_security_owner_acceptance"]
        )
        status["delivery_method_qa"] = "PENDING"
        status["delivery"] = "PENDING"
        status["last_material_change"] = ""
        status["next_action"] = (
            "ADOPT_4_0_SERVICE_ROUTE_MAP"
            if accepted_direct
            else "ASSESS_4_0_APPLICABILITY_AND_SERVICE_ROUTES"
        )
        blockers = [*source.get("blockers", []), ROUTE_REFORMATION_BLOCKER]
        if accepted_direct:
            blockers.append(JOURNEY_REVALIDATION_BLOCKER)
        status["blockers"] = _deduplicated(blockers)
    expected = (set(template) - SUMMARY_FIELDS) | SUMMARY_FIELDS
    if set(status) != expected:
        raise MigrationError("target status does not use the closed 4.0 status shape")
    return status


def migrated_phase_status(status, source_phase_status, reform):
    if reform:
        initial = copy.deepcopy(source_phase_status["phases"]["INITIAL"])
        phases = {
            "INITIAL": initial,
            "PRODUCT_FORMATION": {"status": "ACTIVE", "exit_evidence": "PENDING"},
            "REAL_PRODUCT_INTEGRATION": {
                "status": "PENDING",
                "per_run_acceptances": [],
                "aggregate_exit_gate": "PENDING",
            },
            "REAL_USER_JOURNEY_ACCEPTANCE": {
                "status": "PENDING",
                "acceptance_record": "NOT_APPLICABLE",
                "defect_log": "NOT_APPLICABLE",
                "complete_rounds": 0,
                "exit_gate": "PENDING",
            },
            "DELIVERY_PREPARATION": {"status": "PENDING", "exit_gate": "PENDING"},
        }
    else:
        phases = copy.deepcopy(source_phase_status["phases"])
    return {
        "record_role": "DERIVED_VIEW",
        "status_schema_version": TARGET_SCHEMA,
        "derived_from": "status.json",
        "current_phase": status["current_phase"],
        "phases": phases,
        "updated_at": source_phase_status.get("updated_at", ""),
        "evidence": _deduplicated(
            [*source_phase_status.get("evidence", []), REPORT_REFERENCE]
        ),
        "blockers": _deduplicated(
            [*source_phase_status.get("blockers", []), *status.get("blockers", [])]
        ),
    }


def migrated_route_map(status, route_template):
    if status["service_route_map"] == "PENDING":
        return copy.deepcopy(route_template)
    project_id = status.get("project_id", "")
    map_suffix = hashlib.sha256(project_id.encode("utf-8")).hexdigest()[:16].upper()
    return {
        "record_role": "CALABASH_SERVICE_ROUTE_MAP",
        "service_topology_schema_version": TARGET_SCHEMA,
        "map_id": "SERVICE-ROUTES-MIGRATED-" + map_suffix,
        "project_id": project_id,
        "state": "DRAFT",
        "primary_strategy": "PLATFORM_COMPLETION",
        "required_coexisting_strategies": [],
        "service_center_applicability": "NOT_APPLICABLE",
        "journeys": [
            {
                "journey_id": "JOURNEY-MIGRATED-DIRECT",
                "journey_class": "CORE",
                "delivery_state": "PLANNED",
                "business_capability_id": "CAPABILITY-MIGRATED-DIRECT",
                "shared_capability_implementation_id": "WORKFLOW-MIGRATED-DIRECT",
                "routes": [
                    {
                        "route_id": "ROUTE-MIGRATED-DIRECT",
                        "route_kind": "DIRECT_PRODUCT",
                        "support_state": "REQUIRED",
                        "delivery_state": "UNPROVED",
                        "human_beneficiary_id": "HUMAN-PRINCIPAL-MIGRATED",
                        "actor_id": "HUMAN-PRINCIPAL-MIGRATED",
                        "actor_kind": "HUMAN_PRINCIPAL",
                        "capability_id": "CAPABILITY-MIGRATED-DIRECT",
                        "capability_implementation_id": "WORKFLOW-MIGRATED-DIRECT",
                        "promised_entry": "existing direct-product browser entry pending Calabash refinement",
                        "human_observable_outcome": "existing browser outcome pending route-faithful 4.0 revalidation",
                        "authority": {
                            "action_id": "ACTION-MIGRATED-DIRECT",
                            "resource_id": "RESOURCE-MIGRATED-DIRECT",
                            "delegation_basis_id": "NOT_APPLICABLE",
                        },
                        "consent": {
                            "requirement": "NOT_REQUIRED",
                            "policy_id": "POLICY-MIGRATED-DIRECT",
                        },
                        "adapter_or_surface_id": "DIRECT-PRODUCT-SURFACE-MIGRATED",
                        "acceptance_evidence_ids": [
                            "LEGACY-BROWSER-EVIDENCE-HISTORICAL"
                        ],
                        "audit_event_ids": [],
                    }
                ],
            }
        ],
    }


def migration_report(accepted_direct, reform):
    return {
        "artifact_role": "LCCODING_4_0_MIGRATION_EVIDENCE",
        "source_status_schema": SOURCE_SCHEMA,
        "target_status_schema": TARGET_SCHEMA,
        "applicability": "WHOLE_PRODUCT_FIT" if accepted_direct else "PENDING",
        "product_service_strategy": (
            "PLATFORM_COMPLETION" if accepted_direct else "PENDING"
        ),
        "service_route_map_state": "DRAFT" if accepted_direct else "PENDING",
        "direct_product_delivery": "UNPROVED_4_0",
        "personal_agent_delivery": "NOT_CLAIMED",
        "service_center_delivery": "NOT_CLAIMED",
        "legacy_phase4_treatment": (
            "HISTORICAL_PRESERVED_REVALIDATION_REQUIRED"
            if accepted_direct
            else "NO_ACCEPTED_PHASE4_EVIDENCE"
        ),
        "product_formation_reopened": reform,
        "historical_evidence": {
            "root": ".lccoding/history/3.0.0",
            "treatment": "HISTORICAL_ONLY_NOT_4_0_ROUTE_PROOF",
        },
        "result": "MIGRATED_CANDIDATE_REQUIRES_4_0_ROUTE_ADOPTION",
    }


def transform(stage, source_status, source_phase_status, template, route_template):
    lc = stage / ".lccoding"
    history = lc / HISTORY_ROOT
    history.mkdir(parents=True)
    shutil.copy2(lc / "status.json", history / "status.json")
    shutil.copy2(lc / "PHASE-STATUS.json", history / "PHASE-STATUS.json")
    accepted_direct = direct_browser_accepted(source_status)
    reform = route_reformation_required(source_status)
    status = migrated_status(source_status, template)
    phase_status = migrated_phase_status(status, source_phase_status, reform)
    route_map = migrated_route_map(status, route_template)
    write_json(lc / "status.json", status)
    write_json(lc / "PHASE-STATUS.json", phase_status)
    write_json(lc / "SERVICE-ROUTE-MAP.json", route_map)
    write_json(lc / REPORT_REFERENCE, migration_report(accepted_direct, reform))
    if tuple(phase_status["phases"]) != PHASES:
        raise MigrationError("target phase identity is not exact 4.0.0")


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


def run_git(repository, *arguments):
    result = git_result(repository, *arguments)
    if result.returncode:
        raise MigrationError("independent Git materialization failed")
    return result.stdout.strip()


def git_result(repository, *arguments):
    return subprocess.run(
        ["git", "--no-optional-locks", *arguments],
        cwd=repository,
        capture_output=True,
        text=True,
    )


def absolute_git_path(repository, *arguments):
    value = Path(run_git(repository, *arguments))
    if not value.is_absolute():
        value = Path(repository) / value
    return value.resolve(strict=True)


def reject_shared_git_objects(source_common, target_common):
    source_objects = source_common / "objects"
    target_objects = target_common / "objects"
    if not source_objects.is_dir() or not target_objects.is_dir():
        raise MigrationError("independent Git object storage cannot be proved")
    for target_object in target_objects.rglob("*"):
        if not target_object.is_file() or target_object.is_symlink():
            continue
        relative = target_object.relative_to(target_objects)
        source_object = source_objects / relative
        if not source_object.is_file() or source_object.is_symlink():
            continue
        try:
            shared = os.path.samefile(source_object, target_object)
        except OSError as error:
            raise MigrationError("independent Git object storage cannot be proved") from error
        if shared:
            raise MigrationError("target Git object storage shares source hardlinks")


def verify_independent_git(source, target):
    source_admin = absolute_git_path(source, "rev-parse", "--absolute-git-dir")
    source_common = absolute_git_path(source, "rev-parse", "--git-common-dir")
    target_admin = absolute_git_path(target, "rev-parse", "--absolute-git-dir")
    target_common = absolute_git_path(target, "rev-parse", "--git-common-dir")
    expected_admin = (target / ".git").resolve(strict=True)
    if not expected_admin.is_dir() or target_admin != expected_admin or target_common != expected_admin:
        raise MigrationError("target Git metadata is not an independent repository")
    if target_admin in {source_admin, source_common} or target_common in {
        source_admin,
        source_common,
    }:
        raise MigrationError("target Git metadata still points at the source repository")
    alternates = target_common / "objects/info/alternates"
    if alternates.exists():
        try:
            if alternates.read_bytes().strip():
                raise MigrationError("target Git object storage uses source alternates")
        except OSError as error:
            raise MigrationError("independent Git alternates state cannot be proved") from error
    reject_shared_git_objects(source_common, target_common)


def remove_checkout_except_git(stage):
    for child in stage.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()


def overlay_source_tree(source, stage):
    def ignore_root_git(directory, names):
        if Path(directory).resolve() == source:
            return {".git"}.intersection(names)
        return set()

    shutil.copytree(
        source,
        stage,
        dirs_exist_ok=True,
        copy_function=shutil.copy2,
        ignore=ignore_root_git,
    )


def materialize_source(source, stage):
    git_marker = source / ".git"
    if not git_marker.exists():
        shutil.copytree(source, stage, copy_function=shutil.copy2)
        return
    inside_work_tree = git_result(source, "rev-parse", "--is-inside-work-tree")
    if inside_work_tree.returncode or inside_work_tree.stdout.strip() != "true":
        raise MigrationError("independent Git materialization failed")
    source_head = git_result(source, "rev-parse", "--verify", "HEAD")
    source_origin = git_result(source, "config", "--get", "remote.origin.url")
    if source_head.returncode:
        source_branch = git_result(
            source, "symbolic-ref", "--quiet", "--short", "HEAD"
        )
        if source_branch.returncode or not source_branch.stdout.strip():
            raise MigrationError("independent Git materialization failed")
        source_refs = run_git(
            source, "for-each-ref", "--format=%(refname) %(objectname)"
        )
        stage.mkdir()
        mirrored = subprocess.run(
            [
                "git",
                "clone",
                "--quiet",
                "--mirror",
                "--no-local",
                "--no-hardlinks",
                str(source),
                str(stage / ".git"),
            ],
            cwd=stage.parent,
            capture_output=True,
            text=True,
        )
        if mirrored.returncode:
            raise MigrationError("independent Git materialization failed")
        run_git(stage, "config", "core.bare", "false")
        remote_cleanup = git_result(stage, "config", "--remove-section", "remote.origin")
        if remote_cleanup.returncode not in {0, 5}:
            raise MigrationError("independent Git materialization failed")
        if source_origin.returncode == 0 and source_origin.stdout.strip():
            run_git(stage, "config", "remote.origin.url", source_origin.stdout.strip())
            run_git(
                stage,
                "config",
                "remote.origin.fetch",
                "+refs/heads/*:refs/remotes/origin/*",
            )
        overlay_source_tree(source, stage)
        verify_independent_git(source, stage)
        if git_result(stage, "rev-parse", "--verify", "HEAD").returncode == 0:
            raise MigrationError("unborn Git materialization invented a commit")
        if run_git(stage, "symbolic-ref", "--quiet", "--short", "HEAD") != (
            source_branch.stdout.strip()
        ):
            raise MigrationError("unborn Git branch identity was not preserved")
        if run_git(stage, "for-each-ref", "--format=%(refname) %(objectname)") != (
            source_refs
        ):
            raise MigrationError("unborn Git history or refs were not preserved")
        return
    clone = subprocess.run(
        [
            "git",
            "clone",
            "--quiet",
            "--no-checkout",
            "--no-local",
            "--no-hardlinks",
            str(source),
            str(stage),
        ],
        capture_output=True,
        text=True,
    )
    if clone.returncode:
        raise MigrationError("independent Git materialization failed")
    run_git(stage, "checkout", "--quiet", "--detach", source_head.stdout.strip())
    if source_origin.returncode == 0 and source_origin.stdout.strip():
        run_git(stage, "remote", "set-url", "origin", source_origin.stdout.strip())
    else:
        run_git(stage, "remote", "remove", "origin")
    remove_checkout_except_git(stage)
    overlay_source_tree(source, stage)
    verify_independent_git(source, stage)


def migrate(source_argument, destination_argument):
    source, destination, destination_parent = resolve_paths(
        source_argument, destination_argument
    )
    source_status, source_phase_status, template, route_template = validate_source(source)
    stage = destination_parent / f".{destination.name}.lccoding-migrate-{uuid.uuid4().hex}"
    try:
        materialize_source(source, stage)
        transform(stage, source_status, source_phase_status, template, route_template)
        phase_validation = run_phase_validator(stage)
        if phase_validation.returncode:
            raise MigrationError(
                "target phase view fails complete validation: "
                + phase_validation.stdout.strip()
            )
        target_validation = run_project_validator(stage)
        if target_validation.returncode:
            raise MigrationError(
                "target project fails complete validation: "
                + target_validation.stdout.strip()
            )
        stage.rename(destination)
    except Exception:
        safe_cleanup(stage, destination_parent, destination.name)
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Copy an exact LCCoding 3.0 project into a conservative 4.0 candidate."
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
