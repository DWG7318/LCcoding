from pathlib import Path
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
    "LOOP_ENGINEERING",
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
    "protected Loop Governance report",
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
sequence = reference[reference.index("## 10."):reference.index("## 11.")]
for marker in [
    "### LCCoding 2.5.0 one-click sequence",
    "typed Rust reader",
    "no-argument single-flight `get_snapshot`",
    "current-user NSIS package",
]:
    assert marker in sequence, marker
plain_sequence = sequence.replace("`", "")
assert plain_sequence.index("typed Rust reader") < plain_sequence.index("get_snapshot")
assert plain_sequence.index("get_snapshot") < plain_sequence.index("current-user NSIS package")
for contradiction in [
    "C. Implement the typed Rust reader",
    "D. Add the narrow Tauri bridge",
    "E. Atomically update every existing root release carrier",
]:
    assert contradiction not in sequence, contradiction

assert (root / "VERSION").read_text(encoding="utf-8").strip() == "2.5.0"
print("PASS: BI adds only protected subtree and Loop governance reports")
