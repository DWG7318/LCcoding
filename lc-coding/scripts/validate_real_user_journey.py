#!/usr/bin/env python3
"""Validate exact 3.0 browser and 4.0 route-faithful user-journey evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


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
ROUTE_EVIDENCE_KINDS = {
    "DIRECT_PRODUCT": {"SCREENSHOT"},
    "PERSONAL_AGENT": {
        "HUMAN_GOAL_MESSAGE", "AGENT_IDENTITY", "REQUEST_MESSAGE", "TASK_TRANSITION",
        "AUTHORIZATION_DECISION", "RESULT_ARTIFACT", "PLATFORM_EFFECT", "AGENT_RESPONSE",
        "RESULT_DELIVERY",
    },
    "SERVICE_CENTER": {
        "USER_REQUEST", "SERVICE_ACTOR_IDENTITY", "DELEGATION_BASIS", "ASSISTED_ACTION",
        "PLATFORM_EFFECT", "USER_COMMUNICATION", "RESULT_DELIVERY",
    },
}
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
        if (
            summary.get("coverage_state") != "COMPLETE"
            or summary.get("acceptance_environment_state") != "VERIFIED"
            or summary.get("failed_journey_count") != 0
            or summary.get("open_defect_ids")
            or summary.get("deferred_defect_ids")
            or summary.get("reopened_defect_ids")
            or summary.get("owner_result") != "REAL_USER_JOURNEY_ACCEPTED"
            or summary.get("passed_journey_count", -1)
            + summary.get("not_applicable_journey_count", -1)
            != summary.get("required_journey_count")
        ):
            errors.append("accepted journey state requires complete coverage and no open blocking defects")
        if status.get("phase_gates", {}).get("REAL_USER_JOURNEY_ACCEPTED") != "REAL_USER_JOURNEY_ACCEPTED":
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
    if not isinstance(record, dict) or record.get("state") != "ADOPTED" or status.get(
        "service_route_map"
    ) != "ADOPTED":
        errors.append("4.0 journey acceptance requires an ADOPTED Service Route Map")
        return {}, path, errors
    required = {}
    journeys = record.get("journeys")
    if not isinstance(journeys, list):
        return {}, path, errors + ["adopted Service Route Map journeys must be an array"]
    for journey in journeys:
        if not isinstance(journey, dict) or journey.get("delivery_state") != "DELIVERED":
            continue
        journey_id = journey.get("journey_id")
        routes = journey.get("routes")
        if not isinstance(routes, list):
            continue
        for route in routes:
            if not isinstance(route, dict) or route.get("support_state") != "REQUIRED" or route.get(
                "delivery_state"
            ) != "DELIVERED":
                continue
            key = (journey_id, route.get("route_id"))
            if key in required:
                errors.append("adopted Service Route Map contains duplicate required route identity")
            required[key] = route
    if not required:
        errors.append("4.0 journey acceptance requires at least one required delivered route")
    return required, path, errors


def _validate_route_coverage(text, required_routes):
    rows, errors = _rows_with_header_prefix(
        text, ("Journey ID", "Service Route ID"), "route-faithful journey coverage"
    )
    actual = {}
    for row in rows:
        key = (row.get("Journey ID"), row.get("Service Route ID"))
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
        adopted_ids = route.get("acceptance_evidence_ids", [])
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


def _validate_route_rounds(text, summary, required_count):
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
        by_number[number] = row
        if row.get("Candidate ID / SHA-256") != " / ".join((
            str(summary.get("candidate_id")), str(summary.get("candidate_hash")),
        )):
            errors.append("acceptance round candidate identity disagrees with status")
        if row.get("Started from every actual route entry") != "YES":
            errors.append("every complete-round restart must restart from every actual route entry")
        counts = _split_exact(row.get("Required routes / passed / failed"), 3)
        try:
            required, passed, failed = [int(value) for value in counts]
        except (TypeError, ValueError):
            required, passed, failed = -1, -1, -1
            errors.append("acceptance round route counts are malformed")
        if required != required_count:
            errors.append("acceptance round required route count disagrees with adopted map coverage")
        result = row.get("Result")
        if result not in {"PASS", "REWORK", "BLOCKED"}:
            errors.append("acceptance round result is invalid")
        if result == "PASS":
            complete_count += 1
            if passed != required_count or failed != 0:
                errors.append("complete acceptance round must pass every required delivered route")
    numbers = list(by_number)
    if numbers != sorted(set(numbers)) or any(number < 1 for number in numbers):
        errors.append("acceptance round numbers must be unique and increasing")
    current_round = summary.get("current_round")
    if current_round not in by_number:
        errors.append("current acceptance round is absent from the record")
    elif current_round != max(by_number):
        errors.append("current acceptance round must be the latest recorded round")
    if summary.get("complete_round_count") != complete_count:
        errors.append("complete-round count disagrees with route-faithful round history")
    if summary.get("state") == "REAL_USER_JOURNEY_ACCEPTED" and (
        current_round not in by_number or by_number[current_round].get("Result") != "PASS"
    ):
        errors.append("accepted journey state requires a complete current route-faithful round")
    return by_number, errors


def _validate_nonvisual_evidence(path):
    try:
        data = path.read_bytes()
    except OSError:
        return ["non-visual evidence is unreadable"]
    errors = []
    if not data:
        errors.append("non-visual evidence bytes are empty")
    return errors


def _validate_route_evidence(lc, text, summary, required_routes, rounds):
    rows, errors = _rows_with_header_prefix(
        text,
        ("Round", "Journey ID", "Service Route ID"),
        "route-faithful evidence digest",
    )
    evidence_ids = set()
    evidence_paths = set()
    evidence_by_round = {}
    for row in rows:
        try:
            number = int(row.get("Round", ""))
        except (TypeError, ValueError):
            number = -1
        if number not in rounds:
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
        reference = row.get("Evidence path")
        if not SAFE_ID_RE.fullmatch(str(evidence_id or "")):
            errors.append("route evidence ID is missing or malformed")
        if evidence_id in evidence_ids or reference in evidence_paths:
            errors.append("route-faithful acceptance requires unique evidence IDs and paths")
        evidence_ids.add(evidence_id)
        evidence_paths.add(reference)

        authority = route.get("authority") if isinstance(route.get("authority"), dict) else {}
        expected_bindings = {
            "Actor ID": route.get("actor_id"),
            "Authority action ID": authority.get("action_id"),
            "Delegation basis ID": authority.get("delegation_basis_id"),
        }
        for field, value in expected_bindings.items():
            if row.get(field) != value:
                errors.append(field + " disagrees with the adopted route")
        evidence_kind = row.get("Evidence kind")
        route_kind = route.get("route_kind")
        allowed_kinds = set(ROUTE_EVIDENCE_KINDS.get(route_kind, set())) | {
            "AUDIT_EVENT", "SCREENSHOT",
        }
        if evidence_kind not in allowed_kinds:
            errors.append("route evidence kind is invalid for " + str(route_kind))
        result_pair = _split_exact(row.get("Expected / observed route result"), 2)
        if not result_pair or any(not _meaningful(item) for item in result_pair):
            errors.append("route evidence requires meaningful expected and observed route result")
        audit_id = row.get("Audit event ID")
        if evidence_kind == "AUDIT_EVENT":
            if audit_id not in route.get("audit_event_ids", []):
                errors.append("route audit evidence disagrees with the adopted audit lineage")
        elif audit_id != "NOT_APPLICABLE":
            errors.append("non-audit route step must not claim an audit event ID")
        if row.get("Result") not in {"PASS", "DEFECT", "BLOCKED_BY_DEFECT"}:
            errors.append("route evidence result is invalid")

        digest = row.get("Evidence SHA-256", "")
        mode = row.get("Step mode")
        if mode == "VISIBLE":
            path = _safe_reference(lc, reference, screenshot=True)
            if evidence_kind != "SCREENSHOT":
                errors.append("meaningful visible route step requires screenshot evidence")
            if path is None:
                errors.append("screenshot evidence path is outside the journey evidence root or unreadable")
            else:
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
                if not HASH_RE.fullmatch(str(digest)) or digest != actual:
                    errors.append("screenshot digest does not match visible evidence bytes")
        elif mode == "NONVISUAL":
            path = _safe_reference(lc, reference)
            if evidence_kind == "SCREENSHOT":
                errors.append("non-visual route step cannot fabricate screenshot evidence")
            if path is None:
                errors.append("non-visual evidence path is outside the project evidence boundary or unreadable")
            else:
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
                if not HASH_RE.fullmatch(str(digest)) or digest != actual:
                    errors.append("non-visual evidence digest does not match resolved evidence bytes")
                errors.extend(_validate_nonvisual_evidence(path))
        else:
            errors.append("route evidence Step mode must be VISIBLE or NONVISUAL")
        evidence_by_round.setdefault(number, {}).setdefault(key, []).append(row)

    for number, round_row in rounds.items():
        if round_row.get("Result") != "PASS":
            continue
        for key, route in required_routes.items():
            route_rows = evidence_by_round.get(number, {}).get(key, [])
            if not route_rows:
                errors.append("complete round lacks route evidence for " + str(key[1]))
                continue
            route_kind = route.get("route_kind")
            pass_rows = [row for row in route_rows if row.get("Result") == "PASS"]
            kinds = {row.get("Evidence kind") for row in pass_rows}
            required_kinds = set(ROUTE_EVIDENCE_KINDS.get(route_kind, set()))
            expected_audits = route.get("audit_event_ids", [])
            if expected_audits:
                required_kinds.add("AUDIT_EVENT")
            if not required_kinds.issubset(kinds):
                errors.append(
                    str(route_kind) + " complete-round PASS lacks required first-hand evidence kinds"
                )
            actual_audits = [
                row.get("Audit event ID")
                for row in pass_rows if row.get("Evidence kind") == "AUDIT_EVENT"
            ]
            if len(actual_audits) != len(set(actual_audits)) or set(actual_audits) != set(
                expected_audits
            ):
                errors.append("complete-round audit evidence must exactly cover adopted audit event IDs")
            terminal_kind = "SCREENSHOT" if route_kind == "DIRECT_PRODUCT" else "RESULT_DELIVERY"
            final_rows = [row for row in pass_rows if row.get("Evidence kind") == terminal_kind]
            if not any(
                row.get("Human-observable outcome") == route.get("human_observable_outcome")
                for row in final_rows
            ):
                errors.append("route lacks its final human-observable outcome: " + str(key[1]))
    return errors


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
    required_count = len(required_routes)
    if summary.get("required_journey_count") != required_count:
        errors.append("required journey count must equal required delivered route coverage in 4.0")
    if summary.get("state") == "REAL_USER_JOURNEY_ACCEPTED" and summary.get(
        "passed_journey_count"
    ) != required_count:
        errors.append("accepted 4.0 journey summary must pass every required delivered route")
    rounds, round_errors = _validate_route_rounds(text, summary, required_count)
    errors.extend(round_errors)
    errors.extend(_validate_route_evidence(lc, text, summary, required_routes, rounds))
    return errors


def _route_ids_by_kind(project_root, status):
    routes, _, errors = _required_route_map(project_root, status)
    by_id = {}
    for (_, route_id), route in routes.items():
        by_id[route_id] = route
    return by_id, errors


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
    routes, map_errors = _route_ids_by_kind(project_root, status)
    errors.extend(map_errors)
    rows, table_errors = _rows_with_header_prefix(
        text,
        ("Defect ID", "Discovery time / candidate / round / Journey / Route / Step"),
        "route-faithful defect register",
    )
    errors.extend(table_errors)
    ids = []
    states = {state: [] for state in DEFECT_STATES}
    register = {}
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
        if (
            not discovery or not SAFE_ID_RE.fullmatch(discovery[1])
            or not JOURNEY_ID_RE.fullmatch(discovery[3])
            or not STEP_ID_RE.fullmatch(discovery[5])
        ):
            errors.append("defect discovery identity is malformed")
        if route is None:
            errors.append("defect discovery route is not a required delivered adopted route")
        evidence = _split_exact(row.get("Evidence ID / kind / SHA-256"), 3)
        if not evidence or not SAFE_ID_RE.fullmatch(evidence[0]) or not _meaningful(
            evidence[1]
        ) or not HASH_RE.fullmatch(evidence[2]):
            errors.append("defect requires stable route evidence identity, kind, and SHA-256")
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
        if not affected or any(item not in routes for item in affected):
            errors.append("defect affected routes must identify required delivered adopted routes")
        try:
            discovery_round = int(discovery[2]) if discovery else -1
            retest_round = int(row.get("Retest round", ""))
        except (TypeError, ValueError):
            discovery_round, retest_round = -1, -1
        if state == "FIXED_VERIFIED" and (
            row.get("Correction identity / engineering re-verification") in {"", "NOT_APPLICABLE"}
            or retest_round <= discovery_round
        ):
            errors.append("fixed defect requires correction identity and later-round retest evidence")
        if state == "OWNER_EXEMPTED":
            exemption = _split_exact(row.get("Exemption authority / impact / recovery"), 3)
            if not exemption or any(not _meaningful(part) for part in exemption):
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
    if status.get("status_schema_version") not in {"3.0.0", "4.0.0"}:
        return errors
    summary = status.get("real_user_journey_acceptance", {})
    errors.extend(validate_acceptance_record(project_root, status))
    errors.extend(validate_defect_log(project_root, status))
    phase = phase_status.get("phases", {}).get("REAL_USER_JOURNEY_ACCEPTANCE", {})
    if isinstance(summary, dict) and summary.get("state") != "UNPROVED":
        if phase.get("acceptance_record") != summary.get("acceptance_record_reference"):
            errors.append("derived journey acceptance record disagrees with authoritative status")
        if phase.get("defect_log") != summary.get("defect_log_reference"):
            errors.append("derived journey defect log disagrees with authoritative status")
        if phase.get("complete_rounds") != summary.get("complete_round_count"):
            errors.append("derived complete-round count disagrees with authoritative status")
    if status.get("current_phase") == "DELIVERY_PREPARATION" and (
        status.get("phase_gates", {}).get("REAL_USER_JOURNEY_ACCEPTED") != "REAL_USER_JOURNEY_ACCEPTED"
        or not isinstance(summary, dict)
        or summary.get("state") != "REAL_USER_JOURNEY_ACCEPTED"
    ):
        errors.append("Delivery Preparation requires current REAL_USER_JOURNEY_ACCEPTED evidence")
    return errors
