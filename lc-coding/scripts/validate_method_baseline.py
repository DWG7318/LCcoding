#!/usr/bin/env python3
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import re
import subprocess


CALABASH_VERSION = "2.5.0"
CALABASH_REPOSITORY = "github.com/DWG7318/calabash"
REFERENCED_PATHS = [
    "SPEC.md",
    "calabash/contracts/project-calabash-baseline.schema.json",
    "calabash/templates/upgrade-receipt-template.json",
]
MANIFEST_KEYS = {"version", "hash"}
LOCK_KEYS = {
    "version",
    "canonical_repository",
    "exact_commit",
    "referenced_files",
    "combined_identity_hash",
}
FILE_KEYS = {"path", "sha256"}
EXACT_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
EXACT_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def _closed_path(value):
    if not isinstance(value, str) or "\\" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and value == path.as_posix() and all(
        part not in {"", ".", ".."} for part in path.parts
    )


def combined_identity_hash(record):
    try:
        payload = {
            "version": record["version"],
            "canonical_repository": record["canonical_repository"],
            "exact_commit": record["exact_commit"],
            "referenced_files": sorted(
                (
                    {"path": item["path"], "sha256": item["sha256"]}
                    for item in record["referenced_files"]
                ),
                key=lambda item: item["path"],
            ),
        }
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    except (KeyError, TypeError):
        return None
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def validate_method_baseline_records(manifest, lock):
    errors = []
    if not isinstance(manifest, dict) or not isinstance(lock, dict):
        return ["Method Baseline Manifest and Interpretation Lock must be objects"]

    manifest_record = manifest.get("calabash")
    lock_present = "calabash" in lock
    lock_record = lock.get("calabash")
    manifest_claimed = isinstance(manifest_record, dict) and any(
        value is not None and value != "" for value in manifest_record.values()
    )
    claimed = manifest_claimed or lock_present

    if not claimed:
        if manifest_record is not None and manifest_record != {"version": "", "hash": ""}:
            errors.append("legacy Calabash bootstrap record must be exactly blank version/hash")
        return errors

    if not isinstance(manifest_record, dict):
        errors.append("Canonical Manifest Calabash record must be an object")
        manifest_record = {}
    if set(manifest_record) != MANIFEST_KEYS:
        errors.append("Canonical Manifest Calabash record must contain only version and hash")
    if not isinstance(lock_record, dict):
        errors.append("Interpretation Lock Calabash detail record is required")
        lock_record = {}
    if set(lock_record) != LOCK_KEYS:
        errors.append("Interpretation Lock Calabash detail record has missing or unknown fields")

    if manifest_record.get("version") != CALABASH_VERSION:
        errors.append("Canonical Manifest Calabash version must be 2.5.0")
    if lock_record.get("version") != CALABASH_VERSION:
        errors.append("Interpretation Lock Calabash version must be 2.5.0")
    if lock_record.get("canonical_repository") != CALABASH_REPOSITORY:
        errors.append("Interpretation Lock Calabash canonical repository is invalid")
    commit = lock_record.get("exact_commit")
    if not isinstance(commit, str) or not EXACT_COMMIT_RE.fullmatch(commit):
        errors.append("Interpretation Lock Calabash exact commit must be 40 lowercase hex")

    referenced = lock_record.get("referenced_files")
    if not isinstance(referenced, list):
        errors.append("Interpretation Lock Calabash referenced_files must be a list")
        referenced = []
    paths = []
    for index, item in enumerate(referenced):
        prefix = f"Calabash referenced file {index + 1}"
        if not isinstance(item, dict):
            errors.append(prefix + " must be an object")
            continue
        if set(item) != FILE_KEYS:
            errors.append(prefix + " must contain only path and sha256")
        path = item.get("path")
        digest = item.get("sha256")
        if not _closed_path(path):
            errors.append(prefix + " path is unsafe")
        else:
            paths.append(path)
        if not isinstance(digest, str) or not EXACT_HASH_RE.fullmatch(digest):
            errors.append(prefix + " hash must be lowercase SHA-256")
    if paths != sorted(paths):
        errors.append("Calabash referenced file paths must be sorted")
    if len(paths) != len(set(paths)):
        errors.append("Calabash referenced file paths must be unique")
    if set(paths) != set(REFERENCED_PATHS) or len(paths) != len(REFERENCED_PATHS):
        errors.append("Calabash referenced file paths must match the closed required set")

    computed = combined_identity_hash(lock_record)
    recorded = lock_record.get("combined_identity_hash")
    if not isinstance(recorded, str) or not EXACT_HASH_RE.fullmatch(recorded):
        errors.append("Interpretation Lock Calabash combined identity hash is invalid")
    if computed is None or recorded != computed:
        errors.append("Interpretation Lock Calabash combined identity hash mismatch")
    if manifest_record.get("hash") != recorded:
        errors.append("Canonical Manifest and Interpretation Lock Calabash hash mismatch")
    if manifest_record.get("version") != lock_record.get("version"):
        errors.append("Canonical Manifest and Interpretation Lock Calabash version mismatch")
    return errors


