use lccoding::projection::load_loop_governance;
use lccoding::records::compatibility::{embedded_compatibility_asset, parse_compatibility_asset};
use lccoding::records::loops::{
    GlkArtifact, GovernanceStatus, parse_clk_governance, parse_glk_governance, parse_slk_governance,
};
use lccoding::records::manifest::parse_manifest;
use lccoding::records::status::parse_status;
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::fs;
use std::time::{SystemTime, UNIX_EPOCH};

const SLK: &str = include_str!("../../tests/fixtures/slk-run-runtime-index.json");

const CLK: &str = r#"
trace_type: CLK_RUN_CONTROL_TRACE
version: 2.5.0
clock_mode: INJECTED_MINUTES
run: {run_id: RUN-001, state: RUNNING, terminal_confirmed: false}
required_sets: [{required_go_ids: [GO-1, GO-2]}]
device_capacity_profile: {version: DEVICE-1}
engineering_load_snapshots: [{version: LOAD-1}]
cell_capacity_gates: [{result: PASS}]
method_role_capabilities:
  - {role_kind: SUPERVISOR, set_thread_pinned: false}
  - {role_kind: CHECKER, set_thread_pinned: false}
  - {role_kind: WORKER, set_thread_pinned: false}
  - {role_kind: VERIFICATION, set_thread_pinned: false}
pin_observations: []
worker_bindings: [{worker_id: WORKER-1}]
patrols:
  - {interval_minutes: 15, heartbeat_count: 1, heartbeat_state: ACTIVE, set_thread_pinned: false}
events:
  - {action: WAKE_ATTEMPT, data: {level: 1}}
  - {action: WAKE_ATTEMPT, data: {level: 2}}
  - {action: WAKE_ATTEMPT, data: {level: 3}}
  - {action: WAKE_ATTEMPT, data: {level: 4}}
  - {action: WAKE_ACK, data: {}}
  - {action: PATROL_STATUS, data: {status: CLEAR, checks: [SUPERVISOR_WAIT, SUBAGENT_EVIDENCE, THREAD_PIN_PROVENANCE]}}
  - {action: SUPERVISOR_PROGRESS, data: {current_level_verified_go_count: 1, current_level_required_go_total: 2}}
"#;

const GLK_INDEX: &str = r#"
schema_version: 3.1.0
artifact_type: RUN_PACKAGE_INDEX
formal_artifacts:
{entries}
"#;

const GLK_MONITOR: &str = r#"
schema_version: 3.1.0
artifact_type: MONITOR_CONTROL
patrol_interval_minutes: 15
monitor_state: MONITOR_ACTIVE
patrol_checklist:
  - {check_id: SUPERVISOR_WAIT, result: CLEAR}
  - {check_id: SUBAGENT_EVIDENCE, result: CLEAR}
  - {check_id: THREAD_PIN, result: CLEAR}
  - {check_id: TERMINAL_CLOSURE, result: CLEAR}
  - {check_id: PENDING_WAKE, result: CLEAR}
  - {check_id: PATROL_UNIQUENESS, result: CLEAR}
  - {check_id: UNEXPLAINED_STALL, result: CLEAR}
"#;

const GLK_PROGRESS: &str = r#"
schema_version: 3.1.0
artifact_type: CHECKER_PROGRESS_EVENT
accepted_cell_count: 1
required_cell_count: 2
"#;

const GLK_CAPACITY: &str = r#"
schema_version: 3.1.0
artifact_type: CELL_CAPACITY_GATE
result: PASS
"#;

