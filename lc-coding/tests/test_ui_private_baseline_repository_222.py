from pathlib import Path
import copy
import importlib.util
import json

root = Path(__file__).resolve().parents[2]
module_path = root / "lc-coding/scripts/validate_project.py"
spec = importlib.util.spec_from_file_location("validate_project", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert hasattr(module, "validate_ui_private_baseline_preflight")

PRODUCT_REPOSITORY = "owner/product"


def validate(fields, product_repository=PRODUCT_REPOSITORY):
    return module.validate_ui_private_baseline_preflight(fields, product_repository)

ready = {
    "UI independent GitHub repository / baseline path(s)": "https://github.com/owner/ui-private :: ui/",
    "UI Owner-control / PRIVATE evidence": "PRIVATE: GH-VIS-002 | OWNER_CONTROLLED: OWNER-CTRL-002",
    "UI frozen exact remote commit SHA": "a" * 40,
    "UI content hash": "sha256:" + "b" * 64,
    "UI content hash scope / manifest evidence": "HASH_SCOPE: UI-HASH-MANIFEST-002",
    "UI remote commit push / resolve evidence": "REMOTE_RESOLVED: GH-COMMIT-002",
    "UI recovery reference": "RECOVERY: github.com/owner/ui-private@commit:ui/",
    "UI Product / Integration Baseline identity": "MATCH: UI-LOCK-002",
    "UI baseline comparison before Slice / Run": "MATCH: UI-COMP-START-002",
    "UI comparison before acceptance route": "REQUIRED",
}
assert validate(ready) == []

for invalid_repo in [
    "", "file:///local/ui", "LOCAL_ONLY", "SCREENSHOT_ONLY", "BUILD_ONLY",
    "https://evilgithub.com/owner/ui-private :: ui/",
    "https://token@github.com/owner/ui-private :: ui/",
    "https://github.com/owner/ui-private",
]:
    blocked = copy.deepcopy(ready)
    blocked["UI independent GitHub repository / baseline path(s)"] = invalid_repo
    assert validate(blocked)

for invalid_visibility in [
    "", "PRIVATE", "PRIVATE: arbitrary", "PRIVATE: GH-VIS | OWNER_CONTROLLED:",
    "PUBLIC: GH-VIS | OWNER_CONTROLLED: OWNER-CTRL",
    "UNKNOWN: GH-VIS | OWNER_CONTROLLED: OWNER-CTRL",
]:
    blocked = copy.deepcopy(ready)
    blocked["UI Owner-control / PRIVATE evidence"] = invalid_visibility
    assert validate(blocked)

for invalid_commit in ["", "main", "latest", "HEAD", "v2.0.0", "abc1234", "c" * 39]:
    blocked = copy.deepcopy(ready)
    blocked["UI frozen exact remote commit SHA"] = invalid_commit
    assert validate(blocked)

sha256_ready = copy.deepcopy(ready)
sha256_ready["UI frozen exact remote commit SHA"] = "c" * 64
assert validate(sha256_ready) == []

for invalid_hash in ["", "latest", "sha256:abc123", "b" * 64]:
    blocked = copy.deepcopy(ready)
    blocked["UI content hash"] = invalid_hash
    assert validate(blocked)

missing_hash_scope = copy.deepcopy(ready)
missing_hash_scope["UI content hash scope / manifest evidence"] = ""
assert validate(missing_hash_scope)

missing_remote = copy.deepcopy(ready)
missing_remote["UI remote commit push / resolve evidence"] = ""
assert validate(missing_remote)

missing_recovery = copy.deepcopy(ready)
missing_recovery["UI recovery reference"] = ""
assert validate(missing_recovery)

unauthorized_delta = copy.deepcopy(ready)
unauthorized_delta["UI baseline comparison before Slice / Run"] = "DIFF: unapproved UI change"
assert validate(unauthorized_delta)

mismatched_baselines = copy.deepcopy(ready)
mismatched_baselines["UI Product / Integration Baseline identity"] = "MISMATCH: different commit"
assert validate(mismatched_baselines)

same_as_product = copy.deepcopy(ready)
same_as_product["UI independent GitHub repository / baseline path(s)"] = "https://github.com/owner/product :: ui/"
assert validate(same_as_product)

assert module.validate_ui_private_baseline_preflight(ready, product_repository=None)
assert module.validate_ui_private_baseline_preflight(ready, product_repository="UNKNOWN")

missing_acceptance_check = copy.deepcopy(ready)
missing_acceptance_check["UI comparison before acceptance route"] = "PENDING"
assert validate(missing_acceptance_check)


def require(relative, *markers):
    text = (root / relative).read_text(encoding="utf-8")
    for marker in markers:
        assert marker in text, f"{relative}: {marker}"


require(
    "SPEC.md",
    "complete rebuildable UI source",
    "Owner-controlled independent GitHub repository",
    "must remain `PRIVATE`",
    "product repository visibility",
    "exact remote commit SHA",
    "content hash",
    "canonical tracked-file manifest",
    "branch name or `latest`",
    "Screenshots, exported images, previews, or build artifacts",
    "must not silently overwrite user material",
)
require(
    "lc-coding/SKILL.md",
    "UI source baseline lives in its own Git repository",
    "Owner-controlled independent GitHub repository that remains `PRIVATE`",
    "Product repository visibility never relaxes",
    "remote commit SHA",
    "content hash",
    "restore from the locked Private remote commit or isolate the work",
    "before acceptance, re-prove Owner control, `PRIVATE` visibility, and remote resolution",
)
require(
    "lc-coding/references/integration-baseline-lock.md",
    "PUBLIC or UNKNOWN visibility blocks",
    "exact commit SHA",
    "branch name or `latest` is not an immutable reference",
    "Baseline Change Request",
    "canonical tracked-file manifest",
    "one locked identity tuple",
)
require(
    "lc-coding/templates/PRODUCT-BASELINE-HANDOFF.md",
    "UI independent repository identity / GitHub URL",
    "UI baseline path(s)",
    "UI repository visibility: PRIVATE",
    "UI frozen exact remote commit SHA",
    "UI content hash",
    "UI content hash scope / manifest evidence",
    "UI remote commit push / resolve evidence",
    "UI recovery reference",
)
require(
    "lc-coding/templates/INTEGRATION-BASELINE.md",
    "UI independent Private GitHub repository",
    "UI exact frozen remote commit SHA",
    "UI content hash",
    "UI content hash scope / manifest evidence",
    "Branch / latest accepted: NO",
    "Product Handoff identity match",
)
require(
    "lc-coding/templates/BASELINE-CHANGE-REQUEST.md",
    "Owner decision / approval evidence",
    "Owner-control re-verification",
    "New UI commit differs from prior lock: YES",
    "New UI commit SHA",
    "Private visibility re-verification",
    "Product Baseline Handoff update",
    "Affected evidence re-verification",
)
require(
    "lc-coding/templates/FEATURE-SLICE.md",
    "UI independent GitHub repository / baseline path(s)",
    "UI Owner-control / PRIVATE evidence",
    "UI frozen exact remote commit SHA",
    "UI content hash",
    "UI content hash scope / manifest evidence",
    "UI remote commit push / resolve evidence",
    "UI recovery reference",
    "UI Product / Integration Baseline identity",
    "UI baseline comparison before Slice / Run",
    "UI comparison before acceptance route",
)
require(
    "lc-coding/templates/FINAL-FEATURE-VERIFICATION.md",
    "Locked UI remote / exact commit / content hash",
    "UI comparison before acceptance",
    "UI Owner-control / PRIVATE re-verification before acceptance",
    "UI exact remote commit resolve before acceptance",
    "Unauthorized UI delta",
)
require(
    "lc-coding/templates/AGENT-RULE.md",
    "independent Owner-controlled GitHub repository that remains PRIVATE",
    "never silently overwrite user material",
)
require(
    "lc-coding/templates/OWNER-POLICY.md",
    "Default product repository visibility: OWNER_DECISION_REQUIRED",
    "UI baseline repository visibility: GITHUB_PRIVATE_REQUIRED",
    "no Public override",
)

lifecycle = json.loads((root / "lc-coding/contracts/lifecycle.json").read_text(encoding="utf-8"))
phases = json.loads((root / "lc-coding/contracts/phases.json").read_text(encoding="utf-8"))
status = json.loads((root / "lc-coding/templates/STATUS.json").read_text(encoding="utf-8"))
assert [phase["id"] for phase in phases["phases"]] == [
    "INITIAL", "PRODUCT_FORMATION", "ENGINEERING_RUNS", "DELIVERY_PREPARATION"
]
framework = json.dumps((lifecycle, phases, status)).upper()
for forbidden in ["UI_PRIVATE_BASELINE_PHASE", "UI_PRIVATE_BASELINE_STATE", "UI_PRIVATE_BASELINE_GATE"]:
    assert forbidden not in framework

print("PASS: UI lock requires an Owner-controlled Private GitHub baseline and exact recovery proof")
