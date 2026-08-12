import re
from pathlib import Path

root = Path(__file__).resolve().parents[2]
spec = (root / "SPEC.md").read_text(encoding="utf-8")
clause_start = re.search(
    r'(?m)^<a id="lc-integ-003"></a>\s*\n### LC-INTEG-003[^\n]*\n', spec
)
assert clause_start, "SPEC is missing LC-INTEG-003"
clause_tail = spec[clause_start.end() :]
clause_end = re.search(r'(?m)^<a id="lc-|^## ', clause_tail)
impact = clause_tail[: clause_end.start()] if clause_end else clause_tail

assert "may be blank" in impact
for marker in ["future decision", "constraint", "check", "template", "reuse"]:
    assert marker in impact
assert "one existing canonical artifact" in impact

for path in root.rglob("*"):
    if path.is_dir():
        assert path.name.lower() not in {"learning", "lessons", "retrospective"}

print("PASS: consequential learning returns to one existing artifact without a new system")