const GLK_WAKE_1: &str = "schema_version: 3.1.0\nartifact_type: WAKE_ATTEMPT\nlevel: 1\ntimeout_seconds: 120\noutcome: ACKNOWLEDGED\n";
const GLK_WAKE_2: &str = "schema_version: 3.1.0\nartifact_type: WAKE_ATTEMPT\nlevel: 2\ntimeout_seconds: 120\noutcome: ACKNOWLEDGED\n";
const GLK_WAKE_3: &str = "schema_version: 3.1.0\nartifact_type: WAKE_ATTEMPT\nlevel: 3\ntimeout_seconds: 120\noutcome: ACKNOWLEDGED\n";
const GLK_WAKE_4: &str = "schema_version: 3.1.0\nartifact_type: WAKE_ATTEMPT\nlevel: 4\ntimeout_seconds: 120\noutcome: ACKNOWLEDGED\n";

fn sha(body: &str) -> String {
    format!("{:x}", Sha256::digest(body.as_bytes()))
}

fn glk_fixture() -> (String, Vec<GlkArtifact<'static>>) {
    let bodies = [
        (
            "governance/MONITOR_CONTROL.yaml",
            "MONITOR_CONTROL",
            GLK_MONITOR,
        ),
        (
            "governance/CHECKER_PROGRESS_EVENT.yaml",
            "CHECKER_PROGRESS_EVENT",
            GLK_PROGRESS,
        ),
        (
            "governance/CELL_CAPACITY_GATE.yaml",
            "CELL_CAPACITY_GATE",
            GLK_CAPACITY,
        ),
        (
            "governance/WAKE_ATTEMPT-L1.yaml",
            "WAKE_ATTEMPT",
            GLK_WAKE_1,
        ),
        (
            "governance/WAKE_ATTEMPT-L2.yaml",
            "WAKE_ATTEMPT",
            GLK_WAKE_2,
        ),
        (
            "governance/WAKE_ATTEMPT-L3.yaml",
            "WAKE_ATTEMPT",
            GLK_WAKE_3,
        ),
        (
            "governance/WAKE_ATTEMPT-L4.yaml",
            "WAKE_ATTEMPT",
            GLK_WAKE_4,
        ),
    ];
    let entries = bodies
        .iter()
        .map(|(path, kind, body)| {
            format!(
                "  - {{path: {path}, sha256: {}, artifact_type: {kind}}}",
                sha(body)
            )
        })
        .collect::<Vec<_>>()
        .join("\n");
    let artifacts = bodies
        .iter()
        .map(|(path, kind, body)| GlkArtifact {
            path,
            artifact_type: kind,
            body,
        })
        .collect();
    (GLK_INDEX.replace("{entries}", &entries), artifacts)
}

fn statuses(summary: &lccoding::records::loops::GovernanceSummary) -> Vec<GovernanceStatus> {
    summary.metrics.iter().map(|metric| metric.status).collect()
}

fn raw_compatibility_asset() -> Value {
    serde_json::from_str(include_str!("../../release/loop-contract-identities.json")).unwrap()
}

fn v2_compatibility_asset() -> Value {
    let mut asset = raw_compatibility_asset();
    if asset["asset_schema"] == "LCCODING_BI_COMPATIBILITY_V2" {
        assert!(asset["status_adapters"].get("2.8.0").is_some());
        return asset;
    }
    assert_eq!(asset["asset_schema"], "LCCODING_BI_COMPATIBILITY_V1");
    asset["asset_schema"] = Value::String("LCCODING_BI_COMPATIBILITY_V2".into());
    asset["status_adapters"]["2.7.0"]["compatibility_status"] =
        Value::String("SUPPORTED_LEGACY".into());
    let mut current = asset["status_adapters"]["2.7.0"].clone();
    current["status_schema_version"] = Value::String("2.8.0".into());
    current["compatibility_status"] = Value::String("CURRENT".into());
    current["minimum_bi_version"] = Value::String("2.8.0".into());
    let integration = current["phase_steps"]
        .as_object_mut()
        .unwrap()
        .remove("ENGINEERING_RUNS")
        .unwrap();
    current["phase_steps"]["REAL_PRODUCT_INTEGRATION"] = integration;
    asset["status_adapters"]["2.8.0"] = current;
    asset
}

