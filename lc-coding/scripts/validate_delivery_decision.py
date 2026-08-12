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
