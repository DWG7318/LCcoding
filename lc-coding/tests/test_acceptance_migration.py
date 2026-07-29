from pathlib import Path

root = Path(__file__).resolve().parents[2]
migration = (root / "MIGRATION-1.1.1-TO-2.0.0.md").read_text(encoding="utf-8")

stale_rule = (
    "Treat legacy Loop Human Acceptance as Acceptance Handoff; "
    "keep one LCCoding Owner Acceptance."
)
assert stale_rule not in migration
assert "Every normal SLK/CLK/GLK Run retains its Owner Acceptance." in migration
assert "Post-Security Owner Acceptance" in migration

print("PASS: migration preserves both Owner Acceptance boundaries")
