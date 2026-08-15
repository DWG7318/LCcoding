from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
MIGRATION_CONTRACT = ROOT / "MIGRATION-2.7.0-TO-2.8.0.md"
MIGRATOR = ROOT / "lc-coding/scripts/migrate_project_270_to_280.py"
PROJECT_VALIDATOR = ROOT / "lc-coding/scripts/validate_project.py"
PHASE_VALIDATOR = ROOT / "lc-coding/scripts/validate_phase_status.py"
TEMPLATES = ROOT / "lc-coding/templates"

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
UNPROVED = {
    "agent_configuration_baseline": "UNPROVED",
    "agent_security_evidence": "UNPROVED",
    "operations_agent_integration": "UNPROVED",
    "product_operations_agent_isolation": "UNPROVED",
    "production_execution_topology": "UNPROVED",
    "runtime_adapter_attestation": "UNPROVED",
}
BLOCKERS = [
    "AGENT_CONFIGURATION_BASELINE_UNPROVED",
    "AGENT_SECURITY_EVIDENCE_UNPROVED",
    "OPERATIONS_AGENT_INTEGRATION_UNPROVED",
    "PRODUCT_OPERATIONS_AGENT_ISOLATION_UNPROVED",
    "PRODUCTION_EXECUTION_TOPOLOGY_UNPROVED",
    "RUNTIME_ADAPTER_ATTESTATION_UNPROVED",
]
REPORT_REFERENCE = "MIGRATION-2.7.0-TO-2.8.0.json"
AGENT_PRODUCT_FORMATION_FIELD = "agent_product_formation"
UNPROVED_AGENT_PRODUCT_FORMATION = {
    "state": "UNPROVED",
    "product_agent_applicability": "UNPROVED",
    "calabash_definition_handoff_id": "NOT_APPLICABLE",
    "calabash_definition_handoff_hash": "NOT_APPLICABLE",
    "configuration_baseline_id": "NOT_APPLICABLE",
    "configuration_baseline_hash": "NOT_APPLICABLE",
    "product_agent_capability_state": "UNPROVED",
    "operations_agent_state": "UNPROVED",
}

assert MIGRATION_CONTRACT.is_file(), "2.7.0 to 2.8.0 migration contract is absent"
assert MIGRATOR.is_file(), "2.7.0 to 2.8.0 migrator is absent"


def run(command):
    return subprocess.run(command, capture_output=True, text=True)


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def strict_json(path):
    def no_duplicates(pairs):
        value = {}
        for key, item in pairs:
            assert key not in value, f"duplicate JSON field: {key}"
            value[key] = item
        return value

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicates)


def snapshot(root):
    return {
        path.relative_to(root).as_posix(): (
            "directory" if path.is_dir() else "file",
            None if path.is_dir() else path.read_bytes(),
            path.stat().st_mtime_ns,
        )
        for path in root.rglob("*")
    }


def source_phase_status():
    record = strict_json(TEMPLATES / "PHASE-STATUS.json")
    record["status_schema_version"] = "2.7.0"
    record["current_phase"] = "PRODUCT_FORMATION"
    phase3 = record["phases"].pop("REAL_PRODUCT_INTEGRATION")
    record["phases"] = {
        "INITIAL": {"status": "COMPLETE", "exit_gate": "PASS"},
        "PRODUCT_FORMATION": {"status": "ACTIVE", "exit_evidence": "PENDING"},
        "ENGINEERING_RUNS": phase3,
        "DELIVERY_PREPARATION": record["phases"]["DELIVERY_PREPARATION"],
    }
    return record


