from pathlib import Path
import re


root = Path(__file__).resolve().parents[2]
spec = (root / "SPEC.md").read_text(encoding="utf-8")

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

print("PASS: SPEC exposes one closed 26-clause semantic authority graph")
