from datetime import datetime, timezone
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile


root = Path(__file__).resolve().parents[2]
contract_path = root / "lc-coding/contracts/loop-control-contract.json"
template_path = root / "lc-coding/templates/LOOP-CONTROL-BINDING.json"
project_validator_path = root / "lc-coding/scripts/validate_project.py"
validator_spec = importlib.util.spec_from_file_location(
    "validate_loop_control_transition_270", project_validator_path
)
project_validator = importlib.util.module_from_spec(validator_spec)
validator_spec.loader.exec_module(project_validator)

AS_OF = datetime(2026, 8, 13, 12, 0, 0, tzinfo=timezone.utc)


def exact_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def valid_binding(contract_file: Path, *, method="SLK", state="RETAINED"):
    prefix = method + "_"
    binding = {
        "artifact_type": "LOOP_CONTROL_BINDING",
        "binding_version": "1.0.0",
        "contract": {
            "contract_id": "LCCODING_LOOP_CONTROL",
            "contract_version": "1.0.0",
            "contract_sha256": exact_hash(contract_file),
        },
        "runtime_attestation": {
            "runtime_owner": "LCagent_or_trusted_runtime",
            "runtime_adapter_id": "TRUSTED-RUNTIME-1",
            "attestation_root": "ATTESTATION-ROOT-1",
            "evidence_digest": "sha256:" + "a" * 64,
            "observed_at": "2026-08-13T11:45:00Z",
            "validated_at": "2026-08-13T11:50:00Z",
            "expires_at": "2026-08-13T12:20:00Z",
            "currentness": "CURRENT",
            "result": "PASS",
        },
        "method_mapping": {
            "method": method,
            "topology_owned_progress_fields": [prefix + "PROGRESS-1"],
            "topology_owned_capacity_fields": [prefix + "CAPACITY-1"],
            "topology_owned_model_fields": [prefix + "MODEL-1"],
            "topology_owned_evidence_fields": [prefix + "EVIDENCE-1"],
        },
        "model_binding": {
            "role_kind": "TECHNICAL",
            "actual_model": "gpt-5.6-terra",
            "reference_model": "gpt-5.6-terra",
            "capability_class": "NORMAL_TECHNICAL",
            "reasoning_effort": "xhigh",
            "selection_reason": "NORMAL_TECHNICAL",
            "equivalence": {
                "status": "EXACT_REFERENCE",
                "evidence_id": "NOT_APPLICABLE",
                "evidence_digest": "NOT_APPLICABLE",
            },
            "owner_ultra_authorization": "NOT_APPLICABLE",
        },
        "local_control": {"state": state},
    }
    if state == "RETIRED":
        binding["local_control"]["retirement_evidence"] = {
            "runtime_conformance": {
                "positive": {
                    "evidence_id": "CONFORMANCE-POSITIVE-1",
                    "evidence_digest": "sha256:" + "b" * 64,
                    "result": "PASS",
                },
                "negative": {
                    "evidence_id": "CONFORMANCE-NEGATIVE-1",
                    "evidence_digest": "sha256:" + "c" * 64,
                    "result": "PASS",
                },
            },
            "historical_receipts": {
                "status": "READABLE",
                "evidence_id": "HISTORICAL-RECEIPTS-1",
                "evidence_digest": "sha256:" + "d" * 64,
            },
            "owner_approved_release": {
                "release_id": method + "-RELEASE-1",
                "approval_evidence_id": "OWNER-RETIREMENT-1",
                "approval_evidence_digest": "sha256:" + "e" * 64,
                "result": "LOCAL_CONTROL_RETIRED",
            },
        }
    return binding


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def validate(binding, *, contract=None, raw=None, as_of=AS_OF):
    assert hasattr(project_validator, "validate_loop_control_binding"), (
        "validate_project must expose the closed Loop Control binding validator"
    )
    with tempfile.TemporaryDirectory(prefix="lccoding-loop-control-") as temporary:
        temporary_root = Path(temporary)
        lc = temporary_root / ".lccoding"
        lc.mkdir()
        local_contract = temporary_root / "loop-control-contract.json"
        if contract is None:
            local_contract.write_bytes(contract_path.read_bytes())
        else:
            write_json(local_contract, contract)
        binding_path = lc / "LOOP-CONTROL-BINDING.json"
        if raw is None:
            write_json(binding_path, binding)
        else:
            binding_path.write_text(raw, encoding="utf-8")
        before = binding_path.read_bytes()
        errors = project_validator.validate_loop_control_binding(
            lc, contract_path=local_contract, as_of=as_of
        )
        assert binding_path.read_bytes() == before
        return errors