fn v1_compatibility_asset() -> Value {
    let mut asset = raw_compatibility_asset();
    asset["asset_schema"] = Value::String("LCCODING_BI_COMPATIBILITY_V1".into());
    asset["status_adapters"]
        .as_object_mut()
        .unwrap()
        .remove("2.8.0");
    asset["status_adapters"]["2.7.0"]["compatibility_status"] = Value::String("CURRENT".into());
    asset
}

fn rejects_mutation(change: impl FnOnce(&mut Value)) {
    let mut asset = raw_compatibility_asset();
    change(&mut asset);
    assert!(parse_compatibility_asset(&serde_json::to_string(&asset).unwrap()).is_err());
}

fn rejects_v2_mutation(change: impl FnOnce(&mut Value)) {
    let mut asset = v2_compatibility_asset();
    change(&mut asset);
    assert!(parse_compatibility_asset(&serde_json::to_string(&asset).unwrap()).is_err());
}

fn rust_sources(root: &std::path::Path) -> Vec<String> {
    fs::read_dir(root)
        .unwrap()
        .flat_map(|entry| {
            let path = entry.unwrap().path();
            if path.is_dir() {
                rust_sources(&path)
            } else if path.extension().and_then(|value| value.to_str()) == Some("rs") {
                vec![fs::read_to_string(path).unwrap()]
            } else {
                Vec::new()
            }
        })
        .collect()
}

#[test]
fn embedded_execution_method_identities_match_the_single_asset() {
    let raw = raw_compatibility_asset();
    let parsed = embedded_compatibility_asset().unwrap();
    let mapping = [
        "worker_checker_wake",
        "supervisor_wait",
        "heartbeat",
        "no_subagents",
        "progress",
        "cell_capacity",
        "pin_policy",
    ];

    assert_eq!(raw["asset_schema"], "LCCODING_BI_COMPATIBILITY_V2");
    for method_id in ["slk", "clk", "glk"] {
        let expected = &raw["execution_methods"][method_id];
        let actual = parsed.execution_method(method_id).unwrap();
        assert_eq!(actual.version, expected["version"].as_str().unwrap());
        assert_eq!(
            actual.compatibility_status,
            expected["compatibility_status"].as_str().unwrap()
        );
        assert_eq!(
            actual.minimum_bi_version,
            expected["minimum_bi_version"].as_str().unwrap()
        );
        assert_eq!(
            actual.adapter_schema_kind,
            expected["adapter_schema_kind"].as_str().unwrap()
        );
        assert_eq!(actual.normalization_mapping, mapping);
        assert_eq!(
            actual.candidate_commit,
            expected["candidate_commit"].as_str().unwrap()
        );
        assert_eq!(
            actual.manifest_sha256,
            expected["manifest_sha256"].as_str().unwrap()
        );
        assert_eq!(
            actual.schema_sha256,
            expected["schema_sha256"].as_str().unwrap()
        );
        assert_eq!(
            actual.template_sha256,
            expected["template_sha256"].as_str().unwrap()
        );
    }
    assert!(parsed.execution_method("calabash").is_none());
}

