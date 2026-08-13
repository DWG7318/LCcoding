import hashlib
from pathlib import Path
import re


root = Path(__file__).resolve().parents[2]
spec = (root / "SPEC.md").read_text(encoding="utf-8")

HISTORICAL_ROOT = (root / "docs/superpowers").resolve()
HISTORICAL_BOUNDARY = (HISTORICAL_ROOT / "README.md").resolve()
HISTORICAL_MARKERS = (
    "Artifact class: HISTORICAL_DESIGN_RECORDS",
    "Authority: NON_NORMATIVE",
    "Use: PROVENANCE_ONLY",
    "Validator/runtime input: FORBIDDEN",
    "Current semantic authority: ../../SPEC.md",
    "descendant wording never overrides current authority",
)


def contained_under(path, parent):
    candidate = Path(path).resolve(strict=False)
    boundary = Path(parent).resolve(strict=False)
    try:
        candidate.relative_to(boundary)
        return True
    except ValueError:
        return False


def historical_kind(path):
    candidate = Path(path).resolve(strict=False)
    if candidate == HISTORICAL_BOUNDARY:
        return "BOUNDARY"
    if contained_under(candidate, HISTORICAL_ROOT / "specs") or contained_under(
        candidate, HISTORICAL_ROOT / "plans"
    ):
        return "HISTORICAL_RECORD"
    return "ACTIVE_OR_OTHER"


assert historical_kind(HISTORICAL_ROOT / "specs/x.md") == "HISTORICAL_RECORD"
assert historical_kind(HISTORICAL_ROOT / "plans/x.md") == "HISTORICAL_RECORD"
assert historical_kind(HISTORICAL_BOUNDARY) == "BOUNDARY"
assert historical_kind(HISTORICAL_ROOT / "specs/../README.md") == "BOUNDARY"
assert historical_kind(root / "docs/other.md") == "ACTIVE_OR_OTHER"
assert historical_kind(root / "lc-coding/references/x.md") == "ACTIVE_OR_OTHER"

assert HISTORICAL_BOUNDARY.is_file(), "missing historical design boundary"
boundary_text = HISTORICAL_BOUNDARY.read_text(encoding="utf-8")
for marker in HISTORICAL_MARKERS:
    assert marker in boundary_text, marker
assert "Source clauses:" not in boundary_text
boundary_readmes = sorted(
    path.resolve()
    for path in HISTORICAL_ROOT.rglob("README.md")
    if path.is_file()
)
assert boundary_readmes == [HISTORICAL_BOUNDARY]

HISTORICAL_RECORD_HASHES = {
    "docs/superpowers/plans/2026-08-06-lccoding-bi-github-windows-release.md": "30f23b334ad110d5263c2ac9e754a81bc2740010ea6244f56ccdd90c69b5063d",
    "docs/superpowers/plans/2026-08-12-lccoding-2.7.0-structure-consolidation-implementation-plan.md": "7d6f5fa8f08f379c024d088ef2fb6f676f44f2ee5904a7da4b49daa78174cd27",
    "docs/superpowers/specs/2026-08-05-lccoding-bi-one-click-react-design.md": "d945eab23b20a977b906f8e38396b2ba0283284924df8ba77469ec3728af9db2",
    "docs/superpowers/specs/2026-08-06-lccoding-bi-github-windows-release-design.md": "2f1281949b527c2efbef99bf9a32b5b098aa2c04a8a9760bbfa7a865056e7f51",
    "docs/superpowers/specs/2026-08-10-cross-phase-execution-methods-design.md": "14c7460ee661c94df34d0ff8985e50b225799db57591649e3deb79ae82d92e51",
    "docs/superpowers/specs/2026-08-12-lccoding-2.7.0-structure-consolidation-design.md": "c48b659333f1b6252029faebe50476016f561ba9c6818de1a138e86fe4b5604e",
}
actual_historical_records = {
    path.relative_to(root).as_posix()
    for directory in (HISTORICAL_ROOT / "specs", HISTORICAL_ROOT / "plans")
    for path in directory.rglob("*.md")
    if path.is_file()
}
assert actual_historical_records == set(HISTORICAL_RECORD_HASHES)
for relative, expected_hash in HISTORICAL_RECORD_HASHES.items():
    assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == expected_hash