contract = json.loads(contract_path.read_text(encoding="utf-8"))
template = json.loads(template_path.read_text(encoding="utf-8"))
reference = (root / "lc-coding/references/loop-control-contract.md").read_text(
    encoding="utf-8"
)
assert contract["worker_wake"]["levels"][2] == "CHECKER_WAKE_HEARTBEAT"
assert contract["worker_wake"]["heartbeat_kind"] == "CHECKER_WAKE_HEARTBEAT"
assert contract["run_patrol"]["heartbeat_kind"] == "RUN_PATROL_HEARTBEAT"
assert contract["heartbeat_separation"] == {
    "shared_id": "FORBIDDEN",
    "shared_lifecycle": "FORBIDDEN",
    "shared_counting": "FORBIDDEN",
    "shared_evidence_claim": "FORBIDDEN",
}
assert template["local_control"]["state"] == "ACTIVE|RETAINED|RETIRED"
assert set(template["local_control"]["retirement_evidence"]) == {
    "runtime_conformance",
    "historical_receipts",
    "owner_approved_release",
}
assert set(template["runtime_attestation"]) == {
    "runtime_owner",
    "runtime_adapter_id",
    "attestation_root",
    "evidence_digest",
    "observed_at",
    "validated_at",
    "expires_at",
    "currentness",
    "result",
}
assert set(template["method_mapping"]) == {
    "method",
    "topology_owned_progress_fields",
    "topology_owned_capacity_fields",
    "topology_owned_model_fields",
    "topology_owned_evidence_fields",
}
assert "absent binding leaves the method's verified local control `ACTIVE` or `RETAINED`" in reference
assert "absent, stale, mismatched, or failed evidence blocks new formal work" not in reference

