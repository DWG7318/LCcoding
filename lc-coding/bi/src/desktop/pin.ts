import type { PinPort } from "../state/view-state";

export type TauriInvoke = <T>(
  command: string,
  args?: Record<string, unknown>,
) => Promise<T>;

const PIN_UNAVAILABLE = "BI_PIN_UNAVAILABLE";

function confirmedBoolean(value: unknown): boolean {
  if (typeof value !== "boolean") throw new Error(PIN_UNAVAILABLE);
  return value;
}

export function createTauriPinPort(invoke: TauriInvoke): PinPort {
  const confirmedInvoke = async (
    command: "is_pinned" | "set_pinned",
    args?: Record<string, unknown>,
  ): Promise<boolean> => {
    try {
      return confirmedBoolean(await invoke<unknown>(command, args));
    } catch {
      throw new Error(PIN_UNAVAILABLE);
    }
  };

  return Object.freeze({
    read: (): Promise<boolean> => confirmedInvoke("is_pinned"),
    set: (enabled: boolean): Promise<boolean> =>
      confirmedInvoke("set_pinned", { enabled }),
  });
}

export function selectDesktopPinPort(
  isDesktopRuntime: boolean,
  fallback: PinPort,
  invoke: TauriInvoke,
): PinPort {
  return isDesktopRuntime ? createTauriPinPort(invoke) : fallback;
}
