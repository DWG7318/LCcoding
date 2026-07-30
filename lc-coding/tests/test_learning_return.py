from pathlib import Path

root = Path(__file__).resolve().parents[2]
acceptance = (root / "lc-coding/templates/LOOP-OWNER-ACCEPTANCE.md").read_text(
    encoding="utf-8"
)
impact = (root / "lc-coding/references/impact-and-synchronization.md").read_text(
    encoding="utf-8"
)
combined = acceptance + "\n" + impact

assert "may be blank" in combined
for marker in ["future decision", "constraint", "check", "template", "reuse"]:
    assert marker in combined
assert "one existing canonical artifact" in combined

for path in root.rglob("*"):
    if path.is_dir():
        assert path.name.lower() not in {"learning", "lessons", "retrospective"}

print("PASS: consequential learning returns to one existing artifact without a new system")
