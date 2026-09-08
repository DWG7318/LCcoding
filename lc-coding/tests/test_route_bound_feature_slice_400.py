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
assert hasattr(validator, "validate_phase3_run_slice_binding"), (
    "4.0 route-aware Run/Slice aggregate binding is missing"
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
    "loop_owner_acceptances": [
        "ACCEPTANCE-ROUTE-DIRECT",
        "ACCEPTANCE-ROUTE-AGENT",
        "ACCEPTANCE-ROUTE-CENTER",
    ],
}

CANDIDATE = "CANDIDATE-1 / sha256:" + "a" * 64


WORKFLOWS = [
    {
        "Workflow ID": "WF-APPLICATION",
        "Workflow Capability ID": "CAP-APPLICATION",
        "Implementation status": "IMPLEMENTED",
        "Trigger": "observed authorized application request",
        "Rules / state / side-effect trace": (
            "authoritative application state transition and persisted submission side effect"
        ),
        "Evidence / attestation": "candidate-observed Workflow execution attestation",
        "API contract / evidence": "application API contract presence",
        "MCP contract / evidence": "application MCP contract presence",
    }
]
WORKFLOW_ROUTES = [
    {
        "Service Route ID": route_id,
        "Workflow ID": "WF-APPLICATION",
        "Workflow Capability ID": "CAP-APPLICATION",
    }
    for route_id in ("ROUTE-DIRECT", "ROUTE-AGENT", "ROUTE-CENTER")
]
SURFACES = [
    {
        "Service Route ID": "ROUTE-DIRECT",
        "Service Surface ID": "UI-DIRECT",
        "Service Surface Kind": "DIRECT_PRODUCT",
        "Workflow Capability ID": "CAP-APPLICATION",
    },
    {
        "Service Route ID": "ROUTE-AGENT",
        "Service Surface ID": "AGENT-SERVICE-APPLICATION",
        "Service Surface Kind": "AGENT_SERVICE",
        "Workflow Capability ID": "CAP-APPLICATION",
    },
    {
        "Service Route ID": "ROUTE-AGENT",
        "Service Surface ID": "UI-HUMAN-RESULT",
        "Service Surface Kind": "HUMAN_RESULT_CONSENT_EXCEPTION",
        "Workflow Capability ID": "CAP-APPLICATION",
    },
    {
        "Service Route ID": "ROUTE-CENTER",
        "Service Surface ID": "SERVICE-CENTER-APPLICATION",
        "Service Surface Kind": "ASSISTED_SERVICE",
        "Workflow Capability ID": "CAP-APPLICATION",
    },
    {
        "Service Route ID": "ROUTE-CENTER",
        "Service Surface ID": "UI-CENTER-RESULT",
        "Service Surface Kind": "HUMAN_RESULT_CONSENT_EXCEPTION",
        "Workflow Capability ID": "CAP-APPLICATION",
    },
]
UI_ROWS = [
    {
        "UI ID": ui_id,
        "Subtree path": "ui/" + ui_id.lower(),
        "Component version": "1.0.0",
        "Content hash": "sha256:" + hash_character * 64,
        "Actions / feedback": feedback,
        "Evidence / attestation": attestation,
        "UI change authority": "OWNER_ONLY",
        "Baseline Change Request": "NONE",
    }
    for ui_id, hash_character, feedback, attestation in (
        (
            "UI-DIRECT", "b", "rendered the accepted application result to the human",
            "candidate-observed direct UI result attestation",
        ),
        (
            "UI-HUMAN-RESULT", "c", "delivered the Personal Agent result to the human",
            "candidate-observed Personal Agent human outcome attestation",
        ),
        (
            "UI-CENTER-RESULT", "d", "delivered the assisted result to the human",
            "candidate-observed Service Center human outcome attestation",
        ),
    )
]
SIMULATIONS = [{"Simulation ID": "SIM-APPLICATION"}]
SCENARIOS = [
    {
        "Simulation ID": "SIM-APPLICATION",
        "Scenario ID": "SCENARIO-" + suffix,
        "Actors": actor_id,
        "Path": path,
        "Visible / invisible evidence": result,
        "Used by Slice/Run/Acceptance": "FS-" + suffix,
    }
    for suffix, actor_id, path, result in (
        (
            "DIRECT", "HUMAN-1", "direct entry invoked the authoritative application Workflow",
            "observed direct route result after authoritative state change",
        ),
        (
            "AGENT", "PERSONAL-AGENT-1", "authorized Personal Agent request invoked the application Workflow",
            "observed Personal Agent task result after authoritative state change",
        ),
        (
            "CENTER", "SERVICE-CENTER-ACTOR-1", "delegated assisted request invoked the application Workflow",
            "observed Service Center result after authoritative state change",
        ),
    )
]
SIMULATION_ROUTES = [
    {
        "Service Route ID": "ROUTE-" + suffix,
        "Simulation ID": "SIM-APPLICATION",
        "Workflow Capability ID": "CAP-APPLICATION",
        "Scenario IDs": "SCENARIO-" + suffix,
        "Audit event IDs": audits,
    }
    for suffix, audits in (("DIRECT", "NONE"), ("AGENT", "AUDIT-AGENT"), ("CENTER", "AUDIT-CENTER"))
]
HANDOFF_ROUTES = [
    {
        "Service Route ID": "ROUTE-DIRECT",
        "Workflow Capability ID": "CAP-APPLICATION",
        "Service Surface IDs": "UI-DIRECT",
        "Simulation Scenario IDs": "SCENARIO-DIRECT",
        "Audit event IDs": "NONE",
    },
    {
        "Service Route ID": "ROUTE-AGENT",
        "Workflow Capability ID": "CAP-APPLICATION",
        "Service Surface IDs": "AGENT-SERVICE-APPLICATION, UI-HUMAN-RESULT",
        "Simulation Scenario IDs": "SCENARIO-AGENT",
        "Audit event IDs": "AUDIT-AGENT",
    },
    {
        "Service Route ID": "ROUTE-CENTER",
        "Workflow Capability ID": "CAP-APPLICATION",
        "Service Surface IDs": "SERVICE-CENTER-APPLICATION, UI-CENTER-RESULT",
        "Simulation Scenario IDs": "SCENARIO-CENTER",
        "Audit event IDs": "AUDIT-CENTER",
    },
]


