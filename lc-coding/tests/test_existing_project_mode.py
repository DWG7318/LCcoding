from pathlib import Path
import json
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[2]
bootstrap = root / "lc-coding/scripts/bootstrap_lccoding.py"


def git(project, *args):
    return subprocess.run(
        ["git", "-C", str(project), *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


with tempfile.TemporaryDirectory() as td:
    empty_repo = Path(td)
    git(empty_repo, "init")
    cp = subprocess.run(
        [
            sys.executable,
            str(bootstrap),
            "--project",
            str(empty_repo),
            "--name",
            "Uncommitted Product",
            "--repository",
            "owner/uncommitted",
            "--visibility",
            "private",
            "--mode",
            "existing",
        ],
        capture_output=True,
        text=True,
    )
    assert cp.returncode != 0
    assert not (empty_repo / ".lccoding").exists()


with tempfile.TemporaryDirectory() as td:
    project = Path(td)
    git(project, "init")
    git(project, "config", "user.name", "LCCoding Test")
    git(project, "config", "user.email", "lccoding@example.invalid")
    (project / "VERSION").write_text("7.4.2\n", encoding="utf-8")
    (project / "product.txt").write_text("preserve me\n", encoding="utf-8")
    git(project, "add", "VERSION", "product.txt")
    git(project, "commit", "-m", "existing product")

    head_before = git(project, "rev-parse", "HEAD")
    history_before = git(project, "rev-list", "--count", "HEAD")
    product_before = (project / "product.txt").read_bytes()

    cp = subprocess.run(
        [
            sys.executable,
            str(bootstrap),
            "--project",
            str(project),
            "--name",
            "Existing Product",
            "--repository",
            "owner/existing",
            "--visibility",
            "private",
            "--mode",
            "existing",
            "--continuity",
            "narrow_redirect",
            "--claimed-state",
            "complete",
        ],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 0, cp.stdout + cp.stderr

    assert git(project, "rev-parse", "HEAD") == head_before
    assert git(project, "rev-list", "--count", "HEAD") == history_before
    assert git(project, "diff", "--exit-code") == ""
    assert (project / "VERSION").read_text(encoding="utf-8").strip() == "7.4.2"
    assert (project / "product.txt").read_bytes() == product_before

    lc = project / ".lccoding"
    start = json.loads((lc / "PROJECT-START.json").read_text(encoding="utf-8"))
    assert start["initialization_mode"] == "EXISTING"
    assert start["source_version"] == "7.4.2"
    assert start["source_head"] == head_before
    assert start["continuity_decision"] == "NARROW_REDIRECT"
    assert start["reported_project_state"] == "COMPLETE"
    assert start["completion_claim_status"] == "CLAIMED_UNATTESTED"
    assert start["attestation_status"] == "PENDING"

    status = json.loads((lc / "status.json").read_text(encoding="utf-8"))
    health = json.loads((lc / "PROJECT-HEALTH.json").read_text(encoding="utf-8"))
    assert status["existing_project_attestation"] == "PENDING"
    assert status["initialization"] == "EXISTING_INTAKE_PENDING"
    assert health["existing_project_classification"] == "PENDING"

print("PASS: existing project intake preserves history, version, and evidence boundary")
