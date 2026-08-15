import copy
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import tempfile


ROOT = Path(__file__).resolve().parents[2]
ASSET = ROOT / "lc-coding/bi/release/loop-contract-identities.json"
ASSET_SCHEMA = "LCCODING_BI_COMPATIBILITY_V2"
EXECUTION_METHODS_FRAGMENT_SHA256 = (
    "904a0f8ce8eea72e5d1774b95acaa5239d9a4f1a5b39214eb1c5f91c3b7d054b"
)
TOP_KEYS = {"asset_schema", "status_adapters", "execution_methods"}
STATUS_FIELDS = {
    "status_schema_version",
    "compatibility_status",
    "minimum_bi_version",
    "phase_steps",
}
METHOD_FIELDS = {
    "version",
    "compatibility_status",
    "minimum_bi_version",
    "adapter_schema_kind",
    "normalization_mapping",
    "candidate_commit",
    "manifest_sha256",
    "schema_sha256",
    "template_sha256",
}
LEGACY_PHASES = (
    "INITIAL",
    "PRODUCT_FORMATION",
    "ENGINEERING_RUNS",
    "DELIVERY_PREPARATION",
)
PREPARED_PHASES = (
    "INITIAL",
    "PRODUCT_FORMATION",
    "REAL_PRODUCT_INTEGRATION",
    "DELIVERY_PREPARATION",
)
INITIAL = ["PROPOSAL_READINESS", "PROJECT_INITIALIZATION", "INITIAL_READY"]
DELIVERY = [
    "CENTRALIZED_VULNERABILITY_AUDIT",
    "SECURITY_REMEDIATION",
    "SECURITY_REAUDIT_VULNERABILITY_CLOSURE",
    "POST_SECURITY_OWNER_ACCEPTANCE",
    "DELIVERY_METHOD_QA",
    "DELIVERY_PACKAGE_GUARD_READY",
]
FORMATION_260 = [
    "CALABASH_DRAFT",
    "SIMULATION_WORLD_FOUNDATION",
    "WORKFLOW_CAPABILITY_END",
    "UI_PRODUCT_SURFACE_END",
    "CALABASH_UPGRADE_READY",
]
INTEGRATION_260 = [
    "MANDATORY_CALABASH_UPGRADE",
    "PRODUCT_BASELINE",
    "FEATURE_SLICE_EXECUTION_COVERAGE",
    "UI_LOCKED_INTEGRATION_BASELINE",
    "LOOP_RUN_D0_D3",
    "LOOP_OWNER_ACCEPTANCE",
    "ALL_REQUIRED_RUNS_ACCEPTED",
]
FORMATION_270 = FORMATION_260 + ["MANDATORY_CALABASH_UPGRADE", "PRODUCT_BASELINE"]
INTEGRATION_270 = INTEGRATION_260[2:]
EXPECTED_ADAPTERS = {
    "2.6.0": {
        "status_schema_version": "2.6.0",
        "compatibility_status": "SUPPORTED_LEGACY",
        "minimum_bi_version": "2.6.0",
        "phase_steps": dict(
            zip(LEGACY_PHASES, (INITIAL, FORMATION_260, INTEGRATION_260, DELIVERY))
        ),
    },
    "2.7.0": {
        "status_schema_version": "2.7.0",
        "compatibility_status": "SUPPORTED_LEGACY",
        "minimum_bi_version": "2.7.0",
        "phase_steps": dict(
            zip(LEGACY_PHASES, (INITIAL, FORMATION_270, INTEGRATION_270, DELIVERY))
        ),
    },
    "2.8.0": {
        "status_schema_version": "2.8.0",
        "compatibility_status": "CURRENT",
        "minimum_bi_version": "2.8.0",
        "phase_steps": dict(
            zip(
                PREPARED_PHASES,
                (INITIAL, FORMATION_270, INTEGRATION_270, DELIVERY),
            )
        ),
    },
}
NORMALIZATION = [
    "worker_checker_wake",
    "supervisor_wait",
    "heartbeat",
    "no_subagents",
    "progress",
    "cell_capacity",
    "pin_policy",
]
METHOD_IDENTITIES = {
    "slk": {
        "version": "2.6.0",
        "candidate_commit": "fa75bcf1c0819c8499d3b6c4ee9ec251dae62ae5",
        "manifest_sha256": "b1191453bbedc5b1b8af8327176776602a392913507583bb60bd8ff643a1c339",
        "schema_sha256": "ee3978e0b408e67d69d7f78d94bd31c43d68af2a6d0c7a56966dd9ef93f412c5",
        "template_sha256": "3d9e7f640b6bb0ad2ea168267d7c38fb41e47e098bca4aaae113603352038e73",
        "adapter_schema_kind": "SLK_RUN_RUNTIME_INDEX",
    },
    "clk": {
        "version": "2.5.0",
        "candidate_commit": "6043ce6011b7bb162f8ff6a169b144f4a24fe342",
        "manifest_sha256": "64bbaa4964a56fcafb26eeaed3a912707a20b2ece989cb1a33bdc4240b720b9d",
        "schema_sha256": "c292658717e383dd4c95b54403a0fd2b51a590311cf94f4ef28dc6ddef227867",
        "template_sha256": "b582d667b46eda1b468033c399a38f380a4a291f1aaf5301af749246ebfea5eb",
        "adapter_schema_kind": "CLK_RUN_CONTROL_TRACE",
    },
    "glk": {
        "version": "3.1.0",
        "candidate_commit": "2cbbd20167376e4ce57cd0e3a201e5fdb323c43f",
        "manifest_sha256": "c8d7789f0aa6792379873dc62edb2f6142842cbf2600c079002f44d7755551d7",
        "schema_sha256": "21f33235666394e3c50df3311795cd73093f0b25954e4c40a3d67d1c58a3057b",
        "template_sha256": "0b24cec677f7e008d0959201c9c3117a278378e4c1bf05f0aec6ca7a2dcb46ab",
        "adapter_schema_kind": "GLK_RUN_PACKAGE_INDEX",
    },
}


