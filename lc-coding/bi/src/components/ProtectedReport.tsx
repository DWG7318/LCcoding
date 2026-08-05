import { message, type Language, type MessageKey } from "../i18n/catalog";
import type { MetricStatus, ReportRow, ReportView, ViewState } from "../model/snapshot";
import { StateMark } from "./StateMark";

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

function RowValue({ row, language }: Readonly<{ row: ReportRow; language: Language }>) {
  const value = row.value;
  if (value.kind === "view_state") return <StateMark state={value.value} language={language} />;
  if (value.kind === "metric") {
    const details = [
      value.completed === null
        ? null
        : value.total === null
          ? String(value.completed)
          : `${value.completed}/${value.total}`,
      value.interval_minutes === null
        ? null
        : language === "zh_CN"
          ? `${value.interval_minutes} 分钟`
          : `${value.interval_minutes} min`,
    ].filter((part): part is string => part !== null);
    return (
      <>
        <span className={`state state--${METRIC_STATES[value.status]}`}>
          <span className="state-glyph" aria-hidden="true" />
          <span className="state-text">{message(METRIC_KEYS[value.status], language)}</span>
        </span>
        {details.length === 0 ? null : <span className="metric-detail">{details.join(" · ")}</span>}
      </>
    );
  }
  if (value.kind === "phase") {
    return (
      <span className="row-value">
        {value.value === "UNKNOWN"
          ? message("value.unknown", language)
          : message(`phase.${value.value}`, language)}
      </span>
    );
  }
  return <span className="row-value">{message(VALUE_KEYS[value.value], language)}</span>;
}

export function ProtectedReport({
  report,
  language,
  onBack,
}: Readonly<{ report: Readonly<ReportView>; language: Language; onBack(): void }>) {
  return (
    <section className="report-surface">
      <button className="back-button" type="button" onClick={onBack}>
        {message("app.back", language)}
      </button>
      <h1 className="report-heading">{message(`report.${report.id}`, language)}</h1>
      <div className="report-version">
        {report.version ?? message("value.not_recorded", language)}
      </div>
      <p className="protected-notice">{message("app.protected", language)}</p>
      <div className="report-rows">
        {report.rows.map((row) => (
          <div className="report-row" data-row-key={row.key} key={row.key}>
            <span className="row-label">{message(row.key, language)}</span>
            <RowValue row={row} language={language} />
          </div>
        ))}
      </div>
    </section>
  );
}
