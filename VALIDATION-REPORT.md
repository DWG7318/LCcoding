# LCCoding 2.5.0 Validation Report

## Result

Local implementation candidate: **PASS**. Formal GitHub publication: **BLOCKED by external Loop release dependencies**.

LCCoding 2.5.0 provides one current-user NSIS-installed `lccoding-bi.exe`, a React + Vite packaged frontend, and one Rust read-only project projector. It preserves the canonical mainline, four phases, 21 BI steps, eight protected reports, 300×480 client area, English-first/Chinese interaction, Pin, Refresh, Open/Back, visual tokens, and `status.json` authority.

## Fresh verification

- `python lc-coding/tests/run_tests.py`: PASS, 29 tests.
- `python lc-coding/scripts/validate_repository.py .`: PASS.
- `python lc-coding/tests/test_release_integrity.py`: PASS; release tree and SHA-256 manifest agree.
- React `typecheck`: PASS.
- Vitest DOM/accessibility/refresh tests: PASS, 71/71.
- Vite production build: PASS; production graph contains React only and no fixture selector or retired Vanilla runtime.
- Playwright installed-Chrome visual suite: PASS, 33/33 at the fixed 300×480 viewport, including bilingual, reduced-motion, error, boundary-name, Product Baseline, and Loop Governance coverage.
- Rust normal tests: PASS, 31/31 across binding, single-flight commands, `gix` exact-commit reads, bounded input, Loop adapters, and project projection.
- Rust optimized tests: PASS, the same 31/31.
- NSIS current-user packaging contract and candidate build: PASS with `embedBootstrapper`, installer SHA-256, overall-version/commit provenance, and no independent BI version.
- Installed-tool smoke: PASS. The installed `lccoding-bi.exe --project` ran with no source or Node/npm/Rust/Python/Git CLI path, opened a 300×480 logical client, survived refresh, and left project bytes and mtimes unchanged.
- Uninstall smoke: PASS. Installation directory, exact user PATH entry, uninstall registration, and Start Menu shortcut were removed.
- `git diff --check`, JSON/Markdown/version consistency, secret/path scans, and scope inspection: PASS.

## Safety and authority

- CLI and native Folder Picker share the same Rust-owned canonical root validation and immutable one-project binding.
- `get_snapshot` accepts no path argument and joins one Rust-side in-flight projection; the React scheduler also joins one request and waits two seconds after settlement.
- The reader is bounded, no-follow/reparse-aware, strict-schema, network-disabled, and read-only. It uses `gix` rather than Git CLI for packaged project reads.
- Only allowlisted Snapshot fields cross IPC. Project paths, repositories, commits, hashes, evidence bodies, raw errors, URLs, secrets, and task identifiers do not reach the webview.
- Missing or unsupported evidence projects `UNKNOWN`, `NOT_RECORDED`, or a fixed path-free error. The BI never writes project state or controls Agent/runtime behavior.
- The Tauri ACL remains exactly `bind_project`, `choose_project`, `get_snapshot`, `is_pinned`, and `set_pinned`; no filesystem, shell, opener, HTTP, updater, or arbitrary path capability is enabled.

## Formal release dependency blocker

The adapters are implemented and tested against the recorded SLK 2.5.0, CLK 2.5.0, and GLK 3.1.0 candidate contract identities. A fresh GitHub read found each canonical repository `main`, but none of the required version tags or GitHub Releases exists. Therefore:

- no candidate identity is represented as a formal release;
- the package driver blocks formal mode and marks explicit non-release builds `BLOCKED_CANDIDATE_IDENTITIES`;
- LCCoding 2.5.0 must not be pushed, tagged, or released until all three method versions are published and their main/tag/Release/schema/template/hash identities mechanically match.