with tempfile.TemporaryDirectory(prefix="lccoding-loop-control-contract-") as temporary:
    local_contract = Path(temporary) / "loop-control-contract.json"
    local_contract.write_bytes(contract_path.read_bytes())
    legacy_ultra_bypass = valid_binding(local_contract)
    legacy_ultra_bypass["model_binding"].pop("owner_ultra_authorization")
    legacy_ultra_bypass["model_binding"].update(
        role_kind="HIGH_DIFFICULTY_CORRECTION",
        actual_model="gpt-5.6-sol",
        reference_model="gpt-5.6-sol",
        capability_class="DIFFICULT_CORRECTION",
        reasoning_effort="ultra",
        selection_reason="HIGH_DIFFICULTY_CORRECTION",
        owner_ultra_authorization_id="ARBITRARY-NON-OWNER-TEXT",
    )
    assert validate(legacy_ultra_bypass), "arbitrary ultra authorization text was accepted"

    retained = valid_binding(local_contract)
    retained_errors = validate(retained)
    assert retained_errors == [], retained_errors
    duplicate_errors = validate(
        {},
        raw="{\"artifact_type\":\"LOOP_CONTROL_BINDING\",\"artifact_type\":\"LOOP_CONTROL_BINDING\"}",
    )
    assert "LOOP_CONTROL_BINDING_INVALID_JSON" in duplicate_errors
    malformed_errors = validate({}, raw="{")
    assert "LOOP_CONTROL_BINDING_INVALID_JSON" in malformed_errors

    no_binding_lc = Path(temporary) / "no-binding" / ".lccoding"
    no_binding_lc.mkdir(parents=True)
    assert project_validator.validate_loop_control_binding(
        no_binding_lc, contract_path=local_contract, as_of=AS_OF
    ) == []

    invalid = []

    def reject(label, mutate, *, source=retained, contract_value=None, raw=None):
        candidate = copy.deepcopy(source)
        mutate(candidate)
        errors = validate(candidate, contract=contract_value, raw=raw)
        if not errors:
            invalid.append(label)

    reject("contract ID", lambda value: value["contract"].update(contract_id="OTHER"))
    reject("contract hash", lambda value: value["contract"].update(contract_sha256="sha256:" + "f" * 64))
    reject("method", lambda value: value["method_mapping"].update(method="CALABASH"))
    reject("missing attestation", lambda value: value.pop("runtime_attestation"))
    reject("empty progress mapping", lambda value: value["method_mapping"].update(topology_owned_progress_fields=[]))
    reject("empty capacity mapping", lambda value: value["method_mapping"].update(topology_owned_capacity_fields=[]))
    reject("shared heartbeat mapping", lambda value: value["method_mapping"].update(topology_owned_progress_fields=["RUN_PATROL_HEARTBEAT"]))
    reject("checker heartbeat mapping", lambda value: value["method_mapping"].update(topology_owned_evidence_fields=["CHECKER_WAKE_HEARTBEAT"]))
    def patrol_engineering_progress(value):
        value["method_mapping"]["topology_owned_progress_fields"] = ["SLK_ENGINEERING_PROGRESS"]
        value["model_binding"].update(
            role_kind="PATROL",
            actual_model="gpt-5.6-luna",
            reference_model="gpt-5.6-luna",
            capability_class="FASTEST_NONTECHNICAL",
            selection_reason="PATROL_NONTECHNICAL",
        )

    reject("Patrol engineering progress", patrol_engineering_progress)
    reject("stale attestation", lambda value: value["runtime_attestation"].update(validated_at="2026-08-13T10:00:00Z"))
    reject("future attestation", lambda value: value["runtime_attestation"].update(observed_at="2026-08-13T12:01:00Z"))
    reject("expired attestation", lambda value: value["runtime_attestation"].update(expires_at="2026-08-13T11:59:00Z"))
    reject("failed attestation", lambda value: value["runtime_attestation"].update(result="FAIL"))
    reject("bad timezone", lambda value: value["runtime_attestation"].update(validated_at="2026-08-13T11:50:00+00:00"))
    reject("unknown field", lambda value: value.update(unexpected="NO"))
    reject("placeholder", lambda value: value["runtime_attestation"].update(runtime_adapter_id="<adapter>"))
    reject("low model", lambda value: value["model_binding"].update(actual_model="gpt-5.5", reference_model="gpt-5.5"))
    def set_ultra(value, authorization):
        value["model_binding"].update(
            role_kind="HIGH_DIFFICULTY_CORRECTION",
            actual_model="gpt-5.6-sol",
            reference_model="gpt-5.6-sol",
            capability_class="DIFFICULT_CORRECTION",
            reasoning_effort="ultra",
            selection_reason="HIGH_DIFFICULTY_CORRECTION",
            owner_ultra_authorization=authorization,
        )

    bypass = copy.deepcopy(retained)
    set_ultra(bypass, "ARBITRARY-NON-OWNER-TEXT")
    bypass_errors = validate(bypass)
    assert bypass_errors, "arbitrary ultra authorization text was accepted"

    ultra_authorization = {
        "item_id": "RUN-ITEM-1",
        "owner_authorization_id": "OWNER-ULTRA-1",
        "authorization_evidence_digest": "sha256:" + "f" * 64,
        "result": "OWNER_APPROVED_ULTRA",
    }
    approved_ultra = copy.deepcopy(retained)
    set_ultra(approved_ultra, ultra_authorization)
    approved_ultra_errors = validate(approved_ultra)
    assert approved_ultra_errors == [], approved_ultra_errors

    reject("unapproved ultra", lambda value: set_ultra(value, "NOT_APPLICABLE"))
    reject(
        "ultra missing item",
        lambda value: set_ultra(value, {key: item for key, item in ultra_authorization.items() if key != "item_id"}),
    )
    reject(
        "ultra missing digest",
        lambda value: set_ultra(value, {key: item for key, item in ultra_authorization.items() if key != "authorization_evidence_digest"}),
    )
    reject(
        "ultra missing Owner authorization",
        lambda value: set_ultra(value, {key: item for key, item in ultra_authorization.items() if key != "owner_authorization_id"}),
    )
    reject(
        "ultra wrong result",
        lambda value: set_ultra(value, {**ultra_authorization, "result": "PASS"}),
    )
    reject(
        "ultra template placeholder",
        lambda value: set_ultra(value, {**ultra_authorization, "item_id": "<item>"}),
    )
    reject(
        "xhigh authorization",
        lambda value: value["model_binding"].update(owner_ultra_authorization=ultra_authorization),
    )

    retired = valid_binding(local_contract, state="RETIRED")
    assert validate(retired) == []
    reject(
        "retirement contract binding",
        lambda value: value["contract"].update(contract_sha256="sha256:" + "f" * 64),
        source=retired,
    )
    reject(
        "retirement method mapping",
        lambda value: value["method_mapping"].update(topology_owned_evidence_fields=[]),
        source=retired,
    )
    reject(
        "retirement current attestation",
        lambda value: value["runtime_attestation"].update(result="FAIL"),
        source=retired,
    )
    for key in ("runtime_conformance", "historical_receipts", "owner_approved_release"):
        reject(
            "retirement " + key,
            lambda value, key=key: value["local_control"]["retirement_evidence"].pop(key),
            source=retired,
        )
    reject(
        "retirement negative evidence",
        lambda value: value["local_control"]["retirement_evidence"]["runtime_conformance"]["negative"].update(result="FAIL"),
        source=retired,
    )
    reject(
        "retirement release approval",
        lambda value: value["local_control"]["retirement_evidence"]["owner_approved_release"].update(result="PENDING"),
        source=retired,
    )
    reject(
        "retirement wrong method release",
        lambda value: value["local_control"]["retirement_evidence"]["owner_approved_release"].update(release_id="CLK-RELEASE-1"),
        source=retired,
    )

    bad_contract = copy.deepcopy(contract)
    bad_contract["worker_wake"]["levels"][2] = "TEMPORARY_HEARTBEAT"
    reject("temporary heartbeat contract", lambda value: None, contract_value=bad_contract)
    bad_progress_contract = copy.deepcopy(contract)
    bad_progress_contract["progress"]["patrol"] = "ENGINEERING_PROGRESS"
    reject("Patrol progress contract", lambda value: None, contract_value=bad_progress_contract)
    bad_capacity_contract = copy.deepcopy(contract)
    bad_capacity_contract["capacity"]["outcomes"] = ["PASS"]
    reject("capacity contract", lambda value: None, contract_value=bad_capacity_contract)
    mixed_heartbeat_contract = copy.deepcopy(contract)
    mixed_heartbeat_contract["run_patrol"]["heartbeat_kind"] = "CHECKER_WAKE_HEARTBEAT"
    reject("mixed heartbeat contract", lambda value: None, contract_value=mixed_heartbeat_contract)

    assert not invalid, "Loop Control binding accepted: " + ", ".join(invalid)

print("PASS: transitional Loop Control binding is closed, current, and local-control conservative")
