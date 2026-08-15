#!/usr/bin/env python3
from pathlib import Path
import argparse
from datetime import datetime
import importlib.util
import json
import math
import re


GROUPS = [
    "delivery_model",
    "assets",
    "source_and_modification_rights",
    "runtime_and_infrastructure",
    "data",
    "internal_dependencies",
    "license",
    "operations",
]
DECISION_FIELDS = {
    "delivery_decision_id",
    "delivery_id",
    "customer",
    "candidate_id",
    "owner_policy_version",
    "locked_exclusions",
    "decisions",
    "qa_status",
    "owner_confirmed",
    "confirmed_at",
}

PROJECT_VALIDATOR_PATH = Path(__file__).with_name("validate_project.py")
PROJECT_VALIDATOR_SPEC = importlib.util.spec_from_file_location(
    "lccoding_delivery_project_validator", PROJECT_VALIDATOR_PATH
)
PROJECT_VALIDATOR = importlib.util.module_from_spec(PROJECT_VALIDATOR_SPEC)
PROJECT_VALIDATOR_SPEC.loader.exec_module(PROJECT_VALIDATOR)
POLICY_PATH = Path(__file__).resolve().parents[1] / "contracts/delivery-policy.json"
DELIVERY_GENERIC_VALUES = frozenset(
    PROJECT_VALIDATOR._VULNERABILITY_VALIDATOR.GENERIC
).union({
    "", "N/A", "CONFIRMED", "APPROVED", "ACCEPTED", "FAIL", "INVALID",
    "REJECTED", "PLACEHOLDER", "SAMPLE", "EXAMPLE", "FAKE", "TEST", "MOCK",
    "STUB", "DUMMY", "CURRENT", "SUPERSEDED", "DELIVERY_METHOD_CONFIRMED",
    "POST_SECURITY_OWNER_ACCEPTED", "DELIVERY_READY", "LOOP_OWNER_ACCEPTED",
    "ALL_REQUIRED_RUNS_ACCEPTED", "INITIAL_READY",
})
DELIVERY_TEST_HEADS = frozenset({
    "PLACEHOLDER", "SAMPLE", "EXAMPLE", "FAKE", "TEST", "MOCK", "STUB", "DUMMY",
})
AGENT_DECISION_GRAMMAR = {
    "runtime_and_infrastructure": {
        "runtime_responsibility": "CUSTOMER",
        "model_responsibility": "CUSTOMER",
        "provider_responsibility": "CUSTOMER",
        "replacement_route": "IMPACT_SECURITY_REVALIDATION",
    },
    "data": {
        "credential_owner": "CUSTOMER",
        "private_agent_data": "EXCLUDED",
    },
    "operations": {
        "fallback_operation": "OWNER_CONTROLLED",
        "kill_switch_operation": "OWNER_CONTROLLED",
        "audit_retention": "APPEND_ONLY_RETAINED",
    },
}
AGENT_DELIVERY_CERTIFICATION_FIELDS = (
    "state", "candidate_id", "candidate_hash", "configuration_baseline_id",
    "configuration_baseline_hash", "production_topology_id",
    "production_topology_hash", "runtime_adapter_attestation_id",
    "runtime_adapter_attestation_hash", "runtime_adapter_id",
    "runtime_adapter_version", "runtime_adapter_digest",
    "product_agent_applicability", "product_agent_id", "operations_agent_id",
    "operations_base_model_id", "operations_base_model_hash",
    "operations_runtime_provider_id", "operations_runtime_provider_hash",
    "product_base_model_id", "product_base_model_hash",
    "product_runtime_provider_id", "product_runtime_provider_hash",
    "isolation_evidence_id", "isolation_evidence_hash",
    "fallback_evidence_id", "fallback_evidence_hash",
    "kill_switch_evidence_id", "kill_switch_evidence_hash",
    "audit_evidence_id", "audit_evidence_hash",
    "vulnerability_closure_id", "vulnerability_closure_hash",
    "post_security_acceptance_id", "post_security_acceptance_hash", "result",
)
AGENT_DELIVERY_MANIFEST_ONLY_FIELDS = (
    "runtime_certification_reference", "runtime_certification_hash",
    "delivery_decision_id", "delivery_decision_hash",
    "approved_product_assets", "approved_runtime_assets",
)
AGENT_DELIVERY_MANIFEST_FIELDS = (
    AGENT_DELIVERY_CERTIFICATION_FIELDS[:-1]
    + AGENT_DELIVERY_MANIFEST_ONLY_FIELDS
    + ("result",)
)
AGENT_DELIVERY_FORBIDDEN_ASSET_TERMS = (
    "raw-prompt", "raw-prompts", "system-prompt", "system-prompts",
    "private-memory", "private-memories", "session", "sessions",
    "context", "contexts", "retriever", "retrievers",
    "vector-store", "vector-stores", "prompt-cache", "prompt-caches",
    "credential", "credentials", "secret", "secrets", "key", "keys",
    "construction-agent", "construction-agents",
    "runtime-internal", "runtime-internals",
)


