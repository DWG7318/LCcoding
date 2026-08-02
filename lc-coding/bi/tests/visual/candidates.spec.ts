import { expect, test, type Page } from "@playwright/test";

import { VISUAL_CASES, type CandidateView, type VisualCase } from "./cases";

declare const process: { readonly env: Readonly<Record<string, string | undefined>> };

const configuredReviewDir = process.env.BI_OWNER_REVIEW_DIR;
if (configuredReviewDir === undefined || configuredReviewDir.trim() === "") {
  throw new Error("BI_OWNER_REVIEW_DIR is required for candidate capture");
}
const OWNER_REVIEW_DIR = configuredReviewDir.replace(/[\\/]+$/, "");
const CANDIDATE_DIR = `${OWNER_REVIEW_DIR}/candidates`;
const REPORT_STEP: Readonly<
  Record<Exclude<CandidateView, "main">, { phase: string; step: string }>
> = Object.freeze({
  proposal: { phase: "INITIAL", step: "PROPOSAL_READINESS" },
  candidate: { phase: "INITIAL", step: "PROJECT_INITIALIZATION" },
  calabash: { phase: "PRODUCT_FORMATION", step: "CALABASH_DRAFT" },
  simulation: {
    phase: "PRODUCT_FORMATION",
    step: "SIMULATION_WORLD_FOUNDATION",
  },
  workflow: {
    phase: "PRODUCT_FORMATION",
    step: "WORKFLOW_CAPABILITY_END",
  },
  ui: { phase: "PRODUCT_FORMATION", step: "UI_PRODUCT_SURFACE_END" },
});

async function waitForPreview(page: Page): Promise<void> {
  await expect(page.locator(".app-shell")).toBeVisible();
  await expect(page.locator(".pin-button")).toBeEnabled();
  await expect(page.locator(".pin-button")).not.toContainText("Checking");
}

async function assertMotionContract(page: Page, candidate: VisualCase): Promise<void> {
  const activeGlyphs = page.locator(
    '.state--active .state-glyph[aria-hidden="true"]',
  );

  if (candidate.preview === "error") {
    expect(await page.evaluate(() => matchMedia("(prefers-reduced-motion: reduce)").matches)).toBe(true);
    expect(await page.evaluate(() => document.getAnimations().length)).toBe(0);
    return;
  }

  await expect(activeGlyphs.first()).toBeVisible();
  const motion = await activeGlyphs.first().evaluate((glyph) => {
    const style = getComputedStyle(glyph);
    const text = glyph.nextElementSibling?.textContent ?? "";
    return {
      animationName: style.animationName,
      duration: style.animationDuration,
      iterationCount: style.animationIterationCount,
      glyph: getComputedStyle(glyph, "::before").content,
      text,
    };
  });

  if (candidate.motion === "reduced") {
    expect(motion.animationName).toBe("none");
    expect(motion.duration).toBe("0s");
    expect(motion.glyph).toContain("●");
    expect(await page.evaluate(() => document.getAnimations().length)).toBe(0);
    return;
  }

  expect(motion.animationName).toBe("state-spinner");
  expect(motion.duration).toBe("0.8s");
  expect(motion.iterationCount).toBe("infinite");
  expect(motion.text).toBe("Running");
  await page.addStyleTag({
    content: `
      .state--active .state-glyph[aria-hidden="true"] {
        animation: none !important;
        transform: rotate(90deg) !important;
      }
    `,
  });
  const frozen = await activeGlyphs.first().evaluate((glyph) => {
    const style = getComputedStyle(glyph);
    return { animationName: style.animationName, transform: style.transform };
  });
  expect(frozen).toEqual({
    animationName: "none",
    transform: "matrix(0, 1, -1, 0, 0, 0)",
  });
}

