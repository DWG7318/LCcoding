# Built-in Project BI — LCCoding 2.6.0

This reference is the focused product contract for LCCoding's built-in project BI. The BI ships only as part of LCCoding 2.6.0: it has no independent version, repository, tag, release, lifecycle, or authority. Implementation, build, test, and release navigation lives only in the [BI subtree README](../bi/README.md).

## 1. Product boundary

Source clauses: [LC-BI-001](../../SPEC.md#lc-bi-001), [LC-BI-002](../../SPEC.md#lc-bi-002)

- Each adopting LCCoding project has one local BI for that project only. There is no multi-project control surface.
- The BI is a read-only projection of the project's existing authoritative method records. `status.json` remains the single authoritative project status; the BI never writes it and never becomes a second truth source.
- The BI does not control an Agent, session, process, queue, retry, tool, runtime, or lower method. It does not absorb Calabash, SLK, CLK, or GLK internals.
- The desktop application is Tauri 2 with one bundled React/TypeScript frontend built by Vite and one Rust projection core. It ships no Vanilla runtime, Python/Node subprocess, second runtime, remote web application, router, state library, or unrelated UI framework.
- Windows uses the installed WebView2 runtime. The application remains capable of using Tauri's supported native webview on other desktop platforms without changing the projection contract.
- Every application version carrier must equal the overall LCCoding version. There is no BI-specific version field or release identity.

LCCoding 2.6.0 installs one reusable current-user tool. `lccoding-bi.exe --project <root>` and the native Folder Picker share one Rust validation and immutable binding; one process/window binds one project. The Rust core reads only the closed canonical record set and formally published Loop contracts, then emits one allowlisted sanitized Snapshot. Projects contain no BI source, npm, Rust, Python, Git CLI, or build requirement. Missing or unverifiable facts remain `UNKNOWN` or `NOT_RECORDED`.

## 2. Visual and interaction contract

### Window

- Use one native decorated desktop window whose logical client area is exactly `300 × 480`, with `resizable=false`, maximize disabled, and no custom imitation of operating-system window controls. Native borders and titlebar may add only their normal outer size.
- The client area never grows when a phase or report opens. The body scrolls internally; the title/control strip and refresh status remain fixed.
- Use a `34px minmax(0, 1fr) 32px` client grid: control strip, internally scrolling body, and refresh strip. Body padding is `8px`; the spacing scale is `4/6/8/12px`; separators are `1px`; corner radius never exceeds `6px`.
- Use Segoe UI where available, followed by the system sans-serif. The base size is `14px` at `1.4` line height; the report heading is `15px`; phase, step, state, row, control, and metadata text never falls below `12px`.
- Phase summaries are at least `36px` high, step and report rows at least `34px`, and buttons at least `28px` high with `8px` horizontal padding. Use the native scrollbar rather than a styled decorative scrollbar.
- Every keyboard-focusable control has a persistent `2px #2563eb` outline with `2px` offset. Hover, pressed, disabled, error, and focus states retain the same component vocabulary.
- The register is a plain PowerShell-like utility: white surface, restrained neutral chrome, compact separators, standard buttons, and no card grid, gradient, glass, large shadow, ornamental illustration, dashboard chrome, or decorative motion.
- Safety, authoritative truth, read-only behavior, accessibility, and fail-closed reliability are non-negotiable gates. Only among UI choices that already satisfy those gates, preserve this order: visual fidelity first, reliability second, and avoidance of unnecessary bloat third.

This reference is self-contained: no machine-local prototype path or metadata is part of the product contract. The normalized dimensions, tokens, labels, and behavior below govern both the React product and its test-only visual fixtures; the accepted screenshot set remains the portable golden visual baseline.

### Language and text

- English is the canonical and default display language. A visible control switches every fixed interface label to a complete Chinese catalog.
- The language control is one standard button displaying `EN | 中`; the active language is bold and underlined. Its accessible name is `app.language_current_en` or `app.language_current_zh`, so current value and next action are both announced.
- Owner/project-authored text is never machine-translated. A project name that passes the Rust display-name policy is shown byte-for-byte as decoded Unicode; unsafe text produces the generic failure projection instead.
- State is never communicated by color alone. Every state has a symbol and localized text: complete, error/blocked, active, or not reached.

The catalog is a closed `MessageKey -> { en, zh_CN }` map. Build and DOM tests require identical key sets and reject fallback to English while Chinese is active. These are the canonical non-step strings:

| Key | English | Chinese |
|---|---|---|
| `app.title` | LCCoding BI | LCCoding BI |
| `app.read_only` | Read-only project view | 只读工程视图 |
| `app.refresh` | Refresh | 刷新 |
| `app.updated` | Updated now | 刚刚更新 |
| `app.pin_on` | Pin: On | 置顶：开 |
| `app.pin_off` | Pin: Off | 置顶：关 |
| `app.pin_checking` | Pin: Checking | 置顶：检查中 |
| `app.pin_unavailable` | Pin: Unavailable | 置顶：不可用 |
| `app.pin_error` | Pin state unavailable | 无法读取置顶状态 |
| `app.open` | Open | 打开 |
| `app.back` | Back | 返回 |
| `app.language_display` | EN \| 中 | EN \| 中 |
| `app.language_current_en` | Language: English; switch to Chinese | 语言：英文；切换到中文 |
| `app.language_current_zh` | Language: Chinese; switch to English | 语言：中文；切换到英文 |
| `app.error` | Authoritative status unavailable | 权威状态不可用 |
| `app.unnamed_project` | Unnamed project | 未命名工程 |
| `app.protected` | Read-only sanitized report; no project file, source, private repository, evidence body, URL, or local path access | 只读安全报告；不访问工程文件、源码、私有仓库、证据正文、网址或本地路径 |
| `state.done` | Complete | 已完成 |
| `state.active` | Running | 执行中 |
| `state.pending` | Not reached | 未到达 |
| `state.error` | Error or blocked | 错误或阻塞 |
| `value.locked` | Locked | 已锁定 |
| `value.recorded` | Recorded | 已记录 |
| `value.present` | Present | 存在 |
| `value.not_recorded` | Not recorded | 未记录 |
| `value.pending` | Pending | 待处理 |
| `value.unknown` | Unknown | 未知 |
| `report.proposal` | Proposal Readiness | 提案就绪 |
| `report.candidate` | Canonical Candidate | 权威候选 |
| `report.calabash` | Calabash | Calabash |
| `report.simulation` | Simulation World | Simulation World |
| `report.workflow` | Workflow | Workflow |
| `report.ui` | UI Baseline | UI 基线 |
| `report.baseline` | Product Baseline | 产品基线 |
| `report.loop_governance` | Execution Method Governance | 工程方法治理 |
| `row.conclusion` | Conclusion | 结论 |
| `row.initial_gate` | Initial gate | 初始门禁 |
| `row.identity` | Identity | 身份 |
| `row.integrity` | Integrity | 完整性 |
| `row.status` | Status | 状态 |
| `row.version_record` | Version record | 版本记录 |
| `row.current_phase` | Current phase | 当前阶段 |
| `row.realized_peer_subtrees` | Realized peer subtrees | 已实现同级子树 |
| `row.realized_subtrees` | Realized subtrees | 已实现子树 |
| `row.component_version_coverage` | Component version records | 组件版本记录 |
| `row.primary_mainline` | Primary mainline | 产品主线 |
| `row.core_implementation` | CORE implemented | CORE 已实现 |
| `row.extra_implemented` | EXTRA implemented | EXTRA 已实现 |
| `row.extra_deferred` | EXTRA deferred | EXTRA 已延期 |
| `row.api_coverage` | API coverage | API 覆盖 |
| `row.mcp_coverage` | MCP coverage | MCP 覆盖 |
| `row.lock_status` | Lock status | 锁定状态 |
| `row.git_identity` | Verified project Git identity | 已验证总项目 Git 身份 |
| `row.locked_subtree_coverage` | Locked subtree coverage | 锁定子树覆盖 |
| `row.map_handoff_consistency` | Map / Handoff consistency | Map / Handoff 一致性 |
| `row.owner_confirmed_mainline` | Owner-confirmed mainline | Owner 确认产品主线 |
| `row.worker_checker_wake` | Worker → Checker wake chain | Worker → Checker 唤醒链 |
| `row.supervisor_wait` | Supervisor wait discipline | Supervisor 等待纪律 |
| `row.heartbeat` | Temporary Heartbeat | 临时 Heartbeat |
| `row.no_subagents` | No subagents | 禁止子代理 |
| `row.progress` | Progress receipt | 进度回执 |
| `row.cell_capacity` | CELL capacity | CELL 容量 |
| `row.pin_policy` | Pin policy | 置顶规则 |
| `metric.compliant` | Compliant | 合规 |
| `metric.active` | Active | 执行中 |
| `metric.violation` | Violation | 违规 |
| `metric.unknown` | Unknown | 未知 |
| `metric.not_recorded` | Not recorded | 未记录 |

### State colors and motion

Neutral and control tokens are fixed before the first fixture:

| Token | Value | Use |
|---|---|---|
| `surface` | `#ffffff` | body and button default |
| `chrome` | `#f3f4f6` | fixed control/refresh strips and disabled control background |
| `soft` | `#f6f7f9` | restrained artifact/hover background |
| `ink` | `#20242b` | primary and ordinary report text |
| `muted` | `#667085` | secondary text |
| `separator` | `#d9dde3` | one-pixel separators and disabled border |
| `control_border` | `#838a94` | default button border |
| `control_hover_border` | `#4b5563` | hover/pressed border |
| `control_pressed` | `#e5e7eb` | pressed button background |
| `focus` | `#2563eb` | two-pixel focus outline |
| `error_surface` | `#fff4f4` | failure projection background |
| `protected_surface` | `#edf2ff` | protected-report notice |
| `protected_ink` | `#30456f` | protected-report notice text |

Default buttons use `surface/ink/control_border`; hover uses `soft/control_hover_border`; pressed uses `control_pressed/control_hover_border`; disabled uses `chrome/muted/separator` without opacity. No neutral or state token is produced by alpha-blending with the surface.

| State | Token | Required presentation |
|---|---|---|
| complete | `#198754` | check symbol + Complete/已完成 |
| error or blocked | `#c92a2a` | alert symbol + Error or blocked/错误或阻塞 |
| active | `#2563eb` | spinner + Running/执行中 |
| not reached | `#6b7280` | hollow symbol + Not reached/未到达 |

All four tokens must retain at least `4.5:1` contrast on white. The green token is already near the threshold and must never be lightened, blended with white, or rendered with opacity below `1`. Normal report values use neutral ink rather than inheriting a report-wide state color. Under `prefers-reduced-motion: reduce`, the spinner becomes a static state mark while the active text remains visible.

### Four phase views

The main view is one vertical, foldable sequence in this fixed order. It exposes only status facts that the current LCCoding records can support.

1. `INITIAL` / 初始
   - Proposal Readiness / 提案就绪
   - Project Initialization / 工程初始化
   - phase exit `INITIAL_READY` / 初始就绪门禁
2. `PRODUCT_FORMATION` / 产品形成
   - Calabash Draft / Calabash 草案
   - Simulation World foundation / Simulation World 基础
   - Workflow capability end / Workflow 能力端
   - UI product-surface end / UI 产品呈现端
   - phase exit `CALABASH_UPGRADE_READY` / Calabash 升级就绪门禁
3. `ENGINEERING_RUNS` / Real Product Integration / 真实产品集成
   - Mandatory Calabash Upgrade / 强制 Calabash 升级
   - Product Baseline / 产品基线
   - Feature Slice · Execution Coverage Preflight / Feature Slice · 执行覆盖预检
   - UI-locked Integration Baseline / UI 锁定集成基线
   - Real Product Integration · D0–D3 Proof / 真实产品集成 · D0–D3 证明
   - Loop Owner Acceptance / Loop Owner 验收
   - aggregate exit `ALL_REQUIRED_RUNS_ACCEPTED` / 全部必需 Run 已验收
4. `DELIVERY_PREPARATION` / 交付准备
   - Centralized Vulnerability Audit / 集中漏洞审计
   - Security Remediation / 安全修复
   - Independent Security Re-audit · Vulnerability Closure / 独立安全复审 · 漏洞关闭
   - Post-Security Owner Acceptance / 安全后 Owner 验收
   - Delivery Method Q&A / 交付方法问答
   - Delivery Package Guard · `DELIVERY_READY` / 交付包保护 · 交付就绪门禁

Phase catalog keys are exactly `phase.<PhaseId>` and step catalog keys exactly `step.<StepId>`, using the IDs in section 6 and the English/Chinese labels above. Together with the closed table in the Language section, that is the complete fixed-text catalog; a literal user-visible string outside it fails the catalog test.

Only the current phase starts expanded. Folding, scrolling, and language changes are frontend-local view state and never change project data.

### Protected reports

Exactly eight `Open` actions are available: the existing Proposal Readiness, Canonical Candidate, Calabash, Simulation World, Workflow, and UI Baseline actions, plus Product Baseline on the existing `PRODUCT_BASELINE` step and Execution Method Governance on the compatibility `LOOP_RUN_D0_D3` step ID. No phase or step is added. `Open` replaces the body inside the same window with a fixed, sanitized report; `Back` restores the prior phase view and scroll/fold state.

- Report titles, row labels, and row order come from a compiled catalog, never from project input.
- Candidate may show only `LOCKED/PENDING/UNKNOWN`, `RECORDED/PENDING/UNKNOWN`, and a validated version. Repository and commit values never reach the frontend.
- Calabash may show its validated current version when a complete Canonical Manifest supplies it. Simulation, Workflow, UI, Product Baseline, and Execution Method Governance have no report-header version source; their header version stays Not recorded/未记录. Component-version completeness appears only as a sanitized metric and never exposes a component version, path, commit, hash, evidence, or raw artifact.
- Subtree and Product Baseline metrics may eventually derive only from successful 2.4.0+ Maps/Handoff mechanical validation. Execution-method metrics may eventually derive only from normalized registered-method contracts and valid receipts. SLK/CLK/GLK are not treated as an exhaustive list. The BI never copies internal methods, writes `status.json`, judges execution, or performs wake/wait/Heartbeat/archive/pin operations.
- The BI remains a lifecycle projection. Cross-phase method activity is phase-local evidence; it does not become a lifecycle node or automatically activate the third-phase integration step.
- Status rows use their own semantic color. Non-state values use neutral ink, so a blocked row can never appear green because another row or the report is complete.
- The protected-report notice states that the view cannot open project files, source, private repositories, evidence bodies, URLs, or local paths.

No Open or Back action creates an anchor, navigation request, download, file read, or shell action.

The report tuples and row order are exact:

| Report | Header version | Ordered row key | Rust source | Wire value |
|---|---|---|---|---|
| `proposal` | `null` | `row.conclusion` | `status.proposal` | `view_state` |
| `proposal` | `null` | `row.initial_gate` | `status.phase_gates.INITIAL_READY` | `view_state` |
| `candidate` | validated `canonical_candidate.version` or `null` | `row.identity` | Candidate completeness | `lock` |
| `candidate` | same | `row.integrity` | Candidate completeness + `status.initialization` | `record` |
| `calabash` | validated `manifest.calabash.version` or `null` | `row.status` | `status.calabash_draft` | `view_state` |
| `calabash` | same | `row.version_record` | complete Manifest + safe Calabash version | `record` |
| `simulation` | `null` | `row.realized_peer_subtrees`; `row.component_version_coverage`; `row.primary_mainline` | validated peer Simulation subtree summary | `metric` |
| `workflow` | `null` | `row.core_implementation`; `row.extra_implemented`; `row.extra_deferred`; `row.api_coverage`; `row.mcp_coverage`; `row.component_version_coverage`; `row.primary_mainline` | validated Workflow Map/Handoff summary | `metric` |
| `ui` | `null` | `row.realized_subtrees`; `row.component_version_coverage`; `row.lock_status`; `row.primary_mainline` | validated UI Map/Handoff summary | `metric` |
| `baseline` | `null` | `row.git_identity`; `row.locked_subtree_coverage`; `row.map_handoff_consistency`; `row.owner_confirmed_mainline` | successful Product Baseline mechanical validation summary | `metric` |
| `loop_governance` | `null` | `row.worker_checker_wake`; `row.supervisor_wait`; `row.heartbeat`; `row.no_subagents`; `row.progress`; `row.cell_capacity`; `row.pin_policy` | normalized, sanitized lower-method governance summary | `metric` |

Each report's `state` equals its associated main-step state. `StepView.report` is non-null only for the eight approved steps and equals the corresponding report ID; all other steps use `null`. Candidate/Manifest invalidity is a whole-record error, never a report-only warning. A metric is `{kind:"metric", status, completed, total, interval_minutes}`: status is exactly `COMPLIANT|ACTIVE|VIOLATION|UNKNOWN|NOT_RECORDED`; counts are bounded non-negative integers with `completed <= total`; and Heartbeat interval is only `10|15|30|null`. Unknown/unrecorded metrics contain no numeric claim.

## 3. Real-project data and trust flow

```text
one CLI- or Picker-selected project root, retained only in Rust
→ fixed .lccoding/status.json + optional .lccoding/CANONICAL-MANIFEST.json
→ bounded no-follow single-handle reader
→ strict JSON and typed schema validation
→ phase/gate/aggregate monotonic validation
→ fixed-field sanitization and Snapshot projection
→ no-argument Tauri get_snapshot invocation
→ DOM node creation with textContent
```

The webview never receives the startup root, a path, raw record body, repository, commit, evidence pointer/body, URL, command, log, stack, token, secret, or unknown field. Rust errors exposed through IPC are fixed error codes and localized-safe message keys; operating-system and parser details remain outside the DTO and user-visible stderr.

All wire keys use lower `snake_case`; all enums use the exact casing below. Every object rejects unknown or missing keys.

```text
Health     = "ok" | "error"
ViewState  = "done" | "active" | "pending" | "error"
PhaseId    = "INITIAL" | "PRODUCT_FORMATION" | "ENGINEERING_RUNS" |
             "DELIVERY_PREPARATION"
PhaseValue = PhaseId | "UNKNOWN"
ReportId   = "proposal" | "candidate" | "calabash" | "simulation" |
             "workflow" | "ui" | "baseline" | "loop_governance"
LockValue  = "LOCKED" | "PENDING" | "UNKNOWN"
RecordValue = "RECORDED" | "PRESENT" | "PENDING" | "NOT_RECORDED" |
              "UNKNOWN"
MetricStatus = "COMPLIANT" | "ACTIVE" | "VIOLATION" | "UNKNOWN" |
               "NOT_RECORDED"

RowValue =
  { "kind": "view_state", "value": ViewState } |
  { "kind": "phase",      "value": PhaseValue } |
  { "kind": "lock",       "value": LockValue } |
  { "kind": "record",     "value": RecordValue } |
  { "kind": "metric",     "status": MetricStatus,
    "completed": uint | null, "total": uint | null,
    "interval_minutes": 10 | 15 | 30 | null }

ReportRow  = { "key": RowKey, "value": RowValue }
ReportView = {
  "id": ReportId,
  "state": ViewState,
  "version": SafeVersion | null,
  "rows": readonly ReportRow[]
}
StepView   = { "id": StepId, "state": ViewState, "report": ReportId | null }
PhaseView  = { "id": PhaseId, "state": ViewState, "steps": readonly StepView[] }

Snapshot = {
  "schema": "LCCoding 2.6.0 derived BI",
  "authoritative": false,
  "read_only": true,
  "health": Health,
  "project": SafeProjectName | "Unnamed project",
  "current_phase": PhaseValue,
  "phases": readonly [InitialPhase, ProductFormationPhase,
                       EngineeringRunsPhase, DeliveryPreparationPhase],
  "reports": {
    "proposal": ProposalReport,
    "candidate": CandidateReport,
    "calabash": CalabashReport,
    "simulation": SimulationReport,
    "workflow": WorkflowReport,
    "ui": UiReport,
    "baseline": ProductBaselineReport,
    "loop_governance": LoopGovernanceReport
  }
}
```

`RowKey` is the closed set shown in the protected-report table; each report's row tuple, order, `kind`, and version source are fixed by that table. `StepId` and each phase's exact tuple are fixed by the source table in section 6. `SafeVersion` matches the exact rule in section 5.

Rust `serde` structs with `deny_unknown_fields` are the executable wire source. TypeScript uses one manually mirrored exact runtime guard; no schema generator or second model package is introduced. Implementation step A checks in `snapshot-ok.json` and `snapshot-error.json`; the TypeScript guard must accept and deep-freeze both. Implementation step C Rust tests must deserialize/serialize those same fixtures without shape or value drift, and each side must reject a one-field mutation of every object kind.

The sanitized visual `snapshot-ok.json` is deterministic: project `Example Project`; current phase `PRODUCT_FORMATION`; Initial done; Calabash and Simulation done; Workflow active; UI error; Product Formation exit pending; all later steps pending; Candidate version `v1.11.6`; and Calabash version `v2.4.0`. It contains no repository, commit, path, evidence, URL, date, or raw text. Chinese mode keeps `Example Project` unchanged. The second fixture is exactly the error Snapshot defined below.

For record/schema/truth errors, `get_snapshot()` returns the exact error Snapshot: `health="error"`, project `Unnamed project`, `current_phase="UNKNOWN"`, all four phases and every fixed step `error`, all eight reports `error`, versions `null`, legacy rows fail closed, and metric rows use `UNKNOWN` with no numeric claim. Startup argument failure emits only a fixed path-free code. No raw error is serialized or printed. Topmost failures use internal code `BI_PIN_UNAVAILABLE`; this diagnostic code is never rendered as user-facing text.

When `health="error"`, the frontend renders catalog key `app.unnamed_project` rather than treating the sentinel as Owner text. When `health="ok"`, a valid real project literally named `Unnamed project` remains Owner text and is displayed unchanged.

No free-form object or arbitrary report row crosses IPC. Production logs contain only fixed error codes and never the startup root, record content, parser detail, repository, commit, evidence, or secret value.

## 4. Adapter input safety and strict schemas

- Rust accepts either no project argument or exactly `--project <root>`. No argument opens the minimal binding view; malformed, duplicated, or additional CLI roots fail path-free before a project window is exposed. Typed binding and the native Folder Picker call the same root validator. The normalized root is retained in Rust managed state and cannot be replaced after binding.
- Each record has a `512 KiB` hard limit. Open one handle, read at most `limit + 1`, reject oversize, and verify the same file identity before/open/after the read. Do not stat one path and read through another handle.
- Reject a symlink, junction, reparse point, non-directory project or `.lccoding` boundary, non-regular record, dangling link, identity change, or unsupported no-follow guarantee before parsing.
- On Windows, open and inspect the root, record directory, and record with reparse-aware handles and stable volume/file identity. On Unix, retain anchored directory descriptors for the root and `.lccoding`, traverse fixed components with `openat`, and open a record with `O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK`; `fstat` must prove a regular file before any read. This prevents a regular-file-to-FIFO/device race from blocking. Platform adapters must produce the same path-free error contract.
- Before typed deserialization, the strict JSON layer enforces: UTF-8 only; nesting depth at most `32`; at most `16,384` total keys/values; at most `128` members per object; at most `2,048` items per array; at most `4,096` UTF-8 bytes per string; and at most `128` ASCII characters per numeric token. Duplicate keys at any depth, malformed/trailing data, non-finite/out-of-range numbers, and resource-limit excess fail closed. Current Status and Manifest schemas accept no JSON number fields.
- Supported `status_schema_version` values are exactly the closed compatibility set implemented by the reader, including `2.4.0`, `2.4.1`, `2.5.0`, `2.5.1`, `2.5.2`, and `2.6.0`. `record_role` is exactly `AUTHORITATIVE_PROJECT_STATUS`; `current_phase` is exactly one `PhaseId`. Any other version fails as incompatible rather than being guessed.
- `status.json` has no optional or extra top-level keys. Its exact key set is:

```text
record_role, status_schema_version, project_id, updated_at,
initialization_mode, continuity_decision, takeover_readiness,
canonical_candidate, existing_project_attestation,
existing_project_classification, current_phase, phase_gates,
proposal, initialization, calabash_draft, workflow, ui, simulation,
mandatory_calabash_upgrade, product_baseline, active_slice,
integration_baseline, active_runs, loop_owner_acceptances,
open_owner_gaps, all_required_runs_accepted,
centralized_security_audit, security_remediation,
vulnerability_closure, post_security_owner_acceptance,
delivery_method_qa, delivery, last_material_change, next_action,
evidence_pointers, blockers
```

- `phase_gates` has exactly `INITIAL_READY`, `CALABASH_UPGRADE_READY`, `ALL_REQUIRED_RUNS_ACCEPTED`, and `DELIVERY_READY`. The direct state fields are exactly `proposal`, `initialization`, `calabash_draft`, `workflow`, `ui`, `simulation`, `mandatory_calabash_upgrade`, `product_baseline`, `all_required_runs_accepted`, `centralized_security_audit`, `security_remediation`, `vulnerability_closure`, `post_security_owner_acceptance`, `delivery_method_qa`, and `delivery`; each must normalize under section 6.
- `initialization_mode` is `NEW|EXISTING`; `continuity_decision` is `PENDING|CONTINUE|NARROW_REDIRECT|HOLD|TERMINATE`; `takeover_readiness` is `NOT_APPLICABLE|READY|BLOCKED|NOT_CONTINUING`; `existing_project_attestation` is `PENDING|NOT_APPLICABLE|CLAIMED_UNATTESTED|EVIDENCED`; and `existing_project_classification` is `PENDING|NOT_APPLICABLE|ATTESTED_COMPLETE|NEEDS_GAP_CLOSURE|PARTIAL|DIRECTION_CHANGED|NOT_CONTINUING`. `updated_at` is empty or RFC 3339. `last_material_change` and `next_action` are at most `4,096` UTF-8 bytes with no control, surrogate, or bidirectional-control character; they are validated but never projected.
- `SafeRef` is at most `256` ASCII characters and matches `^[A-Za-z0-9][A-Za-z0-9._-]{0,63}(?:/[A-Za-z0-9][A-Za-z0-9._-]{0,63}){0,15}$`. `active_slice` and `integration_baseline` are `null`, one `SafeRef`, or an exact non-empty `{id?: SafeRef, path?: SafeRef}` object. `active_runs`, `loop_owner_acceptances`, and `evidence_pointers` are arrays of `SafeRef`. `open_owner_gaps` is an array of exact `{gap_id: SafeRef, state: "OPEN"|"IN_CLOSURE", source_acceptance: SafeRef, evidence_pointers: non-empty SafeRef[]}` index objects with unique `gap_id`. `blockers` is an array of at most `2,048` non-control strings, each at most `256` UTF-8 bytes. None is serialized.
- The Canonical Manifest file is optional. Once present it has exactly `lccoding`, `calabash`, `slk`, `clk`, `glk`, `compatibility`, and `load_order`. Each method object has exactly string fields `version` and `hash`; version is empty or `SafeVersion`, and hash is empty or 64 hex characters with optional `sha256:` prefix. `compatibility` matches `^[A-Z][A-Z0-9_]{0,63}$`. `load_order` is an array of at most `2,048` strings, each `1..64` UTF-8 bytes with no control, surrogate, or bidirectional-control character. Missing, extra, or wrong-typed fields fail closed.
- `SafeVersion` matches `^[A-Za-z0-9][A-Za-z0-9._+-]{0,31}$`.
- `canonical_candidate` has exactly string keys `repository`, `version`, and `commit`. All three exact empty strings mean not locked. Otherwise repository matches `^[A-Za-z0-9][A-Za-z0-9._~:/@+-]{0,255}$`, version is `SafeVersion`, and commit is exactly 40 or 64 hexadecimal characters. Partial, whitespace-only, or malformed identity fails closed. Only a full valid identity may project `LOCKED`; `RECORDED` additionally requires initialization to normalize complete. Repository and commit never serialize.
- A project display name is `1..80` Unicode scalar values, begins and ends with an alphanumeric character, and otherwise contains only Unicode alphanumerics plus ASCII space, `-`, `_`, `.`, `(`, `)`, `[`, `]`, or em dash `—`. Any separator/path form, drive/UNC/POSIX-home form, URI or Git remote syntax, control/format/surrogate/bidirectional-control character, or leading/trailing whitespace fails closed. A valid English or Chinese name is serialized unchanged.

All input failures produce a visibly red, path-free error Snapshot. A malformed refresh never leaves an old green state presented as current truth.

## 5. Adapter truthful status projection

State strings are exact uppercase values; do not trim or case-fold them. Normalize only with this closed table:

```text
done:
  ACCEPTED, ALL_REQUIRED_RUNS_ACCEPTED, CLOSED, COMPLETE, COMPLETED,
  DELIVERED, DELIVERY_READY, DONE, ESTABLISHED, EVIDENCED, INITIALIZED,
  INVENTORIED, LOCKED, LOOP_OWNER_ACCEPTED, PASS, PASSED,
  POST_SECURITY_OWNER_ACCEPTED, READY, RECONSTRUCTED, VERIFIED,
  VULNERABILITY_CLOSED

active:
  ACTIVE, EXECUTING, EXISTING_INTAKE_PENDING, IN_PROGRESS, RUNNING

pending:
  PENDING

error:
  BLOCKED, ERROR, FAIL, FAILED, INVALID, NOT_CONTINUING, REJECTED
```

`NOT_APPLICABLE` is valid only in the non-displayed intake/classification fields whose field contract permits it. No displayed lifecycle step or phase gate accepts it; a displayed required step using it fails closed. This preserves the mandatory mainline and gives every displayed row one of the four approved states.

The exact phase/step tuple and source precedence are:

| Phase | `StepId` | Authoritative source and exact rule |
|---|---|---|
| `INITIAL` | `PROPOSAL_READINESS` | direct normalization of `status.proposal` |
| `INITIAL` | `PROJECT_INITIALIZATION` | direct normalization of `status.initialization` |
| `INITIAL` | `INITIAL_READY` | direct normalization of `status.phase_gates.INITIAL_READY` |
| `PRODUCT_FORMATION` | `CALABASH_DRAFT` | direct normalization of `status.calabash_draft` |
| `PRODUCT_FORMATION` | `SIMULATION_WORLD_FOUNDATION` | direct normalization of `status.simulation` |
| `PRODUCT_FORMATION` | `WORKFLOW_CAPABILITY_END` | direct normalization of `status.workflow` |
| `PRODUCT_FORMATION` | `UI_PRODUCT_SURFACE_END` | direct normalization of `status.ui` |
| `PRODUCT_FORMATION` | `CALABASH_UPGRADE_READY` | direct normalization of `status.phase_gates.CALABASH_UPGRADE_READY` |
| `ENGINEERING_RUNS` | `MANDATORY_CALABASH_UPGRADE` | direct normalization of `status.mandatory_calabash_upgrade` |
| `ENGINEERING_RUNS` | `PRODUCT_BASELINE` | direct normalization of `status.product_baseline` |
| `ENGINEERING_RUNS` | `FEATURE_SLICE_EXECUTION_COVERAGE` | if aggregate is done: done; else if `active_slice` is non-null: active; else if Integration, active Run, or acceptance receipt provides a downstream fact: done; else pending |
| `ENGINEERING_RUNS` | `UI_LOCKED_INTEGRATION_BASELINE` | valid non-null `integration_baseline`: the baseline is established/done; null: pending. This row does not claim Feature Integration implementation is complete. |
| `ENGINEERING_RUNS` | `LOOP_RUN_D0_D3` | compatibility ID displayed as Real Product Integration proof; done aggregate: done; error aggregate: error; else non-empty Phase-3 integration `active_runs`: active; else applicable integration acceptance receipt exists: done; else pending. Cross-phase method activity outside Product Integration does not activate this row. |
| `ENGINEERING_RUNS` | `LOOP_OWNER_ACCEPTANCE` | done aggregate + receipt(s): done; error aggregate: error; receipt(s) before done aggregate: active; no receipt: pending; done aggregate without receipt is a contradiction |
| `ENGINEERING_RUNS` | `ALL_REQUIRED_RUNS_ACCEPTED` | direct normalization of top-level `status.all_required_runs_accepted`, which must equal the same-named phase gate after normalization |
| `DELIVERY_PREPARATION` | `CENTRALIZED_VULNERABILITY_AUDIT` | direct normalization of `status.centralized_security_audit` |
| `DELIVERY_PREPARATION` | `SECURITY_REMEDIATION` | direct normalization of `status.security_remediation` |
| `DELIVERY_PREPARATION` | `SECURITY_REAUDIT_VULNERABILITY_CLOSURE` | one combined row, direct normalization of `status.vulnerability_closure` |
| `DELIVERY_PREPARATION` | `POST_SECURITY_OWNER_ACCEPTANCE` | direct normalization of `status.post_security_owner_acceptance` |
| `DELIVERY_PREPARATION` | `DELIVERY_METHOD_QA` | direct normalization of `status.delivery_method_qa` |
| `DELIVERY_PREPARATION` | `DELIVERY_PACKAGE_GUARD_READY` | one combined row sourced from `status.phase_gates.DELIVERY_READY`; done means package governance issued the existing exit gate, not that post-gate Delivery occurred |

The four combined rows are the only permitted consolidation. `active_slice` never independently lights Feature Slice and Preflight; Phase-3 integration `active_runs` never independently lights integration work and D0–D3; `vulnerability_closure` never creates separate Re-audit and Closure facts; and `DELIVERY_READY` is not duplicated into an invented Package Guard fact. No display ID is a new lifecycle node, gate, or authoritative field. The existing `FEATURE_SLICE_EXECUTION_COVERAGE_PASS` entry Gate and per-Run `LOOP_OWNER_ACCEPTANCE_READY` Gate remain wholly governed by their existing LCCoding contracts. The BI does not read, evaluate, issue, or replace either Gate's `PASS`/`READY`; a combined row shown as done is display-only progress, never Gate evidence or a verdict.

Apply validation and projection in this order:

1. Validate both record schemas, every direct state, Candidate, and reference value. Any failure returns the error Snapshot.
2. Normalize direct states and derive the four grouped states by the table above.
3. Require every historical phase exit gate and every historical step, including grouped steps, to be done.
4. Require every future phase exit gate and every future step to be pending.
5. For the current non-final phase, a done exit gate is a stale-phase contradiction; a pending/active exit gate makes the phase active, and an error exit gate makes the phase error. A valid current child error remains a red child row while the phase stays active unless the exit gate itself is error.
6. Require `phase_gates.ALL_REQUIRED_RUNS_ACCEPTED` and top-level `all_required_runs_accepted` to have the same normalized state. A done aggregate also requires at least one acceptance receipt, no `active_runs`, and no `open_owner_gaps`.
7. `status.delivery` is a post-`DELIVERY_READY` Delivery fact and is never used as the Package Guard source. Before `DELIVERY_READY` it must be pending; after the gate it may truthfully describe subsequent Delivery but does not change the four-phase projection.
8. For current `DELIVERY_PREPARATION`, a done `DELIVERY_READY` plus every preceding delivery-preparation step done makes the combined Package Guard/Ready row and final phase done. A done gate with any incomplete preceding step is contradictory. Pending/active makes the phase active; error makes it error.
9. Any history/future/stale/aggregate contradiction returns the complete error Snapshot. A valid operational error is project truth, not record corruption: it renders red but does not alone change `health` from `ok`.

This precedence ensures Delivery never retains a normal-looking active engineering step after a valid done aggregate. It reports the Integration Baseline as established without claiming the later Integration work itself is complete.

## 6. Tauri security boundary

- Bundle only the Vite-built local frontend. `tauri.conf.json` defines one `main` window with `create=false`, `width=300`, `height=480`, `resizable=false`, `maximizable=false`, `decorations=true`, `dragDropEnabled=false`, `devtools=false` for production, and no second window. Rust creates it in `setup` with `WebviewWindowBuilder::from_config` so the security handlers below are unavoidable.
- The builder's `on_navigation` permits only the packaged `WebviewUrl::App` origin; development permits only the exact scheme, host, and port in the configured Vite `devUrl`, never a wildcard localhost rule. `on_download` returns false for every requested download and never supplies a destination. `on_new_window` always returns `Deny`. Tests attempt `location` navigation, an external anchor, `<a download>`, and `window.open` and prove that no navigation, file, or new window results.
- Configure this CSP baseline: `default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; font-src 'self'; connect-src ipc: http://ipc.localhost; object-src 'none'; base-uri 'none'; frame-src 'none'; form-action 'none'`. Keep Tauri CSP modification enabled. Verification parses the effective CSP after Tauri build processing: every baseline directive and source must remain, and only Tauri-generated hash/nonce tokens may be added to `script-src` or `style-src`; reject wildcards, `'unsafe-inline'`, `'unsafe-eval'`, any other source, or a weakened directive.
- `build.rs`, `capabilities/main.json`, the final resolved ACL, and the Rust handler expose exactly five commands: `bind_project`, `choose_project`, async no-argument `get_snapshot`, `set_pinned`, and `is_pinned`. `tauri.conf.json` sets `app.security.capabilities` to exactly `["main"]`; `capabilities/` contains only `main.json`; and no default/plugin capability is enabled. Tests compare all surfaces and reject any extra command or capability.
- `bind_project(project_root)` accepts a path only while the unbound binding view is active; `choose_project()` obtains its path only from the Rust-owned native picker. Both call the same canonicalization/boundary validation and may set the immutable root exactly once. After binding, no command can select or replace a path.
- `get_snapshot()` accepts no argument, acquires the Rust single-flight guard, and runs fixed-handle read/parse/projection in `spawn_blocking`. `set_pinned(enabled)` returns the confirmed native topmost state; `is_pinned()` reads that state.
- Do not expose a URL, command string, report identifier, file identifier, raw record, or arbitrary object. Report selection stays in the fixed frontend catalog.
- Keep `withGlobalTauri=false`, `assetProtocol.enable=false`, prototype freezing enabled, browser extensions disabled, inline event handlers absent, and project-derived rendering on `textContent`/created text nodes only. Project values never enter `innerHTML`, style, attribute URLs, or executable contexts.
- Do not enable filesystem, shell, opener, dialog, HTTP, updater, clipboard, process, notification, global-shortcut, generic path, or drag/drop plugins/capabilities. The `plugins` object is empty; `createUpdaterArtifacts=false`; no updater endpoint, updater plugin, or updater artifact exists.
- Windows uses the Tauri NSIS `embedBootstrapper` WebView2 mode. The current-user installer may bootstrap WebView2 but silently installs no unrelated runtime; runtime probing still fails path-free when WebView2 remains unavailable. LCCoding defines no independent WebView2 version line.
- `productName` and Start Menu display are `LCCoding BI`, the installed executable is exactly `lccoding-bi.exe`, and bundle identifier is `com.lccoding.desktop`. The BI remains part of the overall LCCoding release, not an independent product version. `package.json` is `private:true`, Cargo is `publish=false`, production source maps are disabled, and Rust release debug data is stripped/remapped.
- On startup, render Pin disabled with catalog text `app.pin_checking` and no `aria-pressed`, then query `is_pinned()`. Success enables the button and paints localized On/Off text plus the confirmed `aria-pressed`. Initial failure keeps it disabled, paints `app.pin_unavailable`, and announces `app.pin_error`; it never defaults to Off. After a confirmed state exists, every click uses only the actual boolean returned after set-and-read; failure restores the last confirmed On/Off state and announces `app.pin_error`. Internal code `BI_PIN_UNAVAILABLE` is diagnostic only.

The native titlebar owns close/minimize behavior. No frontend permission is granted merely to duplicate native window controls.

## 7. Refresh and local view state

- After binding, load one real sanitized Snapshot. Schedule the next request two seconds after settlement; never use overlapping interval requests. The React controller and Rust command each enforce joinable single-flight, so manual and timed refreshes cannot queue duplicate reads.
- A failed refresh immediately replaces status content with the red error projection while preserving no apparently current green claim. The scheduler continues, so a later valid record can recover the view.
- If a report is open when input fails, replace it with the protected error body. Do not retain stale report values under an error banner.
- Open, Back, language, phase fold, scroll, Pin, refresh, and close never write or touch project records. Refresh may read only the fixed Rust-held root.
- Main-view fold and scroll positions survive Open/Back and language switching when the current Snapshot remains valid.
- Use native `<button type="button">` controls. Phase toggles expose `aria-expanded` and `aria-controls`; the four phases use an ordered-list landmark; the active phase uses `aria-current="step"`; decorative spinner glyphs are `aria-hidden`; the adjacent state text remains readable by assistive technology.
- Main-view keyboard order is language, Pin, then phase toggles and their visible Open buttons from top to bottom, then Refresh. Report-view order is language, Pin, Back, then Refresh. Opening a report moves focus to Back; Back restores focus to the originating Open button. Folding never traps or discards focus.
- Successful refresh text uses `role="status" aria-live="polite"`; the input failure uses `role="alert"`. Language and Pin controls expose their current value in accessible name/state as well as visible text. No focus outline is clipped by the fixed client boundary.

## 8. Verification and visual acceptance

The acceptance boundary covers the exact DTO, four-phase/21-step order, all eight report joins, bilingual and keyboard behavior, `300 × 480` visual contract, protected navigation, fail-closed error/recovery, packaging safety, and project-byte immutability. Owner visual acceptance remains required for visual-contract change. Detailed commands and harness locations remain implementation navigation, not product authority; see the [BI subtree README](../bi/README.md).

## 9. Non-goals

- multi-project dashboard or portfolio view;
- original file/evidence/source/private-repository opener, arbitrary browser, download, or any post-binding/arbitrary path selector;
- project status editing, UI editing, Agent/session/runtime/tool control, or lower-method execution logic;
- a second frontend/runtime, Vue, Svelte, Electron, Python GUI/runtime, remote frontend, database, cache, packaged server, or background service;
- generic filesystem/shell/network/plugin access;
- new canonical phase, gate, status field, authoritative record, BI-only schema authority, or altered CORE/EXTRA, Simulation-first, logical-subtree UI baseline, Feature Slice, or Loop responsibility;
- an independent repository, version, tag, release, installer identity, or product line.

Vite's local development server is a build/test tool only and is not included in the packaged application.
