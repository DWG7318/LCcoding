from pathlib import Path
import json
import re


root = Path(__file__).resolve().parents[2]
migration_path = root / "MIGRATION-2.6.0-TO-2.7.0.md"
assert migration_path.is_file(), "2.6.0 to 2.7.0 migration contract is absent"
migration = migration_path.read_text(encoding="utf-8")


def section(markdown, heading):
    marker = f"## {heading}\n"
    start = markdown.find(marker)
    assert start >= 0, f"missing migration section: {heading}"
    start += len(marker)
    end = markdown.find("\n## ", start)
    return markdown[start:] if end < 0 else markdown[start:end]


def closed_fields(markdown, heading):
    fields = {}
    for line in section(markdown, heading).splitlines():
        if not line.startswith("- "):
            continue
        key, separator, value = line[2:].partition(": ")
        assert separator and key and value, f"malformed {heading} field: {line}"
        assert key not in fields, f"duplicate {heading} field: {key}"
        fields[key] = value
    return fields


contract = closed_fields(migration, "Closed migration contract")
assert contract == {
    "Source version": "2.6.0",
    "Target candidate version": "2.7.0",
    "Migration status": "CANDIDATE_ONLY_NOT_A_RELEASE",
    "Current repository release": "2.6.0",
    "Source preservation": "ORIGINAL_2_6_INPUTS_UNCHANGED",
    "Candidate construction": "COPY_ON_WRITE_EXTERNAL_TARGET",
    "Generated output as migration input": "FORBIDDEN",
    "2.6 status adapter": "SUPPORTED_LEGACY",
    "2.7 status adapter": "CURRENT",
    "Adapter inference or mixed schema": "FORBIDDEN",
    "Existing receipt treatment": "PRESERVE_AS_HISTORICAL_EVIDENCE",
    "Current acceptance treatment": "REPROVE_NEW_CONDITIONS",
    "Rollback treatment": "DISCARD_OR_ISOLATE_UNACCEPTED_CANDIDATE",
    "Rollback authority": "ORIGINAL_2_6_STATUS_AND_EVIDENCE_POINTERS",
    "2.7 state backflow into 2.6": "FORBIDDEN",
    "BI compatibility": "EXISTING_SINGLE_ASSET_DUAL_READ_ONLY",
    "BI modification in this migration": "NONE",
    "Global Skill deployment": "POST_RELEASE_ONLY_WITH_EXACT_DIGEST",
    "Global Skill state": "NOT_DEPLOYED_BY_MIGRATION",
}

copy_on_write = section(migration, "Copy-on-write execution")
assert "$sourceProject" in copy_on_write
assert "$candidateProject" in copy_on_write
assert "--project $sourceProject --output $candidateProject" in copy_on_write
assert "source and candidate must be distinct non-overlapping trees" in copy_on_write
assert "generated output is never an input" in copy_on_write
assert "outside the repository worktree" in copy_on_write

mapping_match = re.search(
    r"## Exact phase boundary map\n\n```json\n(?P<payload>.*?)\n```",
    migration,
    re.DOTALL,
)
assert mapping_match, "missing exact phase boundary map"
phase_map = json.loads(mapping_match.group("payload"))
assert phase_map == {
    "source": {
        "version": "2.6.0",
        "phase_step_counts": [3, 5, 7, 6],
        "MANDATORY_CALABASH_UPGRADE": "ENGINEERING_RUNS",
        "PRODUCT_BASELINE": "ENGINEERING_RUNS",
    },
    "target": {
        "version": "2.7.0",
        "phase_step_counts": [3, 7, 5, 6],
        "MANDATORY_CALABASH_UPGRADE": "PRODUCT_FORMATION",
        "PRODUCT_BASELINE": "PRODUCT_FORMATION",
    },
    "same_exact_21_step_set": True,
    "new_lifecycle_gates": [],
    "new_steps": [],
    "synthetic_progress": "FORBIDDEN",
}

for overclaim in (
    "Current repository release: 2.7.0",
    "BI modification in this migration: REQUIRED",
    "Global Skill state: DEPLOYED_BY_MIGRATION",
):
    assert overclaim not in migration, f"migration overclaim: {overclaim}"

changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
release_heading = "## 2.7.0"
next_heading = "## 2.6.0"
assert changelog.startswith("# Changelog\n\n")
assert changelog.count("\n" + release_heading + "\n") == 1
assert changelog.count("\n" + next_heading + "\n") == 1
release_start = changelog.index("\n" + release_heading + "\n") + 1
release_end = changelog.index("\n" + next_heading + "\n")
assert release_start < release_end
release_section = changelog[release_start:release_end]
for marker in (
    "copy-on-write",
    "current repository and BI release carriers are finalized for 2.7.0",
    "global installed Skill deployment remains a separate post-release action",
    "only after the formal release is independently accepted",
):
    assert marker in release_section
for stale_claim in (
    "Unreleased - 2.7.0 candidate",
    "not a release",
    "no formal tag or GitHub Release exists yet",
    "prepared for 2.7.0",
    "does not change VERSION, BI",
):
    assert stale_claim not in release_section

print("PASS: 2.6.0 to 2.7.0 migration and final release-entry contracts are closed")
