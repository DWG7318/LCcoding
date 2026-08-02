import { defineConfig } from "@playwright/test";

declare const process: { readonly env: Readonly<Record<string, string | undefined>> };

const configuredReviewDir = process.env.BI_OWNER_REVIEW_DIR;
if (configuredReviewDir === undefined || configuredReviewDir.trim() === "") {
  throw new Error("BI_OWNER_REVIEW_DIR is required for candidate capture");
}

export const OWNER_REVIEW_DIR = configuredReviewDir.replace(/[\\/]+$/, "");
const reviewPath = (...parts: readonly string[]): string =>
  [OWNER_REVIEW_DIR, ...parts].join("/");

export default defineConfig({
  testDir: "./tests/visual",
  testMatch: "candidates.spec.ts",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  forbidOnly: true,
  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  outputDir: reviewPath("test-results"),
  preserveOutput: "always",
  reporter: [
    ["line"],
    [
      "html",
      {
        outputFolder: reviewPath("html-report"),
        open: "never",
      },
    ],
  ],
  use: {
    baseURL: "http://127.0.0.1:4173",
    viewport: { width: 300, height: 480 },
    deviceScaleFactor: 1,
    colorScheme: "light",
    locale: "en-US",
    screenshot: "off",
    trace: "off",
    video: "off",
  },
  projects: [
    {
      name: "installed-chrome",
      use: {
        browserName: "chromium",
        channel: "chrome",
      },
    },
  ],
  webServer: {
    command:
      "node ./node_modules/vite/bin/vite.js preview --host 127.0.0.1 --port 4173 --strictPort",
    url: "http://127.0.0.1:4173",
    reuseExistingServer: true,
    timeout: 30_000,
  },
});
