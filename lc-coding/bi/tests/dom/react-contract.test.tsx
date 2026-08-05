import "./setup";

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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

    const workflow = document.querySelector<HTMLElement>(
      '[data-step-id="WORKFLOW_CAPABILITY_END"]',
    );
    const open = workflow?.querySelector<HTMLButtonElement>(".open-report");
    expect(open).toBeTruthy();
    open?.focus();
    fireEvent.click(open!);

    expect(await screen.findByRole("heading", { name: "Workflow" })).toBeTruthy();
    const back = screen.getByRole("button", { name: "Back" });
    expect(document.activeElement).toBe(back);
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
});