EXPECTED_TITLES = {
    "LC-AUTH-001": "Owner authority and method boundary",
    "LC-AUTH-002": "Single semantic authority and project truth",
    "LC-PHASE-001": "Initial",
    "LC-PHASE-002": "Product Formation",
    "LC-PHASE-003": "Real Product Integration",
    "LC-PHASE-004": "Delivery Preparation",
    "LC-FORM-001": "Calabash and Simulation-first formation",
    "LC-FORM-002": "Workflow, UI, and Simulation product units",
    "LC-FORM-003": "Product Baseline and primary product mainline",
    "LC-INTEG-001": "Feature Slice and real integration proof",
    "LC-INTEG-002": "One-way UI lock",
    "LC-INTEG-003": "Impact, mutability, and evidence reuse",
    "LC-RUN-001": "Cross-phase Run call contract",
    "LC-RUN-002": "Run start and terminal receipt",
    "LC-RUN-003": "Execution-method selection and aggregate scope",
    "LC-VERIFY-001": "Layered independent verification",
    "LC-ACCEPT-001": "Per-Run Loop Owner Acceptance",
    "LC-ACCEPT-002": "Owner gap closure lineage",
    "LC-ACCEPT-003": "Post-Security Owner Acceptance",
    "LC-SEC-001": "Centralized vulnerability closure",
    "LC-SEC-002": "Security evidence invalidation",
    "LC-DELIVERY-001": "Protected delivery",
    "LC-BI-001": "Built-in BI method boundary",
    "LC-BI-002": "BI responsibility and compatibility boundary",
    "LC-COMPAT-001": "Names, baselines, migration, and versioning",
    "LC-COMPAT-002": "Shared Loop Control transition",
}
EXPECTED = set(EXPECTED_TITLES)

heading_re = re.compile(
    r"(?m)^### (LC-(?:AUTH|PHASE|FORM|INTEG|RUN|VERIFY|ACCEPT|SEC|DELIVERY|BI|COMPAT)-\d{3}) — (.+)$"
)
headings = heading_re.findall(spec)
found_ids = [clause_id for clause_id, _ in headings]
assert len(found_ids) == len(set(found_ids)), "duplicate normative clause heading"
assert set(found_ids) == EXPECTED, (
    f"closed clause IDs missing/unknown: missing={sorted(EXPECTED - set(found_ids))}; "
    f"unknown={sorted(set(found_ids) - EXPECTED)}"
)
assert dict(headings) == EXPECTED_TITLES, "clause ID/title binding drifted"

all_level_three = re.findall(r"(?m)^### (.+)$", spec)
assert len(all_level_three) == len(EXPECTED), "every level-three section must be a clause"

anchors = re.findall(r'(?m)^<a id="(lc-[a-z]+-\d{3})"></a>$', spec)
assert len(anchors) == len(set(anchors)), "duplicate clause anchor"
assert {anchor.upper() for anchor in anchors} == EXPECTED
for clause_id, title in EXPECTED_TITLES.items():
    anchor = clause_id.lower()
    assert f'<a id="{anchor}"></a>\n### {clause_id} — {title}' in spec

index_match = re.search(
    r"(?ms)^## Normative clause index\n\n(.+?)(?=^## )", spec
)
assert index_match, "missing the sole normative clause index"
index_rows = re.findall(
    r"(?m)^\| \[(LC-[A-Z]+-\d{3})\]\(#(lc-[a-z]+-\d{3})\) \| ([^|]+?) \|$",
    index_match.group(1),
)
assert len(index_rows) == len(EXPECTED), "clause index must contain one row per clause"
assert {clause_id for clause_id, _, _ in index_rows} == EXPECTED
for clause_id, anchor, topic in index_rows:
    assert anchor == clause_id.lower()
    assert topic.strip() == EXPECTED_TITLES[clause_id]

