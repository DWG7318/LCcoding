import "./setup";

import { describe, expect, it } from "vitest";

import {
  createTauriPinPort,
  selectDesktopPinPort,
  type TauriInvoke,
} from "../../src/desktop/pin";
import type { PinPort } from "../../src/state/view-state";

describe("Tauri desktop Pin adapter", () => {
  it("uses only the two Pin commands and returns confirmed host booleans", async () => {
    const calls: Array<
      readonly [string, Record<string, unknown> | undefined]
    > = [];
    const invoke: TauriInvoke = async <T>(
      command: string,
      args?: Record<string, unknown>,
    ): Promise<T> => {
      calls.push([command, args]);
      return (command === "is_pinned" ? true : false) as T;
    };
    const pin = createTauriPinPort(invoke);

    expect(Object.isFrozen(pin)).toBe(true);
    expect(await pin.read()).toBe(true);
    expect(await pin.set(true)).toBe(false);
    expect(calls).toEqual([
      ["is_pinned", undefined],
      ["set_pinned", { enabled: true }],
    ]);
  });

  it("maps rejected and non-boolean replies to one path-free diagnostic", async () => {
    const rejected = createTauriPinPort(async () => {
      throw new Error("private native window detail");
    });
    const malformed = createTauriPinPort(
      async <T>(): Promise<T> => "false" as T,
    );

    await expect(rejected.read()).rejects.toThrowError("BI_PIN_UNAVAILABLE");
    await expect(rejected.set(false)).rejects.toThrowError(
      "BI_PIN_UNAVAILABLE",
    );
    await expect(malformed.read()).rejects.toThrowError("BI_PIN_UNAVAILABLE");
    await expect(malformed.set(true)).rejects.toThrowError(
      "BI_PIN_UNAVAILABLE",
    );
  });

  it("keeps the fixture Pin outside Tauri and selects IPC only inside Tauri", async () => {
    const memoryPin: PinPort = Object.freeze({
      read: async (): Promise<boolean> => false,
      set: async (enabled: boolean): Promise<boolean> => enabled,
    });
    const calls: string[] = [];
    const invoke: TauriInvoke = async <T>(command: string): Promise<T> => {
      calls.push(command);
      return true as T;
    };

    expect(selectDesktopPinPort(false, memoryPin, invoke)).toBe(memoryPin);
    expect(calls).toEqual([]);

    const desktopPin = selectDesktopPinPort(true, memoryPin, invoke);
    expect(desktopPin).not.toBe(memoryPin);
    expect(await desktopPin.read()).toBe(true);
    expect(calls).toEqual(["is_pinned"]);
  });
});
