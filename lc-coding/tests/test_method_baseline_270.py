from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile


root = Path(__file__).resolve().parents[2]
validator_path = root / "lc-coding/scripts/validate_method_baseline.py"
project_validator_path = root / "lc-coding/scripts/validate_project.py"
exact_commit = "0031c776eaabba21aca66b9d8aa4382f6dfe6015"
required_paths = [
    "SPEC.md",
    "calabash/contracts/project-calabash-baseline.schema.json",
    "calabash/templates/upgrade-receipt-template.json",
]
forbidden_machine_path = "D:" + "\\LCcoding\\calabash"
assert forbidden_machine_path not in Path(__file__).read_text(encoding="utf-8")

assert validator_path.exists(), "Method Baseline validator is absent"
spec = importlib.util.spec_from_file_location("lccoding_method_baseline", validator_path)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)
project_spec = importlib.util.spec_from_file_location("lccoding_project_validator", project_validator_path)
project_validator = importlib.util.module_from_spec(project_spec)
project_spec.loader.exec_module(project_validator)


def git(repo, *arguments, check=True):
    return subprocess.run(
        ["git", *arguments], cwd=repo, capture_output=True, check=check
    )


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))


def init_repo(path, *, tree_spec=False, omit_spec=False):
    path.mkdir(parents=True)
    git(path, "init", "--quiet")
    git(path, "config", "user.email", "fixture@example.com")
    git(path, "config", "user.name", "Fixture")
    if tree_spec:
        write(path / "SPEC.md/child.txt", "tree, not a regular blob\n")
    elif not omit_spec:
        write(path / "SPEC.md", "# Product definition\n")
    write(path / required_paths[1], b'{"title":"baseline"}\n')
    write(path / required_paths[2], b'{"title":"upgrade"}\n')
    git(path, "add", "--all")
    git(path, "commit", "--quiet", "-m", "canonical definition")
    return git(path, "rev-parse", "HEAD").stdout.decode().strip()


def blob_hash(repo, commit, path):
    result = git(repo, "cat-file", "blob", f"{commit}:{path}", check=False)
    if result.returncode:
        return "sha256:" + "0" * 64
    return "sha256:" + hashlib.sha256(result.stdout).hexdigest()


def combined_hash(detail):
    payload = {
        "version": detail["version"],
        "canonical_repository": detail["canonical_repository"],
        "exact_commit": detail["exact_commit"],
        "referenced_files": sorted(
            (
                {"path": item["path"], "sha256": item["sha256"]}
                for item in detail["referenced_files"]
            ),
            key=lambda item: item["path"],
        ),
    }
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def detail_for(repo, commit):
    detail = {
        "version": "2.5.0",
        "canonical_repository": "github.com/DWG7318/calabash",
        "exact_commit": commit,
        "referenced_files": [
            {"path": path, "sha256": blob_hash(repo, commit, path)}
            for path in required_paths
        ],
    }
    detail["combined_identity_hash"] = combined_hash(detail)
    return detail


def records_for(detail):
    manifest = {"calabash": {"version": detail["version"], "hash": detail["combined_identity_hash"]}}
    lock = {"calabash": copy.deepcopy(detail)}
    return manifest, lock


def refresh_combined(detail):
    detail["combined_identity_hash"] = combined_hash(detail)


def write_records(base, manifest, lock):
    manifest_path = base / "CANONICAL-MANIFEST.json"
    lock_path = base / "INTERPRETATION-LOCK.json"
    write(manifest_path, json.dumps(manifest, indent=2) + "\n")
    write(lock_path, json.dumps(lock, indent=2) + "\n")
    return manifest_path, lock_path


def assert_record_invalid(manifest, lock, label):
    assert validator.validate_method_baseline_records(manifest, lock), label


def assert_repository_invalid(base, manifest, lock, repo, label):
    manifest_path, lock_path = write_records(base, manifest, lock)
    assert validator.validate_method_baseline(manifest_path, lock_path, repo), label


