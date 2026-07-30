from pathlib import Path
import copy
import importlib.util
import json

root = Path(__file__).resolve().parents[2]
module_path = root / "lc-coding/scripts/validate_project.py"
spec = importlib.util.spec_from_file_location("validate_project", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

status = json.loads((root / "lc-coding/templates/STATUS.json").read_text(encoding="utf-8"))
phase_status = json.loads(
    (root / "lc-coding/templates/PHASE-STATUS.json").read_text(encoding="utf-8")
)
health = json.loads(
    (root / "lc-coding/templates/PROJECT-HEALTH.json").read_text(encoding="utf-8")
)

assert status.get("record_role") == "AUTHORITATIVE_PROJECT_STATUS"
assert phase_status.get("record_role") == "DERIVED_VIEW"
assert phase_status.get("derived_from") == "status.json"
assert health.get("record_role") == "ASSESSMENT_EVIDENCE"
assert hasattr(module, "validate_status_authority")
assert module.validate_status_authority(status, phase_status, health) == []

duplicate_authority = copy.deepcopy(phase_status)
duplicate_authority["record_role"] = "AUTHORITATIVE_PROJECT_STATUS"
assert any(
    "single authoritative project status" in error
    for error in module.validate_status_authority(status, duplicate_authority, health)
)

runtime_polluted = copy.deepcopy(status)
runtime_polluted["session_id"] = "runtime-state-does-not-belong-here"
assert any(
    "runtime field" in error
    for error in module.validate_status_authority(runtime_polluted, phase_status, health)
)

drifted_view = copy.deepcopy(phase_status)
drifted_view["current_phase"] = "ENGINEERING_RUNS"
assert any(
    "derived phase status disagrees" in error
    for error in module.validate_status_authority(status, drifted_view, health)
)

start = {
    "initialization_mode": "EXISTING",
    "source_head": "abc123",
    "source_version": "7.4.2",
    "source_candidate": {
        "repository": "owner/existing",
        "version": "7.4.2",
        "commit": "abc123",
    },
    "continuity_decision": "CONTINUE",
    "completion_claim_status": "CLAIMED_UNATTESTED",
    "attestation_status": "PENDING",
    "historical_materials_status": "PENDING",
    "evidence_inventory_status": "PENDING",
    "product_mainline_status": "PENDING",
    "takeover_readiness": "BLOCKED",
}
blocked_status = copy.deepcopy(status)
blocked_status["initialization_mode"] = "EXISTING"
blocked_status["continuity_decision"] = "CONTINUE"
blocked_status["takeover_readiness"] = "BLOCKED"
blocked_status["canonical_candidate"] = start["source_candidate"]
blocked_health = copy.deepcopy(health)
blocked_health["initialization_mode"] = "EXISTING"
blocked_health["continuity_decision"] = "CONTINUE"
blocked_health["takeover_readiness"] = "BLOCKED"
assert hasattr(module, "validate_takeover_readiness")
assert module.validate_takeover_readiness(start, blocked_status, blocked_health) == []

premature_ready = copy.deepcopy(start)
premature_ready["takeover_readiness"] = "READY"
ready_status = copy.deepcopy(blocked_status)
ready_status["takeover_readiness"] = "READY"
ready_health = copy.deepcopy(blocked_health)
ready_health["takeover_readiness"] = "READY"
assert any(
    "READY requires" in error
    for error in module.validate_takeover_readiness(
        premature_ready, ready_status, ready_health
    )
)

attested_ready = copy.deepcopy(premature_ready)
attested_ready.update(
    {
        "attestation_status": "EVIDENCED",
        "historical_materials_status": "INVENTORIED",
        "evidence_inventory_status": "INVENTORIED",
        "product_mainline_status": "RECONSTRUCTED",
    }
)
attested_status = copy.deepcopy(ready_status)
attested_status["existing_project_attestation"] = "EVIDENCED"
attested_health = copy.deepcopy(ready_health)
attested_health["existing_project_classification"] = "PARTIAL"
assert any(
    "READY requires evidence inventory" in error
    for error in module.validate_takeover_readiness(
        attested_ready, attested_status, attested_health
    )
)
attested_ready["historical_materials"] = []
attested_ready["evidence_inventory"] = ["D3-existing-candidate"]
attested_ready["product_mainline_evidence"] = ["WF-current", "UI-current"]
assert module.validate_takeover_readiness(
    attested_ready, attested_status, attested_health
) == []

not_continuing = copy.deepcopy(start)
not_continuing["continuity_decision"] = "TERMINATE"
not_continuing["takeover_readiness"] = "NOT_CONTINUING"
stopped_status = copy.deepcopy(blocked_status)
stopped_status["continuity_decision"] = "TERMINATE"
stopped_status["takeover_readiness"] = "NOT_CONTINUING"
stopped_health = copy.deepcopy(blocked_health)
stopped_health["continuity_decision"] = "TERMINATE"
stopped_health["takeover_readiness"] = "NOT_CONTINUING"
assert module.validate_takeover_readiness(
    not_continuing, stopped_status, stopped_health
) == []

phases = json.loads(
    (root / "lc-coding/contracts/phases.json").read_text(encoding="utf-8")
)
assert "TAKEOVER" not in {phase["id"] for phase in phases["phases"]}
assert phases["phases"][0]["id"] == "INITIAL"

print("PASS: takeover readiness stays in initialization with one canonical status")