async function switchLanguage(page: Page, candidate: VisualCase): Promise<void> {
  if (candidate.language === "zh") {
    await page.locator(".language-button").click();
  }
  const options = page.locator(".language-option");
  await expect(options).toHaveCount(2);
  await expect(options.nth(candidate.language === "en" ? 0 : 1)).toHaveAttribute(
    "aria-current",
    "true",
  );
  await expect(options.nth(candidate.language === "en" ? 1 : 0)).not.toHaveAttribute(
    "aria-current",
    "true",
  );
}

async function openTargetReport(page: Page, view: Exclude<CandidateView, "main">): Promise<void> {
  const target = REPORT_STEP[view];
  const row = page.locator(`[data-step-id="${target.step}"]`);
  if (!(await row.isVisible())) {
    await page.locator(`[data-phase-id="${target.phase}"] .phase-summary`).click();
  }
  await expect(row).toBeVisible();
  await row.locator(".open-report").click();
  await expect(page.locator(".report-heading")).toBeVisible();
  await expect(page.locator(".report-rows")).toBeVisible();
  await expect(page.locator(".protected-notice")).toBeVisible();
  await expect(page.locator(".back-button")).toBeFocused();
}

async function focusCaptureControl(page: Page, candidate: VisualCase): Promise<void> {
  await page.keyboard.press("Tab");
  const target =
    candidate.view !== "main"
      ? page.locator(".back-button")
      : candidate.preview === "error"
        ? page.locator(".language-button")
        : page.locator('[data-phase-id="INITIAL"] .phase-summary');
  await target.focus();
}

async function assertFixedViewport(page: Page): Promise<void> {
  expect(page.viewportSize()).toEqual({ width: 300, height: 480 });
  const dimensions = await page.evaluate(() => {
    const shell = document.querySelector<HTMLElement>(".app-shell");
    const body = document.querySelector<HTMLElement>(".app-body");
    if (shell === null || body === null) throw new Error("preview shell missing");
    return {
      inner: [window.innerWidth, window.innerHeight],
      html: [document.documentElement.clientWidth, document.documentElement.clientHeight],
      documentScroll: [
        document.documentElement.scrollWidth,
        document.documentElement.scrollHeight,
      ],
      shell: [shell.offsetWidth, shell.offsetHeight],
      body: [body.clientWidth, body.scrollWidth, body.clientHeight, body.scrollHeight],
      horizontalEscape: [...document.querySelectorAll<HTMLElement>("#app *")]
        .filter((element) => {
          const style = getComputedStyle(element);
          const rect = element.getBoundingClientRect();
          return (
            style.display !== "none" &&
            style.visibility !== "hidden" &&
            rect.width > 0 &&
            (rect.left < -0.5 || rect.right > window.innerWidth + 0.5)
          );
        })
        .map((element) => element.className),
      clippedText: [
        ...document.querySelectorAll<HTMLElement>(
          ".app-title, button, h1, .project-name, .state-text, .row-label, .row-value",
        ),
      ]
        .filter(
          (element) =>
            element.clientWidth > 0 &&
            (element.scrollWidth > element.clientWidth + 0.5 ||
              element.scrollHeight > element.clientHeight + 0.5),
        )
        .map((element) => ({
          className: element.className,
          text: element.textContent,
        })),
    };
  });

  expect(dimensions.inner).toEqual([300, 480]);
  expect(dimensions.html).toEqual([300, 480]);
  expect(dimensions.documentScroll).toEqual([300, 480]);
  expect(dimensions.shell).toEqual([300, 480]);
  expect(dimensions.body[1]!).toBeLessThanOrEqual(dimensions.body[0]!);
  expect(dimensions.body[3]!).toBeGreaterThanOrEqual(dimensions.body[2]!);
  expect(dimensions.horizontalEscape).toEqual([]);
  expect(dimensions.clippedText).toEqual([]);
}

