use std::fs;
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};

use lccoding::projection::{load_project_snapshot, snapshot_from_status};
use lccoding::records::compatibility::{embedded_compatibility_asset, parse_compatibility_asset};
use lccoding::records::manifest::parse_manifest;
use lccoding::records::status::parse_status;
use serde_json::Value;
use sha2::{Digest, Sha256};

fn initial_status() -> String {
    include_str!("../../../templates/STATUS.json")
        .replace("\"project_id\": \"\"", "\"project_id\": \"示例 Project\"")
        .replace(
            "\"initialization_mode\": \"NEW|EXISTING\"",
            "\"initialization_mode\": \"NEW\"",
        )
}

fn product_formation_status() -> String {
    initial_status()
        .replace(
            "\"current_phase\": \"INITIAL\"",
            "\"current_phase\": \"PRODUCT_FORMATION\"",
        )
        .replace(
            "\"INITIAL_READY\": \"PENDING\"",
            "\"INITIAL_READY\": \"COMPLETE\"",
        )
        .replace("\"proposal\": \"PENDING\"", "\"proposal\": \"COMPLETE\"")
        .replace(
            "\"initialization\": \"PENDING\"",
            "\"initialization\": \"COMPLETE\"",
        )
        .replace(
            "\"calabash_draft\": \"PENDING\"",
            "\"calabash_draft\": \"ACTIVE\"",
        )
}

fn baseline_complete_status() -> String {
    product_formation_status()
        .replace(
            "\"current_phase\": \"PRODUCT_FORMATION\"",
            "\"current_phase\": \"REAL_PRODUCT_INTEGRATION\"",
        )
        .replace(
            "\"CALABASH_UPGRADE_READY\": \"PENDING\"",
            "\"CALABASH_UPGRADE_READY\": \"COMPLETE\"",
        )
        .replace(
            "\"calabash_draft\": \"ACTIVE\"",
            "\"calabash_draft\": \"COMPLETE\"",
        )
        .replace("\"workflow\": \"PENDING\"", "\"workflow\": \"COMPLETE\"")
        .replace("\"ui\": \"PENDING\"", "\"ui\": \"COMPLETE\"")
        .replace(
            "\"simulation\": \"PENDING\"",
            "\"simulation\": \"COMPLETE\"",
        )
        .replace(
            "\"mandatory_calabash_upgrade\": \"PENDING\"",
            "\"mandatory_calabash_upgrade\": \"COMPLETE\"",
        )
        .replace(
            "\"product_baseline\": \"PENDING\"",
            "\"product_baseline\": \"COMPLETE\"",
        )
}

fn status_version(body: &str, version: &str) -> String {
    let mut value: Value = serde_json::from_str(body).unwrap();
    if version == "2.8.0" {
        assert!(value.get("agent_product_formation").is_some());
        assert!(value.get("agent_slice_integration").is_some());
    } else {
        assert!(
            value
                .as_object_mut()
                .unwrap()
                .remove("agent_product_formation")
                .is_some()
        );
        assert!(
            value
                .as_object_mut()
                .unwrap()
                .remove("agent_slice_integration")
                .is_some()
        );
        if value["current_phase"] == "REAL_PRODUCT_INTEGRATION" {
            value["current_phase"] = Value::String("ENGINEERING_RUNS".into());
        }
    }
    value["status_schema_version"] = Value::String(version.to_owned());
    serde_json::to_string_pretty(&value).unwrap()
}

fn accepted_agent_status(applicability: &str) -> String {
    let mut value: Value = serde_json::from_str(&initial_status()).unwrap();
    value["canonical_candidate"] = serde_json::json!({
        "repository": "https://example.invalid/repository",
        "version": "1.0.0",
        "commit": "c".repeat(40),
        "candidate_id": "CANDIDATE-1",
        "candidate_hash": format!("sha256:{}", "a".repeat(64)),
    });
    let capability = match applicability {
        "APPLICABLE_CORE" => "REAL_RUNNABLE_CORE",
        "APPLICABLE_EXTRA" => "UNIMPLEMENTED_EXTRA",
        "NOT_APPLICABLE" => "NOT_APPLICABLE",
        _ => panic!("unsupported Product Agent applicability fixture"),
    };
    value["agent_product_formation"] = serde_json::json!({
        "state": "PRODUCT_FORMATION_AGENT_BOUND",
        "product_agent_applicability": applicability,
        "calabash_definition_handoff_id": "CALABASH-HANDOFF-1",
        "calabash_definition_handoff_hash": format!("sha256:{}", "d".repeat(64)),
        "configuration_baseline_id": "AGENT-CONFIG-1",
        "configuration_baseline_hash": format!("sha256:{}", "b".repeat(64)),
        "product_agent_capability_state": capability,
        "operations_agent_state": "PREPARED_NOT_INTEGRATED",
    });
    value["agent_slice_integration"] = serde_json::json!({
        "state": "AGENT_SLICES_ACCEPTED",
        "candidate_id": "CANDIDATE-1",
        "candidate_hash": format!("sha256:{}", "a".repeat(64)),
        "product_baseline_id": "PRODUCT-BASELINE-1",
        "product_baseline_hash": format!("sha256:{}", "e".repeat(64)),
        "configuration_baseline_id": "AGENT-CONFIG-1",
        "configuration_baseline_hash": format!("sha256:{}", "b".repeat(64)),
        "production_topology_id": "PRODUCTION-TOPOLOGY-1",
        "production_topology_hash": format!("sha256:{}", "f".repeat(64)),
        "runtime_adapter_attestation_id": "RUNTIME-ATTESTATION-1",
        "runtime_adapter_attestation_hash": format!("sha256:{}", "1".repeat(64)),
        "runtime_adapter_id": "RUNTIME-ADAPTER-1",
        "runtime_adapter_version": "1.2.3",
        "dual_agent_isolation_state": "VERIFIED",
        "product_agent_applicability": applicability,
        "product_integration_state": "ACCEPTED",
        "product_agent_integration_state": if applicability == "NOT_APPLICABLE" {
            "NOT_APPLICABLE"
        } else {
            "ACCEPTED"
        },
        "operations_agent_integration_state": "ACCEPTED",
        "accepted_product_slice_ids": ["PRODUCT-SLICE-1", "PRODUCT-SLICE-2"],
        "accepted_operations_slice_ids": ["OPERATIONS-SLICE-1"],
        "required_operations_slice_id": "OPERATIONS-SLICE-1",
        "current_product_slice_reference": "slices/PRODUCT-FEATURE.md",
        "product_verification_reference": "slices/PRODUCT-FINAL.md",
        "current_operations_slice_reference": "slices/OPERATIONS-FEATURE.md",
        "operations_verification_reference": "slices/OPERATIONS-FINAL.md",
        "integration_baseline_reference": "INTEGRATION-BASELINE.md",
    });
    serde_json::to_string_pretty(&value).unwrap()
}

