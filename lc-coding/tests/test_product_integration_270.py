from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile


root = Path(__file__).resolve().parents[2]
validator_path = root / "lc-coding/scripts/validate_project.py"
spec = importlib.util.spec_from_file_location("validate_project", validator_path)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def git(repo, *arguments):
    return subprocess.run(
        ["git", *arguments], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def authority(classification, suffix):
    return (
        f"CLASSIFICATION:{classification}; CALABASH:CAL-{suffix}; "
        f"OWNER_CONFIRMED:OA-{suffix}"
    )


def trace(suffix):
    return f"RULES:R-{suffix}; STATE:S-{suffix}; SIDE_EFFECTS:SE-{suffix}"


def interface(kind, capability, suffix):
    return f"CAPABILITY:{capability}; CONTRACT:{kind}-{suffix}; EVIDENCE:E-{kind}-{suffix}"


def workflow(
    workflow_id,
    classification,
    path,
    content_hash,
    capability,
    ui_refs,
    simulation_refs,
    *,
    primary="NO",
    implementation="IMPLEMENTED",
):
    suffix = workflow_id.removeprefix("WF-")
    if implementation == "UNIMPLEMENTED":
        path = content_hash = capability = "NOT_APPLICABLE"
        version = rules = api = mcp = implementation_evidence = "NOT_APPLICABLE"
        ui_refs = simulation_refs = "NONE"
    else:
        version = "1.0.0"
        rules = trace(suffix)
        api = interface("API", capability, suffix)
        mcp = interface("MCP", capability, suffix)
        implementation_evidence = (
            f"IMPLEMENTATION:E-IMPL-{suffix}; RUNNABLE:E-RUN-{suffix}"
        )
    return {
        "Workflow ID": workflow_id,
        "Classification (CORE/EXTRA)": classification,
        "Classification authority": authority(classification, suffix),
        "Implementation status": implementation,
        "Subtree path": path,
        "Component version": version,
        "Content hash": content_hash,
        "Workflow Capability ID": capability,
        "Rules / state / side-effect trace": rules,
        "API contract / evidence": api,
        "MCP contract / evidence": mcp,
        "UI subtree references": ui_refs,
        "Simulation subtree references": simulation_refs,
        "Evidence / attestation": implementation_evidence,
        "Primary mainline": primary,
    }


def ui(ui_id, path, content_hash, workflow_refs, simulation_refs, *, primary="NO"):
    return {
        "UI ID": ui_id,
        "Subtree path": path,
        "Component version": "1.0.0",
        "Content hash": content_hash,
        "Actor": "Owner",
        "Surface / state": "Surface",
        "Actions / feedback": "Action",
        "Workflow subtree references": workflow_refs,
        "Simulation subtree references": simulation_refs,
        "Evidence / attestation": f"E-{ui_id}",
        "Lock status": "LOCKED",
        "Primary mainline": primary,
    }


def simulation(simulation_id, path, content_hash, workflow_refs, ui_refs, *, primary="NO"):
    return {
        "Simulation ID": simulation_id,
        "Subtree path": path,
        "Component version": "1.0.0",
        "Content hash": content_hash,
        "Foundation status": "RUNNABLE",
        "Workflow subtree references": workflow_refs,
        "UI subtree references": ui_refs,
        "Primary mainline": primary,
    }


def locked_row(subtree_type, row):
    id_field = {"UI": "UI ID", "WORKFLOW": "Workflow ID", "SIMULATION": "Simulation ID"}[
        subtree_type
    ]
    relations = []
    for field in {
        "UI": ("Workflow subtree references", "Simulation subtree references"),
        "WORKFLOW": ("UI subtree references", "Simulation subtree references"),
        "SIMULATION": ("Workflow subtree references", "UI subtree references"),
    }[subtree_type]:
        relations.extend(
            token.strip()
            for token in row[field].split(",")
            if token.strip() and token.strip() != "NONE"
        )
    return {
        "Subtree type": subtree_type,
        "Subtree ID": row[id_field],
        "Path": row["Subtree path"],
        "Component version": row["Component version"],
        "Content hash": row["Content hash"],
        "Classification": row.get("Classification (CORE/EXTRA)", "NOT_APPLICABLE"),
        "Classification authority": row.get("Classification authority", "NOT_APPLICABLE"),
        "Workflow Capability ID": row.get("Workflow Capability ID", "NOT_APPLICABLE"),
        "API evidence": row.get("API contract / evidence", "NOT_APPLICABLE"),
        "MCP evidence": row.get("MCP contract / evidence", "NOT_APPLICABLE"),
        "Primary mainline": row["Primary mainline"],
        "Related subtree IDs": ", ".join(relations) if relations else "NONE",
    }


def baseline_rows(workflows, uis, simulations):
    rows = [locked_row("UI", row) for row in uis]
    rows += [
        locked_row("WORKFLOW", row)
        for row in workflows
        if row["Implementation status"] == "IMPLEMENTED"
    ]
    rows += [locked_row("SIMULATION", row) for row in simulations]
    return rows


def validate(repo, commit, workflows, uis, simulations, locked, *, mainline="MAINLINE-1", owner="OWNER_CONFIRMED: OA-MAINLINE", map_ids=None):
    errors = validator.validate_workflow_subtrees(workflows, repo, commit)
    errors += validator.validate_product_subtree_baseline(
        locked,
        mainline,
        owner,
        repo,
        commit,
        workflows,
        uis,
        simulations,
        map_ids
        or {"Workflow": "MAINLINE-1", "UI": "MAINLINE-1", "Simulation": "MAINLINE-1"},
    )
    return errors


def must_fail(repo, commit, workflows, uis, simulations, locked, label, **options):
    assert validate(repo, commit, workflows, uis, simulations, locked, **options), label


WORKFLOW_COLUMNS = [
    "Workflow ID", "Classification (CORE/EXTRA)", "Implementation status",
    "Classification authority", "Subtree path", "Component version", "Content hash",
    "Workflow Capability ID", "Actors", "Trigger", "Rules / state / side-effect trace",
    "Data / permissions", "Failure / recovery", "API contract / evidence",
    "MCP contract / evidence", "UI subtree references", "Simulation subtree references",
    "Evidence / attestation", "Primary mainline",
]
UI_COLUMNS = [
    "UI ID", "Subtree path", "Component version", "Content hash", "Actor",
    "Surface / state", "Actions / feedback", "Workflow subtree references",
    "Simulation subtree references", "Evidence / attestation", "Lock status",
    "Primary mainline",
]
SIMULATION_COLUMNS = [
    "Simulation ID", "Subtree path", "Component version", "Content hash",
    "Foundation status", "Workflow subtree references", "UI subtree references",
    "Primary mainline",
]
SCENARIO_COLUMNS = [
    "Simulation ID", "Scenario ID", "Actors", "Data/state/time", "Path",
    "Failure/recovery", "Fidelity", "Visible / invisible evidence",
    "Used by Slice/Run/Acceptance", "Scenario version",
]
HANDOFF_COLUMNS = [
    "Subtree type", "Subtree ID", "Path", "Component version", "Content hash",
    "Classification", "Classification authority", "Workflow Capability ID",
    "API evidence", "MCP evidence", "Primary mainline", "Related subtree IDs",
]


def table(columns, rows):
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "DEFINED")) for column in columns) + " |")
    return "\n".join(lines)


