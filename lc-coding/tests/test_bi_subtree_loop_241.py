from pathlib import Path
import hashlib
import json
import re


root = Path(__file__).resolve().parents[2]

expected_mainline = [
    "PROPOSAL_READINESS",
    "PROJECT_INITIALIZATION",
    "CALABASH_DRAFT",
    "WORKFLOW_UI_SIMULATION",
    "MANDATORY_CALABASH_UPGRADE",
    "PRODUCT_BASELINE",
    "FEATURE_SLICE",
    "FEATURE_INTEGRATION",
    "FINAL_VERIFICATION",
    "OWNER_ACCEPTANCE",
    "DELIVERY",
]
expected_steps = [
    ("PROPOSAL_READINESS", "proposal"),
    ("PROJECT_INITIALIZATION", "candidate"),
    ("INITIAL_READY", None),
    ("CALABASH_DRAFT", "calabash"),
    ("SIMULATION_WORLD_FOUNDATION", "simulation"),
    ("WORKFLOW_CAPABILITY_END", "workflow"),
    ("UI_PRODUCT_SURFACE_END", "ui"),
    ("CALABASH_UPGRADE_READY", None),
    ("MANDATORY_CALABASH_UPGRADE", None),
    ("PRODUCT_BASELINE", "baseline"),
    ("FEATURE_SLICE_EXECUTION_COVERAGE", None),
    ("UI_LOCKED_INTEGRATION_BASELINE", None),
    ("LOOP_RUN_D0_D3", "loop_governance"),
    ("LOOP_OWNER_ACCEPTANCE", None),
    ("ALL_REQUIRED_RUNS_ACCEPTED", None),
    ("CENTRALIZED_VULNERABILITY_AUDIT", None),
    ("SECURITY_REMEDIATION", None),
    ("SECURITY_REAUDIT_VULNERABILITY_CLOSURE", None),
    ("POST_SECURITY_OWNER_ACCEPTANCE", None),
    ("DELIVERY_METHOD_QA", None),
    ("DELIVERY_PACKAGE_GUARD_READY", None),
]

lifecycle = json.loads(
    (root / "lc-coding/contracts/lifecycle.json").read_text(encoding="utf-8")
)
assert lifecycle["mainline"] == expected_mainline

model = (root / "lc-coding/bi/src/model/snapshot.ts").read_text(encoding="utf-8")
layout = model[model.index("const PHASE_LAYOUT"):model.index("type RowKind")]
actual_steps = [
    (step, report or None)
    for step, report in re.findall(
        r'\["([A-Z0-9_]+)",\s*(?:"([a-z_]+)"|null)\]', layout
    )
]
assert actual_steps == expected_steps
assert len(actual_steps) == 21

report_type = model[model.index("export type ReportId"):model.index("export type StepId")]
assert re.findall(r'\| "([a-z_]+)"', report_type) == [
    "proposal",
    "candidate",
    "calabash",
    "simulation",
    "workflow",
    "ui",
    "baseline",
    "loop_governance",
]

candidate_rows_280 = model[
    model.index("const REPORT_ROWS_280"):model.index(
        "const REPORT_ROWS: Readonly<Record<SnapshotSchema"
    )
]
assert re.findall(r'\["(row\.[a-z_]+)", "([a-z_]+)"\]', candidate_rows_280) == [
    ("row.operations_agent_integration", "record"),
    ("row.product_agent_integration", "agent_status"),
    ("row.runtime_adapter", "safe_identity"),
    ("row.dual_agent_isolation", "record"),
    ("row.product_slice_progress", "metric"),
    ("row.operations_slice_progress", "metric"),
]

tokens = (root / "lc-coding/bi/src/styles/tokens.css").read_text(encoding="utf-8")
app_css = (root / "lc-coding/bi/src/styles/app.css").read_text(encoding="utf-8")
for marker in [
    "--state-complete: #198754",
    "--state-error: #c92a2a",
    "--state-active: #2563eb",
    "--state-pending: #6b7280",
]:
    assert marker in tokens