mentioned_ids = set(re.findall(r"\bLC-[A-Z]+-\d{3}\b", spec))
assert mentioned_ids == EXPECTED, "SPEC may not cite unknown clause IDs"
assert "PRODUCT_BASELINE_READY" not in spec


def clause_body(clause_id: str) -> str:
    start = re.search(
        rf"(?m)^### {re.escape(clause_id)} — .+$", spec
    )
    assert start
    end = re.search(r"(?m)^(?:### LC-|## )", spec[start.end() :])
    return spec[start.end() : start.end() + end.start()] if end else spec[start.end() :]


PRODUCT_FORMATION_REFERENCE = root / "lc-coding/references/product-formation.md"
assert PRODUCT_FORMATION_REFERENCE.is_file(), "missing focused Product Formation explanation"
product_formation_reference = PRODUCT_FORMATION_REFERENCE.read_text(encoding="utf-8")
source_clause_lines = [
    line
    for line in product_formation_reference.splitlines()
    if line.startswith("Source clauses:")
]
product_source_links = re.findall(
    r"\[(LC-FORM-\d{3})\]\(\.\./\.\./SPEC\.md#(lc-form-\d{3})\)",
    "\n".join(source_clause_lines),
)
assert {clause_id for clause_id, _ in product_source_links} == {
    "LC-FORM-001",
    "LC-FORM-002",
    "LC-FORM-003",
}
assert all(anchor == clause_id.lower() for clause_id, anchor in product_source_links)
assert set(re.findall(r"\bLC-[A-Z]+-\d{3}\b", "\n".join(source_clause_lines))) == {
    "LC-FORM-001",
    "LC-FORM-002",
    "LC-FORM-003",
}, "Product Formation guidance must cite only its three semantic-core clauses"
focused_sections = re.findall(
    r"(?ms)^## [^\n]+\n\n(.*?)(?=^## |\Z)", product_formation_reference
)
assert len(focused_sections) <= 3
assert all(section.count("Source clauses:") == 1 for section in focused_sections)
reference_anchors = set(
    re.findall(r'(?m)^<a id="([a-z0-9-]+)"></a>$', product_formation_reference)
)
for clause_id in ("LC-FORM-001", "LC-FORM-002", "LC-FORM-003"):
    focused_links = re.findall(
        r"\[Product Formation guidance\]\(lc-coding/references/product-formation\.md#([a-z0-9-]+)\)",
        clause_body(clause_id),
    )
    assert len(focused_links) == 1, f"{clause_id} needs one focused explanation link"
    assert focused_links[0] in reference_anchors, f"{clause_id} focused anchor is missing"