def validate_asset(asset):
    errors = []
    if not isinstance(asset, dict) or set(asset) != TOP_KEYS:
        return ["top-level shape"]
    if asset["asset_schema"] != ASSET_SCHEMA:
        errors.append("asset schema")
    adapters = asset["status_adapters"]
    if not isinstance(adapters, dict) or set(adapters) != set(EXPECTED_ADAPTERS):
        errors.append("status adapter keys")
    else:
        for version, expected in EXPECTED_ADAPTERS.items():
            record = adapters[version]
            if not isinstance(record, dict) or set(record) != STATUS_FIELDS:
                errors.append(f"{version} fields")
                continue
            if record != expected:
                errors.append(f"{version} content")
            phase_steps = record.get("phase_steps")
            expected_phases = list(expected["phase_steps"])
            if not isinstance(phase_steps, dict) or list(phase_steps) != expected_phases:
                errors.append(f"{version} phases")
                continue
            steps = [step for phase in expected_phases for step in phase_steps[phase]]
            if len(steps) != 21 or len(set(steps)) != 21:
                errors.append(f"{version} steps")
    methods = asset["execution_methods"]
    if not isinstance(methods, dict) or set(methods) != set(METHOD_IDENTITIES):
        errors.append("execution method keys")
    else:
        for method_id, identity in METHOD_IDENTITIES.items():
            record = methods[method_id]
            if not isinstance(record, dict) or set(record) != METHOD_FIELDS:
                errors.append(f"{method_id} fields")
                continue
            if record.get("compatibility_status") != "CURRENT":
                errors.append(f"{method_id} compatibility")
            if record.get("minimum_bi_version") != "2.6.0":
                errors.append(f"{method_id} minimum")
            if record.get("normalization_mapping") != NORMALIZATION:
                errors.append(f"{method_id} normalization")
            for field, expected in identity.items():
                if record.get(field) != expected:
                    errors.append(f"{method_id} {field}")
            if not re.fullmatch(r"[0-9a-f]{40}", str(record.get("candidate_commit", ""))):
                errors.append(f"{method_id} commit")
            for field in ("manifest_sha256", "schema_sha256", "template_sha256"):
                if not re.fullmatch(r"[0-9a-f]{64}", str(record.get(field, ""))):
                    errors.append(f"{method_id} {field} format")
    return errors


def strict_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key: " + key)
        value[key] = item
    return value


def strict_asset(text):
    return json.loads(text, object_pairs_hook=strict_object)


def execution_methods_fragment(raw):
    start = raw.index(b'  "execution_methods": {')
    end = raw.rfind(b"\n  }\n}") + len(b"\n  }")
    return raw[start:end]


