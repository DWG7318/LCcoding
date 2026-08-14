from pathlib import Path
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile


root = Path(__file__).resolve().parents[2]
migrator = root / "lc-coding/scripts/migrate_project_260_to_270.py"
assert migrator.exists(), "2.6 to 2.7 migration command is absent"


def run(command, cwd=None, check=True):
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return result


def git(repo, *arguments, text=True):
    return subprocess.run(
        ["git", *arguments], cwd=repo, capture_output=True, text=text, check=True
    ).stdout


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def canonical_subtree_hash(repo, commit, subtree):
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
        mode, object_type, object_id = metadata.split(b" ")
        assert object_type == b"blob"
        blob = git(repo, "cat-file", "blob", object_id.decode("ascii"), text=False)
        entries.append((path, mode, hashlib.sha256(blob).hexdigest().encode("ascii")))
    manifest = b"".join(
        path + b"\0" + mode + b"\0" + digest + b"\n"
        for path, mode, digest in sorted(entries)
    )
    return "sha256:" + hashlib.sha256(manifest).hexdigest()


def workflow_map(content_hash):
    return f"""# Workflow Map

- Primary product mainline ID: MAINLINE-PRIMARY

| Workflow ID | Classification (CORE/EXTRA) | Implementation status | Subtree path | Component version | Content hash | Actors | Trigger | States / rules | Data / permissions | Failure / recovery | API contract / evidence | MCP contract / evidence | UI subtree references | Simulation subtree references | Evidence / attestation | Calabash trace | Primary mainline |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| WF-CORE | CORE | IMPLEMENTED | product/workflows/core | 1.0.0 | {content_hash} | Owner | Invoke | Defined | Defined | Defined | API-WF / D2-API | MCP-WF / D2-MCP | UI-MAIN | SIM-MAIN | D2-WF | CAL-1 | YES |
"""


def ui_map(content_hash):
    return f"""# UI Map

- Primary product mainline ID: MAINLINE-PRIMARY

| UI ID | Subtree path | Component version | Content hash | Actor | Surface / state | Actions / feedback | Workflow subtree references | Simulation subtree references | Evidence / attestation | Lock status | Primary mainline |
|---|---|---|---|---|---|---|---|---|---|---|---|
| UI-MAIN | product/ui/main | 1.0.0 | {content_hash} | Owner | Main | Invoke | WF-CORE | SIM-MAIN | D2-UI | LOCKED | YES |
"""


def simulation_map(content_hash):
    return f"""# Simulation World

- Primary product mainline ID: MAINLINE-PRIMARY

## Simulation subtree registry

| Simulation ID | Subtree path | Component version | Content hash | Foundation status | Workflow subtree references | UI subtree references | Primary mainline |
|---|---|---|---|---|---|---|---|
| SIM-MAIN | product/simulations/main | 1.0.0 | {content_hash} | RUNNABLE | WF-CORE | UI-MAIN | YES |

## Scenario registry

| Simulation ID | Scenario ID | Actors | Data/state/time | Path | Failure/recovery | Fidelity | Visible / invisible evidence | Used by Slice/Run/Acceptance | Scenario version |
|---|---|---|---|---|---|---|---|---|---|
"""


def definition_handoff():
    return """# Calabash Definition Handoff

- Artifact role: CALABASH_DEFINITION_HANDOFF
- Definition Handoff ID: CDH-MIGRATION
- Definition Baseline kind: CALABASH_DEFINITION_BASELINE
- Definition Baseline ID: DB-MIGRATION
- Definition Baseline semantic version: 1.0.0
- Definition Baseline exact hash: sha256:1111111111111111111111111111111111111111111111111111111111111111
- Calabash standard version: 2.5.0
- Baseline status: FROZEN
- Applicable Definition clause references: baseline:/grandpa/product
- Snake review status: NONE_IDENTIFIED
- Snake review scope: Grandpa
- Snake review evidence refs: E-SNAKE-REVIEW
- Scorpion review status: NONE_IDENTIFIED
- Scorpion review scope: Grandpa
- Scorpion review evidence refs: E-SCORPION-REVIEW
- Meaning-change / invalidation rules reference: CAL-CHANGE-1
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


def product_handoff(commit, hashes, definition_hash, *, valid=True):
    confirmation = "OWNER_CONFIRMED: OA-PB-1" if valid else "OWNER_CONFIRMED:"
    return f"""# Product Baseline Handoff