required_semantics = {
    "LC-AUTH-001": (
        "Owner decides product meaning",
        "AI completes routine engineering",
        "runtime, session control, and Agent execution kernels",
    ),
    "LC-AUTH-002": (
        "`SPEC.md` is the sole complete semantic authority",
        "`status.json` is the single authoritative project-status record",
        "non-authoritative projection",
    ),
    "LC-PHASE-001": (
        "`INITIAL`",
        "Proposal Readiness",
        "Project Initialization",
        "`INITIAL_READY`",
    ),
    "LC-PHASE-002": (
        "`PRODUCT_FORMATION`",
        "Mandatory Calabash Upgrade",
        "Product Baseline Handoff is mechanically validated and accepted",
        "no new gate",
    ),
    "LC-PHASE-003": (
        "Real Product Integration",
        "`ENGINEERING_RUNS`",
        "Feature Slice is the first lifecycle work",
        "`ALL_REQUIRED_RUNS_ACCEPTED`",
    ),
    "LC-PHASE-004": (
        "`DELIVERY_PREPARATION`",
        "centralized vulnerability",
        "Post-Security Owner Acceptance",
        "`DELIVERY_READY`",
    ),
    "LC-FORM-001": (
        "Calabash Definition Baseline",
        "Product Simulation World",
        "Run Control Simulation",
        "Snake",
        "Scorpion",
    ),
    "LC-FORM-002": (
        "peer logical subtrees",
        "one total project repository",
        "both API and MCP",
        "CORE",
        "EXTRA",
        "worktree",
    ),
    "LC-FORM-003": (
        "LCCoding Product Baseline",
        "Primary product mainline",
        "commit and content hash are authoritative",
        "component version",
    ),
    "LC-INTEG-001": (
        "real UI operation",
        "API/MCP-backed Workflow",
        "real state/data/side effect",
        "visible UI result",
        "Simulation covers the same capability",
    ),
    "LC-INTEG-002": (
        "`UI = LOCKED`",
        "Owner may initiate or explicitly approve",
        "Baseline Change Request",
        "must not silently overwrite user material",
    ),
    "LC-INTEG-003": (
        "Impact Analysis",
        "`CONTROLLED_MUTABLE`",
        "`VERSIONED_MUTABLE`",
        "reuse",
    ),
    "LC-RUN-001": (
        "calling phase",
        "phase-owned objective",
        "evidence return target",
        "acceptance condition",
    ),
    "LC-RUN-002": (
        "`RUN-HANDOFF.md` is the Run-start contract",
        "`LOOP-OWNER-ACCEPTANCE.md` is the terminal receipt",
        "Run completion does not advance a phase",
    ),
    "LC-RUN-003": (
        "another registered execution method",
        "minimal registry",
        "required Real Product Integration Runs",
        "not a lifecycle node",
    ),
    "LC-VERIFY-001": (
        "D0",
        "D1",
        "D2",
        "D3",
        "independent",
        "reuse",
    ),
    "LC-ACCEPT-001": (
        "Every normal Run",
        "Loop Owner Acceptance",
        "`LOOP_OWNER_ACCEPTED`",
    ),
    "LC-ACCEPT-002": (
        "Owner gap ID",
        "correction Run",
        "delta re-verification",
        "delta Owner re-acceptance",
    ),
    "LC-ACCEPT-003": (
        "`VULNERABILITY_CLOSED`",
        "Post-Security Owner Acceptance",
        "unchanged prior product acceptance",
    ),
    "LC-SEC-001": (
        "centralized",
        "fresh independent Security Auditor",
        "`VULNERABILITY_CLOSED`",
    ),
    "LC-SEC-002": (
        "product or security surface",
        "invalidates",
        "Post-Security Owner Acceptance",
        "Delivery remains blocked",
    ),
    "LC-DELIVERY-001": (
        "Delivery Method Q&A",
        "Owner Policy",
        "approved product assets",
        "Source code is excluded",
    ),
    "LC-BI-001": (
        "built-in BI",
        "read-only",
        "second status authority",
        "BI Window Always-on-top",
    ),
    "LC-BI-002": (
        "method compatibility asset",
        "status adapter",
        "execution-method adapter identities",
        "no Calabash identity",
    ),
    "LC-COMPAT-001": (
        "compatibility ID",
        "Real Product Integration",
        "LCCoding Method Baseline",
        "copy-on-write",
        "2.6.0",
    ),
    "LC-COMPAT-002": (
        "`LCCODING_LOOP_CONTROL`",
        "not a fourth execution method",
        "transitional binding",
        "`RUN_PATROL_HEARTBEAT`",
        "`CHECKER_WAKE_HEARTBEAT`",
    ),
}

assert set(required_semantics) == EXPECTED
for clause_id, markers in required_semantics.items():
    body = clause_body(clause_id)
    assert body.strip(), f"empty clause: {clause_id}"
    for marker in markers:
        assert marker in body, f"{clause_id} missing semantic relation: {marker}"


