import ast
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[2]
SELF = Path(__file__).resolve()
CONSOLIDATIONS = {
    "mainline": {
        "retired": ("lc-coding/references/method-mainline.md",),
        "replacement": None,
    },
    "product_formation": {
        "retired": (
            "lc-coding/references/calabash-lifecycle.md",
            "lc-coding/references/dual-end-design.md",
            "lc-coding/references/simulation-world.md",
        ),
        "replacement": "lc-coding/references/product-formation.md",
    },
    "real_product_integration": {
        "retired": (
            "lc-coding/references/integration-baseline-lock.md",
            "lc-coding/references/impact-and-synchronization.md",
        ),
        "replacement": "lc-coding/references/feature-slice-and-integration.md",
    },
    "acceptance_duplicate": {
        "retired": ("lc-coding/references/owner-acceptance.md",),
        "replacement": None,
    },
}
RETIRED_REFERENCES = tuple(
    retired
    for consolidation in CONSOLIDATIONS.values()
    for retired in consolidation["retired"]
)
RETIRED_BASENAMES = tuple(Path(retired).name for retired in RETIRED_REFERENCES)
RETIRED_REFERENCE = CONSOLIDATIONS["mainline"]["retired"][0]
RETIRED_BASENAME = Path(RETIRED_REFERENCE).name
PRODUCT_FORMATION_CLAUSES = {"LC-FORM-001", "LC-FORM-002", "LC-FORM-003"}
REAL_PRODUCT_INTEGRATION_CLAUSES = {
    "LC-INTEG-001",
    "LC-INTEG-002",
    "LC-INTEG-003",
}
ACCEPTANCE_CLAUSES = {"LC-ACCEPT-001", "LC-ACCEPT-002", "LC-ACCEPT-003"}
VERIFICATION_CLAUSES = {"LC-VERIFY-001"}
HISTORICAL_PREFIXES = (
    "docs/superpowers/specs/",
    "docs/superpowers/plans/",
)
CALLER_SUFFIXES = {".py", ".md", ".json"}


def tracked_active_paths():
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    paths = {
        item.decode("utf-8")
        for item in result.stdout.split(b"\0")
        if item
    }
    paths.add(SELF.relative_to(ROOT).as_posix())
    return sorted(
        path
        for path in paths
        if path != "FILE_HASHES.json"
        and not path.startswith(HISTORICAL_PREFIXES)
    )


def required_paths():
    validator = ROOT / "lc-coding/scripts/validate_repository.py"
    module = ast.parse(validator.read_text(encoding="utf-8"))
    for node in module.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if any(isinstance(target, ast.Name) and target.id == "REQUIRED" for target in targets):
            return ast.literal_eval(node.value)
    raise AssertionError("validate_repository.py has no parseable REQUIRED declaration")


def without_own_retired_declaration(text):
    lines = text.splitlines(keepends=True)
    module = ast.parse(text)
    declarations = []
    for node in module.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if any(
            isinstance(target, ast.Name) and target.id == "CONSOLIDATIONS"
            for target in targets
        ):
            declarations.append(node)
    assert len(declarations) == 1, "consolidations must have one explicit declaration"
    declaration = declarations[0]
    for line_number in range(declaration.lineno, declaration.end_lineno + 1):
        lines[line_number - 1] = "\n"
    return "".join(lines)


