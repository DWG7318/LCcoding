# Shared Loop Control Contract

`LCCODING_LOOP_CONTROL` is one versioned method contract shared by SLK, CLK, and GLK. It is not a fourth Loop method, does not change which topology a Run selects, and does not replace D0-D3, the selected Loop's authority, or Loop Owner Acceptance.

It owns only cross-Loop control policy and evidence: Worker-to-Checker wake, Supervisor no-wait, distinct Checker-wake and Run-Patrol heartbeats, actual-subagent prohibition, Pin provenance, layered progress ownership, capacity-before-dispatch, and controllable model policy. The canonical machine-readable source is [`../contracts/loop-control-contract.json`](../contracts/loop-control-contract.json).

## Runtime boundary

LCCoding does not implement a runtime. It never creates conversations, sends messages, waits, schedules a heartbeat, pins a task, dispatches a model, or keeps session state. LCagent or another trusted runtime performs those operations and supplies a current, verifiable attestation. A Loop consumes that attestation through one `LOOP_CONTROL_BINDING`; an absent binding leaves the method's verified local control `ACTIVE` or `RETAINED`, while stale, mismatched, or failed binding evidence blocks shared-control reliance and local-control retirement. It is not enough to create an envelope or a template: the binding needs the current runtime result.

The binding does not permit a Loop to trust a self-authored claim. It binds the exact contract ID/version/hash, runtime adapter identity, attestation root, result, and only the selected method's own mapping. The mapping may add graph, chain, or serial dimensions, but cannot weaken a common rule.

## Required common policy

1. Only a Worker can wake its frozen Checker. It tries exactly four levels—direct send; same-task read/list/unarchive; one temporary `CHECKER_WAKE_HEARTBEAT`; then a `PENDING_WAKE` record for Patrol fallback—and waits 120 seconds before each escalation. The temporary wake heartbeat belongs to one delivery/wake incident only, is removed on bound Checker `WAKE_ACK` or terminal fallback, and never counts as Patrol. A bound Checker `WAKE_ACK` stops the ladder.
2. A Supervisor never uses positive-duration, looping, or wait-all `wait_threads`. A zero-time snapshot is allowed only as an observation.
3. Each active Run has one fast, non-technical Patrol conversation and exactly one `RUN_PATROL_HEARTBEAT`, with frozen LOW/MEDIUM/HIGH intervals of 10/15/30 minutes. Patrol itself creates no conversation. On terminal closure it deletes the Patrol heartbeat and archives itself. Its ID, lifecycle, count, and evidence claim cannot be shared with a Checker-wake heartbeat.
4. Patrol checks only unexplained stoppage, pending wake, actual subagent use, forbidden Supervisor wait, duplicate Patrol/heartbeat, Pin provenance, and terminal closure. It neither writes product work nor reports engineering progress.
5. `spawn_agent`, `delegate_task`, hidden-agent, and background-agent operations are actual subagent use. A GO, CELL, task, role, or a phrase such as “subtask” is not itself an actual subagent.
6. Agents do not Pin tasks. Owner UI or an item-specific Owner authorization is the sole exception; unknown provenance is reported and never auto-unpinned.
7. Worker reports delivered CELL `x/y` to Checker; Checker reports accepted CELL `x/y` to Supervisor; Supervisor reports GO/Level/Run scope and material state. Patrol reports no engineering progress.
8. Capacity passes before dispatch. The only outcomes are `PASS`, `SPLIT_REQUIRED`, and `CAPACITY_BLOCKED`; a Worker cannot self-split.
9. Patrol uses the fastest qualified non-technical capability class (the GPT reference is Luna + `xhigh`); ordinary technical work uses Terra + `xhigh`; difficult correction, root cause, or complex rework uses Sol + `xhigh`. `ultra` is limited to high-difficulty correction and requires one closed item-specific Owner authorization object: safe item ID, safe Owner authorization ID, exact authorization-evidence SHA-256, and `OWNER_APPROVED_ULTRA`. Under `xhigh`, that field is exactly `NOT_APPLICABLE`. GPT 5.5 and lower are forbidden. A binding records the actual model and capability choice, with trusted equivalence evidence when it does not use the reference model.

## Adoption sequence

The contract is method policy, not an implementation to be copied into three repositories. SLK, CLK, and GLK first bind the same exact contract version and digest while retaining their current validated controls. A method may retire local control only when its exact contract binding and non-weakening topology mapping, current trusted runtime attestation, positive and negative runtime conformance evidence, readable historical receipts, and that method's Owner-approved release all prove retirement. Historical receipts remain readable, but never become current evidence merely through migration.