relationship_requirements = (
    (
        "LC-COMPAT-002",
        "Worker-to-frozen-Checker wake ladder",
        (
            "Only a Worker may use this ladder to wake its frozen Checker",
            "direct send",
            "same-task read/list/unarchive",
            "`CHECKER_WAKE_HEARTBEAT`",
            "`PENDING_WAKE`",
            "120 seconds",
            "`WAKE_ACK`",
            "not a generic Checker or Supervisor escalation ladder",
        ),
    ),
    (
        "LC-COMPAT-002",
        "Supervisor no-wait boundary",
        (
            "positive-duration, looping, and wait-all `wait_threads` are forbidden",
            "zero-time snapshot",
            "must not wait online",
        ),
    ),
    (
        "LC-COMPAT-002",
        "single Run Patrol lifecycle",
        (
            "one fast, non-technical Patrol conversation",
            "one `RUN_PATROL_HEARTBEAT`",
            "10/15/30 minutes",
            "creates no conversation",
            "removes its heartbeat and archives itself",
        ),
    ),
    (
        "LC-COMPAT-002",
        "Patrol observation-only scope",
        (
            "unexplained stoppage",
            "pending wake",
            "actual subagent use",
            "forbidden Supervisor wait",
            "duplicate Patrol or heartbeat",
            "Pin provenance",
            "terminal closure",
            "must not perform product or engineering work",
            "must not report engineering progress",
        ),
    ),
    (
        "LC-COMPAT-002",
        "actual-subagent distinction",
        (
            "`spawn_agent`",
            "`delegate_task`",
            "hidden-agent",
            "background-agent",
            "GO, CELL, task, role, or the word subtask",
            "is not itself a subagent operation",
        ),
    ),
    (
        "LC-COMPAT-002",
        "task Pin provenance",
        (
            "Agents must not Pin tasks",
            "Owner UI",
            "item-specific Owner authorization",
            "unknown provenance",
            "must not auto-unpin",
        ),
    ),
    (
        "LC-COMPAT-002",
        "capacity-before-dispatch",
        (
            "Capacity is evaluated before dispatch",
            "`PASS`",
            "`SPLIT_REQUIRED`",
            "`CAPACITY_BLOCKED`",
            "Worker must not self-split",
        ),
    ),
    (
        "LC-COMPAT-002",
        "progress ownership",
        (
            "Worker reports delivered CELL `x/y`",
            "Checker reports accepted CELL `x/y`",
            "Supervisor reports GO/Level/Run scope",
            "Patrol reports no engineering progress",
        ),
    ),
    (
        "LC-COMPAT-002",
        "model policy and transitional adoption",
        (
            "Luna with `xhigh`",
            "Terra with `xhigh`",
            "Sol with `xhigh`",
            "`ultra` requires item-specific Owner authorization",
            "verified local control",
            "trusted runtime attestations",
            "approved release explicitly retires",
        ),
    ),
    (
        "LC-DELIVERY-001",
        "Delivery Preparation and actual Delivery boundary",
        (
            "Delivery Preparation conducts customer-specific Delivery Method Q&A",
            "current Post-Security Owner Acceptance",
            "delivery decisions",
            "package protection",
            "Actual Delivery begins only after `DELIVERY_READY`",
            "Q&A is not actual Delivery",
        ),
    ),
    (
        "LC-DELIVERY-001",
        "Owner-confirmed rights boundary",
        (
            "no-resale",
            "redistribution",
            "sublicense",
            "repackaging",
            "unauthorized modification",
            "reverse engineering",
            "transfer",
            "control removal",
            "Owner Policy or an Owner decision",
            "must not be invented as default legal facts",
        ),
    ),
)

for clause_id, relation, markers in relationship_requirements:
    body = clause_body(clause_id)
    for marker in markers:
        assert marker in body, f"{clause_id} {relation} missing: {marker}"