- Baseline ID / version / hash: PB-1 / 1.0.0 / E-PB
- Project repository identity: github.com/example/project
- Project frozen exact commit SHA: {commit}
- Calabash source: CAL-1
- Calabash Definition Handoff ID / exact hash: CDH-MIGRATION / {definition_hash}
- Calabash Definition Handoff result: PASS
- Workflow Map: .lccoding/WORKFLOW-MAP.md
- UI Map: .lccoding/UI-MAP.md
- Simulation World: .lccoding/SIMULATION-WORLD.md
- Primary product mainline ID: MAINLINE-PRIMARY
- Primary mainline Owner confirmation: {confirmation}
- Handoff status: COMPLETE

## Locked logical subtrees

| Subtree type | Subtree ID | Path | Component version | Content hash | Classification | API evidence | MCP evidence | Primary mainline | Related subtree IDs |
|---|---|---|---|---|---|---|---|---|---|
| UI | UI-MAIN | product/ui/main | 1.0.0 | {hashes['UI']} | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | YES | WF-CORE, SIM-MAIN |
| WORKFLOW | WF-CORE | product/workflows/core | 1.0.0 | {hashes['WORKFLOW']} | CORE | API-WF / D2-API | MCP-WF / D2-MCP | YES | UI-MAIN, SIM-MAIN |
| SIMULATION | SIM-MAIN | product/simulations/main | 1.0.0 | {hashes['SIMULATION']} | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | YES | WF-CORE, UI-MAIN |
"""


def receipt(
    acceptance_id,
    run_id,
    *,
    phase="ENGINEERING_RUNS",
    owner_result="LOOP_OWNER_ACCEPTED",
    gap=None,
    complete=True,
):
    gap_fields = ""
    if gap:
        gap_fields = f"""- Owner Gap ID: {gap}
- Gap source Acceptance ID: {acceptance_id}
- Gap source candidate / scenario: CANDIDATE-1 / SCENARIO-1
- Gap route: IMPACT_CORRECTION
- Gap status: OPEN
"""
    terminal_fields = ""
    if complete:
        terminal_fields = """- Feature Slice ID / version (when applicable): FS-1 / 1.0.0
- Candidate ID / hash: PB-1 / E-CANDIDATE
- D3 Receipt: D3-{run_id}
- Evidence return target in the calling phase: FS-1 / Product Integration evidence
- Accepted at: 2026-08-12T00:00:00Z
""".format(run_id=run_id)
    return f"""# Loop Owner Acceptance

- Acceptance ID: {acceptance_id}
- Run ID: {run_id}
- LCCoding phase scope: {phase}
{terminal_fields}- Calling phase gate remains independently evaluated: YES
- Owner result: {owner_result}
{gap_fields}"""


def feature_slice(commit, ui_hash, required_runs):
    return f"""# Feature Slice

