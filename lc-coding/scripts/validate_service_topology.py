#!/usr/bin/env python3
from pathlib import Path
import json
import re


CONTRACT_PATH = Path(__file__).resolve().parents[1] / "contracts/service-topology.json"
CONTRACT = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
MAP_FIELDS = set(CONTRACT["map_fields"])
JOURNEY_FIELDS = set(CONTRACT["journey_fields"])
ROUTE_FIELDS = set(CONTRACT["route_fields"])
AUTHORITY_FIELDS = set(CONTRACT["authority_fields"])
CONSENT_FIELDS = set(CONTRACT["consent_fields"])
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
GENERIC_IDS = {
    "",
    "ALL",
    "ANY",
    "GLOBAL",
    "NONE",
    "PENDING",
    "PROJECT-WIDE",
    "UNKNOWN",
    "WILDCARD",
}
APPLICABILITY_VALUES = {"PENDING", "WHOLE_PRODUCT_FIT", "BOUNDED_PRODUCT_FIT"}
STATUS_STRATEGIES = {
    "PENDING",
    "PLATFORM_COMPLETION",
    "AGENT_COLLABORATIVE",
    "MIXED",
}


class DuplicateKeyError(ValueError):
    pass


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _strict_json(path):
    raw = Path(path).read_bytes().decode("utf-8")
    return json.loads(
        raw,
        object_pairs_hook=_pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError("non-finite JSON number: " + value)
        ),
    )


def _closed(value, fields, label, errors):
    if not isinstance(value, dict):
        errors.append(label + " must be an object")
        return {}
    missing = fields - set(value)
    unknown = set(value) - fields
    if missing:
        errors.append(label + " missing fields " + ", ".join(sorted(missing)))
    if unknown:
        errors.append(label + " unknown fields " + ", ".join(sorted(unknown)))
    return value


def _safe_id(value, *, allow_not_applicable=False):
    if allow_not_applicable and value == "NOT_APPLICABLE":
        return True
    return (
        isinstance(value, str)
        and bool(SAFE_ID.fullmatch(value))
        and value.upper() not in GENERIC_IDS
    )


def _id_list(value, label, errors, *, required=False):
    if not isinstance(value, list):
        errors.append(label + " must be an array")
        return []
    if required and not value:
        errors.append(label + " requires at least one evidence ID")
    if any(not _safe_id(item) for item in value):
        errors.append(label + " contains an invalid stable ID")
    if all(isinstance(item, str) for item in value) and len(value) != len(set(value)):
        errors.append(label + " contains duplicate IDs")
    return value


def _meaningful(value):
    return isinstance(value, str) and bool(value.strip()) and value.strip().upper() not in {
        "NONE",
        "NOT_APPLICABLE",
        "PENDING",
        "TBD",
        "TODO",
        "UNKNOWN",
    }


def _validate_status_summary(status):
    errors = []
    for field in CONTRACT["status_summary_fields"]:
        if field not in status:
            errors.append("4.0 status missing service-topology summary " + field)
    if not isinstance(status.get("lccoding_applicability"), str) or status.get(
        "lccoding_applicability"
    ) not in APPLICABILITY_VALUES:
        errors.append("lccoding_applicability is invalid for a 4.0 project")
    if not isinstance(status.get("product_service_strategy"), str) or status.get(
        "product_service_strategy"
    ) not in STATUS_STRATEGIES:
        errors.append("product_service_strategy is invalid for a 4.0 project")
    if not isinstance(status.get("service_route_map"), str) or status.get(
        "service_route_map"
    ) not in CONTRACT["map_states"]:
        errors.append("service_route_map status is invalid for a 4.0 project")
    return errors


def _validate_pending(record, status):
    errors = []
    if record.get("state") != "PENDING":
        return errors
    expected = {
        "map_id": "",
        "project_id": "",
        "primary_strategy": "PENDING",
        "required_coexisting_strategies": [],
        "service_center_applicability": "PENDING",
        "journeys": [],
    }
    if any(record.get(field) != value for field, value in expected.items()):
        errors.append("PENDING Service Route Map cannot claim route decisions or identities")
    if status.get("service_route_map") != "PENDING":
        errors.append("Service Route Map state disagrees with authoritative status")
    return errors


