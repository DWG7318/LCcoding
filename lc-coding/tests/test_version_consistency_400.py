from pathlib import Path
import json
import re
import tomllib


ROOT = Path(__file__).resolve().parents[2]
CURRENT = "4.0.0"
INSTALLER = "LCCoding-BI_4.0.0_x64-setup.exe"
PROVENANCE_SCHEMA = "LCCoding 4.0.0 installer provenance"


def text(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def strict_json(relative):
    return json.loads(text(relative))


assert text("VERSION").strip() == CURRENT
manifest = strict_json("MANIFEST.json")
assert manifest["version"] == CURRENT

for relative in (
    "lc-coding/contracts/version-policy.json",
    "lc-coding/contracts/delivery-policy.json",
    "lc-coding/contracts/verification-receipt.json",
    "lc-coding/contracts/vulnerability-closure.json",
    "lc-coding/contracts/lifecycle.json",
    "lc-coding/contracts/phases.json",
):
    assert strict_json(relative)["version"] == CURRENT, relative

canonical = strict_json("lc-coding/templates/CANONICAL-MANIFEST.json")
assert canonical["lccoding"]["version"] == CURRENT
assert canonical["calabash"] == {
    "version": "2.5.0",
    "hash": "sha256:74602032de04ca47c4ccc9d661119ae1d08913dfe0c5361759798697c0310b21",
}

status = strict_json("lc-coding/templates/STATUS.json")
assert status["status_schema_version"] == CURRENT
assert {
    "lccoding_applicability": status["lccoding_applicability"],
    "product_service_strategy": status["product_service_strategy"],
    "service_route_map": status["service_route_map"],
} == {
    "lccoding_applicability": "PENDING",
    "product_service_strategy": "PENDING",
    "service_route_map": "PENDING",
}
assert set(status) == {
    "record_role",
    "status_schema_version",
    "lccoding_applicability",
    "product_service_strategy",
    "service_route_map",
    "project_id",
    "updated_at",
    "initialization_mode",
    "continuity_decision",
    "takeover_readiness",
    "canonical_candidate",
    "existing_project_attestation",
    "existing_project_classification",
    "current_phase",
    "phase_gates",
    "product_baseline",
    "agent_product_formation",
    "agent_slice_integration",
    "proposal",
    "initialization",
    "calabash_draft",
    "workflow",
    "ui",
    "simulation",
    "mandatory_calabash_upgrade",
    "active_slice",
    "integration_baseline",
    "active_runs",
    "loop_owner_acceptances",
    "open_owner_gaps",
    "all_required_runs_accepted",
    "real_user_journey_acceptance",
    "centralized_security_audit",
    "security_remediation",
    "vulnerability_closure",
    "post_security_owner_acceptance",
    "delivery_method_qa",
    "delivery",
    "last_material_change",
    "next_action",
    "evidence_pointers",
    "blockers",
}

phase_status = strict_json("lc-coding/templates/PHASE-STATUS.json")
assert phase_status["status_schema_version"] == CURRENT
assert tuple(phase_status["phases"]) == (
    "INITIAL",
    "PRODUCT_FORMATION",
    "REAL_PRODUCT_INTEGRATION",
    "REAL_USER_JOURNEY_ACCEPTANCE",
    "DELIVERY_PREPARATION",
)

bi_root = ROOT / "lc-coding/bi"
package = strict_json("lc-coding/bi/package.json")
package_lock = strict_json("lc-coding/bi/package-lock.json")
assert package["version"] == CURRENT
assert package_lock["version"] == CURRENT
assert package_lock["packages"][""]["version"] == CURRENT

cargo_manifest = tomllib.loads(text("lc-coding/bi/src-tauri/Cargo.toml"))
cargo_lock = tomllib.loads(text("lc-coding/bi/src-tauri/Cargo.lock"))
assert cargo_manifest["package"]["version"] == CURRENT
lccoding_packages = [
    package for package in cargo_lock["package"] if package["name"] == "lccoding"
]
assert [package["version"] for package in lccoding_packages] == [CURRENT]
assert strict_json("lc-coding/bi/src-tauri/tauri.conf.json")["version"] == CURRENT

assert text("README.md").startswith("# LCCoding 4.0.0\n")
assert text("README.zh-CN.md").startswith("# LCCoding 4.0.0\n")
assert text("lc-coding/SKILL.md").startswith("---\nname: lc-coding\n")
assert "# LCCoding 4.0.0\n" in text("lc-coding/SKILL.md")
for relative in (
    "lc-coding/templates/RUN-HANDOFF.md",
    "lc-coding/templates/LOOP-OWNER-ACCEPTANCE.md",
):
    assert "- Status schema version: 4.0.0\n" in text(relative), relative

built_in_bi = text("lc-coding/references/built-in-bi.md")
assert built_in_bi.startswith("# Built-in Project BI — LCCoding 4.0.0\n")
for marker in (
    "The BI ships only as part of LCCoding 4.0.0",
    "LCCoding 4.0.0 installs one reusable current-user tool",
    "current `LCCoding 4.0.0 derived BI` schema",
):
    assert marker in built_in_bi, marker
for marker in (
    "Applicability Assessment",
    "PLATFORM_COMPLETION",
    "AGENT_COLLABORATIVE",
    "route-faithful",
):
    assert marker in text("README.md"), marker
for marker in (
    "Applicability Assessment",
    "PLATFORM_COMPLETION",
    "AGENT_COLLABORATIVE",
    "route-faithful",
):
    assert marker in text("README.zh-CN.md"), marker

compatibility = strict_json("lc-coding/bi/release/loop-contract-identities.json")
current_adapters = [
    version
    for version, adapter in compatibility["status_adapters"].items()
    if adapter["compatibility_status"] == "CURRENT"
]
assert current_adapters == [CURRENT]
assert compatibility["status_adapters"][CURRENT]["minimum_bi_version"] == CURRENT
assert compatibility["status_adapters"]["3.0.0"]["compatibility_status"] == "SUPPORTED_LEGACY"
assert {
    method: identity["version"]
    for method, identity in compatibility["execution_methods"].items()
} == {"slk": "2.6.0", "clk": "2.5.0", "glk": "3.1.0"}

assert (ROOT / "MIGRATION-3.0.0-TO-4.0.0.md").is_file()
assert (ROOT / "lc-coding/scripts/migrate_project_300_to_400.py").is_file()

changelog = text("CHANGELOG.md")
candidate_heading = "## Unreleased - 4.0.0 candidate"
assert changelog.startswith("# Changelog\n\n" + candidate_heading + "\n")
candidate_section = changelog[: changelog.index("\n## 3.0.0\n")]
for marker in (
    "Applicability Assessment",
    "Service Route Map",
    "route-faithful",
    "This candidate does not create a tag or GitHub Release, deploy the global Skill, or perform a persistent BI installation.",
):
    assert marker in candidate_section, marker
for released_claim in (
    "4.0.0 has been released",
    "formal 4.0.0 release is complete",
    "global 4.0.0 Skill was deployed",
    "LCCoding BI 4.0.0 was persistently installed",
):
    assert released_claim not in candidate_section

# Task 11 owns fresh 4.0 verification evidence. Task 10 must not relabel the
# accepted 3.0 report as current 4.0 evidence before that independent run.
validation_report = text("VALIDATION-REPORT.md")
assert validation_report.startswith("# LCCoding 3.0.0 Validation Report\n")
assert "# LCCoding 4.0.0 Validation Report" not in validation_report
assert "PASS, 76 tests" not in validation_report

package_surfaces = (
    "lc-coding/bi/scripts/package-release.ps1",
    "lc-coding/bi/tests/packaging/install-smoke.ps1",
    "lc-coding/bi/tests/packaging/nsis-contract.ps1",
    "lc-coding/bi/tests/packaging/run-standard-user-install-smoke.ps1",
    "lc-coding/bi/tests/packaging/standard-user-install-smoke.ps1",
    ".github/workflows/release-bi.yml",
    "PUBLISH-TO-GITHUB.md",
)
for relative in package_surfaces:
    assert INSTALLER in text(relative), relative
assert PROVENANCE_SCHEMA in text("lc-coding/bi/scripts/package-release.ps1")
assert PROVENANCE_SCHEMA in text("lc-coding/bi/tests/packaging/install-smoke.ps1")
assert 'VERSION -Raw).Trim() -ne "4.0.0"' in text(
    ".github/workflows/release-bi.yml"
)

workflow = text(".github/workflows/release-bi.yml").lower()
for forbidden in (
    "git push",
    "git tag",
    "gh release",
    "actions/create-release",
    "softprops/action-gh-release",
    "ncipollo/release-action",
):
    assert forbidden not in workflow

repository_validator = text("lc-coding/scripts/validate_repository.py")
assert "!='4.0.0'" in repository_validator
assert "!='3.0.0'" not in repository_validator

print("PASS: LCCoding 4.0 candidate carriers and package identity are consistent")
