/// <reference types="vite/client" />

import "./setup";

import { describe, expect, it } from "vitest";

import { CATALOG, DEFAULT_LANGUAGE, message } from "../../src/i18n/catalog";

const nodeFs = ["node", "fs"].join(":");
const { readFileSync } = await import(/* @vite-ignore */ nodeFs);
const runtimeProcess = (
  globalThis as typeof globalThis & { process: { cwd: () => string } }
).process;

function readCss(relativeUrl: string): string {
  const url = new URL(relativeUrl, import.meta.url);
  if (url.protocol === "file:") return readFileSync(url, "utf8") as string;

  const pathname = decodeURIComponent(url.pathname);
  const windowsPath = pathname.match(/^\/([A-Za-z]:\/.*)$/u)?.[1];
  const cwd = runtimeProcess.cwd().replaceAll("\\", "/");
  const filename = windowsPath ?? (pathname.startsWith(`${cwd}/`) ? pathname : `${cwd}${pathname}`);
  return readFileSync(filename, "utf8") as string;
}

const appCss = readCss("../../src/styles/app.css");
const tokensCss = readCss("../../src/styles/tokens.css");

const EXPECTED_CATALOG = {
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
} as const;

describe("closed bilingual catalog", () => {
  it("has the exact 98-key catalog with four phases and 21 steps", () => {
    expect(CATALOG).toEqual(EXPECTED_CATALOG);
    expect(Object.keys(CATALOG)).toHaveLength(98);
    expect(Object.keys(CATALOG).filter((key) => key.startsWith("phase."))).toHaveLength(4);
    expect(Object.keys(CATALOG).filter((key) => key.startsWith("step."))).toHaveLength(21);
  });

  it("keeps identical complete language sets and never falls back in Chinese", () => {
    expect(DEFAULT_LANGUAGE).toBe("en");
    for (const key of Object.keys(EXPECTED_CATALOG) as (keyof typeof EXPECTED_CATALOG)[]) {
      expect(Object.keys(CATALOG[key])).toEqual(["en", "zh_CN"]);
      expect(message(key, "en")).toBe(EXPECTED_CATALOG[key].en);
      expect(message(key, "zh_CN")).toBe(EXPECTED_CATALOG[key].zh_CN);
      expect(message(key, "zh_CN")).not.toBe("");
    }
  });

  it("preserves representative app, value, report, and row strings exactly", () => {
    expect(message("app.protected", "zh_CN")).toBe(
      "只读安全报告；不访问工程文件、源码、私有仓库、证据正文、网址或本地路径",
    );
    expect(message("value.not_recorded", "en")).toBe("Not recorded");
    expect(message("report.candidate", "zh_CN")).toBe("权威候选");
    expect(message("row.current_phase", "en")).toBe("Current phase");
  });
});

function block(css: string, selector: string): string {
  const flatCss = css.replace(/\s+/gu, " ");
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&");
  const match = flatCss.match(new RegExp(`${escaped}\\s*\\{([^}]*)\\}`, "u"));
  expect(match, `missing CSS rule: ${selector}`).not.toBeNull();
  return match?.[1]?.trim() ?? "";
}

function declaration(cssBlock: string, property: string): string {
  const escaped = property.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&");
  const match = cssBlock.match(new RegExp(`(?:^|;)\\s*${escaped}\\s*:\\s*([^;]+)`, "u"));
  expect(match, `missing CSS declaration: ${property}`).not.toBeNull();
  return match?.[1]?.trim() ?? "";
}

function mediaBody(css: string, query: string): string {
  const start = css.indexOf(`@media ${query}`);
  expect(start, `missing media query: ${query}`).toBeGreaterThanOrEqual(0);
  const open = css.indexOf("{", start);
  let depth = 0;
  for (let index = open; index < css.length; index += 1) {
    if (css[index] === "{") depth += 1;
    if (css[index] === "}") depth -= 1;
    if (depth === 0) return css.slice(open + 1, index);
  }
  throw new Error(`unterminated media query: ${query}`);
}

function luminance(hex: string): number {
  const channels = hex
    .slice(1)
    .match(/.{2}/gu)!
    .map((pair) => Number.parseInt(pair, 16) / 255)
    .map((channel) =>
      channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4,
    );
  return 0.2126 * channels[0]! + 0.7152 * channels[1]! + 0.0722 * channels[2]!;
}

function contrast(foreground: string, background: string): number {
  const first = luminance(foreground);
  const second = luminance(background);
  return (Math.max(first, second) + 0.05) / (Math.min(first, second) + 0.05);
}

