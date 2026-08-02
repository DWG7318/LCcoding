import "./setup";

import { describe, expect, it } from "vitest";

import { VISUAL_CASES } from "../visual/cases";

const EXPECTED_SLUGS = [
  "candidate--success--main--en--normal",
  "candidate--success--main--en--reduced",
  "candidate--success--main--zh--normal",
  "candidate--success--main--zh--reduced",
  "candidate--success--proposal--en--normal",
  "candidate--success--proposal--en--reduced",
  "candidate--success--proposal--zh--normal",
  "candidate--success--proposal--zh--reduced",
  "candidate--success--candidate--en--normal",
  "candidate--success--candidate--en--reduced",
  "candidate--success--candidate--zh--normal",
  "candidate--success--candidate--zh--reduced",
  "candidate--success--calabash--en--normal",
  "candidate--success--calabash--en--reduced",
  "candidate--success--calabash--zh--normal",
  "candidate--success--calabash--zh--reduced",
  "candidate--success--simulation--en--normal",
  "candidate--success--simulation--en--reduced",
  "candidate--success--simulation--zh--normal",
  "candidate--success--simulation--zh--reduced",
  "candidate--success--workflow--en--normal",
  "candidate--success--workflow--en--reduced",
  "candidate--success--workflow--zh--normal",
  "candidate--success--workflow--zh--reduced",
  "candidate--success--ui--en--normal",
  "candidate--success--ui--en--reduced",
  "candidate--success--ui--zh--normal",
  "candidate--success--ui--zh--reduced",
  "candidate--error--main--en--reduced",
  "candidate--error--main--zh--reduced",
  "candidate--max-en--main--en--reduced",
  "candidate--max-zh--main--zh--reduced",
] as const;

describe("fixed BI visual candidate matrix", () => {
  it("enumerates exactly 32 unique ordered candidate slugs", () => {
    const slugs = VISUAL_CASES.map(({ slug }) => slug);

    expect(slugs).toEqual(EXPECTED_SLUGS);
    expect(slugs).toHaveLength(32);
    expect(new Set(slugs).size).toBe(32);
    expect(slugs.every((slug) => slug.startsWith("candidate--"))).toBe(true);
  });

  it("keeps the 28-case success core and four reduced-motion boundaries closed", () => {
    const core = VISUAL_CASES.filter(({ preview }) => preview === "ok");
    const boundaries = VISUAL_CASES.filter(({ preview }) => preview !== "ok");

    expect(core).toHaveLength(28);
    expect(
      core.map(({ view, language, motion }) => `${view}:${language}:${motion}`),
    ).toEqual([
      "main:en:normal", "main:en:reduced", "main:zh:normal", "main:zh:reduced",
      "proposal:en:normal", "proposal:en:reduced", "proposal:zh:normal", "proposal:zh:reduced",
      "candidate:en:normal", "candidate:en:reduced", "candidate:zh:normal", "candidate:zh:reduced",
      "calabash:en:normal", "calabash:en:reduced", "calabash:zh:normal", "calabash:zh:reduced",
      "simulation:en:normal", "simulation:en:reduced", "simulation:zh:normal", "simulation:zh:reduced",
      "workflow:en:normal", "workflow:en:reduced", "workflow:zh:normal", "workflow:zh:reduced",
      "ui:en:normal", "ui:en:reduced", "ui:zh:normal", "ui:zh:reduced",
    ]);
    expect(boundaries).toEqual([
      {
        slug: "candidate--error--main--en--reduced",
        preview: "error",
        view: "main",
        language: "en",
        motion: "reduced",
      },
      {
        slug: "candidate--error--main--zh--reduced",
        preview: "error",
        view: "main",
        language: "zh",
        motion: "reduced",
      },
      {
        slug: "candidate--max-en--main--en--reduced",
        preview: "max-en",
        view: "main",
        language: "en",
        motion: "reduced",
      },
      {
        slug: "candidate--max-zh--main--zh--reduced",
        preview: "max-zh",
        view: "main",
        language: "zh",
        motion: "reduced",
      },
    ]);
  });
});
