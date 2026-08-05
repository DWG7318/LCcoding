import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./styles/tokens.css";
import "./styles/app.css";

const host = document.querySelector<HTMLElement>("#app");
if (host === null) {
  throw new Error("BI_ROOT_MISSING");
}

createRoot(host).render(
  <StrictMode>
    <main className="app-shell" aria-label="LCCoding BI" />
  </StrictMode>,
);
