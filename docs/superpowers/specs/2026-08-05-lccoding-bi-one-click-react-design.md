# LCCoding 2.5.0 One-Click Project BI — React + Rust Design

**Status:** Design direction approved; written specification awaiting Owner review

**Target release:** LCCoding 2.5.0

**Authority:** This document defines the 2.5.0 one-click BI replacement. It does not change the LCCoding lifecycle, gates, project authority model, or lower-method responsibilities.

## 1. Problem and decision

LCCoding 2.4.1 ships a visually accepted desktop BI shell and a strict sanitized Snapshot contract, but the released runtime still selects checked-in fixtures. A project cannot install LCCoding once, point the BI at its own root, and see verified live project facts. Requiring project-local source, Node, Rust, Python, compilation, or hand-built UI would also contradict the Owner's one-click requirement.

LCCoding 2.5.0 replaces that static runtime with one centrally maintained application:

- Tauri 2 provides the installed desktop process and native window.
- React + Vite provide one packaged local frontend.
- Rust binds one project root, reads only allowlisted canonical project records, validates them, and produces one immutable sanitized Snapshot in memory.
- The project contributes parameters and its existing LCCoding artifacts only. It contains no BI source, dependency installation, generated UI, or build step.
- `status.json` remains the single authoritative project status. The BI is a read-only derived view and never becomes a second authority.
- The BI has no independent version, repository, tag, release, or updater. Its version is the overall LCCoding version, `2.5.0`.

This is a replacement, not a second BI. React must reach functional and visual parity before the old imperative Vanilla runtime is removed; after the cutover, only the React runtime ships. Existing sanitized fixtures remain test inputs and cannot be imported by the production entry graph.

## 2. Success definition

The design succeeds only when all of the following are true:

1. A user installs one current-user Windows installer without administrator rights and can launch `LCCoding BI` from the Start menu or run `lccoding-bi --project "D:\Project"`.
2. A no-argument launch shows one minimal project-binding surface in the same fixed window. Typed root and native Folder Picker both reach the same Rust validator.
3. One process and one window bind to exactly one project. Multiple independent processes may view different projects; no process becomes a multi-project dashboard.
4. The dashboard shows real, mechanically validated project facts for the fixed four phases, 21 steps, and eight protected reports. Missing facts remain `UNKNOWN` or `NOT_RECORDED`; contradictory or malformed inputs fail closed.
5. Auto refresh and manual Refresh re-read the bound root without overlapping reads, stale-green concealment, project writes, or path leakage.
6. The accepted 300×480 product register, bilingual behavior, Pin, Open/Back, focus, scrolling, state semantics, and protected-report appearance remain equivalent.
7. The installed executable works on a clean Windows machine with a real canonical project root but no LCCoding or BI source checkout, Node, npm, Rust, Cargo, Python, Git executable, or build tools installed.
8. Installer, executable, and runtime leave every project file's bytes and modification time unchanged.

## 3. Considered approaches

### 3.1 Selected: one packaged Tauri + React + Rust application

This is the only approach that simultaneously gives one installation, native project binding, a tightly closed filesystem boundary, no project-local runtime, and reuse across projects. React replaces the UI implementation without changing the product register; Rust owns paths, Git object access, strict parsing, truth checks, and projection.

### 3.2 Rejected: keep the Vanilla fixture runtime

Keeping the current runtime would preserve appearance but would not produce real project data. Adding more fixtures would improve demonstrations while making the truth gap worse. The fixture runtime therefore cannot satisfy 2.5.0.

### 3.3 Rejected: copy or build a viewer inside every project

Project-local source or generated viewers would duplicate code, create version drift, require dependencies or compilation, and turn every project into a BI deployment. That is the opposite of one centrally released tool.

### 3.4 Rejected: background service or browser dashboard

A server, database, remote dashboard, or browser endpoint would add a second runtime and a larger attack surface. It would also complicate project isolation and invite raw path or evidence exposure. The desktop process reads locally and directly; there is no service tier.

## 4. Product boundary and product register

The dashboard retains the accepted product register exactly:

- one native decorated window with a 300×480 logical client area;
- non-resizable and non-maximizable, with internal scrolling and no outer growth;
- Segoe UI/system sans, 14px base, PowerShell/plain-tool visual register;
- English canonical/default UI and a complete Chinese fixed-text switch;
- project-supplied display text is validated and then shown unchanged, never machine-translated;
- four phases in this exact order: `INITIAL`, `PRODUCT_FORMATION`, `ENGINEERING_RUNS`, `DELIVERY_PREPARATION`;
- the existing 21 steps in their existing order;
- done green, error/blocked red, pending dark gray at or above 4.5:1 on white, active blue spinner; every state also has a symbol and readable text;
- reduced-motion mode replaces animation with a static mark without removing state text;
- eight existing Open actions, same-window protected report, and Back;
- Pin reflects actual native always-on-top state; Refresh reflects projection refresh only;
- no cards, dashboard chrome, gradients, glass, decorative grid, second window, router, or new navigation model.

