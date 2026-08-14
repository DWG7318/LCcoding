from pathlib import Path
import re


root = Path(__file__).resolve().parents[2]
spec_path = root / "SPEC.md"
spec = spec_path.read_text(encoding="utf-8-sig")

BASE_TITLES = {
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

AGENT_NATIVE_TITLES = {
    "LC-AGENT-001": "Agent classes, applicability, and required Operations Agent",
    "LC-AGENT-002": "Agent Configuration Baseline and Runtime neutrality",
    "LC-AGENT-003": "Dual-Agent isolation and controlled operations",
    "LC-INTEG-004": "Agent-native topology and Slice proof",
    "LC-SEC-003": "Agent security, degradation, and replacement",
}

EXPECTED_TITLES = BASE_TITLES | AGENT_NATIVE_TITLES
EXPECTED_IDS = set(EXPECTED_TITLES)
HEADING_RE = re.compile(r"(?m)^### (LC-[A-Z]+-[0-9]{3}) — ([^\n]+)$")
ANCHOR_RE = re.compile(r'(?m)^<a id="(lc-[a-z]+-[0-9]{3})"></a>$')
INDEX_SECTION_RE = re.compile(
    r"(?ms)^## Normative clause index\n\n(.+?)(?=^## )"
)
INDEX_ROW_RE = re.compile(
    r"(?m)^\| \[(LC-[A-Z]+-[0-9]{3})\]\(#(lc-[a-z]+-[0-9]{3})\) \| ([^|]+) \|$"
)


def authority_errors(text: str) -> list[str]:
    errors: list[str] = []
    headings = HEADING_RE.findall(text)
    ids = [clause_id for clause_id, _ in headings]
    if len(ids) != len(set(ids)):
        errors.append("duplicate heading")
    if set(ids) != EXPECTED_IDS:
        errors.append(
            f"closed IDs missing={sorted(EXPECTED_IDS - set(ids))} "
            f"unknown={sorted(set(ids) - EXPECTED_IDS)}"
        )
    if dict(headings) != EXPECTED_TITLES:
        errors.append("heading/title binding")

    anchors = ANCHOR_RE.findall(text)
    expected_anchors = {clause_id.lower() for clause_id in EXPECTED_IDS}
    if len(anchors) != len(set(anchors)):
        errors.append("duplicate anchor")
    if set(anchors) != expected_anchors:
        errors.append("anchor set")

    index_match = INDEX_SECTION_RE.search(text)
    if not index_match:
        errors.append("normative index missing")
        return errors
    rows = INDEX_ROW_RE.findall(index_match.group(1))
    row_ids = [clause_id for clause_id, _, _ in rows]
    if len(row_ids) != len(set(row_ids)):
        errors.append("duplicate index row")
    if set(row_ids) != EXPECTED_IDS:
        errors.append("index ID set")
    for clause_id, anchor, title in rows:
        if anchor != clause_id.lower() or title.strip() != EXPECTED_TITLES.get(clause_id):
            errors.append(f"index binding {clause_id}")

    mentioned = set(re.findall(r"\bLC-[A-Z]+-[0-9]{3}\b", text))
    if mentioned != EXPECTED_IDS:
        errors.append("mentioned ID set")
    return errors


def clause_sections(text: str) -> dict[str, str]:
    matches = list(HEADING_RE.finditer(text))
    return {
        match.group(1): text[
            match.end() : matches[index + 1].start()
            if index + 1 < len(matches)
            else len(text)
        ]
        for index, match in enumerate(matches)
    }


def require_all(body: str, markers: tuple[str, ...], clause_id: str) -> None:
    missing = [marker for marker in markers if marker not in body]
    assert not missing, f"{clause_id} missing semantic markers: {missing}"


errors = authority_errors(spec)
assert not errors, "; ".join(errors)

duplicate = spec + "\n### LC-AGENT-001 — Agent classes, applicability, and required Operations Agent\n"
assert "duplicate heading" in authority_errors(duplicate)
unknown = spec + "\n### LC-AGENT-999 — Unknown Agent authority\n"
assert any("unknown=['LC-AGENT-999']" in error for error in authority_errors(unknown))

sections = clause_sections(spec)
require_all(
    sections["LC-AGENT-001"],
    (
        "Construction Agent",
        "Product Agent",
        "Operations Agent",
        "`APPLICABLE_CORE`",
        "`APPLICABLE_EXTRA`",
        "`NOT_APPLICABLE`",
        "required for every 2.8 project",
        "two independent logical Agents",
        "role switching",
    ),
    "LC-AGENT-001",
)
require_all(
    sections["LC-AGENT-002"],
    (
        "Owner decides",
        "Calabash defines",
        "LCCoding construction implements",
        "independent Verification",
        "Owner accepts",
        "authorized Runtime Adapter mechanically loads",
        "Runtime-neutral",
        "LCagent",
        "reference Runtime",
        "Secrets",
        "third configuration Agent",
    ),
    "LC-AGENT-002",
)
require_all(
    sections["LC-AGENT-003"],
    (
        "Agent ID",
        "session/context",
        "private memory store",
        "vector index",
        "retriever",
        "write credentials",
        "encryption key",
        "system prompt",
        "prompt cache",
        "API/MCP/tool credentials",
        "Policy",
        "Action Catalog",
        "audit",
        "Kill Switch",
        "shared authoritative product state is not Agent memory",
        "`MAINTENANCE_REQUEST`",
        "`SERVICE_STATUS_UPDATE`",
        "Natural-language messages cannot convey administrator authority",
        "online training",
        "observe → diagnose → propose",
        "deterministic action",
        "`OWNER_APPROVAL_REQUIRED`",
        "`CALABASH_PREAUTHORIZED_BOUNDED`",
    ),
    "LC-AGENT-003",
)
require_all(
    sections["LC-INTEG-004"],
    (
        "`REAL_PRODUCT_INTEGRATION`",
        "`ENGINEERING_RUNS`",
        "`SELECT`",
        "`COMPOSE`",
        "`FEDERATE`",
        "`RETIRE`",
        "does not require physical consolidation",
        "Slice class is exactly one of {`PRODUCT`, `OPERATIONS`}",
        "Product Agent",
        "API/MCP-backed Workflow",
        "visible result",
        "telemetry/log/event",
        "deterministic maintenance action",
        "verification/rollback",
        "UI one-way Owner lock",
        "Simulation",
    ),
    "LC-INTEG-004",
)
require_all(
    sections["LC-SEC-003"],
    (
        "prompt injection",
        "privilege escalation",
        "memory leakage",
        "model drift and unavailability",
        "tool and secret protection",
        "Agent isolation",
        "fallback",
        "Kill Switch",
        "audit",
        "Runtime replacement",
        "Operations Agent failure",
        "Product Agent failure",
        "CORE",
        "adds no new security or Delivery gate",
    ),
    "LC-SEC-003",
)

require_all(
    sections["LC-PHASE-001"],
    ("Agent responsibilities", "permissions", "degradation"),
    "LC-PHASE-001",
)
require_all(
    sections["LC-PHASE-002"],
    ("Product Agent", "Operations Agent configuration"),
    "LC-PHASE-002",
)
require_all(
    sections["LC-PHASE-003"],
    ("2.8 new-write machine ID", "`REAL_PRODUCT_INTEGRATION`", "final production execution topology"),
    "LC-PHASE-003",
)
require_all(
    sections["LC-PHASE-004"],
    ("Agent-specific", "existing `DELIVERY_READY` gate"),
    "LC-PHASE-004",
)
require_all(
    sections["LC-BI-001"],
    (
        "Operations Agent integration status",
        "Product Agent applicability",
        "Runtime Adapter identity",
        "isolation status",
        "`PRODUCT` and `OPERATIONS` Slice progress",
        "cannot control an Agent",
    ),
    "LC-BI-001",
)
require_all(
    sections["LC-COMPAT-001"],
    (
        "2.8 new writes",
        "`REAL_PRODUCT_INTEGRATION`",
        "2.6/2.7",
        "`ENGINEERING_RUNS`",
        "copy-on-write",
        "cannot claim 2.8",
        "does not promote historical evidence",
    ),
    "LC-COMPAT-001",
)

agent_native_text = "\n".join(sections[clause_id] for clause_id in AGENT_NATIVE_TITLES)
assert "fifth phase" not in agent_native_text
assert "Agent phase" not in agent_native_text
assert "new lifecycle gate" not in agent_native_text
assert "LCCoding implements the Runtime" not in agent_native_text

print("PASS: SPEC exposes a closed 31-clause Agent-native authority graph")
