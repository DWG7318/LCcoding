from pathlib import Path


root = Path(__file__).resolve().parents[2]
migration = (root / "MIGRATION-2.4.0-TO-2.4.1.md").read_text(encoding="utf-8")

for marker in [
    "canonical mainline",
    "four phases",
    "21 steps",
    "PRODUCT_BASELINE.report",
    "LOOP_RUN_D0_D3.report",
    "UNKNOWN",
    "NOT_RECORDED",
    "10",
    "15",
    "30",
    "two native Pin commands",
    "not part of this migration",
]:
    assert marker in migration, marker

for forbidden in [
    "new lifecycle phase",
    "BI controls",
    "real project integration is complete",
]:
    assert forbidden not in migration

print("PASS: migration from 2.4.0 to 2.4.1 preserves the BI boundary")
