# Shared Loop Control Contract

`LCCODING_LOOP_CONTROL` is one versioned method contract shared by SLK, CLK, and GLK. It is not a fourth Loop method, does not change which topology a Run selects, and does not replace D0-D3, the selected Loop's authority, or Loop Owner Acceptance.

It owns only cross-Loop control policy and evidence: Worker-to-Checker wake, Supervisor no-wait, one temporary Run Patrol, actual-subagent prohibition, Pin provenance, layered progress ownership, capacity-before-dispatch, and controllable model policy. The canonical machine-readable source is [`../contracts/loop-control-contract.json`](../contracts/loop-control-contract.json).

## Runtime boundary

LCCoding does not implement a runtime. It never creates conversations, sends messages, waits, schedules a heartbeat, pins a task, dispatches a model, or keeps session state. LCagent or another trusted runtime performs those operations and supplies a current, verifiable attestation. A Loop consumes that attestation through one `LOOP_CONTROL_BINDING`; absent, stale, mismatched, or failed evidence blocks new formal work. It is not enough to create an envelope or a template: the binding needs the current runtime result.

The binding does not permit a Loop to trust a self-authored claim. It binds the exact contract ID/version/hash, runtime adapter identity, attestation root, result, and only the selected method's own mapping. The mapping may add graph, chain, or serial dimensions, but cannot weaken a common rule.

## Required common policy

1. Only a Worker can wake its frozen Checker. It tries exactly four levels—direct send; same-task read/list/unarchive; one temporary heartbeat; then a `PENDING_WAKE` record for Patrol fallback—and waits 120 seconds before each escalation. A bound Checker `WAKE_ACK` stops the ladder.
2. A Supervisor never uses positive-duration, looping, or wait-all `wait_threads`. A zero-time snapshot is allowed only as an observation.
3. Each Run has one fast, non-technical Patrol conversation and one heartbeat, with frozen LOW/MEDIUM/HIGH intervals of 10/15/30 minutes. It creates no conversation. On terminal completion it deletes its heartbeat and archives itself.
4. Patrol checks only unexplained stoppage, pending wake, actual subagent use, forbidden Supervisor wait, duplicate Patrol/heartbeat, Pin provenance, and terminal closure. It neither writes product work nor reports engineering progress.
5. `spawn_agent`, `delegate_task`, hidden-agent, and background-agent operations are actual subagent use. A GO, CELL, task, role, or a phrase such as “subtask” is not itself an actual subagent.
6. Agents do not Pin tasks. Owner UI or an item-specific Owner authorization is the sole exception; unknown provenance is reported and never auto-unpinned.
7. Worker reports its own delivery position to Checker; Checker reports current-valid D1 and GO boundaries; Supervisor reports material global D1/D2, active/waiting, holds, and version changes. Patrol reports no engineering progress.
8. Capacity passes before dispatch. The only outcomes are `PASS`, `SPLIT_REQUIRED`, and `CAPACITY_BLOCKED`; a Worker cannot self-split.
9. `ultra` is forbidden without separate Owner authorization. Roles default to `gpt-5.6-terra` + `xhigh`; fine-grained CELL work may use `gpt-5.6-luna` + `xhigh`; only high-difficulty correction may use `gpt-5.6-sol` + `xhigh`; no binding is below `gpt-5.6-luna` + `xhigh`.

## Adoption sequence

The contract is method policy, not an implementation to be copied into three repositories. SLK, CLK, and GLK first bind the same exact contract version and digest while retaining their current validated controls. Only after every method has a valid binding and LCagent (or another trusted runtime) provides current attestations may the duplicated method-local control engines be removed. Historical receipts remain readable, but never become current evidence merely through migration.