def compatibility_candidates(root):
    candidates = []
    for path in root.rglob("*.json"):
        relative = path.relative_to(root).as_posix()
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        keys = set(parsed) if isinstance(parsed, dict) else set()
        name = PurePosixPath(relative).name.casefold()
        if (
            "compatibility" in name
            or "contract-identities" in name
            or keys.intersection(TOP_KEYS)
        ):
            candidates.append(relative)
    return sorted(candidates)


asset_raw = ASSET.read_bytes()
asset = strict_asset(asset_raw.decode("utf-8"))
assert not validate_asset(asset), validate_asset(asset)
assert (
    hashlib.sha256(execution_methods_fragment(asset_raw)).hexdigest()
    == EXECUTION_METHODS_FRAGMENT_SHA256
)


def mutation(mutator):
    changed = copy.deepcopy(asset)
    mutator(changed)
    assert validate_asset(changed), mutator


mutation(lambda x: x.update({"unknown": 1}))
mutation(lambda x: x.pop("asset_schema"))
mutation(lambda x: x.__setitem__("asset_schema", "WRONG"))
mutation(lambda x: x["status_adapters"]["2.6.0"].update({"extra": 1}))
mutation(lambda x: x["status_adapters"]["2.7.0"].pop("minimum_bi_version"))
mutation(lambda x: x["status_adapters"].pop("2.8.0"))
mutation(
    lambda x: x["status_adapters"].update(
        {"2.9.0": copy.deepcopy(x["status_adapters"]["2.8.0"])}
    )
)
mutation(lambda x: x["status_adapters"]["2.6.0"].__setitem__("compatibility_status", "CURRENT"))
mutation(lambda x: x["status_adapters"]["2.7.0"].__setitem__("minimum_bi_version", "2.6.0"))
mutation(lambda x: x["status_adapters"]["2.8.0"].__setitem__("status_schema_version", "2.7.0"))
mutation(lambda x: x["status_adapters"]["2.7.0"].__setitem__("compatibility_status", "CURRENT"))
mutation(lambda x: x["status_adapters"]["2.8.0"].__setitem__("compatibility_status", "PREPARED"))
mutation(lambda x: x["status_adapters"]["2.8.0"].__setitem__("minimum_bi_version", "2.7.0"))
mutation(lambda x: x["status_adapters"]["2.7.0"]["phase_steps"].__setitem__("PRODUCT_FORMATION", FORMATION_260))
mutation(lambda x: x["status_adapters"]["2.7.0"]["phase_steps"].__setitem__("PRODUCT_INTEGRATION", x["status_adapters"]["2.7.0"]["phase_steps"].pop("ENGINEERING_RUNS")))
mutation(lambda x: x["status_adapters"]["2.8.0"]["phase_steps"].__setitem__("ENGINEERING_RUNS", x["status_adapters"]["2.8.0"]["phase_steps"]["REAL_PRODUCT_INTEGRATION"]))
mutation(lambda x: x["status_adapters"]["2.8.0"]["phase_steps"].__setitem__("PRODUCT_INTEGRATION", x["status_adapters"]["2.8.0"]["phase_steps"].pop("REAL_PRODUCT_INTEGRATION")))
mutation(lambda x: x["status_adapters"]["2.6.0"]["phase_steps"]["INITIAL"].append("INITIAL_READY"))
mutation(lambda x: x["status_adapters"]["2.8.0"]["phase_steps"]["INITIAL"].append("NEW_GATE"))
mutation(lambda x: x["status_adapters"]["2.8.0"]["phase_steps"]["PRODUCT_FORMATION"].reverse())
mutation(lambda x: x["execution_methods"].update({"fourth": copy.deepcopy(x["execution_methods"]["slk"])}))
mutation(lambda x: x["execution_methods"].update({"calabash": copy.deepcopy(x["execution_methods"]["slk"])}))
mutation(lambda x: x["execution_methods"]["slk"].update({"extra": 1}))
mutation(lambda x: x["execution_methods"]["clk"].pop("adapter_schema_kind"))
mutation(lambda x: x["execution_methods"]["glk"].__setitem__("version", "latest"))
mutation(lambda x: x["execution_methods"]["slk"].__setitem__("candidate_commit", "HEAD"))
mutation(lambda x: x["execution_methods"]["clk"].__setitem__("manifest_sha256", "0" * 64))
mutation(lambda x: x["execution_methods"]["glk"].__setitem__("adapter_schema_kind", "UNKNOWN"))
mutation(lambda x: x["execution_methods"]["slk"].__setitem__("normalization_mapping", NORMALIZATION[:-1]))
mutation(lambda x: x.update({"slk": copy.deepcopy(x["execution_methods"]["slk"])}))