def _git(repository, *arguments):
    return subprocess.run(
        ["git", *arguments], cwd=repository, capture_output=True, check=False
    )


def validate_method_baseline(manifest_path, lock_path, calabash_repository):
    errors = []
    try:
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        lock = json.loads(Path(lock_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return ["cannot read Method Baseline JSON: " + str(error)]
    errors.extend(validate_method_baseline_records(manifest, lock))
    record = lock.get("calabash") if isinstance(lock, dict) else None
    if not isinstance(record, dict) or errors:
        return errors

    repository = Path(calabash_repository)
    inside = _git(repository, "rev-parse", "--is-inside-work-tree") if repository.is_dir() else None
    if inside is None or inside.returncode or inside.stdout.strip() != b"true":
        return errors + ["Calabash repository must be a Git worktree"]
    commit = record.get("exact_commit")
    if not isinstance(commit, str) or not EXACT_COMMIT_RE.fullmatch(commit):
        return errors
    object_type = _git(repository, "cat-file", "-t", commit)
    if object_type.returncode or object_type.stdout.strip() != b"commit":
        return errors + ["Calabash exact commit does not resolve to a commit object"]

    for item in record["referenced_files"]:
        path = item["path"]
        listing = _git(repository, "ls-tree", "-z", commit, "--", path)
        entries = [entry for entry in listing.stdout.split(b"\0") if entry]
        if listing.returncode or len(entries) != 1 or b"\t" not in entries[0]:
            errors.append("Calabash referenced path is absent at exact commit: " + path)
            continue
        metadata, actual_path = entries[0].split(b"\t", 1)
        parts = metadata.split()
        if actual_path.decode("utf-8", errors="replace") != path or len(parts) != 3:
            errors.append("Calabash referenced path identity mismatch: " + path)
            continue
        mode, object_kind, object_id = parts
        if mode not in {b"100644", b"100755"} or object_kind != b"blob":
            errors.append("Calabash referenced path is not a regular blob: " + path)
            continue
        blob = _git(repository, "cat-file", "blob", object_id.decode("ascii"))
        if blob.returncode:
            errors.append("cannot read Calabash blob at exact commit: " + path)
            continue
        actual_hash = "sha256:" + hashlib.sha256(blob.stdout).hexdigest()
        if actual_hash != item["sha256"]:
            errors.append("Calabash referenced blob hash mismatch: " + path)
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--calabash-repository", required=True)
    args = parser.parse_args()
    errors = validate_method_baseline(args.manifest, args.lock, args.calabash_repository)
    if errors:
        print("FAIL")
        print("\n".join(errors))
        raise SystemExit(1)
    print("PASS: LCCoding Method Baseline matches exact Calabash commit-tree bytes")


if __name__ == "__main__":
    main()