PROJECTIONS = (
    root / "CONSTITUTION.md",
    root / "README.md",
    root / "README.zh-CN.md",
    root / "lc-coding/SKILL.md",
)
BI_PRODUCT_CONTRACT = root / "lc-coding/references/built-in-bi.md"
BI_IMPLEMENTATION_NAVIGATION = root / "lc-coding/bi/README.md"
assert BI_PRODUCT_CONTRACT.is_file()
assert BI_IMPLEMENTATION_NAVIGATION.is_file()
bi_product = BI_PRODUCT_CONTRACT.read_text(encoding="utf-8")
bi_implementation = BI_IMPLEMENTATION_NAVIGATION.read_text(encoding="utf-8")
bi_source_ids = set(re.findall(r"\bLC-[A-Z]+-\d{3}\b", "\n".join(
    line for line in bi_product.splitlines() if line.startswith("Source clauses:")
)))
assert bi_source_ids == {"LC-BI-001", "LC-BI-002"}
assert "Source clauses:" not in bi_implementation
assert BI_PRODUCT_CONTRACT not in PROJECTIONS
assert BI_IMPLEMENTATION_NAVIGATION not in PROJECTIONS
assert "Authority: NON_NORMATIVE_IMPLEMENTATION_NAVIGATION" in bi_implementation
assert "../references/built-in-bi.md" in bi_implementation

for readme in (root / "README.md", root / "README.zh-CN.md"):
    text = readme.read_text(encoding="utf-8")
    assert "lc-coding/references/built-in-bi.md" in text
    assert "lc-coding/bi/README.md" in text
assert HISTORICAL_BOUNDARY not in PROJECTIONS
for historical in [HISTORICAL_BOUNDARY, *(root / path for path in HISTORICAL_RECORD_HASHES)]:
    assert historical not in PROJECTIONS
    assert not contained_under(historical, root / "lc-coding/references")

validator_source = (root / "lc-coding/scripts/validate_repository.py").read_text(
    encoding="utf-8"
)
for historical in [HISTORICAL_BOUNDARY, *(root / path for path in HISTORICAL_RECORD_HASHES)]:
    assert historical.relative_to(root).as_posix() not in validator_source
MODAL_RE = re.compile(
    r"(?i)\b(?:must|shall|required|never|forbidden|prohibited|may not|cannot)\b"
    r"|(?:必须|不得|禁止|不可|只能)"
)
SOURCE_LINE_RE = re.compile(r"(?m)^Source clauses: (.+)$")
SOURCE_LINK_RE = re.compile(
    r"\[(LC-[A-Z]+-\d{3})\]\(([^)#]+)#(lc-[a-z]+-\d{3})\)"
)
MARKDOWN_ANCHORED_LINK_RE = re.compile(r"\[([^]]+)\]\(([^)#]+)#([^)]+)\)")
SEMANTIC_NAVIGATION = {
    "fixed_lifecycle_proportional_depth": {
        "labels": {
            "fixed lifecycle, proportional depth",
            "fixed lifecycle and proportional depth",
            "固定生命周期与比例深度",
        },
        "clause_id": "LC-AUTH-002",
    },
}


def projection_sections(text: str):
    headings = list(re.finditer(r"(?m)^## ([^\n]+)$", text))
    preface = text[: headings[0].start()] if headings else text
    sections = []
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        sections.append((heading.group(1).strip(), text[heading.end() : end]))
    return preface, sections


def projection_errors(path: Path, text: str):
    errors = []
    preface, sections = projection_sections(text)
    if MODAL_RE.search(preface):
        errors.append("normative preface has no section-level source")
    for title, body in sections:
        source_lines = SOURCE_LINE_RE.findall(body)
        if MODAL_RE.search(body) and len(source_lines) != 1:
            errors.append(f"{title}: normative section requires exactly one Source clauses line")
        if not source_lines:
            continue
        links = SOURCE_LINK_RE.findall(source_lines[0])
        residue = SOURCE_LINK_RE.sub("", source_lines[0]).replace(",", "").strip()
        if not links or residue:
            errors.append(f"{title}: Source clauses line is not closed and parseable")
            continue
        source_ids = [clause_id for clause_id, _, _ in links]
        if len(source_ids) != len(set(source_ids)):
            errors.append(f"{title}: duplicate source clause")
        for clause_id, relative, anchor in links:
            if clause_id not in EXPECTED:
                errors.append(f"{title}: unknown source clause {clause_id}")
                continue
            target = (path.parent / relative).resolve()
            if target != (root / "SPEC.md").resolve():
                errors.append(f"{title}: source does not resolve to canonical SPEC")
            if anchor != clause_id.lower():
                errors.append(f"{title}: clause/anchor mismatch")
    return errors


