#!/usr/bin/env python3
from pathlib import Path
import argparse
import importlib.util
import json
import os
import re
import hashlib
import unicodedata


MANIFEST_FIELDS = {
    "delivery_id", "project_id", "product_version", "candidate_id", "included",
    "excluded", "internal_dependencies", "runtime_certification", "license_policy",
    "package_hashes", "verification_receipts", "owner_approval",
    "delivery_decision_id", "delivery_method_confirmed", "qa_status", "agent_delivery",
}
HASH_RE = re.compile(r"sha256:[0-9a-f]{64}")
VERSION_BUILD_SUFFIX_RE = re.compile(
    r"^(?:[-_@.](?:"
    r"v?\d+(?:\.\d+){1,3}(?:[-+][a-z0-9.-]+)?|"
    r"(?:build|release)[-_]?[a-z0-9.-]+|"
    r"x86|x64|arm64|amd64|win32|win64|linux|macos"
    r"))+$"
)
WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}
BIDI_CONTROLS = {
    *range(0x202A, 0x202F),
    *range(0x2066, 0x206A),
    0x200E,
    0x200F,
}

DECISION_PATH = Path(__file__).with_name("validate_delivery_decision.py")
DECISION_SPEC = importlib.util.spec_from_file_location(
    "lccoding_delivery_decision_validator", DECISION_PATH
)
DECISION_VALIDATOR = importlib.util.module_from_spec(DECISION_SPEC)
DECISION_SPEC.loader.exec_module(DECISION_VALIDATOR)
PROJECT_VALIDATOR = DECISION_VALIDATOR.PROJECT_VALIDATOR
AGENT_DELIVERY_HEADING = "## Agent Delivery evidence"


def file_hash(path):
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def closed_record(value, fields, label):
    if not isinstance(value, dict): return {}, [label + " must be a closed object"]
    missing = set(fields) - set(value); unknown = set(value) - set(fields); errors = []
    if missing: errors.append(label + " missing fields " + ", ".join(sorted(missing)))
    if unknown: errors.append(label + " unknown fields " + ", ".join(sorted(unknown)))
    return value, errors


def not_applicable_agent_delivery(fields):
    return {
        field: ([] if field in {"approved_product_assets", "approved_runtime_assets"}
                else "NOT_APPLICABLE")
        for field in fields
    }


def forbidden_agent_asset(value, terms):
    normalized = re.sub(r"[^a-z0-9]+", "-", str(value).casefold()).strip("-")
    padded = "-" + normalized + "-"
    return any(
        "-" + re.sub(r"[^a-z0-9]+", "-", term).strip("-") + "-" in padded
        for term in terms
    )


def parse_agent_certification(path):
    try: text = Path(path).read_bytes().decode("utf-8")
    except (OSError, UnicodeError) as error: return {}, ["Runtime Certification is unreadable: " + str(error)]
    pattern = re.escape(AGENT_DELIVERY_HEADING) + r"\r?\n\r?\n```json\r?\n(.*?)\r?\n```"
    matches = re.findall(pattern, text, re.DOTALL)
    if len(matches) != 1: return {}, ["Runtime Certification requires one strict Agent Delivery JSON section"]
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result: raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result
    try:
        return json.loads(matches[0], object_pairs_hook=pairs,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError("non-finite JSON"))), []
    except (ValueError, json.JSONDecodeError) as error:
        return {}, ["Runtime Certification Agent Delivery JSON is invalid: " + str(error)]


