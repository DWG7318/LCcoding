#!/usr/bin/env python3
"""Validate exact 3.0 browser and 4.0 route-faithful user-journey evidence."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import zlib


SUMMARY_FIELDS = {
    "state", "candidate_id", "candidate_hash", "coverage_state",
    "acceptance_environment_state", "current_round", "complete_round_count",
    "required_journey_count", "passed_journey_count", "failed_journey_count",
    "not_applicable_journey_count", "open_defect_ids",
    "fixed_verified_defect_ids", "exempted_defect_ids", "deferred_defect_ids",
    "reopened_defect_ids", "acceptance_record_reference", "defect_log_reference",
    "owner_result",
}
ID_LIST_FIELDS = (
    "open_defect_ids", "fixed_verified_defect_ids", "exempted_defect_ids",
    "deferred_defect_ids", "reopened_defect_ids",
)
COUNT_FIELDS = (
    "current_round", "complete_round_count", "required_journey_count",
    "passed_journey_count", "failed_journey_count", "not_applicable_journey_count",
)
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9_.-]{0,127}$")
JOURNEY_ID_RE = re.compile(r"^JOURNEY-[0-9]{3,}$")
STEP_ID_RE = re.compile(r"^STEP-[0-9]{3,}$")
DEFECT_STATES = {
    "OPEN", "FIXED_VERIFIED", "OWNER_EXEMPTED", "DEFERRED", "MERGED_INTO", "REOPENED",
}
ROUTE_KINDS = {"DIRECT_PRODUCT", "PERSONAL_AGENT", "SERVICE_CENTER"}
ROUTE_ALLOWED_EVIDENCE_KINDS = {
    "DIRECT_PRODUCT": {"SCREENSHOT"},
    "PERSONAL_AGENT": {
        "HUMAN_GOAL_MESSAGE", "AGENT_IDENTITY", "REQUEST_MESSAGE", "TASK_TRANSITION",
        "AUTHORIZATION_DECISION", "RESULT_ARTIFACT", "PLATFORM_EFFECT", "AGENT_RESPONSE",
        "AUDIT_EVENT", "RESULT_DELIVERY",
    },
    "SERVICE_CENTER": {
        "USER_REQUEST", "SERVICE_ACTOR_IDENTITY", "DELEGATION_BASIS", "ASSISTED_ACTION",
        "AUTHORIZATION_DECISION", "PLATFORM_EFFECT", "USER_COMMUNICATION", "AUDIT_EVENT",
        "RESULT_DELIVERY",
    },
}
ROUTE_ENTRY_KINDS = {
    "DIRECT_PRODUCT": {"SCREENSHOT"},
    "PERSONAL_AGENT": {"HUMAN_GOAL_MESSAGE", "REQUEST_MESSAGE"},
    "SERVICE_CENTER": {"USER_REQUEST"},
}
EVIDENCE_RECORD_FIELDS = {
    "record_role", "evidence_schema_version", "evidence_id", "evidence_kind",
    "candidate_id", "candidate_hash", "round", "journey_id", "route_id", "step_id",
    "actor_id", "authority_action_id", "authority_resource_id", "delegation_basis_id",
    "event_or_result",
}
EXEMPTION_RECORD_FIELDS = {
    "record_role", "evidence_schema_version", "evidence_id", "defect_id",
    "candidate_id", "candidate_hash", "round", "route_id", "authority", "impact",
    "recovery_condition", "decision",
}
PRIORITY_EXCEPTION_FIELDS = {
    "record_role", "evidence_schema_version", "evidence_id", "candidate_id",
    "candidate_hash", "earlier_defect_id", "earlier_repair_sequence", "earlier_layer",
    "later_defect_id", "later_repair_sequence", "later_layer", "authority", "rationale",
    "decision",
}
KIND_PAYLOAD_FIELDS = {
    "HUMAN_GOAL_MESSAGE": {"message_id", "direction", "content"},
    "REQUEST_MESSAGE": {"message_id", "direction", "content"},
    "USER_REQUEST": {"message_id", "direction", "content"},
    "AGENT_RESPONSE": {"message_id", "direction", "content"},
    "USER_COMMUNICATION": {"message_id", "direction", "content", "delivery_result"},
    "AGENT_IDENTITY": {"subject_id", "verified_by", "result"},
    "SERVICE_ACTOR_IDENTITY": {"subject_id", "verified_by", "result"},
    "TASK_TRANSITION": {"task_id", "from_state", "to_state"},
    "AUTHORIZATION_DECISION": {"decision_id", "decision", "scope"},
    "RESULT_ARTIFACT": {"artifact_id", "artifact_reference", "result"},
    "PLATFORM_EFFECT": {"effect_id", "before_state", "after_state"},
    "AUDIT_EVENT": {"audit_event_id", "event", "result"},
    "RESULT_DELIVERY": {"delivery_id", "recipient_id", "result"},
    "DELEGATION_BASIS": {"delegation_basis_id", "delegated_by", "scope"},
    "ASSISTED_ACTION": {"action_event_id", "action", "result"},
}
VIEWPORT_RE = re.compile(r"^[1-9][0-9]*x[1-9][0-9]*@[0-9]+(?:\.[0-9]+)?$")
EXACT_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
DEFECT_LAYERS_400 = {
    "USER_SERVICE_BOUNDARY", "WORKFLOW_ORCHESTRATION", "BACKEND_CORE",
}
BOUNDARY_SURFACES_BY_ROUTE = {
    "DIRECT_PRODUCT": {"UI"},
    "PERSONAL_AGENT": {"UI", "AGENT_SERVICE"},
    "SERVICE_CENTER": {"UI", "ASSISTED_SERVICE"},
}
REPAIR_PRIORITY_400 = (
    "USER_SERVICE_BOUNDARY -> WORKFLOW_ORCHESTRATION -> BACKEND_CORE"
)
DEFECT_LAYER_ORDER = {
    "USER_SERVICE_BOUNDARY": 0,
    "WORKFLOW_ORCHESTRATION": 1,
    "BACKEND_CORE": 2,
}
IDENTITY_SUCCESS_RESULTS = {"AUTHENTICATED", "VERIFIED", "MATCHED"}
ASSISTED_ACTION_SUCCESS_RESULTS = {"PERFORMED", "SUCCEEDED"}
USER_COMMUNICATION_SUCCESS_RESULTS = {"DELIVERED", "ACKNOWLEDGED"}
AUTHORIZATION_SUCCESS_RESULTS = {"ALLOW", "APPROVED"}

_VERIFICATION_VALIDATOR_PATH = Path(__file__).with_name("validate_verification.py")
_VERIFICATION_SPEC = importlib.util.spec_from_file_location(
    "lccoding_validate_verification", _VERIFICATION_VALIDATOR_PATH
)
_VERIFICATION_VALIDATOR = importlib.util.module_from_spec(_VERIFICATION_SPEC)
_VERIFICATION_SPEC.loader.exec_module(_VERIFICATION_VALIDATOR)


def _is_nonnegative_integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _lc_root(project_root: Path) -> Path:
    root = Path(project_root)
    return root if root.name == ".lccoding" else root / ".lccoding"


def _safe_reference(lc: Path, reference, *, screenshot=False):
    text = str(reference or "").strip().replace("\\", "/")
    prefix = ".lccoding/evidence/real-user-journey/" if screenshot else ""
    if not text or text == "NOT_APPLICABLE" or "://" in text or Path(text).is_absolute():
        return None
    if screenshot:
        if not text.startswith(prefix):
            return None
        relative = Path(text[len(".lccoding/"):])
    else:
        relative = Path(text)
    if any(part in {"", ".", ".."} or ":" in part for part in relative.parts):
        return None
    candidate = lc
    try:
        for part in relative.parts:
            candidate = candidate / part
            if candidate.is_symlink():
                return None
        resolved = candidate.resolve(strict=True)
        if not resolved.is_file() or not resolved.is_relative_to(lc.resolve(strict=True)):
            return None
        return resolved
    except (OSError, RuntimeError, ValueError):
        return None


def _read_markdown(path: Path):
    try:
        return path.read_bytes().decode("utf-8"), []
    except (OSError, UnicodeError) as error:
        return "", [f"cannot read journey Markdown: {error}"]


def _read_json(path: Path):
    try:
        return json.loads(
            path.read_bytes().decode("utf-8"),
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError("non-finite JSON number: " + value)
            ),
        ), []
    except (OSError, UnicodeError, ValueError) as error:
        return None, [f"cannot read journey JSON: {error}"]


def _reject_duplicate_json_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _meaningful(value):
    return isinstance(value, str) and bool(value.strip()) and value.strip().upper() not in {
        "NONE", "NOT_APPLICABLE", "PENDING", "TBD", "TODO", "UNKNOWN",
    }


def _split_exact(value, count):
    parts = [part.strip() for part in str(value or "").split(" / ")]
    return parts if len(parts) == count else []


def _markdown_fields(text: str):
    fields = {}
    errors = []
    for line in text.splitlines():
        match = re.match(r"^- ([^:|]+):\s*(.*)$", line)
        if not match:
            continue
        key, value = match.group(1).strip(), match.group(2).strip()
        if key in fields:
            errors.append("duplicate Markdown field: " + key)
        else:
            fields[key] = value
    return fields, errors


def _table_rows(text: str, first_header: str):
    lines = text.splitlines()
    tables = []
    for index, line in enumerate(lines[:-1]):
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or cells[0] != first_header:
            continue
        separator = [cell.strip() for cell in lines[index + 1].strip().strip("|").split("|")]
        if len(separator) != len(cells) or any(not re.fullmatch(r":?-{3,}:?", cell) for cell in separator):
            return [], [f"{first_header} table separator is malformed"]
        rows = []
        for row_line in lines[index + 2:]:
            if not row_line.startswith("|"):
                break
            values = [cell.strip() for cell in row_line.strip().strip("|").split("|")]
            if len(values) != len(cells):
                return [], [f"{first_header} table row has wrong column count"]
            rows.append(dict(zip(cells, values)))
        tables.append(rows)
    if len(tables) != 1:
        return [], [f"{first_header} requires exactly one table"]
    return tables[0], []


def _rows_with_header_prefix(text: str, prefix: tuple[str, ...], label: str):
    lines = text.splitlines()
    matches = []
    for index, line in enumerate(lines[:-1]):
        if not line.startswith("|"):
            continue
        headers = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if tuple(headers[:len(prefix)]) != prefix:
            continue
        separator = [cell.strip() for cell in lines[index + 1].strip().strip("|").split("|")]
        if len(separator) != len(headers) or any(not re.fullmatch(r":?-{3,}:?", cell) for cell in separator):
            return [], [label + " table separator is malformed"]
        rows = []
        for row_line in lines[index + 2:]:
            if not row_line.startswith("|"):
                break
            cells = [cell.strip() for cell in row_line.strip().strip("|").split("|")]
            if len(cells) != len(headers):
                return [], [label + " table row has wrong column count"]
            rows.append(dict(zip(headers, cells)))
        matches.append(rows)
    if len(matches) != 1:
        return [], [label + " requires exactly one table"]
    return matches[0], []


def validate_status_summary(status: dict) -> list[str]:
    errors = []
    if not isinstance(status, dict):
        return ["authoritative status must be an object"]
    summary = status.get("real_user_journey_acceptance")
    if not isinstance(summary, dict):
        return ["real_user_journey_acceptance must be a closed object"]
    missing = SUMMARY_FIELDS - set(summary)
    unknown = set(summary) - SUMMARY_FIELDS
    if missing:
        errors.append("real_user_journey_acceptance missing fields " + ", ".join(sorted(missing)))
    if unknown:
        errors.append("real_user_journey_acceptance unknown fields " + ", ".join(sorted(unknown)))
    counts_valid = all(_is_nonnegative_integer(summary.get(field)) for field in COUNT_FIELDS)
    for field in COUNT_FIELDS:
        if not _is_nonnegative_integer(summary.get(field)):
            errors.append(field + " must be a non-negative integer")
    for field in ID_LIST_FIELDS:
        value = summary.get(field)
        if not isinstance(value, list) or any(
            not isinstance(item, int) or isinstance(item, bool) or item < 40001 for item in value
        ) or value != sorted(set(value)):
            errors.append(field + " must contain unique increasing defect IDs from 40001")
    candidate = status.get("canonical_candidate")
    if not isinstance(candidate, dict):
        errors.append("canonical candidate identity is missing")
    elif summary.get("state") != "UNPROVED" and (
        summary.get("candidate_id") != candidate.get("candidate_id")
        or summary.get("candidate_hash") != candidate.get("candidate_hash")
        or not HASH_RE.fullmatch(str(summary.get("candidate_hash", "")))
    ):
        errors.append("journey candidate identity disagrees with canonical candidate identity")
    if summary.get("state") == "REAL_USER_JOURNEY_ACCEPTED":
        phase_gates = status.get("phase_gates")
        if (
            summary.get("coverage_state") != "COMPLETE"
            or summary.get("acceptance_environment_state") != "VERIFIED"
            or summary.get("failed_journey_count") != 0
            or summary.get("open_defect_ids")
            or summary.get("deferred_defect_ids")
            or summary.get("reopened_defect_ids")
            or summary.get("owner_result") != "REAL_USER_JOURNEY_ACCEPTED"
            or not counts_valid
            or (
                summary.get("passed_journey_count")
                + summary.get("not_applicable_journey_count")
                != summary.get("required_journey_count")
            )
        ):
            errors.append("accepted journey state requires complete coverage and no open blocking defects")
        if (
            not isinstance(phase_gates, dict)
            or phase_gates.get("REAL_USER_JOURNEY_ACCEPTED") != "REAL_USER_JOURNEY_ACCEPTED"
        ):
            errors.append("accepted journey state disagrees with REAL_USER_JOURNEY_ACCEPTED gate")
    return errors


def _validate_acceptance_record_300(project_root: Path, status: dict) -> list[str]:
    errors = []
    summary = status.get("real_user_journey_acceptance", {})
    if not isinstance(summary, dict) or summary.get("state") == "UNPROVED":
        return errors
    lc = _lc_root(project_root)
    path = _safe_reference(lc, summary.get("acceptance_record_reference"))
    if path is None:
        return ["journey acceptance record reference is missing, unsafe, or unreadable"]
    text, read_errors = _read_markdown(path)
    errors.extend(read_errors)
    fields, field_errors = _markdown_fields(text)
    errors.extend(field_errors)
    if not SAFE_ID_RE.fullmatch(fields.get("Acceptance ID", "")):
        errors.append("Acceptance ID is missing or malformed")
    if (
        fields.get("Candidate ID") != summary.get("candidate_id")
        or fields.get("Candidate SHA-256") != summary.get("candidate_hash")
    ):
        errors.append("acceptance record candidate identity disagrees with status")

    journeys, table_errors = _table_rows(text, "Journey ID")
    errors.extend(table_errors)
    journey_ids = []
    for row in journeys:
        journey_id = row.get("Journey ID", "")
        if not JOURNEY_ID_RE.fullmatch(journey_id):
            errors.append("Journey ID is missing or malformed")
        journey_ids.append(journey_id)
        for token in re.split(r"\s*,\s*", row.get("Ordered visible actions", "")):
            if not STEP_ID_RE.fullmatch(token):
                errors.append("Step ID is missing or malformed")
        if row.get("Applicability") not in {"REQUIRED", "NOT_APPLICABLE"}:
            errors.append("journey applicability is invalid")
    if len(journey_ids) != len(set(journey_ids)):
        errors.append("duplicate Journey ID")

    rounds, table_errors = _rows_with_header_prefix(
        text, ("Round", "Candidate ID / SHA-256"), "acceptance rounds"
    )
    errors.extend(table_errors)
    round_numbers = []
    for row in rounds:
        try:
            number = int(row.get("Round", ""))
        except ValueError:
            number = -1
        round_numbers.append(number)
        if number > 1 and row.get("Started from home entry") != "YES":
            errors.append("every post-repair round must restart from home entry")
        identity = row.get("Candidate ID / SHA-256", "").split(" / ")
        if identity != [summary.get("candidate_id"), summary.get("candidate_hash")]:
            errors.append("acceptance round candidate identity disagrees with status")
    if round_numbers != sorted(set(round_numbers)) or any(number < 1 for number in round_numbers):
        errors.append("acceptance round numbers must be unique and increasing")
    if summary.get("current_round") not in round_numbers:
        errors.append("current acceptance round is absent from the record")

    evidence, evidence_errors = _evidence_rows(text)
    errors.extend(evidence_errors)
    used_paths = set()
    for row in evidence:
        try:
            number = int(row.get("Round", ""))
        except ValueError:
            number = -1
        if not JOURNEY_ID_RE.fullmatch(row.get("Journey ID", "")):
            errors.append("evidence Journey ID is missing or malformed")
        if not STEP_ID_RE.fullmatch(row.get("Step ID", "")):
            errors.append("evidence Step ID is missing or malformed")
        screenshot = row.get("Screenshot path")
        screenshot_path = _safe_reference(lc, screenshot, screenshot=True)
        if screenshot_path is None:
            errors.append("screenshot path is outside the journey evidence root or unreadable")
        else:
            digest = row.get("Screenshot SHA-256", "")
            actual = hashlib.sha256(screenshot_path.read_bytes()).hexdigest()
            if not HASH_RE.fullmatch(digest) or digest != actual:
                errors.append("screenshot digest does not match visible evidence bytes")
        if row.get("Result") == "PASS":
            if screenshot in used_paths:
                errors.append("current-round PASS cannot reuse a prior-round screenshot")
            used_paths.add(screenshot)
        if number == summary.get("current_round") and row.get("Result") == "PASS" and screenshot_path is None:
            errors.append("current-round PASS lacks readable screenshot evidence")
    return errors


def _evidence_rows(text: str):
    return _rows_with_header_prefix(text, ("Round", "Journey ID"), "evidence digest")


def _validate_defect_log_300(project_root: Path, status: dict) -> list[str]:
    errors = []
    summary = status.get("real_user_journey_acceptance", {})
    if not isinstance(summary, dict) or summary.get("state") == "UNPROVED":
        return errors
    lc = _lc_root(project_root)
    path = _safe_reference(lc, summary.get("defect_log_reference"))
    if path is None:
        return ["journey defect log reference is missing, unsafe, or unreadable"]
    text, read_errors = _read_markdown(path)
    errors.extend(read_errors)
    rows, table_errors = _rows_with_header_prefix(
        text,
        ("Defect ID", "Discovery time / candidate / round / Journey / Step"),
        "defect register",
    )
    errors.extend(table_errors)
    ids = []
    states = {state: [] for state in DEFECT_STATES}
    for row in rows:
        try:
            defect_id = int(row.get("Defect ID", ""))
        except ValueError:
            defect_id = -1
        ids.append(defect_id)
        state = row.get("State")
        if state not in DEFECT_STATES:
            errors.append("defect state is invalid")
        else:
            states[state].append(defect_id)
        discovery = row.get("Discovery time / candidate / round / Journey / Step", "").split(" / ")
        try:
            discovery_round = int(discovery[2])
        except (IndexError, ValueError):
            discovery_round = -1
        try:
            retest_round = int(row.get("Retest round", ""))
        except ValueError:
            retest_round = -1
        if state == "FIXED_VERIFIED" and (
            row.get("Correction identity / engineering re-verification") in {"", "NOT_APPLICABLE"}
            or retest_round <= discovery_round
        ):
            errors.append("fixed defect requires correction identity and later-round retest evidence")
        if state == "OWNER_EXEMPTED":
            parts = [part.strip() for part in row.get("Exemption authority / impact / recovery", "").split(" / ")]
            if len(parts) != 3 or any(not part or part == "NOT_APPLICABLE" for part in parts):
                errors.append("Owner exemption requires authority, user impact, and recovery condition")
    if ids != sorted(set(ids)) or any(defect_id < 40001 for defect_id in ids):
        errors.append("defect IDs must be unique, increasing, unrecycled, and start at 40001")
    expected = {
        "open_defect_ids": states["OPEN"],
        "fixed_verified_defect_ids": states["FIXED_VERIFIED"],
        "exempted_defect_ids": states["OWNER_EXEMPTED"],
        "deferred_defect_ids": states["DEFERRED"],
        "reopened_defect_ids": states["REOPENED"],
    }
    for field, value in expected.items():
        if summary.get(field) != value:
            errors.append(field + " disagrees with the append-only defect register")
    return errors


def _required_route_map(project_root: Path, status: dict):
    lc = _lc_root(project_root)
    path = _safe_reference(lc, "SERVICE-ROUTE-MAP.json")
    if path is None:
        return {}, None, ["4.0 journey acceptance requires a readable adopted Service Route Map"]
    record, read_errors = _read_json(path)
    if read_errors:
        return {}, path, ["4.0 journey acceptance requires a readable adopted Service Route Map"] + read_errors
    errors = []
    if not isinstance(record, dict):
        return {}, path, ["Service Route Map must be an object"]
    if record.get("state") != "ADOPTED" or status.get("service_route_map") != "ADOPTED":
        errors.append("4.0 journey acceptance requires an ADOPTED Service Route Map")
        return {}, path, errors
    if not SAFE_ID_RE.fullmatch(str(record.get("map_id") or "")):
        errors.append("adopted Service Route Map map_id is malformed")
    if record.get("project_id") != status.get("project_id"):
        errors.append("adopted Service Route Map project identity disagrees with status")
    required = {}
    journeys = record.get("journeys")
    if not isinstance(journeys, list):
        return {}, path, errors + ["adopted Service Route Map journeys must be an array"]
    for journey in journeys:
        if not isinstance(journey, dict):
            errors.append("adopted Service Route Map journey member must be an object")
            continue
        if journey.get("delivery_state") != "DELIVERED":
            continue
        journey_id = str(journey.get("journey_id") or "")
        if not SAFE_ID_RE.fullmatch(journey_id):
            errors.append("adopted Service Route Map journey_id is malformed")
            continue
        routes = journey.get("routes")
        if not isinstance(routes, list):
            errors.append("adopted Service Route Map routes must be an array")
            continue
        for route in routes:
            if not isinstance(route, dict):
                errors.append("adopted Service Route Map route member must be an object")
                continue
            if route.get("support_state") != "REQUIRED" or route.get("delivery_state") != "DELIVERED":
                continue
            route_id = str(route.get("route_id") or "")
            route_kind = route.get("route_kind")
            authority = route.get("authority")
            consent = route.get("consent")
            acceptance_ids = route.get("acceptance_evidence_ids")
            audit_ids = route.get("audit_event_ids")
            if not SAFE_ID_RE.fullmatch(route_id):
                errors.append("adopted Service Route Map route_id is malformed")
                continue
            if route_kind not in ROUTE_KINDS:
                errors.append("adopted Service Route Map route kind is malformed")
            if not isinstance(authority, dict):
                errors.append("adopted Service Route Map route authority must be an object")
                authority = {}
            if not isinstance(consent, dict):
                errors.append("adopted Service Route Map route consent must be an object")
                consent = {}
            if (
                not isinstance(acceptance_ids, list) or not acceptance_ids
                or any(not isinstance(item, str) or not SAFE_ID_RE.fullmatch(item) for item in acceptance_ids)
                or len(acceptance_ids) != len(set(acceptance_ids))
            ):
                errors.append("adopted route acceptance_evidence_ids must be a unique stable ID array")
                acceptance_ids = []
            if (
                not isinstance(audit_ids, list)
                or any(not isinstance(item, str) or not SAFE_ID_RE.fullmatch(item) for item in audit_ids)
                or len(audit_ids) != len(set(audit_ids))
            ):
                errors.append("adopted route audit_event_ids must be a unique stable ID array")
                audit_ids = []
            normalized = dict(route)
            normalized["authority"] = authority
            normalized["consent"] = consent
            normalized["acceptance_evidence_ids"] = acceptance_ids
            normalized["audit_event_ids"] = audit_ids
            key = (journey_id, route_id)
            if key in required:
                errors.append("adopted Service Route Map contains duplicate required route identity")
            required[key] = normalized
    if not required:
        errors.append("4.0 journey acceptance requires at least one required delivered route")
    return required, path, errors


def _parse_exact_citation(value, label):
    parts = _split_exact(value, 3)
    if (
        not parts or not SAFE_ID_RE.fullmatch(parts[0])
        or not EXACT_HASH_RE.fullmatch(parts[1])
    ):
        return None, [label + " requires exact evidence ID / sha256 / contained path"]
    return tuple(parts), []


def _resolve_exact_citation(lc, value, label):
    citation, errors = _parse_exact_citation(value, label)
    if citation is None:
        return None, None, errors
    path = _safe_reference(lc, citation[2])
    if path is None:
        return citation, None, errors + [label + " path is missing, unsafe, or unreadable"]
    actual = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != citation[1]:
        errors.append(label + " hash does not match resolved bytes")
    return citation, path, errors


def _canonical_run_start_hash(text):
    lines = text.splitlines(keepends=True)
    canonical = []
    matches = 0
    for line in lines:
        ending = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
        body = line[:-len(ending)] if ending else line
        if body.startswith("- Start Contract SHA-256:"):
            body = "- Start Contract SHA-256:"
            matches += 1
        canonical.append(body + ending)
    if matches != 1:
        return None
    return "sha256:" + hashlib.sha256("".join(canonical).encode("utf-8")).hexdigest()


def _run_starts(lc):
    starts = {}
    errors = []
    root = lc / "runs"
    if not root.is_dir():
        return starts, ["Task5 receipt join requires the Run evidence directory"]
    for path in root.rglob("*.md"):
        if path.is_symlink() or not path.is_file():
            continue
        text, read_errors = _read_markdown(path)
        errors.extend(read_errors)
        fields, field_errors = _markdown_fields(text)
        errors.extend(field_errors)
        if fields.get("Artifact role") != "RUN_START_CONTRACT":
            continue
        run_id = fields.get("Run ID")
        if not SAFE_ID_RE.fullmatch(str(run_id or "")):
            errors.append("Task5 Run start has malformed Run ID")
            continue
        starts.setdefault(run_id, []).append((path, text, fields))
    return starts, errors


def _bound_route_evidence(value):
    parts = [part.strip() for part in str(value or "").split("~")]
    if (
        len(parts) != 4 or not SAFE_ID_RE.fullmatch(parts[0])
        or not HASH_RE.fullmatch(parts[1]) or not SAFE_ID_RE.fullmatch(parts[2])
        or not SAFE_ID_RE.fullmatch(parts[3])
    ):
        return None
    return tuple(parts)


def _validate_task5_final_and_d3(lc, row, route, receipt, receipt_id):
    errors = []
    labeled = {}
    for item in str(row.get("Task5 Final Verification / D3 citations") or "").split(";"):
        label, separator, value = item.strip().partition(":")
        if not separator or label not in {"FINAL", "D3"} or label in labeled:
            errors.append("Task5 Final Verification / D3 citations are malformed")
            continue
        labeled[label] = value.strip()
    if set(labeled) != {"FINAL", "D3"}:
        errors.append("Task5 Final Verification / D3 citations must resolve both artifacts")
        return errors
    resolved = {}
    for label in ("FINAL", "D3"):
        reference, path, citation_errors = _resolve_exact_citation(
            lc, labeled[label], "Task5 " + label + " artifact"
        )
        errors.extend(citation_errors)
        if reference is not None and path is not None:
            resolved[label] = (reference, path)
    if set(resolved) != {"FINAL", "D3"}:
        return errors
    final_reference, final_path = resolved["FINAL"]
    d3_reference, d3_path = resolved["D3"]
    if final_path == d3_path or final_reference[0] == d3_reference[0]:
        errors.append("Task5 Final Verification and D3 must be distinct exact artifacts")

    final_text, read_errors = _read_markdown(final_path)
    errors.extend(read_errors)
    final, field_errors = _markdown_fields(final_text)
    errors.extend(field_errors)
    candidate = _split_exact(receipt.get("Candidate ID / hash"), 2)
    authority = route.get("authority") if isinstance(route.get("authority"), dict) else {}
    final_expected = {
        "Artifact role": "FINAL_FEATURE_VERIFICATION",
        "Verification ID": final_reference[0],
        "Integration candidate ID / exact hash": receipt.get("Candidate ID / hash"),
        "Integration Route ID": route.get("route_id"),
        "Service Route ID": route.get("route_id"),
        "Human-observable outcome": route.get("human_observable_outcome"),
        "Final verdict": "PASS",
    }
    if any(final.get(field) != value for field, value in final_expected.items()):
        errors.append("Task5 Final Feature Verification does not join the adopted route result")
    terminal = {}
    for item in str(final.get("D3 / Loop Owner Acceptance evidence") or "").split(";"):
        label, separator, value = item.strip().partition(":")
        if separator and label in {"D3", "OWNER"} and label not in terminal:
            terminal[label] = _bound_route_evidence(value)
    expected_prefix = (
        candidate[0] if candidate else None,
        candidate[1].removeprefix("sha256:") if candidate else None,
        route.get("route_id"),
    )
    if (
        set(terminal) != {"D3", "OWNER"} or None in terminal.values()
        or terminal.get("D3") != expected_prefix + (d3_reference[0],)
        or terminal.get("OWNER") != expected_prefix + (receipt_id,)
    ):
        errors.append("Task5 Final Feature Verification terminal evidence join is invalid")

    d3, d3_errors = _read_json(d3_path)
    errors.extend(d3_errors)
    if not isinstance(d3, dict):
        errors.append("actual Task5 D3 artifact must be a strict verification receipt")
        return errors
    errors.extend(
        "actual Task5 D3 artifact violates canonical verification contract: " + error
        for error in _VERIFICATION_VALIDATOR.validate_receipt(d3)
    )
    d3_expected = {
        "receipt_id": d3_reference[0],
        "layer": "D3",
        "claim_id": route.get("capability_implementation_id"),
        "candidate_id": candidate[0] if candidate else None,
        "candidate_hash": candidate[1].removeprefix("sha256:") if candidate else None,
        "authority": authority.get("action_id"),
        "verdict": "PASS",
    }
    if any(d3.get(field) != value for field, value in d3_expected.items()):
        errors.append("actual Task5 D3 artifact does not join candidate, route, authority, and PASS")
    coverage = d3.get("coverage")
    if not isinstance(coverage, list) or route.get("route_id") not in coverage:
        errors.append("actual Task5 D3 artifact coverage does not join the adopted route")
    if receipt.get("D3 Receipt") != d3_reference[0]:
        errors.append("receipt D3 identity disagrees with the actual Task5 D3 artifact")
    return errors


def _validate_task5_receipts(lc, status, coverage, required_routes):
    errors = []
    indexed = status.get("loop_owner_acceptances")
    if (
        not isinstance(indexed, list)
        or any(not isinstance(item, str) or not SAFE_ID_RE.fullmatch(item) for item in indexed)
        or len(indexed) != len(set(indexed))
    ):
        errors.append("Task5 authoritative acceptance index must contain unique stable IDs")
        indexed_set = set()
    else:
        indexed_set = set(indexed)
    starts, start_errors = _run_starts(lc)
    errors.extend(start_errors)
    seen_ids = set()
    seen_paths = set()
    summary = status.get("real_user_journey_acceptance")
    summary = summary if isinstance(summary, dict) else {}
    candidate = str(summary.get("candidate_id")) + " / sha256:" + str(summary.get("candidate_hash"))
    for key, route in required_routes.items():
        row = coverage.get(key)
        if not isinstance(row, dict):
            continue
        raw = row.get("Task5 acceptance receipt citations")
        values = [item.strip() for item in str(raw or "").split(";") if item.strip()]
        resolved_ids = []
        for value in values:
            reference, path, item_errors = _resolve_exact_citation(
                lc, value, "Task5 acceptance receipt"
            )
            errors.extend(item_errors)
            if reference is None:
                continue
            acceptance_id = reference[0]
            resolved_ids.append(acceptance_id)
            if acceptance_id in seen_ids or reference[2] in seen_paths:
                errors.append("Task5 acceptance receipts must have unique IDs and paths")
            seen_ids.add(acceptance_id)
            seen_paths.add(reference[2])
            if acceptance_id not in indexed_set:
                errors.append("Task5 receipt is absent from the authoritative acceptance index")
            if path is None:
                continue
            try:
                relative = path.relative_to(lc.resolve(strict=True))
            except (OSError, ValueError):
                relative = Path()
            if not relative.parts or relative.parts[0] != "reviews":
                errors.append("Task5 acceptance receipt must resolve inside reviews")
            receipt_text, read_errors = _read_markdown(path)
            errors.extend(read_errors)
            receipt, field_errors = _markdown_fields(receipt_text)
            errors.extend(field_errors)
            authority = route.get("authority", {})
            expected = {
                "Artifact role": "LOOP_OWNER_ACCEPTANCE_RECEIPT",
                "Acceptance ID": acceptance_id,
                "Status schema version": "4.0.0",
                "LCCoding phase scope": "REAL_PRODUCT_INTEGRATION",
                "Phase-owned objective": route.get("human_observable_outcome"),
                "Candidate ID / hash": candidate,
                "Entry / role / account": " / ".join((
                    str(route.get("promised_entry")), str(route.get("actor_id")),
                    str(authority.get("resource_id")),
                )),
                "Calling phase gate remains independently evaluated": "YES",
                "Owner result": "LOOP_OWNER_ACCEPTED",
            }
            for field, expected_value in expected.items():
                if receipt.get(field) != expected_value:
                    if field == "Candidate ID / hash":
                        errors.append("Task5 receipt candidate join disagrees with current candidate")
                    else:
                        errors.append("Task5 receipt " + field + " join disagrees with adopted route")
            run_id = receipt.get("Run ID")
            d3 = receipt.get("D3 Receipt")
            run_d3 = _split_exact(row.get("Task5 Run ID / D3 Receipt"), 2)
            if run_d3 != [run_id, d3]:
                errors.append("Task5 receipt Run/D3 citation disagrees with resolved receipt")
            errors.extend(_validate_task5_final_and_d3(
                lc, row, route, receipt, acceptance_id
            ))
            steps = [item.strip() for item in str(receipt.get("Acceptance steps") or "").split(",") if item.strip()]
            required_steps = [
                route.get("route_id"), route.get("actor_id"), authority.get("action_id"),
                authority.get("resource_id"),
            ]
            if authority.get("delegation_basis_id") != "NOT_APPLICABLE":
                required_steps.append(authority.get("delegation_basis_id"))
            required_steps.extend((
                route.get("adapter_or_surface_id"),
                route.get("capability_implementation_id"), d3, acceptance_id,
            ))
            if any(item not in steps for item in required_steps):
                errors.append("Task5 receipt route/D3 join is absent from Acceptance steps")
            run_items = starts.get(run_id, []) if isinstance(run_id, str) else []
            if len(run_items) != 1:
                errors.append("Task5 receipt Run join must resolve exactly one Run start")
            else:
                _, run_text, run = run_items[0]
                canonical_hash = _canonical_run_start_hash(run_text)
                run_expected = {
                    "Artifact role": "RUN_START_CONTRACT",
                    "Start Contract ID": receipt.get("Run-start contract ID"),
                    "Start Contract SHA-256": receipt.get("Run-start contract SHA-256"),
                    "Run ID": run_id,
                    "Status schema version": "4.0.0",
                    "LCCoding phase scope": "REAL_PRODUCT_INTEGRATION",
                    "Phase-owned objective": route.get("human_observable_outcome"),
                    "Evidence return target in calling phase": receipt.get(
                        "Evidence return target in the calling phase"
                    ),
                    "Readiness result": "READY",
                    "Blocker evidence": "NONE",
                }
                if any(run.get(field) != value for field, value in run_expected.items()):
                    errors.append("Task5 receipt Run join disagrees with canonical Run start")
                route_baseline = _split_exact(
                    run.get("Service Route / Integration Baseline (REAL_PRODUCT_INTEGRATION only)"), 2
                )
                if not route_baseline or route_baseline[0] != route.get("route_id"):
                    errors.append("Task5 receipt Run join disagrees with adopted route")
                if canonical_hash is None or run.get("Start Contract SHA-256") != canonical_hash:
                    errors.append("Task5 canonical Run start hash is invalid")
        adopted_ids = route.get("acceptance_evidence_ids", [])
        if len(resolved_ids) != len(set(resolved_ids)) or set(resolved_ids) != set(adopted_ids):
            errors.append("Task5 receipt citations must exactly cover adopted acceptance evidence IDs")
    return errors


def _validate_route_coverage(text, required_routes):
    rows, errors = _rows_with_header_prefix(
        text, ("Journey ID", "Service Route ID"), "route-faithful journey coverage"
    )
    actual = {}
    for row in rows:
        journey_id = row.get("Journey ID")
        route_id = row.get("Service Route ID")
        key = (journey_id, route_id)
        if key in actual:
            errors.append("route-faithful journey coverage contains duplicate route identity")
        actual[key] = row
    if set(actual) != set(required_routes):
        errors.append("route-faithful journey coverage must exactly cover required delivered adopted routes")
    for key in set(actual) & set(required_routes):
        row = actual[key]
        route = required_routes[key]
        authority = route.get("authority") if isinstance(route.get("authority"), dict) else {}
        expected = {
            "Route kind": route.get("route_kind"),
            "Actor ID / kind": str(route.get("actor_id")) + " / " + str(route.get("actor_kind")),
            "Authority action / resource / delegation": " / ".join((
                str(authority.get("action_id")), str(authority.get("resource_id")),
                str(authority.get("delegation_basis_id")),
            )),
            "Actual external entry": route.get("promised_entry"),
            "Expected human-observable outcome": route.get("human_observable_outcome"),
            "Applicability": "REQUIRED",
        }
        for field, value in expected.items():
            if row.get(field) != value:
                errors.append(field + " disagrees with the adopted Service Route Map for " + str(key[1]))
        adopted_ids = route.get("acceptance_evidence_ids")
        adopted_ids = adopted_ids if isinstance(adopted_ids, list) else []
        cited_ids = [
            item.strip() for item in str(row.get("Adopted acceptance evidence IDs", "")).split(",")
            if item.strip()
        ]
        if len(cited_ids) != len(set(cited_ids)) or set(cited_ids) != set(adopted_ids):
            errors.append(
                "Adopted acceptance evidence IDs disagree with the adopted Service Route Map for "
                + str(key[1])
            )
    return actual, errors


def _parse_unattempted_dispositions(value):
    if value == "NONE":
        return {}, []
    dispositions = {}
    errors = []
    for item in str(value or "").split(";"):
        parts = _split_exact(item.strip(), 4)
        try:
            defect_id = int(parts[3]) if parts else -1
        except (TypeError, ValueError):
            defect_id = -1
        if (
            not parts or not SAFE_ID_RE.fullmatch(parts[0])
            or parts[1] not in {"DEPENDENCY_BLOCKED", "GLOBAL_BLOCKED"}
            or not SAFE_ID_RE.fullmatch(parts[2]) or defect_id < 40001
        ):
            errors.append("unattempted route disposition is malformed")
            continue
        if parts[0] in dispositions:
            errors.append("unattempted route dispositions contain duplicate routes")
        dispositions[parts[0]] = (parts[1], parts[2], defect_id)
    return dispositions, errors


def _validate_route_rounds(text, summary, required_routes):
    required_count = len(required_routes)
    required_route_ids = {key[1] for key in required_routes}
    rows, errors = _rows_with_header_prefix(
        text, ("Round", "Candidate ID / SHA-256"), "acceptance rounds"
    )
    by_number = {}
    complete_count = 0
    for row in rows:
        try:
            number = int(row.get("Round", ""))
        except (TypeError, ValueError):
            number = -1
        if number in by_number:
            errors.append("acceptance round numbers must be unique and increasing")
        candidate = _split_exact(row.get("Candidate ID / SHA-256"), 2)
        if (
            not candidate or not SAFE_ID_RE.fullmatch(candidate[0])
            or not HASH_RE.fullmatch(candidate[1])
        ):
            errors.append("acceptance round candidate identity is malformed")
            candidate = []
        attempted = [
            item.strip() for item in str(row.get("Attempted route IDs") or "").split(",")
            if item.strip()
        ]
        if not attempted or len(attempted) != len(set(attempted)) or any(
            not SAFE_ID_RE.fullmatch(item) for item in attempted
        ):
            errors.append("acceptance round attempted route IDs are malformed or duplicated")
        if any(item not in required_route_ids for item in attempted):
            errors.append("acceptance round attempts a route outside adopted coverage")
        dispositions, disposition_errors = _parse_unattempted_dispositions(
            row.get("Unattempted route dispositions")
        )
        errors.extend(disposition_errors)
        if set(dispositions) != required_route_ids - set(attempted):
            errors.append("every unattempted adopted route requires one exact blocking disposition")
        if row.get("Started from each attempted actual route entry") != "YES":
            errors.append("every attempted round must restart from each attempted actual route entry")
        counts = _split_exact(row.get("Required routes / passed / failed"), 3)
        try:
            required, passed, failed = [int(value) for value in counts]
        except (TypeError, ValueError):
            required, passed, failed = -1, -1, -1
            errors.append("acceptance round route counts are malformed")
        if min(required, passed, failed) < 0:
            errors.append("acceptance round route counts must be non-negative")
        if required != required_count:
            errors.append("acceptance round required route count disagrees with adopted map coverage")
        result = row.get("Result")
        if result not in {"PASS", "REWORK", "BLOCKED"}:
            errors.append("acceptance round result is invalid")
        if result == "PASS":
            complete_count += 1
            if passed != required_count or failed != 0 or len(attempted) != required_count:
                errors.append("complete acceptance round must pass every required delivered route")
        elif result in {"REWORK", "BLOCKED"}:
            if failed < 1:
                errors.append("REWORK/BLOCKED round requires at least one failed attempted route")
            if passed + failed != len(attempted):
                errors.append("attempted route counts must equal passed plus failed routes")
        raw_defects = str(row.get("Defect IDs") or "").strip()
        defects = []
        if raw_defects != "NONE":
            try:
                defects = [int(item.strip()) for item in raw_defects.split(",") if item.strip()]
            except ValueError:
                errors.append("acceptance round Defect IDs are malformed")
                defects = []
            if defects != sorted(set(defects)) or any(item < 40001 for item in defects):
                errors.append("acceptance round Defect IDs must be unique increasing IDs from 40001")
        if result in {"REWORK", "BLOCKED"} and not defects:
            errors.append("REWORK/BLOCKED round defects must identify actual defects")
        stored = dict(row)
        stored["_candidate"] = tuple(candidate) if candidate else None
        stored["_attempted"] = tuple(attempted)
        stored["_defects"] = tuple(defects)
        stored["_dispositions"] = dispositions
        stored["_counts"] = (required, passed, failed)
        by_number[number] = stored
    numbers = list(by_number)
    if numbers != sorted(set(numbers)) or any(number < 1 for number in numbers):
        errors.append("acceptance round numbers must be unique and increasing")
    current_round = summary.get("current_round")
    current_valid = _is_nonnegative_integer(current_round) and current_round in by_number
    if not current_valid:
        errors.append("current acceptance round is absent from the record")
    else:
        if current_round != max(by_number):
            errors.append("current acceptance round must be the latest recorded round")
        expected_candidate = (summary.get("candidate_id"), summary.get("candidate_hash"))
        if by_number[current_round].get("_candidate") != expected_candidate:
            errors.append("current acceptance round candidate identity disagrees with status")
    if summary.get("complete_round_count") != complete_count:
        errors.append("complete-round count disagrees with route-faithful round history")
    if summary.get("state") == "REAL_USER_JOURNEY_ACCEPTED" and (
        not current_valid or by_number[current_round].get("Result") != "PASS"
    ):
        errors.append("accepted journey state requires a complete current route-faithful round")
    return by_number, errors


def _screenshot_dimensions(data):
    """Return PNG dimensions only after validating a complete image stream."""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    position = 8
    chunks = []
    idat = []
    while position + 12 <= len(data):
        length = int.from_bytes(data[position:position + 4], "big")
        end = position + 12 + length
        if end > len(data):
            return None
        kind = data[position + 4:position + 8]
        payload = data[position + 8:position + 8 + length]
        crc = int.from_bytes(data[position + 8 + length:end], "big")
        if (
            len(kind) != 4
            or not all(65 <= byte <= 90 or 97 <= byte <= 122 for byte in kind)
            or zlib.crc32(kind + payload) & 0xFFFFFFFF != crc
        ):
            return None
        chunks.append((kind, payload))
        if kind == b"IDAT":
            idat.append(payload)
        position = end
        if kind == b"IEND":
            break
    if (
        position != len(data) or not chunks or chunks[0][0] != b"IHDR"
        or chunks[-1] != (b"IEND", b"")
        or sum(kind == b"IHDR" for kind, _ in chunks) != 1
        or sum(kind == b"IEND" for kind, _ in chunks) != 1
        or not idat
    ):
        return None
    ihdr = chunks[0][1]
    if len(ihdr) != 13:
        return None
    width = int.from_bytes(ihdr[0:4], "big")
    height = int.from_bytes(ihdr[4:8], "big")
    bit_depth, color_type, compression, filtering, interlace = ihdr[8:13]
    valid_depths = {
        0: {1, 2, 4, 8, 16}, 2: {8, 16}, 3: {1, 2, 4, 8},
        4: {8, 16}, 6: {8, 16},
    }
    if (
        width < 1 or height < 1 or bit_depth not in valid_depths.get(color_type, set())
        or compression != 0 or filtering != 0 or interlace != 0
    ):
        return None
    kinds = [kind for kind, _ in chunks]
    first_idat = kinds.index(b"IDAT")
    last_idat = len(kinds) - 1 - kinds[::-1].index(b"IDAT")
    if any(kind != b"IDAT" for kind in kinds[first_idat:last_idat + 1]):
        return None
    if color_type == 3 and b"PLTE" not in kinds[:first_idat]:
        return None
    known_critical = {b"IHDR", b"PLTE", b"IDAT", b"IEND"}
    if any(kind[0] & 0x20 == 0 and kind not in known_critical for kind in kinds):
        return None
    try:
        decoder = zlib.decompressobj()
        pixels = decoder.decompress(b"".join(idat)) + decoder.flush()
    except zlib.error:
        return None
    if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        return None
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
    row_bytes = (width * channels * bit_depth + 7) // 8
    stride = row_bytes + 1
    if len(pixels) != height * stride or any(
        pixels[offset] > 4 for offset in range(0, len(pixels), stride)
    ):
        return None
    return width, height


def _validate_screenshot(path, row):
    errors = []
    try:
        data = path.read_bytes()
    except OSError:
        return ["visible route step screenshot is unreadable"]
    dimensions = _screenshot_dimensions(data)
    if not dimensions or min(dimensions) <= 0:
        errors.append(
            "visible route step requires actual screenshot bytes as a structurally complete screenshot"
        )
    digest = row.get("Screenshot SHA-256")
    actual = hashlib.sha256(data).hexdigest()
    if not HASH_RE.fullmatch(str(digest or "")) or digest != actual:
        errors.append("screenshot digest does not match visible evidence bytes")
    return errors


def _validate_project_evidence(path, row, round_record, route):
    record, read_errors = _read_json(path)
    if read_errors or not isinstance(record, dict):
        return ["nonvisual project evidence is not strict structured evidence"] + read_errors
    errors = []
    missing = EVIDENCE_RECORD_FIELDS - set(record)
    unknown = set(record) - EVIDENCE_RECORD_FIELDS
    if missing:
        errors.append("nonvisual project evidence missing fields " + ", ".join(sorted(missing)))
    if unknown:
        errors.append("nonvisual project evidence unknown fields " + ", ".join(sorted(unknown)))
    if record.get("record_role") != "REAL_USER_JOURNEY_EVIDENCE":
        errors.append("nonvisual project evidence record role is invalid")
    if record.get("evidence_schema_version") != "4.0.0":
        errors.append("nonvisual project evidence schema is invalid")
    authority = route.get("authority") if isinstance(route.get("authority"), dict) else {}
    candidate = round_record.get("_candidate") if isinstance(round_record, dict) else None
    expected = {
        "evidence_id": row.get("Evidence ID"),
        "evidence_kind": row.get("Evidence kind"),
        "candidate_id": candidate[0] if candidate else None,
        "candidate_hash": candidate[1] if candidate else None,
        "round": row.get("_round_number"),
        "journey_id": row.get("Journey ID"),
        "route_id": row.get("Service Route ID"),
        "step_id": row.get("Step ID"),
        "actor_id": route.get("actor_id"),
        "authority_action_id": authority.get("action_id"),
        "authority_resource_id": authority.get("resource_id"),
        "delegation_basis_id": authority.get("delegation_basis_id"),
    }
    if any(record.get(field) != value for field, value in expected.items()):
        errors.append("nonvisual project evidence does not join exact candidate/route/round/step authority")
    kind = row.get("Evidence kind")
    payload = record.get("event_or_result")
    expected_payload = KIND_PAYLOAD_FIELDS.get(kind)
    if (
        not isinstance(payload, dict) or not expected_payload
        or set(payload) != expected_payload
        or any(
            str(value or "").strip().upper() in {"", "NONE", "NOT_APPLICABLE", "UNKNOWN"}
            for value in payload.values()
        )
    ):
        errors.append("nonvisual project evidence lacks a kind-specific event/result payload")
        return errors
    if kind in {"AGENT_IDENTITY", "SERVICE_ACTOR_IDENTITY"} and payload.get("subject_id") != route.get("actor_id"):
        errors.append("identity evidence does not identify the adopted route actor")
    if kind in {"AGENT_IDENTITY", "SERVICE_ACTOR_IDENTITY"} and str(
        payload.get("result") or ""
    ).upper() not in IDENTITY_SUCCESS_RESULTS:
        errors.append("identity success evidence must affirm authenticated or matched identity")
    if kind == "AUTHORIZATION_DECISION" and payload.get("scope") != authority.get("resource_id"):
        errors.append("authorization evidence scope disagrees with adopted authority")
    if kind == "AUTHORIZATION_DECISION" and str(
        payload.get("decision") or ""
    ).upper() not in AUTHORIZATION_SUCCESS_RESULTS:
        errors.append("delegated route requires an affirmative authorization decision")
    if kind == "PLATFORM_EFFECT" and payload.get("before_state") == payload.get("after_state"):
        errors.append("platform-effect evidence does not prove a state effect")
    if kind == "TASK_TRANSITION" and payload.get("from_state") == payload.get("to_state"):
        errors.append("task evidence does not prove a transition")
    if kind == "AUDIT_EVENT" and payload.get("audit_event_id") != row.get("Audit event ID"):
        errors.append("audit payload disagrees with the adopted audit event")
    if kind == "RESULT_DELIVERY" and (
        payload.get("recipient_id") != route.get("human_beneficiary_id")
        or payload.get("result") != route.get("human_observable_outcome")
    ):
        errors.append("result-delivery payload does not prove the human outcome")
    if kind == "DELEGATION_BASIS" and payload.get("delegation_basis_id") != authority.get(
        "delegation_basis_id"
    ):
        errors.append("delegation evidence disagrees with adopted authority")
    if kind == "ASSISTED_ACTION" and str(
        payload.get("result") or ""
    ).upper() not in ASSISTED_ACTION_SUCCESS_RESULTS:
        errors.append("assisted action success evidence must show the action was performed")
    if kind == "USER_COMMUNICATION":
        if (
            str(payload.get("direction") or "").upper() != "SERVICE_TO_HUMAN"
            or str(payload.get("delivery_result") or "").upper()
            not in USER_COMMUNICATION_SUCCESS_RESULTS
        ):
            errors.append(
                "user communication direction/result must prove successful delivery to the user"
            )
    return errors


def _validate_completed_route_evidence(route, route_rows, route_id):
    errors = []
    route_kind = route.get("route_kind")
    kinds = {row.get("Evidence kind") for row in route_rows}
    if route_kind in {"PERSONAL_AGENT", "SERVICE_CENTER"} and "AUTHORIZATION_DECISION" not in kinds:
        errors.append("accepted delegated route lacks affirmative authorization evidence")
    if route_kind == "PERSONAL_AGENT" and "AGENT_IDENTITY" not in kinds:
        errors.append("accepted Personal Agent route lacks Agent identity evidence")
    if route_kind == "SERVICE_CENTER":
        if "SERVICE_ACTOR_IDENTITY" not in kinds:
            errors.append("accepted Service Center route lacks service actor identity evidence")
        if "ASSISTED_ACTION" not in kinds:
            errors.append("accepted Service Center route lacks assisted action evidence")
        if "USER_COMMUNICATION" not in kinds:
            errors.append("accepted Service Center route lacks user communication evidence")
    if route_kind in {"PERSONAL_AGENT", "SERVICE_CENTER"} and "PLATFORM_EFFECT" not in kinds:
        errors.append("accepted delegated route lacks platform-effect evidence")
    if route_kind == "SERVICE_CENTER" and "DELEGATION_BASIS" not in kinds:
        errors.append("accepted Service Center route lacks delegation-basis evidence")
    expected_audits = route.get("audit_event_ids")
    expected_audits = expected_audits if isinstance(expected_audits, list) else []
    actual_audits = [
        row.get("Audit event ID")
        for row in route_rows if row.get("Evidence kind") == "AUDIT_EVENT"
    ]
    if len(actual_audits) != len(set(actual_audits)) or set(actual_audits) != set(
        expected_audits
    ):
        errors.append("complete-round audit evidence must exactly cover adopted audit event IDs")
    terminal_kind = "SCREENSHOT" if route_kind == "DIRECT_PRODUCT" else "RESULT_DELIVERY"
    final_row = route_rows[-1]
    if (
        final_row.get("Evidence kind") != terminal_kind
        or final_row.get("Human-observable outcome") != route.get("human_observable_outcome")
    ):
        errors.append("route lacks its final human-observable outcome: " + str(route_id))
    return errors


def _validate_route_evidence(lc, text, summary, required_routes, rounds):
    rows, errors = _rows_with_header_prefix(
        text,
        ("Round", "Journey ID", "Service Route ID"),
        "route-faithful evidence digest",
    )
    evidence_ids = set()
    evidence_paths = set()
    digest_rounds = {}
    evidence_by_round = {}
    evidence_by_identity = {}
    for row in rows:
        try:
            number = int(row.get("Round", ""))
        except (TypeError, ValueError):
            number = -1
        round_record = rounds.get(number)
        if round_record is None:
            errors.append("route evidence round is absent from acceptance round history")
        key = (row.get("Journey ID"), row.get("Service Route ID"))
        route = required_routes.get(key)
        if route is None:
            errors.append("route evidence does not belong to a required delivered adopted route")
            continue
        if row.get("Route kind") != route.get("route_kind"):
            errors.append("route evidence kind disagrees with the adopted Service Route Map")
        if not STEP_ID_RE.fullmatch(str(row.get("Step ID", ""))):
            errors.append("route evidence Step ID is missing or malformed")
        evidence_id = row.get("Evidence ID")
        if not SAFE_ID_RE.fullmatch(str(evidence_id or "")):
            errors.append("route evidence ID is missing or malformed")
        if evidence_id in evidence_ids:
            errors.append("route-faithful acceptance requires unique evidence IDs")
        evidence_ids.add(evidence_id)

        authority = route.get("authority") if isinstance(route.get("authority"), dict) else {}
        expected_bindings = {
            "Actor ID": route.get("actor_id"),
            "Authority action ID": authority.get("action_id"),
            "Authority resource ID": authority.get("resource_id"),
            "Delegation basis ID": authority.get("delegation_basis_id"),
        }
        for field, value in expected_bindings.items():
            if row.get(field) != value:
                errors.append(field + " disagrees with the adopted route")
        evidence_kind = row.get("Evidence kind")
        route_kind = route.get("route_kind")
        allowed_kinds = set(ROUTE_ALLOWED_EVIDENCE_KINDS.get(route_kind, set())) | {"SCREENSHOT"}
        if evidence_kind not in allowed_kinds:
            errors.append("route evidence kind is not applicable to " + str(route_kind) + " step")
        audit_id = row.get("Audit event ID")
        if evidence_kind == "AUDIT_EVENT":
            audit_ids = route.get("audit_event_ids")
            if not isinstance(audit_ids, list) or audit_id not in audit_ids:
                errors.append("route audit evidence disagrees with the adopted audit lineage")
        elif audit_id != "NOT_APPLICABLE":
            errors.append("non-audit route step must not claim an audit event ID")
        if row.get("Result") not in {"PASS", "DEFECT", "BLOCKED_BY_DEFECT"}:
            errors.append("route evidence result is invalid")

        path = None
        digest = None
        if evidence_kind == "SCREENSHOT":
            for field in ("Action", "Expected / observed visible result", "Visible location"):
                if not _meaningful(row.get(field)):
                    errors.append("visible " + field + " is required for screenshot-backed route step")
            if not VIEWPORT_RE.fullmatch(str(row.get("Viewport") or "")):
                errors.append("visible Viewport must be exact widthxheight@DPR")
            if row.get("Native evidence path") != "NOT_APPLICABLE" or row.get(
                "Native evidence SHA-256"
            ) != "NOT_APPLICABLE":
                errors.append("visible screenshot step must not fabricate native nonvisual evidence")
            reference = row.get("Screenshot path")
            path = _safe_reference(lc, reference, screenshot=True)
            if path is None:
                errors.append("screenshot evidence path is outside the journey evidence root or unreadable")
            else:
                errors.extend(_validate_screenshot(path, row))
            digest = row.get("Screenshot SHA-256")
        else:
            for field in (
                "Action", "Expected / observed visible result", "Visible location", "Viewport",
                "Screenshot path", "Screenshot SHA-256",
            ):
                if row.get(field) != "NOT_APPLICABLE":
                    errors.append("nonvisual route step must not fabricate visible/screenshot field " + field)
            reference = row.get("Native evidence path")
            path = _safe_reference(lc, reference)
            if path is None:
                errors.append("non-visual evidence path is outside the project evidence boundary or unreadable")
            else:
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
                digest = row.get("Native evidence SHA-256")
                if not HASH_RE.fullmatch(str(digest)) or digest != actual:
                    errors.append("non-visual evidence digest does not match resolved evidence bytes")
                stored = dict(row)
                stored["_round_number"] = number
                errors.extend(_validate_project_evidence(path, stored, round_record, route))
            digest = row.get("Native evidence SHA-256")
        if reference in evidence_paths:
            errors.append("route-faithful acceptance requires unique evidence paths")
        evidence_paths.add(reference)
        if HASH_RE.fullmatch(str(digest or "")):
            prior_rounds = digest_rounds.setdefault(digest, set())
            if prior_rounds and number not in prior_rounds:
                errors.append("evidence digest cannot be reused across rounds")
            prior_rounds.add(number)
        stored = dict(row)
        stored["_round_number"] = number
        stored["_path"] = path
        stored["_digest"] = digest
        evidence_by_round.setdefault(number, {}).setdefault(key, []).append(stored)
        identity = (number, row.get("Journey ID"), row.get("Service Route ID"), row.get("Step ID"))
        evidence_by_identity.setdefault(identity, []).append(stored)

    for number, round_row in rounds.items():
        attempted = set(round_row.get("_attempted", ()))
        actual_route_ids = {
            key[1] for key, route_rows in evidence_by_round.get(number, {}).items() if route_rows
        }
        if actual_route_ids != attempted:
            errors.append("attempted route entry IDs must exactly match routes with real evidence")
        ordered_round_rows = [row for row in rows if str(row.get("Round")) == str(number)]
        endpoints = _split_exact(round_row.get("First and last evidence"), 2)
        if ordered_round_rows and endpoints != [
            ordered_round_rows[0].get("Evidence ID"), ordered_round_rows[-1].get("Evidence ID"),
        ]:
            errors.append("acceptance round first/last evidence does not match attempted evidence")
        observed_passed = 0
        observed_failed = 0
        blocking_evidence_ids = set()
        for key, route in required_routes.items():
            if key[1] not in attempted:
                continue
            route_rows = evidence_by_round.get(number, {}).get(key, [])
            if not route_rows:
                errors.append("attempted route entry lacks real evidence for " + str(key[1]))
                continue
            route_kind = route.get("route_kind")
            if route_rows[0].get("Evidence kind") not in ROUTE_ENTRY_KINDS.get(route_kind, set()):
                errors.append("attempted route entry does not begin with applicable first-hand evidence")
            nonpassing = [row for row in route_rows if row.get("Result") != "PASS"]
            if nonpassing:
                observed_failed += 1
                blocking_evidence_ids.update(row.get("Evidence ID") for row in nonpassing)
                if route_rows[-1].get("Result") not in {"DEFECT", "BLOCKED_BY_DEFECT"}:
                    errors.append("failed attempted route must end at its real defect or blocked step")
            else:
                observed_passed += 1
                errors.extend(_validate_completed_route_evidence(route, route_rows, key[1]))
        counts = round_row.get("_counts")
        if isinstance(counts, tuple) and len(counts) == 3 and (
            observed_passed != counts[1] or observed_failed != counts[2]
        ):
            errors.append("acceptance round passed/failed counts disagree with route evidence")
        if round_row.get("Result") == "PASS" and observed_failed:
            errors.append("PASS round route evidence contains a non-PASS step")
        for _, evidence_id, defect_id in round_row.get("_dispositions", {}).values():
            if evidence_id not in blocking_evidence_ids:
                errors.append("unattempted route disposition must join actual blocking evidence")
            if defect_id not in round_row.get("_defects", ()):
                errors.append("unattempted route disposition must join a round defect")
    context = {
        "rows": rows,
        "by_round": evidence_by_round,
        "by_identity": evidence_by_identity,
    }
    return context, errors


def _validate_acceptance_record_400(project_root: Path, status: dict) -> list[str]:
    summary = status.get("real_user_journey_acceptance", {})
    if not isinstance(summary, dict) or summary.get("state") == "UNPROVED":
        return []
    lc = _lc_root(project_root)
    path = _safe_reference(lc, summary.get("acceptance_record_reference"))
    if path is None:
        return ["journey acceptance record reference is missing, unsafe, or unreadable"]
    text, errors = _read_markdown(path)
    fields, field_errors = _markdown_fields(text)
    errors.extend(field_errors)
    if not SAFE_ID_RE.fullmatch(fields.get("Acceptance ID", "")):
        errors.append("Acceptance ID is missing or malformed")
    if fields.get("Status schema version") != "4.0.0":
        errors.append("route-faithful acceptance record must select schema 4.0.0")
    if fields.get("Candidate ID") != summary.get("candidate_id") or fields.get(
        "Candidate SHA-256"
    ) != summary.get("candidate_hash"):
        errors.append("acceptance record candidate identity disagrees with status")

    required_routes, map_path, map_errors = _required_route_map(project_root, status)
    errors.extend(map_errors)
    if map_path is not None:
        map_record, _ = _read_json(map_path)
        map_identity = _split_exact(fields.get("Service Route Map ID / exact hash"), 2)
        expected_identity = [
            str(map_record.get("map_id")) if isinstance(map_record, dict) else "",
            "sha256:" + hashlib.sha256(map_path.read_bytes()).hexdigest(),
        ]
        if map_identity != expected_identity:
            errors.append("acceptance record Service Route Map identity/hash drift")
    coverage, coverage_errors = _validate_route_coverage(text, required_routes)
    errors.extend(coverage_errors)
    errors.extend(_validate_task5_receipts(lc, status, coverage, required_routes))
    required_count = len(required_routes)
    if summary.get("required_journey_count") != required_count:
        errors.append("required journey count must equal required delivered route coverage in 4.0")
    if summary.get("state") == "REAL_USER_JOURNEY_ACCEPTED" and summary.get(
        "passed_journey_count"
    ) != required_count:
        errors.append("accepted 4.0 journey summary must pass every required delivered route")
    rounds, round_errors = _validate_route_rounds(text, summary, required_routes)
    errors.extend(round_errors)
    _, evidence_errors = _validate_route_evidence(
        lc, text, summary, required_routes, rounds
    )
    errors.extend(evidence_errors)
    return errors


def _route_ids_by_kind(project_root, status):
    routes, _, errors = _required_route_map(project_root, status)
    by_id = {}
    for (_, route_id), route in routes.items():
        by_id[route_id] = route
    return by_id, errors


def _acceptance_context_for_defects(project_root, status, required_routes):
    lc = _lc_root(project_root)
    summary = status.get("real_user_journey_acceptance")
    summary = summary if isinstance(summary, dict) else {}
    path = _safe_reference(lc, summary.get("acceptance_record_reference"))
    if path is None:
        return {}, {}, ["defect binding requires a readable journey acceptance record"]
    text, errors = _read_markdown(path)
    rounds, round_errors = _validate_route_rounds(text, summary, required_routes)
    context, evidence_errors = _validate_route_evidence(
        lc, text, summary, required_routes, rounds
    )
    errors.extend(round_errors)
    errors.extend(evidence_errors)
    return rounds, context, errors


def _matching_evidence(context, *, round_number, journey_id, route_id, step_id=None, evidence=None):
    candidates = []
    if step_id is not None:
        candidates = context.get("by_identity", {}).get(
            (round_number, journey_id, route_id, step_id), []
        )
    else:
        candidates = context.get("by_round", {}).get(round_number, {}).get(
            (journey_id, route_id), []
        )
    if not evidence:
        return []
    return [
        row for row in candidates
        if row.get("Evidence ID") == evidence[0]
        and row.get("Evidence kind") == evidence[1]
        and row.get("_digest") == evidence[2]
        and row.get("_path") is not None
    ]


def _evidence_identity(row):
    if not isinstance(row, dict):
        return None
    return (
        row.get("_round_number"), row.get("Evidence ID"), row.get("_digest"),
        row.get("_path"),
    )


def _resolve_history_route_evidence(lc, value, context, round_number):
    label = "defect history evidence"
    reference, path, errors = _resolve_exact_citation(lc, value, label)
    if reference is None or path is None:
        return None, errors
    round_rows = [
        row
        for rows in context.get("by_round", {}).get(round_number, {}).values()
        for row in rows
    ]
    matches = [
        row for row in round_rows
        if row.get("_round_number") == round_number
        and row.get("Evidence ID") == reference[0]
        and "sha256:" + str(row.get("_digest")) == reference[1]
        and row.get("_path") == path
    ]
    if len(matches) != 1:
        errors.append("defect history evidence must join one actual route evidence row/file")
        return None, errors
    return matches[0], errors


def _validate_exemption_citation(lc, value, defect_id, defect_row, history_row):
    """Resolve and bind the Owner decision record cited by an exemption event."""
    label = "OWNER_EXEMPTED history evidence"
    reference, path, errors = _resolve_exact_citation(lc, value, label)
    if reference is None or path is None:
        return errors
    record, read_errors = _read_json(path)
    errors.extend(label + ": " + error for error in read_errors)
    if not isinstance(record, dict):
        if not read_errors:
            errors.append(label + " must be a strict project evidence object")
        return errors
    if set(record) != EXEMPTION_RECORD_FIELDS:
        errors.append(label + " must use the closed project exemption schema")
    exemption = _split_exact(defect_row.get("Exemption authority / impact / recovery"), 3)
    candidate = _split_exact(history_row.get("Candidate ID / SHA-256"), 2)
    discovery = _split_exact(
        defect_row.get("Discovery time / candidate / round / Journey / Route / Step"), 6
    )
    expected = {
        "record_role": "REAL_USER_JOURNEY_DEFECT_EXEMPTION",
        "evidence_schema_version": "4.0.0",
        "evidence_id": reference[0],
        "defect_id": defect_id,
        "candidate_id": candidate[0] if candidate else None,
        "candidate_hash": candidate[1] if candidate else None,
        "round": history_row.get("_round_number"),
        "route_id": discovery[4] if discovery else None,
        "authority": exemption[0] if exemption else None,
        "impact": exemption[1] if exemption else None,
        "recovery_condition": exemption[2] if exemption else None,
        "decision": "OWNER_EXEMPTED",
    }
    if any(record.get(field) != expected_value for field, expected_value in expected.items()):
        errors.append(label + " does not join the defect, candidate, route, or Owner decision")
    return errors


def _validate_priority_exception(lc, value, summary, earlier, later):
    label = "repair priority exception evidence"
    reference, path, errors = _resolve_exact_citation(lc, value, label)
    if reference is None or path is None:
        return False, errors
    record, read_errors = _read_json(path)
    errors.extend(label + ": " + error for error in read_errors)
    if not isinstance(record, dict):
        if not read_errors:
            errors.append(label + " must be a strict project evidence object")
        return False, errors
    if set(record) != PRIORITY_EXCEPTION_FIELDS:
        errors.append(label + " must use the closed project exception schema")
    expected = {
        "record_role": "REAL_USER_JOURNEY_REPAIR_PRIORITY_EXCEPTION",
        "evidence_schema_version": "4.0.0",
        "evidence_id": reference[0],
        "candidate_id": summary.get("candidate_id"),
        "candidate_hash": summary.get("candidate_hash"),
        "earlier_defect_id": earlier[4],
        "earlier_repair_sequence": earlier[0],
        "earlier_layer": earlier[1],
        "later_defect_id": later[4],
        "later_repair_sequence": later[0],
        "later_layer": later[1],
        "decision": "ALLOW_PRIORITY_EXCEPTION",
    }
    if any(record.get(field) != expected_value for field, expected_value in expected.items()):
        errors.append(label + " does not join the exact candidate and inverted repairs")
    if not _meaningful(record.get("authority")) or not _meaningful(record.get("rationale")):
        errors.append(label + " requires authority and a meaningful rationale")
    return not errors, errors


def _validate_defect_log_400(project_root: Path, status: dict) -> list[str]:
    summary = status.get("real_user_journey_acceptance", {})
    if not isinstance(summary, dict) or summary.get("state") == "UNPROVED":
        return []
    lc = _lc_root(project_root)
    path = _safe_reference(lc, summary.get("defect_log_reference"))
    if path is None:
        return ["journey defect log reference is missing, unsafe, or unreadable"]
    text, errors = _read_markdown(path)
    fields, field_errors = _markdown_fields(text)
    errors.extend(field_errors)
    if fields.get("Status schema version") != "4.0.0":
        errors.append("route-faithful defect log must select schema 4.0.0")
    if fields.get("Normal repair priority") != REPAIR_PRIORITY_400:
        errors.append("4.0 defect log must preserve user-experience-first repair priority")
    required_routes, _, map_errors = _required_route_map(project_root, status)
    errors.extend(map_errors)
    routes = {route_id: route for (_, route_id), route in required_routes.items()}
    rounds, evidence_context, context_errors = _acceptance_context_for_defects(
        project_root, status, required_routes
    )
    errors.extend(context_errors)
    rows, table_errors = _rows_with_header_prefix(
        text,
        ("Defect ID", "Discovery time / candidate / round / Journey / Route / Step"),
        "route-faithful defect register",
    )
    errors.extend(table_errors)
    ids = []
    states = {state: [] for state in DEFECT_STATES}
    register = {}
    discoveries_by_round = {}
    discovery_evidence = {}
    retest_evidence = {}
    repair_rows = []
    for row in rows:
        try:
            defect_id = int(row.get("Defect ID", ""))
        except (TypeError, ValueError):
            defect_id = -1
        ids.append(defect_id)
        register[defect_id] = row
        state = row.get("State")
        if state not in DEFECT_STATES:
            errors.append("defect state is invalid")
        else:
            states[state].append(defect_id)
        discovery = _split_exact(
            row.get("Discovery time / candidate / round / Journey / Route / Step"), 6
        )
        route_id = discovery[4] if discovery else None
        route = routes.get(route_id)
        try:
            discovery_round = int(discovery[2]) if discovery else -1
        except (TypeError, ValueError):
            discovery_round = -1
        if (
            not discovery or not SAFE_ID_RE.fullmatch(discovery[1])
            or not JOURNEY_ID_RE.fullmatch(discovery[3])
            or not STEP_ID_RE.fullmatch(discovery[5])
            or discovery_round < 1
        ):
            errors.append("defect discovery identity is malformed")
        round_candidate = rounds.get(discovery_round, {}).get("_candidate")
        if discovery and (
            not isinstance(round_candidate, tuple)
            or len(round_candidate) != 2
            or discovery[1] != round_candidate[0]
        ):
            errors.append("defect discovery candidate/round disagrees with acceptance history")
        if route is None:
            errors.append("defect discovery route is not a required delivered adopted route")
        evidence = _split_exact(row.get("Evidence ID / kind / SHA-256"), 3)
        if not evidence or not SAFE_ID_RE.fullmatch(evidence[0]) or not _meaningful(
            evidence[1]
        ) or not HASH_RE.fullmatch(evidence[2]):
            errors.append("defect requires stable route evidence identity, kind, and SHA-256")
        matches = _matching_evidence(
            evidence_context,
            round_number=discovery_round,
            journey_id=discovery[3] if discovery else None,
            route_id=route_id,
            step_id=discovery[5] if discovery else None,
            evidence=evidence,
        )
        if len(matches) != 1 or matches[0].get("Result") not in {"DEFECT", "BLOCKED_BY_DEFECT"}:
            errors.append("defect discovery evidence must resolve one actual DEFECT/BLOCKED row/file")
        else:
            discovery_evidence[defect_id] = matches[0]
        row["_discovery_evidence_id"] = evidence[0] if evidence else None
        discoveries_by_round.setdefault(discovery_round, set()).add(defect_id)
        layer_parts = _split_exact(row.get("Affected layer / root cause"), 2)
        layer = layer_parts[0] if layer_parts else None
        if layer not in DEFECT_LAYERS_400 or not layer_parts or not _meaningful(layer_parts[1]):
            errors.append("defect affected layer is invalid or lacks root-cause evidence")
        boundary = row.get("Boundary surface / evidence")
        if layer == "USER_SERVICE_BOUNDARY":
            boundary_parts = _split_exact(boundary, 2)
            expected_surfaces = BOUNDARY_SURFACES_BY_ROUTE.get(
                route.get("route_kind") if isinstance(route, dict) else None
            )
            if (
                not boundary_parts
                or boundary_parts[0] not in (expected_surfaces or set())
                or not SAFE_ID_RE.fullmatch(boundary_parts[1])
                or not evidence
                or boundary_parts[1] != evidence[0]
            ):
                errors.append("USER_SERVICE_BOUNDARY defect requires route-faithful boundary evidence")
        elif boundary != "NOT_APPLICABLE":
            errors.append("non-boundary defect must use NOT_APPLICABLE boundary evidence")
        affected = [item.strip() for item in str(row.get("Affected routes", "")).split(",")]
        if (
            not affected or len(affected) != len(set(affected))
            or any(item not in routes for item in affected)
        ):
            errors.append("defect affected routes must identify required delivered adopted routes")
        row["_affected_routes"] = set(affected)
        severity = _split_exact(row.get("Severity / reachability / blocking scope"), 3)
        blocking_scope = severity[2] if severity else None
        if blocking_scope == "GLOBAL_BOUNDARY":
            scope_routes = set()
        else:
            scope_routes = {
                item.strip() for item in str(blocking_scope or "").split(",") if item.strip()
            }
            if not scope_routes or any(item not in routes for item in scope_routes):
                errors.append("defect blocking scope must name adopted routes or GLOBAL_BOUNDARY")
        row["_blocking_scope"] = blocking_scope
        row["_blocking_scope_routes"] = scope_routes
        try:
            retest_round = int(row.get("Retest round", ""))
        except (TypeError, ValueError):
            retest_round = -1
        retest = _split_exact(row.get("Retest evidence ID / kind / SHA-256"), 3)
        if state == "FIXED_VERIFIED":
            if (
                row.get("Correction identity / engineering re-verification") in {"", "NOT_APPLICABLE"}
                or retest_round <= discovery_round or retest_round not in rounds
            ):
                errors.append("fixed defect requires correction identity and later-round retest evidence")
            retest_matches = _matching_evidence(
                evidence_context,
                round_number=retest_round,
                journey_id=discovery[3] if discovery else None,
                route_id=route_id,
                evidence=retest,
            )
            if len(retest_matches) != 1 or retest_matches[0].get("Result") != "PASS":
                errors.append("FIXED_VERIFIED defect retest evidence must resolve a later PASS row/file")
            else:
                retest_evidence[defect_id] = retest_matches[0]
        elif row.get("Retest round") != "NOT_APPLICABLE" or row.get(
            "Retest evidence ID / kind / SHA-256"
        ) != "NOT_APPLICABLE":
            errors.append("non-fixed defect must not claim retest evidence")
        if state == "OWNER_EXEMPTED":
            exemption = _split_exact(row.get("Exemption authority / impact / recovery"), 3)
            if not exemption or any(not _meaningful(part) for part in exemption):
                errors.append("Owner exemption requires authority, user impact, and recovery condition")
        try:
            repair_sequence = int(row.get("Repair sequence", ""))
        except (TypeError, ValueError):
            repair_sequence = -1
        if repair_sequence < 1:
            errors.append("defect Repair sequence must be a positive integer")
        repair_rows.append((
            repair_sequence, layer, row.get("Priority exception justification"), state,
            defect_id,
        ))
    if ids != sorted(set(ids)) or any(defect_id < 40001 for defect_id in ids):
        errors.append("defect IDs must be unique, increasing, unrecycled, and start at 40001")
    expected = {
        "open_defect_ids": states["OPEN"],
        "fixed_verified_defect_ids": states["FIXED_VERIFIED"],
        "exempted_defect_ids": states["OWNER_EXEMPTED"],
        "deferred_defect_ids": states["DEFERRED"],
        "reopened_defect_ids": states["REOPENED"],
    }
    for field, value in expected.items():
        if summary.get(field) != value:
            errors.append(field + " disagrees with the append-only defect register")

    for round_row in rounds.values():
        for omitted_route, disposition in round_row.get("_dispositions", {}).items():
            disposition_kind, evidence_id, defect_id = disposition
            defect = register.get(defect_id)
            if not isinstance(defect, dict) or defect.get("_discovery_evidence_id") != evidence_id:
                errors.append(
                    "unattempted route disposition defect must join its exact blocking evidence"
                )
                continue
            if omitted_route not in defect.get("_affected_routes", set()):
                errors.append("blocking defect does not cover omitted route in affected routes")
            if disposition_kind == "GLOBAL_BLOCKED":
                if defect.get("_blocking_scope") != "GLOBAL_BOUNDARY":
                    errors.append("GLOBAL_BLOCKED requires an explicit validated global boundary")
            elif omitted_route not in defect.get("_blocking_scope_routes", set()):
                errors.append("blocking defect does not cover omitted route in blocking scope")

    scheduled_repairs = [
        item for item in repair_rows
        if item[3] in {"OPEN", "REOPENED", "DEFERRED", "FIXED_VERIFIED"}
    ]
    sequences = [item[0] for item in scheduled_repairs]
    if len(sequences) != len(set(sequences)):
        errors.append("scheduled defect Repair sequence values must be unique")
    ordered_repairs = sorted(scheduled_repairs, key=lambda item: item[0])
    for earlier, later in zip(ordered_repairs, ordered_repairs[1:]):
        earlier_rank = DEFECT_LAYER_ORDER.get(earlier[1])
        later_rank = DEFECT_LAYER_ORDER.get(later[1])
        if earlier_rank is not None and later_rank is not None and earlier_rank > later_rank:
            justified, exception_errors = _validate_priority_exception(
                lc, earlier[2], summary, earlier, later
            )
            errors.extend(exception_errors)
            if not justified:
                errors.append(
                    "repair priority order requires boundary before orchestration before core, "
                    "or exact justified exception evidence"
                )

    for number, round_row in rounds.items():
        if set(round_row.get("_defects", ())) != discoveries_by_round.get(number, set()):
            errors.append("REWORK/BLOCKED round defects must exactly join discovered evidence rows")

    history, history_errors = _rows_with_header_prefix(
        text, ("Defect ID", "Event time", "Prior state", "New state"), "defect state history"
    )
    errors.extend(history_errors)
    by_id = {}
    for row in history:
        try:
            defect_id = int(row.get("Defect ID", ""))
        except (TypeError, ValueError):
            defect_id = -1
        by_id.setdefault(defect_id, []).append(row)
        if defect_id not in register:
            errors.append("defect state history references an unknown defect ID")
        history_candidate = _split_exact(row.get("Candidate ID / SHA-256"), 2)
        if (
            not history_candidate or not SAFE_ID_RE.fullmatch(history_candidate[0])
            or not HASH_RE.fullmatch(history_candidate[1])
        ):
            errors.append("defect state history candidate identity is malformed")
        try:
            history_round = int(row.get("Round", ""))
        except (TypeError, ValueError):
            history_round = -1
        row["_round_number"] = history_round
        round_candidate = rounds.get(history_round, {}).get("_candidate")
        if not history_candidate or tuple(history_candidate) != round_candidate:
            errors.append("defect history candidate/round does not join acceptance history")
        if row.get("New state") != "OWNER_EXEMPTED":
            row["_evidence"], evidence_errors = _resolve_history_route_evidence(
                lc, row.get("Evidence / reason"), evidence_context, history_round
            )
            errors.extend(evidence_errors)
    for defect_id, row in register.items():
        events = by_id.get(defect_id, [])
        valid = bool(events) and events[0].get("Prior state") == "NOT_APPLICABLE" and events[
            0
        ].get("New state") == "OPEN"
        for prior, current in zip(events, events[1:]):
            valid = valid and prior.get("New state") == current.get("Prior state")
        if not events or events[-1].get("New state") != row.get("State"):
            valid = False
        if any(
            event.get("New state") not in DEFECT_STATES
            or event.get("Prior state") not in DEFECT_STATES | {"NOT_APPLICABLE"}
            for event in events
        ):
            valid = False
        if not valid:
            errors.append("defect requires complete state history from OPEN through current state")
            continue
        first_row = discovery_evidence.get(defect_id)
        if _evidence_identity(events[0].get("_evidence")) != _evidence_identity(first_row):
            errors.append("OPEN history evidence does not join defect discovery evidence")
        if row.get("State") == "FIXED_VERIFIED":
            if _evidence_identity(events[-1].get("_evidence")) != _evidence_identity(
                retest_evidence.get(defect_id)
            ):
                errors.append("FIXED_VERIFIED history evidence does not join later retest evidence")
        if row.get("State") == "OWNER_EXEMPTED":
            errors.extend(_validate_exemption_citation(
                lc, events[-1].get("Evidence / reason"), defect_id, row, events[-1]
            ))
    return errors


def validate_acceptance_record(project_root: Path, status: dict) -> list[str]:
    if status.get("status_schema_version") == "4.0.0":
        return _validate_acceptance_record_400(project_root, status)
    return _validate_acceptance_record_300(project_root, status)


def validate_defect_log(project_root: Path, status: dict) -> list[str]:
    if status.get("status_schema_version") == "4.0.0":
        return _validate_defect_log_400(project_root, status)
    return _validate_defect_log_300(project_root, status)


def validate_real_user_journey(project_root: Path, status: dict, phase_status: dict) -> list[str]:
    errors = validate_status_summary(status)
    if not isinstance(status, dict):
        return errors
    if status.get("status_schema_version") not in {"3.0.0", "4.0.0"}:
        return errors
    summary = status.get("real_user_journey_acceptance", {})
    errors.extend(validate_acceptance_record(project_root, status))
    errors.extend(validate_defect_log(project_root, status))
    phases = phase_status.get("phases") if isinstance(phase_status, dict) else None
    if not isinstance(phases, dict):
        errors.append("derived phase status phases must be an object")
        phase = {}
    else:
        phase = phases.get("REAL_USER_JOURNEY_ACCEPTANCE")
        if not isinstance(phase, dict):
            errors.append("derived journey phase status must be an object")
            phase = {}
    if isinstance(summary, dict) and summary.get("state") != "UNPROVED":
        if phase.get("acceptance_record") != summary.get("acceptance_record_reference"):
            errors.append("derived journey acceptance record disagrees with authoritative status")
        if phase.get("defect_log") != summary.get("defect_log_reference"):
            errors.append("derived journey defect log disagrees with authoritative status")
        if phase.get("complete_rounds") != summary.get("complete_round_count"):
            errors.append("derived complete-round count disagrees with authoritative status")
    phase_gates = status.get("phase_gates")
    if status.get("current_phase") == "DELIVERY_PREPARATION" and (
        not isinstance(phase_gates, dict)
        or phase_gates.get("REAL_USER_JOURNEY_ACCEPTED") != "REAL_USER_JOURNEY_ACCEPTED"
        or not isinstance(summary, dict)
        or summary.get("state") != "REAL_USER_JOURNEY_ACCEPTED"
    ):
        errors.append("Delivery Preparation requires current REAL_USER_JOURNEY_ACCEPTED evidence")
    return errors
