import { message, type Language } from "../i18n/catalog";
import type { PhaseId, ReportId, Snapshot } from "../model/snapshot";
import { StateMark } from "./StateMark";

export function DashboardView({
  snapshot,
  language,
  expanded,
  onTogglePhase,
  onOpenReport,
}: Readonly<{
  snapshot: Readonly<Snapshot>;
  language: Language;
  expanded: ReadonlySet<PhaseId>;
  onTogglePhase(phase: PhaseId): void;
  onOpenReport(report: ReportId): void;
}>) {
  if (snapshot.health === "error") {
    return (
      <div className="error-projection" role="alert">
        <div className="project-name">{message("app.unnamed_project", language)}</div>
        <StateMark state="error" language={language} />
        <div className="error-message">{message("app.error", language)}</div>
      </div>
    );
  }

  return (
    <>
      <div className="project-name">{snapshot.project}</div>
      <div className="read-only-label">{message("app.read_only", language)}</div>
      <ol className="phase-list">
        {snapshot.phases.map((phase) => {
          const isExpanded = expanded.has(phase.id);
          const panelId = `phase-panel-${phase.id}`;
          return (
            <li className="phase-view" data-phase-id={phase.id} key={phase.id}>
              <button
                className="phase-summary"
                type="button"
                aria-expanded={isExpanded}
                aria-controls={panelId}
                aria-current={snapshot.current_phase === phase.id ? "step" : undefined}
                onClick={() => onTogglePhase(phase.id)}
              >
                <span className="phase-label">{message(`phase.${phase.id}`, language)}</span>
                <StateMark state={phase.state} language={language} />
              </button>
              <div className="phase-panel" id={panelId} hidden={!isExpanded}>
                <ol className="step-list">
                  {phase.steps.map((step) => (
                    <li className="step-row" data-step-id={step.id} key={step.id}>
                      <span className="step-label">{message(`step.${step.id}`, language)}</span>
                      <StateMark state={step.state} language={language} />
                      {step.report === null ? null : (
                        <button
                          type="button"
                          className="open-report"
                          onClick={() => onOpenReport(step.report as ReportId)}
                        >
                          {message("app.open", language)}
                        </button>
                      )}
                    </li>
                  ))}
                </ol>
              </div>
            </li>
          );
        })}
      </ol>
    </>
  );
}