fn phase_steps(snapshot: &Value) -> Vec<(String, Vec<String>)> {
    snapshot["phases"]
        .as_array()
        .unwrap()
        .iter()
        .map(|phase| {
            (
                phase["id"].as_str().unwrap().to_owned(),
                phase["steps"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|step| step["id"].as_str().unwrap().to_owned())
                    .collect(),
            )
        })
        .collect()
}

fn report_row<'a>(snapshot: &'a Value, key: &str) -> Option<&'a Value> {
    snapshot["reports"]["candidate"]["rows"]
        .as_array()
        .unwrap()
        .iter()
        .find(|row| row["key"] == key)
}

fn canonical_single_blob_hash(path: &str, bytes: &[u8]) -> String {
    let blob_digest = format!("{:x}", Sha256::digest(bytes));
    let manifest = format!("{path}\0{}\0{blob_digest}\n", "100644");
    format!("sha256:{:x}", Sha256::digest(manifest.as_bytes()))
}

fn git(root: &std::path::Path, arguments: &[&str]) -> String {
    let output = Command::new("git")
        .args(arguments)
        .current_dir(root)
        .env("GIT_AUTHOR_NAME", "LCCoding Test")
        .env("GIT_AUTHOR_EMAIL", "test@example.invalid")
        .env("GIT_COMMITTER_NAME", "LCCoding Test")
        .env("GIT_COMMITTER_EMAIL", "test@example.invalid")
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    String::from_utf8(output.stdout).unwrap().trim().to_owned()
}

#[test]
fn strict_status_projects_four_phases_twenty_one_steps_and_eight_reports() {
    let status = parse_status(&product_formation_status()).unwrap();
    let snapshot = snapshot_from_status(&status, None).unwrap();
    let value = serde_json::to_value(snapshot).unwrap();

    assert_eq!(value["health"], "ok");
    assert_eq!(value["project"], "示例 Project");
    assert_eq!(value["current_phase"], "PRODUCT_FORMATION");
    assert_eq!(value["phases"].as_array().unwrap().len(), 4);
    assert_eq!(
        value["phases"]
            .as_array()
            .unwrap()
            .iter()
            .map(|phase| phase["steps"].as_array().unwrap().len())
            .sum::<usize>(),
        21,
    );
    assert_eq!(value["reports"].as_object().unwrap().len(), 8);
    assert_eq!(value["schema"], "LCCoding 2.8.0 derived BI");
    assert_eq!(value["phases"][2]["id"], "REAL_PRODUCT_INTEGRATION");

    for phase in value["phases"].as_array().unwrap() {
        for step in phase["steps"].as_array().unwrap() {
            if let Some(report) = step["report"].as_str() {
                assert_eq!(value["reports"][report]["state"], step["state"]);
            }
        }
    }
}

#[test]
fn agent_native_status_projects_only_sanitized_candidate_summary_rows() {
    let raw = accepted_agent_status("APPLICABLE_CORE");
    let status = parse_status(&raw).unwrap();
    let snapshot = serde_json::to_value(snapshot_from_status(&status, None).unwrap()).unwrap();

    assert_eq!(
        report_row(&snapshot, "row.operations_agent_integration").unwrap()["value"],
        serde_json::json!({"kind": "record", "value": "ACCEPTED"})
    );
    assert_eq!(
        report_row(&snapshot, "row.product_agent_integration").unwrap()["value"],
        serde_json::json!({
            "kind": "agent_status",
            "applicability": "APPLICABLE_CORE",
            "integration": "ACCEPTED"
        })
    );
    assert_eq!(
        report_row(&snapshot, "row.runtime_adapter").unwrap()["value"],
        serde_json::json!({
            "kind": "safe_identity",
            "id": "RUNTIME-ADAPTER-1",
            "version": "1.2.3"
        })
    );
    assert_eq!(
        report_row(&snapshot, "row.dual_agent_isolation").unwrap()["value"],
        serde_json::json!({"kind": "record", "value": "VERIFIED"})
    );
    assert_eq!(
        report_row(&snapshot, "row.product_slice_progress").unwrap()["value"]["completed"],
        2
    );
    assert_eq!(
        report_row(&snapshot, "row.operations_slice_progress").unwrap()["value"]["completed"],
        1
    );

    let wire = serde_json::to_string(&snapshot).unwrap();
    let candidate_hash = format!("sha256:{}", "a".repeat(64));
    let configuration_hash = format!("sha256:{}", "b".repeat(64));
    for forbidden in [
        "CANDIDATE-1",
        "AGENT-CONFIG-1",
        "PRODUCTION-TOPOLOGY-1",
        "RUNTIME-ATTESTATION-1",
        "PRODUCT-SLICE-1",
        "OPERATIONS-SLICE-1",
        "slices/PRODUCT-FEATURE.md",
        "INTEGRATION-BASELINE.md",
        &candidate_hash,
        &configuration_hash,
    ] {
        assert!(
            !wire.contains(forbidden),
            "raw Agent value leaked: {forbidden}"
        );
    }
}

