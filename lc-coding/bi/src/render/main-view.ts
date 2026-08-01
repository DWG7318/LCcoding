import { message, type Language, type MessageKey } from "../i18n/catalog";
import type { PhaseId, ReportId, Snapshot, ViewState } from "../model/snapshot";

export interface MainViewCallbacks {
  togglePhase(phase: PhaseId): void;
  openReport(report: ReportId): void;
}

const STATE_KEYS = {
  done: "state.done",
  active: "state.active",
  pending: "state.pending",
  error: "state.error",
} as const satisfies Readonly<Record<ViewState, MessageKey>>;

function element<K extends keyof HTMLElementTagNameMap>(
  document: Document,
  tag: K,
  className?: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className !== undefined) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function stateElement(document: Document, state: ViewState, language: Language): HTMLElement {
  const container = element(document, "span", `state state--${state}`);
  const glyph = element(document, "span", "state-glyph");
  glyph.setAttribute("aria-hidden", "true");
  const text = element(document, "span", "state-text", message(STATE_KEYS[state], language));
  container.append(glyph, text);
  return container;
}

function renderErrorProjection(
  root: HTMLElement,
  snapshot: Readonly<Snapshot>,
  language: Language,
): boolean {
  if (snapshot.health !== "error") return false;

  const document = root.ownerDocument;
  const alert = element(document, "div", "error-projection");
  alert.setAttribute("role", "alert");
  alert.append(
    stateElement(document, "error", language),
    element(document, "div", "error-message", message("app.error", language)),
  );
  root.replaceChildren(alert);
  return true;
}

function phaseElement(
  document: Document,
  snapshot: Readonly<Snapshot>,
  phase: Readonly<Snapshot["phases"][number]>,
  language: Language,
  expanded: ReadonlySet<PhaseId>,
  callbacks: MainViewCallbacks,
): HTMLLIElement {
  const item = element(document, "li", "phase-view");
  item.dataset.phaseId = phase.id;

  const panelId = `phase-panel-${phase.id}`;
  const summaryId = `phase-summary-${phase.id}`;
  const isExpanded = expanded.has(phase.id);
  const summary = element(document, "button", "phase-summary");
  summary.type = "button";
  summary.id = summaryId;
  summary.setAttribute("aria-expanded", String(isExpanded));
  summary.setAttribute("aria-controls", panelId);
  if (snapshot.current_phase === phase.id) summary.setAttribute("aria-current", "step");
  summary.append(
    element(document, "span", "phase-label", message(`phase.${phase.id}`, language)),
    stateElement(document, phase.state, language),
  );
  summary.addEventListener("click", () => callbacks.togglePhase(phase.id));

  const panel = element(document, "div", "phase-panel");
  panel.id = panelId;
  panel.hidden = !isExpanded;
  panel.setAttribute("role", "region");
  panel.setAttribute("aria-labelledby", summaryId);

  const steps = element(document, "ol", "step-list");
  for (const step of phase.steps) {
    const row = element(document, "li", "step-row");
    row.dataset.stepId = step.id;
    row.append(
      element(document, "span", "step-label", message(`step.${step.id}`, language)),
      stateElement(document, step.state, language),
    );

    const report = step.report;
    if (report !== null) {
      const open = element(document, "button", "open-report", message("app.open", language));
      open.type = "button";
      open.addEventListener("click", () => callbacks.openReport(report));
      row.append(open);
    }
    steps.append(row);
  }
  panel.append(steps);
  item.append(summary, panel);
  return item;
}

export function renderMainView(
  root: HTMLElement,
  snapshot: Readonly<Snapshot>,
  language: Language,
  expanded: ReadonlySet<PhaseId>,
  callbacks: MainViewCallbacks,
): void {
  if (renderErrorProjection(root, snapshot, language)) return;

  const document = root.ownerDocument;
  const project = element(document, "div", "project-name", snapshot.project);
  const readOnly = element(
    document,
    "div",
    "read-only-label",
    message("app.read_only", language),
  );
  const phases = element(document, "ol", "phase-list");
  for (const phase of snapshot.phases) {
    phases.append(phaseElement(document, snapshot, phase, language, expanded, callbacks));
  }
  root.replaceChildren(project, readOnly, phases);
}
