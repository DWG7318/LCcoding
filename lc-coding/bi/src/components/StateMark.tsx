import { message, type Language, type MessageKey } from "../i18n/catalog";
import type { ViewState } from "../model/snapshot";

const STATE_KEYS = {
  done: "state.done",
  active: "state.active",
  pending: "state.pending",
  error: "state.error",
} as const satisfies Readonly<Record<ViewState, MessageKey>>;

export function StateMark({ state, language }: Readonly<{ state: ViewState; language: Language }>) {
  return (
    <span className={`state state--${state}`}>
      <span className="state-glyph" aria-hidden="true" />
      <span className="state-text">{message(STATE_KEYS[state], language)}</span>
    </span>
  );
}