#[test]
fn agent_native_status_is_schema_exact_and_identity_bound() {
    let accepted: Value = serde_json::from_str(&accepted_agent_status("APPLICABLE_CORE")).unwrap();
    assert!(parse_status(&accepted.to_string()).is_ok());

    for field in ["agent_product_formation", "agent_slice_integration"] {
        let mut missing = accepted.clone();
        missing.as_object_mut().unwrap().remove(field);
        assert!(
            parse_status(&missing.to_string()).is_err(),
            "missing {field}"
        );
        let mut null = accepted.clone();
        null[field] = Value::Null;
        assert!(parse_status(&null.to_string()).is_err(), "null {field}");
    }

    for raw_field in [
        "raw_prompt",
        "private_memory",
        "credential",
        "absolute_path",
        "raw_hash",
        "event",
    ] {
        let mut leaked = accepted.clone();
        leaked["agent_slice_integration"][raw_field] = Value::String("secret".into());
        assert!(
            parse_status(&leaked.to_string()).is_err(),
            "raw field {raw_field}"
        );
    }
    for field in ["runtime_adapter_id", "production_topology_id"] {
        let mut missing = accepted.clone();
        missing["agent_slice_integration"]
            .as_object_mut()
            .unwrap()
            .remove(field);
        assert!(
            parse_status(&missing.to_string()).is_err(),
            "missing {field}"
        );
        let mut null = accepted.clone();
        null["agent_slice_integration"][field] = Value::Null;
        assert!(parse_status(&null.to_string()).is_err(), "null {field}");
    }
    let mut stale_candidate = accepted.clone();
    stale_candidate["agent_slice_integration"]["candidate_id"] =
        Value::String("CANDIDATE-STALE".into());
    assert!(parse_status(&stale_candidate.to_string()).is_err());
    let mut wrong_configuration = accepted.clone();
    wrong_configuration["agent_slice_integration"]["configuration_baseline_hash"] =
        Value::String(format!("sha256:{}", "9".repeat(64)));
    assert!(parse_status(&wrong_configuration.to_string()).is_err());
    let mut wrong_topology = accepted.clone();
    wrong_topology["agent_slice_integration"]["production_topology_hash"] =
        Value::String("NOT_APPLICABLE".into());
    assert!(parse_status(&wrong_topology.to_string()).is_err());
    let mut wrong_adapter = accepted.clone();
    wrong_adapter["agent_slice_integration"]["runtime_adapter_version"] =
        Value::String("latest".into());
    assert!(parse_status(&wrong_adapter.to_string()).is_err());
    let mut secret_adapter = accepted.clone();
    secret_adapter["agent_slice_integration"]["runtime_adapter_id"] =
        Value::String("sk-secret".into());
    assert!(parse_status(&secret_adapter.to_string()).is_err());
    let mut aliased_slices = accepted.clone();
    aliased_slices["agent_slice_integration"]["accepted_operations_slice_ids"] =
        serde_json::json!(["PRODUCT-SLICE-1"]);
    aliased_slices["agent_slice_integration"]["required_operations_slice_id"] =
        Value::String("PRODUCT-SLICE-1".into());
    assert!(parse_status(&aliased_slices.to_string()).is_err());
    let mut hybrid_phase = accepted.clone();
    hybrid_phase["current_phase"] = Value::String("ENGINEERING_RUNS".into());
    assert!(parse_status(&hybrid_phase.to_string()).is_err());

    for version in ["2.6.0", "2.7.0"] {
        let legacy = status_version(&initial_status(), version);
        let status = parse_status(&legacy).unwrap();
        let snapshot = serde_json::to_value(snapshot_from_status(&status, None).unwrap()).unwrap();
        assert_eq!(snapshot["schema"], format!("LCCoding {version} derived BI"));
        assert_eq!(snapshot["phases"][2]["id"], "ENGINEERING_RUNS");
        assert_eq!(
            snapshot["reports"]["candidate"]["rows"]
                .as_array()
                .unwrap()
                .len(),
            2
        );
        assert!(report_row(&snapshot, "row.runtime_adapter").is_none());
        let mut hybrid: Value = serde_json::from_str(&legacy).unwrap();
        hybrid["agent_product_formation"] = accepted["agent_product_formation"].clone();
        assert!(parse_status(&hybrid.to_string()).is_err());
    }

    let not_applicable = parse_status(&accepted_agent_status("NOT_APPLICABLE")).unwrap();
    let snapshot =
        serde_json::to_value(snapshot_from_status(&not_applicable, None).unwrap()).unwrap();
    assert_eq!(
        report_row(&snapshot, "row.product_agent_integration").unwrap()["value"],
        serde_json::json!({
            "kind": "agent_status",
            "applicability": "NOT_APPLICABLE",
            "integration": "NOT_APPLICABLE"
        })
    );
}

