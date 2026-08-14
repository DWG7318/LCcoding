from pathlib import Path
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile

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
assert status.get("status_schema_version") == "2.8.0"
assert phase_status.get("status_schema_version") == "2.8.0"
assert "CALABASH_UPGRADE_READY" in status.get("phase_gates", {})
assert "PRODUCT_BASELINE_READY" not in status.get("phase_gates", {})
assert status.get("product_baseline") == "PENDING"
assert status["vulnerability_closure"]["state"] == "PENDING"
assert status["post_security_owner_acceptance"]["state"] == "PENDING"
assert set(status["vulnerability_closure"]) == module.VULNERABILITY_STATUS_FIELDS
assert set(status["post_security_owner_acceptance"]) == module.POST_SECURITY_STATUS_FIELDS
assert "product_baseline" not in status.get("phase_gates", {})
formation_view = phase_status["phases"]["PRODUCT_FORMATION"]
assert "exit_gate" not in formation_view
assert formation_view.get("exit_evidence") == "PENDING"
assert hasattr(module, "validate_status_authority")
assert module.validate_status_authority(status, phase_status, health) == []


def legacy_phase_view(current_view):
    view = copy.deepcopy(current_view)
    records = view["phases"]
    view["status_schema_version"] = "2.7.0"
    view["phases"] = {
        "INITIAL": records["INITIAL"],
        "PRODUCT_FORMATION": records["PRODUCT_FORMATION"],
        "ENGINEERING_RUNS": records["REAL_PRODUCT_INTEGRATION"],
        "DELIVERY_PREPARATION": records["DELIVERY_PREPARATION"],
    }
    if view["current_phase"] == "REAL_PRODUCT_INTEGRATION":
        view["current_phase"] = "ENGINEERING_RUNS"
    return view


# Exact 2.7 schema remains readable with its legacy phase identity.
legacy_status_270 = copy.deepcopy(status)
legacy_status_270["status_schema_version"] = "2.7.0"
legacy_view_270 = legacy_phase_view(phase_status)
assert module.validate_status_authority(legacy_status_270, legacy_view_270, health) == []

# Schema and identity cannot be mixed, inferred, or crossed.
mixed_schema_view = legacy_phase_view(phase_status)
assert any(
    "status schema disagrees" in error
    for error in module.validate_status_authority(status, mixed_schema_view, health)
)
cross_identity_view = copy.deepcopy(mixed_schema_view)
cross_identity_view["status_schema_version"] = "2.8.0"
assert any(
    "phase identity does not match schema" in error
    for error in module.validate_status_authority(status, cross_identity_view, health)
)
inferred_view = copy.deepcopy(phase_status)
del inferred_view["status_schema_version"]
assert any(
    "status_schema_version is required" in error
    for error in module.validate_status_authority(status, inferred_view, health)
)
inferred_status = copy.deepcopy(status)
del inferred_status["status_schema_version"]
assert any(
    "authoritative status_schema_version is required" in error
    for error in module.validate_status_authority(inferred_status, phase_status, health)
)

# Explicit legacy/non-current scalar security status remains readable, but a
# current record cannot mix scalar and structured truth or add a second ledger.
legacy_security = copy.deepcopy(status)
legacy_security["vulnerability_closure"] = "PENDING"
legacy_security["post_security_owner_acceptance"] = "PENDING"
assert module.validate_status_authority(legacy_security, phase_status, health) == []
mixed_security = copy.deepcopy(status)
mixed_security["vulnerability_closure"] = "PENDING"
assert any(
    "mix scalar and structured" in error
    for error in module.validate_status_authority(mixed_security, phase_status, health)
)
second_security_authority = copy.deepcopy(status)
second_security_authority["security_invalidation_ledger"] = []
assert any(
    "second security invalidation authority" in error
    for error in module.validate_status_authority(
        second_security_authority, phase_status, health
    )
)


