from pathlib import Path


root = Path(__file__).resolve().parents[2]
migration = root / "MIGRATION-2.3.0-TO-2.4.0.md"
assert migration.is_file()
text = migration.read_text(encoding="utf-8")
for marker in [
    "one total project repository",
    "logical subtrees",
    "multiple UI, Workflow, and peer Simulation",
    "API and MCP",
    "Primary product mainline",
    "exact project commit",
    "component version",
    "content hash",
    "worktree is optional",
    "no new phase, gate, state, runtime, or lower-method responsibility",
]:
    assert marker in text, marker

print("PASS: migration from 2.3.0 to 2.4.0 defines logical subtree governance")
