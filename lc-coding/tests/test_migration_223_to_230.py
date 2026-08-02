from pathlib import Path


root = Path(__file__).resolve().parents[2]
migration = root / "MIGRATION-2.2.3-TO-2.3.0.md"

assert migration.is_file()
text = migration.read_text(encoding="utf-8")
lower = text.lower()

for marker in [
    "2.2.3",
    "2.3.0",
    "read-only",
    "windows",
    "english",
    "chinese",
    "pin",
    "project files",
    "agent",
    "runtime",
    "real project data",
]:
    assert marker in lower, marker

for phase in [
    "INITIAL",
    "PRODUCT_FORMATION",
    "ENGINEERING_RUNS",
    "DELIVERY_PREPARATION",
]:
    assert phase in text, phase

assert "does not read or mutate project files" in lower
assert "does not control agent or runtime" in lower
assert "does not claim that real project data integration is complete" in lower

print("PASS: migration from 2.2.3 to 2.3.0 defines the built-in BI boundary")
