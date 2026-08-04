import { message, type Language, type MessageKey } from "../i18n/catalog";
import type {
  MetricStatus,
  MetricValue,
  ReportRow,
  ReportView,
  ViewState,
} from "../model/snapshot";

const STATE_KEYS = {
  done: "state.done",
  active: "state.active",
  pending: "state.pending",
  error: "state.error",
} as const satisfies Readonly<Record<ViewState, MessageKey>>;

const VALUE_KEYS = {
  LOCKED: "value.locked",
  RECORDED: "value.recorded",
  PRESENT: "value.present",
  PENDING: "value.pending",
  NOT_RECORDED: "value.not_recorded",
  UNKNOWN: "value.unknown",
} as const satisfies Readonly<Record<string, MessageKey>>;

const METRIC_KEYS = {
  COMPLIANT: "metric.compliant",
  ACTIVE: "metric.active",
  VIOLATION: "metric.violation",
  UNKNOWN: "metric.unknown",
  NOT_RECORDED: "metric.not_recorded",
} as const satisfies Readonly<Record<MetricStatus, MessageKey>>;

const METRIC_STATES = {
  COMPLIANT: "done",
  ACTIVE: "active",
  VIOLATION: "error",
  UNKNOWN: "pending",
  NOT_RECORDED: "pending",
} as const satisfies Readonly<Record<MetricStatus, ViewState>>;

function element<K extends keyof HTMLElementTagNameMap>(
  document: Document,
  tag: K,
  className: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function stateValue(document: Document, state: ViewState, language: Language): HTMLElement {
  const value = element(document, "span", `state state--${state}`);
  const glyph = element(document, "span", "state-glyph");
  glyph.setAttribute("aria-hidden", "true");
  value.append(
    glyph,
    element(document, "span", "state-text", message(STATE_KEYS[state], language)),
  );
  return value;
}

function metricValue(document: Document, value: MetricValue, language: Language): DocumentFragment {
  const rendered = document.createDocumentFragment();
  const state = element(document, "span", `state state--${METRIC_STATES[value.status]}`);
  const glyph = element(document, "span", "state-glyph");
  glyph.setAttribute("aria-hidden", "true");
  state.append(
    glyph,
    element(document, "span", "state-text", message(METRIC_KEYS[value.status], language)),
  );
  rendered.append(state);

  const details: string[] = [];
  if (value.completed !== null) {
    details.push(
      value.total === null ? String(value.completed) : `${value.completed}/${value.total}`,
    );
  }
  if (value.interval_minutes !== null) {
    details.push(
      language === "zh_CN"
        ? `${value.interval_minutes} 分钟`
        : `${value.interval_minutes} min`,
    );
  }
  if (details.length > 0) {
    rendered.append(element(document, "span", "metric-detail", details.join(" · ")));
  }
  return rendered;
}

function ordinaryValue(row: ReportRow, language: Language): string {
  const value = row.value;
  if (value.kind === "phase") {
    return value.value === "UNKNOWN"
      ? message("value.unknown", language)
      : message(`phase.${value.value}`, language);
  }
  if (value.kind === "lock" || value.kind === "record") {
    return message(VALUE_KEYS[value.value], language);
  }
  return "";
}

function reportRow(document: Document, row: ReportRow, language: Language): HTMLElement {
  const rendered = element(document, "div", "report-row");
  rendered.dataset.rowKey = row.key;
  rendered.append(element(document, "span", "row-label", message(row.key, language)));
  rendered.append(
    row.value.kind === "view_state"
      ? stateValue(document, row.value.value, language)
      : row.value.kind === "metric"
        ? metricValue(document, row.value, language)
      : element(document, "span", "row-value", ordinaryValue(row, language)),
  );
  return rendered;
}

export function renderReportView(
  root: HTMLElement,
  report: Readonly<ReportView>,
  language: Language,
  onBack: () => void,
): void {
  const document = root.ownerDocument;
  const back = element(document, "button", "back-button", message("app.back", language));
  back.type = "button";
  back.addEventListener("click", onBack);

  const rows = element(document, "div", "report-rows");
  for (const row of report.rows) rows.append(reportRow(document, row, language));

  root.replaceChildren(
    back,
    element(document, "h1", "report-heading", message(`report.${report.id}`, language)),
    element(
      document,
      "div",
      "report-version",
      report.version ?? message("value.not_recorded", language),
    ),
    element(document, "p", "protected-notice", message("app.protected", language)),
    rows,
  );
}
