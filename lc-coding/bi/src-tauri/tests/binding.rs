use std::ffi::OsString;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use lccoding::binding::{parse_launch_args, BindingState, LaunchRequest};


fn temp_directory(name: &str) -> PathBuf {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let path = std::env::temp_dir().join(format!("lccoding-bi-{name}-{nonce}"));
    fs::create_dir_all(path.join(".lccoding")).unwrap();
    path
}


fn args(values: &[&str]) -> Vec<OsString> {
    values.iter().map(OsString::from).collect()
}


#[test]
fn launch_arguments_accept_no_root_or_one_explicit_project() {
    assert_eq!(
        parse_launch_args(args(&["lccoding-bi"])).unwrap(),
        LaunchRequest::Unbound,
    );
    assert_eq!(
        parse_launch_args(args(&["lccoding-bi", "--project", "project-root"])).unwrap(),
        LaunchRequest::Project(PathBuf::from("project-root")),
    );

    for invalid in [
        args(&["lccoding-bi", "--project"]),
        args(&["lccoding-bi", "--unknown", "root"]),
        args(&["lccoding-bi", "--project", "one", "two"]),
    ] {
        let error = parse_launch_args(invalid).unwrap_err();
        assert_eq!(error.code(), "BI_ARGUMENT_INVALID");
        assert_eq!(error.to_string(), "BI_ARGUMENT_INVALID");
    }
}


#[test]
fn one_process_binds_one_canonical_directory_and_rejects_replacement() {
    let first = temp_directory("first");
    let second = temp_directory("second");
    let state = BindingState::default();

    state.bind_root(&first).unwrap();
    assert!(state.is_bound());

    let error = state.bind_root(&second).unwrap_err();
    assert_eq!(error.code(), "BI_PROJECT_ALREADY_BOUND");
    let rendered = format!("{error:?} {error}");
    assert!(!rendered.contains(first.to_string_lossy().as_ref()));
    assert!(!rendered.contains(second.to_string_lossy().as_ref()));

    fs::remove_dir_all(first).unwrap();
    fs::remove_dir_all(second).unwrap();
}


#[test]
fn invalid_roots_fail_with_path_free_codes() {
    let state = BindingState::default();
    let missing = Path::new("C:/private/missing/project");
    let error = state.bind_root(missing).unwrap_err();
    assert_eq!(error.code(), "BI_ROOT_INVALID");
    let rendered = format!("{error:?} {error}");
    assert!(!rendered.contains("private"));
    assert!(!rendered.contains("missing"));
}


#[test]
fn packaged_binary_embeds_the_local_frontend() {
    let manifest = include_str!("../Cargo.toml");
    assert!(manifest.contains("default = [\"custom-protocol\"]"));
    assert!(manifest.contains("custom-protocol = [\"tauri/custom-protocol\"]"));
}