def valid_agent_decision_record(value, expected):
    if not isinstance(value, str):
        return False
    parts = value.split(";")
    if not parts or parts[0] != "AGENT_DELIVERY_V1":
        return False
    record = {}
    for token in parts[1:]:
        if token.count("=") != 1:
            return False
        key, selected = token.split("=", 1)
        if key in record:
            return False
        record[key] = selected
    return record == expected


def unique_string_list(value, *, nonempty=True):
    return (
        isinstance(value, list)
        and (bool(value) or not nonempty)
        and all(isinstance(item, str) for item in value)
        and len(value) == len(set(value))
    )


def lccoding_root(path):
    resolved = Path(path).resolve()
    if resolved.name != "DELIVERY-DECISION.json" or resolved.parent.name != ".lccoding":
        return None
    return resolved.parent


def strict_json(path):
    def reject_duplicate_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key: " + str(key))
            result[key] = value
        return result

    def reject_nonfinite(value):
        raise ValueError("non-finite JSON number: " + value)

    def strict_float(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError("non-finite JSON number: " + value)
        return parsed

    raw = Path(path).read_bytes()
    text = raw.decode("utf-8")
    return json.loads(
        text,
        object_pairs_hook=reject_duplicate_pairs,
        parse_constant=reject_nonfinite,
        parse_float=strict_float,
    )


def exact_candidate(value):
    return PROJECT_VALIDATOR.exact_security_id_hash(value)


def delivery_meaningful(value, *, identifier=False):
    if not isinstance(value, str):
        return False
    text = value.strip()
    upper = text.upper()
    head = re.split(r"[._-]", upper, maxsplit=1)[0]
    generic_identity_prefix = identifier and any(
        generic
        and (
            upper == generic
            or any(upper.startswith(generic + separator) for separator in "._-")
        )
        for generic in DELIVERY_GENERIC_VALUES
    )
    if (
        not text
        or not any(character.isalnum() for character in text)
        or upper in DELIVERY_GENERIC_VALUES
        or generic_identity_prefix
        or head in DELIVERY_TEST_HEADS
        or any(ord(character) < 32 or ord(character) == 127 for character in text)
    ):
        return False
    return not identifier or PROJECT_VALIDATOR.stable_id(text)


def exact_utc_timestamp(value):
    if not isinstance(value, str) or re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value
    ) is None:
        return False
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return False
    return True


def load_policy():
    errors = []
    try:
        policy = strict_json(POLICY_PATH)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        return None, ["Delivery policy is not strict JSON: " + str(error)]
    if not isinstance(policy, dict):
        return None, ["Delivery policy must be a JSON object"]
    groups = policy.get("required_decision_groups")
    if groups != GROUPS:
        errors.append("Delivery policy required decision groups are invalid")
    locked = policy.get("owner_locked_default_exclusions")
    if not isinstance(locked, list) or not locked or any(
        not isinstance(item, str) or not item.strip() for item in locked
    ) or len(locked or []) != len(set(locked or [])):
        errors.append("Delivery policy Owner-locked exclusions are invalid")
    suffixes = policy.get("protected_package_suffixes")
    if (
        not isinstance(suffixes, list)
        or not suffixes
        or any(
            not isinstance(item, str)
            or not item.startswith(".")
            or item != item.casefold()
            for item in suffixes or []
        )
        or len(suffixes or []) != len(set(suffixes or []))
    ):
        errors.append("Delivery policy protected package suffix table is invalid")
    agent_records = policy.get("agent_delivery_decision_records")
    if not isinstance(agent_records, dict) or set(agent_records) != set(
        AGENT_DECISION_GRAMMAR
    ) or any(not valid_agent_decision_record(
        (agent_records or {}).get(group), expected
    ) for group, expected in AGENT_DECISION_GRAMMAR.items()):
        errors.append("Delivery policy Agent-native Q&A records are invalid")
    certification_fields = policy.get("agent_delivery_certification_fields")
    manifest_fields = policy.get("agent_delivery_manifest_fields")
    certification_fields_valid = unique_string_list(certification_fields)
    manifest_fields_valid = unique_string_list(manifest_fields)
    if (
        not certification_fields_valid
        or certification_fields != list(AGENT_DELIVERY_CERTIFICATION_FIELDS)
    ):
        errors.append("Delivery policy Agent certification fields are invalid")
    if (
        not manifest_fields_valid
        or manifest_fields != list(AGENT_DELIVERY_MANIFEST_FIELDS)
    ):
        errors.append("Delivery policy Agent manifest fields are invalid")
    forbidden_terms = policy.get("agent_delivery_forbidden_asset_terms")
    if (
        not unique_string_list(forbidden_terms)
        or forbidden_terms != list(AGENT_DELIVERY_FORBIDDEN_ASSET_TERMS)
    ):
        errors.append("Delivery policy forbidden Agent asset terms are invalid")
    return policy, errors