for projection in PROJECTIONS:
    projection_text = projection.read_text(encoding="utf-8")
    errors = projection_errors(projection, projection_text)
    assert not errors, f"{projection.relative_to(root)} projection drift: {errors}"
    assert "SPEC.md" in projection_text, f"{projection.relative_to(root)} lacks SPEC navigation"
    local_targets = []
    for target in re.findall(r"\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)", projection_text):
        if target.startswith(("http://", "https://")):
            continue
        resolved = (projection.parent / target).resolve()
        assert resolved.exists(), f"{projection.relative_to(root)} missing link target: {target}"
        local_targets.append(resolved)
    references_root = (root / "lc-coding/references").resolve()
    assert any(
        target.parent == references_root for target in local_targets
    ), f"{projection.relative_to(root)} lacks focused-reference navigation"
    assert "Real Product Integration" in projection_text
    assert "ENGINEERING_RUNS" in projection_text
    assert not re.search(r"(?m)^#{1,6} .*ENGINEERING_RUNS", projection_text)


def normalized_navigation_label(label: str) -> str:
    return re.sub(r"\s+", " ", label).strip().casefold()


fixed_lifecycle_navigation = SEMANTIC_NAVIGATION[
    "fixed_lifecycle_proportional_depth"
]
expected_labels = {
    normalized_navigation_label(label)
    for label in fixed_lifecycle_navigation["labels"]
}
expected_clause_id = fixed_lifecycle_navigation["clause_id"]
assert expected_clause_id in EXPECTED
for projection in PROJECTIONS[:3]:
    matches = []
    projection_text = projection.read_text(encoding="utf-8")
    for label, target, anchor in MARKDOWN_ANCHORED_LINK_RE.findall(projection_text):
        if normalized_navigation_label(label) in expected_labels:
            matches.append((target, anchor))
    assert len(matches) == 1, (
        f"{projection.relative_to(root)} must expose one fixed-lifecycle semantic link"
    )
    target, anchor = matches[0]
    assert (projection.parent / target).resolve() == (root / "SPEC.md").resolve()
    assert anchor == expected_clause_id.lower(), (
        f"{projection.relative_to(root)} fixed-lifecycle navigation maps to {anchor}, "
        f"expected {expected_clause_id.lower()}"
    )

valid_projection_sample = """# Projection

## Governed summary

Source clauses: [LC-AUTH-001](SPEC.md#lc-auth-001)

The Owner must decide product meaning.
"""
assert not projection_errors(root / "README.md", valid_projection_sample)
assert projection_errors(
    root / "README.md", valid_projection_sample.replace("Source clauses: ", "Sources: ")
)
assert projection_errors(
    root / "README.md", valid_projection_sample.replace("LC-AUTH-001", "LC-AUTH-999")
)
assert projection_errors(
    root / "README.md", valid_projection_sample.replace("#lc-auth-001", "#lc-phase-001")
)

constitution = (root / "CONSTITUTION.md").read_text(encoding="utf-8")
for marker in (
    "Principle Zero",
    "Owner decides product meaning",
    "CONTINUE",
    "NARROW_REDIRECT",
    "HOLD",
    "TERMINATE",
    "final Owner Acceptance",
    "delivery rights",
):
    assert marker in constitution, f"constitutional Owner right missing: {marker}"

skill_projection = (root / "lc-coding/SKILL.md").read_text(encoding="utf-8")
_, parsed_skill_sections = projection_sections(skill_projection)
skill_sections = dict(parsed_skill_sections)
stop_projection = skill_sections["Start, stop, and route"]
stop_order = ["STOP", "preserve evidence", "route", "resume"]
positions = [stop_projection.index(marker) for marker in stop_order]
assert positions == sorted(positions), "SKILL stop/route order drifted"
for projection in PROJECTIONS:
    text = projection.read_text(encoding="utf-8")
    assert "cross-phase execution axis" in text.casefold()
    assert "not a lifecycle node" in text.casefold()

print("PASS: SPEC exposes one closed 26-clause semantic authority graph")