def expected_agent_certification(lc, status):
    errors = []; lc = Path(lc)
    binding, binding_errors = PROJECT_VALIDATOR._expected_agent_security_binding(lc, status)
    errors.extend(binding_errors)
    if not isinstance(binding, dict) or binding.get("state") != "BOUND":
        return {}, errors + ["Agent-native Delivery requires a BOUND Agent security identity"]
    try:
        configuration = PROJECT_VALIDATOR._AGENT_NATIVE.strict_json(
            lc / PROJECT_VALIDATOR.AGENT_CONFIGURATION_BASELINE_NAME
        )
        attestation = PROJECT_VALIDATOR._AGENT_NATIVE.strict_json(
            lc / PROJECT_VALIDATOR.RUNTIME_ADAPTER_ATTESTATION_NAME
        )
    except (OSError, UnicodeError, ValueError) as error:
        return {}, errors + ["Agent Delivery identity evidence is unreadable: " + str(error)]
    closure_status = status.get("vulnerability_closure", {})
    post_status = status.get("post_security_owner_acceptance", {})
    closure_path = PROJECT_VALIDATOR.resolve_security_reference(
        lc, closure_status.get("current_receipt_reference")
    )
    post_path = PROJECT_VALIDATOR.resolve_security_reference(
        lc, post_status.get("current_acceptance_reference")
    )
    if closure_path is None or post_path is None:
        return {}, errors + ["Agent Delivery requires current contained security receipts"]
    operations = configuration.get("operations_agent", {})
    product = configuration.get("product_agent", {})
    authority = attestation.get("authority_boundaries", {})
    fallback = attestation.get("fallback", {})
    kill_switch = attestation.get("kill_switch", {})
    applicable = binding.get("product_agent_applicability") != "NOT_APPLICABLE"
    expected = dict(binding)
    expected.pop("identity_status", None)
    expected.update({
        "operations_base_model_id": operations.get("base_model_id"),
        "operations_base_model_hash": operations.get("base_model_hash"),
        "operations_runtime_provider_id": operations.get("runtime_provider_id"),
        "operations_runtime_provider_hash": operations.get("runtime_provider_hash"),
        "product_base_model_id": product.get("base_model_id") if applicable else "NOT_APPLICABLE",
        "product_base_model_hash": product.get("base_model_hash") if applicable else "NOT_APPLICABLE",
        "product_runtime_provider_id": product.get("runtime_provider_id") if applicable else "NOT_APPLICABLE",
        "product_runtime_provider_hash": product.get("runtime_provider_hash") if applicable else "NOT_APPLICABLE",
        "isolation_evidence_id": authority.get("isolation_evidence_id"),
        "isolation_evidence_hash": authority.get("isolation_evidence_hash"),
        "fallback_evidence_id": fallback.get("fallback_id"),
        "fallback_evidence_hash": fallback.get("evidence_hash"),
        "kill_switch_evidence_id": kill_switch.get("kill_switch_id"),
        "kill_switch_evidence_hash": kill_switch.get("evidence_hash"),
        "audit_evidence_id": operations.get("audit_stream_id"),
        "audit_evidence_hash": operations.get("audit_stream_hash"),
        "vulnerability_closure_id": closure_status.get("current_receipt_id"),
        "vulnerability_closure_hash": file_hash(closure_path),
        "post_security_acceptance_id": post_status.get("current_acceptance_id"),
        "post_security_acceptance_hash": file_hash(post_path),
        "result": "PASS",
    })
    return expected, errors


def manifest_root(path):
    resolved = Path(path).resolve()
    if resolved.name != "DELIVERY-MANIFEST.json" or resolved.parent.name != ".lccoding":
        return None
    return resolved.parent


def unique_string_list(value, *, allow_empty=False):
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(isinstance(item, str) and item.strip() for item in value)
        and len(value) == len(set(value))
    )


def normalized_asset(value):
    if not isinstance(value, str):
        return None
    parts = [part.strip() for part in re.split(r"[\\/]", value.strip())]
    if not parts or any(not part for part in parts):
        return None
    return "/".join(parts).casefold()


def protected_asset(value, locked, suffixes=None):
    normalized = normalized_asset(value)
    if normalized is None:
        return False
    if suffixes is None:
        policy, _ = DECISION_VALIDATOR.load_policy()
        suffixes = policy.get("protected_package_suffixes", []) if isinstance(
            policy, dict
        ) else []
    if not isinstance(suffixes, (list, tuple)) or any(
        not isinstance(item, str) for item in suffixes
    ):
        suffixes = ()
    protected = {item.casefold() for item in locked}
    ordered_suffixes = sorted(set(suffixes), key=len, reverse=True)
    for part in normalized.split("/"):
        part = part.split(":", 1)[0].rstrip(" .")
        candidate = part
        while candidate:
            for protected_name in protected:
                if candidate == protected_name:
                    return True
                if candidate.startswith(protected_name) and VERSION_BUILD_SUFFIX_RE.fullmatch(
                    candidate[len(protected_name):]
                ):
                    return True
            matched = next(
                (suffix for suffix in ordered_suffixes if candidate.endswith(suffix)),
                None,
            )
            if matched is None:
                break
            stripped = candidate[:-len(matched)].rstrip(" .")
            if not stripped or len(stripped) >= len(candidate):
                break
            candidate = stripped
    return normalized in protected