The no-project binding view uses the same native window, typography, spacing discipline, language control, and plain-tool register. It contains only a short fixed explanation, one root input, `Choose folder`, and `Open`. It does not preview the dashboard, expose recent projects, or store project history.

## 5. Process, binding, and command contract

### 5.1 One process, one immutable binding

Rust managed state has three states: `UNBOUND`, `BINDING`, and `BOUND`. These are application states, not LCCoding lifecycle states and never enter project records.

- An unbound process may attempt typed binding or open the native Folder Picker.
- Only one binding attempt runs at a time.
- A failed attempt returns the process to `UNBOUND` with a fixed safe error and allows another attempt.
- A successful attempt stores one canonical root in Rust memory and permanently enters `BOUND` for that process.
- A bound process cannot switch roots. The user closes it and opens another instance to view another project.
- The root is not persisted across launches. This avoids a path-bearing recent-project store. A reopened no-argument process returns to the binding view; a reopened CLI process binds from its new explicit argument.

### 5.2 Launch forms

`lccoding-bi` opens the unbound view. `lccoding-bi --project <root>` parses exactly one operating-system path argument in Rust before frontend startup. Unknown flags, missing values, or multiple roots terminate with exit code `2` and fixed code `BI_ARGUMENT_INVALID`, without printing the argument.

A syntactically valid CLI root goes through the same `validate_and_bind_root` function as typed and picker input. Semantic failure opens the binding view with a safe localized error and recovery action; it never echoes the failed root. A valid CLI root opens the dashboard directly.

The installed command identity is fixed, not inferred from a display name. Cargo declares `[[bin]] name = "lccoding-bi"`, so Windows packages the real file `lccoding-bi.exe`. Tauri/NSIS use `LCCoding BI` as the product and Start Menu shortcut display name. The current-user NSIS installer adds the directory containing that exact executable to the current user's `PATH`; uninstall removes only that exact entry. No command alias or `.cmd` shim is generated.

### 5.3 Closed Tauri command surface

The final resolved ACL, command registration, and frontend invocation catalog contain exactly:

1. `bind_project(project_root: String)` — accepted only while unbound; validates and binds or returns a fixed `BindErrorCode`.
2. `choose_project()` — takes no argument; Rust owns the native folder picker and feeds its result directly to the same validator. The selected path is not returned to the webview.
3. `get_snapshot()` — takes no argument and operates only on the Rust-held bound root.
4. `is_pinned()` — returns confirmed native topmost state.
5. `set_pinned(enabled: bool)` — sets and then reads the confirmed native topmost state.

There is no arbitrary filesystem, shell, opener, HTTP, process, clipboard, download, generic dialog, URL, or path command. `bind_project` is disabled after the first successful bind; `get_snapshot` can never select or replace a root. Command results contain only fixed codes, a safe project display name when binding succeeds, confirmed Pin state, or a sanitized Snapshot.

## 6. Architecture and component boundaries

```text
CLI argument ───────────────┐
                            ├─> Rust root binder ─> immutable BoundProject
Native Folder Picker ───────┤
Typed binding field ────────┘
                                      │
                                      v
canonical project records ─> bounded readers ─> strict typed records
                                      │
                                      v
                             truth/consistency engine
                                      │
                                      v
                           allowlisted sanitized Snapshot
                                      │ get_snapshot() with no args
                                      v
                         React reducer/hooks ─> existing BI view
```

### 6.1 Rust ownership

Rust modules are separated by responsibility rather than assembled into one file:

- `binding`: launch argument parsing, picker result, root canonicalization, Git repository admission, and immutable managed binding;
- `input`: anchored bounded reads and stable file identity;
- `schema`: closed JSON, Markdown-table, and method-specific YAML record types;
- `git`: `gix` repository/commit/tree/blob access without spawning a Git executable or enabling network operations;
- `projection`: lifecycle truth rules, report metrics, and Snapshot assembly;
- `loop_adapters`: one narrow adapter each for the supported canonical SLK, CLK, and GLK aggregate/index formats, all producing one internal governance summary;
- `security`: safe display-name validation, resource budgets, path-free fixed errors, and output allowlist checks;
- `commands`: the five-command boundary only.

No Rust module writes project data. No method adapter executes, wakes, waits, archives, pins, accepts, modifies, or judges lower-method work. It only validates already-issued records and reports their sanitized state.

### 6.2 React ownership

The packaged frontend uses React and React DOM with Vite. It uses local hooks and a small reducer; it adds no router, global state library, component framework, data-fetching framework, or CSS system.

React responsibilities are limited to:

- binding view and safe fixed errors;
- dashboard shell and the fixed phase/step list;
- same-window protected reports;
- language, fold, scroll, Open/Back focus, Pin, Refresh, and error/recovery interaction state;
- rendering immutable Snapshot values through text nodes only.