#[test]
fn status_adapters_drive_exact_260_270_and_280_phase_layouts() {
    let compatibility = embedded_compatibility_asset().unwrap();
    let expected_counts = [
        ("2.6.0", vec![3, 5, 7, 6]),
        ("2.7.0", vec![3, 7, 5, 6]),
        ("2.8.0", vec![3, 7, 5, 6]),
    ];
    for (version, counts) in expected_counts {
        let status = parse_status(&status_version(&initial_status(), version)).unwrap();
        let snapshot = serde_json::to_value(snapshot_from_status(&status, None).unwrap()).unwrap();
        let projected = phase_steps(&snapshot);
        let adapter = compatibility.status_phase_steps(version).unwrap();
        assert_eq!(
            projected
                .iter()
                .map(|(_, steps)| steps.len())
                .collect::<Vec<_>>(),
            counts
        );
        assert_eq!(
            projected,
            adapter
                .iter()
                .map(|phase| {
                    (
                        phase.phase_id.to_owned(),
                        phase
                            .step_ids
                            .iter()
                            .map(|step| (*step).to_owned())
                            .collect(),
                    )
                })
                .collect::<Vec<_>>()
        );
        assert_eq!(snapshot["reports"].as_object().unwrap().len(), 8);
        assert!(
            !snapshot
                .to_string()
                .contains("\"id\":\"PRODUCT_INTEGRATION\"")
        );
    }

    let legacy = compatibility.status_phase_steps("2.6.0").unwrap();
    assert_eq!(legacy[2].step_ids[0], "MANDATORY_CALABASH_UPGRADE");
    assert_eq!(legacy[2].step_ids[1], "PRODUCT_BASELINE");
    let current = compatibility.status_phase_steps("2.7.0").unwrap();
    assert_eq!(current[1].step_ids[5], "MANDATORY_CALABASH_UPGRADE");
    assert_eq!(current[1].step_ids[6], "PRODUCT_BASELINE");
    assert_eq!(current[2].step_ids[0], "FEATURE_SLICE_EXECUTION_COVERAGE");
    let prepared = compatibility.status_phase_steps("2.8.0").unwrap();
    assert_eq!(prepared[2].phase_id, "REAL_PRODUCT_INTEGRATION");
    assert_eq!(prepared[2].step_ids, current[2].step_ids);
}

#[test]
fn current_status_and_manifest_shapes_are_strict_and_identity_bound() {
    let status_text = initial_status();
    assert!(parse_status(&status_text).is_ok());
    let manifest_text = include_str!("../../../templates/CANONICAL-MANIFEST.json");
    assert!(parse_manifest(manifest_text).is_ok());

    let mut status: Value = serde_json::from_str(&status_text).unwrap();
    status["canonical_candidate"]["shadow"] = Value::Bool(true);
    assert!(parse_status(&status.to_string()).is_err());
    let mut status: Value = serde_json::from_str(&status_text).unwrap();
    status["vulnerability_closure"]
        .as_object_mut()
        .unwrap()
        .remove("candidate_hash");
    assert!(parse_status(&status.to_string()).is_err());
    let mut status: Value = serde_json::from_str(&status_text).unwrap();
    status["post_security_owner_acceptance"]["current_acceptance_id"] =
        Value::String("../unsafe".into());
    assert!(parse_status(&status.to_string()).is_err());

    let method = serde_json::json!({
        "method_id": "METHOD-ONE",
        "version": "1.0.0",
        "exact_hash": format!("sha256:{}", "a".repeat(64)),
        "canonical_contract_reference": "contracts/method-one.json",
        "run_evidence_mapping": "RUN_START_CONTRACT -> D0-D3",
        "owner_acceptance_mapping": "LOOP_OWNER_ACCEPTANCE_RECEIPT",
        "required_control_binding": "LCCODING_LOOP_CONTROL",
        "compatibility_result": "PASS"
    });
    let mut manifest: Value = serde_json::from_str(manifest_text).unwrap();
    manifest["execution_methods"] = Value::Array(vec![method.clone()]);
    assert!(parse_manifest(&manifest.to_string()).is_ok());
    manifest["execution_methods"] = Value::Array(vec![method.clone(), method.clone()]);
    assert!(parse_manifest(&manifest.to_string()).is_err());
    let mut bad = method;
    bad["exact_hash"] = Value::String("A".repeat(64));
    manifest["execution_methods"] = Value::Array(vec![bad]);
    assert!(parse_manifest(&manifest.to_string()).is_err());
}