def package_path_syntax(value):
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or value != unicodedata.normalize("NFC", value)
    ):
        return False
    if "\\" in value or value.startswith("/") or value.endswith("/"):
        return False
    if any(ord(character) < 32 or ord(character) == 127 or ord(character) in BIDI_CONTROLS for character in value):
        return False
    if any(character in '<>:"|?*' for character in value):
        return False
    parts = value.split("/")
    if any(part in {"", ".", ".."} or part.endswith((".", " ")) for part in parts):
        return False
    if any(part.startswith(".") for part in parts):
        return False
    for part in parts:
        stem = part.split(".", 1)[0].upper()
        if stem in WINDOWS_RESERVED:
            return False
    return True


def windows_package_identity(value):
    if not package_path_syntax(value):
        return None
    return "/".join(
        unicodedata.normalize("NFC", part).casefold() for part in value.split("/")
    )


def resolve_package_path(project_root, value, locked=(), suffixes=()):
    if not package_path_syntax(value) or protected_asset(value, locked, suffixes):
        return None, "package path is not canonical and safe"
    try:
        root = Path(project_root).resolve(strict=True)
        unresolved = root.joinpath(*value.split("/"))
        resolved = unresolved.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        return None, "package path is missing or escapes the total project root"
    current = root
    for part in value.split("/"):
        current = current / part
        if current.is_symlink():
            return None, "package path must not traverse a symbolic link"
    if not resolved.is_file():
        return None, "package path must resolve to a regular file"
    return resolved, None


def validate_package_hashes(value, project_root, locked, suffixes):
    if not isinstance(value, dict) or not value:
        return ["package_hashes must be a non-empty closed object"]
    errors = []
    windows_identities = []
    resolved_paths = []
    for asset, digest in value.items():
        windows_identity = windows_package_identity(asset)
        if windows_identity is not None:
            if windows_identity in windows_identities:
                errors.append("package paths must be unique under Windows identity")
            windows_identities.append(windows_identity)
        resolved, path_error = resolve_package_path(
            project_root, asset, locked, suffixes
        )
        if path_error:
            errors.append(path_error)
        if not isinstance(digest, str) or HASH_RE.fullmatch(digest) is None:
            errors.append("package_hashes requires exact lowercase SHA-256 values")
        elif resolved is not None:
            try:
                if resolved.stat().st_nlink > 1:
                    errors.append("package file must not have physical hard-link aliases")
            except OSError:
                errors.append("package file link identity could not be verified")
            try:
                if any(os.path.samefile(resolved, prior) for prior in resolved_paths):
                    errors.append("package paths must not alias the same physical file")
            except OSError:
                errors.append("package file identity could not be verified")
            resolved_paths.append(resolved)
            try:
                actual = "sha256:" + hashlib.sha256(resolved.read_bytes()).hexdigest()
            except OSError:
                errors.append("package bytes could not be read safely")
            else:
                if actual != digest:
                    errors.append("package_hashes does not match actual package bytes")
    return errors


def validate_verification_receipts(value, candidate, package_hashes):
    if not isinstance(value, list) or not value:
        return ["verification_receipts must be a non-empty closed record list"]
    errors = []
    receipt_ids = []
    covered_assets = []
    for record in value:
        if not isinstance(record, str):
            errors.append("verification receipt must be an inline string record")
            continue
        parts = record.split(" | ")
        if len(parts) != 4:
            errors.append("verification receipt has invalid closed shape")
            continue
        receipt_id, candidate_value, asset, digest = parts
        if not DECISION_VALIDATOR.delivery_meaningful(receipt_id, identifier=True):
            errors.append("verification receipt ID is invalid or generic")
        receipt_ids.append(receipt_id)
        if DECISION_VALIDATOR.exact_candidate(candidate_value) != candidate:
            errors.append("verification receipt candidate does not match current manifest")
        if not package_path_syntax(asset) or asset not in package_hashes:
            errors.append("verification receipt asset does not match package_hashes")
        covered_assets.append(asset)
        if not isinstance(digest, str) or HASH_RE.fullmatch(digest) is None:
            errors.append("verification receipt package digest is invalid")
        elif package_hashes.get(asset) != digest:
            errors.append("verification receipt package digest does not match package_hashes")
    if len(receipt_ids) != len(set(receipt_ids)):
        errors.append("verification receipt IDs must be unique")
    if len(covered_assets) != len(set(covered_assets)):
        errors.append("each package may have exactly one verification receipt")
    if set(covered_assets) != set(package_hashes):
        errors.append("verification receipts must exactly cover package_hashes")
    return errors


