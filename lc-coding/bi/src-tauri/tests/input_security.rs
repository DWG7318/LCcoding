use std::fs;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

use lccoding::input::{read_project_record, ProjectRecord, MAX_RECORD_BYTES};


fn project_root(label: &str) -> PathBuf {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let root = std::env::temp_dir().join(format!("lccoding-input-{label}-{nonce}"));
    fs::create_dir_all(root.join(".lccoding")).unwrap();
    root
}


#[test]
fn a_fixed_record_is_read_once_without_modifying_the_project() {
    let root = project_root("stable");
    let record = root.join(".lccoding/status.json");
    fs::write(&record, b"{\"record_role\":\"AUTHORITATIVE_PROJECT_STATUS\"}").unwrap();
    let before = fs::metadata(&record).unwrap();

    let text = read_project_record(&root, ProjectRecord::Status)
        .unwrap()
        .expect("required status");

    assert_eq!(text, "{\"record_role\":\"AUTHORITATIVE_PROJECT_STATUS\"}");
    let after = fs::metadata(&record).unwrap();
    assert_eq!(after.len(), before.len());
    assert_eq!(after.modified().unwrap(), before.modified().unwrap());
    fs::remove_dir_all(root).unwrap();
}


#[test]
fn record_limits_and_encoding_fail_with_path_free_codes() {
    let root = project_root("limits");
    let record = root.join(".lccoding/status.json");

    fs::write(&record, vec![b'x'; MAX_RECORD_BYTES + 1]).unwrap();
    let oversized = read_project_record(&root, ProjectRecord::Status).unwrap_err();
    assert_eq!(oversized.code(), "BI_RESOURCE_LIMIT");

    fs::write(&record, [0xff, 0xfe]).unwrap();
    let encoding = read_project_record(&root, ProjectRecord::Status).unwrap_err();
    assert_eq!(encoding.code(), "BI_RECORD_INVALID");

    for rendered in [format!("{oversized:?} {oversized}"), format!("{encoding:?} {encoding}")] {
        assert!(!rendered.contains(root.to_string_lossy().as_ref()));
        assert!(!rendered.contains("status.json"));
    }
    fs::remove_dir_all(root).unwrap();
}


#[cfg(windows)]
#[test]
fn a_record_symlink_is_never_followed() {
    use std::os::windows::fs::symlink_file;

    let root = project_root("symlink");
    let outside = root.with_extension("outside.json");
    fs::write(&outside, b"private").unwrap();
    let record = root.join(".lccoding/status.json");
    if symlink_file(&outside, &record).is_ok() {
        let error = read_project_record(&root, ProjectRecord::Status).unwrap_err();
        assert_eq!(error.code(), "BI_RECORD_INVALID");
        fs::remove_file(record).unwrap();
    }
    fs::remove_file(outside).unwrap();
    fs::remove_dir_all(root).unwrap();
}


#[cfg(windows)]
#[test]
fn a_dangling_optional_record_is_invalid_not_absent() {
    use std::process::Command;

    let root = project_root("dangling");
    fs::write(root.join(".lccoding/status.json"), b"{}").unwrap();
    let manifest = root.join(".lccoding/CANONICAL-MANIFEST.json");
    let target = root.join("temporary-target");
    fs::create_dir(&target).unwrap();
    let created = Command::new("powershell.exe")
        .args([
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "New-Item -ItemType Junction -Path $env:LCCODING_TEST_LINK -Target $env:LCCODING_TEST_TARGET | Out-Null",
        ])
        .env("LCCODING_TEST_LINK", &manifest)
        .env("LCCODING_TEST_TARGET", &target)
        .output()
        .unwrap();
    assert!(
        created.status.success(),
        "junction fixture failed: {} {}",
        String::from_utf8_lossy(&created.stdout),
        String::from_utf8_lossy(&created.stderr),
    );
    fs::remove_dir(&target).unwrap();

    let error = read_project_record(&root, ProjectRecord::Manifest).unwrap_err();
    assert_eq!(error.code(), "BI_RECORD_INVALID");

    fs::remove_dir(manifest).unwrap();
    fs::remove_dir_all(root).unwrap();
}