def _validate_route(route, journey, project_id, label, errors):
    route = _closed(route, ROUTE_FIELDS, label, errors)
    for field in (
        "route_id",
        "human_beneficiary_id",
        "actor_id",
        "capability_id",
        "capability_implementation_id",
        "adapter_or_surface_id",
    ):
        if not _safe_id(route.get(field)):
            errors.append(label + " " + field + " requires a stable non-generic ID")

    route_kind = route.get("route_kind")
    if route_kind not in CONTRACT["route_kinds"]:
        errors.append(label + " route_kind is invalid")
    allowed_actors = (
        CONTRACT["route_actor_kinds"].get(route_kind, [])
        if isinstance(route_kind, str)
        else []
    )
    if route.get("actor_kind") not in allowed_actors:
        errors.append(label + " actor_kind is invalid for " + str(route_kind))
    if route.get("support_state") not in CONTRACT["route_support_states"]:
        errors.append(label + " support_state is invalid")
    if route.get("delivery_state") not in CONTRACT["route_delivery_states"]:
        errors.append(label + " delivery_state is invalid")
    if (
        route.get("support_state") in {"UNSUPPORTED", "FUTURE"}
        and route.get("delivery_state") == "DELIVERED"
    ):
        errors.append(label + " unsupported or future route cannot claim DELIVERED")
    if route.get("capability_id") != journey.get("business_capability_id"):
        errors.append(label + " must bind the journey business capability")
    if route.get("capability_implementation_id") != journey.get(
        "shared_capability_implementation_id"
    ):
        errors.append(label + " must bind one shared capability implementation")
    if not _meaningful(route.get("promised_entry")):
        errors.append(label + " promised_entry must name the real route entry")
    if not _meaningful(route.get("human_observable_outcome")):
        errors.append(label + " human_observable_outcome is required")

    authority = _closed(route.get("authority"), AUTHORITY_FIELDS, label + " authority", errors)
    for field in ("action_id", "resource_id"):
        if not _safe_id(authority.get(field)) or authority.get(field) == project_id:
            errors.append(
                label
                + " authority "
                + field
                + " forbids project-wide blanket permission"
            )
    delegation = authority.get("delegation_basis_id")
    if not _safe_id(delegation, allow_not_applicable=True):
        errors.append(label + " authority delegation_basis_id is invalid")

    consent = _closed(route.get("consent"), CONSENT_FIELDS, label + " consent", errors)
    if consent.get("requirement") not in CONTRACT["consent_requirements"]:
        errors.append(label + " consent requirement is invalid")
    if not _safe_id(consent.get("policy_id")):
        errors.append(label + " consent policy_id requires a stable ID")

    required = route.get("support_state") == "REQUIRED"
    _id_list(
        route.get("acceptance_evidence_ids"),
        label + " acceptance_evidence_ids",
        errors,
        required=required,
    )
    audits = _id_list(route.get("audit_event_ids"), label + " audit_event_ids", errors)

    if route_kind in ("PERSONAL_AGENT", "SERVICE_CENTER"):
        if route.get("actor_id") == route.get("human_beneficiary_id"):
            errors.append(label + " delegated actor must not alias the human beneficiary")
        if delegation == "NOT_APPLICABLE":
            errors.append(label + " delegated route requires an attributable delegation basis")
    if route_kind == "SERVICE_CENTER" and (delegation == "NOT_APPLICABLE" or not audits):
        errors.append("Service Center route requires attributable delegation and audit evidence")
    return route


