from pathlib import Path
import copy
import importlib.util
import json

root = Path(__file__).resolve().parents[2]
module_path = root / "lc-coding/scripts/validate_project.py"
spec = importlib.util.spec_from_file_location("validate_project", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert hasattr(module, "validate_owner_gap_lineage")

status = json.loads((root / "lc-coding/templates/STATUS.json").read_text(encoding="utf-8"))
status["open_owner_gaps"] = [
    {
        "gap_id": "GAP-001",
        "state": "OPEN",
        "source_acceptance": "OA-001",
        "evidence_pointers": ["reviews/OA-001.md"],
    }
]
open_record = {
    "Owner Gap ID": "GAP-001",
    "Gap source Acceptance ID": "OA-001",
    "Gap source candidate / scenario": "abc123 / SCN-001",
    "Gap route": "IMPACT_CORRECTION",
    "Impact / definition reference": "PENDING",
    "Correction Run IDs": "PENDING",
    "Affected D0-D3 receipts": "PENDING",
    "Delta re-verification receipt": "PENDING",
    "Delta Owner re-acceptance receipt": "PENDING",
    "Gap status": "OPEN",
}
assert module.validate_owner_gap_lineage(status, [open_record]) == []

premature_closed = copy.deepcopy(open_record)
premature_closed["Gap status"] = "CLOSED"
assert any(
    "CLOSED requires" in error
    for error in module.validate_owner_gap_lineage({**status, "open_owner_gaps": []}, [premature_closed])
)

closed = copy.deepcopy(premature_closed)
closed.update(
    {
        "Impact / definition reference": "IA-003",
        "Correction Run IDs": "RUN-003",
        "Affected D0-D3 receipts": "D0-3, D1-3, D2-3, D3-3",
        "Delta re-verification receipt": "D3-3",
        "Delta Owner re-acceptance receipt": "OA-002",
    }
)
assert module.validate_owner_gap_lineage({**status, "open_owner_gaps": []}, [closed]) == []

still_indexed = copy.deepcopy(status)
assert any(
    "CLOSED gap remains in open_owner_gaps" in error
    for error in module.validate_owner_gap_lineage(still_indexed, [closed])
)

overloaded_index = copy.deepcopy(status)
overloaded_index["open_owner_gaps"][0]["correction_tasks"] = ["runtime detail"]
assert any(
    "open_owner_gaps may only index" in error
    for error in module.validate_owner_gap_lineage(overloaded_index, [open_record])
)

template = (root / "lc-coding/templates/LOOP-OWNER-ACCEPTANCE.md").read_text(
    encoding="utf-8"
)
assert "Owner Gap ID" in template
assert "Delta Owner re-acceptance receipt" in template

print("PASS: Owner gaps retain closure lineage while canonical status stays an index")