React never receives a root, record path, raw record, Git identity, hash, evidence body, URL, thread ID, parser message, or native exception. Project values are rendered as text, never HTML.

### 6.3 Snapshot boundary

Snapshot remains non-authoritative and read-only. Its closed surface contains only:

- schema version, health, safe project display name, and current phase;
- the fixed four phase tuples and fixed 21 step tuples;
- the fixed eight reports with fixed row tuples;
- safe versions and closed state/metric values.

It contains no extension object, free-form row, raw value, record reference, or hidden diagnostic field. Report state must mechanically equal its associated main-step state. Unknown fields fail deserialization on both Rust and TypeScript sides.

## 7. Root and input safety

### 7.1 Root admission

`validate_and_bind_root` performs these checks in one shared order:

1. reject empty, over-limit, device, UNC policy-disallowed, control/bidirectional-control, and malformed input;
2. open and canonicalize the root, prove it is a directory, and retain a stable directory identity;
3. reject a root or `.lccoding` component that is a symlink, junction, mount redirection, or other unsupported reparse point;
4. prove `.lccoding/status.json` exists as a regular file and has `record_role=AUTHORITATIVE_PROJECT_STATUS`;
5. open the total project as a Git repository using `gix`, never a shell command or network operation;
6. bind the verified root and repository handles in Rust memory without serializing their locations.

An ordinary `.git` directory is supported. A standard linked-worktree `.git` indirection is supported only through a dedicated parser that accepts the exact Git `gitdir`/`commondir` forms, proves every administrative component is regular and reparse-free, and limits access to Git object/ref operations. Any other indirection fails closed. Project records themselves must always remain beneath the bound root.

### 7.2 Record reads

Every refresh uses a fixed artifact catalog. It never walks the project, follows a record-supplied arbitrary path, or opens an unrecognized file.

- Open one handle, read at most the per-record limit plus one byte, and compare identity before and after the read.
- Require regular files, stable length/identity, UTF-8, and a root-anchored allowlisted location.
- Reject symlink, junction, reparse, FIFO/device, replacement race, oversize, malformed/trailing data, duplicate keys, unknown fields, aliases/tags, and resource-budget excess.
- JSON uses a duplicate-aware strict parser before typed deserialization.
- LCCoding Markdown uses exact heading/table/column grammars with bounded lines, cells, and cell lengths; arbitrary Markdown, HTML, and links are not interpreted.
- Loop YAML uses method-specific closed record types. Duplicate mapping keys, anchors, aliases, tags, unknown fields, and unbounded collections are rejected; it is not a general YAML browser.
- A single unstable read may be retried once inside the same refresh. A second identity change produces `BI_READ_RACE`; it never leaves the last green Snapshot displayed as current truth.

The implementation retains the 2.4.1 limits as a floor: 512 KiB per record, nesting depth 32, 16,384 total JSON/YAML values, 128 object members, 2,048 array items, 4,096 UTF-8 bytes per string, and 128 ASCII characters per numeric token. Each aggregate refresh also has bounded file count, total bytes, Git blobs, table rows, and wall time; exceeding any budget fails closed with `BI_RESOURCE_LIMIT`.

## 8. Version compatibility

The 2.5.0 reader uses exact adapters, not permissive semver guessing.

- Core project adapters accept LCCoding/status schema `2.4.0`, `2.4.1`, and `2.5.0` only. Earlier schemas predate the complete product-subtree contract; later unknown schemas may have changed fields. Either side returns `BI_PROJECT_VERSION_UNSUPPORTED`.
- If `CANONICAL-MANIFEST.json` exists, its LCCoding version must select the same adapter family as `status_schema_version`; its complete closed structure, method versions, hashes, compatibility value, and load order are validated. A mismatch is `BI_RECORD_INCONSISTENT`.
- Product Map/Handoff adapters accept the 2.4.0, 2.4.1, and 2.5.0 canonical table contracts. Absence before the corresponding lifecycle work is `NOT_RECORDED`; presence with a malformed or mixed contract is an error.
- Loop Governance supports exactly SLK 2.5.0 `RUN_RUNTIME_INDEX`, CLK 2.5.0 `CLK_RUN_CONTROL_TRACE`, and GLK 3.1.0 `RUN_PACKAGE_INDEX` plus the indexed formal artifacts. The selected method version and package hash must match the Canonical Manifest. A missing run reference yields `NOT_RECORDED`; an active run with an unsupported/mismatched method contract yields `BI_METHOD_VERSION_UNSUPPORTED` and a fail-closed Loop report.
- Calabash is not parsed internally. Its safe version record may be projected from the Canonical Manifest only after the manifest is valid. LCCoding does not absorb a Calabash schema.

Compatibility is explicit in tests and release notes. Supporting another version requires a new typed adapter and regression fixtures; it cannot be enabled by widening a string check.

### 8.1 Release dependency gate

