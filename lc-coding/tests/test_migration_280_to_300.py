from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "MIGRATION-2.8.0-TO-3.0.0.md"
MIGRATOR = ROOT / "lc-coding/scripts/migrate_project_280_to_300.py"
PROJECT_VALIDATOR = ROOT / "lc-coding/scripts/validate_project.py"
PHASE_VALIDATOR = ROOT / "lc-coding/scripts/validate_phase_status.py"
TEMPLATES = ROOT / "lc-coding/templates"
REPORT_REFERENCE = "MIGRATION-2.8.0-TO-3.0.0.json"
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

    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=no_duplicates)


def snapshot(root):
    return {
        path.relative_to(root).as_posix(): (
            "directory" if path.is_dir() else "file",
            None if path.is_dir() else path.read_bytes(),
            path.stat().st_mtime_ns,
        )
        for path in root.rglob("*")
    }


def source_status():
    status = strict_json(TEMPLATES / "STATUS.json")
    assert status.pop("real_user_journey_acceptance")["state"] == "UNPROVED"
    status["status_schema_version"] = "2.8.0"
    assert status["phase_gates"].pop("REAL_USER_JOURNEY_ACCEPTED") == "PENDING"
    status["project_id"] = "migration-280-fixture"
    status["initialization_mode"] = "NEW"
    status["current_phase"] = "PRODUCT_FORMATION"
    status["phase_gates"]["INITIAL_READY"] = "PASS"
    status["proposal"] = "COMPLETE"
    status["initialization"] = "COMPLETE"
    return status


def source_phase_status():
    phase = strict_json(TEMPLATES / "PHASE-STATUS.json")
    phase["status_schema_version"] = "2.8.0"
    phase["current_phase"] = "PRODUCT_FORMATION"
    phase["phases"].pop("REAL_USER_JOURNEY_ACCEPTANCE")
    phase["phases"]["INITIAL"] = {"status": "COMPLETE", "exit_gate": "PASS"}
    phase["phases"]["PRODUCT_FORMATION"] = {
        "status": "ACTIVE",
        "exit_evidence": "PENDING",
    }
    return phase


