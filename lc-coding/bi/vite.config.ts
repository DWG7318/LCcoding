import { defineConfig } from "vitest/config";

export default defineConfig({
  base: "./",
  build: {
    outDir: "dist",
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
    include: ["tests/dom/**/*.{test,spec}.ts"],
  },
});
