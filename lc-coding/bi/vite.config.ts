import { defineConfig } from "vitest/config";

export default defineConfig(({ command }) => {
  const externalDist = process.env.LCCODING_BI_DIST;
  if (command === "build" && externalDist === undefined) {
    throw new Error("LCCODING_BI_DIST is required for production builds");
  }

  return {
    base: "./",
    build: {
      outDir: externalDist ?? ".vitest-unused-dist",
      sourcemap: false,
    },
    server: {
      host: "127.0.0.1",
    },
    preview: {
      host: "127.0.0.1",
    },
    test: {
      environment: "jsdom",
      include: ["tests/dom/**/*.{test,spec}.{ts,tsx}"],
    },
  };
});