def validate_decision(path):
    path = Path(path)
    errors = []
    lc = lccoding_root(path)
    if lc is None:
        return None, None, [
            "Delivery Decision must be the contained .lccoding/DELIVERY-DECISION.json"
        ]
    try:
        data = strict_json(path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        return None, None, ["Delivery Decision is not strict JSON: " + str(error)]
    if not isinstance(data, dict):
        return None, None, ["Delivery Decision must be a closed JSON object"]
    missing = DECISION_FIELDS - set(data)
    unknown = set(data) - DECISION_FIELDS
    if missing:
        errors.append("Delivery Decision missing fields " + ", ".join(sorted(missing)))
    if unknown:
        errors.append("Delivery Decision unknown fields " + ", ".join(sorted(unknown)))
    policy, policy_errors = load_policy()
    errors.extend(policy_errors)
    candidate = exact_candidate(data.get("candidate_id"))
    if candidate is None:
        errors.append("Delivery Decision candidate_id requires exact ID / sha256 identity")
    for field in ("delivery_decision_id", "delivery_id"):
        if not delivery_meaningful(data.get(field), identifier=True):
            errors.append("Delivery Decision requires safe non-generic " + field)
    if not delivery_meaningful(data.get("customer")):
        errors.append("customer missing or generic")
    if not PROJECT_VALIDATOR.component_version(data.get("owner_policy_version")):
        errors.append("owner policy version must use the existing semantic version format")
    exclusions = data.get("locked_exclusions")
    if not isinstance(exclusions, list) or any(
        not isinstance(item, str) or not item.strip() for item in exclusions
    ) or len(exclusions or []) != len(set(exclusions or [])):
        errors.append("locked exclusions must be a unique string list")
    elif isinstance(policy, dict) and exclusions != policy.get(
        "owner_locked_default_exclusions"
    ):
        errors.append("locked exclusions must exactly match Delivery policy")
    if data.get("qa_status") != "COMPLETE":
        errors.append("Q&A incomplete")
    if data.get("owner_confirmed") is not True:
        errors.append("Owner confirmation missing")
    if not exact_utc_timestamp(data.get("confirmed_at")):
        errors.append("confirmation timestamp must be an exact valid UTC timestamp")
    decisions = data.get("decisions")
    if not isinstance(decisions, dict):
        errors.append("decisions must be a closed object")
    else:
        if set(decisions) != set(GROUPS):
            errors.append("decision groups must exactly match delivery policy")
        for group in GROUPS:
            answer = decisions.get(group)
            if not isinstance(answer, dict) or set(answer) != {"selected"}:
                errors.append("decision group must be a closed selected answer: " + group)
                continue
            selected = answer.get("selected")
            if not delivery_meaningful(selected):
                errors.append("missing decision group: " + group)

    status_path = lc / "status.json"
    try:
        status = strict_json(status_path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        return data, None, errors + ["authoritative status is unavailable: " + str(error)]
    if not isinstance(status, dict):
        return data, None, errors + ["authoritative status must be an object"]
    errors.extend(PROJECT_VALIDATOR.validate_security_invalidation(lc, status))
    canonical = status.get("canonical_candidate", {})
    status_candidate = (
        canonical.get("candidate_id"), canonical.get("candidate_hash")
    ) if isinstance(canonical, dict) else None
    if candidate is None or candidate != status_candidate:
        errors.append("Delivery Decision candidate does not match authoritative current candidate")
    closure = status.get("vulnerability_closure")
    acceptance = status.get("post_security_owner_acceptance")
    if not isinstance(closure, dict) or closure.get("state") != "VULNERABILITY_CLOSED":
        errors.append("Delivery Decision requires current VULNERABILITY_CLOSED")
    if not isinstance(acceptance, dict) or acceptance.get("state") != "POST_SECURITY_OWNER_ACCEPTED":
        errors.append("Delivery Decision requires current POST_SECURITY_OWNER_ACCEPTED")
    if status.get("delivery_method_qa") != "DELIVERY_METHOD_CONFIRMED":
        errors.append("authoritative Delivery Method Q&A is not confirmed")
    if status.get("status_schema_version") == "2.8.0":
        errors.extend(PROJECT_VALIDATOR.validate_agent_native_artifacts(lc, status))
        agent_slice = status.get("agent_slice_integration")
        if not isinstance(agent_slice, dict) or agent_slice.get("state") != "AGENT_SLICES_ACCEPTED":
            errors.append("Agent-native Delivery requires accepted Agent Slice integration")
        expected_records = policy.get("agent_delivery_decision_records", {}) if isinstance(policy, dict) else {}
        for group, expected in expected_records.items():
            answer = decisions.get(group) if isinstance(decisions, dict) else None
            if not isinstance(answer, dict) or answer.get("selected") != expected:
                errors.append("Agent-native Delivery Q&A record mismatch: " + group)
    return data, status, errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("decision")
    args = parser.parse_args()
    _, _, errors = validate_decision(args.decision)
    if errors:
        print("FAIL")
        print("\n".join(errors).encode("ascii", "backslashreplace").decode("ascii"))
        raise SystemExit(1)
    print("PASS")


if __name__ == "__main__":
    main()