def definition_handoff():
    return """# Calabash Definition Handoff

- Artifact role: CALABASH_DEFINITION_HANDOFF
- Definition Handoff ID: CDH-TASK9
- Definition Baseline kind: CALABASH_DEFINITION_BASELINE
- Definition Baseline ID: DB-TASK9
- Definition Baseline semantic version: 1.0.0
- Definition Baseline exact hash: sha256:1111111111111111111111111111111111111111111111111111111111111111
- Calabash standard version: 2.5.0
- Baseline status: FROZEN
- Applicable Definition clause references: baseline:/grandpa/product
- Snake review status: NONE_IDENTIFIED
- Snake review scope: Grandpa
- Snake review evidence refs: E-SNAKE-TASK9
- Scorpion review status: NONE_IDENTIFIED
- Scorpion review scope: Grandpa
- Scorpion review evidence refs: E-SCORPION-TASK9
- Meaning-change / invalidation rules reference: CAL-CHANGE-TASK9
- Upgrade Receipt ID: UPGRADE-TASK9
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


def install_product_markdown_fixture(repo, commit, workflows, uis, simulations, locked):
    lc = repo / ".lccoding"
    for name in ("OWNER-POLICY.md", "PROJECT-PROFILE.md", "AGENT-RULE.md"):
        write(lc / name, "# Evidence\n")
    records = {
        "PROJECT-START.json": {"initialization_mode": "NEW", "repository": "github.com/example/project"},
        "PROJECT-FINGERPRINT.json": {
            "complexity": {
                key: "LOW"
                for key in ("product_uncertainty", "system_coupling", "real_risk", "irreversibility", "novelty")
            },
            "depth": {},
        },
        "PROJECT-HEALTH.json": {},
        "CANONICAL-MANIFEST.json": {},
        "INTERPRETATION-LOCK.json": {"status": "VALID"},
        "status.json": {},
        "PHASE-STATUS.json": {},
    }
    for name, record in records.items():
        write(lc / name, json.dumps(record, ensure_ascii=False) + "\n")
    write(repo / "VERSION", "1.0.0\n")
    gate = definition_handoff()
    write(lc / "CALABASH-UPGRADE-GATE.md", gate)
    gate_hash = "sha256:" + hashlib.sha256(gate.encode("utf-8")).hexdigest()
    write(
        lc / "WORKFLOW-MAP.md",
        "# Workflow Map\n\n- Primary product mainline ID: MAINLINE-1\n\n"
        + table(WORKFLOW_COLUMNS, workflows)
        + "\n",
    )
    write(
        lc / "UI-MAP.md",
        "# UI Map\n\n- Primary product mainline ID: MAINLINE-1\n\n"
        + table(UI_COLUMNS, uis)
        + "\n",
    )
    write(
        lc / "SIMULATION-WORLD.md",
        "# Simulation World\n\n- Primary product mainline ID: MAINLINE-1\n\n"
        "## Simulation subtree registry\n\n"
        + table(SIMULATION_COLUMNS, simulations)
        + "\n\n## Scenario registry\n\n"
        + table(SCENARIO_COLUMNS, [])
        + "\n",
    )
    write(
        lc / "PRODUCT-BASELINE-HANDOFF.md",
        "# Product Baseline Handoff\n\n"
        "- Baseline ID / version / hash: PB-TASK9 / 1.0.0 / E-PB-TASK9\n"
        "- Project repository identity: github.com/example/project\n"
        f"- Project frozen exact commit SHA: {commit}\n"
        "- Calabash source: CAL-TASK9\n"
        f"- Calabash Definition Handoff ID / exact hash: CDH-TASK9 / {gate_hash}\n"
        "- Calabash Definition Handoff result: PASS\n"
        "- Workflow Map: .lccoding/WORKFLOW-MAP.md\n"
        "- UI Map: .lccoding/UI-MAP.md\n"
        "- Simulation World: .lccoding/SIMULATION-WORLD.md\n"
        "- Primary product mainline ID: MAINLINE-1\n"
        "- Primary mainline Owner confirmation: OWNER_CONFIRMED: OA-MAINLINE\n"
        "- Handoff status: COMPLETE\n\n"
        "## Locked logical subtrees\n\n"
        + table(HANDOFF_COLUMNS, locked)
        + "\n",
    )


def validate_cli(repo):
    return subprocess.run(
        [sys.executable, str(validator_path), str(repo)],
        capture_output=True,
        text=True,
    )


def expect_markdown_failure(path, mutate, repo, label):
    original = path.read_text(encoding="utf-8")
    try:
        write(path, mutate(original))
        result = validate_cli(repo)
        assert result.returncode != 0, label
    finally:
        write(path, original)


with tempfile.TemporaryDirectory(prefix="lccoding-product-integration-") as temporary:
    repo = Path(temporary)
    git(repo, "init", "--quiet")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "user.name", "Fixture")
    paths = {
        "UI-MAIN": "product/ui/main",
        "UI-OPS": "product/ui/ops",
        "WF-CORE": "product/workflows/core",
        "WF-EXTRA": "product/workflows/extra",
        "SIM-MAIN": "product/simulations/main",
        "SIM-LOAD": "product/simulations/load",
    }
    for subtree_id, path in paths.items():
        write(repo / path / "identity.txt", subtree_id + "\n")
    git(repo, "add", "product")
    git(repo, "commit", "--quiet", "-m", "freeze peer product subtrees")
    commit = git(repo, "rev-parse", "HEAD")
    hashes = {
        subtree_id: validator.frozen_subtree_content_hash(repo, commit, path)[0]
        for subtree_id, path in paths.items()
    }

    workflows = [
        workflow(
            "WF-CORE",
            "CORE",
            paths["WF-CORE"],
            hashes["WF-CORE"],
            "CAP-CORE",
            "UI-MAIN, UI-OPS",
            "SIM-MAIN, SIM-LOAD",
            primary="YES",
        ),
        workflow(
            "WF-EXTRA",
            "EXTRA",
            paths["WF-EXTRA"],
            hashes["WF-EXTRA"],
            "CAP-EXTRA",
            "UI-OPS",
            "SIM-LOAD",
        ),
        workflow(
            "WF-DEFERRED",
            "EXTRA",
            "NOT_APPLICABLE",
            "NOT_APPLICABLE",
            "NOT_APPLICABLE",
            "NONE",
            "NONE",
            implementation="UNIMPLEMENTED",
        ),
    ]
    uis = [
        ui("UI-MAIN", paths["UI-MAIN"], hashes["UI-MAIN"], "WF-CORE", "SIM-MAIN", primary="YES"),
        ui("UI-OPS", paths["UI-OPS"], hashes["UI-OPS"], "WF-CORE, WF-EXTRA", "SIM-MAIN, SIM-LOAD"),
    ]
    simulations = [
        simulation("SIM-MAIN", paths["SIM-MAIN"], hashes["SIM-MAIN"], "WF-CORE", "UI-MAIN, UI-OPS", primary="YES"),
        simulation("SIM-LOAD", paths["SIM-LOAD"], hashes["SIM-LOAD"], "WF-CORE, WF-EXTRA", "UI-OPS"),
    ]
    locked = baseline_rows(workflows, uis, simulations)
    assert validate(repo, commit, workflows, uis, simulations, locked) == []

    write(repo / paths["WF-CORE"] / "identity.txt", "worktree drift\n")
    assert validate(repo, commit, workflows, uis, simulations, locked) == []

    mutations = []
    for field in (
        "Path",
        "Component version",
        "Content hash",
        "Subtree type",
        "Subtree ID",
        "Classification",
        "Classification authority",
        "Workflow Capability ID",
        "API evidence",
        "MCP evidence",
        "Primary mainline",
        "Related subtree IDs",
    ):
        changed = copy.deepcopy(locked)
        target = next(row for row in changed if row["Subtree type"] == "WORKFLOW")
        target[field] = "DRIFT"
        mutations.append(("Handoff mismatch " + field, workflows, uis, simulations, changed, {}))

    mutations.extend(
        [
            ("missing Handoff row", workflows, uis, simulations, locked[:-1], {}),
            ("extra Handoff row", workflows, uis, simulations, locked + [copy.deepcopy(locked[0]) | {"Subtree ID": "UI-EXTRA"}], {}),
            ("duplicate Handoff ID", workflows, uis, simulations, locked + [copy.deepcopy(locked[0])], {}),
        ]
    )

    changed_workflows = copy.deepcopy(workflows)
    changed_workflows[0]["MCP contract / evidence"] = interface("MCP", "CAP-OTHER", "CORE")
    mutations.append(("API/MCP split capability", changed_workflows, uis, simulations, locked, {}))

    for label, field, value in (
        (
            "classification placeholder evidence",
            "Classification authority",
            "CLASSIFICATION:CORE; CALABASH:CAL-CORE; OWNER_CONFIRMED:PENDING",
        ),
        (
            "API placeholder evidence",
            "API contract / evidence",
            "CAPABILITY:CAP-CORE; CONTRACT:API-CORE; EVIDENCE:PENDING",
        ),
        (
            "runnable placeholder evidence",
            "Evidence / attestation",
            "IMPLEMENTATION:E-IMPL-CORE; RUNNABLE:PENDING",
        ),
        (
            "structured trailing empty item",
            "API contract / evidence",
            "CAPABILITY:CAP-CORE; CONTRACT:API-CORE; EVIDENCE:E-API-CORE;",
        ),
    ):
        changed = copy.deepcopy(workflows)
        changed[0][field] = value
        mutations.append(
            (label, changed, uis, simulations, baseline_rows(changed, uis, simulations), {})
        )

    for field in (
        "Workflow Capability ID",
        "Rules / state / side-effect trace",
        "API contract / evidence",
        "MCP contract / evidence",
        "Evidence / attestation",
    ):
        changed = copy.deepcopy(workflows)
        changed[0][field] = "PENDING"
        mutations.append(("CORE missing " + field, changed, uis, simulations, locked, {}))

    changed = copy.deepcopy(workflows)
    changed[0]["Implementation status"] = "UNIMPLEMENTED"
    mutations.append(("CORE unimplemented", changed, uis, simulations, locked, {}))
    changed = copy.deepcopy(workflows)
    changed[0]["Content hash"] = "sha256:" + "a" * 64
    mutations.append(("CORE frozen hash mismatch", changed, uis, simulations, locked, {}))
    changed = copy.deepcopy(workflows)
    changed[0]["Content hash"] = changed[0]["Content hash"].upper().replace("SHA256:", "sha256:")
    mutations.append(
        (
            "non-canonical uppercase content hash",
            changed,
            uis,
            simulations,
            baseline_rows(changed, uis, simulations),
            {},
        )
    )
    changed = copy.deepcopy(workflows)
    changed[1]["MCP contract / evidence"] = "NOT_APPLICABLE"
    mutations.append(("implemented EXTRA missing MCP", changed, uis, simulations, locked, {}))
    for field, value in (
        ("Subtree path", "product/workflows/fake"),
        ("Workflow Capability ID", "CAP-FAKE"),
        ("API contract / evidence", interface("API", "CAP-FAKE", "FAKE")),
    ):
        changed = copy.deepcopy(workflows)
        changed[2][field] = value
        mutations.append(("unimplemented EXTRA claims " + field, changed, uis, simulations, locked, {}))
    changed_locked = locked + [locked_row("WORKFLOW", workflows[2])]
    mutations.append(("unimplemented EXTRA appears in Handoff", workflows, uis, simulations, changed_locked, {}))

    changed = copy.deepcopy(workflows)
    changed[0]["Classification (CORE/EXTRA)"] = "EXTRA"
    mutations.append(("CORE downgraded against authority", changed, uis, simulations, locked, {}))
    for value in ("", "CLASSIFICATION:CORE; CALABASH:CAL-CORE", "CLASSIFICATION:EXTRA; CALABASH:CAL-CORE; OWNER_CONFIRMED:OA-CORE"):
        changed = copy.deepcopy(workflows)
        changed[0]["Classification authority"] = value
        mutations.append(("invalid classification authority " + value, changed, uis, simulations, locked, {}))

    changed = copy.deepcopy(workflows)
    changed.append(copy.deepcopy(changed[0]) | {"Workflow ID": "WF-DUP", "Workflow Capability ID": "CAP-CORE", "Subtree path": paths["WF-EXTRA"]})
    mutations.append(("duplicate capability ID", changed, uis, simulations, locked, {}))
    changed = copy.deepcopy(workflows)
    changed.append(copy.deepcopy(changed[0]))
    mutations.append(("duplicate Workflow ID/path", changed, uis, simulations, locked, {}))

    nested_uis = copy.deepcopy(uis)
    nested_uis[1]["Subtree path"] = paths["WF-CORE"] + "/nested-ui"
    mutations.append(("cross-type nested path", workflows, nested_uis, simulations, locked, {}))
    nested_simulations = copy.deepcopy(simulations)
    nested_simulations[1]["Subtree path"] = paths["SIM-MAIN"] + "/nested"
    mutations.append(("nested Simulation path", workflows, uis, nested_simulations, locked, {}))

    for label, mutate in (
        ("dangling relation", lambda rows: rows[0].update({"UI subtree references": "UI-MISSING"})),
        ("wrong-type relation", lambda rows: rows[0].update({"UI subtree references": "SIM-MAIN"})),
        ("duplicate relation", lambda rows: rows[0].update({"UI subtree references": "UI-MAIN, UI-MAIN"})),
        ("empty relation item", lambda rows: rows[0].update({"UI subtree references": "UI-MAIN,"})),
    ):
        changed = copy.deepcopy(workflows)
        mutate(changed)
        mutations.append((label, changed, uis, simulations, locked, {}))
    nonreciprocal_uis = copy.deepcopy(uis)
    nonreciprocal_uis[0]["Workflow subtree references"] = "NONE"
    mutations.append(("nonreciprocal relation", workflows, nonreciprocal_uis, simulations, locked, {}))
    invalid_ui = copy.deepcopy(uis)
    invalid_ui[0]["Evidence / attestation"] = "PENDING"
    mutations.append(("UI lacks implementation evidence", workflows, invalid_ui, simulations, locked, {}))
    invalid_ui = copy.deepcopy(uis)
    invalid_ui[0]["Lock status"] = "PENDING"
    mutations.append(("UI is not locked", workflows, invalid_ui, simulations, locked, {}))
    invalid_simulation = copy.deepcopy(simulations)
    invalid_simulation[0]["Foundation status"] = "PENDING"
    mutations.append(("Simulation is not runnable", workflows, uis, invalid_simulation, locked, {}))

    no_primary_ui = copy.deepcopy(uis)
    no_primary_ui[0]["Primary mainline"] = "NO"
    mutations.append(("missing primary UI", workflows, no_primary_ui, simulations, locked, {}))
    no_primary_sim = copy.deepcopy(simulations)
    no_primary_sim[0]["Primary mainline"] = "NO"
    mutations.append(("missing primary Simulation", workflows, uis, no_primary_sim, locked, {}))
    primary_extra = copy.deepcopy(workflows)
    primary_extra[0]["Primary mainline"] = "NO"
    primary_extra[1]["Primary mainline"] = "YES"
    mutations.append(("primary EXTRA", primary_extra, uis, simulations, locked, {}))
    disconnected = copy.deepcopy(uis)
    disconnected[0]["Simulation subtree references"] = "SIM-LOAD"
    mutations.append(("disconnected primary triple", workflows, disconnected, simulations, locked, {}))

    for label, wf_rows, ui_rows, sim_rows, handoff_rows, options in mutations:
        must_fail(repo, commit, wf_rows, ui_rows, sim_rows, handoff_rows, label, **options)

    must_fail(
        repo,
        commit,
        workflows,
        uis,
        simulations,
        locked,
        "mainline ID drift",
        map_ids={"Workflow": "OTHER", "UI": "MAINLINE-1", "Simulation": "MAINLINE-1"},
    )
    must_fail(repo, commit, workflows, uis, simulations, locked, "missing Owner confirmation", owner="OWNER_CONFIRMED:")
    must_fail(repo, commit, workflows, uis, simulations, locked, "non-exact Owner confirmation", owner="owner_confirmed: OA-MAINLINE")

    # Exercise the formal Markdown/CLI entrypoint, not only dictionary validators.
    install_product_markdown_fixture(repo, commit, workflows, uis, simulations, locked)
    valid_cli = validate_cli(repo)
    assert valid_cli.returncode == 0, valid_cli.stdout + valid_cli.stderr
    lc = repo / ".lccoding"
    product_paths = {
        "Workflow": lc / "WORKFLOW-MAP.md",
        "UI": lc / "UI-MAP.md",
        "Simulation": lc / "SIMULATION-WORLD.md",
        "Handoff": lc / "PRODUCT-BASELINE-HANDOFF.md",
    }

    originals = {name: path.read_text(encoding="utf-8") for name, path in product_paths.items()}
    try:
        for name, path in product_paths.items():
            write(path, originals[name] + "\n## Harmless prose\n\nThis heading and prose do not redefine product identity.\n")
        prose_cli = validate_cli(repo)
        assert prose_cli.returncode == 0, prose_cli.stdout + prose_cli.stderr
    finally:
        for name, path in product_paths.items():
            write(path, originals[name])

    expect_markdown_failure(
        product_paths["Workflow"],
        lambda text: text + "\n- Primary product mainline ID: MAINLINE-1\n",
        repo,
        "duplicate Workflow primary scalar must fail",
    )
    expect_markdown_failure(
        product_paths["UI"],
        lambda text: text + "\n- Primary product mainline ID: MAINLINE-1\n",
        repo,
        "duplicate UI primary scalar must fail",
    )
    expect_markdown_failure(
        product_paths["Simulation"],
        lambda text: text + "\n- Primary product mainline ID: MAINLINE-1\n",
        repo,
        "duplicate Simulation primary scalar must fail",
    )
    for scalar, value in (
        ("Project repository identity", "github.com/example/project"),
        ("Project frozen exact commit SHA", commit),
        ("Calabash Definition Handoff ID / exact hash", "CDH-TASK9 / sha256:" + "1" * 64),
        ("Calabash Definition Handoff result", "PASS"),
        ("Primary product mainline ID", "MAINLINE-1"),
        ("Primary mainline Owner confirmation", "OWNER_CONFIRMED: OA-MAINLINE"),
        ("Handoff status", "COMPLETE"),
    ):
        expect_markdown_failure(
            product_paths["Handoff"],
            lambda text, key=scalar, duplicate=value: text + f"\n- {key}: {duplicate}\n",
            repo,
            f"duplicate Handoff scalar {scalar} must fail",
        )

    surface_cases = (
        ("Workflow", WORKFLOW_COLUMNS, workflows, "WF-HIDDEN"),
        ("UI", UI_COLUMNS, uis, "UI-HIDDEN"),
        ("Simulation", SIMULATION_COLUMNS, simulations, "SIM-HIDDEN"),
        ("Handoff", HANDOFF_COLUMNS, locked, "WF-HIDDEN"),
    )
    for name, columns, rows, hidden_id in surface_cases:
        first = copy.deepcopy(rows[0])
        id_field = {
            "Workflow": "Workflow ID",
            "UI": "UI ID",
            "Simulation": "Simulation ID",
            "Handoff": "Subtree ID",
        }[name]
        first[id_field] = hidden_id
        duplicate_block = table(columns, [first])
        expect_markdown_failure(
            product_paths[name],
            lambda text, block=duplicate_block: text + "\n## Hidden identity table\n\n" + block + "\n",
            repo,
            f"hidden second {name} identity table must fail",
        )

        separator = "|" + "|".join("---" for _ in columns) + "|"
        values = [str(rows[0].get(column, "DEFINED")) for column in columns]
        extra_row = "| " + " | ".join(values + ["SHADOW"]) + " |"
        missing_row = "| " + " | ".join(values[:-1]) + " |"
        orphan_row = "| " + " | ".join(values) + " |"
        expect_markdown_failure(
            product_paths[name],
            lambda text, sep=separator, row=extra_row: text.replace(sep + "\n", sep + "\n" + row + "\n", 1),
            repo,
            f"extra-cell {name} row must fail",
        )
        expect_markdown_failure(
            product_paths[name],
            lambda text, sep=separator, row=missing_row: text.replace(sep + "\n", sep + "\n" + row + "\n", 1),
            repo,
            f"missing-cell {name} row must fail",
        )
        expect_markdown_failure(
            product_paths[name],
            lambda text, row=orphan_row: text + "\n## Orphan identity\n\n" + row + "\n",
            repo,
            f"orphan {name} row must fail",
        )

    expect_markdown_failure(
        product_paths["Simulation"],
        lambda text: text + "\n## Duplicate Scenario registry\n\n" + table(SCENARIO_COLUMNS, []) + "\n",
        repo,
        "duplicate Scenario registry must fail",
    )
    expect_markdown_failure(
        product_paths["Simulation"],
        lambda text: text
        + "\n## Malformed Scenario registry\n\n"
        + table(SCENARIO_COLUMNS + ["Shadow identity"], [])
        + "\n| SIM-HIDDEN | product/simulations/hidden | 1.0.0 | sha256:"
        + "a" * 64
        + " | RUNNABLE | WF-CORE | UI-MAIN | NO |\n",
        repo,
        "malformed Scenario table cannot hide a Simulation identity",
    )

print("PASS: Product Baseline closes exact peer subtrees and same-capability interfaces")
