from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
PRC = ROOT / "lc-coding/scripts/prc_check.py"


def run_prc(proposal):
    with tempfile.TemporaryDirectory() as td:
        proposal_path = Path(td) / "proposal.json"
        proposal_path.write_text(json.dumps(proposal), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(PRC), str(proposal_path)],
            capture_output=True,
            text=True,
        )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return json.loads(completed.stdout)


whole = {
    "problem": "Business request intake is fragmented",
    "target_users": ["customer"],
    "core_value": "complete an application",
    "scope": "customer-facing product",
    "constraints": ["auditable"],
    "success_criteria": ["observable accepted result"],
    "lccoding_fit": {
        "human_beneficiary": True,
        "complete_journey": True,
        "real_workflow": True,
        "actor_facing_surface": True,
        "integration_need": True,
        "real_acceptance_entry": True,
        "bounded_product_scope": False,
    },
}

whole_result = run_prc(whole)
assert whole_result["status"] == "PROPOSAL_READY"
assert whole_result["applicability_recommendation"] == "WHOLE_PRODUCT_FIT"
assert whole_result["service_strategy_discussion_required"] is True
assert whole_result["applicability_reasons"]

bounded = deepcopy(whole)
bounded["scope"] = "customer request-intake journey only"
bounded["lccoding_fit"]["bounded_product_scope"] = True
bounded_result = run_prc(bounded)
assert bounded_result["applicability_recommendation"] == "BOUNDED_PRODUCT_FIT"
assert bounded_result["service_strategy_discussion_required"] is True
assert any("bounded" in reason.lower() for reason in bounded_result["applicability_reasons"])

other = deepcopy(whole)
other["scope"] = "headless compiler algorithm library"
other["lccoding_fit"].update(
    {
        "human_beneficiary": False,
        "complete_journey": False,
        "real_workflow": False,
        "actor_facing_surface": False,
        "integration_need": False,
        "real_acceptance_entry": False,
    }
)
other_result = run_prc(other)
assert other_result["status"] == "PROPOSAL_READY"
assert other_result["applicability_recommendation"] == "OTHER_METHOD_RECOMMENDED"
assert other_result["service_strategy_discussion_required"] is False
assert any("full LCCoding lifecycle" in reason for reason in other_result["applicability_reasons"])
assert any("component-focused" in reason for reason in other_result["applicability_reasons"])

missing = deepcopy(whole)
missing["lccoding_fit"].pop("real_workflow")
missing["lccoding_fit"]["actor_facing_surface"] = False
missing_result = run_prc(missing)
assert missing_result["status"] == "PROPOSAL_INCOMPLETE"
assert missing_result["applicability_recommendation"] is None
assert missing_result["service_strategy_discussion_required"] is False
assert "lccoding_fit.real_workflow" in missing_result["missing_blockers"]
assert any(
    question["field"] == "lccoding_fit.real_workflow"
    and question["recommended_answer"]
    for question in missing_result["questions"]
)

invalid = deepcopy(whole)
invalid["lccoding_fit"]["actor_facing_surface"] = "yes"
invalid_result = run_prc(invalid)
assert invalid_result["status"] == "PROPOSAL_INCOMPLETE"
assert invalid_result["applicability_recommendation"] is None
assert "lccoding_fit.actor_facing_surface" in invalid_result["missing_blockers"]

missing_scope = deepcopy(whole)
missing_scope["lccoding_fit"].pop("bounded_product_scope")
missing_scope_result = run_prc(missing_scope)
assert missing_scope_result["status"] == "PROPOSAL_INCOMPLETE"
assert missing_scope_result["applicability_recommendation"] is None
assert "lccoding_fit.bounded_product_scope" in missing_scope_result["missing_blockers"]

conflicted = deepcopy(whole)
conflicted["conflicts"] = ["Scope names both the whole product and a library-only object"]
conflicted_result = run_prc(conflicted)
assert conflicted_result["status"] == "PROPOSAL_INCOMPLETE"
assert conflicted_result["applicability_recommendation"] is None
assert any(
    question["field"] == "conflicts[0]" and question["recommended_answer"]
    for question in conflicted_result["questions"]
)

template = (ROOT / "lc-coding/templates/PROPOSAL-READINESS.md").read_text(
    encoding="utf-8"
)
for marker in (
    "Human beneficiary or authorized representative",
    "Complete product or service journey",
    "Real business Workflow",
    "Actor-facing product surface",
    "Surface / Workflow / Simulation / Backend/Core integration need",
    "Real acceptance entry",
    "Applicability recommendation",
    "Selected primary strategy",
    "Required coexisting strategy",
    "Service Center decision",
    "Strategy rationale",
    "Unresolved Calabash topics",
):
    assert marker in template, marker

reference_path = ROOT / "lc-coding/references/service-topology.md"
reference = reference_path.read_text(encoding="utf-8")
for marker in (
    "PLATFORM_COMPLETION",
    "AGENT_COLLABORATIVE",
    "MIXED",
    "Service Center",
    "per delivered journey",
    "Personal Agent",
    "Product Agent",
    "Operations Agent",
    "one shared Workflow and Backend/Core",
):
    assert marker in reference, marker
assert (
    "Load this reference only for Initial strategy discussion, route-aware Product "
    "Formation, or route-aware Real User Journey Acceptance."
) in reference

repository_validator = (ROOT / "lc-coding/scripts/validate_repository.py").read_text(
    encoding="utf-8"
)
assert "lc-coding/references/service-topology.md" in repository_validator

proposal_guidance = (ROOT / "lc-coding/references/proposal-readiness.md").read_text(
    encoding="utf-8"
)
assert "`status` reports proposal evidence completeness only" in proposal_guidance
assert "`applicability_recommendation` controls LCCoding admission" in proposal_guidance
assert "`OTHER_METHOD_RECOMMENDED` is terminal" in proposal_guidance

print("PASS: Initial applicability assessment and service-strategy discussion")
