from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "MIGRATION-3.0.0-TO-4.0.0.md"
MIGRATOR = ROOT / "lc-coding/scripts/migrate_project_300_to_400.py"
PROJECT_VALIDATOR = ROOT / "lc-coding/scripts/validate_project.py"
PHASE_VALIDATOR = ROOT / "lc-coding/scripts/validate_phase_status.py"
TEMPLATES = ROOT / "lc-coding/templates"
REPORT_REFERENCE = "MIGRATION-3.0.0-TO-4.0.0.json"
HISTORY_ROOT = Path("history/3.0.0")
HASH = "1" * 64


def run(command, *, cwd=None):
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True)


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

    return json.loads(
        Path(path).read_text(encoding="utf-8"), object_pairs_hook=no_duplicates
    )


def snapshot(root):
    return {
        path.relative_to(root).as_posix(): (
            "directory" if path.is_dir() else "file",
            None if path.is_dir() else path.read_bytes(),
            path.stat().st_mtime_ns,
        )
        for path in root.rglob("*")
    }


def table(columns, rows):
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    lines.extend(
        "| " + " | ".join(str(row[column]) for column in columns) + " |"
        for row in rows
    )
    return "\n".join(lines)


WORKFLOW_COLUMNS = (
    "Workflow ID", "Classification (CORE/EXTRA)", "Implementation status",
    "Classification authority", "Subtree path", "Component version", "Content hash",
    "Workflow Capability ID", "Actors", "Trigger", "Rules / state / side-effect trace",
    "Data / permissions", "Failure / recovery", "API contract / evidence",
    "MCP contract / evidence", "UI subtree references", "Simulation subtree references",
    "Evidence / attestation", "Primary mainline",
)
UI_COLUMNS = (
    "UI ID", "Subtree path", "Component version", "Content hash", "Actor",
    "Surface / state", "Actions / feedback", "Workflow subtree references",
    "Simulation subtree references", "Evidence / attestation", "Lock status",
    "Primary mainline", "UI change authority", "Baseline Change Request",
)
SIMULATION_COLUMNS = (
    "Simulation ID", "Subtree path", "Component version", "Content hash",
    "Foundation status", "Workflow subtree references", "UI subtree references",
    "Primary mainline",
)
SCENARIO_COLUMNS = (
    "Simulation ID", "Scenario ID", "Actors", "Data/state/time", "Path",
    "Failure/recovery", "Fidelity", "Visible / invisible evidence",
    "Used by Slice/Run/Acceptance", "Scenario version",
)
HANDOFF_COLUMNS = (
    "Subtree type", "Subtree ID", "Path", "Component version", "Content hash",
    "Classification", "Classification authority", "Workflow Capability ID",
    "API evidence", "MCP evidence", "Primary mainline", "Related subtree IDs",
)


def definition_handoff():
    return """# Calabash Definition Handoff

- Artifact role: CALABASH_DEFINITION_HANDOFF
- Definition Handoff ID: CDH-MIGRATION-400
- Definition Baseline kind: CALABASH_DEFINITION_BASELINE
- Definition Baseline ID: DB-MIGRATION-400
- Definition Baseline semantic version: 1.0.0
- Definition Baseline exact hash: sha256:1111111111111111111111111111111111111111111111111111111111111111
- Calabash standard version: 2.5.0
- Baseline status: FROZEN
- Applicable Definition clause references: baseline:/grandpa/product
- Snake review status: NONE_IDENTIFIED
- Snake review scope: Grandpa
- Snake review evidence refs: E-SNAKE-MIGRATION
- Scorpion review status: NONE_IDENTIFIED
- Scorpion review scope: Grandpa
- Scorpion review evidence refs: E-SCORPION-MIGRATION
- Meaning-change / invalidation rules reference: CAL-CHANGE-MIGRATION
- Upgrade Receipt ID: UPGRADE-MIGRATION
- Upgrade Receipt exact hash: sha256:2222222222222222222222222222222222222222222222222222222222222222
- Upgrade verdict: CALABASH_UPGRADE_PASS
- Owner change authority: OWNER
- Handoff result: PASS

## Snake records

| Snake ID | Disposition | Guard / verification reference | Evidence refs | Affected Definition clause refs |
|---|---|---|---|---|

## Scorpion records

| Scorpion ID | Status | Blocking semantics | Hit condition reference | Evidence refs | Affected Definition clause refs |
|---|---|---|---|---|---|
"""


def source_status(*, accepted):
    status = strict_json(TEMPLATES / "STATUS.json")
    for field in (
        "lccoding_applicability", "product_service_strategy", "service_route_map"
    ):
        status.pop(field, None)
    status["status_schema_version"] = "3.0.0"
    status["project_id"] = "PROJECT-MIGRATION-300"
    status["initialization_mode"] = "NEW"
    status["proposal"] = "COMPLETE"
    status["initialization"] = "COMPLETE"
    status["phase_gates"]["INITIAL_READY"] = "PASS"
    status["current_phase"] = "PRODUCT_FORMATION"
    if accepted:
        status["canonical_candidate"] = {
            "repository": "github.com/example/migration",
            "version": "1.0.0",
            "commit": "fixture-commit",
            "candidate_id": "CANDIDATE-300",
            "candidate_hash": HASH,
        }
        status["current_phase"] = "REAL_USER_JOURNEY_ACCEPTANCE"
        status["phase_gates"].update(
            {
                "CALABASH_UPGRADE_READY": "PASS",
                "ALL_REQUIRED_RUNS_ACCEPTED": "PASS",
                "REAL_USER_JOURNEY_ACCEPTED": "REAL_USER_JOURNEY_ACCEPTED",
            }
        )
        status["product_baseline"] = "ACCEPTED"
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
    assert status["status_schema_version"] == "3.0.0"
    assert not {
        "lccoding_applicability", "product_service_strategy", "service_route_map"
    }.intersection(status)
    return status


