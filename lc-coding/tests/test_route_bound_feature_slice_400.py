from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import tempfile


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "lc-coding/scripts/validate_project.py"

spec = importlib.util.spec_from_file_location("validate_project", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


TEMPLATE_MARKERS = {
    "lc-coding/references/feature-slice-and-integration.md": (
        "promised real entry",
        "human-observable",
        "API or MCP presence alone",
    ),
    "lc-coding/templates/FEATURE-SLICE.md": (
        "- Service Route Map ID / exact hash:",
        "- Promised real entry evidence:",
        "- Human-observable outcome evidence:",
    ),
    "lc-coding/templates/INTEGRATION-BASELINE.md": (
        "- Service Route Map ID / exact hash:",
        "- Route proof basis:",
    ),
    "lc-coding/templates/FINAL-FEATURE-VERIFICATION.md": (
        "- Service Route Map ID / exact hash:",
        "- Human-observable outcome evidence:",
    ),
}
for relative, markers in TEMPLATE_MARKERS.items():
    text = (ROOT / relative).read_text(encoding="utf-8")
    for marker in markers:
        assert marker in text, (relative, marker)

assert hasattr(validator, "validate_route_bound_feature_slice"), (
    "4.0 route-bound Feature Slice validator is missing"
)


def route(route_id, route_kind, actor_id, actor_kind, delegation, surface_id, audits):
    return {
        "route_id": route_id,
        "route_kind": route_kind,
        "support_state": "REQUIRED",
        "delivery_state": "UNPROVED",
        "human_beneficiary_id": "HUMAN-1",
        "actor_id": actor_id,
        "actor_kind": actor_kind,
        "capability_id": "BUSINESS-APPLICATION",
        "capability_implementation_id": "CAP-APPLICATION",
        "promised_entry": "application submission entry",
        "human_observable_outcome": "human sees the application result",
        "authority": {
            "action_id": "ACTION-" + route_id,
            "resource_id": "RESOURCE-APPLICATION",
            "delegation_basis_id": delegation,
        },
        "consent": {
            "requirement": "NOT_REQUIRED" if route_kind == "DIRECT_PRODUCT" else "REQUIRED",
            "policy_id": "POLICY-" + route_id,
        },
        "adapter_or_surface_id": surface_id,
        "acceptance_evidence_ids": ["ACCEPTANCE-" + route_id],
        "audit_event_ids": audits,
    }


SERVICE_MAP = {
    "record_role": "CALABASH_SERVICE_ROUTE_MAP",
    "service_topology_schema_version": "4.0.0",
    "map_id": "SERVICE-ROUTES-1",
    "project_id": "PROJECT-1",
    "state": "ADOPTED",
    "primary_strategy": "AGENT_COLLABORATIVE",
    "required_coexisting_strategies": ["PLATFORM_COMPLETION"],
    "service_center_applicability": "APPLICABLE",
    "journeys": [
        {
            "journey_id": "JOURNEY-APPLICATION",
            "journey_class": "CORE",
            "delivery_state": "PLANNED",
            "business_capability_id": "BUSINESS-APPLICATION",
            "shared_capability_implementation_id": "CAP-APPLICATION",
            "routes": [
                route(
                    "ROUTE-DIRECT", "DIRECT_PRODUCT", "HUMAN-1", "HUMAN_PRINCIPAL",
                    "NOT_APPLICABLE", "UI-DIRECT", [],
                ),
                route(
                    "ROUTE-AGENT", "PERSONAL_AGENT", "PERSONAL-AGENT-1", "PERSONAL_AGENT",
                    "DELEGATION-AGENT-1", "AGENT-SERVICE-APPLICATION", ["AUDIT-AGENT"],
                ),
                route(
                    "ROUTE-CENTER", "SERVICE_CENTER", "SERVICE-CENTER-ACTOR-1",
                    "SERVICE_CENTER_ACTOR", "DELEGATION-CENTER-1",
                    "SERVICE-CENTER-APPLICATION", ["AUDIT-CENTER"],
                ),
            ],
        }
    ],
}

STATUS_400 = {
    "status_schema_version": "4.0.0",
    "project_id": "PROJECT-1",
    "service_route_map": "ADOPTED",
}

CANDIDATE = "CANDIDATE-1 / sha256:" + "a" * 64


def bound(route_id, evidence_id):
    return "CANDIDATE-1~sha256:" + "a" * 64 + "~" + route_id + "~" + evidence_id


def route_fields(route_row, map_hash):
    route_id = route_row["route_id"]
    audits = route_row["audit_event_ids"]
    fields = {
        "Service topology schema version": "4.0.0",
        "Service Route Map ID / exact hash": "SERVICE-ROUTES-1 / " + map_hash,
        "Service Route ID": route_id,
        "Route kind": route_row["route_kind"],
        "Promised real entry": route_row["promised_entry"],
        "Promised real entry evidence": bound(route_id, "ENTRY"),
        "Actor ID": route_row["actor_id"],
        "Authority action ID": route_row["authority"]["action_id"],
        "Authority resource ID": route_row["authority"]["resource_id"],
        "Delegation basis ID": route_row["authority"]["delegation_basis_id"],
        "Actor / authority evidence": bound(route_id, "AUTHORITY"),
        "Route adapter / product surface ID": route_row["adapter_or_surface_id"],
        "Route adapter / product surface evidence": bound(route_id, "SURFACE"),
        "Shared Workflow capability ID": route_row["capability_implementation_id"],
        "Shared Workflow capability evidence": bound(route_id, "WORKFLOW"),
        "Authoritative state / data / side-effect evidence": bound(route_id, "EFFECT"),
        "Route result evidence": bound(route_id, "ROUTE-RESULT"),
        "Human-observable outcome": route_row["human_observable_outcome"],
        "Human-observable outcome evidence": bound(route_id, "HUMAN-OUTCOME"),
        "Audit event IDs": ", ".join(audits) if audits else "NONE",
        "Audit lineage evidence": bound(route_id, "AUDIT") if audits else "NOT_APPLICABLE",
        "Route proof basis": "REAL_ROUTE_EXECUTION",
        "Non-production / simulated / mocked / manually staged evidence used as route proof": "NO",
        "Locked UI touch": "YES" if route_row["route_kind"] == "DIRECT_PRODUCT" else "NO",
        "One-way UI lock evidence": (
            bound(route_id, "UI-LOCK")
            if route_row["route_kind"] == "DIRECT_PRODUCT"
            else "NOT_APPLICABLE"
        ),
    }
    return fields


def write_record(path, title, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "# " + title + "\n\n" + "\n".join(
        "- " + key + ": " + str(value) for key, value in fields.items()
    ) + "\n"
    path.write_text(body, encoding="utf-8", newline="\n")


def validate_fixture(route_index, mutate=None):
    with tempfile.TemporaryDirectory(prefix="route-slice-400-") as temporary:
        root = Path(temporary)
        lc = root / ".lccoding"
        lc.mkdir()
        map_path = lc / "SERVICE-ROUTE-MAP.json"
        map_path.write_text(
            json.dumps(SERVICE_MAP, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
        map_hash = "sha256:" + hashlib.sha256(map_path.read_bytes()).hexdigest()
        route_row = SERVICE_MAP["journeys"][0]["routes"][route_index]
        common = route_fields(route_row, map_hash)
        route_id = route_row["route_id"]
        suffix = route_id.removeprefix("ROUTE-")
        slice_path = lc / "slices" / ("FS-" + suffix + ".md")
        baseline_path = lc / ("INTEGRATION-BASELINE-" + suffix + ".md")
        final_path = lc / ("FINAL-FEATURE-VERIFICATION-" + suffix + ".md")
        slice_fields = {
            "Artifact role": "FEATURE_SLICE_INTEGRATION",
            "Slice ID / version": "FS-" + suffix + " / 4.0.0",
            "Integration Route ID": route_id,
            "Integration candidate ID / exact hash": CANDIDATE,
            "Integration Baseline ID": "IB-" + suffix,
            "Integration Baseline reference": baseline_path.name,
            "Final Feature Verification reference": final_path.name,
            "Required Run IDs": "RUN-" + suffix,
            "D0-D3 evidence plan": bound(route_id, "D0-D3-PLAN"),
            "Normal Loop Owner Acceptance route(s)": bound(route_id, "OWNER-ROUTE"),
            **copy.deepcopy(common),
        }
        baseline_fields = {
            "Artifact role": "INTEGRATION_BASELINE",
            "Baseline ID": "IB-" + suffix,
            "Feature Slice reference": "slices/" + slice_path.name,
            "Slice ID / version": slice_fields["Slice ID / version"],
            "Integration Route ID": route_id,
            "Integration candidate ID / exact hash": CANDIDATE,
            **copy.deepcopy(common),
        }
        final_fields = {
            "Artifact role": "FINAL_FEATURE_VERIFICATION",
            "Verification ID": "VERIFY-" + suffix,
            "Slice ID / version": slice_fields["Slice ID / version"],
            "Integration Route ID": route_id,
            "Integration candidate ID / exact hash": CANDIDATE,
            "Integration Baseline ID / reference": "IB-" + suffix + " / " + baseline_path.name,
            "D3 / Loop Owner Acceptance evidence": (
                "D3:" + bound(route_id, "D3") + "; OWNER:" + bound(route_id, "OWNER")
            ),
            "Final verdict": "PASS",
            **copy.deepcopy(common),
        }
        ui_rows = []
        if route_row["route_kind"] == "DIRECT_PRODUCT":
            slice_fields["Applicable UI identity"] = (
                "ID:UI-DIRECT; PATH:ui/direct; VERSION:1.0.0; HASH:sha256:" + "b" * 64
            )
            baseline_fields.update(
                {
                    "Lock authority": "ONE_WAY_OWNER_AUTHORITY",
                    "System autonomous UI modification": "FORBIDDEN",
                    "Owner-initiated / Owner-approved UI change route": "BASELINE_CHANGE_REQUEST",
                    "UI change disposition": "UNCHANGED",
                    "Baseline Change Request reference": "NONE",
                    "Prior Integration Baseline ID": "NOT_APPLICABLE",
                }
            )
            ui_rows = [
                {
                    "UI ID": "UI-DIRECT",
                    "UI change authority": "OWNER_ONLY",
                    "Baseline Change Request": "NONE",
                }
            ]
        records = {
            "slice": slice_fields,
            "baseline": baseline_fields,
            "final": final_fields,
        }
        if mutate:
            mutate(records)
        write_record(slice_path, "Feature Slice", slice_fields)
        write_record(baseline_path, "Integration Baseline", baseline_fields)
        write_record(final_path, "Final Feature Verification", final_fields)
        return validator.validate_real_product_integration(
            lc,
            slice_path,
            slice_fields,
            [],
            ui_rows,
            [],
            [],
            {},
            copy.deepcopy(STATUS_400),
        )


# One real, ordered, candidate/route-bound Slice per required service route.
for route_index in range(3):
    positive_errors = validate_fixture(route_index)
    assert positive_errors == [], (
        SERVICE_MAP["journeys"][0]["routes"][route_index], positive_errors
    )

# Exact 3.0 validation remains selected independently and gains no 4.0 requirements.
assert validator.validate_route_bound_feature_slice(
    Path("missing"), {"status_schema_version": "3.0.0"}, None, {}, None, {}, None, {}
) == []


def expect_error(route_index, mutation, marker):
    errors = validate_fixture(route_index, mutation)
    assert any(marker in error for error in errors), (marker, errors)


expect_error(
    1,
    lambda records: [record.__setitem__("Route kind", "DIRECT_PRODUCT") for record in records.values()],
    "Route kind mismatch",
)
expect_error(
    1,
    lambda records: [
        record.__setitem__("Human-observable outcome evidence", bound("ROUTE-DIRECT", "UI-PASS"))
        for record in records.values()
    ],
    "another route",
)
expect_error(
    1,
    lambda records: records["slice"].__setitem__("Delegation basis ID", ""),
    "delegation",
)
expect_error(
    1,
    lambda records: [record.__setitem__("Human-observable outcome evidence", "") for record in records.values()],
    "human-observable outcome",
)
expect_error(
    1,
    lambda records: [record.__setitem__("Shared Workflow capability ID", "CAP-DIFFERENT") for record in records.values()],
    "same shared Workflow capability",
)
expect_error(
    2,
    lambda records: [
        record.__setitem__("Route result evidence", bound("ROUTE-AGENT", "AGENT-RESULT"))
        for record in records.values()
    ],
    "another route",
)
expect_error(
    1,
    lambda records: [record.__setitem__("Route proof basis", "DIRECT_UI_PASS") for record in records.values()],
    "API/MCP presence or another route's UI PASS",
)
expect_error(
    0,
    lambda records: [record.__setitem__("Route proof basis", "API_MCP_PRESENCE_ONLY") for record in records.values()],
    "API/MCP presence or another route's UI PASS",
)
expect_error(
    1,
    lambda records: [
        record.__setitem__(
            "Non-production / simulated / mocked / manually staged evidence used as route proof", "YES"
        )
        for record in records.values()
    ],
    "simulation, mock, or manually staged state",
)
expect_error(
    0,
    lambda records: records["final"].__setitem__("Route kind", "PERSONAL_AGENT"),
    "identity drift",
)
expect_error(
    0,
    lambda records: records["baseline"].__setitem__("Lock authority", "AGENT_MUTABLE"),
    "Lock authority must be ONE_WAY_OWNER_AUTHORITY",
)
expect_error(
    0,
    lambda records: [
        record.__setitem__(
            "Service Route Map ID / exact hash", "SERVICE-ROUTES-1 / sha256:" + "0" * 64
        )
        for record in records.values()
    ],
    "Service Route Map identity/hash drift",
)

print("PASS: 4.0 Feature Slices prove one ordered real chain per required service route")
