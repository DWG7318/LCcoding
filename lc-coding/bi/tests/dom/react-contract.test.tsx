import "./setup";

import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { App, type AppPorts } from "../../src/app/App";
import { parseSnapshot } from "../../src/model/snapshot";
import okFixture from "../fixtures/snapshot-ok.json";


function ports(snapshot: unknown | Error): AppPorts {
  return {
    bindProject: vi.fn(async () => ({ ok: true as const, project: "Example Project" })),
    chooseProject: vi.fn(async () => ({ ok: true as const, project: "Example Project" })),
    getSnapshot: vi.fn(async () => {
      if (snapshot instanceof Error) throw snapshot;
      return snapshot;
    }),
    isPinned: vi.fn(async () => false),
    setPinned: vi.fn(async (enabled) => enabled),
  };
}


function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}


describe("React BI product contract", () => {
  it("shows the minimal binding surface when no project is bound", async () => {
    const appPorts = ports(Object.assign(new Error("unbound"), { code: "BI_NO_PROJECT" }));
    render(<App ports={appPorts} />);

    expect(await screen.findByRole("heading", { name: "Open a project" })).toBeTruthy();
    expect(screen.getByLabelText("Project root")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Choose folder" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Open" })).toBeTruthy();
    expect(document.body.textContent).not.toContain("unbound");
  });

  it("renders the fixed four phases, 21 steps, and eight protected reports", async () => {
    const snapshot = parseSnapshot(structuredClone(okFixture));
    render(<App ports={ports(snapshot)} />);

    expect(await screen.findByText("Example Project")).toBeTruthy();
    const phases = document.querySelectorAll("[data-phase-id]");
    expect([...phases].map((phase) => phase.getAttribute("data-phase-id"))).toEqual([
      "INITIAL",
      "PRODUCT_FORMATION",
      "ENGINEERING_RUNS",
      "DELIVERY_PREPARATION",
    ]);
    expect(document.querySelectorAll("[data-step-id]")).toHaveLength(21);
    expect(document.querySelectorAll(".open-report")).toHaveLength(8);
    expect(screen.getByText("REAL_PRODUCT_INTEGRATION")).toBeTruthy();
    expect(screen.queryByText("PRODUCT_INTEGRATION")).toBeNull();

    const workflow = document.querySelector<HTMLElement>(
      '[data-step-id="WORKFLOW_CAPABILITY_END"]',
    );
    const open = workflow?.querySelector<HTMLButtonElement>(".open-report");
    expect(open).toBeTruthy();
    open?.focus();
    fireEvent.click(open!);

    expect(await screen.findByRole("heading", { name: "Workflow" })).toBeTruthy();
    const back = screen.getByRole("button", { name: "Back" });
    await waitFor(() => expect(document.activeElement).toBe(back));
    fireEvent.click(back);
    await waitFor(() => {
      const restored = document.querySelector<HTMLElement>(
        '[data-step-id="WORKFLOW_CAPABILITY_END"] .open-report',
      );
      expect(open?.isConnected).toBe(false);
      expect(document.activeElement).toBe(restored);
    });
  });

  it("switches fixed text to Chinese without translating project values", async () => {
    const user = userEvent.setup();
    const snapshot = parseSnapshot(structuredClone(okFixture));
    render(<App ports={ports(snapshot)} />);
    await screen.findByText("Example Project");

    const language = screen.getByRole("button", { name: /Language:/ });
    await user.click(language);

    expect(screen.getByText("产品形成")).toBeTruthy();
    expect(screen.getByText("Example Project")).toBeTruthy();
    const current = within(language).getByText("中");
    expect(current.getAttribute("aria-current")).toBe("true");
  });

  it("keeps the same protected report open when a real refresh replaces its snapshot", async () => {
    const first = structuredClone(okFixture);
    const refreshed = structuredClone(okFixture);
    refreshed.reports.workflow.rows[0]!.value.status = "ACTIVE";
    const appPorts = ports(first);
    appPorts.getSnapshot = vi
      .fn<() => Promise<unknown>>()
      .mockResolvedValueOnce(first)
      .mockResolvedValueOnce(refreshed);
    render(<App ports={appPorts} />);

    await screen.findByText("Example Project");
    fireEvent.click(
      document.querySelector<HTMLButtonElement>(
        '[data-step-id="WORKFLOW_CAPABILITY_END"] .open-report',
      )!,
    );
    expect(await screen.findByRole("heading", { name: "Workflow" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Refresh" }));
    expect(await screen.findByText("Active")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Workflow" })).toBeTruthy();
    expect(document.querySelector(".phase-list")).toBeNull();
  });

  it("joins concurrent refreshes and starts one two-second timer after settlement", async () => {
    vi.useFakeTimers();
    const reads: ReturnType<typeof deferred<unknown>>[] = [];
    const appPorts = ports(okFixture);
    appPorts.getSnapshot = vi.fn(() => {
      const read = deferred<unknown>();
      reads.push(read);
      return read.promise;
    });
    const mounted = render(<App ports={appPorts} />);

    try {
      await act(async () => undefined);
      expect(reads).toHaveLength(1);

      const refresh = screen.getByRole("button", { name: "Refresh" });
      fireEvent.click(refresh);
      fireEvent.click(refresh);
      expect(reads).toHaveLength(1);

      await act(async () => reads[0]!.resolve(structuredClone(okFixture)));
      await act(async () => vi.advanceTimersByTime(1_999));
      expect(reads).toHaveLength(1);
      await act(async () => vi.advanceTimersByTime(1));
      expect(reads).toHaveLength(2);

      fireEvent.click(refresh);
      expect(reads).toHaveLength(2);
      await act(async () => reads[1]!.resolve(structuredClone(okFixture)));
      expect(vi.getTimerCount()).toBe(1);
    } finally {
      mounted.unmount();
      expect(vi.getTimerCount()).toBe(0);
      vi.useRealTimers();
    }
  });
});