#[test]
fn compatibility_asset_v2_is_strictly_current_in_memory_without_identity_drift() {
    let v1 = v1_compatibility_asset();
    let v2 = v2_compatibility_asset();
    assert!(parse_compatibility_asset(&serde_json::to_string(&v1).unwrap()).is_ok());
    let parsed = parse_compatibility_asset(&serde_json::to_string(&v2).unwrap()).unwrap();
    assert_eq!(v2["asset_schema"], "LCCODING_BI_COMPATIBILITY_V2");
    assert_eq!(v2["execution_methods"], v1["execution_methods"]);
    assert_eq!(
        v2["status_adapters"]["2.7.0"]["compatibility_status"],
        "SUPPORTED_LEGACY"
    );
    assert_eq!(
        v2["status_adapters"]["2.8.0"]["compatibility_status"],
        "CURRENT"
    );
    let phases = parsed.status_phase_steps("2.8.0").unwrap();
    assert_eq!(
        phases
            .iter()
            .map(|phase| phase.phase_id)
            .collect::<Vec<_>>(),
        [
            "INITIAL",
            "PRODUCT_FORMATION",
            "REAL_PRODUCT_INTEGRATION",
            "DELIVERY_PREPARATION",
        ]
    );
    assert_eq!(
        phases
            .iter()
            .map(|phase| phase.step_ids.len())
            .collect::<Vec<_>>(),
        [3, 7, 5, 6]
    );
    for phase in phases {
        assert_eq!(
            Value::Array(phase.step_ids.into_iter().map(Value::String).collect()),
            v2["status_adapters"]["2.8.0"]["phase_steps"][phase.phase_id]
        );
    }
    assert!(parsed.status_phase_steps("2.9.0").is_none());

    rejects_v2_mutation(|asset| {
        asset["status_adapters"]
            .as_object_mut()
            .unwrap()
            .remove("2.8.0");
    });
    rejects_v2_mutation(|asset| {
        asset["status_adapters"]["2.9.0"] = asset["status_adapters"]["2.8.0"].clone();
    });
    rejects_v2_mutation(|asset| {
        asset["status_adapters"]["2.8.0"]["status_schema_version"] = Value::String("2.7.0".into());
    });
    rejects_v2_mutation(|asset| {
        let integration =
            asset["status_adapters"]["2.8.0"]["phase_steps"]["REAL_PRODUCT_INTEGRATION"].clone();
        asset["status_adapters"]["2.8.0"]["phase_steps"]["ENGINEERING_RUNS"] = integration;
    });
    rejects_v2_mutation(|asset| {
        let integration = asset["status_adapters"]["2.8.0"]["phase_steps"]
            .as_object_mut()
            .unwrap()
            .remove("REAL_PRODUCT_INTEGRATION")
            .unwrap();
        asset["status_adapters"]["2.8.0"]["phase_steps"]["PRODUCT_INTEGRATION"] = integration;
    });
    rejects_v2_mutation(|asset| {
        asset["status_adapters"]["2.7.0"]["compatibility_status"] = Value::String("CURRENT".into());
    });
    rejects_v2_mutation(|asset| {
        asset["status_adapters"]["2.8.0"]["compatibility_status"] =
            Value::String("PREPARED".into());
    });
    rejects_v2_mutation(|asset| {
        asset["status_adapters"]["2.8.0"]["phase_steps"]["PRODUCT_FORMATION"]
            .as_array_mut()
            .unwrap()
            .swap(0, 1);
    });
    rejects_v2_mutation(|asset| {
        for version in ["2.6.0", "2.7.0", "2.8.0"] {
            asset["status_adapters"][version]["phase_steps"]["PRODUCT_FORMATION"]
                .as_array_mut()
                .unwrap()
                .swap(0, 1);
        }
    });
    rejects_v2_mutation(|asset| {
        for version in ["2.6.0", "2.7.0", "2.8.0"] {
            asset["status_adapters"][version]["phase_steps"]["INITIAL"]
                .as_array_mut()
                .unwrap()
                .swap(0, 1);
        }
    });
    rejects_v2_mutation(|asset| {
        asset["status_adapters"]["2.6.0"]["phase_steps"]["ENGINEERING_RUNS"]
            .as_array_mut()
            .unwrap()
            .swap(2, 3);
        asset["status_adapters"]["2.7.0"]["phase_steps"]["ENGINEERING_RUNS"]
            .as_array_mut()
            .unwrap()
            .swap(0, 1);
        asset["status_adapters"]["2.8.0"]["phase_steps"]["REAL_PRODUCT_INTEGRATION"]
            .as_array_mut()
            .unwrap()
            .swap(0, 1);
    });
    rejects_v2_mutation(|asset| {
        asset["execution_methods"]["other"] = asset["execution_methods"]["slk"].clone();
    });
    rejects_v2_mutation(|asset| {
        asset["execution_methods"]["calabash"] = asset["execution_methods"]["slk"].clone();
    });
    rejects_v2_mutation(|asset| {
        asset["execution_methods"]["slk"]["candidate_commit"] = Value::String("A".repeat(40));
    });
    rejects_v2_mutation(|asset| {
        asset["execution_methods"]["clk"]["manifest_sha256"] = Value::String("A".repeat(64));
    });
    rejects_v2_mutation(|asset| {
        asset["execution_methods"]["glk"]["normalization_mapping"]
            .as_array_mut()
            .unwrap()
            .swap(0, 1);
    });

    let duplicate = serde_json::to_string_pretty(&v2).unwrap().replacen(
        "\"asset_schema\": \"LCCODING_BI_COMPATIBILITY_V2\",",
        "\"asset_schema\": \"LCCODING_BI_COMPATIBILITY_V2\",\n  \"asset_schema\": \"LCCODING_BI_COMPATIBILITY_V2\",",
        1,
    );
    assert!(parse_compatibility_asset(&duplicate).is_err());
}

