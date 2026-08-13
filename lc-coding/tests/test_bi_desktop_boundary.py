import json
import re
import tomllib
from pathlib import Path


root = Path(__file__).resolve().parents[2]
bi_root = root / "lc-coding" / "bi"
implementation_readme = bi_root / "README.md"
tauri_root = bi_root / "src-tauri"
config_path = tauri_root / "tauri.conf.json"
capability_dir = tauri_root / "capabilities"

assert implementation_readme.is_file(), "missing sole BI implementation entry"
implementation = implementation_readme.read_text(encoding="utf-8")
for marker in [
    "Implementation class: BI_SUBTREE_GUIDANCE",
    "Authority: NON_NORMATIVE_IMPLEMENTATION_NAVIGATION",
    "Product contract: ../references/built-in-bi.md",
    "`src/`",
    "`src-tauri/`",
    "`tests/dom/`",
    "`tests/visual/`",
    "`tests/packaging/`",
    "`scripts/package-release.ps1`",
    "`scripts/verify-loop-releases.ps1`",
    "`.github/workflows/release-bi.yml",
    "npm ci --ignore-scripts",
    "npm run typecheck",
    "npm run test:dom",
    "npm run visual:candidates",
    "cargo test",
    "LCCODING_BI_DIST",
    "BI_OWNER_REVIEW_DIR",
    "$runnerBi = '<external-runner>\\lc-coding\\bi'",
    "Set-Location $runnerBi",
    "$runnerTauri = Join-Path $runnerBi 'src-tauri'",
    "$env:CARGO_TARGET_DIR = '<external-cargo-target>'",
    "$env:TAURI_CONFIG",
    "[IO.Path]::GetRelativePath($runnerTauri, $externalDist)",
    "Set-Location $runnerTauri",
    "allowed tracked/Cell inputs",
    "node_modules`, `dist`, `target`, `test-results`, and `playwright-report`",
]:
    assert marker in implementation, marker
assert "Source clauses:" not in implementation

local_verification = implementation.split("## Local verification", 1)[1].split(
    "## Package and release navigation", 1
)[0]
assert local_verification.index("$runnerBi =") < local_verification.index(
    "Set-Location $runnerBi"
) < local_verification.index("npm ci --ignore-scripts")
assert local_verification.index("$env:CARGO_TARGET_DIR") < local_verification.index(
    "Set-Location $runnerTauri"
) < local_verification.index("cargo test")
assert "source worktree" in local_verification
assert "must not be created" in local_verification
assert "must not enter the release manifest" in local_verification

product_contract = (root / "lc-coding/references/built-in-bi.md").read_text(
    encoding="utf-8"
)
assert "Source clauses: [LC-BI-001]" in product_contract
assert "[LC-BI-002]" in product_contract
for operational_marker in [
    "## 3. File boundaries",
    "## 10. Required implementation sequence",
    "### LCCoding 2.6.0 one-click sequence",
    "npm ci --ignore-scripts",
    "cargo test",
    "package-release.ps1",
    "verify-loop-releases.ps1",
]:
    assert operational_marker not in product_contract, operational_marker

assert config_path.is_file(), "missing Tauri desktop configuration"
config = json.loads(config_path.read_text(encoding="utf-8"))
assert config["productName"] == "LCCoding BI"
assert config["version"] == "2.7.0"
assert config["identifier"] == "com.lccoding.desktop"
assert config["build"] == {"frontendDist": "../dist"}
assert config["plugins"] == {}

app = config["app"]
assert app["withGlobalTauri"] is False
assert len(app["windows"]) == 1
window = app["windows"][0]
assert window == {
    "label": "main",
    "title": "LCCoding BI",
    "url": "index.html",
    "create": False,
    "width": 300,
    "height": 480,
    "resizable": False,
    "maximizable": False,
    "minimizable": True,
    "closable": True,
    "decorations": True,
    "dragDropEnabled": False,
    "devtools": False,
}

security = app["security"]
assert security["capabilities"] == ["main"]
assert security["freezePrototype"] is True
assert security["dangerousDisableAssetCspModification"] is False
assert security["assetProtocol"] == {"enable": False, "scope": []}
expected_csp = {
    "default-src": {"'self'"},
    "script-src": {"'self'"},
    "style-src": {"'self'"},
    "img-src": {"'self'"},
    "font-src": {"'self'"},
    "connect-src": {"ipc:", "http://ipc.localhost"},
    "object-src": {"'none'"},
    "base-uri": {"'none'"},
    "frame-src": {"'none'"},
    "form-action": {"'none'"},
}
actual_csp = {}
for raw_directive in security["csp"].split(";"):
    parts = raw_directive.strip().split()
    if parts:
        actual_csp[parts[0]] = set(parts[1:])
assert actual_csp == expected_csp

