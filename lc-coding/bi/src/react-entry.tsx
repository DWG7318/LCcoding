import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./app/App";
import { desktopPorts } from "./desktop/bridge";
import "./styles/tokens.css";
import "./styles/app.css";

const host = document.querySelector<HTMLElement>("#app");
if (host === null) {
  throw new Error("BI_ROOT_MISSING");
}

createRoot(host).render(
  <StrictMode>
    <App ports={desktopPorts} />
  </StrictMode>,
);
