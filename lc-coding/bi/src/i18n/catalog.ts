export type Language = "en" | "zh_CN";

export const DEFAULT_LANGUAGE = "en" satisfies Language;

type Translation = Readonly<Record<Language, string>>;

export const CATALOG = {
  "app.title": { en: "LCCoding BI", zh_CN: "LCCoding BI" },
  "app.open_project": { en: "Open a project", zh_CN: "打开工程" },
  "app.project_hint": {
    en: "Select one canonical LCCoding project. The BI remains read-only.",
    zh_CN: "选择一个规范的 LCCoding 工程；BI 始终只读。",
  },
  "app.project_root": { en: "Project root", zh_CN: "工程根目录" },
  "app.choose_folder": { en: "Choose folder", zh_CN: "选择文件夹" },
  "app.binding_error": {
    en: "Project unavailable. Choose a canonical LCCoding project.",
    zh_CN: "工程不可用；请选择规范的 LCCoding 工程。",
  },
  "app.read_only": { en: "Read-only project view", zh_CN: "只读工程视图" },
  "app.refresh": { en: "Refresh", zh_CN: "刷新" },
  "app.updated": { en: "Updated now", zh_CN: "刚刚更新" },
  "app.pin_on": { en: "Pin: On", zh_CN: "置顶：开" },
  "app.pin_off": { en: "Pin: Off", zh_CN: "置顶：关" },
  "app.pin_checking": { en: "Pin: Checking", zh_CN: "置顶：检查中" },
  "app.pin_unavailable": { en: "Pin: Unavailable", zh_CN: "置顶：不可用" },
  "app.pin_error": { en: "Pin state unavailable", zh_CN: "无法读取置顶状态" },
  "app.open": { en: "Open", zh_CN: "打开" },
  "app.back": { en: "Back", zh_CN: "返回" },
  "app.language_display": { en: "EN | 中", zh_CN: "EN | 中" },
  "app.language_current_en": {
    en: "Language: English; switch to Chinese",
    zh_CN: "语言：英文；切换到中文",
  },
  "app.language_current_zh": {
    en: "Language: Chinese; switch to English",
    zh_CN: "语言：中文；切换到英文",
  },
  "app.error": { en: "Authoritative status unavailable", zh_CN: "权威状态不可用" },
  "app.unnamed_project": { en: "Unnamed project", zh_CN: "未命名工程" },
  "app.protected": {
    en: "Read-only sanitized report; no project file, source, private repository, evidence body, URL, or local path access",
    zh_CN: "只读安全报告；不访问工程文件、源码、私有仓库、证据正文、网址或本地路径",
  },
  "state.done": { en: "Complete", zh_CN: "已完成" },
  "state.active": { en: "Running", zh_CN: "执行中" },
  "state.pending": { en: "Not reached", zh_CN: "未到达" },
  "state.error": { en: "Error or blocked", zh_CN: "错误或阻塞" },
  "value.locked": { en: "Locked", zh_CN: "已锁定" },
  "value.recorded": { en: "Recorded", zh_CN: "已记录" },
  "value.present": { en: "Present", zh_CN: "存在" },
  "value.not_recorded": { en: "Not recorded", zh_CN: "未记录" },
  "value.pending": { en: "Pending", zh_CN: "待处理" },
  "value.unknown": { en: "Unknown", zh_CN: "未知" },
  "report.proposal": { en: "Proposal Readiness", zh_CN: "提案就绪" },
  "report.candidate": { en: "Canonical Candidate", zh_CN: "权威候选" },
  "report.calabash": { en: "Calabash", zh_CN: "Calabash" },
  "report.simulation": { en: "Simulation World", zh_CN: "Simulation World" },
  "report.workflow": { en: "Workflow", zh_CN: "Workflow" },
  "report.ui": { en: "UI Baseline", zh_CN: "UI 基线" },
  "report.baseline": { en: "Product Baseline", zh_CN: "产品基线" },
  "report.loop_governance": { en: "Loop Governance", zh_CN: "Loop 治理" },
  "row.conclusion": { en: "Conclusion", zh_CN: "结论" },
  "row.initial_gate": { en: "Initial gate", zh_CN: "初始门禁" },
  "row.identity": { en: "Identity", zh_CN: "身份" },
  "row.integrity": { en: "Integrity", zh_CN: "完整性" },
  "row.status": { en: "Status", zh_CN: "状态" },
  "row.version_record": { en: "Version record", zh_CN: "版本记录" },
  "row.current_phase": { en: "Current phase", zh_CN: "当前阶段" },
  "row.realized_peer_subtrees": { en: "Realized peer subtrees", zh_CN: "已实现同级子树" },
  "row.realized_subtrees": { en: "Realized subtrees", zh_CN: "已实现子树" },
  "row.component_version_coverage": { en: "Component version records", zh_CN: "组件版本记录" },
  "row.primary_mainline": { en: "Primary mainline", zh_CN: "产品主线" },
  "row.core_implementation": { en: "CORE implemented", zh_CN: "CORE 已实现" },
  "row.extra_implemented": { en: "EXTRA implemented", zh_CN: "EXTRA 已实现" },
  "row.extra_deferred": { en: "EXTRA deferred", zh_CN: "EXTRA 已延期" },
  "row.api_coverage": { en: "API coverage", zh_CN: "API 覆盖" },
  "row.mcp_coverage": { en: "MCP coverage", zh_CN: "MCP 覆盖" },
  "row.lock_status": { en: "Lock status", zh_CN: "锁定状态" },
  "row.git_identity": { en: "Verified project Git identity", zh_CN: "已验证总项目 Git 身份" },
  "row.locked_subtree_coverage": { en: "Locked subtree coverage", zh_CN: "锁定子树覆盖" },
  "row.map_handoff_consistency": { en: "Map / Handoff consistency", zh_CN: "Map / Handoff 一致性" },
  "row.owner_confirmed_mainline": { en: "Owner-confirmed mainline", zh_CN: "Owner 确认产品主线" },
  "row.worker_checker_wake": { en: "Worker → Checker wake chain", zh_CN: "Worker → Checker 唤醒链" },
  "row.supervisor_wait": { en: "Supervisor wait discipline", zh_CN: "Supervisor 等待纪律" },
  "row.heartbeat": { en: "Temporary Heartbeat", zh_CN: "临时 Heartbeat" },
  "row.no_subagents": { en: "No subagents", zh_CN: "禁止子代理" },
  "row.progress": { en: "Progress receipt", zh_CN: "进度回执" },
  "row.cell_capacity": { en: "CELL capacity", zh_CN: "CELL 容量" },
  "row.pin_policy": { en: "Pin policy", zh_CN: "置顶规则" },
  "metric.compliant": { en: "Compliant", zh_CN: "合规" },
  "metric.active": { en: "Active", zh_CN: "执行中" },
  "metric.violation": { en: "Violation", zh_CN: "违规" },
  "metric.unknown": { en: "Unknown", zh_CN: "未知" },
  "metric.not_recorded": { en: "Not recorded", zh_CN: "未记录" },
  "phase.INITIAL": { en: "INITIAL", zh_CN: "初始" },
  "phase.PRODUCT_FORMATION": { en: "PRODUCT_FORMATION", zh_CN: "产品形成" },
  "phase.ENGINEERING_RUNS": { en: "ENGINEERING_RUNS", zh_CN: "工程运行" },
  "phase.DELIVERY_PREPARATION": { en: "DELIVERY_PREPARATION", zh_CN: "交付准备" },
  "step.PROPOSAL_READINESS": { en: "Proposal Readiness", zh_CN: "提案就绪" },
  "step.PROJECT_INITIALIZATION": { en: "Project Initialization", zh_CN: "工程初始化" },
  "step.INITIAL_READY": { en: "INITIAL_READY", zh_CN: "初始就绪门禁" },
  "step.CALABASH_DRAFT": { en: "Calabash Draft", zh_CN: "Calabash 草案" },
  "step.SIMULATION_WORLD_FOUNDATION": {
    en: "Simulation World foundation",
    zh_CN: "Simulation World 基础",
  },
  "step.WORKFLOW_CAPABILITY_END": {
    en: "Workflow capability end",
    zh_CN: "Workflow 能力端",
  },
  "step.UI_PRODUCT_SURFACE_END": {
    en: "UI product-surface end",
    zh_CN: "UI 产品呈现端",
  },
  "step.CALABASH_UPGRADE_READY": {
    en: "CALABASH_UPGRADE_READY",
    zh_CN: "Calabash 升级就绪门禁",
  },
  "step.MANDATORY_CALABASH_UPGRADE": {
    en: "Mandatory Calabash Upgrade",
    zh_CN: "强制 Calabash 升级",
  },
  "step.PRODUCT_BASELINE": { en: "Product Baseline", zh_CN: "产品基线" },
  "step.FEATURE_SLICE_EXECUTION_COVERAGE": {
    en: "Feature Slice · Execution Coverage Preflight",
    zh_CN: "Feature Slice · 执行覆盖预检",
  },
  "step.UI_LOCKED_INTEGRATION_BASELINE": {
    en: "UI-locked Integration Baseline",
    zh_CN: "UI 锁定集成基线",
  },
  "step.LOOP_RUN_D0_D3": {
    en: "SLK / CLK / GLK Run · D0–D3 Verification",
    zh_CN: "SLK / CLK / GLK Run · D0–D3 验证",
  },
  "step.LOOP_OWNER_ACCEPTANCE": {
    en: "Loop Owner Acceptance",
    zh_CN: "Loop Owner 验收",
  },
  "step.ALL_REQUIRED_RUNS_ACCEPTED": {
    en: "ALL_REQUIRED_RUNS_ACCEPTED",
    zh_CN: "全部必需 Run 已验收",
  },
  "step.CENTRALIZED_VULNERABILITY_AUDIT": {
    en: "Centralized Vulnerability Audit",
    zh_CN: "集中漏洞审计",
  },
  "step.SECURITY_REMEDIATION": { en: "Security Remediation", zh_CN: "安全修复" },
  "step.SECURITY_REAUDIT_VULNERABILITY_CLOSURE": {
    en: "Independent Security Re-audit · Vulnerability Closure",
    zh_CN: "独立安全复审 · 漏洞关闭",
  },
  "step.POST_SECURITY_OWNER_ACCEPTANCE": {
    en: "Post-Security Owner Acceptance",
    zh_CN: "安全后 Owner 验收",
  },
  "step.DELIVERY_METHOD_QA": { en: "Delivery Method Q&A", zh_CN: "交付方法问答" },
  "step.DELIVERY_PACKAGE_GUARD_READY": {
    en: "Delivery Package Guard · DELIVERY_READY",
    zh_CN: "交付包保护 · 交付就绪门禁",
  },
} as const satisfies Record<string, Translation>;

export type MessageKey = keyof typeof CATALOG;

export function message(key: MessageKey, language: Language): string {
  return CATALOG[key][language];
}
