from pathlib import Path
import copy
import importlib.util
import json


root = Path(__file__).resolve().parents[2]
module_path = root / "lc-coding/scripts/validate_project.py"
spec = importlib.util.spec_from_file_location("validate_project", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

for function in [
    "validate_workflow_subtrees",
    "validate_product_subtree_baseline",
    "validate_ui_subtree_baseline_preflight",
]:
    assert hasattr(module, function), f"missing {function}"


implemented_workflows = [
    {
        "Workflow ID": "WF-BOOK",
        "Classification (CORE/EXTRA)": "CORE",
        "Implementation status": "IMPLEMENTED",
        "Subtree path": "product/workflows/booking",
        "Component version": "1.4.0",
        "Content hash": "sha256:" + "1" * 64,
        "API contract / evidence": "API-WF-BOOK-v1 / D2-API-BOOK",
        "MCP contract / evidence": "MCP-WF-BOOK-v1 / D2-MCP-BOOK",
        "UI subtree references": "UI-WEB, UI-OPS",
        "Simulation subtree references": "SIM-PRIMARY, SIM-LOAD",
        "Primary mainline": "YES",
    },
    {
        "Workflow ID": "WF-REMIND",
        "Classification (CORE/EXTRA)": "EXTRA",
        "Implementation status": "IMPLEMENTED",
        "Subtree path": "product/workflows/reminders",
        "Component version": "0.3.0",
        "Content hash": "sha256:" + "2" * 64,
        "API contract / evidence": "API-WF-REMIND-v1 / D2-API-REMIND",
        "MCP contract / evidence": "MCP-WF-REMIND-v1 / D2-MCP-REMIND",
        "UI subtree references": "UI-WEB",
        "Simulation subtree references": "SIM-LOAD",
        "Primary mainline": "NO",
    },
    {
        "Workflow ID": "WF-ANALYTICS",
        "Classification (CORE/EXTRA)": "EXTRA",
        "Implementation status": "UNIMPLEMENTED",
        "Subtree path": "NOT_APPLICABLE",
        "Component version": "NOT_APPLICABLE",
        "Content hash": "NOT_APPLICABLE",
        "API contract / evidence": "NOT_APPLICABLE",
        "MCP contract / evidence": "NOT_APPLICABLE",
        "UI subtree references": "NONE",
        "Simulation subtree references": "NONE",
        "Primary mainline": "NO",
    },
]
assert module.validate_workflow_subtrees(implemented_workflows) == []

core_without_mcp = copy.deepcopy(implemented_workflows)
core_without_mcp[0]["MCP contract / evidence"] = "NOT_APPLICABLE"
assert any("MCP" in error for error in module.validate_workflow_subtrees(core_without_mcp))

extra_without_api = copy.deepcopy(implemented_workflows)
extra_without_api[1]["API contract / evidence"] = ""
assert any("API" in error for error in module.validate_workflow_subtrees(extra_without_api))

empty_extra_claiming_capability = copy.deepcopy(implemented_workflows)
empty_extra_claiming_capability[2]["API contract / evidence"] = "API-EMPTY"
assert any(
    "unimplemented EXTRA" in error
    for error in module.validate_workflow_subtrees(empty_extra_claiming_capability)
)

baseline_rows = [
    {
        "Subtree type": "UI",
        "Subtree ID": "UI-WEB",
        "Path": "product/ui/web",
        "Component version": "1.8.0",
        "Content hash": "sha256:" + "3" * 64,
        "Classification": "NOT_APPLICABLE",
        "API evidence": "NOT_APPLICABLE",
        "MCP evidence": "NOT_APPLICABLE",
        "Primary mainline": "YES",
        "Related subtree IDs": "WF-BOOK",
    },
    {
        "Subtree type": "UI",
        "Subtree ID": "UI-OPS",
        "Path": "product/ui/operations",
        "Component version": "1.2.0",
        "Content hash": "sha256:" + "4" * 64,
        "Classification": "NOT_APPLICABLE",
        "API evidence": "NOT_APPLICABLE",
        "MCP evidence": "NOT_APPLICABLE",
        "Primary mainline": "NO",
        "Related subtree IDs": "WF-BOOK",
    },
    {
        "Subtree type": "WORKFLOW",
        "Subtree ID": "WF-BOOK",
        "Path": "product/workflows/booking",
        "Component version": "1.4.0",
        "Content hash": "sha256:" + "1" * 64,
        "Classification": "CORE",
        "API evidence": "D2-API-BOOK",
        "MCP evidence": "D2-MCP-BOOK",
        "Primary mainline": "YES",
        "Related subtree IDs": "UI-WEB, UI-OPS, SIM-PRIMARY, SIM-LOAD",
    },
    {
        "Subtree type": "SIMULATION",
        "Subtree ID": "SIM-PRIMARY",
        "Path": "product/simulations/primary",
        "Component version": "2.1.0",
        "Content hash": "sha256:" + "5" * 64,
        "Classification": "NOT_APPLICABLE",
        "API evidence": "NOT_APPLICABLE",
        "MCP evidence": "NOT_APPLICABLE",
        "Primary mainline": "YES",
        "Related subtree IDs": "WF-BOOK",
    },
    {
        "Subtree type": "SIMULATION",
        "Subtree ID": "SIM-LOAD",
        "Path": "product/simulations/load",
        "Component version": "1.0.0",
        "Content hash": "sha256:" + "6" * 64,
        "Classification": "NOT_APPLICABLE",
        "API evidence": "NOT_APPLICABLE",
        "MCP evidence": "NOT_APPLICABLE",
        "Primary mainline": "NO",
        "Related subtree IDs": "WF-BOOK",
    },
]
assert module.validate_product_subtree_baseline(
    baseline_rows, "MAINLINE-BOOKING", "OWNER_CONFIRMED: OA-PB-001"
) == []

nested_simulations = copy.deepcopy(baseline_rows)
nested_simulations[4]["Path"] = "product/simulations/primary/load"
assert any(
    "Simulation" in error and "peer" in error
    for error in module.validate_product_subtree_baseline(
        nested_simulations, "MAINLINE-BOOKING", "OWNER_CONFIRMED: OA-PB-001"
    )
)

mainline_without_ui = copy.deepcopy(baseline_rows)
for row in mainline_without_ui:
    if row["Subtree type"] == "UI":
        row["Primary mainline"] = "NO"
assert any(
    "UI" in error
    for error in module.validate_product_subtree_baseline(
        mainline_without_ui, "MAINLINE-BOOKING", "OWNER_CONFIRMED: OA-PB-001"
    )
)


def read(relative):
    return (root / relative).read_text(encoding="utf-8")


current_authority = "\n".join(
    read(relative)
    for relative in [
        "SPEC.md",
        "lc-coding/SKILL.md",
        "lc-coding/references/project-initialization.md",
        "lc-coding/references/dual-end-design.md",
        "lc-coding/references/simulation-world.md",
        "lc-coding/references/feature-slice-and-integration.md",
        "lc-coding/references/integration-baseline-lock.md",
        "lc-coding/templates/PRODUCT-BASELINE-HANDOFF.md",
        "lc-coding/templates/FEATURE-SLICE.md",
        "lc-coding/templates/INTEGRATION-BASELINE.md",
    ]
)
for marker in [
    "one project Git/GitHub repository",
    "logical subtree",
    "Multiple UI, Workflow, and Simulation",
    "peer Simulation",
    "worktree is optional",
    "API and MCP",
    "Primary product mainline",
    "exact project commit",
    "component version",
    "content hash",
]:
    assert marker in current_authority, marker

for obsolete in [
    "Build one versioned Simulation World",
    "UI independent GitHub repository / baseline path(s)",
    "UI independent Private GitHub repository",
    "UI source baseline lives in its own Git repository",
]:
    assert obsolete not in current_authority, obsolete

workflow_map = read("lc-coding/templates/WORKFLOW-MAP.md")
assert "- Primary product mainline ID:" in workflow_map
for column in [
    "Implementation status",
    "Subtree path",
    "Component version",
    "Content hash",
    "API contract / evidence",
    "MCP contract / evidence",
    "UI subtree references",
    "Simulation subtree references",
    "Primary mainline",
]:
    assert column in workflow_map, column

simulation_map = read("lc-coding/templates/SIMULATION-WORLD.md")
assert "- Primary product mainline ID:" in simulation_map
assert "Simulation ID" in simulation_map
assert "Subtree path" in simulation_map
assert "Peer simulations do not nest" in simulation_map

handoff = read("lc-coding/templates/PRODUCT-BASELINE-HANDOFF.md")
for marker in [
    "Project repository identity",
    "Project frozen exact commit SHA",
    "Locked logical subtrees",
    "Primary product mainline ID",
    "Primary mainline Owner confirmation",
]:
    assert marker in handoff, marker

ui_map = read("lc-coding/templates/UI-MAP.md")
assert "- Primary product mainline ID:" in ui_map
for marker in [
    "path UTF-8 bytes + NUL + Git mode + NUL + lowercase blob SHA-256 hex + LF",
    "same algorithm for UI, Workflow, and Simulation",
    "must match their canonical Maps",
    "MAJOR.MINOR.PATCH",
]:
    assert marker in current_authority + handoff, marker

project_start = read("lc-coding/templates/PROJECT-START.md")
assert "One total project repository" in project_start
assert "Pre-create empty product subtrees: NO" in project_start

lifecycle = json.loads(read("lc-coding/contracts/lifecycle.json"))
phases = json.loads(read("lc-coding/contracts/phases.json"))
status = json.loads(read("lc-coding/templates/STATUS.json"))
expected = [
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
assert lifecycle["mainline"] == expected
assert phases["mainline_unchanged"] is True
manifest = json.loads(read("MANIFEST.json"))
assert manifest["product_subtree_governance"] == {
    "repository_default": "ONE_TOTAL_PROJECT_REPOSITORY",
    "subtree_types": ["UI", "WORKFLOW", "SIMULATION"],
    "simulation_relationship": "PEER_ONLY",
    "worktree_policy": "OPTIONAL_CONSTRUCTION_ISOLATION",
    "implemented_workflow_interfaces": ["API", "MCP"],
    "primary_mainline_owner_confirmed": True,
    "baseline_identity": ["project_commit", "subtree_path", "component_version", "content_hash"],
}
framework = json.dumps((lifecycle, phases, status)).lower()
for forbidden in [
    "workflow_core",
    "subtree_phase",
    "subtree_gate",
    "subtree_state",
    "primary_mainline_gate",
    "simulation_child",
]:
    assert forbidden not in framework

print("PASS: one-repository logical subtrees, Workflow interfaces, and baseline mainline are governed")