- Slice ID / version: FS-1 / 1.0.0
- Actor intent: exercise real capability
- Product outcome: visible result
- Product Baseline trace: PB-1
- Workflow references: WF-CORE
- UI references: UI-MAIN
- Primary product mainline ID / Owner confirmation: MAINLINE-PRIMARY / OWNER_CONFIRMED
- Project repository / exact baseline commit: github.com/example/project :: {commit}
- Applicable UI subtree ID / path: UI-MAIN :: product/ui/main
- UI component version: 1.0.0
- UI content hash: {ui_hash}
- UI content hash scope / manifest evidence: HASH_SCOPE: frozen subtree
- UI Product / Integration Baseline identity: MATCH: PB-1
- UI subtree comparison before Slice / Run: MATCH: D2-UI
- UI comparison before acceptance route: REQUIRED
- Scenario IDs / versions: SCENARIO-1 / 1.0.0
- State / data / permission trace: E-STATE
- Exception / recovery trace: E-RECOVERY
- Impact Analysis ID: IA-1
- Integration Baseline ID: IB-1
- Required Run IDs: {', '.join(required_runs)}
- D0-D3 evidence plan: D0-D3-PLAN
- Normal Loop Owner Acceptance route(s): OA-ROUTE
- Execution Coverage Preflight: PASS
- Coverage gaps / unknowns: NONE
- Cross-layer connection evidence: PROVEN: D3-E2E
- First Proving Run requirement: NOT_REQUIRED
- Failure expansion rule: HALT_EXPANSION
- Fingerprint depth response: CONCISE_TRUTHFUL
"""


def phase_view_for(status):
    view = copy.deepcopy(
        json.loads((root / "lc-coding/templates/PHASE-STATUS.json").read_text(encoding="utf-8"))
    )
    view["status_schema_version"] = "2.6.0"
    phase3 = view["phases"].pop("REAL_PRODUCT_INTEGRATION")
    view["phases"] = {
        "INITIAL": view["phases"]["INITIAL"],
        "PRODUCT_FORMATION": view["phases"]["PRODUCT_FORMATION"],
        "ENGINEERING_RUNS": phase3,
        "DELIVERY_PREPARATION": view["phases"]["DELIVERY_PREPARATION"],
    }
    view["current_phase"] = status["current_phase"]
    view["phases"]["INITIAL"]["exit_gate"] = status["phase_gates"]["INITIAL_READY"]
    view["phases"]["PRODUCT_FORMATION"]["exit_evidence"] = status["product_baseline"]
    view["phases"]["ENGINEERING_RUNS"]["aggregate_exit_gate"] = status[
        "phase_gates"
    ]["ALL_REQUIRED_RUNS_ACCEPTED"]
    view["phases"]["DELIVERY_PREPARATION"]["exit_gate"] = status["phase_gates"][
        "DELIVERY_READY"
    ]
    return view


def make_project(
    project,
    *,
    initial_ready="PASS",
    calabash_draft="COMPLETE",
    workflow="COMPLETE",
    ui="COMPLETE",
    simulation="COMPLETE",
    mandatory_upgrade="COMPLETE",
    product_baseline="PENDING",
    handoff=None,
    aggregate="PENDING",
    direct_aggregate=None,
    required_runs=None,
    acceptances=(),
    current_phase="INITIAL",
    delivery_ready="PENDING",
    later_evidence_done=False,
    delivery_state=None,
):
    project.mkdir(parents=True)
    git(project, "init", "--quiet")
    git(project, "config", "user.email", "lccoding-test@example.invalid")
    git(project, "config", "user.name", "LCCoding Test")
    product_files = {
        "product/ui/main/index.html": "<main>UI</main>\n",
        "product/workflows/core/workflow.py": "def run(): return 'ok'\n",
        "product/simulations/main/world.json": '{"state":"ready"}\n',
    }
    for relative, content in product_files.items():
        write(project / relative, content)
    git(project, "add", "product")
    git(project, "commit", "--quiet", "-m", "freeze product subtrees")
    commit = git(project, "rev-parse", "HEAD").strip()
    hashes = {
        "UI": canonical_subtree_hash(project, commit, "product/ui/main"),
        "WORKFLOW": canonical_subtree_hash(project, commit, "product/workflows/core"),
        "SIMULATION": canonical_subtree_hash(project, commit, "product/simulations/main"),
    }

    lc = project / ".lccoding"
    for name in ("OWNER-POLICY.md", "PROJECT-PROFILE.md", "AGENT-RULE.md"):
        write(lc / name, "# Evidence\n")
    fingerprint = {
        "complexity": {
            key: "LOW"
            for key in (
                "product_uncertainty",
                "system_coupling",
                "real_risk",
                "irreversibility",
                "novelty",
            )
        },
        "depth": {"rationale": "", "analysis": [], "materials": [], "evidence": []},
    }
    records = {
        "PROJECT-START.json": {
            "initialization_mode": "NEW",
            "repository": "github.com/example/project",
        },
        "PROJECT-FINGERPRINT.json": fingerprint,
        "PROJECT-HEALTH.json": {
            "record_role": "ASSESSMENT_EVIDENCE",
            "initialization_mode": "NEW",
        },
        "CANONICAL-MANIFEST.json": {},
        "INTERPRETATION-LOCK.json": {"status": "VALID"},
    }
    for name, value in records.items():
        write(lc / name, json.dumps(value, ensure_ascii=False) + "\n")
    write(lc / "WORKFLOW-MAP.md", workflow_map(hashes["WORKFLOW"]))
    write(lc / "UI-MAP.md", ui_map(hashes["UI"]))
    write(lc / "SIMULATION-WORLD.md", simulation_map(hashes["SIMULATION"]))
    gate = lc / "CALABASH-UPGRADE-GATE.md"
    write(gate, definition_handoff())
    definition_hash = "sha256:" + hashlib.sha256(gate.read_bytes()).hexdigest()
    write(project / "VERSION", "1.0.0\n")

    status = copy.deepcopy(
        json.loads((root / "lc-coding/templates/STATUS.json").read_text(encoding="utf-8"))
    )
    status["status_schema_version"] = "2.6.0"
    status["project_id"] = "migration-fixture"
    status["initialization_mode"] = "NEW"
    status["current_phase"] = current_phase
    status["phase_gates"]["INITIAL_READY"] = initial_ready
    status["phase_gates"]["CALABASH_UPGRADE_READY"] = (
        "PASS" if mandatory_upgrade == "COMPLETE" else "PENDING"
    )
    status["phase_gates"]["ALL_REQUIRED_RUNS_ACCEPTED"] = aggregate
    status["phase_gates"]["DELIVERY_READY"] = delivery_ready
    status["product_baseline"] = product_baseline
    status["initialization"] = "COMPLETE" if initial_ready == "PASS" else "PENDING"
    status["calabash_draft"] = calabash_draft
    status["workflow"] = workflow
    status["ui"] = ui
    status["simulation"] = simulation
    status["mandatory_calabash_upgrade"] = mandatory_upgrade
    status["all_required_runs_accepted"] = (
        aggregate if direct_aggregate is None else direct_aggregate
    )
    if required_runs is not None:
        status["active_slice"] = "FS-1"
        write(lc / "slices/FS-1.md", feature_slice(commit, hashes["UI"], required_runs))
    if acceptances:
        status["loop_owner_acceptances"] = [
            acceptance["acceptance_id"] for acceptance in acceptances
        ]
        for acceptance in acceptances:
            acceptance_id = acceptance["acceptance_id"]
            write(
                lc / "reviews" / f"{acceptance_id}.md",
                receipt(
                    acceptance_id,
                    acceptance["run_id"],
                    phase=acceptance.get("phase", "ENGINEERING_RUNS"),
                    owner_result=acceptance.get("owner_result", "LOOP_OWNER_ACCEPTED"),
                    gap=acceptance.get("gap"),
                    complete=acceptance.get("complete", True),
                ),
            )
            if acceptance.get("gap"):
                status["open_owner_gaps"].append(
                    {
                        "gap_id": acceptance["gap"],
                        "state": "OPEN",
                        "source_acceptance": acceptance_id,
                        "evidence_pointers": [f"reviews/{acceptance_id}.md"],
                    }
                )
    if later_evidence_done:
        for field in (
            "centralized_security_audit",
            "security_remediation",
            "vulnerability_closure",
            "post_security_owner_acceptance",
            "delivery_method_qa",
        ):
            status[field] = "DONE"
        status["delivery"] = "DONE" if delivery_state is None else delivery_state
    elif delivery_state is not None:
        status["delivery"] = delivery_state
    write(lc / "status.json", json.dumps(status, indent=2) + "\n")
    write(lc / "PHASE-STATUS.json", json.dumps(phase_view_for(status), indent=2) + "\n")
    if handoff is not None:
        write(
            lc / "PRODUCT-BASELINE-HANDOFF.md",
            product_handoff(commit, hashes, definition_hash, valid=handoff),
        )
    return status


def snapshot(project):
    return {
        path.relative_to(project).as_posix(): (
            "directory" if path.is_dir() else "file",
            None if path.is_dir() else path.read_bytes(),
            path.stat().st_mtime_ns,
        )
        for path in project.rglob("*")
    }


def migrate(source, output):
    return run(
        [sys.executable, str(migrator), "--project", str(source), "--output", str(output)],
        check=False,
    )


def assert_source_unchanged(source, before):
    assert snapshot(source) == before


def assert_destination(output, phase, baseline, aggregate):
    migrated_status = json.loads((output / ".lccoding/status.json").read_text(encoding="utf-8"))
    migrated_view = json.loads(
        (output / ".lccoding/PHASE-STATUS.json").read_text(encoding="utf-8")
    )
    assert migrated_status["status_schema_version"] == "2.7.0"
    assert migrated_status["record_role"] == "AUTHORITATIVE_PROJECT_STATUS"
    assert migrated_status["current_phase"] == phase
    assert migrated_status["product_baseline"] == baseline
    assert migrated_status["phase_gates"]["ALL_REQUIRED_RUNS_ACCEPTED"] == aggregate
    assert "PRODUCT_BASELINE_READY" not in json.dumps(migrated_status)
    assert migrated_view["record_role"] == "DERIVED_VIEW"
    assert migrated_view["derived_from"] == "status.json"
    assert migrated_view["current_phase"] == phase
    referenced_phase3_acceptances = []
    for acceptance_id in migrated_status["loop_owner_acceptances"]:
        acceptance_path = output / ".lccoding/reviews" / f"{acceptance_id}.md"
        if acceptance_path.is_file() and (
            "- LCCoding phase scope: ENGINEERING_RUNS"
            in acceptance_path.read_text(encoding="utf-8")
        ):
            referenced_phase3_acceptances.append(acceptance_id)
    assert migrated_view["phases"]["ENGINEERING_RUNS"][
        "per_run_acceptances"
    ] == referenced_phase3_acceptances
    phase_check = run(
        [
            sys.executable,
            str(root / "lc-coding/scripts/validate_phase_status.py"),
            str(output / ".lccoding/PHASE-STATUS.json"),
        ],
        check=False,
    )
    assert phase_check.returncode == 0, phase_check.stdout + phase_check.stderr
    project_check = run(
        [sys.executable, str(root / "lc-coding/scripts/validate_project.py"), str(output)],
        check=False,
    )
    assert project_check.returncode == 0, project_check.stdout + project_check.stderr


def assert_non_status_bytes_equal(source, output):
    excluded = {".lccoding/status.json", ".lccoding/PHASE-STATUS.json"}
    source_files = snapshot(source)
    output_files = snapshot(output)
    for relative, record in source_files.items():
        if relative not in excluded and record[0] == "file":
            assert output_files[relative] == record, relative


with tempfile.TemporaryDirectory(prefix="lccoding-migration-270-") as temporary:
    base = Path(temporary)

    initial = base / "initial-source"
    make_project(initial, initial_ready="PENDING", calabash_draft="PENDING", mandatory_upgrade="PENDING")
    before = snapshot(initial)
    initial_output = base / "initial-output"
    result = migrate(initial, initial_output)
    assert result.returncode == 0, result.stdout + result.stderr
    assert_destination(initial_output, "INITIAL", "PENDING", "PENDING")
    assert_source_unchanged(initial, before)
    assert_non_status_bytes_equal(initial, initial_output)

    formation = base / "formation-source"
    make_project(formation, mandatory_upgrade="ACTIVE")
    before = snapshot(formation)
    formation_output = base / "formation-output"
    result = migrate(formation, formation_output)
    assert result.returncode == 0, result.stdout + result.stderr
    assert_destination(formation_output, "PRODUCT_FORMATION", "PENDING", "PENDING")
    assert_source_unchanged(formation, before)

    readiness_only = base / "readiness-only-source"
    make_project(readiness_only, mandatory_upgrade="COMPLETE", product_baseline="PENDING")
    readiness_output = base / "readiness-only-output"
    result = migrate(readiness_only, readiness_output)
    assert result.returncode == 0, result.stdout + result.stderr
    assert_destination(readiness_output, "PRODUCT_FORMATION", "PENDING", "PENDING")

    missing_handoff = base / "missing-handoff-source"
    make_project(missing_handoff, product_baseline="ACCEPTED")
    missing_output = base / "missing-handoff-output"
    result = migrate(missing_handoff, missing_output)
    assert result.returncode == 0, result.stdout + result.stderr
    assert_destination(missing_output, "PRODUCT_FORMATION", "BLOCKED", "PENDING")

    invalid_handoff = base / "invalid-handoff-source"
    make_project(invalid_handoff, product_baseline="ACCEPTED", handoff=False)
    invalid_before = snapshot(invalid_handoff)
    invalid_output = base / "invalid-handoff-output"
    result = migrate(invalid_handoff, invalid_output)
    assert result.returncode != 0
    assert not invalid_output.exists()
    assert_source_unchanged(invalid_handoff, invalid_before)
    assert not list(base.glob(".invalid-handoff-output.lccoding-migrate-*"))

    contradictory_formation = base / "contradictory-formation-source"
    make_project(
        contradictory_formation,
        mandatory_upgrade="ACTIVE",
        product_baseline="ACCEPTED",
        handoff=True,
    )
    contradictory_formation_output = base / "contradictory-formation-output"
    result = migrate(contradictory_formation, contradictory_formation_output)
    assert result.returncode == 0, result.stdout + result.stderr
    assert_destination(
        contradictory_formation_output, "PRODUCT_FORMATION", "BLOCKED", "PENDING"
    )

    baseline = base / "baseline-source"
    make_project(baseline, product_baseline="ACCEPTED", handoff=True)
    before = snapshot(baseline)
    baseline_output = base / "baseline-output"
    result = migrate(baseline, baseline_output)
    assert result.returncode == 0, result.stdout + result.stderr
    assert_destination(baseline_output, "ENGINEERING_RUNS", "ACCEPTED", "PENDING")
    assert_source_unchanged(baseline, before)
    assert_non_status_bytes_equal(baseline, baseline_output)

    arbitrary_receipt = base / "arbitrary-receipt-source"
    make_project(
        arbitrary_receipt,
        product_baseline="ACCEPTED",
        handoff=True,
        aggregate="ALL_REQUIRED_RUNS_ACCEPTED",
        acceptances=({"acceptance_id": "OA-ARBITRARY", "run_id": "R-ARBITRARY"},),
    )
    arbitrary_output = base / "arbitrary-receipt-output"
    result = migrate(arbitrary_receipt, arbitrary_output)
    assert result.returncode == 0, result.stdout + result.stderr
    assert_destination(arbitrary_output, "ENGINEERING_RUNS", "ACCEPTED", "BLOCKED")

    shell_receipt = base / "shell-receipt-source"
    make_project(
        shell_receipt,
        product_baseline="ACCEPTED",
        handoff=True,
        aggregate="ALL_REQUIRED_RUNS_ACCEPTED",
        required_runs=("R1",),
        acceptances=(
            {"acceptance_id": "OA-R1", "run_id": "R1", "complete": False},
        ),
    )
    shell_output = base / "shell-receipt-output"
    result = migrate(shell_receipt, shell_output)
    assert result.returncode == 0, result.stdout + result.stderr
    assert_destination(shell_output, "ENGINEERING_RUNS", "ACCEPTED", "BLOCKED")

    delivery = base / "delivery-source"
    exact_acceptances = (
        {"acceptance_id": "OA-PHASE3-1", "run_id": "R1"},
        {"acceptance_id": "OA-PHASE3-2", "run_id": "R2"},
    )
    make_project(
        delivery,
        product_baseline="ACCEPTED",
        handoff=True,
        aggregate="ALL_REQUIRED_RUNS_ACCEPTED",
        required_runs=("R1", "R2"),
        acceptances=exact_acceptances,
    )
    receipt_bytes = {
        acceptance["acceptance_id"]: (
            delivery / ".lccoding/reviews" / f"{acceptance['acceptance_id']}.md"
        ).read_bytes()
        for acceptance in exact_acceptances
    }
    before = snapshot(delivery)
    delivery_output = base / "delivery-output"
    result = migrate(delivery, delivery_output)
    assert result.returncode == 0, result.stdout + result.stderr
    assert_destination(
        delivery_output,
        "DELIVERY_PREPARATION",
        "ACCEPTED",
        "ALL_REQUIRED_RUNS_ACCEPTED",
    )
    for acceptance_id, content in receipt_bytes.items():
        assert (delivery_output / ".lccoding/reviews" / f"{acceptance_id}.md").read_bytes() == content
    assert_source_unchanged(delivery, before)

    mixed_phase = base / "mixed-phase-source"
    mixed_acceptances = exact_acceptances + (
        {
            "acceptance_id": "OA-FORM",
            "run_id": "PF-RUN",
            "phase": "PRODUCT_FORMATION",
        },
    )
    make_project(
        mixed_phase,
        product_baseline="ACCEPTED",
        handoff=True,
        aggregate="ALL_REQUIRED_RUNS_ACCEPTED",
        required_runs=("R1", "R2"),
        acceptances=mixed_acceptances,
    )
    unrelated_bytes = (mixed_phase / ".lccoding/reviews/OA-FORM.md").read_bytes()
    mixed_output = base / "mixed-phase-output"
    result = migrate(mixed_phase, mixed_output)
    assert result.returncode == 0, result.stdout + result.stderr
    assert_destination(
        mixed_output,
        "DELIVERY_PREPARATION",
        "ACCEPTED",
        "ALL_REQUIRED_RUNS_ACCEPTED",
    )
    mixed_status = json.loads(
        (mixed_output / ".lccoding/status.json").read_text(encoding="utf-8")
    )
    assert mixed_status["loop_owner_acceptances"] == [
        "OA-PHASE3-1",
        "OA-PHASE3-2",
        "OA-FORM",
    ]
    assert (mixed_output / ".lccoding/reviews/OA-FORM.md").read_bytes() == unrelated_bytes

    invalid_aggregates = {
        "missing": {
            "required_runs": ("R1", "R2"),
            "acceptances": ({"acceptance_id": "OA-R1", "run_id": "R1"},),
        },
        "extra": {
            "required_runs": ("R1",),
            "acceptances": (
                {"acceptance_id": "OA-R1", "run_id": "R1"},
                {"acceptance_id": "OA-R2", "run_id": "R2"},
            ),
        },
        "duplicate-run": {
            "required_runs": ("R1", "R2"),
            "acceptances": (
                {"acceptance_id": "OA-R1-A", "run_id": "R1"},
                {"acceptance_id": "OA-R1-B", "run_id": "R1"},
            ),
        },
        "wrong-phase": {
            "required_runs": ("R1",),
            "acceptances": (
                {
                    "acceptance_id": "OA-R1",
                    "run_id": "R1",
                    "phase": "PRODUCT_FORMATION",
                },
            ),
        },
        "wrong-result": {
            "required_runs": ("R1",),
            "acceptances": (
                {
                    "acceptance_id": "OA-R1",
                    "run_id": "R1",
                    "owner_result": "LOOP_PRODUCT_REWORK",
                },
            ),
        },
        "open-gap": {
            "required_runs": ("R1",),
            "acceptances": (
                {"acceptance_id": "OA-R1", "run_id": "R1", "gap": "GAP-1"},
            ),
        },
        "aggregate-mismatch": {
            "required_runs": ("R1",),
            "direct_aggregate": "PENDING",
            "acceptances": ({"acceptance_id": "OA-R1", "run_id": "R1"},),
        },
    }
    for name, options in invalid_aggregates.items():
        source = base / f"{name}-source"
        output = base / f"{name}-output"
        make_project(
            source,
            product_baseline="ACCEPTED",
            handoff=True,
            aggregate="ALL_REQUIRED_RUNS_ACCEPTED",
            **options,
        )
        result = migrate(source, output)
        assert result.returncode == 0, name + result.stdout + result.stderr
        assert_destination(output, "ENGINEERING_RUNS", "ACCEPTED", "BLOCKED")

    completed_delivery = base / "completed-delivery-source"
    make_project(
        completed_delivery,
        product_baseline="ACCEPTED",
        handoff=True,
        aggregate="ALL_REQUIRED_RUNS_ACCEPTED",
        required_runs=("R1", "R2"),
        acceptances=exact_acceptances,
        current_phase="DELIVERY_PREPARATION",
        delivery_ready="DELIVERY_READY",
        later_evidence_done=True,
    )
    completed_delivery_output = base / "completed-delivery-output"
    result = migrate(completed_delivery, completed_delivery_output)
    assert result.returncode == 0, result.stdout + result.stderr
    assert_destination(
        completed_delivery_output,
        "DELIVERY_PREPARATION",
        "ACCEPTED",
        "ALL_REQUIRED_RUNS_ACCEPTED",
    )
    completed_status = json.loads(
        (completed_delivery_output / ".lccoding/status.json").read_text(encoding="utf-8")
    )
    assert completed_status["phase_gates"]["DELIVERY_READY"] == "DELIVERY_READY"
    for field in (
        "centralized_security_audit",
        "security_remediation",
        "vulnerability_closure",
        "post_security_owner_acceptance",
        "delivery_method_qa",
        "delivery",
    ):
        assert completed_status[field] == "DONE"

    ready_before_delivery = base / "ready-before-delivery-source"
    make_project(
        ready_before_delivery,
        product_baseline="ACCEPTED",
        handoff=True,
        aggregate="ALL_REQUIRED_RUNS_ACCEPTED",
        required_runs=("R1", "R2"),
        acceptances=exact_acceptances,
        current_phase="DELIVERY_PREPARATION",
        delivery_ready="DELIVERY_READY",
        later_evidence_done=True,
        delivery_state="PENDING",
    )
    ready_before_delivery_output = base / "ready-before-delivery-output"
    result = migrate(ready_before_delivery, ready_before_delivery_output)
    assert result.returncode == 0, result.stdout + result.stderr
    assert_destination(
        ready_before_delivery_output,
        "DELIVERY_PREPARATION",
        "ACCEPTED",
        "ALL_REQUIRED_RUNS_ACCEPTED",
    )
    ready_status = json.loads(
        (ready_before_delivery_output / ".lccoding/status.json").read_text(
            encoding="utf-8"
        )
    )
    assert ready_status["phase_gates"]["DELIVERY_READY"] == "DELIVERY_READY"
    assert ready_status["delivery"] == "PENDING"

    delivery_before_ready = base / "delivery-before-ready-source"
    make_project(
        delivery_before_ready,
        product_baseline="ACCEPTED",
        handoff=True,
        aggregate="ALL_REQUIRED_RUNS_ACCEPTED",
        required_runs=("R1", "R2"),
        acceptances=exact_acceptances,
        current_phase="DELIVERY_PREPARATION",
        delivery_ready="PENDING",
        later_evidence_done=True,
        delivery_state="DONE",
    )
    delivery_before_ready_before = snapshot(delivery_before_ready)
    delivery_before_ready_output = base / "delivery-before-ready-output"
    result = migrate(delivery_before_ready, delivery_before_ready_output)
    assert result.returncode != 0
    assert not delivery_before_ready_output.exists()
    assert_source_unchanged(delivery_before_ready, delivery_before_ready_before)

    contradictory_delivery = base / "contradictory-delivery-source"
    make_project(
        contradictory_delivery,
        product_baseline="ACCEPTED",
        handoff=True,
        aggregate="ALL_REQUIRED_RUNS_ACCEPTED",
        required_runs=("R1", "R2"),
        acceptances=exact_acceptances,
        current_phase="DELIVERY_PREPARATION",
        delivery_ready="DELIVERY_READY",
        later_evidence_done=False,
    )
    contradictory_delivery_before = snapshot(contradictory_delivery)
    contradictory_delivery_output = base / "contradictory-delivery-output"
    result = migrate(contradictory_delivery, contradictory_delivery_output)
    assert result.returncode != 0
    assert not contradictory_delivery_output.exists()
    assert_source_unchanged(contradictory_delivery, contradictory_delivery_before)

    malformed = base / "malformed-source"
    make_project(malformed)
    malformed_before = snapshot(malformed)
    write(malformed / ".lccoding/INTERPRETATION-LOCK.json", '{"status":"INVALID"}\n')
    malformed_before = snapshot(malformed)
    malformed_output = base / "malformed-output"
    result = migrate(malformed, malformed_output)
    assert result.returncode != 0
    assert not malformed_output.exists()
    assert_source_unchanged(malformed, malformed_before)
    stages = list(base.glob(".malformed-output.lccoding-migrate-*"))
    assert not stages, stages

    for label, schema in (
        ("missing-derived-schema", None),
        ("wrong-derived-schema", "2.5.2"),
        ("cross-derived-schema", "2.7.0"),
    ):
        source = base / (label + "-source")
        make_project(source)
        phase_path = source / ".lccoding/PHASE-STATUS.json"
        phase_record = json.loads(phase_path.read_text(encoding="utf-8"))
        if schema is None:
            phase_record.pop("status_schema_version")
        else:
            phase_record["status_schema_version"] = schema
        write(phase_path, json.dumps(phase_record, indent=2) + "\n")
        before = snapshot(source)
        output = base / (label + "-output")
        result = migrate(source, output)
        assert result.returncode != 0 and not output.exists()
        assert "source PHASE-STATUS schema must be exact 2.6.0" in result.stdout
        assert_source_unchanged(source, before)

    unsupported = base / "unsupported-source"
    make_project(unsupported)
    unsupported_status_path = unsupported / ".lccoding/status.json"
    unsupported_status = json.loads(unsupported_status_path.read_text(encoding="utf-8"))
    unsupported_status["status_schema_version"] = "2.5.2"
    write(unsupported_status_path, json.dumps(unsupported_status) + "\n")
    unsupported_output = base / "unsupported-output"
    result = migrate(unsupported, unsupported_output)
    assert result.returncode != 0 and not unsupported_output.exists()

    unknown = base / "unknown-source"
    make_project(unknown)
    unknown_status_path = unknown / ".lccoding/status.json"
    unknown_status = json.loads(unknown_status_path.read_text(encoding="utf-8"))
    unknown_status["product_baseline"] = "UNKNOWN"
    write(unknown_status_path, json.dumps(unknown_status) + "\n")
    unknown_output = base / "unknown-output"
    result = migrate(unknown, unknown_output)
    assert result.returncode != 0 and not unknown_output.exists()

    existing_output = base / "existing-output"
    existing_output.mkdir()
    result = migrate(formation, existing_output)
    assert result.returncode != 0

    nested_output = formation / "nested-output"
    before = snapshot(formation)
    result = migrate(formation, nested_output)
    assert result.returncode != 0 and not nested_output.exists()
    assert_source_unchanged(formation, before)

    result = migrate(formation, formation)
    assert result.returncode != 0

    result = migrate(formation, base)
    assert result.returncode != 0

    linked_source = base / "linked-source"
    if os.name == "nt":
        junction = run(
            ["cmd", "/c", "mklink", "/J", str(linked_source), str(formation)],
            check=False,
        )
        assert junction.returncode == 0, junction.stdout + junction.stderr
    else:
        linked_source.symlink_to(formation, target_is_directory=True)
    linked_output = base / "linked-output"
    result = migrate(linked_source, linked_output)
    assert result.returncode != 0 and not linked_output.exists()

print("PASS: 2.6 project status migration is copy-on-write and evidence conservative")