def make_source(project):
    lc = project / ".lccoding"
    lc.mkdir(parents=True)
    for name in (
        "OWNER-POLICY.md",
        "PROJECT-PROFILE.md",
        "AGENT-RULE.md",
        "CANONICAL-MANIFEST.json",
        "WORKFLOW-MAP.md",
        "UI-MAP.md",
        "SIMULATION-WORLD.md",
    ):
        (lc / name).write_bytes((TEMPLATES / name).read_bytes())
    write(project / "VERSION", "1.0.0\n")
    write(
        lc / "PROJECT-START.json",
        json.dumps(
            {"initialization_mode": "NEW", "repository": "github.com/example/migration"}
        )
        + "\n",
    )
    factors = {
        name: "LOW"
        for name in (
            "product_uncertainty",
            "system_coupling",
            "real_risk",
            "irreversibility",
            "novelty",
        )
    }
    write(
        lc / "PROJECT-FINGERPRINT.json",
        json.dumps(
            {
                "complexity": factors,
                "depth": {"rationale": "", "analysis": [], "materials": [], "evidence": []},
            },
            indent=2,
        )
        + "\n",
    )
    write(
        lc / "PROJECT-HEALTH.json",
        json.dumps(
            {"record_role": "ASSESSMENT_EVIDENCE", "initialization_mode": "NEW"},
            indent=2,
        )
        + "\n",
    )
    status = strict_json(TEMPLATES / "STATUS.json")
    assert status.pop(AGENT_PRODUCT_FORMATION_FIELD) == UNPROVED_AGENT_PRODUCT_FORMATION
    status["status_schema_version"] = "2.7.0"
    status["project_id"] = "migration-270-fixture"
    status["initialization_mode"] = "NEW"
    status["current_phase"] = "PRODUCT_FORMATION"
    status["phase_gates"]["INITIAL_READY"] = "PASS"
    status["proposal"] = "COMPLETE"
    status["initialization"] = "COMPLETE"
    write(lc / "status.json", json.dumps(status, indent=2) + "\n")
    write(lc / "PHASE-STATUS.json", json.dumps(source_phase_status(), indent=2) + "\n")

    manifest_bytes = (lc / "CANONICAL-MANIFEST.json").read_bytes()
    lock = strict_json(TEMPLATES / "INTERPRETATION-LOCK.json")
    lock.update(
        {
            "project_id": "migration-270-fixture",
            "issued_at": "2026-08-15T00:00:00Z",
            "agent_platform": "fixture",
            "manifest_hash": "sha256:" + hashlib.sha256(manifest_bytes).hexdigest(),
            "validated_execution_method_ids": [],
            "knowledge_test": "PASS",
            "execution_test": "PASS",
            "compatibility": "PASS",
            "status": "VALID",
        }
    )
    write(lc / "INTERPRETATION-LOCK.json", json.dumps(lock, indent=2) + "\n")

    historical = {
        "runs/RUN-270/evidence.receipt": b"run evidence for 2.7\x00\n",
        "reviews/OA-270.receipt": b"owner acceptance for 2.7\n",
    }
    for relative, payload in historical.items():
        path = lc / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    return historical


def invoke(source, output):
    return run(
        [sys.executable, str(MIGRATOR), "--project", str(source), "--output", str(output)]
    )


def assert_valid_project(project):
    phase_result = run(
        [sys.executable, str(PHASE_VALIDATOR), str(project / ".lccoding/PHASE-STATUS.json")]
    )
    assert phase_result.returncode == 0, phase_result.stdout + phase_result.stderr
    project_result = run([sys.executable, str(PROJECT_VALIDATOR), str(project)])
    assert project_result.returncode == 0, project_result.stdout + project_result.stderr


def assert_failed_without_publish(source, output, before):
    result = invoke(source, output)
    assert result.returncode != 0, result.stdout + result.stderr
    assert not output.exists()
    assert snapshot(source) == before
    assert not list(output.parent.glob(f".{output.name}.lccoding-migrate-*"))


contract = MIGRATION_CONTRACT.read_text(encoding="utf-8")
for marker in (
    "Source status schema: 2.7.0",
    "Target status schema: 2.8.0",
    "Candidate construction: COPY_ON_WRITE_EXTERNAL_TARGET",
    "Source preservation: ORIGINAL_2_7_INPUTS_BYTES_AND_MTIMES_UNCHANGED",
    "Existing receipt treatment: HISTORICAL_ONLY_NOT_CURRENT",
    "Required 2.8 evidence state: EXPLICITLY_UNPROVED",
    "Rollback treatment: ATOMIC_TARGET_ABSENT_ON_FAILURE",
    "BI modification in this migration: NONE",
    "Global Skill deployment: NOT_PERFORMED",
    "Current release change: NONE",
    "ENGINEERING_RUNS",
    "REAL_PRODUCT_INTEGRATION",
    "SELECT / COMPOSE / FEDERATE / RETIRE",
):
    assert marker in contract, marker
for forbidden_claim in (
    "Current release change: 2.8.0",
    "Global Skill deployment: COMPLETE",
    "BI modification in this migration: COMPLETE",
):
    assert forbidden_claim not in contract

changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
assert changelog.startswith("# Changelog\n\n## Unreleased - 2.8.0 candidate\n")
candidate_section = changelog.split("\n## 2.7.0", 1)[0]
for marker in (
    "copy-on-write",
    "does not change VERSION",
    "does not change the current BI release",
    "does not deploy the global Skill",
):
    assert marker in candidate_section
assert "2.8.0 has been released" not in candidate_section

with tempfile.TemporaryDirectory(prefix="lccoding-migration-280-") as temporary:
    base = Path(temporary)
    source = base / "source-270"
    historical = make_source(source)
    assert_valid_project(source)
    before = snapshot(source)
    output = base / "candidate-280"
    assert not output.exists()
    result = invoke(source, output)
    assert result.returncode == 0, result.stdout + result.stderr
    assert snapshot(source) == before
    assert_valid_project(output)

    status = strict_json(output / ".lccoding/status.json")
    phase_status = strict_json(output / ".lccoding/PHASE-STATUS.json")
    report = strict_json(output / ".lccoding" / REPORT_REFERENCE)
    assert status["status_schema_version"] == "2.8.0"
    assert status["current_phase"] == "PRODUCT_FORMATION"
    assert status["product_baseline"] == "PENDING"
    assert status["active_slice"] is None and status["integration_baseline"] is None
    assert status["active_runs"] == [] and status["loop_owner_acceptances"] == []
    assert status["open_owner_gaps"] == []
    assert status["phase_gates"]["ALL_REQUIRED_RUNS_ACCEPTED"] == "PENDING"
    assert status["phase_gates"]["DELIVERY_READY"] == "PENDING"
    assert status["all_required_runs_accepted"] == "PENDING"
    assert status["centralized_security_audit"] == "PENDING"
    assert status["security_remediation"] == "PENDING"
    assert status["vulnerability_closure"]["state"] == "PENDING"
    assert status["post_security_owner_acceptance"]["state"] == "PENDING"
    assert status["delivery_method_qa"] == "PENDING" and status["delivery"] == "PENDING"
    assert status["next_action"] == "PROVE_2_8_AGENT_NATIVE_REQUIREMENTS"
    assert status["evidence_pointers"] == [REPORT_REFERENCE]
    assert status["blockers"] == BLOCKERS
    assert status[AGENT_PRODUCT_FORMATION_FIELD] == UNPROVED_AGENT_PRODUCT_FORMATION

    assert phase_status["status_schema_version"] == "2.8.0"
    assert tuple(phase_status["phases"]) == TARGET_PHASES
    assert "ENGINEERING_RUNS" not in phase_status["phases"]
    assert phase_status["phases"]["REAL_PRODUCT_INTEGRATION"] == {
        "status": "PENDING",
        "per_run_acceptances": [],
        "aggregate_exit_gate": "PENDING",
    }
    assert report == {
        "artifact_role": "LCCODING_2_8_MIGRATION_EVIDENCE",
        "source_status_schema": "2.7.0",
        "target_status_schema": "2.8.0",
        "phase_identity": {
            "source": "ENGINEERING_RUNS",
            "target": "REAL_PRODUCT_INTEGRATION",
            "result": "MAPPED_WITHOUT_COMPLETION",
        },
        "required_evidence": UNPROVED,
        "topology_dispositions": ["SELECT", "COMPOSE", "FEDERATE", "RETIRE"],
        "historical_evidence": {
            "root": ".lccoding/history/2.7.0",
            "treatment": "HISTORICAL_ONLY_NOT_CURRENT",
        },
        "new_lifecycle_gates": [],
        "new_lifecycle_steps": [],
        "result": "MIGRATED_CANDIDATE_REQUIRES_REPROOF",
    }
    for relative, payload in historical.items():
        archived = output / ".lccoding/history/2.7.0" / relative
        assert archived.read_bytes() == payload
        assert not (output / ".lccoding" / relative).exists()
    assert not list(output.parent.glob(f".{output.name}.lccoding-migrate-*"))

    overlap = source / "candidate"
    assert_failed_without_publish(source, overlap, before)
    same_path = invoke(source, source)
    assert same_path.returncode != 0
    assert snapshot(source) == before

    existing = base / "existing-target"
    existing.mkdir()
    result = invoke(source, existing)
    assert result.returncode != 0
    assert snapshot(source) == before

    generated_parent = base / "node_modules"
    generated_source = generated_parent / "source"
    make_source(generated_source)
    generated_before = snapshot(generated_source)
    assert_failed_without_publish(generated_source, base / "generated-output", generated_before)

    generated_content = base / "generated-content-source"
    make_source(generated_content)
    write(generated_content / "dist/generated.js", "generated\n")
    generated_content_before = snapshot(generated_content)
    assert_failed_without_publish(
        generated_content, base / "generated-content-output", generated_content_before
    )

    hybrid = base / "hybrid-source"
    make_source(hybrid)
    hybrid_phase_path = hybrid / ".lccoding/PHASE-STATUS.json"
    hybrid_phase = strict_json(hybrid_phase_path)
    hybrid_phase["phases"]["REAL_PRODUCT_INTEGRATION"] = copy.deepcopy(
        hybrid_phase["phases"]["ENGINEERING_RUNS"]
    )
    write(hybrid_phase_path, json.dumps(hybrid_phase, indent=2) + "\n")
    hybrid_before = snapshot(hybrid)
    assert_failed_without_publish(hybrid, base / "hybrid-output", hybrid_before)

    wrong_identity = base / "wrong-identity-source"
    make_source(wrong_identity)
    wrong_status_path = wrong_identity / ".lccoding/status.json"
    wrong_status = strict_json(wrong_status_path)
    wrong_status["current_phase"] = "REAL_PRODUCT_INTEGRATION"
    write(wrong_status_path, json.dumps(wrong_status, indent=2) + "\n")
    wrong_before = snapshot(wrong_identity)
    assert_failed_without_publish(wrong_identity, base / "wrong-output", wrong_before)

    hybrid_agent = base / "hybrid-agent-source"
    make_source(hybrid_agent)
    hybrid_agent_status_path = hybrid_agent / ".lccoding/status.json"
    hybrid_agent_status = strict_json(hybrid_agent_status_path)
    hybrid_agent_status[AGENT_PRODUCT_FORMATION_FIELD] = copy.deepcopy(
        UNPROVED_AGENT_PRODUCT_FORMATION
    )
    write(hybrid_agent_status_path, json.dumps(hybrid_agent_status, indent=2) + "\n")
    hybrid_agent_before = snapshot(hybrid_agent)
    assert_failed_without_publish(
        hybrid_agent, base / "hybrid-agent-output", hybrid_agent_before
    )

    unknown_source = base / "unknown-status-source"
    make_source(unknown_source)
    unknown_status_path = unknown_source / ".lccoding/status.json"
    unknown_status = strict_json(unknown_status_path)
    unknown_status["unknown_2_8_field"] = "UNPROVED"
    write(unknown_status_path, json.dumps(unknown_status, indent=2) + "\n")
    unknown_before = snapshot(unknown_source)
    assert_failed_without_publish(
        unknown_source, base / "unknown-status-output", unknown_before
    )

    duplicate = base / "duplicate-source"
    make_source(duplicate)
    duplicate_status_path = duplicate / ".lccoding/status.json"
    duplicate_text = duplicate_status_path.read_text(encoding="utf-8")
    duplicate_text = duplicate_text.replace(
        '  "status_schema_version": "2.7.0",',
        '  "status_schema_version": "2.7.0",\n  "status_schema_version": "2.7.0",',
        1,
    )
    write(duplicate_status_path, duplicate_text)
    duplicate_before = snapshot(duplicate)
    assert_failed_without_publish(duplicate, base / "duplicate-output", duplicate_before)

    atomic_source = base / "atomic-source"
    make_source(atomic_source)
    atomic_before = snapshot(atomic_source)
    atomic_output = base / "atomic-output"
    module_spec = importlib.util.spec_from_file_location("migration_270_to_280", MIGRATOR)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    original_validator = module.run_project_validator
    calls = [0]

    def fail_final_validation(project):
        calls[0] += 1
        if calls[0] == 1:
            return original_validator(project)
        return subprocess.CompletedProcess([], 1, "FAIL\n", "")

    module.run_project_validator = fail_final_validation
    try:
        try:
            module.migrate(atomic_source, atomic_output)
            raise AssertionError("failed final validation published a target")
        except module.MigrationError:
            pass
    finally:
        module.run_project_validator = original_validator
    assert not atomic_output.exists()
    assert snapshot(atomic_source) == atomic_before
    assert not list(base.glob(".atomic-output.lccoding-migrate-*"))

print("PASS: 2.7 to 2.8 migration is copy-on-write, atomic, and evidence conservative")