#[test]
fn compatibility_asset_parser_rejects_shadow_or_malformed_identity_shapes() {
    rejects_mutation(|asset| asset["asset_schema"] = Value::String("LEGACY".into()));
    rejects_mutation(|asset| {
        asset["shadow"] = Value::Bool(true);
    });
    rejects_mutation(|asset| {
        asset.as_object_mut().unwrap().remove("status_adapters");
    });
    rejects_mutation(|asset| {
        asset.as_object_mut().unwrap().remove("execution_methods");
    });
    rejects_mutation(|asset| {
        asset["status_adapters"]["2.6.0"]["shadow"] = Value::Bool(true);
    });
    rejects_mutation(|asset| {
        asset["status_adapters"]
            .as_object_mut()
            .unwrap()
            .remove("2.7.0");
    });
    rejects_mutation(|asset| {
        asset["status_adapters"]["2.7.0"]["phase_steps"]
            .as_object_mut()
            .unwrap()
            .remove("ENGINEERING_RUNS");
    });
    rejects_mutation(|asset| {
        asset["execution_methods"]
            .as_object_mut()
            .unwrap()
            .remove("clk");
    });
    rejects_mutation(|asset| {
        let extra = asset["execution_methods"]["slk"].clone();
        asset["execution_methods"]["other"] = extra;
    });
    rejects_mutation(|asset| {
        let calabash = asset["execution_methods"]["slk"].clone();
        asset["execution_methods"]["calabash"] = calabash;
    });
    rejects_mutation(|asset| {
        asset["execution_methods"]["slk"]
            .as_object_mut()
            .unwrap()
            .remove("schema_sha256");
    });
    rejects_mutation(|asset| {
        asset["execution_methods"]["slk"]["released"] = Value::Bool(true);
    });
    rejects_mutation(|asset| {
        asset["execution_methods"]["slk"]["candidate_commit"] = Value::String("A".repeat(40));
    });
    rejects_mutation(|asset| {
        asset["execution_methods"]["slk"]["version"] = Value::String("latest".into());
    });
    rejects_mutation(|asset| {
        asset["execution_methods"]["slk"]["compatibility_status"] = Value::String("BLOCKED".into());
    });
    rejects_mutation(|asset| {
        asset["execution_methods"]["slk"]["minimum_bi_version"] = Value::String("2.5.0".into());
    });
    rejects_mutation(|asset| {
        asset["execution_methods"]["clk"]["manifest_sha256"] = Value::String("A".repeat(64));
    });
    rejects_mutation(|asset| {
        asset["execution_methods"]["glk"]["adapter_schema_kind"] =
            Value::String("SLK_RUN_RUNTIME_INDEX".into());
    });
    for field in ["schema_sha256", "template_sha256"] {
        rejects_mutation(|asset| {
            asset["execution_methods"]["glk"][field] = Value::String("0".repeat(63));
        });
    }
    rejects_mutation(|asset| {
        asset["execution_methods"]["slk"]["normalization_mapping"]
            .as_array_mut()
            .unwrap()
            .pop();
    });
    rejects_mutation(|asset| {
        asset["execution_methods"]["slk"]["normalization_mapping"]
            .as_array_mut()
            .unwrap()
            .swap(0, 1);
    });

    let old_shape = serde_json::json!({
        "slk": raw_compatibility_asset()["execution_methods"]["slk"].clone(),
        "clk": raw_compatibility_asset()["execution_methods"]["clk"].clone(),
        "glk": raw_compatibility_asset()["execution_methods"]["glk"].clone()
    });
    assert!(parse_compatibility_asset(&old_shape.to_string()).is_err());
    let duplicate = include_str!("../../release/loop-contract-identities.json").replacen(
        "\"asset_schema\": \"LCCODING_BI_COMPATIBILITY_V2\",",
        "\"asset_schema\": \"LCCODING_BI_COMPATIBILITY_V2\",\n  \"asset_schema\": \"LCCODING_BI_COMPATIBILITY_V2\",",
        1,
    );
    assert!(parse_compatibility_asset(&duplicate).is_err());
}

