use std::fs;
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};

use lccoding::projection::{load_project_snapshot, snapshot_from_status};
use lccoding::records::manifest::parse_manifest;
use lccoding::records::status::parse_status;
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
            "\"current_phase\": \"ENGINEERING_RUNS\"",
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

    for phase in value["phases"].as_array().unwrap() {
        for step in phase["steps"].as_array().unwrap() {
            if let Some(report) = step["report"].as_str() {
                assert_eq!(value["reports"][report]["state"], step["state"]);
            }
        }
    }
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
    let unsupported = valid.replace("\"2.5.1\"", "\"2.3.0\"");

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

    let mismatched = manifest_text.replace("\"2.5.1\"", "\"2.4.1\"");
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
