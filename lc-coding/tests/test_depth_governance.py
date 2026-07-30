from pathlib import Path
import importlib.util
import json

root = Path(__file__).resolve().parents[2]
module_path = root / "lc-coding/scripts/validate_project.py"
spec = importlib.util.spec_from_file_location("validate_project", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

low = {
    "complexity": {
        "product_uncertainty": "LOW",
        "system_coupling": "LOW",
        "real_risk": "LOW",
        "irreversibility": "LOW",
        "novelty": "LOW",
    },
    "depth": {"rationale": "", "analysis": [], "materials": [], "evidence": []},
    "recommended_loop": "SLK",
}
assert module.validate_complexity_depth(low) == []

loop_independent = json.loads(json.dumps(low))
loop_independent["recommended_loop"] = "GLK"
assert module.validate_complexity_depth(loop_independent) == []

medium = json.loads(json.dumps(low))
medium["complexity"]["system_coupling"] = "MEDIUM"
assert any("rationale" in error for error in module.validate_complexity_depth(medium))

high = json.loads(json.dumps(low))
high["complexity"]["real_risk"] = "HIGH"
high["depth"]["rationale"] = "Security boundary requires deeper evidence."
assert any("deeper coverage" in error for error in module.validate_complexity_depth(high))
high["depth"]["evidence"] = ["security-boundary verification"]
assert module.validate_complexity_depth(high) == []

fingerprint = json.loads(
    (root / "lc-coding/templates/PROJECT-FINGERPRINT.json").read_text(encoding="utf-8")
)
assert isinstance(fingerprint["complexity"], dict)
assert "recommended_loop" in fingerprint
assert "recommended_loop" not in fingerprint["complexity"]

unknown_errors = module.validate_complexity_depth(fingerprint)
assert any(
    "complexity unresolved" in error and "requires depth assessment" in error
    for error in unknown_errors
)
assert not any("invalid complexity factor" in error for error in unknown_errors)
assert any("rationale" in error for error in unknown_errors)
assert any("deeper coverage" in error for error in unknown_errors)

fingerprint["depth"]["rationale"] = "Unresolved factors require conservative depth."
fingerprint["depth"]["evidence"] = ["initial risk investigation"]
resolved_depth_errors = module.validate_complexity_depth(fingerprint)
assert any("complexity unresolved" in error for error in resolved_depth_errors)
assert not any("rationale" in error for error in resolved_depth_errors)
assert not any("deeper coverage" in error for error in resolved_depth_errors)

print("PASS: complexity factors deepen evidence without changing Loop topology")