async function assertFocusedOutlineIsVisible(page: Page): Promise<void> {
  const focused = page.locator(":focus");
  await expect(focused).toHaveCount(1);
  const metrics = await focused.evaluate((element) => {
    const rect = element.getBoundingClientRect();
    const style = getComputedStyle(element);
    const outlineWidth = Number.parseFloat(style.outlineWidth);
    const outlineOffset = Number.parseFloat(style.outlineOffset);
    const extent = outlineWidth + outlineOffset;
    return {
      outlineStyle: style.outlineStyle,
      outlineWidth,
      outlineOffset,
      left: rect.left - extent,
      top: rect.top - extent,
      right: rect.right + extent,
      bottom: rect.bottom + extent,
    };
  });

  expect(metrics.outlineStyle).toBe("solid");
  expect(metrics.outlineWidth).toBe(2);
  expect(metrics.outlineOffset).toBe(2);
  expect(metrics.left).toBeGreaterThanOrEqual(0);
  expect(metrics.top).toBeGreaterThanOrEqual(0);
  expect(metrics.right).toBeLessThanOrEqual(300);
  expect(metrics.bottom).toBeLessThanOrEqual(480);
}

async function assertSanitizedSurface(page: Page): Promise<void> {
  const surface = await page.locator("#app").evaluate((root) => ({
    text: root.textContent ?? "",
    html: root.innerHTML,
  }));
  expect(surface.text).not.toMatch(/[A-Za-z]:[\\/]/);
  expect(surface.text).not.toMatch(/(?:file|https?):\/\//i);
  expect(surface.text).not.toContain("Traceback");
  expect(surface.html).not.toMatch(/<(?:a|input)\b/i);
  expect(surface.html).not.toMatch(/\b(?:href|download)=/i);
}

test.describe.configure({ mode: "serial" });

for (const candidate of VISUAL_CASES) {
  test(candidate.slug, async ({ page }, testInfo) => {
    const consoleErrors: string[] = [];
    const pageErrors: string[] = [];
    page.on("console", (entry) => {
      if (entry.type() === "error") consoleErrors.push(entry.text());
    });
    page.on("pageerror", (error) => pageErrors.push(error.message));
    await page.route("**/favicon.ico", (route) =>
      route.fulfill({ status: 204, body: "" }),
    );

    await page.emulateMedia({
      reducedMotion: candidate.motion === "reduced" ? "reduce" : "no-preference",
    });
    await page.goto(`/?case=${candidate.preview}`, { waitUntil: "networkidle" });
    await waitForPreview(page);
    await assertMotionContract(page, candidate);
    await assertFixedViewport(page);
    await page.keyboard.press("Tab");
    await expect(page.locator(".language-button")).toBeFocused();
    await assertFocusedOutlineIsVisible(page);
    await page.keyboard.press("Tab");
    await expect(page.locator(".pin-button")).toBeFocused();
    await assertFocusedOutlineIsVisible(page);
    for (let index = 0; index < 16; index += 1) {
      if (await page.locator(".refresh-button").evaluate((button) => button === document.activeElement)) {
        break;
      }
      await page.keyboard.press("Tab");
    }
    await expect(page.locator(".refresh-button")).toBeFocused();
    await assertFocusedOutlineIsVisible(page);

    await switchLanguage(page, candidate);
    if (candidate.view !== "main") {
      await openTargetReport(page, candidate.view);
    }
    await focusCaptureControl(page, candidate);
    if (candidate.view !== "main") {
      await expect(page.locator(".back-button")).toBeFocused();
    } else if (candidate.preview === "error") {
      await expect(page.locator(".language-button")).toBeFocused();
    } else {
      await expect(
        page.locator('[data-phase-id="INITIAL"] .phase-summary'),
      ).toBeFocused();
    }
    await assertFocusedOutlineIsVisible(page);
    await assertSanitizedSurface(page);
    expect(consoleErrors).toEqual([]);
    expect(pageErrors).toEqual([]);

    const candidatePath = `${CANDIDATE_DIR}/${candidate.slug}.png`;
    const screenshot = await page.screenshot({
      path: candidatePath,
      fullPage: false,
      caret: "hide",
      scale: "css",
    });
    await testInfo.attach(`${candidate.slug}.candidate`, {
      body: screenshot,
      contentType: "image/png",
    });
  });
}
