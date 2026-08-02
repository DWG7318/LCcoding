import type { PreviewCase } from "../../src/preview";

export type CandidateView =
  | "main"
  | "proposal"
  | "candidate"
  | "calabash"
  | "simulation"
  | "workflow"
  | "ui";
export type CandidateLanguage = "en" | "zh";
export type CandidateMotion = "normal" | "reduced";

export interface VisualCase {
  readonly slug: string;
  readonly preview: PreviewCase;
  readonly view: CandidateView;
  readonly language: CandidateLanguage;
  readonly motion: CandidateMotion;
}

const CORE_VIEWS: readonly CandidateView[] = Object.freeze([
  "main",
  "proposal",
  "candidate",
  "calabash",
  "simulation",
  "workflow",
  "ui",
]);
const CORE_LANGUAGES: readonly CandidateLanguage[] = Object.freeze(["en", "zh"]);
const CORE_MOTIONS: readonly CandidateMotion[] = Object.freeze([
  "normal",
  "reduced",
]);

const coreCases: VisualCase[] = [];
for (const view of CORE_VIEWS) {
  for (const language of CORE_LANGUAGES) {
    for (const motion of CORE_MOTIONS) {
      coreCases.push(
        Object.freeze({
          slug: `candidate--success--${view}--${language}--${motion}`,
          preview: "ok",
          view,
          language,
          motion,
        }),
      );
    }
  }
}

const boundaryCases: readonly VisualCase[] = Object.freeze([
  Object.freeze<VisualCase>({
    slug: "candidate--error--main--en--reduced",
    preview: "error",
    view: "main",
    language: "en",
    motion: "reduced",
  }),
  Object.freeze<VisualCase>({
    slug: "candidate--error--main--zh--reduced",
    preview: "error",
    view: "main",
    language: "zh",
    motion: "reduced",
  }),
  Object.freeze<VisualCase>({
    slug: "candidate--max-en--main--en--reduced",
    preview: "max-en",
    view: "main",
    language: "en",
    motion: "reduced",
  }),
  Object.freeze<VisualCase>({
    slug: "candidate--max-zh--main--zh--reduced",
    preview: "max-zh",
    view: "main",
    language: "zh",
    motion: "reduced",
  }),
]);

export const VISUAL_CASES: readonly VisualCase[] = Object.freeze([
  ...coreCases,
  ...boundaryCases,
]);