def product_formation_pending():
    current_status = copy.deepcopy(status)
    current_view = copy.deepcopy(phase_status)
    current_status["current_phase"] = "PRODUCT_FORMATION"
    current_status["phase_gates"]["INITIAL_READY"] = "PASS"
    current_status["phase_gates"]["CALABASH_UPGRADE_READY"] = "PASS"
    current_status["product_baseline"] = "PENDING"
    current_view["current_phase"] = "PRODUCT_FORMATION"
    current_view["phases"]["INITIAL"]["status"] = "COMPLETE"
    current_view["phases"]["INITIAL"]["exit_gate"] = "PASS"
    current_view["phases"]["PRODUCT_FORMATION"]["status"] = "ACTIVE"
    current_view["phases"]["PRODUCT_FORMATION"]["exit_evidence"] = "PENDING"
    return current_status, current_view


# Upgrade readiness is only internal compatibility evidence. It does not finish
# Product Formation while the authoritative Product Baseline remains pending.
formation_status, formation_phase_status = product_formation_pending()
assert module.validate_status_authority(
    formation_status, formation_phase_status, health
) == []

# Boundary evidence is a raw projection of the authoritative lifecycle state.
# ACTIVE is valid evidence while Product Formation remains in progress.
active_baseline_status = copy.deepcopy(formation_status)
active_baseline_view = copy.deepcopy(formation_phase_status)
active_baseline_status["product_baseline"] = "ACTIVE"
active_baseline_view["phases"]["PRODUCT_FORMATION"]["exit_evidence"] = "ACTIVE"
assert module.validate_status_authority(
    active_baseline_status, active_baseline_view, health
) == []

# READY is a completed lifecycle value for the Initial boundary; the derived
# phase record status remains the separate conservative COMPLETE value.
ready_initial_status = copy.deepcopy(formation_status)
ready_initial_view = copy.deepcopy(formation_phase_status)
ready_initial_status["phase_gates"]["INITIAL_READY"] = "READY"
ready_initial_view["phases"]["INITIAL"]["exit_gate"] = "READY"
assert module.validate_status_authority(
    ready_initial_status, ready_initial_view, health
) == []

premature_engineering_status = copy.deepcopy(formation_status)
premature_engineering_view = copy.deepcopy(formation_phase_status)
premature_engineering_status["current_phase"] = "REAL_PRODUCT_INTEGRATION"
premature_engineering_view["current_phase"] = "REAL_PRODUCT_INTEGRATION"
assert any(
    "REAL_PRODUCT_INTEGRATION requires accepted Product Baseline" in error
    for error in module.validate_status_authority(
        premature_engineering_status, premature_engineering_view, health
    )
)

# Authoritative acceptance may not be hidden by a stale derived pending view.
accepted_with_pending_view = copy.deepcopy(formation_status)
accepted_with_pending_view["product_baseline"] = "ACCEPTED"
assert any(
    "derived Product Formation exit evidence" in error
    for error in module.validate_status_authority(
        accepted_with_pending_view, formation_phase_status, health
    )
)

# Accepted/current Product Baseline plus matching derived completion admits
# Real Product Integration when Initial is also complete.
engineering_status = copy.deepcopy(formation_status)
engineering_view = copy.deepcopy(formation_phase_status)
engineering_status["current_phase"] = "REAL_PRODUCT_INTEGRATION"
engineering_status["product_baseline"] = "ACCEPTED"
engineering_view["current_phase"] = "REAL_PRODUCT_INTEGRATION"
engineering_view["phases"]["PRODUCT_FORMATION"]["status"] = "COMPLETE"
engineering_view["phases"]["PRODUCT_FORMATION"]["exit_evidence"] = "ACCEPTED"
engineering_view["phases"]["REAL_PRODUCT_INTEGRATION"]["status"] = "ACTIVE"
assert module.validate_status_authority(engineering_status, engineering_view, health) == []