LCCoding 2.5.0 cannot be published until all three adapter authorities are formal releases: SLK 2.5.0, CLK 2.5.0, and GLK 3.1.0 must each be present in its canonical repository's `main`, version tag, and GitHub Release. For every method, the release commit, schema/template set, manifest, and file hashes must mechanically agree with the adapter fixtures and expected contract identity.

The BI consumes only those published contract identities. An unpublished checkout, worktree, local candidate, or conversation statement cannot satisfy this gate or become an adapter source. A project with no active Run may still project Loop Governance as `NOT_RECORDED`, but the LCCoding 2.5.0 application itself cannot be released until all three supported adapters have been verified against their formal releases.

## 9. Authoritative data-source matrix

### 9.1 Four phases and 21 steps

All lifecycle states originate in `.lccoding/status.json`; other records may corroborate report detail but cannot change a step state. The existing normalization, chronology, future-state, stale-phase, aggregate, and final-delivery truth rules remain mandatory.

| Phase | Step | Exact authority |
|---|---|---|
| INITIAL | `PROPOSAL_READINESS` | `status.proposal` |
| INITIAL | `PROJECT_INITIALIZATION` | `status.initialization` |
| INITIAL | `INITIAL_READY` | `status.phase_gates.INITIAL_READY` |
| PRODUCT_FORMATION | `CALABASH_DRAFT` | `status.calabash_draft` |
| PRODUCT_FORMATION | `SIMULATION_WORLD_FOUNDATION` | `status.simulation` |
| PRODUCT_FORMATION | `WORKFLOW_CAPABILITY_END` | `status.workflow` |
| PRODUCT_FORMATION | `UI_PRODUCT_SURFACE_END` | `status.ui` |
| PRODUCT_FORMATION | `CALABASH_UPGRADE_READY` | `status.phase_gates.CALABASH_UPGRADE_READY` |
| ENGINEERING_RUNS | `MANDATORY_CALABASH_UPGRADE` | `status.mandatory_calabash_upgrade` |
| ENGINEERING_RUNS | `PRODUCT_BASELINE` | `status.product_baseline` |
| ENGINEERING_RUNS | `FEATURE_SLICE_EXECUTION_COVERAGE` | existing grouped rule over `active_slice` and downstream facts; never an entry-Gate verdict |
| ENGINEERING_RUNS | `UI_LOCKED_INTEGRATION_BASELINE` | valid non-null `status.integration_baseline` means established; null means pending |
| ENGINEERING_RUNS | `LOOP_RUN_D0_D3` | existing grouped rule over `active_runs`, aggregate, and acceptance facts |
| ENGINEERING_RUNS | `LOOP_OWNER_ACCEPTANCE` | existing aggregate + `loop_owner_acceptances` consistency rule |
| ENGINEERING_RUNS | `ALL_REQUIRED_RUNS_ACCEPTED` | top-level field must equal `phase_gates.ALL_REQUIRED_RUNS_ACCEPTED` |
| DELIVERY_PREPARATION | `CENTRALIZED_VULNERABILITY_AUDIT` | `status.centralized_security_audit` |
| DELIVERY_PREPARATION | `SECURITY_REMEDIATION` | `status.security_remediation` |
| DELIVERY_PREPARATION | `SECURITY_REAUDIT_VULNERABILITY_CLOSURE` | existing grouped `status.vulnerability_closure` fact |
| DELIVERY_PREPARATION | `POST_SECURITY_OWNER_ACCEPTANCE` | `status.post_security_owner_acceptance` |
| DELIVERY_PREPARATION | `DELIVERY_METHOD_QA` | `status.delivery_method_qa` |
| DELIVERY_PREPARATION | `DELIVERY_PACKAGE_GUARD_READY` | `status.phase_gates.DELIVERY_READY`; it does not duplicate post-gate delivery |

`PHASE-STATUS.json` remains a derived view and `PROJECT-HEALTH.json` remains assessment evidence. They may be cross-checked for corruption diagnostics but never override `status.json` or create a displayed state.

### 9.2 Eight protected reports

| Report | Exact authority and validation | Compatibility / fail-closed rule |
|---|---|---|
| Proposal | `status.proposal` and `phase_gates.INITIAL_READY`; `PROPOSAL-READINESS.md` may corroborate a safe conclusion but never override status | missing corroboration is `NOT_RECORDED`; contradictory completed evidence is record inconsistency |
| Canonical Candidate | exact `status.canonical_candidate` triple plus `status.initialization`; Git identity is validated internally | partial identity, invalid version/commit, or unresolvable commit is error; repository/commit never serialize |
| Calabash | `status.calabash_draft` plus safe Calabash version from valid Canonical Manifest | absent version is `NOT_RECORDED`; invalid Manifest is error; no Calabash internals are read |
| Simulation | exact registry in `SIMULATION-WORLD.md`: peer IDs, implementation/foundation facts, component versions, and Primary mainline membership | only structurally valid peer rows count; no nested Simulation is inferred; post-Baseline verified counts require matching Handoff/Git identity |
| Workflow | exact rows in `WORKFLOW-MAP.md`: `CORE/EXTRA`, implementation, component version, API evidence, MCP evidence, and Primary mainline | unimplemented EXTRA creates no interface claim; implemented CORE/EXTRA without API or MCP is violation; duplicate/drifting identity is error |
| UI | exact rows in `UI-MAP.md`: implementation, component version, lock state, and Primary mainline | only realized rows count; post-Baseline locked counts require matching Handoff/Git identity; no private repo/path is exposed |
| Product Baseline | `PRODUCT-BASELINE-HANDOFF.md`, all three Maps, total-project Git repository, frozen exact commit, subtree trees/blobs, content hashes, and Owner-confirmed Primary mainline | every locked ID/path/version/hash/classification/interface/mainline fact must match its Map and recomputed commit content; any mismatch is error |
| Loop Governance | `status.active_runs` SafeRefs resolved to one supported canonical method index/trace/package and its strictly indexed receipts | missing inactive evidence is `NOT_RECORDED`; malformed, extra, stale, wrong-scope, mismatched-version, or contradictory active evidence fails closed |