with tempfile.TemporaryDirectory(prefix="lccoding-method-baseline-") as temporary:
    base = Path(temporary)
    repo = base / "calabash"
    commit = init_repo(repo)
    detail = detail_for(repo, commit)
    manifest, lock = records_for(detail)
    assert validator.validate_method_baseline_records(manifest, lock) == []
    manifest_path, lock_path = write_records(base / "valid", manifest, lock)
    assert validator.validate_method_baseline(manifest_path, lock_path, repo) == []

    write(repo / "SPEC.md", "# changed worktree and later commit\n")
    git(repo, "add", "SPEC.md")
    git(repo, "commit", "--quiet", "-m", "later work")
    assert git(repo, "rev-parse", "HEAD").stdout.decode().strip() != commit
    write(repo / "SPEC.md", "# uncommitted worktree drift\n")
    assert git(repo, "status", "--porcelain").stdout
    assert validator.validate_method_baseline(manifest_path, lock_path, repo) == []

    cli = subprocess.run(
        [
            sys.executable,
            str(validator_path),
            "--manifest",
            str(manifest_path),
            "--lock",
            str(lock_path),
            "--calabash-repository",
            str(repo),
        ],
        capture_output=True,
        text=True,
    )
    assert cli.returncode == 0, cli.stdout + cli.stderr

    for label, mutate in (
        ("symbolic commit", lambda value: value.update(exact_commit="HEAD")),
        ("random commit", lambda value: value.update(exact_commit="0" * 40)),
        ("wrong version", lambda value: value.update(version="2.4.0")),
        ("wrong repository", lambda value: value.update(canonical_repository="github.com/example/calabash")),
    ):
        changed = copy.deepcopy(detail)
        mutate(changed)
        refresh_combined(changed)
        changed_manifest, changed_lock = records_for(changed)
        assert_repository_invalid(base / label, changed_manifest, changed_lock, repo, label)

    for label, mutate in (
        ("missing path", lambda files: files.pop()),
        ("extra path", lambda files: files.append({"path": "README.md", "sha256": "sha256:" + "a" * 64})),
        ("duplicate path", lambda files: files.append(copy.deepcopy(files[0]))),
        ("unsafe path", lambda files: files.__setitem__(0, {"path": "../SPEC.md", "sha256": files[0]["sha256"]})),
    ):
        changed = copy.deepcopy(detail)
        mutate(changed["referenced_files"])
        refresh_combined(changed)
        changed_manifest, changed_lock = records_for(changed)
        assert_record_invalid(changed_manifest, changed_lock, label)

    changed = copy.deepcopy(detail)
    changed["referenced_files"][0]["sha256"] = "sha256:" + "f" * 64
    refresh_combined(changed)
    changed_manifest, changed_lock = records_for(changed)
    assert_repository_invalid(base / "blob-mismatch", changed_manifest, changed_lock, repo, "committed hash mismatch")

    changed = copy.deepcopy(detail)
    changed["combined_identity_hash"] = "sha256:" + "e" * 64
    changed_manifest, changed_lock = records_for(changed)
    changed_lock["calabash"]["combined_identity_hash"] = "sha256:" + "e" * 64
    changed_manifest["calabash"]["hash"] = "sha256:" + "e" * 64
    assert_record_invalid(changed_manifest, changed_lock, "combined hash mismatch")

    changed_manifest, changed_lock = records_for(detail)
    changed_manifest["calabash"]["hash"] = "sha256:" + "d" * 64
    assert_record_invalid(changed_manifest, changed_lock, "Manifest and Lock mismatch")

    for label, changed_manifest, changed_lock in (
        ("manifest-only claim", {"calabash": {"version": "2.5.0", "hash": ""}}, {}),
        ("malformed manifest value type", {"calabash": {"version": [], "hash": ""}}, {}),
        ("lock-only claim", {"calabash": {"version": "", "hash": ""}}, {"calabash": detail}),
        ("partial detail", {"calabash": {"version": "2.5.0", "hash": detail["combined_identity_hash"]}}, {"calabash": {"version": "2.5.0"}}),
        ("manifest extra identity", {"calabash": {"version": "2.5.0", "hash": detail["combined_identity_hash"], "exact_commit": commit}}, {"calabash": detail}),
        ("lock extra identity", *records_for({**detail, "tag": "v2.5.0"})),
    ):
        assert_record_invalid(changed_manifest, changed_lock, label)

    assert validator.validate_method_baseline_records(
        {"calabash": {"version": "", "hash": ""}}, {}
    ) == []
    assert project_validator.validate_method_baseline_records(
        {"calabash": {"version": "2.5.0", "hash": ""}}, {}
    )

    worktree_only_repo = base / "worktree-only"
    worktree_only_commit = init_repo(worktree_only_repo, omit_spec=True)
    write(worktree_only_repo / "SPEC.md", "not committed\n")
    worktree_detail = detail_for(worktree_only_repo, worktree_only_commit)
    worktree_detail["referenced_files"][0]["sha256"] = "sha256:" + hashlib.sha256(
        (worktree_only_repo / "SPEC.md").read_bytes()
    ).hexdigest()
    refresh_combined(worktree_detail)
    worktree_manifest, worktree_lock = records_for(worktree_detail)
    assert_repository_invalid(
        base / "worktree-only-records",
        worktree_manifest,
        worktree_lock,
        worktree_only_repo,
        "worktree-only path",
    )

    tree_repo = base / "tree-path"
    tree_commit = init_repo(tree_repo, tree_spec=True)
    tree_detail = detail_for(tree_repo, tree_commit)
    refresh_combined(tree_detail)
    tree_manifest, tree_lock = records_for(tree_detail)
    assert_repository_invalid(base / "tree-records", tree_manifest, tree_lock, tree_repo, "tree path")

