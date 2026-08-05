import { useState } from "react";

import { message, type Language } from "../i18n/catalog";

export function BindingView({
  language,
  busy,
  errorCode,
  onBind,
  onChoose,
}: Readonly<{
  language: Language;
  busy: boolean;
  errorCode: string | null;
  onBind(root: string): void;
  onChoose(): void;
}>) {
  const [root, setRoot] = useState("");
  return (
    <section className="binding-view" aria-labelledby="binding-title">
      <h1 id="binding-title" className="report-heading">
        {message("app.open_project", language)}
      </h1>
      <p className="protected-notice">{message("app.project_hint", language)}</p>
      {errorCode === null ? null : (
        <div className="error-projection" role="alert">
          {message("app.binding_error", language)}
        </div>
      )}
      <label className="binding-label">
        {message("app.project_root", language)}
        <input
          className="binding-input"
          value={root}
          disabled={busy}
          onChange={(event) => setRoot(event.currentTarget.value)}
        />
      </label>
      <div className="binding-actions">
        <button type="button" disabled={busy} onClick={onChoose}>
          {message("app.choose_folder", language)}
        </button>
        <button type="button" disabled={busy || root.length === 0} onClick={() => onBind(root)}>
          {message("app.open", language)}
        </button>
      </div>
    </section>
  );
}