Before Product Baseline, a valid Map row may show recorded/active progress but cannot be labeled locked or Git-verified. After `status.product_baseline` is complete, absent Handoff, unresolvable frozen commit, missing subtree tree, hash mismatch, Map/Handoff drift, incomplete CORE API/MCP evidence, or missing Owner confirmation is a whole-record contradiction.

### 9.3 Loop Governance normalization

The frontend always sees the same seven metrics. Rust keeps three narrow adapters and normalizes only validated facts:

| Metric | SLK 2.5.0 | CLK 2.5.0 | GLK 3.1.0 | Fail-closed projection |
|---|---|---|---|---|
| Worker → Checker wake | `RUN_RUNTIME_INDEX` → runtime contract, worker wake trace, ACK/PENDING evidence | `CLK_RUN_CONTROL_TRACE.worker_bindings/events` | indexed `WORKER_CHECKER_WAKE_BINDING`, `WAKE_ATTEMPT`, `WAKE_ACK`, `PENDING_WAKE` | four bounded levels and frozen Checker scope must be complete; incomplete active chain is `ACTIVE`, invalid chain is `VIOLATION` |
| Supervisor wait discipline | current complete patrol receipt checklist | patrol status event/check | indexed `MONITOR_CONTROL` `SUPERVISOR_WAIT` check | long/looping/wait-all evidence is `VIOLATION`; absence is never guessed compliant |
| Temporary Heartbeat | current `RUN_PATROL_RECEIPT` and terminal cleanup | patrol entry/events and terminal cleanup | `MONITOR_CONTROL` and terminal package evidence | exactly one temporary Heartbeat; interval only 10/15/30; terminal record must prove delete/archive |
| No subagents | patrol subagent check plus runtime contract | patrol check plus method role/event evidence | `MONITOR_CONTROL` `SUBAGENT_EVIDENCE` plus formal role bindings | visible tasks/subtasks are not subagents; actual spawn/delegate/hidden/background Agent evidence is `VIOLATION` |
| Progress receipt | `PROGRESS_TRACE` required sets and receipt-bound events | required sets plus Checker/Supervisor progress events in control trace | indexed `CHECKER_PROGRESS_EVENT` and `SUPERVISOR_PROGRESS_EVENT` | only receipt-derived counts; `completed <= total`; denominator changes require a valid required-set version |
| CELL capacity | current device profile, cumulative load, and capacity gate indexed by the Run | corresponding profile/load/gate sections in control trace | indexed `DEVICE_CAPACITY_PROFILE`, `CUMULATIVE_ENGINEERING_LOAD`, `CELL_CAPACITY_GATE` | unknown or non-PASS dispatch capacity cannot project compliant; split/blocked remains visible |
| Pin policy | thread-pin audit plus patrol Pin check | role capabilities, pin observations, and patrol Pin check | formal role capabilities plus `MONITOR_CONTROL` `THREAD_PIN` check | unauthorized or unknown provenance is `VIOLATION`; the BI itself never pins method tasks |

The method adapter first validates the method's canonical aggregate and references; it does not scan for whichever receipt looks favorable. Every metric uses `COMPLIANT`, `ACTIVE`, `VIOLATION`, `UNKNOWN`, or `NOT_RECORDED`. Numeric progress appears only with proven numerator and denominator; Heartbeat interval appears only with proven 10/15/30. Raw task IDs, thread IDs, evidence refs, messages, model names, paths, and timestamps never reach Snapshot.

## 10. Truth and fail-closed rules

The projector distinguishes absence, uncertainty, operational failure, and corruption:

- `NOT_RECORDED`: the canonical optional record or applicable receipt does not exist and the lifecycle has not claimed it complete.
- `UNKNOWN`: a structurally valid source states that a fact is unresolved, or compatible evidence cannot prove a stronger state.
- `ACTIVE`: a valid canonical record proves bounded work is in progress.
- `VIOLATION` or step `error`: a valid authority explicitly records a blocked/failed/noncompliant condition.
- complete error Snapshot: schema failure, unsupported authoritative version, path/identity failure, map drift, chronology contradiction, stale aggregate, malformed active method package, or projection invariant failure.

