from pathlib import Path
import copy
import importlib.util
import json
import tempfile

root = Path(__file__).resolve().parents[2]
module_path = root / "lc-coding/scripts/validate_project.py"
spec = importlib.util.spec_from_file_location("validate_project", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert hasattr(module, "validate_slice_execution_preflight")


def validate(fields, fingerprint):
    return module.validate_slice_execution_preflight(fields, fingerprint, "owner/product")

low = {
    "complexity": {
        "product_uncertainty": "LOW",
        "system_coupling": "LOW",
        "real_risk": "LOW",
        "irreversibility": "LOW",
        "novelty": "LOW",
    },
    "depth": {"rationale": "", "analysis": [], "materials": [], "evidence": []},
    "recommended_loop": "SLK",
}

ready = {
    "Actor intent": "Owner reviews the recovered product flow",
    "Product outcome": "The recovered flow completes visibly",
    "Product Baseline trace": "PB-002",
    "Workflow references": "WF-RECOVER",
    "UI references": "UI-RECOVER",
    "Scenario IDs / versions": "SCN-RECOVER-v2",
    "State / data / permission trace": "STATE-2 / DATA-2 / ROLE-OWNER",
    "Exception / recovery trace": "RECOVERY-2",
    "Impact Analysis ID": "IA-002",
    "Integration Baseline ID": "IB-002",
    "Required Run IDs": "RUN-002",
    "D0-D3 evidence plan": "D0 local; D1 boundary; D2 outcome; D3 E2E",
    "Normal Loop Owner Acceptance route(s)": "RUN-002 acceptance",
    "Project repository / exact baseline commit": "https://github.com/owner/product :: " + "a" * 40,
    "Applicable UI subtree ID / path": "UI-RECOVER :: product/ui/recovery",
    "UI component version": "2.0.0",
    "UI content hash": "sha256:" + "b" * 64,
    "UI content hash scope / manifest evidence": "HASH_SCOPE: UI-HASH-MANIFEST-002",
    "UI Product / Integration Baseline identity": "MATCH: UI-LOCK-002",
    "UI subtree comparison before Slice / Run": "MATCH: UI-COMP-START-002",
    "UI comparison before acceptance route": "REQUIRED",
    "Execution Coverage Preflight": "PASS",
    "Coverage gaps / unknowns": "NONE",
    "Cross-layer connection evidence": "PROVEN: D3-001",
    "First Proving Run requirement": "NOT_REQUIRED",
    "First Proving Run ID / evidence": "D3-001",
    "First Proving Run production E2E scenario": "SCN-RECOVER-v1",
    "Failure expansion rule": "HALT_EXPANSION",
    "Fingerprint depth response": "CONCISE_TRUTHFUL",
}
assert validate(ready, low) == []

unreferenced_proof = copy.deepcopy(ready)
unreferenced_proof["Cross-layer connection evidence"] = "PROVEN"
assert any(
    "PROVEN requires an evidence pointer" in error
    for error in validate(unreferenced_proof, low)
)

blocked = copy.deepcopy(ready)
blocked["Execution Coverage Preflight"] = "BLOCKED"
assert any(
    "must PASS" in error
    for error in validate(blocked, low)
)

missing_coverage = copy.deepcopy(ready)
missing_coverage["UI references"] = ""
assert any(
    "UI references" in error
    for error in validate(missing_coverage, low)
)

unproven = copy.deepcopy(ready)
unproven["Cross-layer connection evidence"] = "UNPROVEN"
unproven["First Proving Run requirement"] = "NOT_REQUIRED"
unproven["First Proving Run ID / evidence"] = ""
assert any(
    "first proving Run" in error
    for error in validate(unproven, low)
)

unproven["First Proving Run requirement"] = "REQUIRED"
unproven["First Proving Run ID / evidence"] = "RUN-002"
assert validate(unproven, low) == []

unproven_not_required = copy.deepcopy(unproven)
unproven_not_required["Required Run IDs"] = "RUN-OTHER"
assert any(
    "first proving Run in Required Run IDs" in error
    for error in validate(unproven_not_required, low)
)

unproven_without_halt = copy.deepcopy(unproven)
unproven_without_halt["Failure expansion rule"] = "CONTINUE_EXPANSION"
assert any(
    "halt expansion" in error
    for error in validate(unproven_without_halt, low)
)

high = copy.deepcopy(low)
high["complexity"]["real_risk"] = "HIGH"
high["depth"]["rationale"] = "Recovery changes persistent state."
high["depth"]["evidence"] = ["recovery risk investigation"]
risk_blind = copy.deepcopy(ready)
risk_blind["Fingerprint depth response"] = "CONCISE_TRUTHFUL"
assert any(
    "HIGH or UNKNOWN" in error
    for error in validate(risk_blind, high)
)
risk_blind["Fingerprint depth response"] = "SMALLER_INDEPENDENT_RUNS"
assert validate(risk_blind, high) == []

internal_method_leak = copy.deepcopy(ready)
internal_method_leak["GO plan"] = "copied downstream internals"
assert any(
    "internal method field" in error
    for error in validate(internal_method_leak, low)
)

template = (root / "lc-coding/templates/FEATURE-SLICE.md").read_text(encoding="utf-8")
assert "First Proving Run" in template
assert "tracer task" not in template.lower()
for marker in (
    "Integration Route ID",
    "Integration candidate ID / exact hash",
    "Selected entry interface",
    "Connected route evidence",
    "Phase-2-only demonstration evidence",
):
    assert marker in template

with tempfile.TemporaryDirectory() as td:
    temporary_root = Path(td)
    lc = temporary_root / "project/.lccoding"
    (lc / "slices").mkdir(parents=True)
    outside = temporary_root / "outside.md"
    outside.write_text("# outside\n", encoding="utf-8")
    assert module.resolve_active_slice(lc, str(outside)) is None
    assert module.resolve_active_slice(lc, "../../outside.md") is None

print("PASS: Slice preflight covers product execution without absorbing Loop internals")