def make_source(project):
    lc = project / ".lccoding"
    lc.mkdir(parents=True)
    for name in (
        "OWNER-POLICY.md",
        "PROJECT-PROFILE.md",
        "AGENT-RULE.md",
        "WORKFLOW-MAP.md",
        "UI-MAP.md",
        "SIMULATION-WORLD.md",
    ):
        (lc / name).write_bytes((TEMPLATES / name).read_bytes())
    manifest = strict_json(TEMPLATES / "CANONICAL-MANIFEST.json")
    manifest["lccoding"]["version"] = "2.8.0"
    write(lc / "CANONICAL-MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
    write(project / "VERSION", "1.0.0\n")
    write(
        lc / "PROJECT-START.json",
        json.dumps({"initialization_mode": "NEW", "repository": "github.com/example/migration"}) + "\n",
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
        json.dumps({"complexity": factors, "depth": {"rationale": "", "analysis": [], "materials": [], "evidence": []}}, indent=2) + "\n",
    )
    write(
        lc / "PROJECT-HEALTH.json",
        json.dumps({"record_role": "ASSESSMENT_EVIDENCE", "initialization_mode": "NEW"}, indent=2) + "\n",
    )
    write(lc / "status.json", json.dumps(source_status(), indent=2) + "\n")
    write(lc / "PHASE-STATUS.json", json.dumps(source_phase_status(), indent=2) + "\n")
    manifest_bytes = (lc / "CANONICAL-MANIFEST.json").read_bytes()
    lock = strict_json(TEMPLATES / "INTERPRETATION-LOCK.json")
    lock.update({
        "project_id": "migration-280-fixture",
        "issued_at": "2026-09-07T00:00:00Z",
        "agent_platform": "fixture",
        "manifest_hash": "sha256:" + hashlib.sha256(manifest_bytes).hexdigest(),
        "validated_execution_method_ids": [],
        "knowledge_test": "PASS",
        "execution_test": "PASS",
        "compatibility": "PASS",
        "status": "VALID",
    })
    write(lc / "INTERPRETATION-LOCK.json", json.dumps(lock, indent=2) + "\n")


def invoke(source, output, *extra):
    return run([
        sys.executable,
        str(MIGRATOR),
        "--project",
        str(source),
        "--output",
        str(output),
        *extra,
    ])


assert CONTRACT.is_file()
assert MIGRATOR.is_file()
contract = CONTRACT.read_text(encoding="utf-8")
for marker in (
    "Source status schema: 2.8.0",
    "Target status schema: 3.0.0",
    "COPY_ON_WRITE_EXTERNAL_TARGET",
    "ORIGINAL_2_8_INPUTS_BYTES_AND_MTIMES_UNCHANGED",
    "REAL_USER_JOURNEY_ACCEPTANCE",
    "EXPLICITLY_UNPROVED",
    "ATOMIC_TARGET_ABSENT_ON_FAILURE",
    "--reopen-delivery-preparation",
    "never changed",
):
    assert marker in contract, marker

spec = importlib.util.spec_from_file_location("migration_280_to_300", MIGRATOR)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
accepted = source_status()
accepted["current_phase"] = "REAL_PRODUCT_INTEGRATION"
accepted["phase_gates"]["ALL_REQUIRED_RUNS_ACCEPTED"] = "ALL_REQUIRED_RUNS_ACCEPTED"
migrated_accepted = module.migrated_status(accepted, strict_json(TEMPLATES / "STATUS.json"))
assert migrated_accepted["current_phase"] == "REAL_USER_JOURNEY_ACCEPTANCE"
assert migrated_accepted["phase_gates"]["REAL_USER_JOURNEY_ACCEPTED"] == "PENDING"
delivery = source_status()
delivery["current_phase"] = "DELIVERY_PREPARATION"
try:
    module.choose_target_phase(delivery)
    raise AssertionError("Delivery Preparation was silently reopened")
except module.MigrationError:
    pass
assert module.choose_target_phase(delivery, True) == "REAL_USER_JOURNEY_ACCEPTANCE"

with tempfile.TemporaryDirectory(prefix="lccoding-migration-300-") as temporary:
    base = Path(temporary)
    source = base / "source-280"
    make_source(source)
    source_result = run([sys.executable, str(PROJECT_VALIDATOR), str(source)])
    assert source_result.returncode == 0, source_result.stdout + source_result.stderr
    before = snapshot(source)
    output = base / "candidate-300"
    result = invoke(source, output)
    assert result.returncode == 0, result.stdout + result.stderr
    assert snapshot(source) == before
    assert run([sys.executable, str(PHASE_VALIDATOR), str(output / ".lccoding/PHASE-STATUS.json")]).returncode == 0
    target_result = run([sys.executable, str(PROJECT_VALIDATOR), str(output)])
    assert target_result.returncode == 0, target_result.stdout + target_result.stderr
    status = strict_json(output / ".lccoding/status.json")
    phase = strict_json(output / ".lccoding/PHASE-STATUS.json")
    assert status["status_schema_version"] == "3.0.0"
    assert status["current_phase"] == "PRODUCT_FORMATION"
    assert status["phase_gates"]["REAL_USER_JOURNEY_ACCEPTED"] == "PENDING"
    assert status["real_user_journey_acceptance"]["state"] == "UNPROVED"
    assert status["real_user_journey_acceptance"]["current_round"] == 0
    assert status["real_user_journey_acceptance"]["open_defect_ids"] == []
    assert tuple(phase["phases"]) == TARGET_PHASES
    assert phase["phases"]["REAL_USER_JOURNEY_ACCEPTANCE"]["status"] == "PENDING"
    assert (output / ".lccoding/history/2.8.0/status.json").is_file()
    assert (output / ".lccoding/history/2.8.0/PHASE-STATUS.json").is_file()
    assert strict_json(output / ".lccoding" / REPORT_REFERENCE)["journey_evidence_state"] == "UNPROVED"
    assert not list(base.glob(".candidate-300.lccoding-migrate-*"))

    overlap = source / "candidate"
    assert invoke(source, overlap).returncode != 0
    assert snapshot(source) == before
    duplicate = base / "duplicate-source"
    make_source(duplicate)
    status_path = duplicate / ".lccoding/status.json"
    text = status_path.read_text(encoding="utf-8").replace(
        '  "status_schema_version": "2.8.0",',
        '  "status_schema_version": "2.8.0",\n  "status_schema_version": "2.8.0",',
        1,
    )
    write(status_path, text)
    duplicate_before = snapshot(duplicate)
    duplicate_output = base / "duplicate-output"
    assert invoke(duplicate, duplicate_output).returncode != 0
    assert not duplicate_output.exists()
    assert snapshot(duplicate) == duplicate_before

print("PASS: 2.8 to 3.0 migration is copy-on-write, atomic, and journey conservative")