The projector never promotes absence to success, uses a coarse field to invent two precise substep states, or treats a version label as identity evidence. Commit and recomputed content hash remain the subtree identity authority; versions are human-readable labels only.

Every report state equals the associated main-step state. A report cannot claim complete while its Open step is pending. Product Baseline and Loop Governance metrics cannot change `status.json`; they can expose inconsistency by forcing a safe error projection.

## 11. Refresh and interaction data flow

After binding, startup calls `get_snapshot()` once. The frontend schedules the next automatic refresh two seconds after the previous request settles, not on a fixed overlapping interval.

- Frontend and Rust each enforce single-flight. Concurrent auto/manual calls join the same in-flight future; they do not queue another read.
- Rust performs bounded filesystem/Git reads and parsing inside `spawn_blocking` and returns to async command execution only with a sanitized result.
- Manual Refresh cancels the idle timer, joins or starts the single read, then restarts the two-second delay after settlement.
- A new read error immediately replaces any old green dashboard with the fixed red error projection. The next valid refresh restores the current mode and latest safe Snapshot without exposing stale claims.
- Open/Back, language, folds, internal scroll, and Pin do not write project data. Refresh preserves logical report origin and focus using closed IDs, never detached DOM nodes.
- Closing the window cancels the timer, prevents late async settlement from changing UI, drops the bound handles, and exits. There is no tray process or background service.

The Rust projector is the production `SnapshotSource`. Test fixtures are never selected by query string, environment variable, production fallback, or error recovery.

## 12. Error and recovery contract

| Condition | Fixed code | User-visible recovery |
|---|---|---|
| no project selected | `BI_NO_PROJECT` | binding view; type a root or choose a folder |
| invalid or unsafe root | `BI_ROOT_INVALID` | remain unbound; choose another root |
| not a canonical LCCoding project | `BI_PROJECT_NOT_LCCODING` | remain unbound; initialize/choose a conforming project |
| unsupported LCCoding/method version | `BI_PROJECT_VERSION_UNSUPPORTED` / `BI_METHOD_VERSION_UNSUPPORTED` | upgrade the project method records or use a supported project |
| malformed or inconsistent records | `BI_RECORD_INVALID` / `BI_RECORD_INCONSISTENT` | fix canonical project records; Refresh retries after correction |
| unstable file identity/read race | `BI_READ_RACE` | stop concurrent replacement and Refresh; auto refresh retries later |
| resource budget exceeded | `BI_RESOURCE_LIMIT` | reduce the canonical record to supported bounds |
| WebView2 absent or unusable | `BI_WEBVIEW_UNAVAILABLE` | rerun the same verified LCCoding 2.5.0 NSIS installer with network access; application opens no webview |
| invariant/projection failure | `BI_PROJECTION_FAILED` | correct records or reinstall the matching LCCoding release |

Frontend copy is a fixed localized catalog keyed by these classes; internal codes may appear only in the safe error surface and process exit status. No raw exception, root, filename, Git reference, repository, commit, hash, evidence, URL, thread ID, record fragment, or secret is logged or rendered.

If WebView2 cannot initialize, Rust uses one native fixed-text error dialog instructing the user to rerun the same verified LCCoding 2.5.0 NSIS installer, then exits `2` before webview creation. It does not print or install arbitrary dependencies.

## 13. Tauri and webview security

- Ship local Vite assets only. Deny remote navigation, new windows, downloads, forms, arbitrary protocols, and external resources.
- Preserve a strict effective CSP: self-hosted scripts/styles/assets only, IPC connect sources only, no wildcard, `unsafe-inline`, `unsafe-eval`, object, frame, base, or external source. Build verification accepts only Tauri-generated hash/nonce additions.
- The resolved capability catalog names only the five commands in section 5.3. No directory can contribute an automatically merged extra capability.
- The frontend has no filesystem or Git dependency and no project selector after binding.
- Rust uses typed outputs with `serde` unknown-field denial and a final recursive output audit that rejects forbidden keys and path/URL/remote/hash/evidence patterns before IPC serialization.
- Production logging is code-only. Debug builds used for reader tests still redact roots and raw inputs.
- `gix` reads local objects and refs only; its transport/network features are disabled, and no hooks, filters, attributes, submodules, external commands, credential helpers, or network remotes execute. Its exact crate version is fixed later by the implementation plan and package lock rather than invented in this design.
- The app never writes the project, creates lock files within it, changes Git index/worktree state, or updates modification times.

## 14. React migration and Vanilla retirement

Migration is parity-first and atomic at release:

