from pathlib import Path
import json
import re
import tempfile


root = Path(__file__).resolve().parents[2]
driver_text = (root / "lc-coding/bi/scripts/package-release.ps1").read_text(
    encoding="utf-8"
)
workflow_text = (root / ".github/workflows/release-bi.yml").read_text(
    encoding="utf-8"
)

safe_basename = "LCCoding-BI_2.6.0_x64-setup.exe"
safe_pattern = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def github_download_basename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", ".", name)


def validate_surface(directory: Path) -> None:
    files = sorted(path.name for path in directory.iterdir() if path.is_file())
    assert files == sorted([safe_basename, "installer.sha256", "provenance.json"])
    provenance = json.loads((directory / "provenance.json").read_text(encoding="utf-8"))
    checksum_name = (
        (directory / "installer.sha256")
        .read_text(encoding="utf-8")
        .strip()
        .split("  ", 1)[1]
    )
    downloaded_name = next(path.name for path in directory.glob("*.exe"))
    assert safe_pattern.fullmatch(downloaded_name)
    assert downloaded_name == provenance["asset"] == checksum_name == safe_basename


historical_source = "LCCoding BI_2.5.0_x64-setup.exe"
historical_download = github_download_basename(historical_source)
assert historical_download == "LCCoding.BI_2.5.0_x64-setup.exe"
assert historical_download != historical_source

for unsafe in [
    historical_source,
    "LCCoding/BI_2.6.0_x64-setup.exe",
    "LCCoding\\BI_2.6.0_x64-setup.exe",
    "https://example.invalid/installer.exe",
    "LCCoding+BI_2.6.0_x64-setup.exe",
]:
    assert not safe_pattern.fullmatch(unsafe), unsafe
assert safe_pattern.fullmatch(safe_basename)
assert github_download_basename(safe_basename) == safe_basename

with tempfile.TemporaryDirectory(prefix="lccoding-release-name-") as temporary:
    surface = Path(temporary)
    (surface / historical_download).write_bytes(b"MZ")
    (surface / "installer.sha256").write_text(
        f"{'0' * 64}  {historical_source}\n", encoding="utf-8"
    )
    (surface / "provenance.json").write_text(
        json.dumps({"asset": historical_source}), encoding="utf-8"
    )
    try:
        validate_surface(surface)
    except AssertionError:
        pass
    else:
        raise AssertionError("the observed 2.5.0 normalized download must be rejected")

driver_name = re.search(r'^\$releaseInstallerName = "([^"]+)"$', driver_text, re.MULTILINE)
assert driver_name, "package driver must define the closed release installer basename"
assert driver_name.group(1) == safe_basename
assert "BI_RELEASE_ASSET_NAME_UNSAFE" in driver_text

workflow_name = re.search(r'^\s*\$installerName = "([^"]+)"$', workflow_text, re.MULTILINE)
assert workflow_name, "workflow must define the closed release installer basename"
assert workflow_name.group(1) == safe_basename
assert (
    "${{ runner.temp }}\\lccoding-bi-formal\\release\\" + safe_basename
    in workflow_text
)

print("PASS: BI release basename remains exact across GitHub download surfaces")
