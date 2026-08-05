use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};

use lccoding::git_reader::{GitProject, MAX_GIT_BLOB_BYTES};


fn temp_path(label: &str) -> PathBuf {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    std::env::temp_dir().join(format!("lccoding-git-{label}-{nonce}"))
}


fn git(root: &Path, arguments: &[&str]) -> String {
    let output = Command::new("git")
        .args(arguments)
        .current_dir(root)
        .env("GIT_AUTHOR_NAME", "LCCoding Test")
        .env("GIT_AUTHOR_EMAIL", "test@example.invalid")
        .env("GIT_COMMITTER_NAME", "LCCoding Test")
        .env("GIT_COMMITTER_EMAIL", "test@example.invalid")
        .output()
        .unwrap();
    assert!(output.status.success(), "git failed: {}", String::from_utf8_lossy(&output.stderr));
    String::from_utf8(output.stdout).unwrap().trim().to_owned()
}


fn committed_project(label: &str) -> (PathBuf, String) {
    let root = temp_path(label);
    fs::create_dir_all(root.join(".lccoding")).unwrap();
    git(&root, &["init", "--quiet"]);
    fs::write(root.join(".lccoding/status.json"), b"frozen").unwrap();
    git(&root, &["add", ".lccoding/status.json"]);
    git(&root, &["commit", "--quiet", "-m", "fixture"]);
    let commit = git(&root, &["rev-parse", "HEAD"]);
    (root, commit)
}


#[test]
fn gix_reads_the_exact_commit_blob_instead_of_worktree_content() {
    let (root, commit) = committed_project("frozen");
    fs::write(root.join(".lccoding/status.json"), b"uncommitted-private-change").unwrap();

    let project = GitProject::open(&root).unwrap();
    let bytes = project
        .read_blob_at(&commit, Path::new(".lccoding/status.json"))
        .unwrap();

    assert_eq!(bytes, b"frozen");
    fs::remove_dir_all(root).unwrap();
}


#[test]
fn revisions_are_exact_commits_and_fail_without_leaking_repository_details() {
    let (root, commit) = committed_project("identity");
    let project = GitProject::open(&root).unwrap();

    for rejected in ["HEAD", "main", "v2.5.0", "0000000000000000000000000000000000000000"] {
        let error = project
            .read_blob_at(rejected, Path::new(".lccoding/status.json"))
            .unwrap_err();
        assert_eq!(error.code(), "BI_GIT_IDENTITY_INVALID");
        let rendered = format!("{error:?} {error}");
        assert!(!rendered.contains(root.to_string_lossy().as_ref()));
        assert!(!rendered.contains(rejected));
    }

    let missing = project
        .read_blob_at(&commit, Path::new(".lccoding/missing.json"))
        .unwrap_err();
    assert_eq!(missing.code(), "BI_GIT_IDENTITY_INVALID");
    fs::remove_dir_all(root).unwrap();
}


#[test]
fn an_ordinary_linked_worktree_is_supported_without_running_hooks() {
    let (root, commit) = committed_project("linked-main");
    let hook_marker = root.join("hook-ran");
    let hooks = root.join(".git/hooks");
    fs::write(
        hooks.join("post-checkout"),
        format!("#!/bin/sh\nprintf hook > '{}'\n", hook_marker.display()),
    )
    .unwrap();
    let linked = temp_path("linked-worktree");
    git(&root, &["worktree", "add", "--quiet", "--detach", linked.to_str().unwrap(), &commit]);
    if hook_marker.exists() {
        fs::remove_file(&hook_marker).unwrap();
    }

    let project = GitProject::open(&linked).unwrap();
    assert_eq!(
        project
            .read_blob_at(&commit, Path::new(".lccoding/status.json"))
            .unwrap(),
        b"frozen"
    );
    assert!(!hook_marker.exists());

    git(&root, &["worktree", "remove", "--force", linked.to_str().unwrap()]);
    fs::remove_dir_all(root).unwrap();
}


#[test]
fn git_symlink_entries_and_oversized_blobs_fail_closed() {
    let (root, _) = committed_project("hostile-tree");
    let oversized = root.join("oversized.bin");
    fs::write(&oversized, vec![b'x'; MAX_GIT_BLOB_BYTES + 1]).unwrap();
    let oversized_id = git(&root, &["hash-object", "-w", oversized.to_str().unwrap()]);
    git(
        &root,
        &[
            "update-index",
            "--add",
            "--cacheinfo",
            &format!("100644,{oversized_id},.lccoding/oversized.json"),
        ],
    );

    let link_source = root.join("link-source.txt");
    fs::write(&link_source, b"outside-private-target").unwrap();
    let link_id = git(&root, &["hash-object", "-w", link_source.to_str().unwrap()]);
    git(
        &root,
        &[
            "update-index",
            "--add",
            "--cacheinfo",
            &format!("120000,{link_id},.lccoding/link.json"),
        ],
    );
    git(&root, &["commit", "--quiet", "-m", "hostile tree"]);
    let commit = git(&root, &["rev-parse", "HEAD"]);
    let project = GitProject::open(&root).unwrap();

    let oversized_error = project
        .read_blob_at(&commit, Path::new(".lccoding/oversized.json"))
        .unwrap_err();
    assert_eq!(oversized_error.code(), "BI_RESOURCE_LIMIT");
    let link_error = project
        .read_blob_at(&commit, Path::new(".lccoding/link.json"))
        .unwrap_err();
    assert_eq!(link_error.code(), "BI_GIT_IDENTITY_INVALID");

    fs::remove_dir_all(root).unwrap();
}


#[test]
fn an_arbitrary_gitdir_file_cannot_borrow_another_repository() {
    let (real, _) = committed_project("real-owner");
    let imposter = temp_path("imposter");
    fs::create_dir_all(imposter.join(".lccoding")).unwrap();
    fs::write(imposter.join(".lccoding/status.json"), b"imposter").unwrap();
    fs::write(
        imposter.join(".git"),
        format!("gitdir: {}\n", real.join(".git").display()),
    )
    .unwrap();

    let error = GitProject::open(&imposter).err().expect("unsafe gitdir rejected");
    assert_eq!(error.code(), "BI_GIT_REPOSITORY_INVALID");
    assert!(!format!("{error:?} {error}").contains(real.to_string_lossy().as_ref()));

    fs::remove_dir_all(imposter).unwrap();
    fs::remove_dir_all(real).unwrap();
}