def validate_service_route_map_data(record, status):
    errors = _validate_status_summary(status)
    record = _closed(record, MAP_FIELDS, "Service Route Map", errors)
    if record.get("record_role") != "CALABASH_SERVICE_ROUTE_MAP":
        errors.append("Service Route Map record_role is invalid")
    if record.get("service_topology_schema_version") != "4.0.0":
        errors.append("service_topology_schema_version must be 4.0.0")
    if record.get("state") not in CONTRACT["map_states"]:
        errors.append("Service Route Map state is invalid")
    if record.get("state") == "PENDING":
        return errors + _validate_pending(record, status)

    for field in ("map_id", "project_id"):
        if not _safe_id(record.get(field)):
            errors.append(field + " requires a stable non-generic ID")
    if status.get("project_id") and record.get("project_id") != status.get("project_id"):
        errors.append("Service Route Map project_id disagrees with authoritative status")
    if record.get("state") != status.get("service_route_map"):
        errors.append("Service Route Map state disagrees with authoritative status")
    if status.get("lccoding_applicability") == "PENDING":
        errors.append("DRAFT or ADOPTED Service Route Map requires decided LCCoding applicability")

    primary = record.get("primary_strategy")
    primary_values = set(CONTRACT["primary_strategies"])
    if not isinstance(primary, str) or primary not in primary_values:
        errors.append("primary_strategy is invalid")
    coexisting = record.get("required_coexisting_strategies")
    if not isinstance(coexisting, list):
        errors.append("required_coexisting_strategies must be an array")
        coexisting = []
    elif (
        any(not isinstance(item, str) for item in coexisting)
        or len(coexisting) != len(set(item for item in coexisting if isinstance(item, str)))
        or len(coexisting) > 1
        or any(
            not isinstance(item, str) or item not in primary_values or item == primary
            for item in coexisting
        )
    ):
        errors.append("required_coexisting_strategies is invalid")
        coexisting = []
    selected = (
        {primary} if isinstance(primary, str) and primary in primary_values else set()
    ) | set(coexisting)
    selected_summary = "MIXED" if len(selected) == 2 else primary
    if status.get("product_service_strategy") != selected_summary:
        errors.append("Service Route Map selected strategy disagrees with authoritative status")

    service_center = record.get("service_center_applicability")
    if not isinstance(service_center, str) or service_center not in {
        "APPLICABLE",
        "NOT_APPLICABLE",
    }:
        errors.append("service_center_applicability must be decided before route adoption")
    journeys = record.get("journeys")
    if not isinstance(journeys, list):
        return errors + ["journeys must be an array"]
    if record.get("state") == "ADOPTED" and not journeys:
        errors.append("ADOPTED Service Route Map requires a real business capability journey")

    journey_ids = set()
    route_ids = set()
    journey_route_pairs = set()
    capability_implementations = {}
    required_kinds = set()
    for journey_index, journey_value in enumerate(journeys):
        label = "journey[" + str(journey_index) + "]"
        journey = _closed(journey_value, JOURNEY_FIELDS, label, errors)
        journey_id = journey.get("journey_id")
        if not _safe_id(journey_id):
            errors.append(label + " journey_id requires a stable non-generic ID")
        elif journey_id in journey_ids:
            errors.append("duplicate journey_id " + journey_id)
        if isinstance(journey_id, str):
            journey_ids.add(journey_id)
        if journey.get("journey_class") not in CONTRACT["journey_classes"]:
            errors.append(label + " journey_class is invalid")
        if journey.get("delivery_state") not in CONTRACT["journey_delivery_states"]:
            errors.append(label + " delivery_state is invalid")
        for field in ("business_capability_id", "shared_capability_implementation_id"):
            if not _safe_id(journey.get(field)):
                errors.append(label + " " + field + " requires a stable non-generic ID")
        capability_id = journey.get("business_capability_id")
        implementation_id = journey.get("shared_capability_implementation_id")
        if (
            isinstance(capability_id, str)
            and capability_id in capability_implementations
            and capability_implementations[capability_id] != implementation_id
        ):
            errors.append("one business capability cannot have two capability implementations")
        elif isinstance(capability_id, str):
            capability_implementations[capability_id] = implementation_id

        routes = journey.get("routes")
        if not isinstance(routes, list):
            errors.append(label + " routes must be an array")
            continue
        required_count = 0
        for route_index, route_value in enumerate(routes):
            route_label = label + ".routes[" + str(route_index) + "]"
            route = _validate_route(
                route_value, journey, record.get("project_id"), route_label, errors
            )
            route_id = route.get("route_id")
            if isinstance(route_id, str) and route_id in route_ids:
                errors.append("duplicate route_id " + str(route_id))
            if isinstance(route_id, str):
                route_ids.add(route_id)
            pair = (journey_id, route.get("route_kind"))
            pair_is_stable = all(isinstance(item, str) for item in pair)
            if pair_is_stable and pair in journey_route_pairs:
                errors.append("duplicate journey/route pair " + str(pair))
            if pair_is_stable:
                journey_route_pairs.add(pair)
            if route.get("support_state") == "REQUIRED":
                required_count += 1
                if isinstance(route.get("route_kind"), str):
                    required_kinds.add(route.get("route_kind"))
        if journey.get("delivery_state") == "DELIVERED" and required_count == 0:
            errors.append(label + " delivered journey requires at least one required route")

    if "DIRECT_PRODUCT" in required_kinds and "PLATFORM_COMPLETION" not in selected:
        errors.append("required direct route is inconsistent with selected strategy")
    if "PERSONAL_AGENT" in required_kinds and "AGENT_COLLABORATIVE" not in selected:
        errors.append("required Personal Agent route is inconsistent with selected strategy")
    selected_route_kinds = {
        "PLATFORM_COMPLETION": "DIRECT_PRODUCT",
        "AGENT_COLLABORATIVE": "PERSONAL_AGENT",
    }
    for strategy in selected:
        if selected_route_kinds[strategy] not in required_kinds:
            errors.append("selected strategy has no required route in the Service Route Map")
    if service_center == "APPLICABLE" and "SERVICE_CENTER" not in required_kinds:
        errors.append("Service Center applicability requires a required Service Center route")
    if service_center == "NOT_APPLICABLE" and "SERVICE_CENTER" in required_kinds:
        errors.append("Service Center applicability forbids a required Service Center route")
    return errors


def validate_service_route_map(project_root, status):
    if not isinstance(status, dict) or status.get("status_schema_version") != "4.0.0":
        return []
    path = Path(project_root) / ".lccoding/SERVICE-ROUTE-MAP.json"
    if not path.exists() and not path.is_symlink():
        return ["4.0 project is missing .lccoding/SERVICE-ROUTE-MAP.json"]
    if path.is_symlink() or not path.is_file():
        return ["Service Route Map must be a regular project file"]
    try:
        record = _strict_json(path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        return ["Service Route Map is not strict UTF-8 JSON: " + str(error)]
    return validate_service_route_map_data(record, status)