def bound(route_id, evidence_id):
    return "CANDIDATE-1~sha256:" + "a" * 64 + "~" + route_id + "~" + evidence_id


ROUTE_EXECUTION_EVIDENCE_FIELDS = (
    "Promised real entry evidence",
    "Actor / authority evidence",
    "Route adapter / product surface evidence",
    "Shared Workflow capability evidence",
    "Authoritative state / data / side-effect evidence",
    "Route result evidence",
    "Human-observable outcome evidence",
)


def route_fields(route_row, map_hash, execution_reference):
    route_id = route_row["route_id"]
    suffix = route_id.removeprefix("ROUTE-")
    audits = [item for item in route_row["audit_event_ids"] if isinstance(item, str)]
    scenario = next(row for row in SCENARIOS if row["Scenario ID"] == "SCENARIO-" + suffix)
    adapter = next(
        row
        for row in SURFACES
        if row["Service Route ID"] == route_id
        and row["Service Surface ID"] == route_row["adapter_or_surface_id"]
    )
    route_ui = next(
        (
            ui
            for surface in SURFACES
            if surface["Service Route ID"] == route_id
            for ui in UI_ROWS
            if ui["UI ID"] == surface["Service Surface ID"]
        ),
        None,
    )
    fields = {
        "Service topology schema version": "4.0.0",
        "Service Route Map ID / exact hash": "SERVICE-ROUTES-1 / " + map_hash,
        "Service Route ID": route_id,
        "Route kind": route_row["route_kind"],
        "Promised real entry": route_row["promised_entry"],
        "Promised real entry evidence": execution_reference,
        "Actor ID": route_row["actor_id"],
        "Authority action ID": route_row["authority"]["action_id"],
        "Authority resource ID": route_row["authority"]["resource_id"],
        "Delegation basis ID": route_row["authority"]["delegation_basis_id"],
        "Actor / authority evidence": execution_reference,
        "Route adapter / product surface ID": route_row["adapter_or_surface_id"],
        "Route adapter / product surface evidence": execution_reference,
        "Shared Workflow capability ID": route_row["capability_implementation_id"],
        "Shared Workflow capability evidence": execution_reference,
        "Authoritative state / data / side-effect evidence": execution_reference,
        "Route result evidence": execution_reference,
        "Human-observable outcome": route_row["human_observable_outcome"],
        "Human-observable outcome evidence": execution_reference,
        "Audit event IDs": ", ".join(audits) if audits else "NONE",
        "Audit lineage evidence": bound(route_id, "AUDIT") if audits else "NOT_APPLICABLE",
        "Route proof basis": "REAL_ROUTE_EXECUTION",
        "Non-production / simulated / mocked / manually staged evidence used as route proof": "NO",
        "Locked UI touch": "YES" if route_ui else "NO",
        "One-way UI lock evidence": (
            bound(route_id, "UI-LOCK")
            if route_ui
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


def route_run_start_fields(route_row):
    suffix = route_row["route_id"].removeprefix("ROUTE-")
    return {
        "Artifact role": "RUN_START_CONTRACT",
        "Start Contract ID": "START-" + suffix,
        "Start Contract SHA-256": "PENDING",
        "Run ID": "RUN-" + suffix,
        "Status schema version": "4.0.0",
        "LCCoding phase scope": "REAL_PRODUCT_INTEGRATION",
        "Phase-owned objective": route_row["human_observable_outcome"],
        "Evidence return target in calling phase": "FS-" + suffix,
        "Product Baseline trace (REAL_PRODUCT_INTEGRATION only)": "PB-1",
        "Feature Slice ID / version (REAL_PRODUCT_INTEGRATION only)": (
            "FS-" + suffix + " / 4.0.0"
        ),
        "Service Route / Integration Baseline (REAL_PRODUCT_INTEGRATION only)": (
            route_row["route_id"] + " / IB-" + suffix
        ),
    }


def route_receipt_fields(route_row, run_start_hash):
    suffix = route_row["route_id"].removeprefix("ROUTE-")
    scenario_id = "SCENARIO-" + suffix
    required_steps = [
        route_row["route_id"],
        route_row["actor_id"],
        route_row["authority"]["action_id"],
        route_row["authority"]["resource_id"],
    ]
    delegation = route_row["authority"]["delegation_basis_id"]
    if delegation != "NOT_APPLICABLE":
        required_steps.append(delegation)
    required_steps.extend(
        (
            route_row["adapter_or_surface_id"],
            "WF-APPLICATION",
            route_row["capability_implementation_id"],
            scenario_id,
            "D3-" + suffix,
            "ACCEPTANCE-" + route_row["route_id"],
        )
    )
    return {
        "Artifact role": "LOOP_OWNER_ACCEPTANCE_RECEIPT",
        "Acceptance ID": "ACCEPTANCE-" + route_row["route_id"],
        "Run ID": "RUN-" + suffix,
        "Run-start contract ID": "START-" + suffix,
        "Run-start contract SHA-256": run_start_hash,
        "Status schema version": "4.0.0",
        "LCCoding phase scope": "REAL_PRODUCT_INTEGRATION",
        "Phase-owned objective": route_row["human_observable_outcome"],
        "Candidate ID / hash": CANDIDATE,
        "D3 Receipt": "D3-" + suffix,
        "Entry / role / account": " / ".join(
            (route_row["promised_entry"], route_row["actor_id"], route_row["authority"]["resource_id"])
        ),
        "Scenario IDs": scenario_id,
        "Acceptance steps": ", ".join(required_steps),
        "Product questions": "NONE",
        "Prior accepted dependencies reused": "NONE",
        "Invisible risks already verified": "D3-" + suffix,
        "Known limits": "NONE",
        "Evidence return target in the calling phase": "FS-" + suffix,
        "Calling phase gate remains independently evaluated": "YES",
        "Owner result": "LOOP_OWNER_ACCEPTED",
        "Owner Gap ID (blank when accepted)": "",
        "Gap source Acceptance ID": "",
        "Gap source candidate / scenario": "",
        "Gap route": "",
        "Impact / definition reference": "",
        "Correction Run IDs": "",
        "Affected D0-D3 receipts": "",
        "Delta re-verification receipt": "",
        "Delta Owner re-acceptance receipt": "",
        "Gap status": "",
        "Product learning / route (may be blank; only consequential learning that changes a future decision, constraint, check, template, or reuse rule; update one existing canonical artifact)": "",
        "Accepted at": "2026-09-08T00:00:00Z",
    }


def evidence_reference(path, evidence_id):
    lc = next(parent for parent in path.parents if parent.name == ".lccoding")
    return (
        evidence_id
        + " / sha256:"
        + hashlib.sha256(path.read_bytes()).hexdigest()
        + " / "
        + path.relative_to(lc).as_posix()
    )


def validate_fixture(
    route_index, mutate=None, mutate_inputs=None, mutate_map=None, mutate_evidence=None
):
    with tempfile.TemporaryDirectory(prefix="route-slice-400-") as temporary:
        root = Path(temporary)
        lc = root / ".lccoding"
        lc.mkdir()
        route_map = copy.deepcopy(SERVICE_MAP)
        if mutate_map:
            mutate_map(route_map)
        map_path = lc / "SERVICE-ROUTE-MAP.json"
        map_path.write_text(
            json.dumps(route_map, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
        map_hash = "sha256:" + hashlib.sha256(map_path.read_bytes()).hexdigest()
        route_row = route_map["journeys"][0]["routes"][route_index]
        route_id = route_row["route_id"]
        suffix = route_id.removeprefix("ROUTE-")
        evidence_paths = {}
        evidence_references = {}
        for evidence_route in route_map["journeys"][0]["routes"]:
            evidence_suffix = evidence_route["route_id"].removeprefix("ROUTE-")
            run_path = lc / "runs" / ("RUN-" + evidence_suffix) / "RUN-HANDOFF.md"
            run_fields = route_run_start_fields(evidence_route)
            write_record(run_path, "Run Handoff", run_fields)
            run_fields["Start Contract SHA-256"] = validator.canonical_run_start_hash(
                run_path.read_text(encoding="utf-8")
            )
            write_record(run_path, "Run Handoff", run_fields)
            evidence_path = lc / "reviews" / ("OA-" + evidence_suffix + ".md")
            write_record(
                evidence_path,
                "Loop Owner Acceptance Receipt",
                route_receipt_fields(evidence_route, run_fields["Start Contract SHA-256"]),
            )
            evidence_paths[evidence_route["route_id"]] = evidence_path
            evidence_references[evidence_route["route_id"]] = evidence_reference(
                evidence_path, "ACCEPTANCE-" + evidence_route["route_id"]
            )
        common = route_fields(route_row, map_hash, evidence_references[route_id])
        slice_path = lc / "slices" / ("FS-" + suffix + ".md")
        baseline_path = lc / ("INTEGRATION-BASELINE-" + suffix + ".md")
        final_path = lc / ("FINAL-FEATURE-VERIFICATION-" + suffix + ".md")
        slice_fields = {
            "Artifact role": "FEATURE_SLICE_INTEGRATION",
            "Slice ID / version": "FS-" + suffix + " / 4.0.0",
            "Integration Route ID": route_id,
            "Integration candidate ID / exact hash": CANDIDATE,
            "Product Baseline trace": "PB-1",
            "Integration Baseline ID": "IB-" + suffix,
            "Integration Baseline reference": baseline_path.name,
            "Final Feature Verification reference": final_path.name,
            "Required Run IDs": "RUN-" + suffix,
            "Accepted integration candidate / baseline identity": CANDIDATE,
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
        route_surface_ids = {
            row["Service Surface ID"]
            for row in SURFACES
            if row["Service Route ID"] == route_id
        }
        applicable_ui = next(
            (row for row in UI_ROWS if row["UI ID"] in route_surface_ids), None
        )
        if applicable_ui:
            slice_fields["Applicable UI identity"] = (
                "ID:" + applicable_ui["UI ID"]
                + "; PATH:" + applicable_ui["Subtree path"]
                + "; VERSION:" + applicable_ui["Component version"]
                + "; HASH:" + applicable_ui["Content hash"]
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
        records = {
            "slice": slice_fields,
            "baseline": baseline_fields,
            "final": final_fields,
        }
        if mutate:
            mutate(records)
        inputs = {
            "workflow_rows": copy.deepcopy(WORKFLOWS),
            "ui_rows": copy.deepcopy(UI_ROWS),
            "simulation_rows": copy.deepcopy(SIMULATIONS),
            "scenario_rows": copy.deepcopy(SCENARIOS),
            "handoff_fields": {
                "Service Route Map ID / exact hash": "SERVICE-ROUTES-1 / " + map_hash,
            },
            "workflow_route_rows": copy.deepcopy(WORKFLOW_ROUTES),
            "service_surface_rows": copy.deepcopy(SURFACES),
            "simulation_route_rows": copy.deepcopy(SIMULATION_ROUTES),
            "handoff_route_rows": copy.deepcopy(HANDOFF_ROUTES),
        }
        if mutate_inputs:
            mutate_inputs(inputs)
        if mutate_evidence:
            mutate_evidence(lc, records, evidence_paths, evidence_references)
        write_record(slice_path, "Feature Slice", slice_fields)
        write_record(baseline_path, "Integration Baseline", baseline_fields)
        write_record(final_path, "Final Feature Verification", final_fields)
        return validator.validate_real_product_integration(
            lc,
            slice_path,
            slice_fields,
            inputs["workflow_rows"],
            inputs["ui_rows"],
            inputs["simulation_rows"],
            inputs["scenario_rows"],
            inputs["handoff_fields"],
            copy.deepcopy(STATUS_400),
            inputs["workflow_route_rows"],
            inputs["service_surface_rows"],
            inputs["simulation_route_rows"],
            inputs["handoff_route_rows"],
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


def expect_input_error(route_index, mutation, marker):
    errors = validate_fixture(route_index, mutate_inputs=mutation)
    assert any(marker in error for error in errors), (marker, errors)


def expect_evidence_error(route_index, mutation, marker):
    errors = validate_fixture(route_index, mutate_evidence=mutation)
    assert any(marker in error for error in errors), (marker, errors)


def use_other_route_evidence(other_route_index, field):
    def mutate(lc, records, paths, references):
        other_route_id = SERVICE_MAP["journeys"][0]["routes"][other_route_index]["route_id"]
        for record in records.values():
            record[field] = references[other_route_id]
    return mutate


expect_error(
    1,
    lambda records: [record.__setitem__("Route kind", "DIRECT_PRODUCT") for record in records.values()],
    "Route kind mismatch",
)
expect_evidence_error(
    1,
    use_other_route_evidence(0, "Human-observable outcome evidence"),
    "route execution receipt does not belong to the adopted route",
)
expect_error(
    1,
    lambda records: records["slice"].__setitem__("Delegation basis ID", ""),
    "delegation",
)
expect_error(
    1,
    lambda records: [record.__setitem__("Human-observable outcome evidence", "") for record in records.values()],
    "Human-observable outcome",
)
expect_error(
    1,
    lambda records: [
        [record.__setitem__(field, "") for field in ROUTE_EXECUTION_EVIDENCE_FIELDS]
        for record in records.values()
    ],
    "route execution evidence collection must contain resolved runtime results",
)
expect_error(
    1,
    lambda records: [record.__setitem__("Shared Workflow capability ID", "CAP-DIFFERENT") for record in records.values()],
    "same shared Workflow capability",
)
expect_evidence_error(
    2,
    use_other_route_evidence(1, "Route result evidence"),
    "route execution receipt does not belong to the adopted route",
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
expect_error(
    1,
    lambda records: [record.__setitem__("Integration Route ID", "") for record in records.values()],
    "active 4.0 Feature Slice requires Integration Route ID",
)
missing_dispatch_identity_errors = validate_fixture(
    1,
    lambda records: [
        [
            record.__setitem__(field, "")
            for field in (
                "Integration Route ID", "Integration candidate ID / exact hash",
                "Service Route Map ID / exact hash", "Actor ID", "Authority action ID",
                "Authority resource ID", "Delegation basis ID",
            )
        ]
        for record in records.values()
    ],
)
for marker in (
    "Integration Route ID", "candidate ID / exact hash", "Service Route Map ID / exact hash",
    "Actor ID", "Authority action ID", "Authority resource ID", "Delegation basis ID",
):
    assert any(marker in error for error in missing_dispatch_identity_errors), (
        marker, missing_dispatch_identity_errors
    )
expect_error(
    1,
    lambda records: [
        record.__setitem__("Actor / authority evidence", WORKFLOWS[0]["API contract / evidence"])
        for record in records.values()
    ],
    "exact evidence ID / SHA-256 / contained path",
)
expect_error(
    1,
    lambda records: [
        record.__setitem__("Human-observable outcome evidence", "operations log only")
        for record in records.values()
    ],
    "exact evidence ID / SHA-256 / contained path",
)


def substitute_nonexecution_record(role, evidence_id, field):
    def mutate(lc, records, paths, references):
        path = lc / "reviews" / (evidence_id + ".md")
        write_record(
            path,
            role.replace("_", " ").title(),
            {
                "Artifact role": role,
                "Evidence ID": evidence_id,
                "Candidate ID / hash": CANDIDATE,
                "Result": "PASS",
            },
        )
        reference = evidence_reference(path, evidence_id)
        for record in records.values():
            record[field] = reference
    return mutate


expect_evidence_error(
    1,
    substitute_nonexecution_record(
        "AGENT_FAILURE_SIMULATION_EVIDENCE", "SIMULATION-OUTPUT-ONLY", "Route result evidence"
    ),
    "Simulation output is expected behavior, not actual route execution evidence",
)
expect_evidence_error(
    1,
    substitute_nonexecution_record(
        "OPERATIONS_LOG", "OPERATIONS-LOG-ONLY", "Human-observable outcome evidence"
    ),
    "human-observable outcome requires an accepted runtime result record",
)


def missing_evidence_path(lc, records, paths, references):
    missing = "ACCEPTANCE-ROUTE-AGENT / sha256:" + "f" * 64
    missing += " / reviews/missing.md"
    for record in records.values():
        record["Route result evidence"] = missing


expect_evidence_error(1, missing_evidence_path, "route execution evidence path is missing or unreadable")


def mismatched_evidence_hash(lc, records, paths, references):
    stale = references["ROUTE-AGENT"].split(" / ")
    stale[1] = "sha256:" + "0" * 64
    for record in records.values():
        record["Authoritative state / data / side-effect evidence"] = " / ".join(stale)


expect_evidence_error(1, mismatched_evidence_hash, "route execution evidence hash does not match bytes")


def mismatched_record_identity(lc, records, paths, references):
    wrong_id = references["ROUTE-AGENT"].split(" / ")
    wrong_id[0] = "ACCEPTANCE-DIFFERENT"
    for record in records.values():
        record["Promised real entry evidence"] = " / ".join(wrong_id)


expect_evidence_error(1, mismatched_record_identity, "route execution evidence record identity mismatch")


def remove_route_run_start(lc, records, paths, references):
    run_path = lc / "runs" / "RUN-AGENT" / "RUN-HANDOFF.md"
    run_path.unlink()


expect_evidence_error(
    1, remove_route_run_start, "route execution receipt must resolve exactly one canonical Run start"
)


def reorder_route_steps(lc, records, paths, references):
    path = paths["ROUTE-AGENT"]
    fields = validator.parse_markdown_fields_strict(path)[0]
    steps = [item.strip() for item in fields["Acceptance steps"].split(",")]
    steps[0], steps[1] = steps[1], steps[0]
    fields["Acceptance steps"] = ", ".join(steps)
    write_record(path, "Loop Owner Acceptance Receipt", fields)
    reference = evidence_reference(path, fields["Acceptance ID"])
    for record in records.values():
        for field in ROUTE_EXECUTION_EVIDENCE_FIELDS:
            record[field] = reference


expect_evidence_error(
    1, reorder_route_steps, "route execution receipt does not join the ordered route identities"
)
expect_error(
    1,
    lambda records: [
        record.__setitem__("Locked UI touch", "NO")
        or record.__setitem__("One-way UI lock evidence", "NOT_APPLICABLE")
        for record in records.values()
    ],
    "Locked UI touch must equal the adopted route's realized surfaces",
)

expect_input_error(
    1,
    lambda inputs: [
        inputs[name].clear()
        for name in (
            "workflow_rows", "ui_rows", "simulation_rows", "scenario_rows",
            "workflow_route_rows", "service_surface_rows", "simulation_route_rows",
            "handoff_route_rows",
        )
    ],
    "authoritative route evidence join",
)
expect_input_error(
    1,
    lambda inputs: inputs["workflow_route_rows"][1].__setitem__(
        "Workflow Capability ID", "CAP-DIFFERENT"
    ),
    "Workflow route trace",
)

malformed_audit_errors = validate_fixture(
    1,
    mutate_map=lambda route_map: route_map["journeys"][0]["routes"][1][
        "audit_event_ids"
    ].append({"not": "an ID"}),
)
assert any("audit_event_ids must be an array of stable IDs" in error for error in malformed_audit_errors), (
    malformed_audit_errors
)

# Run aggregation is route-aware for 4.0 and exactly UI-bound for 3.0.
run_slice_400 = {
    "Slice ID / version": "FS-AGENT / 4.0.0",
    "Product Baseline trace": "PB-1",
    "Service Route ID": "ROUTE-AGENT",
    "Integration candidate ID / exact hash": CANDIDATE,
    "Accepted integration candidate / baseline identity": CANDIDATE,
    "Integration Baseline ID": "IB-AGENT",
}
run_start_400 = {
    "Feature Slice ID / version (REAL_PRODUCT_INTEGRATION only)": "FS-AGENT / 4.0.0",
    "Product Baseline trace (REAL_PRODUCT_INTEGRATION only)": "PB-1",
    "Service Route / Integration Baseline (REAL_PRODUCT_INTEGRATION only)": (
        "ROUTE-AGENT / IB-AGENT"
    ),
}
assert validator.validate_phase3_run_slice_binding(
    "4.0.0", run_start_400, run_slice_400
) == []
candidate_b_drift = copy.deepcopy(run_slice_400)
candidate_b_drift["Accepted integration candidate / baseline identity"] = (
    "CANDIDATE-B / sha256:" + "b" * 64
)
assert any(
    "accepted integration candidate disagrees" in error
    for error in validator.validate_phase3_run_slice_binding(
        "4.0.0", run_start_400, candidate_b_drift
    )
)
baseline_b_drift = copy.deepcopy(run_start_400)
baseline_b_drift["Service Route / Integration Baseline (REAL_PRODUCT_INTEGRATION only)"] = (
    "ROUTE-AGENT / IB-B"
)
assert any(
    "Integration Baseline disagree" in error
    for error in validator.validate_phase3_run_slice_binding(
        "4.0.0", baseline_b_drift, run_slice_400
    )
)
ui_inventing_start = copy.deepcopy(run_start_400)
ui_inventing_start.pop("Service Route / Integration Baseline (REAL_PRODUCT_INTEGRATION only)")
ui_inventing_start["Applicable UI / Integration Baseline (REAL_PRODUCT_INTEGRATION only)"] = (
    "UI-INVENTED / IB-AGENT"
)
assert validator.validate_phase3_run_slice_binding(
    "4.0.0", ui_inventing_start, run_slice_400
)
legacy_slice = {
    "Slice ID / version": "FS-1 / 3.0.0",
    "Product Baseline trace": "PB-1",
    "Applicable UI subtree ID / path": "UI-1 :: product/ui",
    "Integration Baseline ID": "IB-1",
}
legacy_start = {
    "Feature Slice ID / version (REAL_PRODUCT_INTEGRATION only)": "FS-1 / 3.0.0",
    "Product Baseline trace (REAL_PRODUCT_INTEGRATION only)": "PB-1",
    "Applicable UI / Integration Baseline (REAL_PRODUCT_INTEGRATION only)": "UI-1 / IB-1",
}
assert validator.validate_phase3_run_slice_binding("3.0.0", legacy_start, legacy_slice) == []

print("PASS: 4.0 Feature Slices prove one ordered real chain per required service route")
