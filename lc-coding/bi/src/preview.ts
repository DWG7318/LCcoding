import "./styles/tokens.css";
import "./styles/app.css";

import { mountBi } from "./main";
import { parseSnapshot, type Snapshot } from "./model/snapshot";
import type { PinPort, SnapshotSource } from "./state/view-state";
import errorFixture from "../tests/fixtures/snapshot-error.json";
import successFixture from "../tests/fixtures/snapshot-ok.json";

export type PreviewCase = "ok" | "error" | "max-en" | "max-zh";

const SNAPSHOTS: Readonly<Record<PreviewCase, Readonly<Snapshot>>> = Object.freeze({
  ok: parseSnapshot(successFixture),
  error: parseSnapshot(errorFixture),
  "max-en": parseSnapshot({ ...successFixture, project: "A".repeat(80) }),
  "max-zh": parseSnapshot({ ...successFixture, project: "工程".repeat(40) }),
});

export function resolvePreviewCase(value: string | null): PreviewCase {
  switch (value) {
    case "ok":
    case "error":
    case "max-en":
    case "max-zh":
      return value;
    default:
      return "error";
  }
}

function createMemoryPin(): PinPort {
  let enabled = false;
  return Object.freeze({
    read: async (): Promise<boolean> => enabled,
    set: async (requested: boolean): Promise<boolean> => {
      enabled = requested;
      return enabled;
    },
  });
}

export function createPreviewDependencies(
  previewCase: PreviewCase,
): Readonly<{ source: SnapshotSource; pin: PinPort }> {
  const snapshot = SNAPSHOTS[previewCase];
  const source: SnapshotSource = Object.freeze({
    read: async (): Promise<Readonly<Snapshot>> => snapshot,
  });
  return Object.freeze({ source, pin: createMemoryPin() });
}

const previewRoot = document.querySelector<HTMLElement>("#app");
if (previewRoot !== null) {
  const previewCase = resolvePreviewCase(
    new URLSearchParams(window.location.search).get("case"),
  );
  mountBi(previewRoot, createPreviewDependencies(previewCase));
}