bundle = config["bundle"]
assert bundle["active"] is True
assert bundle["targets"] == ["nsis"]
assert bundle["createUpdaterArtifacts"] is False
assert bundle["icon"] == ["icons/icon.ico"]
assert bundle["windows"] == {
    "webviewInstallMode": {"type": "embedBootstrapper"},
    "nsis": {
        "installMode": "currentUser",
        "installerHooks": "windows/hooks.nsh",
        "languages": ["English", "SimpChinese"],
    },
}
assert (tauri_root / "icons" / "icon.ico").is_file()
assert (tauri_root / "icons" / "icon.svg").is_file()

capability_files = sorted(path.name for path in capability_dir.glob("*.json"))
assert capability_files == ["main.json"]
capability = json.loads((capability_dir / "main.json").read_text(encoding="utf-8"))
assert capability["identifier"] == "main"
assert capability["windows"] == ["main"]
assert "remote" not in capability
commands = ["bind_project", "choose_project", "get_snapshot", "is_pinned", "set_pinned"]
assert capability["permissions"] == [
    f"allow-{command.replace('_', '-')}" for command in commands
]

permission_dir = tauri_root / "permissions" / "autogenerated"
permission_files = sorted(path.name for path in permission_dir.glob("*.toml"))
assert permission_files == [f"{command}.toml" for command in commands]
for command in commands:
    permissions = tomllib.loads(
        (permission_dir / f"{command}.toml").read_text(encoding="utf-8")
    )["permission"]
    assert permissions == [
        {
            "identifier": f"allow-{command.replace('_', '-')}",
            "description": (
                f"Enables the {command} command without any pre-configured scope."
            ),
            "commands": {"allow": [command]},
        },
        {
            "identifier": f"deny-{command.replace('_', '-')}",
            "description": (
                f"Denies the {command} command without any pre-configured scope."
            ),
            "commands": {"deny": [command]},
        },
    ]

build_rs = (tauri_root / "build.rs").read_text(encoding="utf-8")
library_rs = (tauri_root / "src" / "lib.rs").read_text(encoding="utf-8")
main_rs = (tauri_root / "src" / "main.rs").read_text(encoding="utf-8")
assert re.search(
    r'AppManifest::new\(\)\.commands\(&\[\s*"bind_project",\s*"choose_project",\s*"get_snapshot",\s*"is_pinned",\s*"set_pinned",?\s*\]\)',
    build_rs,
)
handler = re.search(r"generate_handler!\[(?P<commands>[^]]+)\]", library_rs)
assert handler is not None
handler_commands = []
for value in handler.group("commands").split(","):
    value = value.strip()
    if value:
        handler_commands.append(value.removeprefix("commands::").removeprefix("pin::"))
assert handler_commands == commands
assert "tauri::webview_version()" in library_rs
assert "BI_WEBVIEW_UNAVAILABLE" in library_rs
assert "WebviewWindowBuilder::from_config" in library_rs
assert ".on_navigation(" in library_rs
assert ".on_download(" in library_rs
assert ".on_new_window(" in library_rs
assert "NewWindowResponse::Deny" in library_rs
assert "lccoding::run();" in main_rs
assert 'windows_subsystem = "windows"' in main_rs

cargo = tomllib.loads((tauri_root / "Cargo.toml").read_text(encoding="utf-8"))
assert cargo["bin"] == [{"name": "lccoding-bi", "path": "src/main.rs"}]
assert cargo["package"] == {
    "name": "lccoding",
    "version": "2.7.0",
    "edition": "2024",
    "rust-version": "1.96",
    "publish": False,
}
assert cargo["features"] == {
    "default": ["custom-protocol"],
    "custom-protocol": ["tauri/custom-protocol"],
}
assert cargo["dependencies"] == {
    "futures-util": "=0.3.33",
    "gix": {
        "version": "=0.86.0",
        "default-features": False,
        "features": ["sha1"],
    },
    "serde": {"version": "=1.0.229", "features": ["derive"]},
    "serde_json": "=1.0.151",
    "serde_yaml_ng": "=0.10.0",
    "sha2": "=0.10.9",
    "tauri": {
        "version": "=2.11.5",
        "default-features": False,
        "features": ["common-controls-v6", "compression", "wry"],
    }
}
assert cargo["target"]["cfg(windows)"]["dependencies"] == {
    "windows": {
        "version": "=0.61.3",
        "features": [
            "Win32_Foundation",
            "Win32_Security",
            "Win32_Storage_FileSystem",
            "Win32_System_Com",
            "Win32_UI_Shell",
            "Win32_UI_Shell_Common",
        ],
    }
}
assert cargo["build-dependencies"] == {
    "tauri-build": {"version": "=2.6.3", "features": []}
}

for forbidden_output in ("node_modules", "dist", "target"):
    assert not (bi_root / forbidden_output).exists()
assert not (tauri_root / "target").exists()

print("PASS: built-in BI desktop keeps one five-command binding, projection, and Pin boundary")
