from pathlib import Path
import json
import re


root = Path(__file__).resolve().parents[2]
bi = root / "lc-coding/bi"


def reachable_import_text(entry: Path) -> str:
    pending = [entry]
    visited: set[Path] = set()
    chunks: list[str] = []
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        text = current.read_text(encoding="utf-8")
        chunks.append(text)
        for specifier in re.findall(r'(?:from\s+|import\s*)["\']([^"\']+)["\']', text):
            if not specifier.startswith("."):
                continue
            base = (current.parent / specifier).resolve()
            candidates = [
                base,
                base.with_suffix(".ts"),
                base.with_suffix(".tsx"),
                base / "index.ts",
                base / "index.tsx",
            ]
            target = next((candidate for candidate in candidates if candidate.is_file()), None)
            if target is not None:
                pending.append(target)
    return "\n".join(chunks)


package = json.loads((bi / "package.json").read_text(encoding="utf-8"))
assert package["dependencies"]["react"]
assert package["dependencies"]["react-dom"]
assert package["devDependencies"]["@types/react"]
assert package["devDependencies"]["@types/react-dom"]

entry = bi / "src/react-entry.tsx"
assert entry.is_file()
assert 'src="/src/react-entry.tsx"' in (bi / "index.html").read_text(encoding="utf-8")
assert "LCCODING_BI_DIST" in (bi / "vite.config.ts").read_text(encoding="utf-8")

production_graph = reachable_import_text(entry)
assert "tests/fixtures" not in production_graph
assert "./preview" not in production_graph
assert "snapshot-ok.json" not in production_graph
assert "snapshot-error.json" not in production_graph

print("PASS: React is the only packaged BI frontend contract")