def validate_manifest(path):
    path = Path(path)
    errors = []
    lc = manifest_root(path)
    if lc is None:
        return ["Delivery Manifest must be the contained .lccoding/DELIVERY-MANIFEST.json"]
    try:
        data = DECISION_VALIDATOR.strict_json(path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        return ["Delivery Manifest is not strict JSON: " + str(error)]
    if not isinstance(data, dict):
        return ["Delivery Manifest must be a closed JSON object"]
    missing = MANIFEST_FIELDS - set(data)
    unknown = set(data) - MANIFEST_FIELDS
    if missing:
        errors.append("Delivery Manifest missing fields " + ", ".join(sorted(missing)))
    if unknown:
        errors.append("Delivery Manifest unknown fields " + ", ".join(sorted(unknown)))

    candidate = DECISION_VALIDATOR.exact_candidate(data.get("candidate_id"))
    if candidate is None:
        errors.append("Delivery Manifest candidate_id requires exact ID / sha256 identity")
    for field in ("delivery_id", "project_id"):
        if not DECISION_VALIDATOR.delivery_meaningful(
            data.get(field), identifier=True
        ):
            errors.append("Delivery Manifest requires safe non-generic " + field)
    if not PROJECT_VALIDATOR.component_version(data.get("product_version")):
        errors.append("product_version must use the existing semantic version format")
    for field in ("runtime_certification", "license_policy"):
        if not DECISION_VALIDATOR.delivery_meaningful(data.get(field)):
            errors.append(field + " missing or generic")
    included = data.get("included")
    excluded = data.get("excluded")
    dependencies = data.get("internal_dependencies")
    if not unique_string_list(included):
        errors.append("included must be a non-empty unique string list")
        included = []
    if not unique_string_list(excluded, allow_empty=True):
        errors.append("excluded must be a unique string list")
        excluded = []
    if not unique_string_list(dependencies, allow_empty=True):
        errors.append("internal_dependencies must be a unique string list")
    normalized_included = {normalized_asset(item) for item in included}
    normalized_excluded = {normalized_asset(item) for item in excluded}
    if normalized_included & normalized_excluded:
        errors.append("included and excluded assets must be disjoint")
    policy, policy_errors = DECISION_VALIDATOR.load_policy()
    errors.extend(policy_errors)
    locked = policy.get("owner_locked_default_exclusions", []) if isinstance(policy, dict) else []
    suffixes = policy.get("protected_package_suffixes", []) if isinstance(policy, dict) else []
    bad = sorted(
        item for item in included if protected_asset(item, locked, suffixes)
    )
    if bad:
        errors.append("forbidden internal assets included")
    forbidden_terms = policy.get("agent_delivery_forbidden_asset_terms", []) if isinstance(policy, dict) else []
    exposed_assets = [*included, *(data.get("package_hashes", {}) if isinstance(data.get("package_hashes"), dict) else {})]
    if any(forbidden_agent_asset(asset, forbidden_terms) for asset in exposed_assets):
        errors.append("Agent-private or unapproved Runtime evidence included")
    package_hashes = data.get("package_hashes")
    errors.extend(validate_package_hashes(
        package_hashes, lc.parent, locked, suffixes
    ))
    errors.extend(validate_verification_receipts(
        data.get("verification_receipts"), candidate,
        package_hashes if isinstance(package_hashes, dict) else {},
    ))
    if data.get("qa_status") != "COMPLETE":
        errors.append("Delivery Method Q&A incomplete")
    if data.get("delivery_method_confirmed") is not True:
        errors.append("delivery method not confirmed")
    if data.get("owner_approval") != "APPROVED":
        errors.append("Owner approval missing")

    decision_path = lc / "DELIVERY-DECISION.json"
    decision, status, decision_errors = DECISION_VALIDATOR.validate_decision(decision_path)
    errors.extend(decision_errors)
    if isinstance(decision, dict):
        if data.get("delivery_decision_id") != decision.get("delivery_decision_id"):
            errors.append("Delivery Manifest does not bind the current Delivery Decision")
        if data.get("delivery_id") != decision.get("delivery_id"):
            errors.append("Delivery Manifest delivery_id does not match the Delivery Decision")
        if candidate is None or candidate != DECISION_VALIDATOR.exact_candidate(
            decision.get("candidate_id")
        ):
            errors.append("Delivery Manifest candidate does not match the Delivery Decision")
        locked = decision.get("locked_exclusions")
        if isinstance(locked, list) and not set(locked).issubset(set(excluded)):
            errors.append("Delivery Manifest omits Owner-locked exclusions")
    if isinstance(status, dict):
        canonical = status.get("canonical_candidate", {})
        status_candidate = (
            canonical.get("candidate_id"), canonical.get("candidate_hash")
        ) if isinstance(canonical, dict) else None
        if candidate is None or candidate != status_candidate:
            errors.append("Delivery Manifest candidate does not match authoritative status")
        gates = status.get("phase_gates", {})
        if not isinstance(gates, dict) or gates.get("DELIVERY_READY") != "DELIVERY_READY":
            errors.append("Delivery Manifest requires current DELIVERY_READY")
        agent_fields = policy.get("agent_delivery_manifest_fields", []) if isinstance(policy, dict) else []
        agent_delivery, agent_errors = closed_record(
            data.get("agent_delivery"), agent_fields, "Delivery Manifest agent_delivery"
        )
        errors.extend(agent_errors)
        if status.get("status_schema_version") == "2.8.0":
            if agent_delivery.get("state") != "BOUND":
                errors.append("Agent-native Delivery Manifest requires BOUND Agent evidence")
            certification_reference = agent_delivery.get("runtime_certification_reference")
            if data.get("runtime_certification") != certification_reference:
                errors.append("Delivery Manifest Runtime Certification reference mismatch")
            certification_path = PROJECT_VALIDATOR.resolve_security_reference(
                lc, certification_reference
            )
            if certification_path is None:
                errors.append("Agent-native Runtime Certification is missing or outside .lccoding")
                certification = {}
            else:
                certification, certification_errors = parse_agent_certification(
                    certification_path
                )
                errors.extend(certification_errors)
                certification, certification_shape_errors = closed_record(
                    certification,
                    policy.get("agent_delivery_certification_fields", []),
                    "Runtime Certification Agent Delivery evidence",
                )
                errors.extend(certification_shape_errors)
                if agent_delivery.get("runtime_certification_hash") != file_hash(certification_path):
                    errors.append("Runtime Certification hash mismatch")
            expected_certification, certification_identity_errors = expected_agent_certification(
                lc, status
            )
            errors.extend(certification_identity_errors)
            if certification != expected_certification:
                errors.append("Runtime Certification Agent identity/evidence mismatch")
            for field in policy.get("agent_delivery_certification_fields", []):
                if agent_delivery.get(field) != certification.get(field):
                    errors.append("Delivery Manifest disagrees with Runtime Certification: " + field)
            if isinstance(decision, dict):
                if agent_delivery.get("delivery_decision_id") != decision.get("delivery_decision_id"):
                    errors.append("Agent Delivery evidence decision ID mismatch")
                if agent_delivery.get("delivery_decision_hash") != file_hash(decision_path):
                    errors.append("Agent Delivery evidence decision hash mismatch")
            product_assets = agent_delivery.get("approved_product_assets")
            runtime_assets = agent_delivery.get("approved_runtime_assets")
            if not unique_string_list(product_assets, allow_empty=True) or not unique_string_list(runtime_assets, allow_empty=True):
                errors.append("approved Product/Runtime assets must be closed unique lists")
                product_assets = []; runtime_assets = []
            if set(product_assets) & set(runtime_assets):
                errors.append("approved Product and Runtime assets must be disjoint")
            approved = set(product_assets) | set(runtime_assets)
            if approved != set(package_hashes if isinstance(package_hashes, dict) else {}):
                errors.append("approved Product/Runtime assets must exactly cover package_hashes")
            if approved != set(included):
                errors.append("approved Product/Runtime assets must exactly equal included assets")
            if agent_delivery.get("result") != "PASS":
                errors.append("Agent Delivery evidence result must be PASS")
        elif agent_delivery != not_applicable_agent_delivery(agent_fields):
            errors.append("legacy Delivery requires exact NOT_APPLICABLE Agent evidence")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    args = parser.parse_args()
    errors = validate_manifest(args.manifest)
    if errors:
        print("FAIL")
        print("\n".join(errors).encode("ascii", "backslashreplace").decode("ascii"))
        raise SystemExit(1)
    print("PASS")


if __name__ == "__main__":
    main()
