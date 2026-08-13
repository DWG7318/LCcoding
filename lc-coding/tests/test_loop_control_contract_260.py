from pathlib import Path
import json


root = Path(__file__).resolve().parents[2]
contract = json.loads(
    (root / "lc-coding/contracts/loop-control-contract.json").read_text(encoding="utf-8")
)
template = json.loads(
    (root / "lc-coding/templates/LOOP-CONTROL-BINDING.json").read_text(encoding="utf-8")
)
reference = (root / "lc-coding/references/loop-control-contract.md").read_text(encoding="utf-8")
repository_validator = (root / "lc-coding/scripts/validate_repository.py").read_text(encoding="utf-8")

assert contract["contract_id"] == "LCCODING_LOOP_CONTROL"
assert contract["contract_version"] == "1.0.0"
assert contract["owner"] == "LCCoding"
assert contract["is_loop_method"] is False
assert contract["runtime_execution_owner"] == "LCagent_or_trusted_runtime"
assert contract["method_consumers"] == ["SLK", "CLK", "GLK"]
assert contract["heartbeat_separation"] == {
    "shared_id": "FORBIDDEN",
    "shared_lifecycle": "FORBIDDEN",
    "shared_counting": "FORBIDDEN",
    "shared_evidence_claim": "FORBIDDEN",
}
assert contract["runtime_attestation_policy"] == {
    "required_owner": "LCagent_or_trusted_runtime",
    "required_result": "PASS",
    "required_currentness": "CURRENT",
    "max_validated_age_minutes": 30,
    "max_validity_minutes": 60,
}

wake = contract["worker_wake"]
assert wake["initiator"] == "WORKER"
assert wake["receiver"] == "CHECKER"
assert wake["retry_interval_seconds"] == 120
assert wake["levels"] == [
    "DIRECT_SEND",
    "SAME_TASK_READ_LIST_UNARCHIVE",
    "CHECKER_WAKE_HEARTBEAT",
    "PENDING_WAKE_PATROL_FALLBACK",
]
assert wake["ack"] == "RUN_GO_CELL_ROUND_BOUND_WAKE_ACK"
assert wake["heartbeat_kind"] == "CHECKER_WAKE_HEARTBEAT"
assert wake["maximum_temporary_heartbeats_per_delivery_wake_incident"] == 1
assert wake["terminal_action"] == "REMOVE_ON_WAKE_ACK_OR_TERMINAL_FALLBACK"

patrol = contract["run_patrol"]
assert patrol["role"] == "RUN_PATROL"
assert patrol["maximum_conversations_per_run"] == 1
assert patrol["heartbeat_kind"] == "RUN_PATROL_HEARTBEAT"
assert patrol["maximum_run_patrol_heartbeats_per_run"] == 1
assert patrol["interval_minutes"] == {"LOW": 10, "MEDIUM": 15, "HIGH": 30}
assert patrol["may_create_conversations"] is False
assert patrol["may_report_engineering_progress"] is False
assert patrol["terminal_action"] == "ARCHIVE_AND_DELETE_HEARTBEAT"
assert patrol["checks"] == [
    "UNEXPLAINED_LOOP_STOPPAGE",
    "PENDING_WAKE",
    "ACTUAL_SUBAGENT_USE",
    "SUPERVISOR_FORBIDDEN_WAIT",
    "DUPLICATE_PATROL_OR_HEARTBEAT",
    "PIN_PROVENANCE",
    "TERMINAL_CLOSURE",
]

assert contract["supervisor_wait"] == {
    "positive_duration_wait_threads": "FORBIDDEN",
    "looping_wait_threads": "FORBIDDEN",
    "wait_all": "FORBIDDEN",
    "zero_timeout_snapshot": "ALLOWED",
}
assert contract["prohibitions"] == {
    "actual_subagent_operations": ["spawn_agent", "delegate_task", "hidden_agent", "background_agent"],
    "agent_pin": "FORBIDDEN",
    "owner_pin": "EXPLICIT_OWNER_UI_OR_ITEM_AUTHORIZATION_ONLY",
}