pinned_detail = {
    "version": "2.5.0",
    "canonical_repository": "github.com/DWG7318/calabash",
    "exact_commit": exact_commit,
    "referenced_files": [
        {"path": "SPEC.md", "sha256": "sha256:666f17e0e650e9cf37ad3452eab6db99adf1e6f62b140f8b934176af932c3c79"},
        {"path": required_paths[1], "sha256": "sha256:cd215d03beca3b28cdeeb0ebd7fe51c6d07fbbf17af0753307a73e8df729d7f1"},
        {"path": required_paths[2], "sha256": "sha256:27db7b330b400aba8124fb76014d88369555092433126d36ab51b6a0fdce9449"},
    ],
    "combined_identity_hash": "sha256:74602032de04ca47c4ccc9d661119ae1d08913dfe0c5361759798697c0310b21",
}
template_manifest = json.loads((root / "lc-coding/templates/CANONICAL-MANIFEST.json").read_text(encoding="utf-8"))
template_lock = json.loads((root / "lc-coding/templates/INTERPRETATION-LOCK.json").read_text(encoding="utf-8"))
assert template_manifest["calabash"] == {
    "version": pinned_detail["version"],
    "hash": pinned_detail["combined_identity_hash"],
}
assert template_lock["calabash"] == pinned_detail

external_repository = os.environ.get("LCCODING_CALABASH_REPOSITORY")
if external_repository:
    assert validator.validate_method_baseline(
        root / "lc-coding/templates/CANONICAL-MANIFEST.json",
        root / "lc-coding/templates/INTERPRETATION-LOCK.json",
        Path(external_repository),
    ) == []
    print("PASS: external canonical Calabash repository matches the pinned Method Baseline")
else:
    print(
        "SKIP: external canonical Calabash repository verification not run "
        "(LCCODING_CALABASH_REPOSITORY unset)"
    )

if os.environ.get("LCCODING_METHOD_BASELINE_PORTABILITY_CHILD") != "1":
    portable_environment = os.environ.copy()
    portable_environment.pop("LCCODING_CALABASH_REPOSITORY", None)
    portable_environment["LCCODING_METHOD_BASELINE_PORTABILITY_CHILD"] = "1"
    portable = subprocess.run(
        [sys.executable, str(Path(__file__).resolve())],
        cwd=root,
        env=portable_environment,
        capture_output=True,
        text=True,
    )
    assert portable.returncode == 0, portable.stdout + portable.stderr
    assert "SKIP: external canonical Calabash repository verification not run" in portable.stdout

print("PASS: LCCoding Method Baseline binds exact Calabash commit-tree bytes")