1. Framework-neutral Snapshot types, closed catalog, visual tokens, approved CSS, and sanitized test fixtures may be reused.
2. React recreates the binding view, four-phase main view, eight reports, Pin/Refresh, language, folds, scroll, focus, safe error, and reduced-motion behavior at the same 300×480 viewport.
3. Screenshot and DOM parity are accepted before Rust data integration changes the visual source.
4. The Rust projector replaces the fixture source behind the same Snapshot boundary.
5. The old imperative entry/controller/render modules and production fixture selector are deleted in the same candidate that makes React the only runtime.

Fixture JSON may remain only under test-owned paths. Build graph tests fail if the production Vite entry, React components, Tauri resources, or packaged assets import or copy a fixture. There is no hidden `demo`, query-string, or fallback mode in the shipped executable.

## 15. Windows distribution

LCCoding 2.5.0 publishes one NSIS `-setup.exe` installer configured for the current user. Tauri's current-user mode installs under the user profile and does not require administrator rights. The installer uses `webviewInstallMode.type = "embedBootstrapper"`, replacing 2.4.1's unsafe `skip`: the Microsoft Evergreen Bootstrapper is included in the installer and installs the architecture-matched WebView2 runtime when absent. This choice adds little installer size but requires network access for first-time WebView2 installation. Offline installation is not claimed.