def source_phase_status(*, accepted):
    phase = strict_json(TEMPLATES / "PHASE-STATUS.json")
    phase["status_schema_version"] = "3.0.0"
    phase["current_phase"] = "PRODUCT_FORMATION"
    phase["phases"]["INITIAL"] = {"status": "COMPLETE", "exit_gate": "PASS"}
    phase["phases"]["PRODUCT_FORMATION"] = {
        "status": "ACTIVE",
        "exit_evidence": "PENDING",
    }
    if accepted:
        phase["current_phase"] = "REAL_USER_JOURNEY_ACCEPTANCE"
        phase["phases"]["PRODUCT_FORMATION"] = {
            "status": "COMPLETE",
            "exit_evidence": "ACCEPTED",
        }
        phase["phases"]["REAL_PRODUCT_INTEGRATION"] = {
            "status": "COMPLETE",
            "per_run_acceptances": [],
            "aggregate_exit_gate": "PASS",
        }
        phase["phases"]["REAL_USER_JOURNEY_ACCEPTANCE"] = {
            "status": "COMPLETE",
            "acceptance_record": "REAL-USER-JOURNEY-ACCEPTANCE.md",
            "defect_log": "REAL-USER-JOURNEY-DEFECT-LOG.md",
            "complete_rounds": 1,
            "exit_gate": "REAL_USER_JOURNEY_ACCEPTED",
        }
    return phase


def install_product_baseline(project):
    module_spec = importlib.util.spec_from_file_location(
        "migration_400_project_validator", PROJECT_VALIDATOR
    )
    project_validator = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(project_validator)

    run(["git", "init", "--quiet"], cwd=project).check_returncode()
    run(["git", "config", "user.email", "fixture@example.invalid"], cwd=project).check_returncode()
    run(["git", "config", "user.name", "Fixture"], cwd=project).check_returncode()
    paths = {
        "UI-MAIN": "product/ui/main",
        "WF-CORE": "product/workflows/core",
        "SIM-MAIN": "product/simulations/main",
    }
    for subtree_id, relative in paths.items():
        write(project / relative / "identity.txt", subtree_id + "\n")
    run(["git", "add", "product"], cwd=project).check_returncode()
    run(["git", "commit", "--quiet", "-m", "freeze direct product"], cwd=project).check_returncode()
    commit = run(["git", "rev-parse", "HEAD"], cwd=project).stdout.strip()
    hashes = {
        subtree_id: project_validator.frozen_subtree_content_hash(project, commit, relative)[0]
        for subtree_id, relative in paths.items()
    }

    workflow = {
        "Workflow ID": "WF-CORE",
        "Classification (CORE/EXTRA)": "CORE",
        "Implementation status": "IMPLEMENTED",
        "Classification authority": "CLASSIFICATION:CORE; CALABASH:CAL-CORE; OWNER_CONFIRMED:OA-CORE",
        "Subtree path": paths["WF-CORE"],
        "Component version": "1.0.0",
        "Content hash": hashes["WF-CORE"],
        "Workflow Capability ID": "CAP-CORE",
        "Actors": "Human principal",
        "Trigger": "Direct browser action",
        "Rules / state / side-effect trace": "RULES:R-CORE; STATE:S-CORE; SIDE_EFFECTS:SE-CORE",
        "Data / permissions": "Owner-scoped fixture data",
        "Failure / recovery": "Visible failure and retry",
        "API contract / evidence": "CAPABILITY:CAP-CORE; CONTRACT:API-CORE; EVIDENCE:E-API-CORE",
        "MCP contract / evidence": "CAPABILITY:CAP-CORE; CONTRACT:MCP-CORE; EVIDENCE:E-MCP-CORE",
        "UI subtree references": "UI-MAIN",
        "Simulation subtree references": "SIM-MAIN",
        "Evidence / attestation": "IMPLEMENTATION:E-IMPL-CORE; RUNNABLE:E-RUN-CORE",
        "Primary mainline": "YES",
    }
    ui = {
        "UI ID": "UI-MAIN",
        "Subtree path": paths["UI-MAIN"],
        "Component version": "1.0.0",
        "Content hash": hashes["UI-MAIN"],
        "Actor": "Human principal",
        "Surface / state": "Browser result",
        "Actions / feedback": "Submit / visible accepted result",
        "Workflow subtree references": "WF-CORE",
        "Simulation subtree references": "SIM-MAIN",
        "Evidence / attestation": "E-UI-MAIN",
        "Lock status": "LOCKED",
        "Primary mainline": "YES",
        "UI change authority": "OWNER_ONLY",
        "Baseline Change Request": "NONE",
    }
    simulation = {
        "Simulation ID": "SIM-MAIN",
        "Subtree path": paths["SIM-MAIN"],
        "Component version": "1.0.0",
        "Content hash": hashes["SIM-MAIN"],
        "Foundation status": "RUNNABLE",
        "Workflow subtree references": "WF-CORE",
        "UI subtree references": "UI-MAIN",
        "Primary mainline": "YES",
    }
    scenario = {
        "Simulation ID": "SIM-MAIN",
        "Scenario ID": "SCN-MAIN",
        "Actors": "Human principal",
        "Data/state/time": "candidate-bound state",
        "Path": "direct browser route",
        "Failure/recovery": "visible failure and recovery",
        "Fidelity": "PRODUCTION_EQUIVALENT",
        "Visible / invisible evidence": "E-SCENARIO",
        "Used by Slice/Run/Acceptance": "JOURNEY-001",
        "Scenario version": "1.0.0",
    }
    locked = [
        {
            "Subtree type": "UI", "Subtree ID": "UI-MAIN", "Path": paths["UI-MAIN"],
            "Component version": "1.0.0", "Content hash": hashes["UI-MAIN"],
            "Classification": "NOT_APPLICABLE", "Classification authority": "NOT_APPLICABLE",
            "Workflow Capability ID": "NOT_APPLICABLE", "API evidence": "NOT_APPLICABLE",
            "MCP evidence": "NOT_APPLICABLE", "Primary mainline": "YES",
            "Related subtree IDs": "WF-CORE, SIM-MAIN",
        },
        {
            "Subtree type": "WORKFLOW", "Subtree ID": "WF-CORE", "Path": paths["WF-CORE"],
            "Component version": "1.0.0", "Content hash": hashes["WF-CORE"],
            "Classification": "CORE", "Classification authority": workflow["Classification authority"],
            "Workflow Capability ID": "CAP-CORE", "API evidence": workflow["API contract / evidence"],
            "MCP evidence": workflow["MCP contract / evidence"], "Primary mainline": "YES",
            "Related subtree IDs": "UI-MAIN, SIM-MAIN",
        },
        {
            "Subtree type": "SIMULATION", "Subtree ID": "SIM-MAIN", "Path": paths["SIM-MAIN"],
            "Component version": "1.0.0", "Content hash": hashes["SIM-MAIN"],
            "Classification": "NOT_APPLICABLE", "Classification authority": "NOT_APPLICABLE",
            "Workflow Capability ID": "NOT_APPLICABLE", "API evidence": "NOT_APPLICABLE",
            "MCP evidence": "NOT_APPLICABLE", "Primary mainline": "YES",
            "Related subtree IDs": "WF-CORE, UI-MAIN",
        },
    ]

    lc = project / ".lccoding"
    gate = definition_handoff()
    write(lc / "CALABASH-UPGRADE-GATE.md", gate)
    gate_hash = "sha256:" + hashlib.sha256(gate.encode("utf-8")).hexdigest()
    write(
        lc / "WORKFLOW-MAP.md",
        "# Workflow Map\n\n- Primary product mainline ID: MAINLINE-1\n\n"
        + table(WORKFLOW_COLUMNS, [workflow]) + "\n",
    )
    write(
        lc / "UI-MAP.md",
        "# UI Map\n\n- Primary product mainline ID: MAINLINE-1\n\n"
        + table(UI_COLUMNS, [ui]) + "\n",
    )
    write(
        lc / "SIMULATION-WORLD.md",
        "# Simulation World\n\n- Primary product mainline ID: MAINLINE-1\n\n"
        "## Simulation subtree registry\n\n"
        + table(SIMULATION_COLUMNS, [simulation])
        + "\n\n## Scenario registry\n\n"
        + table(SCENARIO_COLUMNS, [scenario]) + "\n",
    )
    write(
        lc / "PRODUCT-BASELINE-HANDOFF.md",
        "# Product Baseline Handoff\n\n"
        "- Baseline ID / version / hash: PB-MIGRATION / 1.0.0 / E-PB-MIGRATION\n"
        "- Project repository identity: github.com/example/migration\n"
        f"- Project frozen exact commit SHA: {commit}\n"
        "- Calabash source: CAL-MIGRATION\n"
        f"- Calabash Definition Handoff ID / exact hash: CDH-MIGRATION-400 / {gate_hash}\n"
        "- Calabash Definition Handoff result: PASS\n"
        "- Workflow Map: .lccoding/WORKFLOW-MAP.md\n"
        "- UI Map: .lccoding/UI-MAP.md\n"
        "- Simulation World: .lccoding/SIMULATION-WORLD.md\n"
        "- Primary product mainline ID: MAINLINE-1\n"
        "- Primary mainline Owner confirmation: OWNER_CONFIRMED: OA-MAINLINE\n"
        "- Handoff status: COMPLETE\n\n"
        "## Locked logical subtrees\n\n"
        + table(HANDOFF_COLUMNS, locked) + "\n",
    )