for marker in [
    "width: 300px",
    "height: 480px",
    "grid-template-rows: 34px minmax(0, 1fr) 32px",
    'font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif',
    "font-size: 14px",
]:
    assert marker in app_css

tauri_root = root / "lc-coding/bi/src-tauri"
capability = json.loads(
    (tauri_root / "capabilities/main.json").read_text(encoding="utf-8")
)
expected_commands = [
    "bind_project",
    "choose_project",
    "get_snapshot",
    "is_pinned",
    "set_pinned",
]
assert capability["permissions"] == [
    f"allow-{command.replace('_', '-')}" for command in expected_commands
]
runtime = "\n".join(
    (tauri_root / relative).read_text(encoding="utf-8")
    for relative in ["build.rs", "src/lib.rs"]
)
for command in expected_commands:
    assert command in runtime
assert not (root / "lc-coding/scripts/project_bi.py").exists()

authority = "\n".join(
    (root / relative).read_text(encoding="utf-8")
    for relative in ["SPEC.md", "lc-coding/SKILL.md", "lc-coding/references/built-in-bi.md"]
)
for marker in [
    "protected Product Baseline report",
    "protected Execution Method Governance report",
    "lccoding-bi.exe --project",
    "sanitized Snapshot",
]:
    assert marker in authority, marker
for forbidden in [
    "BI controls Worker",
    "BI creates Heartbeat",
    "BI archives patrol",
    "BI pins method tasks",
]:
    assert forbidden not in authority

reference = (root / "lc-coding/references/built-in-bi.md").read_text(encoding="utf-8")
implementation = (root / "lc-coding/bi/README.md").read_text(encoding="utf-8")
protected_report = (root / "lc-coding/bi/src/components/ProtectedReport.tsx").read_text(
    encoding="utf-8"
)
for marker in [
    "src/model/snapshot.ts",
    "src-tauri/src/projection.rs",
    "npm run test:dom",
    "npm run visual:candidates",
    "cargo test",
    "scripts/package-release.ps1",
    "scripts/verify-loop-releases.ps1",
    ".github/workflows/release-bi.yml",
]:
    assert marker in implementation, marker
for product_marker in [
    "read-only projection",
    "four phases",
    "21-step",
    "eight report joins",
    "status.json",
    "Non-goals",
]:
    assert product_marker in reference, product_marker
for agent_marker in [
    "### Agent-native candidate summary",
    "Operations Agent integration",
    "Product Agent applicability / integration",
    "safe Runtime Adapter ID/version",
    "dual-Agent isolation",
    "Product Slice count",
    "Operations Slice count",
    "not an Agent console",
]:
    assert agent_marker in reference, agent_marker
for forbidden_element in ["<a", "href=", "download=", "clipboard", "navigator."]:
    assert forbidden_element not in protected_report, forbidden_element

release_paths = {
    ".github/workflows/release-bi.yml": "540f77590b345cffe05663605be0c74a00fe26349b39a3df92c58cd97f920e35",
    "lc-coding/bi/scripts/package-release.ps1": "6171ba9c3ddf8888029e40dbe089053087ca52eb9c5784526bd39b83e85a05c8",
    "lc-coding/bi/scripts/verify-loop-releases.ps1": "03ae6c0aaf823808694261fb7734a7280e17d9b0022ece70d0c4304f3e37eabe",
    "lc-coding/bi/tests/packaging/nsis-contract.ps1": "47cd5609a9fb26630697fe1595f5ca1733d2c8f8ec66541f6e5cc5cacf801aeb",
}
for relative, expected_hash in release_paths.items():
    assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == expected_hash

assert (root / "VERSION").read_text(encoding="utf-8").strip() == "2.7.0"
print("PASS: BI keeps protected subtree and Execution Method Governance reports")
