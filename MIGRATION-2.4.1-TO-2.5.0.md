# Migration: LCCoding 2.4.1 to 2.5.0

LCCoding 2.5.0 turns the integrated BI from a source-only static compatibility surface into one reusable, installed Windows tool. The canonical method mainline, four phases, 21 BI steps, eight protected reports, status authority, and lower-method ownership do not change.

## Required changes

1. Update all overall LCCoding version carriers from `2.4.1` to `2.5.0`; the BI still has no independent version, repository, tag, or Release.
2. Retire the production Vanilla runtime after React + Vite reaches functional and visual parity. Keep sanitized fixtures only under tests; no production module may import them.
3. Install the current-user NSIS package once. Launch `lccoding-bi.exe --project <canonical-project-root>` or use the native Folder Picker; both routes bind one immutable root through the same Rust validation.
4. Preserve `.lccoding/status.json` as the sole authoritative project status. The Rust reader may only project allowlisted, sanitized facts from the supported canonical records and must never write the project.
5. Treat missing, incompatible, contradictory, or unverifiable source facts as `UNKNOWN`, `NOT_RECORDED`, or a fixed path-free error. Do not infer progress, Loop governance, subtree identity, or evidence.
6. Before Release, mechanically verify published SLK `2.5.0`, CLK `2.5.0`, and GLK `3.1.0` contracts from each canonical main/tag/Release. A feature branch, worktree, or candidate commit cannot satisfy this gate.

## Operator result

Projects contain no BI source or toolchain. One installed LCCoding BI can open one project per process, refresh the read-only projection every two seconds, and open multiple independent processes for different projects.
