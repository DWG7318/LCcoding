import { message, type Language, type MessageKey } from "../i18n/catalog";
import type { ReportRow, ReportView, ViewState } from "../model/snapshot";

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