def source_references_retired(relative, text):
    normalized = text.replace("\\", "/")
    if any(retired in normalized for retired in RETIRED_REFERENCES) or any(
        basename in normalized for basename in RETIRED_BASENAMES
    ):
        return True
    if Path(relative).suffix.casefold() != ".py":
        return False

    def static_string(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = static_string(node.left)
            right = static_string(node.right)
            if left is not None and right is not None:
                return left + right
        return None

    module = ast.parse(text)
    for node in ast.walk(module):
        value = static_string(node)
        if value is None:
            continue
        normalized_value = value.replace("\\", "/")
        if any(retired in normalized_value for retired in RETIRED_REFERENCES) or any(
            basename in normalized_value for basename in RETIRED_BASENAMES
        ):
            return True
    return False


def active_callers():
    callers = []
    for relative in tracked_active_paths():
        path = ROOT / relative
        if path.suffix.casefold() not in CALLER_SUFFIXES or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if path.resolve() == SELF:
            text = without_own_retired_declaration(text)
        if source_references_retired(relative, text):
            callers.append(relative)
    return callers


adversarial_sources = {
    "retired Markdown link": (
        "notes.md",
        f"[legacy]({RETIRED_REFERENCE})",
        True,
    ),
    "retired JSON backslash path": (
        "config.json",
        json.dumps({"legacy": RETIRED_REFERENCE.replace("/", "\\")}),
        True,
    ),
    "two-piece Python constant concatenation": (
        "caller.py",
        f'p = "lc-coding/references/" + "{RETIRED_BASENAME}"',
        True,
    ),
    "three-piece Python constant concatenation": (
        "caller.py",
        'p = "lc-coding/references/" + "method-" + "mainline.md"',
        True,
    ),
    "RETIRED_CALLER exact assignment": (
        "caller.py",
        f"RETIRED_CALLER = {RETIRED_REFERENCE!r}",
        True,
    ),
    "RETIRED_CALLER split assignment": (
        "caller.py",
        'RETIRED_CALLER = "lc-coding/references/" + "method-" + "mainline.md"',
        True,
    ),
    "ordinary caller RETIRED_REFERENCE split assignment": (
        "caller.py",
        'RETIRED_REFERENCE = "lc-coding/references/" + "method-" + "mainline.md"',
        True,
    ),
    "Python list element constant concatenation": (
        "caller.py",
        'REQUIRED = ["lc-coding/references/" + "method-" + "mainline.md"]',
        True,
    ),
    "Python dict value constant concatenation": (
        "caller.py",
        'MAP = {"legacy": "lc-coding/references/" + "method-" + "mainline.md"}',
        True,
    ),
    "Python assert comparison constant concatenation": (
        "caller.py",
        'assert path != "lc-coding/references/" + "method-" + "mainline.md"',
        True,
    ),
    "Python if comparison constant concatenation": (
        "caller.py",
        'if path == "lc-coding/references/" + "method-" + "mainline.md":\n    pass',
        True,
    ),
    "ordinary product mainline concept": (
        "notes.md",
        "Primary product mainline remains governed.",
        False,
    ),
    "unrelated Python concatenation": (
        "caller.py",
        'label = "method-" + "mainline concept"',
        False,
    ),
}
for case, (relative, source, expected) in adversarial_sources.items():
    assert source_references_retired(relative, source) is expected, case

integration_retired = CONSOLIDATIONS["real_product_integration"]["retired"]
baseline_path, impact_path = integration_retired
baseline_name = Path(baseline_path).name
impact_name = Path(impact_path).name
baseline_parts = ("integration-", "baseline-", "lock.md")
impact_parts = ("impact-", "and-", "synchronization.md")
integration_adversarial_sources = {
    "integration exact Markdown link": (
        "notes.md",
        f"[legacy]({baseline_path})",
        True,
    ),
    "integration backslash JSON path": (
        "config.json",
        json.dumps({"legacy": impact_path.replace("/", "\\")}),
        True,
    ),
    "integration two-piece Python concatenation": (
        "caller.py",
        f'p = "lc-coding/references/{baseline_parts[0]}" + "{baseline_parts[1]}{baseline_parts[2]}"',
        True,
    ),
    "integration three-piece Python concatenation": (
        "caller.py",
        f'p = "lc-coding/references/" + "{impact_parts[0]}" + "{impact_parts[1]}{impact_parts[2]}"',
        True,
    ),
    "integration Python list concatenation": (
        "caller.py",
        f'REQUIRED = ["lc-coding/references/" + "{baseline_parts[0]}" + "{baseline_parts[1]}" + "{baseline_parts[2]}"]',
        True,
    ),
    "integration Python dict concatenation": (
        "caller.py",
        f'MAP = {{"legacy": "lc-coding/references/" + "{impact_parts[0]}" + "{impact_parts[1]}" + "{impact_parts[2]}"}}',
        True,
    ),
    "ordinary integration wording": (
        "notes.md",
        "Real Product Integration keeps one governed proving route.",
        False,
    ),
}
for case, (relative, source, expected) in integration_adversarial_sources.items():
    assert source_references_retired(relative, source) is expected, case

owner_path = CONSOLIDATIONS["acceptance_duplicate"]["retired"][0]
owner_name = Path(owner_path).name
owner_adversarial_sources = {
    "owner acceptance exact Markdown link": (
        "notes.md",
        f"[legacy]({owner_path})",
        True,
    ),
    "owner acceptance backslash JSON path": (
        "config.json",
        json.dumps({"legacy": owner_path.replace("/", "\\")}),
        True,
    ),
    "owner acceptance two-piece Python concatenation": (
        "caller.py",
        f'p = "lc-coding/references/" + "{owner_name}"',
        True,
    ),
    "owner acceptance three-piece Python concatenation": (
        "caller.py",
        'p = "lc-coding/references/" + "owner-" + "acceptance.md"',
        True,
    ),
    "owner acceptance Python list concatenation": (
        "caller.py",
        'REQUIRED = ["lc-coding/references/" + "owner-" + "acceptance.md"]',
        True,
    ),
    "owner acceptance Python dict concatenation": (
        "caller.py",
        'MAP = {"legacy": "lc-coding/references/" + "owner-" + "acceptance.md"}',
        True,
    ),
    "ordinary Owner acceptance wording": (
        "notes.md",
        "Owner acceptance remains a terminal product decision.",
        False,
    ),
}
for case, (relative, source, expected) in owner_adversarial_sources.items():
    assert source_references_retired(relative, source) is expected, case

self_declaration = f"CONSOLIDATIONS = {CONSOLIDATIONS!r}\n"
stripped_self_declaration = without_own_retired_declaration(self_declaration)
assert not source_references_retired(SELF.as_posix(), stripped_self_declaration)
self_with_other_split_reference = self_declaration + (
    'OTHER_CALLER = "lc-coding/references/" + "method-" + "mainline.md"\n'
)
assert source_references_retired(
    SELF.as_posix(),
    without_own_retired_declaration(self_with_other_split_reference),
), "self declaration exclusion must not hide another split caller"


errors = []
manifest = json.loads((ROOT / "FILE_HASHES.json").read_text(encoding="utf-8"))
required = required_paths()
for group, consolidation in CONSOLIDATIONS.items():
    replacement = consolidation["replacement"]
    if replacement:
        if not (ROOT / replacement).is_file():
            errors.append(f"{group} replacement missing: {replacement}")
        if replacement not in manifest:
            errors.append(f"hash manifest missing {group} replacement: {replacement}")
    for retired in consolidation["retired"]:
        if (ROOT / retired).exists():
            errors.append(f"retired reference still exists: {retired}")
        if retired in required:
            errors.append(f"repository validator still requires retired reference: {retired}")
        if retired in manifest:
            errors.append(f"hash manifest still publishes retired reference: {retired}")

focused_owners = []
for reference in sorted((ROOT / "lc-coding/references").glob("*.md")):
    source_ids = set(
        re.findall(
            r"\bLC-FORM-\d{3}\b",
            "\n".join(
                line
                for line in reference.read_text(encoding="utf-8").splitlines()
                if line.startswith("Source clauses:")
            ),
        )
    )
    if source_ids.intersection(PRODUCT_FORMATION_CLAUSES):
        focused_owners.append(reference.relative_to(ROOT).as_posix())
assert focused_owners == [CONSOLIDATIONS["product_formation"]["replacement"]], (
    f"Product Formation must have one focused owner: {focused_owners}"
)

integration_focused_owners = []
for reference in sorted((ROOT / "lc-coding/references").glob("*.md")):
    source_ids = set(
        re.findall(
            r"\bLC-INTEG-\d{3}\b",
            "\n".join(
                line
                for line in reference.read_text(encoding="utf-8").splitlines()
                if line.startswith("Source clauses:")
            ),
        )
    )
    if source_ids.intersection(REAL_PRODUCT_INTEGRATION_CLAUSES):
        integration_focused_owners.append(reference.relative_to(ROOT).as_posix())
assert integration_focused_owners == [
    CONSOLIDATIONS["real_product_integration"]["replacement"]
], f"Real Product Integration must have one focused owner: {integration_focused_owners}"

integration_reference_path = ROOT / CONSOLIDATIONS["real_product_integration"][
    "replacement"
]
integration_reference = integration_reference_path.read_text(encoding="utf-8")
integration_sections = re.findall(
    r'(?ms)^<a id="([a-z0-9-]+)"></a>\n## ([^\n]+)\n\n(.*?)(?=^<a id="|\Z)',
    integration_reference,
)
assert len(integration_sections) == 3, "integration guidance needs exactly three focused sections"
source_lines = []
reference_anchors = set()
for anchor, _, section in integration_sections:
    reference_anchors.add(anchor)
    section_source_lines = [
        line for line in section.splitlines() if line.startswith("Source clauses:")
    ]
    assert len(section_source_lines) == 1, f"{anchor} needs one Source clauses line"
    source_lines.extend(section_source_lines)
assert set(re.findall(r"\bLC-[A-Z]+-\d{3}\b", "\n".join(source_lines))) == (
    REAL_PRODUCT_INTEGRATION_CLAUSES
), "integration guidance may cite only LC-INTEG-001/002/003"

spec = (ROOT / "SPEC.md").read_text(encoding="utf-8")


def clause_body(clause_id):
    start = re.search(
        rf'(?m)^<a id="{clause_id.lower()}"></a>\s*\n### [^\n]+\n', spec
    )
    assert start, f"SPEC is missing {clause_id}"
    tail = spec[start.end() :]
    end = re.search(r'(?m)^<a id="lc-|^## ', tail)
    return tail[: end.start()] if end else tail


integration_links = {
    "LC-INTEG-001": "slice-and-proving-path",
    "LC-INTEG-002": "one-way-ui-lock-and-recoverable-identity",
    "LC-INTEG-003": "impact-mutability-evidence-and-learning",
}
for clause_id, anchor in integration_links.items():
    links = re.findall(
        r"\[Real Product Integration guidance\]"
        r"\(lc-coding/references/feature-slice-and-integration\.md#([a-z0-9-]+)\)",
        clause_body(clause_id),
    )
    assert links == [anchor], f"{clause_id} needs one exact focused explanation link"
    assert anchor in reference_anchors, f"{clause_id} focused anchor is missing"


def focused_owner(clause_ids):
    owners = []
    for reference in sorted((ROOT / "lc-coding/references").glob("*.md")):
        source_lines = "\n".join(
            line
            for line in reference.read_text(encoding="utf-8").splitlines()
            if line.startswith("Source clauses:")
        )
        if set(re.findall(r"\bLC-[A-Z]+-\d{3}\b", source_lines)).intersection(
            clause_ids
        ):
            owners.append(reference.relative_to(ROOT).as_posix())
    return owners


acceptance_reference_path = "lc-coding/references/loop-acceptance-boundary.md"
verification_reference_path = "lc-coding/references/verification-de-duplication.md"
assert focused_owner(ACCEPTANCE_CLAUSES) == [acceptance_reference_path]
assert focused_owner(VERIFICATION_CLAUSES) == [verification_reference_path]


def focused_reference(relative, expected_clauses, expected_sections):
    text = (ROOT / relative).read_text(encoding="utf-8")
    sections = re.findall(
        r'(?ms)^<a id="([a-z0-9-]+)"></a>\n## ([^\n]+)\n\n(.*?)(?=^<a id="|\Z)',
        text,
    )
    assert len(sections) == expected_sections, f"{relative}: unexpected focused section count"
    source_lines = []
    anchors = set()
    for anchor, _, section in sections:
        anchors.add(anchor)
        lines = [line for line in section.splitlines() if line.startswith("Source clauses:")]
        assert len(lines) == 1, f"{relative}#{anchor}: needs one Source clauses line"
        source_lines.extend(lines)
    actual = set(re.findall(r"\bLC-[A-Z]+-\d{3}\b", "\n".join(source_lines)))
    assert actual == expected_clauses, f"{relative}: unrelated source clauses {actual}"
    return anchors


acceptance_anchors = focused_reference(
    acceptance_reference_path, ACCEPTANCE_CLAUSES, 3
)
verification_anchors = focused_reference(
    verification_reference_path, VERIFICATION_CLAUSES, 3
)
acceptance_links = {
    "LC-ACCEPT-001": "per-run-terminal-decision",
    "LC-ACCEPT-002": "owner-gap-lineage",
    "LC-ACCEPT-003": "post-security-terminal-decision",
}
for clause_id, anchor in acceptance_links.items():
    links = re.findall(
        r"\[Owner terminal decision guidance\]"
        r"\(lc-coding/references/loop-acceptance-boundary\.md#([a-z0-9-]+)\)",
        clause_body(clause_id),
    )
    assert links == [anchor], f"{clause_id} needs one exact focused link"
    assert anchor in acceptance_anchors
verification_links = re.findall(
    r"\[Verification evidence guidance\]"
    r"\(lc-coding/references/verification-de-duplication\.md#([a-z0-9-]+)\)",
    clause_body("LC-VERIFY-001"),
)
assert verification_links == ["layered-independent-verification"]
assert "layered-independent-verification" in verification_anchors

callers = active_callers()
if callers:
    errors.append(f"active retired-reference callers: {callers}")

assert not errors, "\n".join(errors)
print("PASS: retired references have one focused owner and no active callers")
