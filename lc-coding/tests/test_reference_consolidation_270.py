import ast
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
SELF = Path(__file__).resolve()
RETIRED_REFERENCE = "lc-coding/references/method-mainline.md"
RETIRED_BASENAME = Path(RETIRED_REFERENCE).name
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
            isinstance(target, ast.Name) and target.id == "RETIRED_REFERENCE"
            for target in targets
        ):
            declarations.append(node)
    assert len(declarations) == 1, "retired reference must have one explicit declaration"
    declaration = declarations[0]
    for line_number in range(declaration.lineno, declaration.end_lineno + 1):
        lines[line_number - 1] = "\n"
    return "".join(lines)


def source_references_retired(relative, text):
    normalized = text.replace("\\", "/")
    if RETIRED_REFERENCE in normalized or RETIRED_BASENAME in normalized:
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
        if (
            RETIRED_REFERENCE in normalized_value
            or RETIRED_BASENAME in normalized_value
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

self_declaration = f"RETIRED_REFERENCE = {RETIRED_REFERENCE!r}\n"
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
retired_path = ROOT / RETIRED_REFERENCE
if retired_path.exists():
    errors.append(f"retired reference still exists: {RETIRED_REFERENCE}")
if RETIRED_REFERENCE in required_paths():
    errors.append("repository validator still requires retired reference")

manifest = json.loads((ROOT / "FILE_HASHES.json").read_text(encoding="utf-8"))
if RETIRED_REFERENCE in manifest:
    errors.append("hash manifest still publishes retired reference")

callers = active_callers()
if callers:
    errors.append(f"active retired-reference callers: {callers}")

assert not errors, "\n".join(errors)
print("PASS: duplicate mainline reference is absent from the active release graph")
