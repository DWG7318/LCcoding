import { invoke } from "@tauri-apps/api/core";

import type { AppPorts, BindResult } from "../app/App";

export const desktopPorts: AppPorts = Object.freeze({
  bindProject: (projectRoot: string): Promise<BindResult> =>
    invoke("bind_project", { projectRoot }),
  chooseProject: (): Promise<BindResult> => invoke("choose_project"),
  getSnapshot: (): Promise<unknown> => invoke("get_snapshot"),
  isPinned: (): Promise<boolean> => invoke("is_pinned"),
  setPinned: (enabled: boolean): Promise<boolean> => invoke("set_pinned", { enabled }),
});
