from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[2]
ignore_file = root / ".gitignore"
required_ignores = {"__pycache__/", "*.pyc", ".venv/", ".DS_Store", "*.log"}

assert ignore_file.is_file()
ignore_rules = {
    line.strip()
    for line in ignore_file.read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.lstrip().startswith("#")
}
assert required_ignores <= ignore_rules

hash_manifest = json.loads((root / "FILE_HASHES.json").read_text(encoding="utf-8"))
actual_files = {
    path.relative_to(root).as_posix()
    for path in root.rglob("*")
    if path.is_file()
    and ".git" not in path.relative_to(root).parts
    and ".codex" not in path.relative_to(root).parts
    and "__pycache__" not in path.relative_to(root).parts
    and path.suffix != ".pyc"
    and path.name != "FILE_HASHES.json"
}

assert set(hash_manifest) == actual_files
for relative_path, expected_hash in hash_manifest.items():
    actual_hash = hashlib.sha256((root / relative_path).read_bytes()).hexdigest()
    assert actual_hash == expected_hash, relative_path

print("PASS: release files and hash manifest are complete")