legacy_engineering_status = copy.deepcopy(engineering_status)
legacy_engineering_status["status_schema_version"] = "2.7.0"
legacy_engineering_status["current_phase"] = "ENGINEERING_RUNS"
legacy_engineering_view = legacy_phase_view(engineering_view)
assert module.validate_status_authority(
    legacy_engineering_status, legacy_engineering_view, health
) == []

# The aggregate boundary keeps its exact authoritative raw value and
# normalizes to completed when Delivery Preparation begins.
delivery_status = copy.deepcopy(engineering_status)
delivery_view = copy.deepcopy(engineering_view)
delivery_status["current_phase"] = "DELIVERY_PREPARATION"
delivery_status["phase_gates"][
    "ALL_REQUIRED_RUNS_ACCEPTED"
] = "ALL_REQUIRED_RUNS_ACCEPTED"
delivery_view["current_phase"] = "DELIVERY_PREPARATION"
delivery_view["phases"]["REAL_PRODUCT_INTEGRATION"]["status"] = "COMPLETE"
delivery_view["phases"]["REAL_PRODUCT_INTEGRATION"][
    "aggregate_exit_gate"
] = "ALL_REQUIRED_RUNS_ACCEPTED"
delivery_view["phases"]["DELIVERY_PREPARATION"]["status"] = "ACTIVE"
assert module.validate_status_authority(delivery_status, delivery_view, health) == []

engineering_without_initial = copy.deepcopy(engineering_view)
engineering_without_initial["phases"]["INITIAL"]["status"] = "PENDING"
assert any(
    "prior phase status not complete: INITIAL" in error
    for error in module.validate_status_authority(
        engineering_status, engineering_without_initial, health
    )
)

arbitrary_baseline_status = copy.deepcopy(engineering_status)
arbitrary_baseline_view = copy.deepcopy(engineering_view)
arbitrary_baseline_status["product_baseline"] = "FINISHEDISH"
arbitrary_baseline_view["phases"]["PRODUCT_FORMATION"]["exit_evidence"] = "FINISHEDISH"
assert any(
    "invalid Product Baseline evidence state" in error
    for error in module.validate_status_authority(
        arbitrary_baseline_status, arbitrary_baseline_view, health
    )
)

unknown_baseline_status = copy.deepcopy(engineering_status)
unknown_baseline_view = copy.deepcopy(engineering_view)
unknown_baseline_status["product_baseline"] = "UNKNOWN"
unknown_baseline_view["phases"]["PRODUCT_FORMATION"]["exit_evidence"] = "UNKNOWN"
assert any(
    "invalid Product Baseline evidence state" in error
    for error in module.validate_status_authority(
        unknown_baseline_status, unknown_baseline_view, health
    )
)

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
drifted_view["current_phase"] = "REAL_PRODUCT_INTEGRATION"
assert any(
    "derived phase status disagrees" in error
    for error in module.validate_status_authority(status, drifted_view, health)
)

invented_gate = copy.deepcopy(status)
invented_gate["phase_gates"]["PRODUCT_BASELINE_READY"] = "PASS"
assert any(
    "PRODUCT_BASELINE_READY" in error
    for error in module.validate_status_authority(invented_gate, phase_status, health)
)


def run_phase_status_validator(view):
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "PHASE-STATUS.json"
        path.write_text(json.dumps(view), encoding="utf-8")
        return subprocess.run(
            [
                sys.executable,
                str(root / "lc-coding/scripts/validate_phase_status.py"),
                str(path),
            ],
            capture_output=True,
            text=True,
        )


valid_phase_result = run_phase_status_validator(engineering_view)
assert valid_phase_result.returncode == 0, valid_phase_result.stdout + valid_phase_result.stderr
invalid_phase_view = copy.deepcopy(engineering_view)
invalid_phase_view["phases"]["PRODUCT_FORMATION"]["exit_evidence"] = "FINISHEDISH"
invalid_phase_result = run_phase_status_validator(invalid_phase_view)
assert invalid_phase_result.returncode != 0
assert "invalid exit evidence state" in invalid_phase_result.stdout

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