describe("approved visual tokens", () => {
  it("defines every fixed neutral, control, state, and spacing token exactly", () => {
    const root = block(tokensCss, ":root");
    const expected = {
      "--surface": "#ffffff",
      "--chrome": "#f3f4f6",
      "--soft": "#f6f7f9",
      "--ink": "#20242b",
      "--muted": "#667085",
      "--separator": "#d9dde3",
      "--control-border": "#838a94",
      "--control-hover-border": "#4b5563",
      "--control-pressed": "#e5e7eb",
      "--focus": "#2563eb",
      "--error-surface": "#fff4f4",
      "--protected-surface": "#edf2ff",
      "--protected-ink": "#30456f",
      "--state-complete": "#198754",
      "--state-error": "#c92a2a",
      "--state-active": "#2563eb",
      "--state-pending": "#6b7280",
      "--space-1": "4px",
      "--space-2": "6px",
      "--space-3": "8px",
      "--space-4": "12px",
      "--separator-width": "1px",
      "--radius": "6px",
    } as const;
    for (const [property, value] of Object.entries(expected)) {
      expect(declaration(root, property)).toBe(value);
    }
  });

  it("keeps all four product states at 4.5:1 or better on opaque white", () => {
    const root = block(tokensCss, ":root");
    for (const [property, value] of [
      ["--state-complete", "#198754"],
      ["--state-error", "#c92a2a"],
      ["--state-active", "#2563eb"],
      ["--state-pending", "#6b7280"],
    ] as const) {
      expect(declaration(root, property)).toBe(value);
      expect(contrast(value, "#ffffff"), property).toBeGreaterThanOrEqual(4.5);
    }
    expect(tokensCss).not.toMatch(/(?:rgba?|hsla?)\s*\(/iu);
  });
});

describe("fixed compact utility layout", () => {
  it("fixes the 300 by 480 client and scrolls only the middle grid row", () => {
    const css = appCss;
    const client = block(css, "html, body, #app");
    expect(declaration(client, "width")).toBe("300px");
    expect(declaration(client, "height")).toBe("480px");
    expect(declaration(client, "overflow")).toBe("hidden");

    const shell = block(css, ".app-shell");
    expect(declaration(shell, "display")).toBe("grid");
    expect(declaration(shell, "grid-template-rows")).toBe("34px minmax(0, 1fr) 32px");
    expect(declaration(shell, "width")).toBe("300px");
    expect(declaration(shell, "height")).toBe("480px");
    expect(declaration(shell, "overflow")).toBe("hidden");

    const body = block(css, ".app-body");
    expect(declaration(body, "min-height")).toBe("0");
    expect(declaration(body, "overflow-y")).toBe("auto");
    expect(declaration(body, "padding")).toBe("8px");
    expect(css).not.toMatch(/scrollbar(?:-color|-width)?|::-webkit-scrollbar/iu);
  });

  it("uses the exact compact typography and minimum interactive row sizes", () => {
    const css = appCss;
    const body = block(css, "body");
    expect(declaration(body, "font-family")).toBe(
      '"Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif',
    );
    expect(declaration(body, "font-size")).toBe("14px");
    expect(declaration(body, "line-height")).toBe("1.4");
    expect(declaration(block(css, ".report-heading"), "font-size")).toBe("15px");
    expect(declaration(block(css, ".phase-summary"), "min-height")).toBe("36px");
    expect(declaration(block(css, ".step-row"), "min-height")).toBe("34px");
    expect(declaration(block(css, ".report-row"), "min-height")).toBe("34px");
    const button = block(css, "button");
    expect(declaration(button, "min-height")).toBe("28px");
    expect(declaration(button, "padding")).toBe("0 8px");

    const pixelSizes = [...css.matchAll(/font-size\s*:\s*(\d+(?:\.\d+)?)px/giu)].map(
      (match) => Number(match[1]),
    );
    expect(pixelSizes.length).toBeGreaterThan(0);
    expect(Math.min(...pixelSizes)).toBeGreaterThanOrEqual(12);
  });

  it("keeps the exact persistent keyboard focus treatment inside the client", () => {
    const css = appCss;
    const focusMatch = css
      .replace(/\s+/gu, " ")
      .match(/[^{}]*:focus-visible[^{}]*\{([^}]*)\}/u);
    expect(focusMatch).not.toBeNull();
    expect(declaration(focusMatch?.[1] ?? "", "outline")).toBe("2px solid #2563eb");
    expect(declaration(focusMatch?.[1] ?? "", "outline-offset")).toBe("2px");
  });
});

describe("state-only accessible motion", () => {
  it("animates only an aria-hidden active glyph beside readable state text", () => {
    const css = appCss;
    const glyph = block(css, '.state--active .state-glyph[aria-hidden="true"]');
    expect(declaration(glyph, "animation")).toBe("state-spinner 800ms linear infinite");
    expect(block(css, '.state--active .state-glyph[aria-hidden="true"] + .state-text')).not.toBe("");
    expect(css).toMatch(/@keyframes\s+state-spinner\s*\{[\s\S]*rotate\(360deg\)/u);
    expect(css.match(/\banimation\s*:/gu)).toHaveLength(2);
  });

  it("replaces spinner motion with an explicit static mark for reduced motion", () => {
    const reduced = mediaBody(appCss, "(prefers-reduced-motion: reduce)");
    const glyph = block(reduced, '.state--active .state-glyph[aria-hidden="true"]');
    expect(declaration(glyph, "animation")).toBe("none");
    const staticMark = block(
      reduced,
      '.state--active .state-glyph[aria-hidden="true"]::before',
    );
    expect(declaration(staticMark, "content")).toBe('"●"');
  });
});

describe("plain PowerShell-like anti-decoration contract", () => {
  it("rejects decorative architecture, effects, scrollbars, side stripes, and fluid type", () => {
    const css = `${tokensCss}\n${appCss}`;
    expect(css).not.toMatch(/(?:repeating-)?(?:linear|radial|conic)-gradient|background-clip\s*:\s*text/iu);
    expect(css).not.toMatch(/backdrop-filter|filter\s*:\s*blur|box-shadow/iu);
    expect(css).not.toMatch(/\.card(?:\b|[-_])|card-grid|dashboard|grid-template-columns/iu);
    expect(css).not.toMatch(/scrollbar(?:-color|-width)?|::-webkit-scrollbar/iu);
    expect(css).not.toMatch(/border-(?:left|right)\s*:\s*(?:[2-9]|\d{2,})px/iu);
    expect(css).not.toMatch(/font-size\s*:[^;]*(?:clamp\(|\b(?:vw|vh|vmin|vmax)\b)/iu);
  });
});