#[test]
fn status_and_manifest_field_presence_is_schema_version_sensitive() {
    let status_text = initial_status();
    let mut current: Value = serde_json::from_str(&status_version(&status_text, "2.7.0")).unwrap();
    assert!(parse_status(&current.to_string()).is_ok());

    current["canonical_candidate"] = serde_json::json!({
        "repository": "https://example.invalid/repo",
        "version": "1.0.0",
        "commit": "a".repeat(40),
        "candidate_id": "CANDIDATE-1",
        "candidate_hash": format!("sha256:{}", "b".repeat(64))
    });
    assert!(parse_status(&current.to_string()).is_ok());

    for fields in [
        vec!["candidate_id", "candidate_hash"],
        vec!["candidate_id"],
        vec!["candidate_hash"],
    ] {
        let mut mutation = current.clone();
        for field in fields {
            mutation["canonical_candidate"]
                .as_object_mut()
                .unwrap()
                .remove(field);
        }
        assert!(parse_status(&mutation.to_string()).is_err());
    }
    for field in ["candidate_id", "candidate_hash"] {
        let mut mutation = current.clone();
        mutation["canonical_candidate"][field] = Value::Null;
        assert!(parse_status(&mutation.to_string()).is_err());
    }
    for (field, value) in [
        ("candidate_id", String::new()),
        ("candidate_hash", String::new()),
        ("candidate_hash", format!("sha256:{}", "B".repeat(64))),
        ("commit", "A".repeat(40)),
    ] {
        let mut mutation = current.clone();
        mutation["canonical_candidate"][field] = Value::String(value);
        assert!(parse_status(&mutation.to_string()).is_err());
    }

    let explicit_empty = status_version(&status_text, "2.7.0");
    assert!(parse_status(&explicit_empty).is_ok());

    let mut legacy: Value = serde_json::from_str(&status_text).unwrap();
    assert!(
        legacy
            .as_object_mut()
            .unwrap()
            .remove("agent_product_formation")
            .is_some()
    );
    assert!(
        legacy
            .as_object_mut()
            .unwrap()
            .remove("agent_slice_integration")
            .is_some()
    );
    legacy["status_schema_version"] = Value::String("2.6.0".into());
    legacy["canonical_candidate"]
        .as_object_mut()
        .unwrap()
        .remove("candidate_id");
    legacy["canonical_candidate"]
        .as_object_mut()
        .unwrap()
        .remove("candidate_hash");
    assert!(parse_status(&legacy.to_string()).is_ok());
    legacy["canonical_candidate"]["candidate_id"] = Value::String("CANDIDATE-1".into());
    assert!(parse_status(&legacy.to_string()).is_err());
    legacy["canonical_candidate"]["candidate_hash"] =
        Value::String(format!("sha256:{}", "b".repeat(64)));
    legacy["canonical_candidate"]["repository"] =
        Value::String("https://example.invalid/repo".into());
    legacy["canonical_candidate"]["version"] = Value::String("1.0.0".into());
    legacy["canonical_candidate"]["commit"] = Value::String("a".repeat(40));
    assert!(parse_status(&legacy.to_string()).is_ok());
    legacy["canonical_candidate"]["candidate_hash"] =
        Value::String(format!("sha256:{}", "B".repeat(64)));
    assert!(parse_status(&legacy.to_string()).is_err());

    let manifest_text = include_str!("../../../templates/CANONICAL-MANIFEST.json");
    let mut current_manifest: Value = serde_json::from_str(manifest_text).unwrap();
    current_manifest["lccoding"]["version"] = Value::String("2.7.0".into());
    assert!(parse_manifest(&current_manifest.to_string()).is_ok());
    for replacement in [None, Some(Value::Null), Some(serde_json::json!({}))] {
        let mut mutation = current_manifest.clone();
        match replacement {
            None => {
                mutation
                    .as_object_mut()
                    .unwrap()
                    .remove("execution_methods");
            }
            Some(value) => mutation["execution_methods"] = value,
        }
        assert!(parse_manifest(&mutation.to_string()).is_err());
    }

    let mut legacy_manifest: Value = serde_json::from_str(manifest_text).unwrap();
    legacy_manifest["lccoding"]["version"] = Value::String("2.6.0".into());
    legacy_manifest
        .as_object_mut()
        .unwrap()
        .remove("execution_methods");
    assert!(parse_manifest(&legacy_manifest.to_string()).is_ok());
    legacy_manifest["execution_methods"] = serde_json::json!([{"method_id": "INCOMPLETE"}]);
    assert!(parse_manifest(&legacy_manifest.to_string()).is_err());
}

#[test]
fn unsupported_status_adapters_and_layout_mutations_fail_closed() {
    for version in ["2.5.2", "2.3.0", "9.9.9"] {
        assert_eq!(
            parse_status(&status_version(&initial_status(), version))
                .unwrap_err()
                .code(),
            "BI_PROJECT_VERSION_UNSUPPORTED"
        );
    }
    let raw = include_str!("../../release/loop-contract-identities.json");
    let mut asset: Value = serde_json::from_str(raw).unwrap();
    asset["status_adapters"]["2.7.0"]["phase_steps"]["ENGINEERING_RUNS"][0] =
        Value::String("UNKNOWN_STEP".into());
    assert!(parse_compatibility_asset(&asset.to_string()).is_err());
    let mut asset: Value = serde_json::from_str(raw).unwrap();
    asset["status_adapters"]["2.7.0"]["phase_steps"]["PRODUCT_FORMATION"]
        .as_array_mut()
        .unwrap()
        .push(Value::String("PRODUCT_BASELINE".into()));
    assert!(parse_compatibility_asset(&asset.to_string()).is_err());
}

#[test]
fn phase_truth_and_report_links_follow_the_selected_270_layout() {
    let engineering = status_version(&baseline_complete_status(), "2.7.0");
    let status = parse_status(&engineering).unwrap();
    let snapshot = serde_json::to_value(snapshot_from_status(&status, None).unwrap()).unwrap();
    assert_eq!(snapshot["phases"][1]["state"], "done");
    assert_eq!(
        snapshot["phases"][2]["steps"][0]["id"],
        "FEATURE_SLICE_EXECUTION_COVERAGE"
    );
    for phase in snapshot["phases"].as_array().unwrap() {
        for step in phase["steps"].as_array().unwrap() {
            if let Some(report) = step["report"].as_str() {
                assert_eq!(snapshot["reports"][report]["state"], step["state"]);
            }
        }
    }

    let upgrade_pending = engineering.replace(
        "\"mandatory_calabash_upgrade\": \"COMPLETE\"",
        "\"mandatory_calabash_upgrade\": \"PENDING\"",
    );
    let status = parse_status(&upgrade_pending).unwrap();
    assert!(snapshot_from_status(&status, None).is_err());

    let baseline_exit_while_formation = status_version(
        &baseline_complete_status().replace(
            "\"current_phase\": \"REAL_PRODUCT_INTEGRATION\"",
            "\"current_phase\": \"PRODUCT_FORMATION\"",
        ),
        "2.7.0",
    );
    let status = parse_status(&baseline_exit_while_formation).unwrap();
    assert!(snapshot_from_status(&status, None).is_err());
}

#[test]
fn rust_status_and_projection_have_no_second_adapter_layout() {
    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("src");
    let status = fs::read_to_string(root.join("records/status.rs")).unwrap();
    let projection = fs::read_to_string(root.join("projection.rs")).unwrap();
    let compatibility = fs::read_to_string(root.join("records/compatibility.rs")).unwrap();
    assert!(!status.contains("SUPPORTED_VERSIONS"));
    assert!(!projection.contains("vec![\n        phase("));
    assert!(!projection.contains("PRODUCT_INTEGRATION"));
    assert_eq!(
        [status, projection, compatibility]
            .join("\n")
            .matches("loop-contract-identities.json")
            .count(),
        1
    );
}

