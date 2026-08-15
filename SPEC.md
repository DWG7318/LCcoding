# LCCoding Standard Specification 2.7.0

This document is the complete normative specification for LCCoding. Stable clause IDs are the source for every constitutional, operational, explanatory, contractual, template, validator, and BI projection. A projection may summarize or mechanically encode a clause, but it may not redefine it.

## Normative clause index

| Clause | Topic |
|---|---|
| [LC-AUTH-001](#lc-auth-001) | Owner authority and method boundary |
| [LC-AUTH-002](#lc-auth-002) | Single semantic authority and project truth |
| [LC-PHASE-001](#lc-phase-001) | Initial |
| [LC-PHASE-002](#lc-phase-002) | Product Formation |
| [LC-PHASE-003](#lc-phase-003) | Real Product Integration |
| [LC-PHASE-004](#lc-phase-004) | Delivery Preparation |
| [LC-FORM-001](#lc-form-001) | Calabash and Simulation-first formation |
| [LC-FORM-002](#lc-form-002) | Workflow, UI, and Simulation product units |
| [LC-FORM-003](#lc-form-003) | Product Baseline and primary product mainline |
| [LC-AGENT-001](#lc-agent-001) | Agent classes, applicability, and required Operations Agent |
| [LC-AGENT-002](#lc-agent-002) | Agent Configuration Baseline and Runtime neutrality |
| [LC-AGENT-003](#lc-agent-003) | Dual-Agent isolation and controlled operations |
| [LC-INTEG-001](#lc-integ-001) | Feature Slice and real integration proof |
| [LC-INTEG-002](#lc-integ-002) | One-way UI lock |
| [LC-INTEG-003](#lc-integ-003) | Impact, mutability, and evidence reuse |
| [LC-INTEG-004](#lc-integ-004) | Agent-native topology and Slice proof |
| [LC-RUN-001](#lc-run-001) | Cross-phase Run call contract |
| [LC-RUN-002](#lc-run-002) | Run start and terminal receipt |
| [LC-RUN-003](#lc-run-003) | Execution-method selection and aggregate scope |
| [LC-VERIFY-001](#lc-verify-001) | Layered independent verification |
| [LC-ACCEPT-001](#lc-accept-001) | Per-Run Loop Owner Acceptance |
| [LC-ACCEPT-002](#lc-accept-002) | Owner gap closure lineage |
| [LC-ACCEPT-003](#lc-accept-003) | Post-Security Owner Acceptance |
| [LC-SEC-001](#lc-sec-001) | Centralized vulnerability closure |
| [LC-SEC-002](#lc-sec-002) | Security evidence invalidation |
| [LC-SEC-003](#lc-sec-003) | Agent security, degradation, and replacement |
| [LC-DELIVERY-001](#lc-delivery-001) | Protected delivery |
| [LC-BI-001](#lc-bi-001) | Built-in BI method boundary |
| [LC-BI-002](#lc-bi-002) | BI responsibility and compatibility boundary |
| [LC-COMPAT-001](#lc-compat-001) | Names, baselines, migration, and versioning |
| [LC-COMPAT-002](#lc-compat-002) | Shared Loop Control transition |

## Authority and truth

<a id="lc-auth-001"></a>
### LC-AUTH-001 — Owner authority and method boundary

LCCoding governs an Owner-led, AI-executed enterprise product-development lifecycle. Owner decides product meaning, value, Workflow intent, UI/UX direction, material scope and trade-offs, material definition changes, release, delivery rights, runtime/cost boundaries, and final Owner Acceptance. For an existing project the Owner alone chooses `CONTINUE`, `NARROW_REDIRECT`, `HOLD`, or `TERMINATE`.

AI completes routine engineering autonomously inside frozen Owner authority. Its duties include source/evidence analysis, proposal-gap detection, project initialization, Workflow/UI/Simulation construction, impact and reuse analysis, Feature Slice planning, bounded execution-method selection, implementation, debugging, verification, evidence management, acceptance preparation, and delivery packaging. AI must not ask the Owner to approve routine technical actions already inside a frozen boundary, and it must not optimize or silently reinterpret product direction.

LCCoding coordinates Calabash definition, product formation, real integration, verification, acceptance, and delivery. It does not redefine Calabash, SLK, CLK, GLK, or another compatible execution method. It specifies only selection conditions, handoff/return contracts, and cross-Run acceptance. The runtime, session control, and Agent execution kernels remain outside LCCoding responsibility. LCCoding adds no runtime, service, Agent role, orchestration engine, or second status system.

<a id="lc-auth-002"></a>
### LC-AUTH-002 — Single semantic authority and project truth

`SPEC.md` is the sole complete semantic authority. `CONSTITUTION.md` contains constitutional principles and Owner rights; `lc-coding/SKILL.md` is the concise execution entry; README files are overview/navigation; references explain only a cited clause; contracts/templates provide mechanical shape; tests and validators prove conformance; BI materials govern only the BI product. Each non-authoritative projection must cite or mechanically trace to its source clause and must not add a phase, gate, state, authority, or normative rule.

`status.json` is the single authoritative project-status record. Project Health is assessment evidence and `PHASE-STATUS.json` is a derived navigation view. A derived view must agree with authoritative evidence, must fail closed on contradiction, and must never become independently writable project truth. Durable method facts belong in project status; sessions, processes, queues, retries, models, hooks, and orchestration do not.

Every project locks exact LCCoding, Calabash, and selected execution-method identities in the existing Canonical Manifest and Interpretation Lock. Load order is canonical LCCoding specification, project Agents Rule, adopted Calabash identity, selected per-Run method contract, project artifacts, repository/code, then AI reasoning. Project rules may add constraints but may not weaken Owner authority, independent Verification, UI lock, delivery protection, or these clauses.

All mandatory lifecycle work remains. Depth is proportional to product uncertainty, coupling, real risk, irreversibility, and novelty. `UNKNOWN` requires conservative depth and evidence; it is not a sufficient final judgment. Existing sufficient evidence is cited and reused. Friction reduction never authorizes missing work, repeated Owner interviews, shallow risk treatment, or empty completion artifacts.

## Four-phase lifecycle

<a id="lc-phase-001"></a>
### LC-PHASE-001 — Initial

`INITIAL` contains Proposal Readiness and Project Initialization and exits through the existing `INITIAL_READY` gate. Proposal Readiness reads supplied material once, builds one completeness view, asks only blocking or materially risky unresolved questions, offers a recommended answer with concise alternatives, persists each answer, and returns only `PROPOSAL_READY` or `PROPOSAL_INCOMPLETE`.

Project Initialization uses `NEW` or `EXISTING` mode. NEW establishes one project Git/GitHub repository, Owner-decided visibility, initial version `0.0.1`, platform Agents Rule, required method identities, capabilities, Canonical Manifest, Interpretation Lock, Profile, Fingerprint, Health, and authoritative status. It does not pre-create empty UI, Workflow, or Simulation directories.

EXISTING mode remains inside Project Initialization. Before engineering it freezes repository, HEAD, declared version or `UNKNOWN`, candidate, inherited materials, and evidence; preserves history and user files; treats inherited completion as `CLAIMED_UNATTESTED`; obtains the Owner continuation decision; and returns only `READY`, `BLOCKED`, or `NOT_CONTINUING`. Runnable UI is a cognition anchor, not proof. Valid evidence is reused; gaps route into existing lifecycle artifacts and Runs. Project Health may classify the intake as `ATTESTED_COMPLETE`, `NEEDS_GAP_CLOSURE`, `PARTIAL`, `DIRECTION_CHANGED`, or `NOT_CONTINUING` without becoming status authority.

Initialization capabilities are tool-neutral: exact/semantic/code-relationship search, syntax and structured-data handling, static quality, secret/dependency intelligence, and architecture/API/data/configuration/observability intelligence. Docker is not a default prerequisite. Later work revalidates only changed identities, capabilities, credentials, or repository state.

For a 2.8 project, Initial also records Agent responsibilities, permissions, protected controls, and degradation expectations; Product Agent applicability or its exact Calabash decision route; the required Operations Agent purpose; root configuration and Kill Switch Owner authority; private-memory and credential boundaries; fallback requirements; and Runtime capability requirements. These facts are inputs to the existing `INITIAL_READY` decision and add no phase or gate.

<a id="lc-phase-002"></a>
### LC-PHASE-002 — Product Formation

`PRODUCT_FORMATION` starts after `INITIAL_READY` and contains, in order of dependency, Calabash Draft, a Simulation-first foundation, separately real and runnable Workflow/UI/peer Simulation product ends, Mandatory Calabash Upgrade, and Product Baseline:

```text
Calabash Draft
→ [Simulation World foundation first → Workflow capability end ∥ UI product-surface end]
→ Mandatory Calabash Upgrade
→ Product Baseline
```

Product Formation ends only when the existing Product Baseline Handoff is mechanically validated and accepted. This direct evidence boundary adds no new gate, status field, or BI gate. `CALABASH_UPGRADE_READY` remains readable for 2.6.0 compatibility only as readiness to begin Mandatory Calabash Upgrade; it is not Product Formation completion.

SLK, CLK, GLK, or another compatible execution method may perform bounded Product Formation work, but method completion merely returns evidence to this phase. It cannot bypass any product-formation condition or advance the phase by itself.

For 2.8, Calabash determines Product Agent applicability, capability, authority, degradation, and CORE/EXTRA classification. An applicable CORE Product Agent is real, runnable, Simulation-covered Workflow capability before Product Baseline and exposes the same underlying capability through governed API and MCP contracts. Product Formation also prepares runtime-neutral Operations Agent configuration, Policy, deterministic Action Catalog, Adapter requirements, telemetry, audit, isolation, fallback, and Kill Switch boundaries without claiming Operations integration; that proof remains Real Product Integration work.

<a id="lc-phase-003"></a>
### LC-PHASE-003 — Real Product Integration

The exact 2.8 new-write machine ID is `REAL_PRODUCT_INTEGRATION`. Exact 2.6/2.7 schemas read only the compatibility machine ID `ENGINEERING_RUNS`; that old ID is not the human meaning and is never written by a 2.8 project. Schema selects one closed ID and a mixed or inferred identity is invalid. Feature Slice is the first lifecycle work in this phase. Admission is the mechanically valid and accepted Product Baseline Handoff, after which a Slice defines an actor-visible claim and its Execution Coverage Preflight admits bounded integration Runs.

The phase organizes separately realized Workflow, UI, and Simulation into a true product path. It proves UI action through a real API/MCP-backed Workflow, real state/data/side effects, and a visible UI result, with the applicable Simulation covering the same capability and exception behavior. It includes UI-locked integration, first proving work when connections are unproved, layered integration evidence, and per-Run Owner receipts.

For 2.8 it also freezes the final production execution topology, resolves every relevant Product Formation backend through `SELECT`, `COMPOSE`, `FEDERATE`, or `RETIRE`, integrates the required Operations Agent through an authorized Runtime Adapter, integrates any applicable Product Agent without merging the two logical Agents, and proves the required `PRODUCT` and `OPERATIONS` Slices. These conditions add no lifecycle gate and do not make an execution method or Runtime a phase.

`ALL_REQUIRED_RUNS_ACCEPTED` is a compatibility aggregate only for required Real Product Integration Runs on the accepted integration candidate. It does not include Runs called by Initial, Product Formation, or Delivery Preparation and does not make an execution method a lifecycle node.

<a id="lc-phase-004"></a>
### LC-PHASE-004 — Delivery Preparation

`DELIVERY_PREPARATION` begins only after `ALL_REQUIRED_RUNS_ACCEPTED` for the required Phase-3 integration set. It contains centralized vulnerability audit, remediation, independent re-audit, vulnerability closure, Post-Security Owner Acceptance, customer-specific Delivery Method Q&A, runtime/license/package checks, and protected packaging.

The existing `DELIVERY_READY` gate is the only exit. It requires current candidate-bound security closure, current Post-Security Owner Acceptance, confirmed delivery decisions, and package protection. Any later product/security-surface change follows the invalidation rule in the security clauses before Delivery may proceed.

For 2.8, the same centralized closure and existing `DELIVERY_READY` gate additionally require current Agent-specific isolation, prompt/tool/memory/privilege/model/Runtime/fallback/Kill-Switch/audit evidence and customer-specific Runtime/credential/recovery decisions. No Agent-specific phase or Delivery gate is introduced.

## Product Formation

<a id="lc-form-001"></a>
### LC-FORM-001 — Calabash and Simulation-first formation

Calabash owns product definition and governance. LCCoding consumes only the adopted Calabash Definition Baseline, applicable clause identity, Snake guards, Scorpion hard blocks, product meaning/invalidation, and Mandatory Upgrade result. Snake and Scorpion are cross-cutting product-definition dimensions, not Agents or new LCCoding layers. LCCoding does not copy Calabash construction procedures, interviews, layers, validators, or internal workflow.

Meaning-changing work requires an applicable Calabash Definition Baseline basis or a governed return to Calabash. Strictly meaning-neutral engineering cites its calling-phase contract and impact evidence and must not fabricate a definition baseline. A relevant Snake `OPEN` or Scorpion `HIT` blocks affected meaning/work under Calabash authority.

Before actual Workflow or UI construction begins, Product Formation requires at least one minimal, real, runnable, versioned Simulation World foundation. It is a starting Product Simulation World, not a complete or frozen Simulation. Workflow, UI, and Simulation are built separately during Product Formation. Only after that foundation exists may Workflow and UI advance as equal product ends, independently; each must produce real, runnable, inspectable results. Early Product Formation does not require Workflow and UI to be connected or all three elements to be jointly integrated. Cross-layer Workflow-to-UI connection and end-to-end proof remain responsibilities of Feature Slice and UI-locked Integration. Simulation remains `VERSIONED_MUTABLE` and gains scenarios and fidelity through versioned deltas.

Product Simulation World means the versioned, resettable product world and its actors, data, state, time, permissions, dependencies, failures, recovery, and history. Run Control Simulation means an execution-method or runtime rehearsal of topology, wake, timing, roles, or controls. Neither is evidence for the other.

Focused explanation: [Product Formation guidance](lc-coding/references/product-formation.md#scope-and-formation-sequence).

<a id="lc-form-002"></a>
### LC-FORM-002 — Workflow, UI, and Simulation product units

Multiple UI, Workflow, and Simulation product units may exist as peer logical subtrees inside one total project repository—the one project Git/GitHub repository. Relations are expressed by stable IDs in Maps and baselines, never by directory nesting. Simulations are peers and never nest under another Simulation. Each realized subtree has a safe relative path, component version, and content hash. A worktree is optional for parallel construction or environment isolation; it is not product structure, permanent identity, or a second repository.

Workflow defines actors, authority, state transitions, input/output, rules, side effects, failure/recovery, external constraints, and reusable capabilities. Workflow is not merely a plan, description, or flowchart of product capability. AI must use Calabash and available Simulation Worlds to decompose Workflow into enough business lines and progressively implement real, runnable business functions. Early implementation may be scattered and need not connect to UI, but plans, empty shells, mocks, or simulation-only results cannot substitute for real Workflow. Workflow may evolve until Mandatory Calabash Upgrade completes.

Every Workflow business line is classified as `CORE` or `EXTRA`; this is business necessity, not a Workflow Core technical layer. CORE is confirmed in Calabash and by the Owner as required product capability. EXTRA is an enhancement derived from Calabash extension space, external research, or comparable-product analysis. An unimplemented EXTRA is only a registry row, creates no empty subtree or interface, does not block Product Baseline, and must not be claimed as existing product capability unless implemented and verified. AI must not reclassify CORE as EXTRA to pass Product Baseline; change requires Calabash basis and Owner confirmation.

Every CORE Workflow and every implemented EXTRA Workflow directly provides both API and MCP calling contracts backed by the same real capability, product rules, and evidence. API and MCP do not create duplicate logic, a mandatory microservice, a Core engine, a runtime, or deployment topology. UI or backend callers may use the API and Agent-facing callers may use MCP.

UI covers every relevant actor-facing product surface. UI, Workflow, and Simulation remain separately runnable and inspectable during formation while sharing product meaning and scenario IDs. Their synchronization is not early cross-layer integration.

Focused explanation: [Product Formation guidance](lc-coding/references/product-formation.md#peer-product-ends-interfaces-and-mainline).

<a id="lc-form-003"></a>
### LC-FORM-003 — Product Baseline and primary product mainline

Mandatory Calabash Upgrade consumes accumulated Owner decisions and synchronized evidence, resolves or governs contradictions, and produces the adopted definition result before LCCoding freezes the LCCoding Product Baseline. The Calabash Definition Baseline fixes meaning; the LCCoding Product Baseline fixes realized product identity.

The Product Baseline implementation gate applies only to CORE Workflow. If any CORE line is not real/runnable with both API and MCP evidence, or is proved infeasible under the current product constraints, the project must not enter Product Baseline and must first adjust Calabash, narrow the direction, hold, or terminate under Owner authority. Incomplete or infeasible EXTRA does not block Product Baseline and remains a non-capability until implemented and verified.

Product Baseline Handoff freezes one total project repository at an exact project commit (full resolvable SHA) and locks every realized UI, Workflow, and Simulation subtree by ID/name, safe path, `MAJOR.MINOR.PATCH` component version, and deterministic content hash. Maps and Handoff must agree on identities, Workflow classification and API/MCP evidence, relations, and Owner confirmation.

When multiple subtrees exist, the Owner confirms one Primary product mainline linking at least one peer Product Simulation, one CORE Workflow, and one UI. It selects first proving/construction priority only; every other CORE remains mandatory. A controlled Calabash upgrade may reconfirm the relation.

At the frozen commit, each subtree path must be a Git tree. Recursively enumerate tracked blobs and encode each manifest row as `path UTF-8 bytes + NUL + Git mode + NUL + lowercase blob SHA-256 hex + LF`; sort by path bytes, concatenate, and record `sha256:<lowercase SHA-256 of manifest bytes>`. Validators resolve commit and blobs from Git objects, never worktree content. Exact commit and content hash are authoritative; component version is the human label. Screenshots, builds, branches, tags, `HEAD`, `latest`, or worktree state cannot replace identity.

Focused explanation: [Product Formation guidance](lc-coding/references/product-formation.md#peer-product-ends-interfaces-and-mainline).

## Agent-native product and operations

<a id="lc-agent-001"></a>
### LC-AGENT-001 — Agent classes, applicability, and required Operations Agent

A Construction Agent—such as a Supervisor, Worker, Checker, Verifier, Auditor, or acceptance preparer—builds or verifies the product. Its engineering role, session, prompt, memory, or tool use never makes it a delivered Product Agent or Operations Agent, and construction evidence never becomes delivered Agent state.

A Product Agent participates in user business behavior. Calabash determines whether it is `APPLICABLE_CORE`, `APPLICABLE_EXTRA`, or `NOT_APPLICABLE`, plus its actors, authority, capability, failure, and degradation semantics. An applicable CORE Product Agent is real product capability before Product Baseline under the existing CORE, Simulation, Workflow, and same-capability API/MCP rules; absence or an implicit applicability decision is invalid.

An Operations Agent is required for every 2.8 project. It observes and assists with product operation and maintenance and must be truly connected during Real Product Integration; a dashboard, chatbot, Construction Agent, or read-only status explanation cannot substitute for it. Product Agent and Operations Agent may both exist, but they are two independent logical Agents. A single Agent using role switching, prompt switching, namespaces, or two memory modes is not conformant.

Focused explanation: [Agent-native integration guidance](lc-coding/references/agent-native-integration.md#agent-classes-and-applicability).

<a id="lc-agent-002"></a>
### LC-AGENT-002 — Agent Configuration Baseline and Runtime neutrality

Agent configuration follows one authority flow:

```text
Owner decides
→ Calabash defines
→ LCCoding construction implements
→ independent Verification
→ Owner accepts
→ authorized Runtime Adapter mechanically loads
```

The versioned, hash-bound, Runtime-neutral Agent Configuration Baseline records exact Product/Operations Agent applicability and IDs; Policy, Action Catalog, prompt/config package, private-memory/retriever, credential/key-reference, audit, Kill Switch, fallback, interface, candidate, Verification, and Owner-acceptance identities. Secrets, tokens, raw prompts, raw sessions, private-memory contents, credentials, and encryption keys do not enter Git; only safe references and exact digests are recorded.

LCCoding defines platform-neutral capabilities, Adapter/attestation shape, and acceptance evidence. It does not implement a Runtime, session/execution state, memory engine, vector database, model router, process manager, or action executor. LCagent is one Owner-selectable reference Runtime whose implementation remains in the LCagent project; OpenAI or any other SDK, model, provider, or store is not mandatory. A conforming Runtime Adapter cannot enlarge permission, merge Agents, weaken memory boundaries, change product meaning, or ignore Scorpion.

Root identity, permission ceiling, memory boundary, Scorpion constraints, credentials, encryption keys, audit policy, and Kill Switch remain protected Owner configuration. A Product Agent may manage only authorized user preferences and its own bounded session memory. An Operations Agent may propose a configuration delta, but protected changes require exact Owner approval and affected re-verification. LCCoding creates no third configuration Agent.

Focused explanation: [Agent-native integration guidance](lc-coding/references/agent-native-integration.md#configuration-authority-and-runtime-neutrality).

<a id="lc-agent-003"></a>
### LC-AGENT-003 — Dual-Agent isolation and controlled operations

When a Product Agent applies, Product and Operations Agents have distinct Agent ID, session/context, private memory store, vector index, retriever, write credentials, encryption key, system prompt, prompt cache, API/MCP/tool credentials, Policy, Action Catalog, audit stream, and Kill Switch. Aliasing any required private identity fails. A base model or Runtime implementation may be shared when these isolation outcomes remain mechanically verified. A shared authoritative product state is not Agent memory and is accessed only through each Agent's governed permission boundary.

Cross-Agent communication uses only typed, minimal, policy-checked, redacted, provenance-bound, audited events, initially `MAINTENANCE_REQUEST` and `SERVICE_STATUS_UPDATE`. Natural-language messages cannot convey administrator authority, credentials, root approval, raw sessions, private memory, unmanaged summaries, prompts, or prompt caches. Private memory from either Agent cannot enter online training or shared-model weight updates.

The Operations Agent minimum path is `observe → diagnose → propose → Owner authorization or exact bounded pre-authorization → deterministic action → verify → rollback when required → audit`. Every action is a closed Action Catalog record with bounded target/input, preconditions, authorization, deterministic Adapter operation, postconditions, verification, rollback, audit, timeout, and retry policy. Authorization is exactly `OWNER_APPROVAL_REQUIRED` or `CALABASH_PREAUTHORIZED_BOUNDED`. The latter is permitted only for individually identified low-risk actions with exact scope, expiry, verification, rollback, and audit; it cannot cover data deletion, permissions, release, upgrade, database migration, credentials, protected root configuration, Kill Switch, or irreversible work. No Agent may self-authorize or modify its protected controls.

Focused explanation: [Agent-native integration guidance](lc-coding/references/agent-native-integration.md#dual-agent-isolation-and-typed-events).

## Real Product Integration

<a id="lc-integ-001"></a>
### LC-INTEG-001 — Feature Slice and real integration proof

Feature Slice is the product-progress unit and the entry to Real Product Integration. It identifies all already implemented and verified Workflow capabilities across CORE and EXTRA and must inherit and reuse them wherever possible. It begins from the Owner-confirmed Primary product mainline unless impact evidence selects another governed route. Because it covers UI, integration, state, data, permissions, exceptions, recovery, and actor-visible results, it may supplement, adjust, and improve Workflow under Impact Analysis and `CONTROLLED_MUTABLE` rules.

A valid Slice proves this same capability chain:

```text
actor intent
→ real UI operation
→ integration boundary
→ API/MCP-backed Workflow
→ real state/data/side effect
→ visible UI result
→ evidence and acceptance
```

Simulation covers the same capability, state, scenarios, exceptions, and recovery; it need not be the production backend. Static UI, mock, stub, simulation-only output, or manually staged state cannot prove third-phase integration. A component, API, table, refactor, or test group alone is not a Slice.

Execution Coverage Preflight runs after the Slice exists and before a bounded integration Run. It covers actor outcome, Product Baseline, Workflow/UI/Simulation, state/data/permissions, exception/recovery, Impact Analysis, Integration Baseline, Required Runs, D0–D3, and Owner Acceptance. `HIGH`/`UNKNOWN` requires deeper evidence or smaller independently verifiable Runs. If cross-layer proof is missing, the first Required Run is the thinnest production-quality end-to-end proving path; failure blocks expansion. Sufficient existing proof may be cited instead.

Focused explanation: [Real Product Integration guidance](lc-coding/references/feature-slice-and-integration.md#slice-and-proving-path).
<a id="lc-integ-002"></a>
### LC-INTEG-002 — One-way UI lock

The Integration Baseline applies this lock to the applicable UI subtree in the total project repository:

```text
UI = LOCKED
Workflow = CONTROLLED_MUTABLE
Simulation = VERSIONED_MUTABLE
Calabash = LIVING_WITH_IMPACT_TRACE
```

`UI = LOCKED` is one-way Owner authority. The Owner may initiate or explicitly approve a UI change; Workflow, Simulation, execution methods, Agents, runtimes, automation, and other system actors must not autonomously modify locked UI. The lock pins total-project exact commit plus applicable UI ID/path/component version/content hash and must match Product Handoff. A branch, tag, `HEAD`, worktree, screenshot, export, build, or `latest` is not the lock.

Before a Slice/Run and before acceptance, compare current UI to the locked commit/hash. An unauthorized difference blocks work or acceptance. Preserve and isolate the difference; the system must not silently overwrite user material or automatically restore it.

A legal UI change uses the existing Baseline Change Request, states necessity and alternatives, records Owner initiation/approval, creates a distinct project commit and updated UI version/hash, synchronizes Product and Integration Baselines, and re-verifies affected evidence. Declared data binding, responsive behavior, accessibility metadata, and exact restoration do not themselves unlock UI.

Focused explanation: [Real Product Integration guidance](lc-coding/references/feature-slice-and-integration.md#one-way-ui-lock-and-recoverable-identity).
<a id="lc-integ-003"></a>
### LC-INTEG-003 — Impact, mutability, and evidence reuse

Before a material change, Impact Analysis covers affected Calabash meaning, Workflow, UI, Simulation, Feature Slices, shared capabilities, data, Verification, Runs, release, and rollback. Later work updates that one analysis by delta unless scope, baseline, or architecture materially changes. Only affected connected layers and evidence change together.

Workflow is `CONTROLLED_MUTABLE`; Simulation is `VERSIONED_MUTABLE`; Calabash is `LIVING_WITH_IMPACT_TRACE`; UI follows the one-way lock. These mutability policies never waive identity, Owner authority, or affected re-verification.

Evidence reuse requires identical candidate/artifact identity, contract version, relevant environment, authority, currency/completeness, and no contradiction. Repeat a check only for candidate change, stale/missing/contradictory evidence, material environment difference, composition risk, affected regression, or a named security/migration/branch/join/fallback/cycle/concurrency/recovery risk. Record source, reason, scope difference, risk, and result.

Product learning may be blank. Return it only when it changes a future decision, constraint, check, template, or reuse rule, and update one existing canonical artifact. LCCoding creates no retrospective phase or learning repository.

Focused explanation: [Real Product Integration guidance](lc-coding/references/feature-slice-and-integration.md#impact-mutability-evidence-and-learning).

<a id="lc-integ-004"></a>
### LC-INTEG-004 — Agent-native topology and Slice proof

Exact 2.8 Real Product Integration writes `REAL_PRODUCT_INTEGRATION`; `ENGINEERING_RUNS` is read-only compatibility identity for exact 2.6/2.7 schemas. The phase freezes one final production execution topology for the accepted candidate. Every relevant backend/service candidate appears exactly once with disposition `SELECT`, `COMPOSE`, `FEDERATE`, or `RETIRE`. Active dispositions bind product behavior, state/data authority, identity, permission, consistency, failure/recovery, and calling boundaries; a retired candidate proves no active dependency or authority remains. The topology does not require physical consolidation, a monolith, or a Product Backend/Core layer, and Workflow `CORE`/`EXTRA` remains business necessity rather than technical topology.

Feature Slice remains the sole product-progress unit. Slice class is exactly one of {`PRODUCT`, `OPERATIONS`}; a cross-domain change uses linked Slices rather than a mixed or third class. A PRODUCT Slice proves actor intent through a real UI or applicable Product Agent, a governed integration boundary, an API/MCP-backed Workflow capability, real state/data/side effect, visible result, and Simulation exception/recovery evidence. Model text, prompts, mocks, stubs, simulation-only output, or manually staged state cannot replace this route.

Every 2.8 project has at least one accepted required OPERATIONS Slice proving real telemetry/log/event → Operations Agent observation/diagnosis/proposal → exact Policy and authorization → deterministic maintenance action → verification/rollback → audit and visible status. Read-only explanation alone is insufficient. Both Slice classes bind the same exact Product Baseline, Agent Configuration Baseline, production topology, Runtime Adapter attestation, candidate, Impact, Verification, and Owner acceptance where applicable.

The existing UI one-way Owner lock, Workflow controlled mutability, Simulation versioned mutability, and Calabash impact trace remain. Simulation covers the same capability, authorization, abnormal condition, fallback, failure, recovery, and audit semantics but is neither production backend nor Agent self-verification. This clause adds no phase, gate, Feature-Slice alternative, Runtime, or execution method.

Focused explanation: [Agent-native integration guidance](lc-coding/references/agent-native-integration.md#topology-slices-and-shared-baseline).

## Runs, verification, and acceptance

<a id="lc-run-001"></a>
### LC-RUN-001 — Cross-phase Run call contract

Any bounded work item in `INITIAL`, `PRODUCT_FORMATION`, `ENGINEERING_RUNS`, or `DELIVERY_PREPARATION` may call a Run. Each Run-start record identifies the Run, calling phase, phase-owned objective, calling-phase authority/contract, frozen scope and exclusions, selected execution-method identity, phase-appropriate input evidence, evidence return target, acceptance condition, D0–D3/Owner-acceptance requirement, proportional depth, and readiness result.

Initial supplies proposal/initialization authority; Product Formation supplies definition, scenario, or product-end authority; Real Product Integration supplies the Slice, Product/Integration identities and Required Run scope; Delivery Preparation supplies the accepted candidate, security finding, delivery decision, or package contract. A phase supplies only applicable evidence and never fabricates a Feature Slice or Calabash basis.

The method returns evidence to the calling phase and evidence return target. Run completion does not advance a phase; only the calling phase evaluates its own acceptance condition and gate against returned evidence.

<a id="lc-run-002"></a>
### LC-RUN-002 — Run start and terminal receipt

`RUN-HANDOFF.md` is the Run-start contract. It contains only facts knowable before execution: identity, calling phase/objective/authority, scope/exclusions, selected method/contract, inputs, return target, acceptance condition, depth, and readiness. It must not contain a D3 verdict, final candidate, Owner result, gap closure, or terminal acceptance evidence.

`LOOP-OWNER-ACCEPTANCE.md` is the terminal receipt for every normal Run. It cites the exact Run-start identity/hash and contains the final candidate, D3 evidence, Owner result, gap lineage, and returned evidence. Start and end artifacts are not two copies of an acceptance packet.

Run completion does not advance a phase, and a terminal receipt answers only its bounded Run. The calling phase decides whether its own objective and evidence set are sufficient.

<a id="lc-run-003"></a>
### LC-RUN-003 — Execution-method selection and aggregate scope

LCCoding chooses the lightest truthful topology: SLK for one serial stream, CLK for fixed Chains with ordered Stages/full barriers, GLK for a real dependency graph, or another registered execution method whose compatible contract fits the bounded work. One method owns a Run. Methods own their internal GO/CELL/Chain/Stage/graph/task/retry topology; LCCoding does not copy it.

The existing Canonical Manifest supplies the minimal registry source. A compatible execution-method entry provides exact identity/hash, supported topology, Run-start mapping, evidence/D0–D3 mapping, Loop Owner Acceptance mapping, and runtime-attestation/compatibility status. This is a small interface, not a new registry system.

Execution methods are a cross-phase axis, not a lifecycle node and not confined to Phase 3. `ALL_REQUIRED_RUNS_ACCEPTED` means all required Real Product Integration Runs for the accepted candidate are accepted. It excludes Initial, Product Formation, Delivery Preparation, optional, superseded, and invalidated Runs.

<a id="lc-verify-001"></a>
### LC-VERIFY-001 — Layered independent verification

- D0 is Worker self-check and feedback, never acceptance.
- D1 is independent Checker CELL acceptance of an immutable local candidate and contract.
- D2 is independent GO outcome Verification that composes D0/D1 evidence; Worker, Checker, and Run Supervisor cannot author it.
- D3 is a fresh independent Stage/Run/Final composition Verification that adds only seam, end-to-end, locked-UI, invisible-system, and final-candidate evidence.

Higher layers reuse valid lower receipts rather than rerunning identical work. If one Run D3 covers the exact Slice claim, candidate, UI baseline, and scenarios, LCCoding promotes it after identity/coverage checks. A multi-Run Slice verifies only seams, uncovered claims, and the integrated actor journey. Verification independence and evidence identity are mandatory at every depth.

Focused explanation: [Verification evidence guidance](lc-coding/references/verification-de-duplication.md#layered-independent-verification).
<a id="lc-accept-001"></a>
### LC-ACCEPT-001 — Per-Run Loop Owner Acceptance

Every normal Run in any phase ends with D3 PASS, `LOOP_OWNER_ACCEPTANCE_READY`, and Supervisor-guided Loop Owner Acceptance while scope and context remain small. Results are `LOOP_OWNER_ACCEPTED`, `LOOP_PRODUCT_REWORK`, `LOOP_PRODUCT_DEFINITION_CHANGE`, or `LOOP_OWNER_DEFERRED`.

Several normal Runs produce several receipts; they are not replaced by one late aggregate review. Only required Real Product Integration Runs contribute to `ALL_REQUIRED_RUNS_ACCEPTED`; each contributing Run must be `LOOP_OWNER_ACCEPTED` and current for the accepted candidate.

Focused explanation: [Owner terminal decision guidance](lc-coding/references/loop-acceptance-boundary.md#per-run-terminal-decision).
<a id="lc-accept-002"></a>
### LC-ACCEPT-002 — Owner gap closure lineage

Rework, definition change, or defer creates one stable Owner gap ID linked from acceptance source through candidate/scenario, Impact/definition route, correction Run, affected D0–D3, delta re-verification, and delta Owner re-acceptance. Definition changes return through Calabash and the normal baseline/Slice path; defer remains open.

A gap closes only when the new candidate and affected evidence are accepted. `status.json` indexes only open gap IDs and evidence pointers; full lineage remains in existing acceptance, impact, Run, and receipt artifacts. A blocking open gap prevents the Phase-3 aggregate.

Focused explanation: [Owner terminal decision guidance](lc-coding/references/loop-acceptance-boundary.md#owner-gap-lineage).
<a id="lc-accept-003"></a>
### LC-ACCEPT-003 — Post-Security Owner Acceptance

After `VULNERABILITY_CLOSED`, the Owner accepts the security-remediated final candidate. This Post-Security Owner Acceptance reuses all current Run receipts and reviews only remediation-affected UI/Workflow/Feature surfaces, final candidate identity, security closure, and critical smoke. It must not repeat unchanged prior product acceptance.

Results are `POST_SECURITY_OWNER_ACCEPTED`, `POST_SECURITY_PRODUCT_REWORK`, or `POST_SECURITY_OWNER_DEFERRED`. Delivery remains blocked until the current candidate is `POST_SECURITY_OWNER_ACCEPTED`.

Focused explanation: [Owner terminal decision guidance](lc-coding/references/loop-acceptance-boundary.md#post-security-terminal-decision).
## Security and delivery

<a id="lc-sec-001"></a>
### LC-SEC-001 — Centralized vulnerability closure

Immediately after the required Phase-3 Run aggregate, freeze the accepted candidate and appoint a fresh independent Security Auditor in an isolated context/workspace. The auditor must not have served as Worker, Checker, Verifier, Run Supervisor, acceptance preparer, or remediation implementer for that candidate.

The centralized audit builds complete attack-surface coverage, reuses valid identical local security evidence, executes missing checks, issues the report/finding ledger, routes remediation to separate engineering roles, and independently re-audits affected surfaces. D0–D3 security assertions do not replace this centralized verdict. `VULNERABILITY_CLOSED` requires complete coverage and no open Critical/High issue, secret exposure, authentication bypass, privilege escalation, cross-customer leakage, or independence violation.

Focused explanation: [Security closure guidance](lc-coding/references/vulnerability-closure.md#centralized-audit-and-closure).
<a id="lc-sec-002"></a>
### LC-SEC-002 — Security evidence invalidation

Security closure and Post-Security acceptance are valid only for their exact candidate and declared attack surfaces. If later Delivery Preparation work changes product or security surface—including behavior, dependency, configuration, privilege, data handling, API/client exposure, installer, or runtime—the impact analysis invalidates affected `vulnerability_closure`, Post-Security Owner Acceptance, and `DELIVERY_READY` evidence for the changed candidate.

Affected engineering verification is rerun, a fresh independent security re-audit covers the delta and transitive surface, closure is reissued for the new identity, and focused Owner acceptance repeats for affected product surfaces and critical smoke. Delivery remains blocked until current closure, acceptance, Q&A, and package protection all pass.

Meaning-neutral and security-surface-neutral work preserves evidence only when Impact Analysis proves unchanged candidate/security identity or an evidence-equivalent packaging transformation. Silence never preserves closure. This rule uses existing status and receipts; it creates no new state source or security runtime.

Focused explanation: [Security closure guidance](lc-coding/references/vulnerability-closure.md#candidate-and-surface-binding).

<a id="lc-sec-003"></a>
### LC-SEC-003 — Agent security, degradation, and replacement

Agent-native security coverage binds the exact candidate, Agent Configuration Baseline, Action Catalog, production topology, Runtime Adapter, applicable Product Agent, and required Operations Agent. Required surfaces include prompt injection and instruction-boundary bypass, privilege escalation and authorization confusion, cross-Agent memory leakage, private store/vector index/retriever/session/prompt-cache exposure, tool and secret protection, model drift and unavailability, Policy/Action-Catalog bypass, deterministic-action integrity, event redaction/provenance, Agent isolation, fallback, rollback, recovery, Kill Switch, audit integrity, and Runtime replacement. Centralized independent audit, remediation, re-audit, closure, and Post-Security Owner Acceptance remain unchanged.

Operations Agent failure must be visible, alertable, degradable, and recoverable and does not by default stop unrelated core business behavior. Product Agent failure stops core behavior only when Calabash classifies that Agent capability as CORE and defines no accepted non-Agent fallback. No fallback may expand permission, merge Agents, bypass Scorpion, use stale credentials, disable audit, or convert a proposal into an action.

A change to Agent applicability, Policy, Action Catalog, private-memory/credential boundary, Adapter, Runtime, model capability, topology, typed-event schema, fallback, or Agent attack surface follows Impact Analysis and invalidates affected engineering evidence, vulnerability closure, Post-Security Owner Acceptance, and `DELIVERY_READY` for the changed identity. Runtime replacement is material unless exact evidence-equivalence is proved under LC-SEC-002. This clause uses the existing status, security, acceptance, and Delivery relationships and adds no new security or Delivery gate.

Focused explanation: [Agent-native integration guidance](lc-coding/references/agent-native-integration.md#security-degradation-replacement-and-delivery).

<a id="lc-delivery-001"></a>
### LC-DELIVERY-001 — Protected delivery

Delivery Preparation conducts customer-specific Delivery Method Q&A after current Post-Security Owner Acceptance, records the delivery decisions, and completes package protection. AI loads Owner Policy, Project Profile, accepted candidate, customer contract/material, and prior decisions; asks only unresolved questions with a recommended option; and immediately persists each answer in the existing delivery decision artifact. It covers hosting/responsibility, assets, rights, runtime/network, data, internal dependencies, license/activation, credentials, launch, rollback, and handover. Actual Delivery begins only after `DELIVERY_READY`; Q&A is not actual Delivery.

Deliver only approved product assets. Default exclusions are LCagent, LCapi, LCCoding, Calabash, SLK, CLK, GLK, Project Intelligence tools, canonical assets, internal knowledge/workflow/recommendation logic, and development evidence. Source code is excluded unless Owner explicitly authorizes it. Owner Policy restrictions are hard constraints, not customer options. Ubuntu and no-source delivery remain recommendations unless locked or confirmed; Docker is not required.

When Owner Policy or an Owner decision confirms them, no-resale, redistribution, sublicense, repackaging, unauthorized modification, reverse engineering, transfer, and control removal boundaries are hard delivery constraints. These boundaries must not be invented as default legal facts, inferred from silence, or weakened after confirmation.

Required evidence includes Delivery Profile, Dependency Classification, Delivery Manifest, Runtime Certification, Delivery License Policy, and Delivery Receipt. Verification checks integrity, exclusions, runtime, license, configuration, startup, and any packaging-induced behavior without repeating unchanged product Verification.

For an Agent-native product, Delivery also proves current Runtime Adapter/configuration/topology/isolation/fallback/Kill-Switch/audit identities and records customer Runtime/model/provider responsibility, credential ownership, recovery, audit retention, and replacement decisions. Approved runtime-neutral product configuration may be delivered; secrets, private memory, raw prompts/sessions, construction-Agent evidence, unapproved Runtime internals, and internal method assets remain excluded.

Focused explanation: [Protected delivery guidance](lc-coding/references/delivery-governance.md#decision-before-delivery).
## BI and compatibility

<a id="lc-bi-001"></a>
### LC-BI-001 — Built-in BI method boundary

LCCoding may ship one built-in BI as a read-only Owner-visible projection. One installation serves projects; a project does not generate or maintain BI source. The BI may show four phases, fine milestones, states, artifacts, and protected reports but cannot write project data, control Agents/Runs/runtime, open raw evidence, or become a second status authority. `status.json` remains authoritative.

The compact desktop keeps the 300×480 logical content baseline, English default, complete Chinese fixed-text switch, internal scrolling, same-window Open/Back, Refresh, and native Pin. Pin controls only BI Window Always-on-top and must confirm host state; it is not Task Pin authority.

The protected Product Baseline report remains on `PRODUCT_BASELINE`; the protected Execution Method Governance report remains on compatibility step `LOOP_RUN_D0_D3`. Simulation/Workflow/UI reports expose only sanitized derived metrics. Missing evidence remains `UNKNOWN` or `NOT_RECORDED`; no phase, step, gate, state field, method authority, or control action is added.

The one-project binding, CLI `lccoding-bi.exe --project <root>`, and native picker share Rust-owned validation. The strict sanitized Snapshot excludes paths, repository/commit/hash/evidence bodies, raw errors, and thread IDs. No-argument `get_snapshot` is single-flight and fail-closed. The BI reads only canonical allowlisted artifacts and never treats a view as project truth.

For exact 2.8 status, the existing Canonical Candidate protected report minimally shows Operations Agent integration status, Product Agent applicability and applicable integration status, Runtime Adapter identity/version, dual-Agent isolation status, and separate `PRODUCT` and `OPERATIONS` Slice progress. It cannot control an Agent, Runtime, session, memory, prompt, credential, tool, action, authorization, fallback, or Kill Switch and exposes no raw evidence. Existing compact-window, bilingual, Pin/Refresh/Open/Back, focus, scroll, protected-report, and read-only behavior remains.

<a id="lc-bi-002"></a>
### LC-BI-002 — BI responsibility and compatibility boundary

BI method meaning is limited to the LC-BI clauses. Product/visual behavior belongs in the focused BI method reference; implementation/build/test navigation belongs beside BI source; strict DTO/ACL/package shapes belong in BI contracts/configuration; release procedure belongs beside release automation. Historical BI designs are non-normative evidence.

The existing `lc-coding/bi/release/loop-contract-identities.json` evolves as the single method compatibility asset. It contains only LCCoding status adapter identity and SLK/CLK/GLK or compatible execution-method adapter identities. It contains no Calabash identity, project status, runtime/session state, or duplicate semantic rules. Rust and release-verifier consumers read the same asset; hard-coded method versions outside it are forbidden.

LCCoding Method Baseline separately records adopted LCCoding, Calabash, and execution-method identities in the existing Canonical Manifest and Interpretation Lock. The BI does not become that baseline or its release authority.

<a id="lc-compat-001"></a>
### LC-COMPAT-001 — Names, baselines, migration, and versioning

Exact 2.8 new writes use `REAL_PRODUCT_INTEGRATION` as the third-phase machine ID and human meaning. Exact 2.6/2.7 schemas remain read-only through compatibility ID `ENGINEERING_RUNS`; schema selects one ID, readers never infer from the tuple, and a 2.8 writer never emits the old ID. The canonical human display remains `REAL_PRODUCT_INTEGRATION` / “Real Product Integration” / “真实产品集成”.

Migration from 2.7 to 2.8 is copy-on-write: preserve the source project and receipt bytes, create and fully validate a distinct candidate, write only the 2.8 schema/phase ID, reuse only unchanged evidence, and leave new Agent-native conditions incomplete until proved. Migration does not promote historical evidence. A readable 2.7 project cannot claim 2.8 until required Operations Agent integration, applicable Product Agent evidence, Agent Configuration Baseline, final topology, Runtime Adapter attestation, dual-Agent isolation, affected Verification, security closure, and migration evidence are current. Rollback discards or isolates the unaccepted candidate and writes no 2.8 state back to 2.7.

Canonical terms are distinct:

- Calabash Definition Baseline fixes product meaning, clauses, Snake guards, and Scorpion blocks.
- LCCoding Product Baseline fixes total-project commit and realized subtree identities/relations.
- LCCoding Integration Baseline fixes Slice/applicable UI lock and integration candidate.
- LCCoding Method Baseline fixes exact method identities, hashes, compatibility, and interpretation.
- Product Simulation World is product evidence; Run Control Simulation is execution rehearsal.
- Task Pin is Owner-authorized task control; BI Window Always-on-top is local window state.

2.6.0 remains immutable. Released 2.7.0 evidence also remains immutable. Project migration to a new phase interpretation is copy-on-write: preserve source artifacts, derive from existing evidence without fabricating completion, validate output fully, and leave failed output absent. Rollback never rewrites a frozen Product or Calabash baseline.

Version policy remains: NEW starts `0.0.1`; EXISTING preserves its declared version or records `UNKNOWN`; small change is commit-only; medium is `0.0.x`; large is `0.x.1`; `1.0.1+` needs explicit Owner authorization. Release promotion never overwrites an earlier tag, release, evidence package, or installed baseline.

<a id="lc-compat-002"></a>
### LC-COMPAT-002 — Shared Loop Control transition

`LCCODING_LOOP_CONTROL` is one shared method contract, not a fourth execution method and not a runtime. It defines common policy and evidence for Worker wake, Supervisor no-wait, Patrol, task/subagent/Pin boundaries, progress, capacity, and model use without copying the same policy into SLK, CLK, and GLK. LCCoding never performs the governed thread, wait, heartbeat, Pin, dispatch, or archive operations; LCagent or another trusted runtime executes them and returns current attestations.

Only a Worker may use this ladder to wake its frozen Checker. The four levels are: (1) direct send; (2) same-task read/list/unarchive; (3) one temporary `CHECKER_WAKE_HEARTBEAT`; and (4) write `PENDING_WAKE` for Run Patrol fallback. The Worker waits 120 seconds for the frozen Checker before each escalation. The bound Checker's `WAKE_ACK` immediately terminates the ladder. This is not a generic Checker or Supervisor escalation ladder.

A Supervisor must not wait online: positive-duration, looping, and wait-all `wait_threads` are forbidden. It may use only a zero-time snapshot for observation and then continue its own work or return control.

Each active Run is assigned exactly one fast, non-technical Patrol conversation and one `RUN_PATROL_HEARTBEAT`; its frozen LOW/MEDIUM/HIGH difficulty selects 10/15/30 minutes respectively. Patrol itself creates no conversation. At terminal closure it removes its heartbeat and archives itself.

Patrol checks only unexplained stoppage, pending wake, actual subagent use, forbidden Supervisor wait, duplicate Patrol or heartbeat, Pin provenance, and terminal closure. It must not perform product or engineering work and must not report engineering progress.

Actual subagent operations are `spawn_agent`, `delegate_task`, hidden-agent, and background-agent operations. A GO, CELL, task, role, or the word subtask is not itself a subagent operation. Agents must not Pin tasks; the only exceptions are Owner UI action or item-specific Owner authorization. A task Pin with unknown provenance is reported and must not auto-unpin a task.

Capacity is evaluated before dispatch. The only outcomes are `PASS`, `SPLIT_REQUIRED`, and `CAPACITY_BLOCKED`; a Worker must not self-split. Worker reports delivered CELL `x/y`; Checker reports accepted CELL `x/y`; Supervisor reports GO/Level/Run scope and material state; Patrol reports no engineering progress.

Patrol uses the fastest capable non-technical inspection class, for example Luna with `xhigh`; normal technical roles use Terra with `xhigh`; difficult correction uses Sol with `xhigh`; `ultra` requires item-specific Owner authorization; 5.5 and lower models are not used for this method line.

Adoption uses transitional binding. Each execution method retains its verified local control until its canonical contract binds these shared clauses, trusted runtime attestations prove equivalent enforcement, failure/rollback is tested, and that method's approved release explicitly retires duplicate behavior. Until then, local controls remain authoritative for their runtime; LCCoding neither deletes nor operates them. Historical evidence does not become current merely through migration.
