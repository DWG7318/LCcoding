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

wake = contract["worker_wake"]
assert wake["initiator"] == "WORKER"
assert wake["receiver"] == "CHECKER"
assert wake["retry_interval_seconds"] == 120
assert wake["levels"] == [
    "DIRECT_SEND",
    "SAME_TASK_READ_LIST_UNARCHIVE",
    "TEMPORARY_HEARTBEAT",
    "PENDING_WAKE_PATROL_FALLBACK",
]
assert wake["ack"] == "RUN_GO_CELL_ROUND_BOUND_WAKE_ACK"

patrol = contract["run_patrol"]
assert patrol["role"] == "RUN_PATROL"
assert patrol["maximum_conversations_per_run"] == 1
assert patrol["maximum_heartbeats_per_run"] == 1
assert patrol["interval_minutes"] == {"LOW": 10, "MEDIUM": 15, "HIGH": 30}
assert patrol["may_create_conversations"] is False
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
    "worker": "DELIVERED_GO_CELL_N_OVER_N_TO_CHECKER",
    "checker": "CURRENT_VALID_D1_ACCEPTED_CELL_AND_GO_BOUNDARY",
    "supervisor": "MATERIAL_GLOBAL_D1_D2_ACTIVE_WAITING_HOLD_VERSION",
    "patrol": "NO_ENGINEERING_PROGRESS",
}
assert contract["capacity"] == {
    "gate_before_dispatch": True,
    "outcomes": ["PASS", "SPLIT_REQUIRED", "CAPACITY_BLOCKED"],
    "worker_may_self_split": False,
}
assert contract["model_policy"] == {
    "ultra": "FORBIDDEN_WITHOUT_SEPARATE_OWNER_AUTHORIZATION",
    "role_default": {"model": "gpt-5.6-terra", "reasoning_effort": "xhigh"},
    "fine_grained_cell": {"model": "gpt-5.6-luna", "reasoning_effort": "xhigh"},
    "high_difficulty_correction": {"model": "gpt-5.6-sol", "reasoning_effort": "xhigh"},
    "minimum": {"model": "gpt-5.6-luna", "reasoning_effort": "xhigh"},
}

assert template["artifact_type"] == "LOOP_CONTROL_BINDING"
assert template["contract"] == {
    "contract_id": "LCCODING_LOOP_CONTROL",
    "contract_version": "1.0.0",
    "contract_sha256": "<exact canonical contract SHA-256>",
}
assert template["runtime_attestation"]["runtime_owner"] == "LCagent_or_trusted_runtime"
assert template["method_mapping"] == {
    "method": "<SLK|CLK|GLK>",
    "method_specific_progress": "<method-owned dimensions only>",
    "method_specific_capacity": "<method-owned reservations only>",
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
