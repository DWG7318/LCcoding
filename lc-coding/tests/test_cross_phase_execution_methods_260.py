from pathlib import Path
import json


root = Path(__file__).resolve().parents[2]


def text(relative: str) -> str:
    return (root / relative).read_text(encoding="utf-8")


def require(relative: str, *markers: str) -> None:
    content = text(relative).casefold()
    for marker in markers:
        assert marker.casefold() in content, f"{relative}: {marker}"


skill = text("lc-coding/SKILL.md")
skill_mainline = skill[
    skill.index("## Canonical mainline") : skill.index("Operational meaning:")
]
assert "SLK / CLK / GLK" not in skill_mainline
assert "UI-locked Real Product Integration" in skill_mainline

method_mainline = text("lc-coding/references/method-mainline.md")
mainline_block = method_mainline[
    method_mainline.index("```text") : method_mainline.index("```", method_mainline.index("```text") + 3)
]
assert "SLK / CLK / GLK" not in mainline_block
assert "UI-locked Real Product Integration" in mainline_block

manifest = json.loads(text("MANIFEST.json"))
assert "SLK / CLK / GLK" not in manifest["mainline"]
assert "UI-locked Real Product Integration" in manifest["mainline"]

canonical_manifest = json.loads(text("lc-coding/templates/CANONICAL-MANIFEST.json"))
assert "Selected Loop" not in canonical_manifest["load_order"]
assert "Per-Run Execution Method" in canonical_manifest["load_order"]
assert canonical_manifest["execution_methods"] == []
assert {"slk", "clk", "glk"}.issubset(canonical_manifest)

interpretation_lock = json.loads(text("lc-coding/templates/INTERPRETATION-LOCK.json"))
assert interpretation_lock["manifest_reference"] == "CANONICAL-MANIFEST.json"
assert interpretation_lock["validated_execution_method_ids"] == []

slice_fields = {}
for line in text("lc-coding/templates/FEATURE-SLICE.md").splitlines():
    if line.startswith("- ") and ":" in line:
        key, value = line[2:].split(":", 1)
        slice_fields[key.strip()] = value.strip()
assert {
    "Accepted integration candidate / baseline identity",
    "Required Run IDs",
    "Optional Run IDs",
    "Superseded Run IDs",
    "Invalidated Run IDs",
}.issubset(slice_fields)

for relative in ["README.md", "README.zh-CN.md", "SPEC.md", "lc-coding/SKILL.md"]:
    require(
        relative,
        "INITIAL",
        "PRODUCT_FORMATION",
        "ENGINEERING_RUNS",
        "DELIVERY_PREPARATION",
    )

require(
    "lc-coding/SKILL.md",
    "lifecycle axis",
    "execution-method axis",
    "in any LCCoding phase",
    "not an exhaustive method list",
    "Completing or accepting a Run does not advance a phase",
    "real product integration phase",
)
require(
    "SPEC.md",
    "Workflow, UI, and Simulation are built separately",
    "real product integration",
    "phase-owned objective",
    "returns evidence to the calling phase",
    "another registered execution method",
)
require(
    "lc-coding/references/loop-method-selection.md",
    "any LCCoding phase",
    "one method per Run",
    "not exhaustive",
    "phase gate",
    "compatible evidence and acceptance interface",
)
require(
    "lc-coding/templates/RUN-HANDOFF.md",
    "Artifact role: RUN_START_CONTRACT",
    "Start Contract ID",
    "Start Contract SHA-256",
    "LCCoding phase scope",
    "Phase-owned objective",
    "Frozen Run scope",
    "Explicit exclusions",
    "Selected execution method ID",
    "Selected execution method version",
    "Selected execution method exact hash",
    "Selected execution method canonical interface / contract reference",
    "Evidence return target in calling phase",
    "Readiness result",
)
require(
    "lc-coding/templates/LOOP-OWNER-ACCEPTANCE.md",
    "Artifact role: LOOP_OWNER_ACCEPTANCE_RECEIPT",
    "Run-start contract ID",
    "Run-start contract SHA-256",
    "LCCoding phase scope",
    "Phase-owned objective",
    "Evidence return target in the calling phase",
    "Calling phase gate remains independently evaluated: YES",
)
require(
    "lc-coding/references/built-in-bi.md",
    "Real Product Integration",
    "lifecycle projection",
    "cross-phase method activity",
)

assert "ALL_REQUIRED_RUNS_ACCEPTED" in text("lc-coding/contracts/phases.json")

print("PASS: execution methods are cross-phase and Phase 3 remains real product integration")
