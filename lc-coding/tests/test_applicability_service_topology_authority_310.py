from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[2]
SPEC = (ROOT / "SPEC.md").read_text(encoding="utf-8")

for marker in (
    "WHOLE_PRODUCT_FIT",
    "BOUNDED_PRODUCT_FIT",
    "OTHER_METHOD_RECOMMENDED",
    "PLATFORM_COMPLETION",
    "AGENT_COLLABORATIVE",
    "MIXED",
    "DIRECT_PRODUCT",
    "PERSONAL_AGENT",
    "SERVICE_CENTER",
    "Human Principal",
    "Personal Agent",
    "Product Agent",
    "Operations Agent",
    "Service Center actor",
    "USER_SERVICE_BOUNDARY",
):
    assert marker in SPEC, marker

phases = json.loads(
    (ROOT / "lc-coding/contracts/phases.json").read_text(encoding="utf-8")
)
assert [item["id"] for item in phases["phases"]] == [
    "INITIAL",
    "PRODUCT_FORMATION",
    "REAL_PRODUCT_INTEGRATION",
    "REAL_USER_JOURNEY_ACCEPTANCE",
    "DELIVERY_PREPARATION",
]

print("PASS: LCCoding 3.1 applicability and service-topology authority")
