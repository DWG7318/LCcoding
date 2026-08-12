from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile


root = Path(__file__).resolve().parents[2]
validator = root / "lc-coding/scripts/validate_project.py"


def run(command, cwd, *, text=True):
    return subprocess.run(command, cwd=cwd, capture_output=True, text=text, check=True)


def git(repo, *args, text=True):
    return run(["git", *args], repo, text=text).stdout


def canonical_subtree_hash(repo, commit, subtree):
    raw = git(
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
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, path = record.split(b"\t", 1)
        mode, object_type, object_id = metadata.split(b" ")
        assert object_type == b"blob"
        blob = git(repo, "cat-file", "blob", object_id.decode("ascii"), text=False)
        entries.append((path, mode, hashlib.sha256(blob).hexdigest().encode("ascii")))
    assert entries
    manifest = b"".join(
        path + b"\0" + mode + b"\0" + digest + b"\n"
        for path, mode, digest in sorted(entries)
    )
    return "sha256:" + hashlib.sha256(manifest).hexdigest()


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def definition_handoff():
    return """# Calabash Definition Handoff

- Artifact role: CALABASH_DEFINITION_HANDOFF
- Definition Handoff ID: CDH-FIXTURE
- Definition Baseline kind: CALABASH_DEFINITION_BASELINE
- Definition Baseline ID: DB-FIXTURE
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
- Upgrade Receipt ID: UPGRADE-FIXTURE
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


def workflow_map(mainline_id, path, version, content_hash, *, classification="CORE", api="API-WF / D2-API", mcp="MCP-WF / D2-MCP", primary="YES"):
    return f"""# Workflow Map

- Primary product mainline ID: {mainline_id}

| Workflow ID | Classification (CORE/EXTRA) | Implementation status | Subtree path | Component version | Content hash | Actors | Trigger | States / rules | Data / permissions | Failure / recovery | API contract / evidence | MCP contract / evidence | UI subtree references | Simulation subtree references | Evidence / attestation | Calabash trace | Primary mainline |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| WF-CORE | {classification} | IMPLEMENTED | {path} | {version} | {content_hash} | Owner | Invoke | Defined | Defined | Defined | {api} | {mcp} | UI-MAIN | SIM-MAIN | D2-WF | CAL-1 | {primary} |
"""


def ui_map(mainline_id, path, version, content_hash, *, primary="YES"):
    return f"""# UI Map

- Primary product mainline ID: {mainline_id}

| UI ID | Subtree path | Component version | Content hash | Actor | Surface / state | Actions / feedback | Workflow subtree references | Simulation subtree references | Evidence / attestation | Lock status | Primary mainline |
|---|---|---|---|---|---|---|---|---|---|---|---|
| UI-MAIN | {path} | {version} | {content_hash} | Owner | Main | Invoke | WF-CORE | SIM-MAIN | D2-UI | LOCKED | {primary} |
"""


def simulation_map(mainline_id, path, version, content_hash, *, primary="YES"):
    return f"""# Simulation World

- Primary product mainline ID: {mainline_id}

## Simulation subtree registry

| Simulation ID | Subtree path | Component version | Content hash | Foundation status | Workflow subtree references | UI subtree references | Primary mainline |
|---|---|---|---|---|---|---|---|
| SIM-MAIN | {path} | {version} | {content_hash} | RUNNABLE | WF-CORE | UI-MAIN | {primary} |

## Scenario registry

| Simulation ID | Scenario ID | Actors | Data/state/time | Path | Failure/recovery | Fidelity | Visible / invisible evidence | Used by Slice/Run/Acceptance | Scenario version |
|---|---|---|---|---|---|---|---|---|---|
"""


def handoff(commit, mainline_id, owner_confirmation, identities, definition_hash, *, workflow_classification="CORE", workflow_api="API-WF / D2-API", workflow_mcp="MCP-WF / D2-MCP", primary="YES"):
    ui, workflow, simulation = identities
    return f"""# Product Baseline Handoff

- Baseline ID / version / hash: PB-1 / 1.0.0 / E-PB
- Project repository identity: github.com/example/project
- Project frozen exact commit SHA: {commit}
- Calabash source: CAL-1
- Calabash Definition Handoff ID / exact hash: CDH-FIXTURE / {definition_hash}
- Calabash Definition Handoff result: PASS
- Workflow Map: .lccoding/WORKFLOW-MAP.md
- UI Map: .lccoding/UI-MAP.md
- Simulation World: .lccoding/SIMULATION-WORLD.md
- Primary product mainline ID: {mainline_id}
- Primary mainline Owner confirmation: {owner_confirmation}
- Handoff status: COMPLETE

## Locked logical subtrees

| Subtree type | Subtree ID | Path | Component version | Content hash | Classification | API evidence | MCP evidence | Primary mainline | Related subtree IDs |
|---|---|---|---|---|---|---|---|---|---|
| UI | UI-MAIN | {ui[0]} | {ui[1]} | {ui[2]} | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | {primary} | WF-CORE, SIM-MAIN |
| WORKFLOW | WF-CORE | {workflow[0]} | {workflow[1]} | {workflow[2]} | {workflow_classification} | {workflow_api} | {workflow_mcp} | {primary} | UI-MAIN, SIM-MAIN |
| SIMULATION | SIM-MAIN | {simulation[0]} | {simulation[1]} | {simulation[2]} | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | {primary} | WF-CORE, UI-MAIN |
"""


def write_identity_artifacts(repo, base_commit, hashes, **changes):
    mainline_map = changes.get("map_mainline", "MAINLINE-PRIMARY")
    mainline_handoff = changes.get("handoff_mainline", "MAINLINE-PRIMARY")
    ui = (
        changes.get("ui_path", "product/ui/main"),
        changes.get("ui_map_version", "1.0.0"),
        changes.get("ui_map_hash", hashes["UI"]),
    )
    workflow = (
        changes.get("workflow_path", "product/workflows/core"),
        changes.get("workflow_map_version", "1.0.0"),
        changes.get("workflow_map_hash", hashes["WORKFLOW"]),
    )
    simulation = (
        changes.get("simulation_path", "product/simulations/main"),
        changes.get("simulation_map_version", "1.0.0"),
        changes.get("simulation_map_hash", hashes["SIMULATION"]),
    )
    lc = repo / ".lccoding"
    gate = lc / "CALABASH-UPGRADE-GATE.md"
    write(gate, definition_handoff())
    definition_hash = "sha256:" + hashlib.sha256(gate.read_bytes()).hexdigest()
    write(lc / "WORKFLOW-MAP.md", workflow_map(
        mainline_map, workflow[0], workflow[1], workflow[2],
        classification=changes.get("workflow_map_classification", "CORE"),
        api=changes.get("workflow_map_api", "API-WF / D2-API"),
        mcp=changes.get("workflow_map_mcp", "MCP-WF / D2-MCP"),
        primary=changes.get("map_primary", "YES"),
    ))
    write(lc / "UI-MAP.md", ui_map(
        mainline_map, ui[0], ui[1], ui[2], primary=changes.get("map_primary", "YES")
    ))
    write(lc / "SIMULATION-WORLD.md", simulation_map(
        mainline_map, simulation[0], simulation[1], simulation[2], primary=changes.get("map_primary", "YES")
    ))
    locked = (
        (changes.get("ui_handoff_path", ui[0]), changes.get("ui_handoff_version", ui[1]), changes.get("ui_handoff_hash", ui[2])),
        (changes.get("workflow_handoff_path", workflow[0]), changes.get("workflow_handoff_version", workflow[1]), changes.get("workflow_handoff_hash", workflow[2])),
        (changes.get("simulation_handoff_path", simulation[0]), changes.get("simulation_handoff_version", simulation[1]), changes.get("simulation_handoff_hash", simulation[2])),
    )
    write(lc / "PRODUCT-BASELINE-HANDOFF.md", handoff(
        changes.get("commit", base_commit),
        mainline_handoff,
        changes.get("owner_confirmation", "OWNER_CONFIRMED: OA-PB-1"),
        locked,
        definition_hash,
        workflow_classification=changes.get("workflow_handoff_classification", "CORE"),
        workflow_api=changes.get("workflow_handoff_api", "API-WF / D2-API"),
        workflow_mcp=changes.get("workflow_handoff_mcp", "MCP-WF / D2-MCP"),
        primary=changes.get("handoff_primary", "YES"),
    ))


def validate(repo):
    return subprocess.run(
        [sys.executable, str(validator), str(repo)],
        capture_output=True,
        text=True,
    )


with tempfile.TemporaryDirectory(prefix="lccoding-subtree-git-") as temporary:
    repo = Path(temporary)
    git(repo, "init", "--quiet")
    git(repo, "config", "user.email", "lccoding-test@example.invalid")
    git(repo, "config", "user.name", "LCCoding Test")
    for relative, content in {
        "product/ui/main/index.html": "<main>UI</main>\n",
        "product/workflows/core/workflow.py": "def run(): return 'ok'\n",
        "product/simulations/main/world.json": '{"state":"ready"}\n',
    }.items():
        write(repo / relative, content)
    git(repo, "add", "product")
    git(repo, "commit", "--quiet", "-m", "freeze product subtrees")
    commit = git(repo, "rev-parse", "HEAD").strip()
    hashes = {
        "UI": canonical_subtree_hash(repo, commit, "product/ui/main"),
        "WORKFLOW": canonical_subtree_hash(repo, commit, "product/workflows/core"),
        "SIMULATION": canonical_subtree_hash(repo, commit, "product/simulations/main"),
    }

    lc = repo / ".lccoding"
    for name in ["OWNER-POLICY.md", "PROJECT-PROFILE.md", "AGENT-RULE.md"]:
        write(lc / name, "# Evidence\n")
    for name, value in {
        "PROJECT-START.json": {"initialization_mode": "NEW", "repository": "github.com/example/project"},
        "PROJECT-FINGERPRINT.json": {"complexity": {key: "LOW" for key in ["product_uncertainty", "system_coupling", "real_risk", "irreversibility", "novelty"]}, "depth": {}},
        "PROJECT-HEALTH.json": {},
        "CANONICAL-MANIFEST.json": {},
        "INTERPRETATION-LOCK.json": {"status": "VALID"},
        "status.json": {},
        "PHASE-STATUS.json": {},
    }.items():
        write(lc / name, json.dumps(value, ensure_ascii=False) + "\n")
    write(repo / "VERSION", "1.0.0\n")

    write_identity_artifacts(repo, commit, hashes)
    valid = validate(repo)
    assert valid.returncode == 0, valid.stdout + valid.stderr

    # The frozen commit, never the mutable worktree, supplies the locked blobs.
    write(repo / "product/ui/main/index.html", "<main>uncommitted change</main>\n")
    still_locked = validate(repo)
    assert still_locked.returncode == 0, still_locked.stdout + still_locked.stderr

    write_identity_artifacts(repo, commit, hashes, commit="0" * 40)
    invalid_commit = validate(repo)
    assert invalid_commit.returncode != 0 and "commit" in invalid_commit.stdout.lower()

    write_identity_artifacts(
        repo, commit, hashes,
        ui_path="product/ui/missing", ui_handoff_path="product/ui/missing",
    )
    missing_tree = validate(repo)
    assert missing_tree.returncode != 0 and "tree" in missing_tree.stdout.lower()

    false_hash = "sha256:" + "a" * 64
    write_identity_artifacts(
        repo, commit, hashes,
        workflow_map_hash=false_hash, workflow_handoff_hash=false_hash,
    )
    hash_mismatch = validate(repo)
    assert hash_mismatch.returncode != 0 and "content hash" in hash_mismatch.stdout.lower()

    write_identity_artifacts(repo, commit, hashes, ui_handoff_version="9.9.9")
    map_mismatch = validate(repo)
    assert map_mismatch.returncode != 0 and "map" in map_mismatch.stdout.lower()

    for field in ["classification", "api", "mcp"]:
        write_identity_artifacts(repo, commit, hashes, **{f"workflow_handoff_{field}": "DRIFT"})
        drift = validate(repo)
        assert drift.returncode != 0 and "map" in drift.stdout.lower(), field

    write_identity_artifacts(
        repo, commit, hashes,
        workflow_map_version="banana", workflow_handoff_version="banana",
    )
    invalid_version = validate(repo)
    assert invalid_version.returncode != 0 and "component version" in invalid_version.stdout.lower()

    write_identity_artifacts(repo, commit, hashes, handoff_mainline="UNBOUND-ID")
    unbound_mainline = validate(repo)
    assert unbound_mainline.returncode != 0 and "mainline" in unbound_mainline.stdout.lower()

    write_identity_artifacts(repo, commit, hashes, owner_confirmation="OWNER_CONFIRMED:")
    empty_confirmation = validate(repo)
    assert empty_confirmation.returncode != 0 and "owner confirmation" in empty_confirmation.stdout.lower()

    write_identity_artifacts(repo, commit, hashes, map_primary="MAYBE", handoff_primary="MAYBE")
    invalid_flag = validate(repo)
    assert invalid_flag.returncode != 0 and "yes or no" in invalid_flag.stdout.lower()

print("PASS: Product Baseline identities resolve to frozen Git trees and match canonical Maps")