def install_browser_acceptance(project):
    lc = project / ".lccoding"
    evidence = lc / "evidence/real-user-journey/round-001/JOURNEY-001"
    evidence.mkdir(parents=True)
    screenshot = b"accepted-direct-browser-result"
    screenshot_path = evidence / "STEP-001.png"
    screenshot_path.write_bytes(screenshot)
    digest = hashlib.sha256(screenshot).hexdigest()
    write(
        lc / "REAL-USER-JOURNEY-ACCEPTANCE.md",
        f"""# Real User Journey Acceptance

## Candidate identity

- Acceptance ID: RUJA-MIGRATION-300
- Candidate ID: CANDIDATE-300
- Candidate SHA-256: {HASH}

## Journey coverage

| Journey ID | Actor / permission | Start | Preconditions / safe data | Ordered visible actions | Expected visible results / outcome | Exception / recovery routes | Trace | Applicability |
|---|---|---|---|---|---|---|---|---|
| JOURNEY-001 | HUMAN-PRINCIPAL | BROWSER-HOME | READY | STEP-001 | ACCEPTED-RESULT | NONE | TRACE-001 | REQUIRED |

## Acceptance rounds

| Round | Candidate ID / SHA-256 | Started from home entry | Required / passed / failed / N/A | First and last evidence | Defect IDs | Result |
|---|---|---|---|---|---|---|
| 1 | CANDIDATE-300 / {HASH} | YES | 1 / 1 / 0 / 0 | STEP-001 / STEP-001 | NONE | PASS |

## Evidence digests

| Round | Journey ID | Step ID | Action | Expected / observed visible result | Visible location | Viewport | Screenshot path | Screenshot SHA-256 | Result |
|---|---|---|---|---|---|---|---|---|---|
| 1 | JOURNEY-001 | STEP-001 | CLICK | ACCEPTED-RESULT / ACCEPTED-RESULT | BROWSER-HOME | 1280x720@1 | .lccoding/evidence/real-user-journey/round-001/JOURNEY-001/STEP-001.png | {digest} | PASS |

## Defect pointers

- Defect log reference: REAL-USER-JOURNEY-DEFECT-LOG.md
- Owner result: REAL_USER_JOURNEY_ACCEPTED
""",
    )
    write(
        lc / "REAL-USER-JOURNEY-DEFECT-LOG.md",
        """# Real User Journey Defect Log

## Defect register

| Defect ID | Discovery time / candidate / round / Journey / Step | Screenshot SHA-256 | Expected / observed | Severity / reachability / blocking scope | Visible layer / root cause | Affected surfaces | Correction identity / engineering re-verification | Retest round | State | Exemption authority / impact / recovery |
|---|---|---|---|---|---|---|---|---|---|---|

## State history

| Defect ID | Event time | Prior state | New state | Candidate ID / SHA-256 | Evidence / reason |
|---|---|---|---|---|---|
""",
    )