#[test]
fn duplicate_unknown_unsafe_and_unsupported_status_values_fail_closed() {
    let valid = initial_status();
    let duplicate = valid.replacen(
        "\"project_id\": \"示例 Project\"",
        "\"project_id\": \"示例 Project\",\n  \"project_id\": \"Other\"",
        1,
    );
    let unknown = valid.replacen(
        "\"updated_at\": \"\"",
        "\"updated_at\": \"\",\n  \"private_path\": \"C:/secret\"",
        1,
    );
    let unsafe_name = valid.replace("示例 Project", "C:/private/project");
    let unsupported = valid.replace("\"2.8.0\"", "\"2.3.0\"");

    for malformed in [duplicate, unknown, unsafe_name] {
        let error = parse_status(&malformed).unwrap_err();
        assert_eq!(error.code(), "BI_RECORD_INVALID");
        assert!(!format!("{error:?} {error}").contains("private"));
    }
    assert_eq!(
        parse_status(&unsupported).unwrap_err().code(),
        "BI_PROJECT_VERSION_UNSUPPORTED",
    );
}

#[test]
fn unicode_evidence_references_are_accepted_without_relaxing_path_safety() {
    let valid = initial_status().replace(
        "\"evidence_pointers\": []",
        "\"evidence_pointers\": [\"docs/proposal/LCGEO_完整方案_v0.5.md\"]",
    );
    assert!(parse_status(&valid).is_ok());

    for reference in [
        "C:/private/project.md",
        "../private/project.md",
        "docs/../private.md",
        "docs//private.md",
        "docs\\private.md",
        "docs/\u{202e}private.md",
    ] {
        let unsafe_status = initial_status().replace(
            "\"evidence_pointers\": []",
            &format!("\"evidence_pointers\": [\"{reference}\"]"),
        );
        assert_eq!(
            parse_status(&unsafe_status).unwrap_err().code(),
            "BI_RECORD_INVALID",
            "unsafe reference was accepted: {reference:?}",
        );
    }
}

#[test]
fn lifecycle_history_future_and_aggregate_contradictions_are_rejected() {
    let future_complete =
        initial_status().replace("\"workflow\": \"PENDING\"", "\"workflow\": \"COMPLETE\"");
    let status = parse_status(&future_complete).unwrap();
    assert_eq!(
        snapshot_from_status(&status, None).unwrap_err().code(),
        "BI_RECORD_INCONSISTENT",
    );

    let stale_phase = initial_status().replace(
        "\"INITIAL_READY\": \"PENDING\"",
        "\"INITIAL_READY\": \"COMPLETE\"",
    );
    let status = parse_status(&stale_phase).unwrap();
    assert_eq!(
        snapshot_from_status(&status, None).unwrap_err().code(),
        "BI_RECORD_INCONSISTENT",
    );
}

#[test]
fn canonical_manifest_is_closed_and_must_match_the_status_adapter_family() {
    let manifest_text = include_str!("../../../templates/CANONICAL-MANIFEST.json");
    let manifest = parse_manifest(manifest_text).unwrap();
    let status = parse_status(&initial_status()).unwrap();
    assert!(snapshot_from_status(&status, Some(&manifest)).is_ok());

    let duplicate = manifest_text.replacen(
        "\"compatibility\": \"PENDING\"",
        "\"compatibility\": \"PENDING\",\n  \"compatibility\": \"OTHER\"",
        1,
    );
    assert_eq!(
        parse_manifest(&duplicate).unwrap_err().code(),
        "BI_RECORD_INVALID"
    );

    let mismatched = manifest_text.replace("\"2.7.0\"", "\"2.4.1\"");
    let manifest = parse_manifest(&mismatched).unwrap();
    assert_eq!(
        snapshot_from_status(&status, Some(&manifest))
            .unwrap_err()
            .code(),
        "BI_RECORD_INCONSISTENT",
    );
}

#[test]
fn project_loader_reads_real_records_and_git_without_writing_the_project() {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let root = std::env::temp_dir().join(format!("lccoding-projection-{nonce}"));
    fs::create_dir_all(root.join(".lccoding")).unwrap();
    let status_path = root.join(".lccoding/status.json");
    let manifest_path = root.join(".lccoding/CANONICAL-MANIFEST.json");
    fs::write(&status_path, product_formation_status()).unwrap();
    fs::write(
        &manifest_path,
        include_str!("../../../templates/CANONICAL-MANIFEST.json"),
    )
    .unwrap();
    let status_before = fs::metadata(&status_path).unwrap().modified().unwrap();
    let manifest_before = fs::metadata(&manifest_path).unwrap().modified().unwrap();
    let git = |arguments: &[&str]| {
        let result = Command::new("git")
            .args(arguments)
            .current_dir(&root)
            .env("GIT_AUTHOR_NAME", "LCCoding Test")
            .env("GIT_AUTHOR_EMAIL", "test@example.invalid")
            .env("GIT_COMMITTER_NAME", "LCCoding Test")
            .env("GIT_COMMITTER_EMAIL", "test@example.invalid")
            .status()
            .unwrap();
        assert!(result.success());
    };
    git(&["init", "--quiet"]);
    git(&["config", "core.autocrlf", "false"]);
    git(&[
        "add",
        ".lccoding/status.json",
        ".lccoding/CANONICAL-MANIFEST.json",
    ]);
    git(&["commit", "--quiet", "-m", "projection fixture"]);

    let snapshot = load_project_snapshot(&root).unwrap();
    assert_eq!(snapshot.project, "示例 Project");
    let refreshed = load_project_snapshot(&root).unwrap();
    assert_eq!(refreshed.project, "示例 Project");
    assert_eq!(
        fs::metadata(&status_path).unwrap().modified().unwrap(),
        status_before
    );
    assert_eq!(
        fs::metadata(&manifest_path).unwrap().modified().unwrap(),
        manifest_before
    );

    fs::remove_dir_all(root).unwrap();
}

