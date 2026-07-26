# LCCoding

**Owner-led, AI-executed product development.**

LCCoding starts from a living Calabash, designs Workflow and UI as two ends, builds a
realistic Simulation World, and advances through user-visible end-to-end Feature Slices.
AI performs engineering, verification, impact analysis, regression, and synchronization;
the Owner controls product decisions and acceptance.

## 1.1.0 — Integration Baseline Lock

During Feature Integration, the UI becomes the fixed target by default:

```text
UI = LOCKED
Workflow = CONTROLLED_MUTABLE
Simulation = VERSIONED_MUTABLE
Calabash = LIVING_WITH_IMPACT_TRACE
```

AI may not redesign or simplify accepted UI to reduce engineering difficulty. A UI
change requires a Baseline Change Request, impact analysis, and explicit Owner approval.

## Install as a skill

Copy `lc-coding/` into the supported skills directory and invoke `$lc-coding`.

## Bootstrap a project

```bash
python lc-coding/scripts/bootstrap_lccoding.py \
  --project /path/to/project \
  --name "Project Name" \
  --profile PRODUCT
```

## Validate

```bash
python lc-coding/scripts/validate_lccoding.py /path/to/project
```

See [`README.zh-CN.md`](README.zh-CN.md) and [`lc-coding/SKILL.md`](lc-coding/SKILL.md).