def make_source(project, *, accepted):
    lc = project / ".lccoding"
    lc.mkdir(parents=True)
    for name in ("OWNER-POLICY.md", "PROJECT-PROFILE.md", "AGENT-RULE.md"):
        write(lc / name, "# Migration fixture evidence\n")
    if accepted:
        install_product_baseline(project)
    else:
        for name in ("WORKFLOW-MAP.md", "UI-MAP.md", "SIMULATION-WORLD.md"):
            (lc / name).write_bytes((TEMPLATES / name).read_bytes())

    manifest = strict_json(TEMPLATES / "CANONICAL-MANIFEST.json")
    manifest["lccoding"]["version"] = "3.0.0"
    # A legacy 3.0 manifest may predate the generic execution-method collection.
    # Keeping that collection absent lets this fixture prove accepted browser
    # evidence without manufacturing unrelated Run records.
    manifest.pop("execution_methods")
    write(lc / "CANONICAL-MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
    write(project / "VERSION", "1.0.0\n")
    write(
        lc / "PROJECT-START.json",
        json.dumps(
            {"initialization_mode": "NEW", "repository": "github.com/example/migration"}
        ) + "\n",
    )
    factors = {
        name: "LOW"
        for name in (
            "product_uncertainty", "system_coupling", "real_risk",
            "irreversibility", "novelty",
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
        ) + "\n",
    )
    write(
        lc / "PROJECT-HEALTH.json",
        json.dumps(
            {"record_role": "ASSESSMENT_EVIDENCE", "initialization_mode": "NEW"},
            indent=2,
        ) + "\n",
    )
    write(lc / "status.json", json.dumps(source_status(accepted=accepted), indent=2) + "\n")
    write(
        lc / "PHASE-STATUS.json",
        json.dumps(source_phase_status(accepted=accepted), indent=2) + "\n",
    )
    manifest_bytes = (lc / "CANONICAL-MANIFEST.json").read_bytes()
    lock = strict_json(TEMPLATES / "INTERPRETATION-LOCK.json")
    lock.update(
        {
            "project_id": "PROJECT-MIGRATION-300",
            "issued_at": "2026-09-09T00:00:00Z",
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
    if accepted:
        install_browser_acceptance(project)


def invoke(source, output):
    return run(
        [
            sys.executable,
            str(MIGRATOR),
            "--project", str(source),
            "--output", str(output),
        ]
    )


assert CONTRACT.is_file(), "3.0.0 to 4.0.0 migration contract is absent"
assert MIGRATOR.is_file(), "3.0.0 to 4.0.0 migration command is absent"

contract = CONTRACT.read_text(encoding="utf-8")
for marker in (
    "Source status schema: 3.0.0",
    "Target status schema: 4.0.0",
    "COPY_ON_WRITE_EXTERNAL_TARGET",
    "ORIGINAL_3_0_INPUTS_BYTES_AND_MTIMES_UNCHANGED",
    "INDEPENDENT_GIT_METADATA_NO_SHARED_ADMIN_OR_HARDLINKS",
    "UNBORN_HEAD_PRESERVED_NO_COMMIT_INVENTED",
    "UNBORN_REFS_AND_REACHABLE_HISTORY_PRESERVED",
    "PLATFORM_COMPLETION",
    "DRAFT",
    "PERSONAL_AGENT_NOT_CLAIMED",
    "SERVICE_CENTER_NOT_CLAIMED",
    "ATOMIC_TARGET_ABSENT_ON_FAILURE",
    "validate_project.py",
):
    assert marker in contract, marker

with tempfile.TemporaryDirectory(prefix="lccoding-migration-400-") as temporary:
    base = Path(temporary)
    unaccepted_source = base / "source-300-unaccepted"
    make_source(unaccepted_source, accepted=False)
    source_result = run([sys.executable, str(PROJECT_VALIDATOR), str(unaccepted_source)])
    assert source_result.returncode == 0, source_result.stdout + source_result.stderr
    unaccepted_before = snapshot(unaccepted_source)
    unaccepted_target = base / "target-400-unaccepted"
    result = invoke(unaccepted_source, unaccepted_target)
    assert result.returncode == 0, result.stdout + result.stderr
    assert snapshot(unaccepted_source) == unaccepted_before
    target_result = run([sys.executable, str(PROJECT_VALIDATOR), str(unaccepted_target)])
    assert target_result.returncode == 0, target_result.stdout + target_result.stderr
    status = strict_json(unaccepted_target / ".lccoding/status.json")
    route_map = strict_json(unaccepted_target / ".lccoding/SERVICE-ROUTE-MAP.json")
    assert status["status_schema_version"] == "4.0.0"
    assert status["lccoding_applicability"] == "PENDING"
    assert status["product_service_strategy"] == "PENDING"
    assert status["service_route_map"] == "PENDING"
    assert route_map["state"] == "PENDING"
    assert route_map["journeys"] == []

    accepted_source = base / "source-300-accepted"
    make_source(accepted_source, accepted=True)
    source_result = run([sys.executable, str(PROJECT_VALIDATOR), str(accepted_source)])
    assert source_result.returncode == 0, source_result.stdout + source_result.stderr
    accepted_before = snapshot(accepted_source)
    accepted_target = base / "target-400-accepted"
    result = invoke(accepted_source, accepted_target)
    assert result.returncode == 0, result.stdout + result.stderr
    assert snapshot(accepted_source) == accepted_before
    target_result = run([sys.executable, str(PROJECT_VALIDATOR), str(accepted_target)])
    assert target_result.returncode == 0, target_result.stdout + target_result.stderr
    assert run(
        [sys.executable, str(PHASE_VALIDATOR), str(accepted_target / ".lccoding/PHASE-STATUS.json")]
    ).returncode == 0

    status = strict_json(accepted_target / ".lccoding/status.json")
    phase = strict_json(accepted_target / ".lccoding/PHASE-STATUS.json")
    route_map = strict_json(accepted_target / ".lccoding/SERVICE-ROUTE-MAP.json")
    historical = strict_json(accepted_target / ".lccoding" / HISTORY_ROOT / "status.json")
    report_bytes = (accepted_target / ".lccoding" / REPORT_REFERENCE).read_bytes()
    report = strict_json(accepted_target / ".lccoding" / REPORT_REFERENCE)

    assert status["status_schema_version"] == "4.0.0"
    assert status["lccoding_applicability"] == "WHOLE_PRODUCT_FIT"
    assert status["product_service_strategy"] == "PLATFORM_COMPLETION"
    assert status["service_route_map"] == "DRAFT"
    assert status["current_phase"] == "PRODUCT_FORMATION"
    assert status["product_baseline"] == "PENDING"
    assert status["phase_gates"]["REAL_USER_JOURNEY_ACCEPTED"] == "PENDING"
    assert status["real_user_journey_acceptance"]["state"] == "UNPROVED"
    assert phase["status_schema_version"] == "4.0.0"
    assert phase["phases"]["PRODUCT_FORMATION"]["status"] == "ACTIVE"
    assert phase["phases"]["REAL_USER_JOURNEY_ACCEPTANCE"]["status"] == "PENDING"
    assert historical["real_user_journey_acceptance"]["state"] == "REAL_USER_JOURNEY_ACCEPTED"
    assert (
        accepted_target / ".lccoding/REAL-USER-JOURNEY-ACCEPTANCE.md"
    ).read_bytes() == (
        accepted_source / ".lccoding/REAL-USER-JOURNEY-ACCEPTANCE.md"
    ).read_bytes()

    assert route_map["state"] == "DRAFT"
    assert route_map["primary_strategy"] == "PLATFORM_COMPLETION"
    assert route_map["required_coexisting_strategies"] == []
    assert route_map["service_center_applicability"] == "NOT_APPLICABLE"
    routes = [route for journey in route_map["journeys"] for route in journey["routes"]]
    assert {route["route_kind"] for route in routes} == {"DIRECT_PRODUCT"}
    assert all(route["delivery_state"] == "UNPROVED" for route in routes)
    assert "PERSONAL_AGENT" not in report_bytes.decode("utf-8") or report["personal_agent_delivery"] == "NOT_CLAIMED"
    assert report["personal_agent_delivery"] == "NOT_CLAIMED"
    assert report["service_center_delivery"] == "NOT_CLAIMED"
    assert report["legacy_phase4_treatment"] == "HISTORICAL_PRESERVED_REVALIDATION_REQUIRED"
    assert REPORT_REFERENCE in status["evidence_pointers"]

    deterministic_target = base / "target-400-deterministic"
    deterministic_result = invoke(accepted_source, deterministic_target)
    assert deterministic_result.returncode == 0, deterministic_result.stdout + deterministic_result.stderr
    assert (
        deterministic_target / ".lccoding" / REPORT_REFERENCE
    ).read_bytes() == report_bytes
    assert snapshot(accepted_source) == accepted_before

    occupied = base / "occupied-target"
    occupied.mkdir()
    write(occupied / "owner.txt", "do not overwrite\n")
    occupied_before = snapshot(occupied)
    assert invoke(unaccepted_source, occupied).returncode != 0
    assert snapshot(occupied) == occupied_before
    assert snapshot(unaccepted_source) == unaccepted_before

    wrong_schema = base / "source-wrong-schema"
    make_source(wrong_schema, accepted=False)
    wrong_status_path = wrong_schema / ".lccoding/status.json"
    wrong_status = strict_json(wrong_status_path)
    wrong_status["status_schema_version"] = "4.0.0"
    write(wrong_status_path, json.dumps(wrong_status, indent=2) + "\n")
    wrong_before = snapshot(wrong_schema)
    wrong_target = base / "wrong-target"
    assert invoke(wrong_schema, wrong_target).returncode != 0
    assert not wrong_target.exists()
    assert snapshot(wrong_schema) == wrong_before

    duplicate_source = base / "source-duplicate"
    make_source(duplicate_source, accepted=False)
    duplicate_status = duplicate_source / ".lccoding/status.json"
    duplicate_text = duplicate_status.read_text(encoding="utf-8").replace(
        '  "status_schema_version": "3.0.0",',
        '  "status_schema_version": "3.0.0",\n  "status_schema_version": "3.0.0",',
        1,
    )
    write(duplicate_status, duplicate_text)
    duplicate_before = snapshot(duplicate_source)
    duplicate_target = base / "duplicate-target"
    assert invoke(duplicate_source, duplicate_target).returncode != 0
    assert not duplicate_target.exists()
    assert snapshot(duplicate_source) == duplicate_before
    assert not list(base.glob(".*.lccoding-migrate-*"))

with tempfile.TemporaryDirectory(prefix="lccoding-linked-worktree-400-") as temporary:
    base = Path(temporary)
    repository = base / "repository"
    linked_source = base / "linked-source-300"
    linked_target = base / "linked-target-400"
    repository.mkdir()
    run(["git", "init", "--quiet"], cwd=repository).check_returncode()
    run(["git", "config", "user.email", "fixture@example.invalid"], cwd=repository).check_returncode()
    run(["git", "config", "user.name", "Fixture"], cwd=repository).check_returncode()
    write(repository / "seed.txt", "seed\n")
    run(["git", "add", "seed.txt"], cwd=repository).check_returncode()
    run(["git", "commit", "--quiet", "-m", "seed"], cwd=repository).check_returncode()
    worktree_result = run(
        ["git", "worktree", "add", "--quiet", "-b", "migration-linked-source", str(linked_source), "HEAD"],
        cwd=repository,
    )
    assert worktree_result.returncode == 0, worktree_result.stdout + worktree_result.stderr
    assert (linked_source / ".git").is_file(), "fixture is not a real linked worktree"
    make_source(linked_source, accepted=False)
    run(["git", "add", "-A"], cwd=linked_source).check_returncode()
    run(["git", "commit", "--quiet", "-m", "valid 3.0 linked source"], cwd=linked_source).check_returncode()

    def git_text(repo, *arguments):
        result = run(["git", "--no-optional-locks", *arguments], cwd=repo)
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout.strip()

    source_status_before = git_text(linked_source, "status", "--porcelain=v1", "--untracked-files=all")
    assert source_status_before == ""
    source_admin = Path(git_text(linked_source, "rev-parse", "--absolute-git-dir")).resolve()
    source_index_text = git_text(
        linked_source, "rev-parse", "--path-format=absolute", "--git-path", "index"
    )
    source_index = Path(source_index_text)
    if not source_index.is_absolute():
        source_index = linked_source / source_index
    source_index = source_index.resolve()
    source_index_before = (source_index.read_bytes(), source_index.stat().st_mtime_ns)
    source_tree_before = snapshot(linked_source)

    linked_result = invoke(linked_source, linked_target)
    assert linked_result.returncode == 0, linked_result.stdout + linked_result.stderr
    assert run([sys.executable, str(PROJECT_VALIDATOR), str(linked_target)]).returncode == 0
    target_admin = Path(git_text(linked_target, "rev-parse", "--absolute-git-dir")).resolve()
    target_common = Path(git_text(linked_target, "rev-parse", "--git-common-dir"))
    if not target_common.is_absolute():
        target_common = linked_target / target_common
    target_common = target_common.resolve()
    assert target_admin != source_admin
    assert (linked_target / ".git").is_dir()
    assert target_admin == target_common == (linked_target / ".git").resolve()
    assert not (target_common / "objects/info/alternates").exists()

    target_add = run(["git", "add", ".lccoding/status.json"], cwd=linked_target)
    assert target_add.returncode == 0, target_add.stdout + target_add.stderr
    assert git_text(linked_target, "status", "--porcelain=v1")
    assert git_text(linked_source, "status", "--porcelain=v1", "--untracked-files=all") == source_status_before
    assert (source_index.read_bytes(), source_index.stat().st_mtime_ns) == source_index_before
    assert snapshot(linked_source) == source_tree_before

with tempfile.TemporaryDirectory(prefix="lccoding-unborn-git-400-") as temporary:
    base = Path(temporary)
    unborn_source = base / "unborn-source-300"
    unborn_target = base / "unborn-target-400"
    unborn_source.mkdir()
    init_result = run(
        ["git", "init", "--quiet", "--initial-branch=unborn-migration"],
        cwd=unborn_source,
    )
    assert init_result.returncode == 0, init_result.stdout + init_result.stderr
    run(
        [
            "git",
            "remote",
            "add",
            "origin",
            "https://example.invalid/lccoding/unborn.git",
        ],
        cwd=unborn_source,
    ).check_returncode()
    make_source(unborn_source, accepted=False)
    run(["git", "add", "-A"], cwd=unborn_source).check_returncode()
    assert run([sys.executable, str(PROJECT_VALIDATOR), str(unborn_source)]).returncode == 0
    assert run(["git", "rev-parse", "--verify", "HEAD"], cwd=unborn_source).returncode != 0
    assert git_text(unborn_source, "symbolic-ref", "--quiet", "--short", "HEAD") == (
        "unborn-migration"
    )

    source_status_before = git_text(
        unborn_source, "status", "--porcelain=v1", "--untracked-files=all"
    )
    assert source_status_before
    source_admin = Path(
        git_text(unborn_source, "rev-parse", "--absolute-git-dir")
    ).resolve()
    source_common = Path(
        git_text(unborn_source, "rev-parse", "--path-format=absolute", "--git-common-dir")
    ).resolve()
    source_index = Path(
        git_text(
            unborn_source,
            "rev-parse",
            "--path-format=absolute",
            "--git-path",
            "index",
        )
    ).resolve()
    source_objects = Path(
        git_text(
            unborn_source,
            "rev-parse",
            "--path-format=absolute",
            "--git-path",
            "objects",
        )
    ).resolve()
    source_index_before = (source_index.read_bytes(), source_index.stat().st_mtime_ns)
    source_tree_before = snapshot(unborn_source)

    unborn_result = invoke(unborn_source, unborn_target)
    assert unborn_result.returncode == 0, unborn_result.stdout + unborn_result.stderr
    target_validation = run(
        [sys.executable, str(PROJECT_VALIDATOR), str(unborn_target)]
    )
    assert target_validation.returncode == 0, target_validation.stdout + target_validation.stderr
    assert run(["git", "rev-parse", "--verify", "HEAD"], cwd=unborn_target).returncode != 0
    assert git_text(unborn_target, "symbolic-ref", "--quiet", "--short", "HEAD") == (
        "unborn-migration"
    )
    assert git_text(unborn_target, "config", "--get", "remote.origin.url") == (
        "https://example.invalid/lccoding/unborn.git"
    )

    target_admin = Path(
        git_text(unborn_target, "rev-parse", "--absolute-git-dir")
    ).resolve()
    target_common = Path(
        git_text(unborn_target, "rev-parse", "--path-format=absolute", "--git-common-dir")
    ).resolve()
    target_index = Path(
        git_text(
            unborn_target,
            "rev-parse",
            "--path-format=absolute",
            "--git-path",
            "index",
        )
    ).resolve()
    target_objects = Path(
        git_text(
            unborn_target,
            "rev-parse",
            "--path-format=absolute",
            "--git-path",
            "objects",
        )
    ).resolve()
    assert (unborn_target / ".git").is_dir()
    assert target_admin == target_common == (unborn_target / ".git").resolve()
    assert target_admin != source_admin
    assert target_common != source_common
    assert target_index != source_index
    assert target_objects != source_objects
    assert not (target_objects / "info/alternates").exists()

    target_add = run(["git", "add", ".lccoding/status.json"], cwd=unborn_target)
    assert target_add.returncode == 0, target_add.stdout + target_add.stderr
    assert target_index.is_file()
    assert git_text(unborn_target, "status", "--porcelain=v1")
    assert run(["git", "rev-parse", "--verify", "HEAD"], cwd=unborn_target).returncode != 0
    assert git_text(
        unborn_source, "status", "--porcelain=v1", "--untracked-files=all"
    ) == source_status_before
    assert (source_index.read_bytes(), source_index.stat().st_mtime_ns) == source_index_before
    assert snapshot(unborn_source) == source_tree_before

with tempfile.TemporaryDirectory(prefix="lccoding-unborn-history-400-") as temporary:
    base = Path(temporary)
    history_repository = base / "history-repository"
    history_source = base / "unborn-history-source-300"
    history_target = base / "unborn-history-target-400"
    history_repository.mkdir()
    init_result = run(
        ["git", "init", "--quiet", "--initial-branch=main"], cwd=history_repository
    )
    assert init_result.returncode == 0, init_result.stdout + init_result.stderr
    run(
        ["git", "config", "user.email", "fixture@example.invalid"],
        cwd=history_repository,
    ).check_returncode()
    run(
        ["git", "config", "user.name", "Fixture"], cwd=history_repository
    ).check_returncode()
    run(
        [
            "git",
            "remote",
            "add",
            "origin",
            "https://example.invalid/lccoding/history.git",
        ],
        cwd=history_repository,
    ).check_returncode()
    write(history_repository / "prior.txt", "reachable history\n")
    run(["git", "add", "prior.txt"], cwd=history_repository).check_returncode()
    run(
        ["git", "commit", "--quiet", "-m", "prior main history"],
        cwd=history_repository,
    ).check_returncode()
    main_commit = git_text(history_repository, "rev-parse", "refs/heads/main")
    run(["git", "repack", "-ad"], cwd=history_repository).check_returncode()
    worktree_result = run(
        [
            "git",
            "worktree",
            "add",
            "--quiet",
            "-b",
            "linked-before-orphan",
            str(history_source),
            "main",
        ],
        cwd=history_repository,
    )
    assert worktree_result.returncode == 0, worktree_result.stdout + worktree_result.stderr
    assert (history_source / ".git").is_file()
    orphan_result = run(
        ["git", "switch", "--quiet", "--orphan", "unborn-with-history"],
        cwd=history_source,
    )
    assert orphan_result.returncode == 0, orphan_result.stdout + orphan_result.stderr
    make_source(history_source, accepted=False)
    run(["git", "add", "-A"], cwd=history_source).check_returncode()
    source_validation = run(
        [sys.executable, str(PROJECT_VALIDATOR), str(history_source)]
    )
    assert source_validation.returncode == 0, source_validation.stdout + source_validation.stderr
    assert run(["git", "rev-parse", "--verify", "HEAD"], cwd=history_source).returncode != 0
    assert git_text(history_source, "symbolic-ref", "--quiet", "--short", "HEAD") == (
        "unborn-with-history"
    )
    source_refs = git_text(
        history_source, "for-each-ref", "--format=%(refname) %(objectname)"
    )
    assert f"refs/heads/main {main_commit}" in source_refs.splitlines()

    source_status_before = git_text(
        history_source, "status", "--porcelain=v1", "--untracked-files=all"
    )
    source_admin = Path(
        git_text(history_source, "rev-parse", "--absolute-git-dir")
    ).resolve()
    source_common = Path(
        git_text(history_source, "rev-parse", "--path-format=absolute", "--git-common-dir")
    ).resolve()
    assert source_admin != source_common
    source_index = Path(
        git_text(
            history_source,
            "rev-parse",
            "--path-format=absolute",
            "--git-path",
            "index",
        )
    ).resolve()
    source_objects = Path(
        git_text(
            history_source,
            "rev-parse",
            "--path-format=absolute",
            "--git-path",
            "objects",
        )
    ).resolve()
    source_index_before = (source_index.read_bytes(), source_index.stat().st_mtime_ns)
    source_tree_before = snapshot(history_source)
    source_repository_before = snapshot(history_repository)

    history_result = invoke(history_source, history_target)
    assert history_result.returncode == 0, history_result.stdout + history_result.stderr
    target_validation = run(
        [sys.executable, str(PROJECT_VALIDATOR), str(history_target)]
    )
    assert target_validation.returncode == 0, target_validation.stdout + target_validation.stderr
    assert run(["git", "rev-parse", "--verify", "HEAD"], cwd=history_target).returncode != 0
    assert git_text(history_target, "symbolic-ref", "--quiet", "--short", "HEAD") == (
        "unborn-with-history"
    )
    assert git_text(history_target, "rev-parse", "refs/heads/main") == main_commit
    assert run(
        ["git", "cat-file", "-e", f"{main_commit}^{{commit}}"], cwd=history_target
    ).returncode == 0
    assert git_text(history_target, "show", f"{main_commit}:prior.txt") == (
        "reachable history"
    )
    assert git_text(
        history_target, "for-each-ref", "--format=%(refname) %(objectname)"
    ) == source_refs
    assert git_text(history_target, "config", "--get", "remote.origin.url") == (
        "https://example.invalid/lccoding/history.git"
    )

    target_admin = Path(
        git_text(history_target, "rev-parse", "--absolute-git-dir")
    ).resolve()
    target_common = Path(
        git_text(history_target, "rev-parse", "--path-format=absolute", "--git-common-dir")
    ).resolve()
    target_index = Path(
        git_text(
            history_target,
            "rev-parse",
            "--path-format=absolute",
            "--git-path",
            "index",
        )
    ).resolve()
    target_objects = Path(
        git_text(
            history_target,
            "rev-parse",
            "--path-format=absolute",
            "--git-path",
            "objects",
        )
    ).resolve()
    assert (history_target / ".git").is_dir()
    assert target_admin == target_common == (history_target / ".git").resolve()
    assert target_admin != source_admin
    assert target_common != source_common
    assert target_index != source_index
    assert target_objects != source_objects
    assert not (target_objects / "info/alternates").exists()

    target_add = run(
        ["git", "add", ".lccoding/status.json", "VERSION"], cwd=history_target
    )
    assert target_add.returncode == 0, target_add.stdout + target_add.stderr
    assert target_index.is_file()
    matching_object_files = 0
    for target_object in target_objects.rglob("*"):
        if not target_object.is_file() or target_object.is_symlink():
            continue
        source_object = source_objects / target_object.relative_to(target_objects)
        if not source_object.is_file() or source_object.is_symlink():
            continue
        matching_object_files += 1
        assert not target_object.samefile(source_object)
    assert matching_object_files > 0
    assert git_text(history_target, "status", "--porcelain=v1")
    assert run(["git", "rev-parse", "--verify", "HEAD"], cwd=history_target).returncode != 0
    assert git_text(
        history_source, "status", "--porcelain=v1", "--untracked-files=all"
    ) == source_status_before
    assert (source_index.read_bytes(), source_index.stat().st_mtime_ns) == source_index_before
    assert snapshot(history_source) == source_tree_before
    assert snapshot(history_repository) == source_repository_before

validator_spec = importlib.util.spec_from_file_location(
    "migration_400_status_authority", PROJECT_VALIDATOR
)
validator = importlib.util.module_from_spec(validator_spec)
validator_spec.loader.exec_module(validator)
status_400 = source_status(accepted=False)
status_400.update(
    {
        "status_schema_version": "4.0.0",
        "lccoding_applicability": "PENDING",
        "product_service_strategy": "PENDING",
        "service_route_map": "PENDING",
    }
)
assert validator.validate_security_status_shape(status_400) == []
for field, bad_value in (
    ("lccoding_applicability", "OTHER_METHOD_RECOMMENDED"),
    ("product_service_strategy", "EVERY_ROUTE"),
    ("service_route_map", "DELIVERED"),
):
    malformed = copy.deepcopy(status_400)
    malformed[field] = bad_value
    assert validator.validate_security_status_shape(malformed), (field, bad_value)
missing_summary = copy.deepcopy(status_400)
missing_summary.pop("service_route_map")
assert validator.validate_security_status_shape(missing_summary)
unknown_summary = copy.deepcopy(status_400)
unknown_summary["second_route_authority"] = "PENDING"
assert validator.validate_security_status_shape(unknown_summary)
scalar_security_bypass = copy.deepcopy(status_400)
scalar_security_bypass["vulnerability_closure"] = "PENDING"
scalar_security_bypass["post_security_owner_acceptance"] = "PENDING"
assert validator.validate_security_status_shape(scalar_security_bypass)
assert validator.validate_security_status_shape(source_status(accepted=False)) == []

# The migration remains usable after the active status template is promoted by
# the later release task; exact 3.0 source shape still comes from the legacy
# fields, while reset defaults may come from the structurally compatible 4.0
# template.
migrator_spec = importlib.util.spec_from_file_location("migration_300_to_400", MIGRATOR)
migrator = importlib.util.module_from_spec(migrator_spec)
migrator_spec.loader.exec_module(migrator)
with tempfile.TemporaryDirectory(prefix="migration-promoted-template-") as temporary:
    promoted_root = Path(temporary)
    promoted_source = promoted_root / "source-300"
    make_source(promoted_source, accepted=False)
    promoted_template = strict_json(TEMPLATES / "STATUS.json")
    promoted_template.update(
        {
            "status_schema_version": "4.0.0",
            "lccoding_applicability": "PENDING",
            "product_service_strategy": "PENDING",
            "service_route_map": "PENDING",
        }
    )
    promoted_template_path = promoted_root / "STATUS-400.json"
    write(promoted_template_path, json.dumps(promoted_template, indent=2) + "\n")
    migrator.STATUS_TEMPLATE_PATH = promoted_template_path
    migrated_source, _, reset_template, _ = migrator.validate_source(promoted_source)
    promoted_status = migrator.migrated_status(migrated_source, reset_template)
    assert promoted_status["status_schema_version"] == "4.0.0"
    assert set(promoted_status) == set(promoted_template)

changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
assert "3.0.0-to-4.0.0" in changelog
assert "Personal Agent or Service Center delivery" in changelog

print("PASS: 3.0 to 4.0 migration is copy-on-write, atomic, and route conservative")