The choice follows the [Tauri Windows installer contract](https://v2.tauri.app/distribute/windows-installer/), which documents current-user NSIS installation and the embedded-bootstrapper mode, and the [Microsoft WebView2 distribution contract](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution), which documents Evergreen bootstrapper deployment and non-elevated per-user installation.

The installer may install WebView2 because it is the explicitly approved webview prerequisite. It cannot install Node, npm, Rust, Cargo, Python, Git, Docker, a database, a service, or any other runtime. If the bootstrapper cannot complete, the installer returns a fixed safe failure and does not leave an apparently usable BI. Recovery is to rerun that same verified 2.5.0 NSIS installer when network access is available.

The formal GitHub Release assets are at least:

- the current-user NSIS installer;
- a separate SHA-256 file for that exact installer;
- a machine-readable provenance record containing overall version `2.5.0`, source commit, build workflow/run identity, target triple, installer filename/hash, and build-tool lock hashes.

Release verification recomputes the installer hash and matches version/commit provenance before publication. The BI creates no independent tag or Release. Automatic application update is absent from 2.5.0.

## 16. Test and acceptance design

### 16.1 React parity and product tests

- exact four phases, 21 steps, eight Open mappings, report row order, state symbol/text/color, English/Chinese catalog completeness;
- same-window Open/Back, logical origin focus, language/fold/scroll preservation, Refresh and Pin confirmed states, error/recovery, destroy safety;
- exact 300×480 client viewport, non-resizable window, internal overflow, maximum safe project name, normal/reduced motion, contrast, and existing screenshot baselines;
- React screenshots match the approved baseline within an intentional reviewed tolerance before the Vanilla runtime is removed;
- no router, card system, second window, fixture selector, raw HTML, external URL, or unexpected control.

### 16.2 Rust reader and projection tests

- strict parsing and chronology for every supported `status.json` version and all 21 sources;
- each of the eight reports against valid, missing, unknown, malformed, contradictory, and post-Baseline records;
- real temporary Git repositories opened through `gix`, with real commits, trees, tracked blobs, Map/Handoff identities, recomputed subtree hashes, linked-worktree admission, and mismatch negatives;
- plural peer Simulation, plural Workflow/UI, CORE/EXTRA, implemented-only API/MCP, component version coverage, Primary mainline, and Baseline lock semantics;
- exact SLK/CLK/GLK adapter fixtures plus stale/extra/missing/wrong-scope receipts, denominator changes, progress bounds, 10/15/30 Heartbeat bounds, violation/active/unknown results;
- report-state-to-step-state equality and complete Snapshot output allowlist;
- no project modification: byte-for-byte and modification-time snapshots before and after binding, repeated auto refresh, manual refresh, reports, and close.

### 16.3 Security negatives

- root/file symlinks, junctions, reparse points, dangling links, linked-worktree indirection abuse, device/FIFO, race replacement, non-regular files;
- oversize, invalid UTF-8, duplicate keys, unknown fields, deep/wide collections, hostile numbers, Markdown ambiguity, YAML anchors/tags/aliases, unsafe display names;
- malicious paths, URLs, remotes, commits, hashes, evidence bodies, thread IDs, raw errors, and secrets proven absent from Snapshot, DOM, logs, crash output, and Release fixtures;
- `get_snapshot` rejects an unbound process and has no path argument; a second bind is rejected; command and capability allowlists contain no extra surface;
- no Git hook/filter/submodule/network/process execution, and no Git executable dependency.

### 16.4 Refresh and binding tests

- typed root, picker root, and CLI root produce the same bound identity and Snapshot through the same validator;
- one request in flight across auto and manual refresh, two-second post-settlement scheduling, no queued read, fixed error on race, and later recovery;
- multiple processes bind different roots without shared state; one process cannot switch roots;
- unbound, invalid, non-project, unsupported, malformed, race, projection, and WebView2 error paths expose only fixed codes/copy;
- production module graph and packaged resources contain no runtime fixture or project path.

### 16.5 Installer and clean-machine acceptance

On clean supported Windows x64 and, when released, each additional declared target architecture:

1. start with no LCCoding source checkout, Node, npm, Rust, Cargo, Python, or Git executable;
2. install the NSIS asset as current user without elevation;
3. when WebView2 is absent, prove the embedded bootstrapper path installs a usable Evergreen runtime; also test the fixed offline/network failure, safe exit, and successful rerun of the same verified installer;
4. launch without arguments, bind a real canonical project by native picker, and verify real dashboard data;
5. launch `lccoding-bi --project <root>` and verify the same Snapshot;
6. observe a canonical status change through two-second auto refresh, use manual Refresh, open all eight reports, switch language, toggle Pin, and close;
7. reopen and bind again, proving no stored project path and no source/runtime dependency;
8. compare every project fixture byte and modification time before and after;
9. verify installer SHA-256, source commit provenance, `lccoding-bi.exe` identity, absence of legacy `lccoding.exe`, Start Menu display name `LCCoding BI`, `Get-Command lccoding-bi` resolution to that exact installed executable, PATH registration, absence of an alias or `.cmd` shim, and exact uninstall cleanup.

The Release is invalid if these checks run only from a development checkout or if the executable succeeds because Node, Cargo, Python, fixtures, or a Git CLI happen to exist.

Release verification also blocks publication until the SLK 2.5.0, CLK 2.5.0, and GLK 3.1.0 dependency gate in section 8.1 resolves against each canonical `main`, tag, GitHub Release, and matching schema/template/hash set.

## 17. Version and release migration

2.5.0 is one atomic overall LCCoding release. Implementation must update the existing overall version carriers, migration note, changelog, validation report, manifest, file hashes, installer metadata, and Release title/tag together. It must not create `BI_VERSION`, a BI tag, or separate BI release notes.

Project records are not auto-migrated or written by the BI. A 2.4.0/2.4.1 project may be read through the exact compatibility adapters above. A project outside that boundary receives the fixed incompatible-version result and must be upgraded through normal LCCoding project maintenance before use.

The 2.4.1 static executable is replaced, not installed side-by-side. NSIS upgrades the same application identity, installs only `lccoding-bi.exe` as the command binary, removes legacy `lccoding.exe` from the prior installation, and preserves no root history. Rollback means uninstalling 2.5.0 and installing a prior overall LCCoding installer; it does not change project data.

## 18. Explicit non-goals

- multi-project overview, recent-project list, tabs, or aggregate dashboard;
- BI writes, project migration, status editing, acceptance, dispatch, wait, wake, Heartbeat, archive, Pin governance, or Agent/runtime/session control;
- opening original files, evidence bodies, repositories, commits, paths, URLs, terminals, editors, or browsers;
- remote service, local server, database, cache, filesystem watcher, Python runtime, Node runtime, or Git executable in the installed product;
- per-project BI generation, source copy, package installation, or compilation;
- automatic application updates;
- compatibility with arbitrary noncanonical or unknown future project/method formats;
- visual redesign, router, state library, component framework, dashboard cards, second window, or new lifecycle node/gate/status field;
- duplication of Calabash, SLK, CLK, or GLK internal decisions.

## 19. Recommended implementation slices

These are dependency boundaries for later approved engineering work, not LCCoding lifecycle phases, gates, or an implementation plan.

1. **React parity slice:** render test-owned sanitized Snapshots through React, pass DOM/accessibility and approved screenshot parity, and keep production disconnected from project files.
2. **Rust binding/security slice:** implement immutable root binding, strict readers, embedded Git access, typed canonical records, source matrix validation, and sanitized Snapshot projection under Rust tests.
3. **Bridge/refresh slice:** expose the five-command ACL, connect React to no-argument `get_snapshot`, and prove single-flight refresh, error recovery, and fixture absence.
4. **Runtime retirement/package slice:** delete the imperative Vanilla runtime and fixture selector, enable only the React build, configure current-user NSIS and embedded WebView2 Bootstrapper, and verify package provenance.
5. **Release acceptance slice:** run the clean-machine matrix with no source environment, verify project immutability and Release assets, then perform the one overall 2.5.0 version/release update.

No slice is complete merely because its UI works in Vite. The released success condition is the installed, real-project, read-only end-to-end path.

## 20. Design invariants

- one LCCoding BI, one overall version, one packaged runtime;
- one process/window, one immutable project root;
- one authoritative project status, one read-only sanitized projection;
- React replaces Vanilla runtime; fixtures remain test-only;
- fixed project structure and lower-method contracts remain owned by their methods;
- no path after binding and no path argument to `get_snapshot`;
- no stale green state after a failed read;
- no project writes, hidden runtime, remote service, or second truth source;
- no visual or lifecycle redesign in the name of the technology migration.
