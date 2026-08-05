from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile


root = Path(__file__).resolve().parents[2]
workflow_relative = Path(".github/workflows/release-bi.yml")
expected_hash = json.loads((root / "FILE_HASHES.json").read_text(encoding="utf-8"))[
    workflow_relative.as_posix()
]


def git(*arguments: str, cwd: Path) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def snapshot_repository(destination: Path, include_policy: bool) -> None:
    listed = git("ls-files", "-co", "--exclude-standard", "-z", cwd=root)
    for relative in filter(None, listed.split("\0")):
        if not include_policy and relative == ".gitattributes":
            continue
        source = root / relative
        if not source.is_file():
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    git("init", "--initial-branch=main", cwd=destination)
    git("config", "user.name", "LCCoding checkout policy test", cwd=destination)
    git("config", "user.email", "checkout-policy@example.invalid", cwd=destination)
    git("add", "--all", cwd=destination)
    git("commit", "-m", "test snapshot", cwd=destination)


def windows_style_clone(source: Path, destination: Path) -> None:
    subprocess.run(
        [
            "git",
            "clone",
            "-c",
            "core.autocrlf=true",
            "--no-hardlinks",
            str(source),
            str(destination),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


with tempfile.TemporaryDirectory(prefix="lccoding-checkout-policy-") as temporary:
    temporary_root = Path(temporary)

    ungoverned_source = temporary_root / "ungoverned-source"
    ungoverned_source.mkdir()
    snapshot_repository(ungoverned_source, include_policy=False)
    ungoverned_clone = temporary_root / "ungoverned-clone"
    windows_style_clone(ungoverned_source, ungoverned_clone)
    ungoverned_hash = hashlib.sha256(
        (ungoverned_clone / workflow_relative).read_bytes()
    ).hexdigest()
    assert ungoverned_hash != expected_hash, "the regression setup must reproduce byte drift"

    policy = root / ".gitattributes"
    assert policy.is_file(), "repository LF checkout policy is missing"
    assert policy.read_text(encoding="utf-8") == "* text=auto eol=lf\n"

    governed_source = temporary_root / "governed-source"
    governed_source.mkdir()
    snapshot_repository(governed_source, include_policy=True)
    governed_clone = temporary_root / "governed-clone"
    windows_style_clone(governed_source, governed_clone)
    eol = git("ls-files", "--eol", "--", workflow_relative.as_posix(), cwd=governed_clone)
    assert "i/lf" in eol and "w/lf" in eol and "attr/text=auto eol=lf" in eol, eol
    governed_hash = hashlib.sha256((governed_clone / workflow_relative).read_bytes()).hexdigest()
    assert governed_hash == expected_hash
    subprocess.run(
        [sys.executable, "lc-coding/tests/test_release_integrity.py"],
        cwd=governed_clone,
        check=True,
        capture_output=True,
        text=True,
    )

print("PASS: LF checkout policy preserves protected bytes with core.autocrlf=true")
