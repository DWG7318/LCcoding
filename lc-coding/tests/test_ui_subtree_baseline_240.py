from pathlib import Path
import copy
import importlib.util
import json


root = Path(__file__).resolve().parents[2]
module_path = root / "lc-coding/scripts/validate_project.py"
spec = importlib.util.spec_from_file_location("validate_project", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert hasattr(module, "validate_ui_subtree_baseline_preflight")
assert not hasattr(module, "validate_ui_private_baseline_preflight")

PRODUCT_REPOSITORY = "owner/product"


def validate(fields, product_repository=PRODUCT_REPOSITORY):
    return module.validate_ui_subtree_baseline_preflight(fields, product_repository)


ready = {
    "Project repository / exact baseline commit": "https://github.com/owner/product :: " + "a" * 40,
    "Applicable UI subtree ID / path": "UI-WEB :: product/ui/web",
    "UI component version": "1.8.0",
    "UI content hash": "sha256:" + "b" * 64,
    "UI content hash scope / manifest evidence": "HASH_SCOPE: UI-HASH-MANIFEST-240",
    "UI Product / Integration Baseline identity": "MATCH: UI-LOCK-240",
    "UI subtree comparison before Slice / Run": "MATCH: UI-COMP-START-240",
    "UI comparison before acceptance route": "REQUIRED",
}
assert validate(ready) == []

for invalid_identity in [
    "",
    "LOCAL_ONLY",
    "https://github.com/owner/product",
    "https://github.com/owner/product :: main",
    "https://github.com/owner/product :: latest",
    "https://github.com/owner/product :: abc1234",
]:
    blocked = copy.deepcopy(ready)
    blocked["Project repository / exact baseline commit"] = invalid_identity
    assert validate(blocked)

wrong_repository = copy.deepcopy(ready)
wrong_repository["Project repository / exact baseline commit"] = (
    "https://github.com/owner/ui-separate :: " + "a" * 40
)
assert any("total project repository" in error for error in validate(wrong_repository))

for invalid_subtree in [
    "",
    "UI-WEB",
    "UI-WEB :: C:/product/ui",
    "UI-WEB :: ../ui",
    "UI-WEB :: https://example.com/ui",
]:
    blocked = copy.deepcopy(ready)
    blocked["Applicable UI subtree ID / path"] = invalid_subtree
    assert validate(blocked)

missing_version = copy.deepcopy(ready)
missing_version["UI component version"] = ""
assert any("component version" in error for error in validate(missing_version))

for invalid_hash in ["", "latest", "sha256:abc123", "b" * 64]:
    blocked = copy.deepcopy(ready)
    blocked["UI content hash"] = invalid_hash
    assert validate(blocked)

missing_hash_scope = copy.deepcopy(ready)
missing_hash_scope["UI content hash scope / manifest evidence"] = ""
assert validate(missing_hash_scope)

unauthorized_delta = copy.deepcopy(ready)
unauthorized_delta["UI subtree comparison before Slice / Run"] = "DIFF: unapproved UI change"
assert validate(unauthorized_delta)

mismatched_baselines = copy.deepcopy(ready)
mismatched_baselines["UI Product / Integration Baseline identity"] = "MISMATCH: different commit"
assert validate(mismatched_baselines)

assert validate(ready, product_repository=None)
assert validate(ready, product_repository="UNKNOWN")

missing_acceptance_check = copy.deepcopy(ready)
missing_acceptance_check["UI comparison before acceptance route"] = "PENDING"
assert validate(missing_acceptance_check)


def require(relative, *markers):
    text = (root / relative).read_text(encoding="utf-8")
    for marker in markers:
        assert marker in text, f"{relative}: {marker}"


require(
    "SPEC.md",
    "one total project repository",
    "exact project commit",
    "applicable UI subtree",
    "component version",
    "content hash",
    "must not silently overwrite user material",
)
require(
    "lc-coding/SKILL.md",
    "one total project repository",
    "applicable UI subtree",
    "total-project exact commit",
    "never use a branch, tag, `HEAD`, worktree, or `latest` as the lock",
)
require(
    "lc-coding/references/integration-baseline-lock.md",
    "applicable UI logical subtree",
    "total-project repository/exact commit",
    "logical subtree means a product path",
    "Baseline Change Request",
)
require(
    "lc-coding/templates/PRODUCT-BASELINE-HANDOFF.md",
    "Project repository identity",
    "Project frozen exact commit SHA",
    "Locked logical subtrees",
    "Component version",
    "Content hash",
)
require(
    "lc-coding/templates/INTEGRATION-BASELINE.md",
    "Project repository identity",
    "Project exact frozen commit SHA",
    "Applicable UI subtree ID / path",
    "UI component version",
    "UI content hash",
    "Branch / latest accepted: NO",
)
require(
    "lc-coding/templates/BASELINE-CHANGE-REQUEST.md",
    "Owner decision / approval evidence",
    "Project repository identity",
    "New project commit differs from prior lock: YES",
    "New UI component version",
    "Product Baseline Handoff update",
    "Affected evidence re-verification",
)
require(
    "lc-coding/templates/FEATURE-SLICE.md",
    "Project repository / exact baseline commit",
    "Applicable UI subtree ID / path",
    "UI component version",
    "UI content hash",
    "UI Product / Integration Baseline identity",
    "UI subtree comparison before Slice / Run",
    "UI comparison before acceptance route",
)
require(
    "lc-coding/templates/FINAL-FEATURE-VERIFICATION.md",
    "locked total-project repository and exact commit",
    "Applicable UI subtree ID / path / component version / content hash",
    "UI comparison before acceptance",
    "Unauthorized UI delta",
)
require(
    "lc-coding/templates/AGENT-RULE.md",
    "one total project repository",
    "never silently overwrite user material",
)
require(
    "lc-coding/templates/OWNER-POLICY.md",
    "Default product repository visibility: OWNER_DECISION_REQUIRED",
    "Product subtree repository policy: ONE_TOTAL_PROJECT_REPOSITORY",
)

current_authority = "\n".join(
    (root / relative).read_text(encoding="utf-8")
    for relative in [
        "SPEC.md",
        "lc-coding/SKILL.md",
        "lc-coding/references/integration-baseline-lock.md",
        "lc-coding/templates/PRODUCT-BASELINE-HANDOFF.md",
        "lc-coding/templates/INTEGRATION-BASELINE.md",
        "lc-coding/templates/FEATURE-SLICE.md",
    ]
)
for obsolete in [
    "UI independent GitHub repository / baseline path(s)",
    "UI independent Private GitHub repository",
    "UI source baseline lives in its own Git repository",
    "UI baseline repository visibility: GITHUB_PRIVATE_REQUIRED",
]:
    assert obsolete not in current_authority

lifecycle = json.loads((root / "lc-coding/contracts/lifecycle.json").read_text(encoding="utf-8"))
phases = json.loads((root / "lc-coding/contracts/phases.json").read_text(encoding="utf-8"))
status = json.loads((root / "lc-coding/templates/STATUS.json").read_text(encoding="utf-8"))
assert [phase["id"] for phase in phases["phases"]] == [
    "INITIAL",
    "PRODUCT_FORMATION",
    "ENGINEERING_RUNS",
    "DELIVERY_PREPARATION",
]
framework = json.dumps((lifecycle, phases, status)).upper()
for forbidden in ["SUBTREE_BASELINE_PHASE", "SUBTREE_BASELINE_STATE", "SUBTREE_BASELINE_GATE"]:
    assert forbidden not in framework

print("PASS: UI lock pins an applicable logical subtree in the total project repository")