#[test]
fn production_rust_contains_no_shadow_loop_identity_table() {
    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("src");
    let production = rust_sources(&root).join("\n");
    assert_eq!(
        production.matches("loop-contract-identities.json").count(),
        1
    );
    for retired in [
        "SLK_VERSION",
        "CLK_VERSION",
        "GLK_VERSION",
        "SLK_MANIFEST_SHA256",
        "CLK_MANIFEST_SHA256",
        "GLK_MANIFEST_SHA256",
    ] {
        assert!(
            !production.contains(retired),
            "retired Rust identity: {retired}"
        );
    }
    let raw = raw_compatibility_asset();
    for method_id in ["slk", "clk", "glk"] {
        let method = &raw["execution_methods"][method_id];
        for field in [
            "candidate_commit",
            "manifest_sha256",
            "schema_sha256",
            "template_sha256",
        ] {
            assert!(!production.contains(method[field].as_str().unwrap()));
        }
    }
}

#[test]
fn slk_and_clk_normalize_the_same_seven_governance_metrics() {
    let slk = parse_slk_governance(SLK).unwrap();
    let clk = parse_clk_governance(CLK).unwrap();
    for summary in [&slk, &clk] {
        assert_eq!(summary.metrics.len(), 7);
        assert_eq!(
            statuses(&summary),
            vec![
                GovernanceStatus::Compliant,
                GovernanceStatus::Compliant,
                GovernanceStatus::Active,
                GovernanceStatus::Compliant,
                GovernanceStatus::Active,
                GovernanceStatus::Compliant,
                GovernanceStatus::Compliant,
            ]
        );
        assert_eq!(summary.metrics[0].completed, Some(4));
        assert_eq!(summary.metrics[0].total, Some(4));
        assert_eq!(summary.metrics[2].interval_minutes, Some(15));
        assert_eq!(summary.metrics[4].total, Some(2));
    }
    assert_eq!(slk.metrics[4].completed, Some(0));
    assert_eq!(clk.metrics[4].completed, Some(1));
}

#[test]
fn glk_indexed_artifacts_normalize_without_exposing_paths() {
    let (index, artifacts) = glk_fixture();
    let summary = parse_glk_governance(&index, &artifacts).unwrap();
    assert_eq!(summary.metrics.len(), 7);
    assert_eq!(summary.metrics[2].interval_minutes, Some(15));
    assert_eq!(summary.metrics[4].completed, Some(1));
    assert_eq!(summary.metrics[4].total, Some(2));
    let serialized = serde_json::to_string(&summary).unwrap();
    assert!(!serialized.contains("governance/"));
    assert!(!serialized.contains("sha256"));
}