assert contract["progress"] == {
    "worker": "DELIVERED_CELL_N_OVER_N_TO_CHECKER",
    "checker": "ACCEPTED_CELL_N_OVER_N_TO_SUPERVISOR",
    "supervisor": "GO_LEVEL_RUN_AND_MATERIAL_STATE",
    "patrol": "NO_ENGINEERING_PROGRESS",
}
assert contract["capacity"] == {
    "gate_before_dispatch": True,
    "outcomes": ["PASS", "SPLIT_REQUIRED", "CAPACITY_BLOCKED"],
    "worker_may_self_split": False,
}
assert contract["model_policy"] == {
    "patrol": {
        "reference_model": "gpt-5.6-luna",
        "capability_class": "FASTEST_NONTECHNICAL",
        "reasoning_effort": "xhigh",
    },
    "technical": {
        "reference_model": "gpt-5.6-terra",
        "capability_class": "NORMAL_TECHNICAL",
        "reasoning_effort": "xhigh",
    },
    "high_difficulty_correction": {
        "reference_model": "gpt-5.6-sol",
        "capability_class": "DIFFICULT_CORRECTION",
        "reasoning_effort": "xhigh",
    },
    "ultra": {
        "requires": "ITEM_SPECIFIC_OWNER_AUTHORIZATION",
        "allowed_role_kind": "HIGH_DIFFICULTY_CORRECTION",
        "authorization_fields": [
            "item_id",
            "owner_authorization_id",
            "authorization_evidence_digest",
            "result",
        ],
        "authorization_result": "OWNER_APPROVED_ULTRA",
    },
    "forbidden_model_maximum": "gpt-5.5",
}

assert template["artifact_type"] == "LOOP_CONTROL_BINDING"
assert template["binding_version"] == "1.0.0"
assert template["contract"] == {
    "contract_id": "LCCODING_LOOP_CONTROL",
    "contract_version": "1.0.0",
    "contract_sha256": "<exact canonical contract SHA-256>",
}
assert template["runtime_attestation"]["runtime_owner"] == "LCagent_or_trusted_runtime"
assert template["method_mapping"] == {
    "method": "<SLK|CLK|GLK>",
    "topology_owned_progress_fields": ["<method-owned progress field>"],
    "topology_owned_capacity_fields": ["<method-owned capacity field>"],
    "topology_owned_model_fields": ["<method-owned model field>"],
    "topology_owned_evidence_fields": ["<method-owned evidence field>"],
}
assert template["model_binding"]["owner_ultra_authorization"] == {
    "item_id": "<item-specific Run or correction item ID>",
    "owner_authorization_id": "<item-specific Owner authorization ID>",
    "authorization_evidence_digest": "<sha256 of Owner authorization evidence>",
    "result": "OWNER_APPROVED_ULTRA",
}
assert template["local_control"]["state"] == "ACTIVE|RETAINED|RETIRED"
assert template["local_control"]["retirement_evidence"] == {
    "runtime_conformance": {
        "positive": {
            "evidence_id": "<positive current conformance evidence ID>",
            "evidence_digest": "<sha256 of positive conformance evidence>",
            "result": "PASS",
        },
        "negative": {
            "evidence_id": "<negative current conformance evidence ID>",
            "evidence_digest": "<sha256 of negative conformance evidence>",
            "result": "PASS",
        },
    },
    "historical_receipts": {
        "status": "READABLE",
        "evidence_id": "<historical receipt readability evidence ID>",
        "evidence_digest": "<sha256 of historical receipt readability evidence>",
    },
    "owner_approved_release": {
        "release_id": "<method-specific Owner-approved release ID>",
        "approval_evidence_id": "<Owner retirement approval evidence ID>",
        "approval_evidence_digest": "<sha256 of Owner retirement approval evidence>",
        "result": "LOCAL_CONTROL_RETIRED",
    },
}

for marker in (
    "not a fourth Loop method",
    "does not implement a runtime",
    "LCagent or another trusted runtime",
    "not enough to create an envelope",
    "does not replace D0-D3",
):
    assert marker in reference

for required_path in (
    "lc-coding/contracts/loop-control-contract.json",
    "lc-coding/templates/LOOP-CONTROL-BINDING.json",
    "lc-coding/references/loop-control-contract.md",
):
    assert required_path in repository_validator

print("PASS: Loop Control Contract")