#[test]
fn plural_maps_and_frozen_handoff_project_sanitized_product_metrics() {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let root = std::env::temp_dir().join(format!("lccoding-product-maps-{nonce}"));
    fs::create_dir_all(root.join(".lccoding")).unwrap();

    let subtrees = [
        (
            "product/workflows/core/capability.txt",
            b"core workflow\n".as_slice(),
        ),
        (
            "product/workflows/extra/capability.txt",
            b"extra workflow\n".as_slice(),
        ),
        ("product/ui/primary/surface.txt", b"primary ui\n".as_slice()),
        ("product/ui/admin/surface.txt", b"admin ui\n".as_slice()),
        (
            "product/simulations/primary/world.txt",
            b"primary simulation\n".as_slice(),
        ),
        (
            "product/simulations/resilience/world.txt",
            b"resilience simulation\n".as_slice(),
        ),
    ];
    for (path, content) in subtrees {
        let target = root.join(path);
        fs::create_dir_all(target.parent().unwrap()).unwrap();
        fs::write(target, content).unwrap();
    }
    fs::write(
        root.join(".lccoding/status.json"),
        baseline_complete_status(),
    )
    .unwrap();
    fs::write(
        root.join(".lccoding/CANONICAL-MANIFEST.json"),
        include_str!("../../../templates/CANONICAL-MANIFEST.json"),
    )
    .unwrap();
    git(&root, &["init", "--quiet"]);
    git(&root, &["config", "core.autocrlf", "false"]);
    git(&root, &["add", "."]);
    git(&root, &["commit", "--quiet", "-m", "frozen product"]);
    let frozen = git(&root, &["rev-parse", "HEAD"]);

    let wf_core =
        canonical_single_blob_hash("product/workflows/core/capability.txt", b"core workflow\n");
    let wf_extra = canonical_single_blob_hash(
        "product/workflows/extra/capability.txt",
        b"extra workflow\n",
    );
    let ui_primary = canonical_single_blob_hash("product/ui/primary/surface.txt", b"primary ui\n");
    let ui_admin = canonical_single_blob_hash("product/ui/admin/surface.txt", b"admin ui\n");
    let sim_primary = canonical_single_blob_hash(
        "product/simulations/primary/world.txt",
        b"primary simulation\n",
    );
    let sim_resilience = canonical_single_blob_hash(
        "product/simulations/resilience/world.txt",
        b"resilience simulation\n",
    );

    let workflow_map = format!(
        r#"# Workflow Map

- Primary product mainline ID: MAIN-1

| Workflow ID | Classification (CORE/EXTRA) | Implementation status | Subtree path | Component version | Content hash | Actors | Trigger | States / rules | Data / permissions | Failure / recovery | API contract / evidence | MCP contract / evidence | UI subtree references | Simulation subtree references | Evidence / attestation | Calabash trace | Primary mainline |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| WF-CORE | CORE | IMPLEMENTED | product/workflows/core | 1.0.0 | {wf_core} | Owner | start | stable | scoped | recover | API-WF-CORE | MCP-WF-CORE | UI-PRIMARY | SIM-PRIMARY | E-WF-CORE | C-WF-CORE | YES |
| WF-EXTRA | EXTRA | IMPLEMENTED | product/workflows/extra | 1.1.0 | {wf_extra} | Admin | start | stable | scoped | recover | API-WF-EXTRA | MCP-WF-EXTRA | UI-ADMIN | SIM-RESILIENCE | E-WF-EXTRA | C-WF-EXTRA | NO |
| WF-DEFERRED | EXTRA | UNIMPLEMENTED | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | Owner | later | concept | none | none | NOT_APPLICABLE | NOT_APPLICABLE | NONE | NONE | E-DEFERRED | C-DEFERRED | NO |
"#
    );
    let ui_map = format!(
        r#"# UI Map

- Primary product mainline ID: MAIN-1

| UI ID | Subtree path | Component version | Content hash | Actor | Surface / state | Actions / feedback | Workflow subtree references | Simulation subtree references | Evidence / attestation | Lock status | Primary mainline |
|---|---|---|---|---|---|---|---|---|---|---|---|
| UI-PRIMARY | product/ui/primary | 2.0.0 | {ui_primary} | Owner | primary | action | WF-CORE | SIM-PRIMARY | E-UI-PRIMARY | LOCKED | YES |
| UI-ADMIN | product/ui/admin | 2.1.0 | {ui_admin} | Admin | admin | action | WF-EXTRA | SIM-RESILIENCE | E-UI-ADMIN | LOCKED | NO |
"#
    );
    let simulation_world = format!(
        r#"# Simulation World

- Primary product mainline ID: MAIN-1

## Simulation subtree registry

| Simulation ID | Subtree path | Component version | Content hash | Foundation status | Workflow subtree references | UI subtree references | Primary mainline |
|---|---|---|---|---|---|---|---|
| SIM-PRIMARY | product/simulations/primary | 3.0.0 | {sim_primary} | REALIZED | WF-CORE | UI-PRIMARY | YES |
| SIM-RESILIENCE | product/simulations/resilience | 3.1.0 | {sim_resilience} | REALIZED | WF-EXTRA | UI-ADMIN | NO |
"#
    );
    let handoff = format!(
        r#"# Product Baseline Handoff

- Baseline ID / version / hash: BASELINE-1
- Project repository identity: github.com/example/product
- Project frozen exact commit SHA: {frozen}
- Calabash source: CALABASH-1
- Workflow Map: WORKFLOW-MAP
- UI Map: UI-MAP
- Simulation World: SIMULATION-WORLD
- Primary product mainline ID: MAIN-1
- Primary mainline Owner confirmation: OWNER_CONFIRMED: acceptance-1
- Acceptance boundaries: BOUNDARY-1
- Open Owner decisions: NONE
- Engineering exclusions: NONE
- Handoff status: COMPLETE

## Locked logical subtrees

| Subtree type | Subtree ID | Path | Component version | Content hash | Classification | API evidence | MCP evidence | Primary mainline | Related subtree IDs |
|---|---|---|---|---|---|---|---|---|---|
| WORKFLOW | WF-CORE | product/workflows/core | 1.0.0 | {wf_core} | CORE | API-WF-CORE | MCP-WF-CORE | YES | UI-PRIMARY, SIM-PRIMARY |
| WORKFLOW | WF-EXTRA | product/workflows/extra | 1.1.0 | {wf_extra} | EXTRA | API-WF-EXTRA | MCP-WF-EXTRA | NO | UI-ADMIN, SIM-RESILIENCE |
| UI | UI-PRIMARY | product/ui/primary | 2.0.0 | {ui_primary} | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | YES | WF-CORE, SIM-PRIMARY |
| UI | UI-ADMIN | product/ui/admin | 2.1.0 | {ui_admin} | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | NO | WF-EXTRA, SIM-RESILIENCE |
| SIMULATION | SIM-PRIMARY | product/simulations/primary | 3.0.0 | {sim_primary} | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | YES | WF-CORE, UI-PRIMARY |
| SIMULATION | SIM-RESILIENCE | product/simulations/resilience | 3.1.0 | {sim_resilience} | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | NO | WF-EXTRA, UI-ADMIN |
"#
    );

    let workflow_path = root.join(".lccoding/WORKFLOW-MAP.md");
    fs::write(&workflow_path, &workflow_map).unwrap();
    fs::write(root.join(".lccoding/UI-MAP.md"), &ui_map).unwrap();
    fs::write(
        root.join(".lccoding/SIMULATION-WORLD.md"),
        &simulation_world,
    )
    .unwrap();
    let handoff_path = root.join(".lccoding/PRODUCT-BASELINE-HANDOFF.md");
    fs::write(&handoff_path, &handoff).unwrap();
    git(&root, &["add", ".lccoding"]);
    git(&root, &["commit", "--quiet", "-m", "baseline records"]);

    let snapshot = load_project_snapshot(&root).unwrap();
    let value = serde_json::to_value(&snapshot).unwrap();
    assert_eq!(
        value["reports"]["simulation"]["rows"][0]["value"]["completed"],
        2
    );
    assert_eq!(
        value["reports"]["workflow"]["rows"][0]["value"]["completed"],
        1
    );
    assert_eq!(value["reports"]["workflow"]["rows"][0]["value"]["total"], 1);
    assert_eq!(
        value["reports"]["workflow"]["rows"][1]["value"]["completed"],
        1
    );
    assert_eq!(
        value["reports"]["workflow"]["rows"][2]["value"]["completed"],
        1
    );
    assert_eq!(
        value["reports"]["workflow"]["rows"][3]["value"]["completed"],
        2
    );
    assert_eq!(value["reports"]["ui"]["rows"][0]["value"]["completed"], 2);
    assert_eq!(
        value["reports"]["baseline"]["rows"][0]["value"]["status"],
        "COMPLIANT"
    );
    assert_eq!(
        value["reports"]["baseline"]["rows"][1]["value"]["completed"],
        6
    );
    assert_eq!(value["reports"]["baseline"]["rows"][1]["value"]["total"], 6);

    let wire = serde_json::to_string(&snapshot).unwrap();
    for forbidden in [
        "product/workflows/core",
        &frozen,
        &wf_core,
        "API-WF-CORE",
        "acceptance-1",
        "github.com/example/product",
    ] {
        assert!(!wire.contains(forbidden));
    }

    fs::write(
        root.join("product/workflows/core/capability.txt"),
        b"uncommitted worktree change\n",
    )
    .unwrap();
    assert!(load_project_snapshot(&root).is_ok());

    fs::write(
        &handoff_path,
        handoff.replacen(
            "| WORKFLOW | WF-CORE | product/workflows/core | 1.0.0 |",
            "| WORKFLOW | WF-CORE | product/workflows/core | 9.9.9 |",
            1,
        ),
    )
    .unwrap();
    assert_eq!(
        load_project_snapshot(&root).unwrap_err().code(),
        "BI_RECORD_INCONSISTENT",
    );

    fs::write(&handoff_path, &handoff).unwrap();
    fs::write(
        &workflow_path,
        workflow_map.replacen("| 1.0.0 |", "| banana |", 1),
    )
    .unwrap();
    assert_eq!(
        load_project_snapshot(&root).unwrap_err().code(),
        "BI_RECORD_INVALID",
    );

    let fake_hash = format!("sha256:{}", "0".repeat(64));
    fs::write(&workflow_path, workflow_map.replace(&wf_core, &fake_hash)).unwrap();
    fs::write(&handoff_path, handoff.replace(&wf_core, &fake_hash)).unwrap();
    assert_eq!(
        load_project_snapshot(&root).unwrap_err().code(),
        "BI_RECORD_INCONSISTENT",
    );

    fs::write(&workflow_path, &workflow_map).unwrap();
    fs::write(&handoff_path, handoff.replace(&frozen, &"0".repeat(40))).unwrap();
    assert_eq!(
        load_project_snapshot(&root).unwrap_err().code(),
        "BI_GIT_IDENTITY_INVALID",
    );

    fs::remove_dir_all(root).unwrap();
}
