#!/usr/bin/env python3
"""Validate LCCoding 3.0 visible, screenshot-backed user-journey evidence."""

from __future__ import annotations

import hashlib
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


def validate_acceptance_record(project_root: Path, status: dict) -> list[str]:
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


def validate_defect_log(project_root: Path, status: dict) -> list[str]:
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


def validate_real_user_journey(project_root: Path, status: dict, phase_status: dict) -> list[str]:
    errors = validate_status_summary(status)
    if status.get("status_schema_version") != "3.0.0":
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