#[test]
fn adapters_fail_closed_on_wrong_identity_or_invalid_governance() {
    assert!(parse_slk_governance(&SLK.replace("2.6.0", "2.5.0")).is_err());
    assert!(
        parse_clk_governance(&CLK.replace("interval_minutes: 15", "interval_minutes: 12")).is_err()
    );
    let (index, mut artifacts) = glk_fixture();
    assert!(parse_glk_governance(&index.replace("3.1.0", "3.0.0"), &artifacts).is_err());
    artifacts[0].body = "schema_version: 3.1.0\nartifact_type: MONITOR_CONTROL\n";
    assert!(parse_glk_governance(&index, &artifacts).is_err());
    assert!(parse_slk_governance(&format!("{SLK}\nunknown_field: true")).is_err());
    assert!(
        parse_slk_governance(&SLK.replacen(
            "\"runtime_contract\": {",
            "\"runtime_contract\": &contract {",
            1,
        ))
        .is_err()
    );
    assert!(parse_clk_governance(&format!("{CLK}\nversion: 2.5.0")).is_err());
}

#[test]
fn active_run_safe_ref_reads_one_supported_index_and_projects_only_summary() {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let root = std::env::temp_dir().join(format!("lccoding-loop-adapter-{nonce}"));
    let run = root.join(".lccoding/runs/RUN-001");
    fs::create_dir_all(&run).unwrap();
    fs::write(run.join("RUN_RUNTIME_INDEX.yaml"), SLK).unwrap();

    let status = include_str!("../../../templates/STATUS.json")
        .replace("\"project_id\": \"\"", "\"project_id\": \"Loop Project\"")
        .replace(
            "\"initialization_mode\": \"NEW|EXISTING\"",
            "\"initialization_mode\": \"NEW\"",
        )
        .replace("\"active_runs\": []", "\"active_runs\": [\"runs/RUN-001\"]");
    let mut status: Value = serde_json::from_str(&status).unwrap();
    assert!(status.get("agent_product_formation").is_some());
    assert!(status.get("agent_slice_integration").is_some());
    assert!(
        status
            .as_object_mut()
            .unwrap()
            .remove("agent_product_formation")
            .is_some()
    );
    assert!(
        status
            .as_object_mut()
            .unwrap()
            .remove("agent_slice_integration")
            .is_some()
    );
    status["status_schema_version"] = Value::String("2.6.0".into());
    status["canonical_candidate"]
        .as_object_mut()
        .unwrap()
        .remove("candidate_id");
    status["canonical_candidate"]
        .as_object_mut()
        .unwrap()
        .remove("candidate_hash");
    status["vulnerability_closure"] = Value::String("PENDING".into());
    status["post_security_owner_acceptance"] = Value::String("PENDING".into());
    let status = parse_status(&serde_json::to_string(&status).unwrap()).unwrap();

    let compatibility = embedded_compatibility_asset().unwrap();
    let slk = compatibility.execution_method("slk").unwrap();
    let mut manifest: Value =
        serde_json::from_str(include_str!("../../../templates/CANONICAL-MANIFEST.json")).unwrap();
    manifest["lccoding"]["version"] = Value::String("2.6.0".into());
    manifest
        .as_object_mut()
        .unwrap()
        .remove("execution_methods");
    manifest["slk"]["version"] = Value::String(slk.version.clone());
    manifest["slk"]["hash"] = Value::String(format!("sha256:{}", slk.manifest_sha256));
    let manifest = parse_manifest(&serde_json::to_string(&manifest).unwrap()).unwrap();
    let summary = load_loop_governance(&root, &status, Some(&manifest))
        .unwrap()
        .unwrap();
    assert_eq!(summary.metrics[0].completed, Some(4));
    assert_eq!(summary.metrics[4].total, Some(2));
    assert!(!serde_json::to_string(&summary).unwrap().contains("RUN-001"));

    fs::write(run.join("CLK_RUN_CONTROL_TRACE.yaml"), CLK).unwrap();
    assert!(load_loop_governance(&root, &status, Some(&manifest)).is_err());
    fs::remove_dir_all(root).unwrap();
}