duplicate = asset_raw.decode("utf-8").replace(
    '  "asset_schema": "LCCODING_BI_COMPATIBILITY_V2",',
    '  "asset_schema": "LCCODING_BI_COMPATIBILITY_V2",\n'
    '  "asset_schema": "LCCODING_BI_COMPATIBILITY_V2",',
    1,
)
try:
    strict_asset(duplicate)
except ValueError as error:
    assert "duplicate JSON key" in str(error)
else:
    raise AssertionError("duplicate JSON must fail closed")

bi_root = ROOT / "lc-coding/bi"
assert compatibility_candidates(bi_root) == ["release/loop-contract-identities.json"]
phase_validator = (ROOT / "lc-coding/scripts/validate_phase_status.py").read_text(
    encoding="utf-8"
)
project_validator = (ROOT / "lc-coding/scripts/validate_project.py").read_text(
    encoding="utf-8"
)
assert phase_validator.count("loop-contract-identities.json") == 1
assert "LEGACY_PHASE_ORDER" not in phase_validator
assert "CURRENT_PHASE_ORDER" not in phase_validator
assert "PROPOSAL_READINESS" not in phase_validator
assert "suffix='REAL_PRODUCT_INTEGRATION' if" not in project_validator

validator_path = ROOT / "lc-coding/scripts/validate_phase_status.py"
validator_spec = importlib.util.spec_from_file_location(
    "lccoding_validate_phase_status_280", validator_path
)
validator = importlib.util.module_from_spec(validator_spec)
validator_spec.loader.exec_module(validator)
assert validator.SCHEMA_PHASE_ORDERS == {
    version: tuple(record["phase_steps"])
    for version, record in EXPECTED_ADAPTERS.items()
}
assert validator.SCHEMA_STEP_IDENTITIES == {
    version: tuple(
        step
        for phase_steps in record["phase_steps"].values()
        for step in phase_steps
    )
    for version, record in EXPECTED_ADAPTERS.items()
}


def production_loader_rejects(body):
    original = validator.COMPATIBILITY_ASSET_PATH
    try:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "loop-contract-identities.json"
            if body is not None:
                path.write_text(body, encoding="utf-8", newline="\n")
            validator.COMPATIBILITY_ASSET_PATH = path
            try:
                validator._load_compatibility_layout()
            except RuntimeError:
                pass
            else:
                raise AssertionError("invalid fixed compatibility asset must fail closed")
    finally:
        validator.COMPATIBILITY_ASSET_PATH = original


production_loader_rejects(None)
production_loader_rejects("{")
production_loader_rejects(duplicate)
for mutator in [
    lambda x: x["status_adapters"].pop("2.8.0"),
    lambda x: x["status_adapters"].update(
        {"2.9.0": copy.deepcopy(x["status_adapters"]["2.8.0"])}
    ),
    lambda x: x["status_adapters"]["2.8.0"].__setitem__(
        "compatibility_status", "PREPARED"
    ),
    lambda x: x["status_adapters"]["2.8.0"]["phase_steps"].__setitem__(
        "ENGINEERING_RUNS",
        x["status_adapters"]["2.8.0"]["phase_steps"].pop(
            "REAL_PRODUCT_INTEGRATION"
        ),
    ),
    lambda x: x["status_adapters"]["2.8.0"]["phase_steps"][
        "PRODUCT_FORMATION"
    ].reverse(),
    lambda x: x["execution_methods"].update(
        {"calabash": copy.deepcopy(x["execution_methods"]["slk"])}
    ),
    lambda x: x["execution_methods"]["slk"].update({"extra": 1}),
]:
    changed = copy.deepcopy(asset)
    mutator(changed)
    production_loader_rejects(json.dumps(changed))
with tempfile.TemporaryDirectory() as temporary:
    shadow_root = Path(temporary)
    first = shadow_root / "release/loop-contract-identities.json"
    first.parent.mkdir(parents=True)
    first.write_text(json.dumps(asset), encoding="utf-8")
    second = shadow_root / "other/compatibility.json"
    second.parent.mkdir(parents=True)
    second.write_text(json.dumps(asset), encoding="utf-8")
    assert len(compatibility_candidates(shadow_root)) == 2

print("PASS: BI compatibility has one closed status and execution-method asset")