def write_project_fixture(project, status_record, phase_record):
    lc = project / ".lccoding"
    lc.mkdir(parents=True)
    (project / "VERSION").write_text("0.0.1\n", encoding="utf-8")
    (lc / "PROJECT-START.json").write_text(
        json.dumps({"initialization_mode": "NEW", "repository": "owner/project"}),
        encoding="utf-8",
    )
    for name in ("OWNER-POLICY.md", "PROJECT-PROFILE.md", "AGENT-RULE.md"):
        (lc / name).write_text("fixture\n", encoding="utf-8")
    fingerprint = {
        "complexity": {
            "product_uncertainty": "LOW",
            "system_coupling": "LOW",
            "real_risk": "LOW",
            "irreversibility": "LOW",
            "novelty": "LOW",
        },
        "depth": {"rationale": "", "analysis": [], "materials": [], "evidence": []},
    }
    (lc / "PROJECT-FINGERPRINT.json").write_text(
        json.dumps(fingerprint), encoding="utf-8"
    )
    fixture_health = copy.deepcopy(health)
    fixture_health["initialization_mode"] = "NEW"
    (lc / "PROJECT-HEALTH.json").write_text(
        json.dumps(fixture_health), encoding="utf-8"
    )
    (lc / "CANONICAL-MANIFEST.json").write_text("{}\n", encoding="utf-8")
    (lc / "INTERPRETATION-LOCK.json").write_text(
        json.dumps({"status": "VALID"}), encoding="utf-8"
    )
    for name in ("WORKFLOW-MAP.md", "UI-MAP.md", "SIMULATION-WORLD.md"):
        (lc / name).write_text(
            (root / "lc-coding/templates" / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    (lc / "status.json").write_text(json.dumps(status_record), encoding="utf-8")
    (lc / "PHASE-STATUS.json").write_text(json.dumps(phase_record), encoding="utf-8")
    return lc


def run_project_validator(project):
    return subprocess.run(
        [
            sys.executable,
            str(root / "lc-coding/scripts/validate_project.py"),
            str(project),
        ],
        capture_output=True,
        text=True,
    )


with tempfile.TemporaryDirectory() as temporary:
    project = Path(temporary) / "missing-handoff"
    write_project_fixture(project, engineering_status, engineering_view)
    result = run_project_validator(project)
    assert result.returncode != 0
    assert "accepted Product Baseline requires PRODUCT-BASELINE-HANDOFF.md" in result.stdout

with tempfile.TemporaryDirectory() as temporary:
    project = Path(temporary) / "invalid-handoff"
    lc = write_project_fixture(project, engineering_status, engineering_view)
    (lc / "PRODUCT-BASELINE-HANDOFF.md").write_text(
        "# Product Baseline Handoff\n\n- Handoff status: COMPLETE\n",
        encoding="utf-8",
    )
    result = run_project_validator(project)
    assert result.returncode != 0
    assert (
        "accepted Product Baseline requires a mechanically valid and COMPLETE Product Baseline Handoff"
        in result.stdout
    )

# The normal project validator must apply the shared phase-view ordering
# validator, even when all raw authoritative boundary mappings agree.
with tempfile.TemporaryDirectory() as temporary:
    project = Path(temporary) / "malformed-future-phase"
    malformed_future_view = copy.deepcopy(formation_phase_status)
    malformed_future_view["phases"]["REAL_PRODUCT_INTEGRATION"]["status"] = "ACTIVE"
    write_project_fixture(project, formation_status, malformed_future_view)
    result = run_project_validator(project)
    assert result.returncode != 0
    assert "future phase status must be PENDING: REAL_PRODUCT_INTEGRATION" in result.stdout

phases = json.loads(
    (root / "lc-coding/contracts/phases.json").read_text(encoding="utf-8")
)
assert "TAKEOVER" not in {phase["id"] for phase in phases["phases"]}
assert phases["phases"][0]["id"] == "INITIAL"

print("PASS: takeover readiness stays in initialization with one canonical status")
