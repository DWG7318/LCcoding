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
spec = importlib.util.spec_from_file_location("lccoding_calabash_boundary", validator_path)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

gate_template = root / "lc-coding/templates/CALABASH-UPGRADE-GATE.md"
product_template = root / "lc-coding/templates/PRODUCT-BASELINE-HANDOFF.md"
impact_template = root / "lc-coding/templates/IMPACT-ANALYSIS.md"
run_template = root / "lc-coding/templates/RUN-HANDOFF.md"


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def artifact_hash(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def fields_text(title, fields, tables=""):
    body = "\n".join(
        f"- {key}: {value}" if value else f"- {key}:" for key, value in fields.items()
    )
    return f"# {title}\n\n{body}\n{tables}"


def valid_gate_fields(**changes):
    fields = {
        "Artifact role": "CALABASH_DEFINITION_HANDOFF",
        "Definition Handoff ID": "CDH-1",
        "Definition Baseline kind": "CALABASH_DEFINITION_BASELINE",
        "Definition Baseline ID": "DB-1",
        "Definition Baseline semantic version": "1.0.0",
        "Definition Baseline exact hash": "sha256:" + "1" * 64,
        "Calabash standard version": "2.5.0",
        "Baseline status": "FROZEN",
        "Applicable Definition clause references": "baseline:/grandpa/product, baseline:/product_architecture/journey, baseline:/ontology/order",
        "Snake review status": "IDENTIFIED",
        "Snake review scope": "Grandpa, Product Architecture, Ontology",
        "Snake review evidence refs": "E-SNAKE-REVIEW",
        "Scorpion review status": "IDENTIFIED",
        "Scorpion review scope": "Grandpa, Product Architecture, Ontology",
        "Scorpion review evidence refs": "E-SCORPION-REVIEW",
        "Meaning-change / invalidation rules reference": "CAL-CHANGE-1",
        "Upgrade Receipt ID": "UPGRADE-1",
        "Upgrade Receipt exact hash": "sha256:" + "2" * 64,
        "Upgrade verdict": "CALABASH_UPGRADE_PASS",
        "Owner change authority": "OWNER",
        "Handoff result": "PASS",
    }
    fields.update(changes)
    return fields


def gate_tables(snake_rows=None, scorpion_rows=None):
    if snake_rows is None:
        snake_rows = [
            ("SNAKE-G", "GUARDED", "GUARD-1", "E-SG", "baseline:/product_architecture/journey"),
            ("SNAKE-A", "ACCEPTED_WITH_EVIDENCE", "VERIFY-1", "E-SA", "baseline:/ontology/order"),
            ("SNAKE-I", "INVALIDATED", "INVALIDATION-1", "E-SI", "baseline:/grandpa/product"),
        ]
    if scorpion_rows is None:
        scorpion_rows = [
            ("SCORPION-C", "CLEAR", "HARD_BLOCK", "HIT-CHECK-1", "E-SC", "baseline:/product_architecture/journey"),
            ("SCORPION-I", "INVALIDATED", "HARD_BLOCK", "HIT-CHECK-2", "E-SI", "baseline:/ontology/order"),
        ]
    snake = "\n".join("| " + " | ".join(row) + " |" for row in snake_rows)
    scorpion = "\n".join("| " + " | ".join(row) + " |" for row in scorpion_rows)
    return f"""
## Snake records

| Snake ID | Disposition | Guard / verification reference | Evidence refs | Affected Definition clause refs |
|---|---|---|---|---|
{snake}

## Scorpion records

| Scorpion ID | Status | Blocking semantics | Hit condition reference | Evidence refs | Affected Definition clause refs |
|---|---|---|---|---|---|
{scorpion}
"""


def write_gate(path, fields=None, snake_rows=None, scorpion_rows=None):
    write(
        path,
        fields_text(
            "Calabash Definition Handoff",
            valid_gate_fields() if fields is None else fields,
            gate_tables(snake_rows, scorpion_rows),
        ),
    )


def valid_impact_fields(classification="MEANING_NEUTRAL", **changes):
    neutral = classification == "MEANING_NEUTRAL"
    fields = {
        "Artifact role": "IMPACT_ANALYSIS",
        "Analysis ID / version": "IA-1 / 1.0.0",
        "Trigger / proposed change": "bounded implementation",
        "Meaning impact classification": classification,
        "Calling phase contract / authority": "LC-PHASE-3",
        "Neutral rationale / evidence": "E-NEUTRAL-1" if neutral else "NOT_APPLICABLE",
        "Definition Baseline ID / exact hash": "NONE" if neutral else "DB-1 / sha256:" + "1" * 64,
        "Affected Definition clause references": "NONE" if neutral else "baseline:/product_architecture/journey",
        "Definition invalidation effect": "NO_DEFINITION_INVALIDATION" if neutral else "INVALIDATES",
        "Governed Calabash update route / Owner authority": "NOT_APPLICABLE" if neutral else "CALABASH_UPDATE / OWNER",
        "Snake / Scorpion applicability and effect references": "NONE_IDENTIFIED: E-REVIEW" if neutral else "CALABASH-UPGRADE-GATE.md",
        "Affected Workflow": "WF-1",
        "Affected UI": "UI-1",
        "Affected Simulation scenarios": "SIM-1",
        "Affected shared capabilities / data / APIs": "API-1",
        "Affected accepted Slices / Runs / evidence": "RUN-1",
        "Existing evidence reused / unknown / contradicted": "E-1",
        "Fingerprint complexity and proportional-depth response": "LOW / bounded",
        "Regression scope": "affected route",
        "Release / rollback": "revert candidate",
        "Impact result": "PASS",
    }
    fields.update(changes)
    return fields


def write_impact(path, fields=None):
    write(
        path,
        fields_text(
            "Impact Analysis",
            valid_impact_fields() if fields is None else fields,
        ),
    )


required_gate_template_fields = {
    "Artifact role",
    "Definition Handoff ID",
    "Definition Baseline kind",
    "Definition Baseline ID",
    "Definition Baseline semantic version",
    "Definition Baseline exact hash",
    "Calabash standard version",
    "Baseline status",
    "Applicable Definition clause references",
    "Snake review status",
    "Snake review scope",
    "Snake review evidence refs",
    "Scorpion review status",
    "Scorpion review scope",
    "Scorpion review evidence refs",
    "Meaning-change / invalidation rules reference",
    "Upgrade Receipt ID",
    "Upgrade Receipt exact hash",
    "Upgrade verdict",
    "Owner change authority",
    "Handoff result",
}
template_fields = validator.parse_markdown_fields(gate_template)
assert required_gate_template_fields.issubset(template_fields), (
    "current Calabash gate is not yet the narrow Definition Handoff",
    required_gate_template_fields - set(template_fields),
)
assert hasattr(validator, "validate_calabash_definition_handoff")
assert hasattr(validator, "validate_impact_analysis")
assert hasattr(validator, "validate_product_definition_basis")
assert hasattr(validator, "validate_run_definition_basis")


with tempfile.TemporaryDirectory(prefix="lccoding-calabash-boundary-") as temporary:
    base = Path(temporary)
    valid_gate = base / "valid/CALABASH-UPGRADE-GATE.md"
    write_gate(valid_gate)
    errors = validator.validate_calabash_definition_handoff(valid_gate, require_pass=True)
    assert errors == [], errors

    none_gate = base / "none/CALABASH-UPGRADE-GATE.md"
    none_fields = valid_gate_fields(
        **{
            "Snake review status": "NONE_IDENTIFIED",
            "Scorpion review status": "NONE_IDENTIFIED",
        }
    )
    write_gate(none_gate, none_fields, snake_rows=[], scorpion_rows=[])
    assert validator.validate_calabash_definition_handoff(none_gate, require_pass=True) == []

    for name, field, value in (
        ("snake-scope-missing", "Snake review scope", ""),
        ("snake-evidence-missing", "Snake review evidence refs", ""),
        ("scorpion-scope-missing", "Scorpion review scope", ""),
        ("scorpion-evidence-missing", "Scorpion review evidence refs", ""),
        ("baseline-kind-product", "Definition Baseline kind", "PRODUCT_BASELINE"),
        ("baseline-kind-integration", "Definition Baseline kind", "INTEGRATION_BASELINE"),
        ("baseline-kind-method", "Definition Baseline kind", "METHOD_BASELINE"),
        ("baseline-kind-ui", "Definition Baseline kind", "UI_LOCK"),
        ("baseline-id", "Definition Baseline ID", ""),
        ("baseline-version", "Definition Baseline semantic version", "banana"),
        ("baseline-hash", "Definition Baseline exact hash", "sha256:" + "A" * 64),
        ("baseline-status", "Baseline status", "READY"),
        ("standard-version", "Calabash standard version", "2.4.0"),
        ("owner-authority", "Owner change authority", "AI"),
        ("upgrade-id", "Upgrade Receipt ID", ""),
        ("upgrade-hash", "Upgrade Receipt exact hash", "bad"),
        ("upgrade-verdict", "Upgrade verdict", "CALABASH_UPGRADE_FAIL"),
    ):
        path = base / name / "CALABASH-UPGRADE-GATE.md"
        fields = valid_gate_fields(**{field: value})
        write_gate(path, fields)
        assert validator.validate_calabash_definition_handoff(path, require_pass=True), name

    for name, clause_refs in (
        ("snake-clause", "baseline:/snake/S-1"),
        ("scorpion-clause", "baseline:/scorpion/SC-1"),
        ("unknown-clause", "baseline:/unknown/value"),
    ):
        path = base / name / "CALABASH-UPGRADE-GATE.md"
        fields = valid_gate_fields(**{"Applicable Definition clause references": clause_refs})
        write_gate(path, fields)
        assert validator.validate_calabash_definition_handoff(path, require_pass=True), name

    snake_open = base / "snake-open/CALABASH-UPGRADE-GATE.md"
    write_gate(
        snake_open,
        valid_gate_fields(**{"Handoff result": "BLOCKED"}),
        snake_rows=[("SNAKE-OPEN", "OPEN", "GUARD-1", "E-SO", "baseline:/grandpa/product")],
    )
    assert validator.validate_calabash_definition_handoff(snake_open, require_pass=False) == []
    assert validator.validate_calabash_definition_handoff(snake_open, require_pass=True)
    false_pass = base / "snake-open-false-pass/CALABASH-UPGRADE-GATE.md"
    write_gate(
        false_pass,
        snake_rows=[("SNAKE-OPEN", "OPEN", "GUARD-1", "E-SO", "baseline:/grandpa/product")],
    )
    assert validator.validate_calabash_definition_handoff(false_pass, require_pass=False)

    scorpion_hit = base / "scorpion-hit/CALABASH-UPGRADE-GATE.md"
    write_gate(
        scorpion_hit,
        valid_gate_fields(**{"Handoff result": "BLOCKED"}),
        scorpion_rows=[("SCORPION-HIT", "HIT", "HARD_BLOCK", "HIT-CHECK", "E-SH", "baseline:/ontology/order")],
    )
    assert validator.validate_calabash_definition_handoff(scorpion_hit, require_pass=False) == []
    assert validator.validate_calabash_definition_handoff(scorpion_hit, require_pass=True)

    for name, row in (
        ("scorpion-no-hard-block", ("SC-1", "CLEAR", "SOFT", "HIT-CHECK", "E", "baseline:/ontology/order")),
        ("scorpion-no-hit", ("SC-1", "CLEAR", "HARD_BLOCK", "", "E", "baseline:/ontology/order")),
        ("scorpion-no-evidence", ("SC-1", "CLEAR", "HARD_BLOCK", "HIT-CHECK", "", "baseline:/ontology/order")),
    ):
        path = base / name / "CALABASH-UPGRADE-GATE.md"
        write_gate(path, scorpion_rows=[row])
        assert validator.validate_calabash_definition_handoff(path, require_pass=True), name

    duplicate_row = base / "duplicate-row/CALABASH-UPGRADE-GATE.md"
    row = ("SNAKE-G", "GUARDED", "GUARD-1", "E-SG", "baseline:/grandpa/product")
    write_gate(duplicate_row, snake_rows=[row, row])
    assert validator.validate_calabash_definition_handoff(duplicate_row, require_pass=True)

    duplicate_field = base / "duplicate-field/CALABASH-UPGRADE-GATE.md"
    write_gate(duplicate_field)
    duplicate_field.write_text(
        duplicate_field.read_text(encoding="utf-8") + "- Owner change authority: OWNER\n",
        encoding="utf-8",
        newline="\n",
    )
    assert validator.validate_calabash_definition_handoff(duplicate_field, require_pass=True)

    extra_column = base / "extra-row-column/CALABASH-UPGRADE-GATE.md"
    write_gate(extra_column)
    extra_text = extra_column.read_text(encoding="utf-8").replace(
        "| Snake ID | Disposition | Guard / verification reference | Evidence refs | Affected Definition clause refs |",
        "| Snake ID | Disposition | Guard / verification reference | Evidence refs | Affected Definition clause refs | Runtime state |",
    ).replace(
        "|---|---|---|---|---|\n| SNAKE-G |",
        "|---|---|---|---|---|---|\n| SNAKE-G |",
    ).replace(
        "| baseline:/product_architecture/journey |",
        "| baseline:/product_architecture/journey | ACTIVE |",
        1,
    )
    write(extra_column, extra_text)
    assert validator.validate_calabash_definition_handoff(extra_column, require_pass=True)

    hidden_snake = base / "hidden-second-snake/CALABASH-UPGRADE-GATE.md"
    write_gate(hidden_snake)
    hidden_snake.write_text(
        hidden_snake.read_text(encoding="utf-8")
        + """
## Hidden Snake records

| Snake ID | Disposition | Guard / verification reference | Evidence refs | Affected Definition clause refs |
|---|---|---|---|---|
| SNAKE-HIDDEN | OPEN | GUARD-H | E-H | baseline:/grandpa/product |
""",
        encoding="utf-8",
        newline="\n",
    )
    assert validator.validate_calabash_definition_handoff(hidden_snake, require_pass=True)

    hidden_scorpion = base / "hidden-second-scorpion/CALABASH-UPGRADE-GATE.md"
    write_gate(hidden_scorpion)
    hidden_scorpion.write_text(
        hidden_scorpion.read_text(encoding="utf-8")
        + """
## Hidden Scorpion records

| Scorpion ID | Status | Blocking semantics | Hit condition reference | Evidence refs | Affected Definition clause refs |
|---|---|---|---|---|---|
| SCORPION-HIDDEN | HIT | HARD_BLOCK | HIT-H | E-H | baseline:/ontology/order |
""",
        encoding="utf-8",
        newline="\n",
    )
    assert validator.validate_calabash_definition_handoff(hidden_scorpion, require_pass=True)

    for name, marker, malformed in (
        (
            "malformed-snake-row",
            "| SNAKE-G | GUARDED | GUARD-1 | E-SG | baseline:/product_architecture/journey |",
            "| SNAKE-MALFORMED | OPEN | GUARD-M | E-M | baseline:/grandpa/product | EXTRA |",
        ),
        (
            "malformed-scorpion-row",
            "| SCORPION-C | CLEAR | HARD_BLOCK | HIT-CHECK-1 | E-SC | baseline:/product_architecture/journey |",
            "| SCORPION-MALFORMED | HIT | HARD_BLOCK | HIT-M | E-M |",
        ),
    ):
        path = base / name / "CALABASH-UPGRADE-GATE.md"
        write_gate(path)
        write(
            path,
            path.read_text(encoding="utf-8").replace(marker, marker + "\n" + malformed),
        )
        assert validator.validate_calabash_definition_handoff(path, require_pass=True), name

    harmless_prose = base / "harmless-prose/CALABASH-UPGRADE-GATE.md"
    write_gate(harmless_prose)
    write(
        harmless_prose,
        harmless_prose.read_text(encoding="utf-8")
        + "\nThis ordinary explanatory sentence is outside both closed tables.\n",
    )
    assert validator.validate_calabash_definition_handoff(harmless_prose, require_pass=True) == []

    for name, orphan in (
        (
            "orphan-snake-row",
            "| SNAKE-ORPHAN | OPEN | G | E | baseline:/grandpa/product |",
        ),
        (
            "orphan-scorpion-row",
            "| SCORPION-ORPHAN | HIT | HARD_BLOCK | H | E | baseline:/ontology/order |",
        ),
    ):
        path = base / name / "CALABASH-UPGRADE-GATE.md"
        write_gate(path)
        write(path, path.read_text(encoding="utf-8") + "\n" + orphan + "\n")
        assert validator.validate_calabash_definition_handoff(path, require_pass=True), name

    neutral = base / "neutral/IMPACT-ANALYSIS.md"
    write_impact(neutral)
    assert validator.validate_impact_analysis(neutral) == []
    changing = base / "changing/IMPACT-ANALYSIS.md"
    write_impact(changing, valid_impact_fields("MEANING_CHANGING"))
    assert validator.validate_impact_analysis(changing) == []

    for name, changes in (
        ("changing-no-basis", {"Definition Baseline ID / exact hash": "NONE"}),
        ("changing-no-route", {"Governed Calabash update route / Owner authority": "NOT_APPLICABLE"}),
        ("changing-no-clauses", {"Affected Definition clause references": "NONE"}),
        ("neutral-fake-basis", {"Definition Baseline ID / exact hash": "DB-FAKE / sha256:" + "9" * 64}),
        ("neutral-invalidation", {"Definition invalidation effect": "INVALIDATES"}),
        ("neutral-no-rationale", {"Neutral rationale / evidence": "NONE"}),
    ):
        path = base / name / "IMPACT-ANALYSIS.md"
        fields = valid_impact_fields("MEANING_CHANGING" if name.startswith("changing") else "MEANING_NEUTRAL", **changes)
        write_impact(path, fields)
        assert validator.validate_impact_analysis(path), name

    product_fields = {
        "Baseline ID / version / hash": "PB-1 / 1.0.0 / sha256:" + "3" * 64,
        "Calabash Definition Handoff ID / exact hash": "",
        "Calabash Definition Handoff result": "PASS",
        "Handoff status": "COMPLETE",
    }
    lc = base / "product/.lccoding"
    write_gate(lc / "CALABASH-UPGRADE-GATE.md")
    product_fields["Calabash Definition Handoff ID / exact hash"] = (
        "CDH-1 / " + artifact_hash(lc / "CALABASH-UPGRADE-GATE.md")
    )
    assert validator.validate_product_definition_basis(lc, product_fields) == []
    for name, value in (
        ("wrong-id", "CDH-X / sha256:" + "1" * 64),
        ("wrong-hash", "CDH-1 / sha256:" + "8" * 64),
        ("kind-substitute", "PRODUCT_BASELINE / sha256:" + "1" * 64),
    ):
        mutation = copy.deepcopy(product_fields)
        mutation["Calabash Definition Handoff ID / exact hash"] = value
        assert validator.validate_product_definition_basis(lc, mutation), name
    definition_as_product = copy.deepcopy(product_fields)
    definition_as_product["Baseline ID / version / hash"] = (
        "CALABASH_DEFINITION_BASELINE / 1.0.0 / sha256:" + "3" * 64
    )
    assert validator.validate_product_definition_basis(lc, definition_as_product)

    original_citation = product_fields["Calabash Definition Handoff ID / exact hash"]
    gate_path = lc / "CALABASH-UPGRADE-GATE.md"
    write(
        gate_path,
        gate_path.read_text(encoding="utf-8").replace(
            "Snake review evidence refs: E-SNAKE-REVIEW",
            "Snake review evidence refs: E-SNAKE-REVIEW-CHANGED",
        ),
    )
    assert product_fields["Calabash Definition Handoff ID / exact hash"] == original_citation
    assert validator.validate_product_definition_basis(lc, product_fields)

    run_lc = base / "run/.lccoding"
    write_gate(run_lc / "CALABASH-UPGRADE-GATE.md")
    write_impact(run_lc / "IMPACT-ANALYSIS.md")
    run_path = run_lc / "runs/R1/RUN-HANDOFF.md"
    run_fields = {
        "Meaning impact classification": "MEANING_NEUTRAL",
        "Definition basis / neutral Impact Analysis reference": "IMPACT-ANALYSIS.md",
        "Applicable Snake / Scorpion disposition evidence reference": "CALABASH-UPGRADE-GATE.md",
        "Readiness result": "READY",
        "Blocker evidence": "NONE",
    }
    write(run_path, fields_text("Run Start Contract", run_fields))
    assert validator.validate_run_definition_basis(run_path, run_fields) == []

    blocked_impact = valid_impact_fields(
        "MEANING_NEUTRAL", **{"Impact result": "BLOCKED"}
    )
    write_impact(run_lc / "IMPACT-ANALYSIS.md", blocked_impact)
    assert validator.validate_run_definition_basis(run_path, run_fields)
    impact_blocked_run = copy.deepcopy(run_fields)
    impact_blocked_run["Readiness result"] = "BLOCKED"
    impact_blocked_run["Blocker evidence"] = "IA-1"
    assert validator.validate_run_definition_basis(run_path, impact_blocked_run) == []
    write_impact(run_lc / "IMPACT-ANALYSIS.md")

    write_gate(
        run_lc / "CALABASH-UPGRADE-GATE.md",
        valid_gate_fields(**{"Owner change authority": "AI"}),
    )
    assert validator.validate_run_definition_basis(run_path, run_fields)
    write_gate(run_lc / "CALABASH-UPGRADE-GATE.md")

    fabricated = copy.deepcopy(run_fields)
    fabricated["Definition basis / neutral Impact Analysis reference"] = "CALABASH-UPGRADE-GATE.md"
    assert validator.validate_run_definition_basis(run_path, fabricated)

    write_impact(run_lc / "IMPACT-ANALYSIS.md", valid_impact_fields("MEANING_CHANGING"))
    changing_run = copy.deepcopy(run_fields)
    changing_run["Meaning impact classification"] = "MEANING_CHANGING"
    assert validator.validate_run_definition_basis(run_path, changing_run) == []

    write_gate(
        run_lc / "CALABASH-UPGRADE-GATE.md",
        valid_gate_fields(**{"Handoff result": "BLOCKED"}),
        snake_rows=[("SNAKE-OPEN", "OPEN", "GUARD-1", "E-SO", "baseline:/grandpa/product")],
    )
    assert validator.validate_run_definition_basis(run_path, changing_run)
    blocked_run = copy.deepcopy(changing_run)
    blocked_run["Readiness result"] = "BLOCKED"
    blocked_run["Blocker evidence"] = "SNAKE-OPEN"
    assert validator.validate_run_definition_basis(run_path, blocked_run) == []
    prefix_collision = copy.deepcopy(blocked_run)
    prefix_collision["Blocker evidence"] = "SNAKE-OPEN-10"
    assert validator.validate_run_definition_basis(run_path, prefix_collision)
    duplicate_blocker = copy.deepcopy(blocked_run)
    duplicate_blocker["Blocker evidence"] = "SNAKE-OPEN, SNAKE-OPEN"
    assert validator.validate_run_definition_basis(run_path, duplicate_blocker)
    unrelated_blocker = copy.deepcopy(blocked_run)
    unrelated_blocker["Blocker evidence"] = "SNAKE-OPEN, OTHER"
    assert validator.validate_run_definition_basis(run_path, unrelated_blocker)

    write_gate(
        run_lc / "CALABASH-UPGRADE-GATE.md",
        valid_gate_fields(**{"Handoff result": "BLOCKED"}),
        scorpion_rows=[("SCORPION-HIT", "HIT", "HARD_BLOCK", "HIT-CHECK", "E-SH", "baseline:/ontology/order")],
    )
    assert validator.validate_run_definition_basis(run_path, changing_run)
    blocked_hit = copy.deepcopy(changing_run)
    blocked_hit["Readiness result"] = "BLOCKED"
    blocked_hit["Blocker evidence"] = "SCORPION-HIT"
    assert validator.validate_run_definition_basis(run_path, blocked_hit) == []

    cli_project = base / "cli-project"
    boot = subprocess.run(
        [
            sys.executable,
            str(root / "lc-coding/scripts/bootstrap_lccoding.py"),
            "--project",
            str(cli_project),
            "--name",
            "Boundary",
            "--repository",
            "owner/boundary",
            "--visibility",
            "private",
        ],
        capture_output=True,
        text=True,
    )
    assert boot.returncode == 0, boot.stdout + boot.stderr
    fingerprint_path = cli_project / ".lccoding/PROJECT-FINGERPRINT.json"
    fingerprint = json.loads(fingerprint_path.read_text(encoding="utf-8"))
    fingerprint["complexity"] = {
        name: "LOW"
        for name in (
            "product_uncertainty",
            "system_coupling",
            "real_risk",
            "irreversibility",
            "novelty",
        )
    }
    write(fingerprint_path, json.dumps(fingerprint, indent=2) + "\n")
    manifest_path = cli_project / ".lccoding/CANONICAL-MANIFEST.json"
    manifest_hash = "sha256:" + hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    lock_path = cli_project / ".lccoding/INTERPRETATION-LOCK.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock.update(
        {
            "manifest_reference": "CANONICAL-MANIFEST.json",
            "manifest_hash": manifest_hash,
            "validated_execution_method_ids": [],
            "knowledge_test": "PASS",
            "execution_test": "PASS",
            "compatibility": "PASS",
            "status": "VALID",
        }
    )
    write(lock_path, json.dumps(lock, indent=2) + "\n")
    cli_gate = cli_project / ".lccoding/CALABASH-UPGRADE-GATE.md"
    write_gate(cli_gate)
    result = subprocess.run(
        [sys.executable, str(validator_path), str(cli_project)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    fields = valid_gate_fields(**{"Owner change authority": "AI"})
    write_gate(cli_gate, fields)
    result = subprocess.run(
        [sys.executable, str(validator_path), str(cli_project)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Owner change authority" in result.stdout
    write_gate(cli_gate)
    cli_product_handoff = cli_project / ".lccoding/PRODUCT-BASELINE-HANDOFF.md"
    write(
        cli_product_handoff,
        """# Product Baseline Handoff

- Baseline ID / version / hash: PB-CLI / 1.0.0 / sha256:3333333333333333333333333333333333333333333333333333333333333333
- Project repository identity: github.com/owner/boundary
- Project frozen exact commit SHA: 0000000000000000000000000000000000000000
- Calabash Definition Handoff ID / exact hash: CDH-WRONG / sha256:1111111111111111111111111111111111111111111111111111111111111111
- Calabash Definition Handoff result: PASS
- Primary product mainline ID: MAINLINE-CLI
- Primary mainline Owner confirmation: OWNER_CONFIRMED: E-CLI
- Handoff status: COMPLETE

## Locked logical subtrees

| Subtree type | Subtree ID | Path | Component version | Content hash | Classification | API evidence | MCP evidence | Primary mainline | Related subtree IDs |
|---|---|---|---|---|---|---|---|---|---|
""",
    )
    result = subprocess.run(
        [sys.executable, str(validator_path), str(cli_project)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Calabash Definition Handoff identity/hash mismatch" in result.stdout
    missing_citation_text = "\n".join(
        line
        for line in cli_product_handoff.read_text(encoding="utf-8").splitlines()
        if not line.startswith("- Calabash Definition Handoff")
    ) + "\n"
    write(cli_product_handoff, missing_citation_text)
    result = subprocess.run(
        [sys.executable, str(validator_path), str(cli_project)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "COMPLETE requires Calabash Definition Handoff citation" in result.stdout
    write(
        cli_gate,
        """# Mandatory Calabash Upgrade Gate

- Draft version: 2.6.0
- Status: PASS
""",
    )
    result = subprocess.run(
        [sys.executable, str(validator_path), str(cli_project)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "COMPLETE requires Calabash Definition Handoff citation" in result.stdout

product_template_fields = validator.parse_markdown_fields(product_template)
assert {
    "Baseline ID / version / hash",
    "Calabash Definition Handoff ID / exact hash",
    "Calabash Definition Handoff result",
}.issubset(product_template_fields)
assert not product_template_fields["Baseline ID / version / hash"].startswith(
    "CALABASH_DEFINITION_BASELINE"
)
impact_template_fields = validator.parse_markdown_fields(impact_template)
IMPACT_TEMPLATE_REQUIRED = {
    "Meaning impact classification",
    "Definition Baseline ID / exact hash",
    "Definition invalidation effect",
    "Governed Calabash update route / Owner authority",
}
assert IMPACT_TEMPLATE_REQUIRED.issubset(impact_template_fields)
run_template_fields = validator.parse_markdown_fields(run_template)
assert {
    "Meaning impact classification",
    "Definition basis / neutral Impact Analysis reference",
    "Applicable Snake / Scorpion disposition evidence reference",
}.issubset(run_template_fields)

print("PASS: LCCoding consumes only the narrow Calabash definition handoff")
