# LCCoding Standard Specification 2.6.0

## 1. Scope

LCCoding governs an Owner-led, AI-executed enterprise product-development lifecycle. It coordinates proposal readiness, project initialization, Calabash evolution, Workflow/UI dual-end design, Simulation, real Product Integration, Verification, Owner Acceptance, and protected Delivery. Execution methods are a separate cross-phase axis.

This specification does not redefine the internal rules of Calabash, SLK, CLK, or GLK. It defines how a bounded work item in any phase selects a method, supplies phase-appropriate authority, and returns evidence to the calling phase.

LCCoding remains portable across Agent platforms. Runtime, session control, and Agent execution kernels are outside its method responsibility.

## 2. Mainline

```text
Owner Proposal
→ Proposal Readiness Check
→ Project Initialization
→ Calabash Draft
→ [Simulation World foundation first → Workflow capability end ∥ UI product-surface end]
→ Mandatory Calabash Upgrade
→ Product Baseline
→ Feature Slice
→ UI-locked Real Product Integration
→ Layered Verification
→ Owner Acceptance
→ Delivery
```

The operational binding is:

- the lifecycle axis defines what each phase must establish, while the execution-method axis defines how bounded work is performed;
- every selected Loop Run contains D0–D3 and incremental Loop Owner Acceptance and returns evidence to its calling phase;
- after all required third-phase integration work is accepted, Layered Verification performs centralized independent vulnerability audit, remediation, re-audit, and closure;
- the mainline Owner Acceptance is Post-Security Owner Acceptance;
- Delivery starts with customer-specific Delivery Method Q&A.

No implementation convenience may remove Workflow, UI, Simulation, Mandatory Calabash Upgrade, Feature Slice, or Owner Acceptance from this mainline.

### 2.1 Four-phase overlay

The mainline is grouped into four phases. Phases are navigation and exit-gate boundaries, not additional lifecycle nodes.

| Phase | Included mainline work | Exit gate | Next boundary |
|---|---|---|---|
| `INITIAL` | Proposal Readiness and Project Initialization | `INITIAL_READY` | Calabash Draft may begin |
| `PRODUCT_FORMATION` | Calabash Draft; Workflow, UI, and Simulation are built separately as runnable product ends with semantic/scenario coordination | `CALABASH_UPGRADE_READY` | Mandatory Calabash Upgrade may begin |
| `ENGINEERING_RUNS` | Real Product Integration: connect Workflow, UI, and Simulation through real API/MCP capability, state/data/side effects, visible UI results, and integration/end-to-end proof | per Run: `LOOP_OWNER_ACCEPTANCE_READY`; compatibility aggregate: `ALL_REQUIRED_RUNS_ACCEPTED` for required Phase-3 integration work | Continue until every required integration claim is accepted |
| `DELIVERY_PREPARATION` | Centralized vulnerability audit/remediation/re-audit, Post-Security Owner Acceptance, Delivery Method Q&A, runtime/license/package checks | `DELIVERY_READY` | Delivery may occur |

A phase exit gate must reference the same canonical artifacts already produced by the mainline; it must not copy or redefine them.

SLK, CLK, GLK, and other registered execution methods may be selected in every phase. Method completion is evidence, not automatic phase advancement.

### 2.2 Fixed coverage, proportional depth

All mandatory mainline nodes remain. Their analysis, material, and evidence depth is proportional to:

- product uncertainty;
- system coupling;
- real risk;
- irreversibility;
- novelty.

`Project Fingerprint.complexity` records these factors and the resulting depth rationale and coverage. `UNKNOWN` is an allowed unresolved intake state, not a sufficient final depth judgment: it requires depth assessment, a rationale, and explicit deeper analysis, material, or evidence until resolved. Existing sufficient evidence must be cited and reused. All-low work may be concise; any other resolved factor requires a rationale, and any high factor requires explicit deeper coverage. Adjusting depth never deletes a node, weakens an authority boundary, or permits an empty completion artifact. `recommended_loop` is an advisory topology hint for the current bounded work, not a project-global selection; the authoritative choice is recorded per Run.

## 3. Owner and AI authority

### Owner authority

The Owner decides:

- product direction and value;
- Workflow intent and business behavior;
- UI/UX direction and accepted visual result;
- material scope and trade-offs;
- material Calabash amendments;
- version promotion and release;
- delivery scope, customer rights, runtime, and cost;
- final Owner Acceptance.
- continuation, narrowing/redirection, holding, or termination of an existing project.

### AI duty

AI performs:

- source and evidence analysis;
- proposal-gap detection and recommended options;
- project initialization;
- Workflow/UI/Simulation construction and synchronization;
- impact and reuse analysis;
- Feature Slice planning;
- per-work-item execution-method selection and engineering execution in any phase;
- debugging, verification, evidence management, and deterministic synchronization;
- acceptance preparation and delivery packaging.

AI must not ask the Owner to approve routine technical actions already inside a frozen authority boundary.

## 4. Proposal Readiness Check

PRC checks whether the Owner Proposal is sufficiently complete to create a meaningful Calabash Draft.

PRC must:

1. read all supplied proposal material once;
2. build one completeness view;
3. identify only blocking or materially risky gaps;
4. reuse answered questions and verified facts;
5. ask targeted questions only for unresolved gaps;
6. offer a recommended answer plus concise alternatives;
7. write every answer immediately into the Proposal record;
8. stop when the proposal is ready.

Outputs:

```text
PROPOSAL_READY
PROPOSAL_INCOMPLETE
```

PRC does not replace the Owner's proposal work and must not repeatedly re-interview already settled topics.

## 5. Project Initialization

Project Initialization prepares one durable enterprise project environment in `NEW` or `EXISTING` mode.

Required results:

- one project Git repository and one project GitHub repository by default;
- Owner-confirmed Public or Private visibility;
- initial commit and version `0.0.1` for NEW, or preserved repository history and declared version for EXISTING;
- platform-appropriate Agents Rule;
- required skills installed and version-locked: LCCoding, Calabash, SLK, CLK, GLK;
- Project Intelligence capability manifest;
- Canonical Manifest and Interpretation Lock;
- Project Profile, Project Fingerprint, and Project Health.

Project Initialization does not pre-create empty UI, Workflow, or Simulation product subtrees. Product structure appears later as real logical subtrees inside the one project Git/GitHub repository. A worktree is optional for parallel construction or environment isolation; it is not a permanent product subtree, baseline asset, or second repository.

`status.json` is the single authoritative project-status record. Project Health is assessment evidence. `PHASE-STATUS.json` is a derived navigation view and must agree with `status.json`; neither may become a second writable source of project truth. Status records durable method facts only, never Agent sessions, processes, queues, retries, models, hooks, or orchestration state.

### Existing engineering mode

EXISTING mode covers half-complete, near-complete, claimed-complete but unattested, dormant, and redirected engineering projects. It is an initialization mode, not a new phase, lifecycle, or mainline.

The mode must:

1. freeze and record the current repository, Git HEAD, declared version or `UNKNOWN`, materials, runnable candidate, and available evidence before engineering;
2. preserve Git/GitHub identity, history, files, versions, and verified assets, without resetting to `0.0.1`;
3. record inherited completion claims as `CLAIMED_UNATTESTED`, never as a LCCoding gate receipt;
4. give the Owner the current facts and obtain `CONTINUE`, `NARROW_REDIRECT`, `HOLD`, or `TERMINATE` before engineering;
5. use runnable UI as the first Owner-visible cognition anchor, not completion evidence;
6. trace visible entries back through Workflow, state, data, permissions, failure/recovery, and independent evidence for invisible behavior;
7. reuse valid evidence under the normal identity, contract, environment, currency, authority, and contradiction rules; unknown remains unknown;
8. convert only uncovered or contradicted claims into existing Feature Slices and SLK/CLK/GLK Runs.
9. issue only `READY`, `BLOCKED`, or `NOT_CONTINUING` as takeover readiness. `READY` requires an evidenced candidate, inventoried historical material and evidence, reconstructed product mainline, a continued-project health classification, and no unresolved takeover blocker.

Project Health classifies the intake as `ATTESTED_COMPLETE`, `NEEDS_GAP_CLOSURE`, `PARTIAL`, `DIRECTION_CHANGED`, or `NOT_CONTINUING`. `HOLD` and `TERMINATE` produce `NOT_CONTINUING`; they never enter engineering. `CONTINUE` and `NARROW_REDIRECT` remain `BLOCKED` until the readiness evidence is complete. Continued work follows the unchanged mainline and existing Calabash, Workflow/UI/Simulation, Product Baseline, Impact Analysis, D0–D3, Owner Acceptance, security, and Delivery rules.

### Capability-first tooling

The required capabilities are:

- code relationships: Code Graph;
- exact search: Code Search and ripgrep;
- semantic symbol navigation: LSP;
- syntax structure: Tree-sitter or equivalent;
- file and structured-data handling: fd and jq or equivalent;
- static quality: Semgrep or equivalent;
- secrets and dependency intelligence;
- architecture, database, API contract, configuration, and observability intelligence.

AI chooses the actual tool and when to invoke it. Docker is not a default prerequisite.

### Initialization reuse

Initialization checks run once. Later work revalidates only changed versions, hashes, capabilities, credentials, or repository state. It must not repeatedly rescan the entire environment without a trigger.

## 6. Canonical consistency

Every project locks the exact versions and hashes of LCCoding, Calabash, SLK, CLK, and GLK.

The load order is:

```text
LCCoding canonical specification
→ current project Agents Rule
→ active Calabash version
→ selected Loop standard
→ project artifacts
→ repository/code
→ AI reasoning
```

Project rules may add constraints but may not redefine LC terms or weaken Owner authority, Verification independence, UI lock, or delivery restrictions.

An Interpretation Lock is reissued only when a locked version/hash, compatibility statement, or project override changes.

## 7. Calabash, Workflow, UI, and Simulation

### Calabash

Calabash begins as a Draft based on the ready Proposal. It evolves throughout Workflow, UI, and Simulation work. It is not assumed complete at project start.

Before actual Workflow or UI construction begins, Product Formation requires at least one minimal, real, runnable, versioned Simulation World foundation. It is a starting world, not a complete or frozen Simulation. A project may form multiple peer Simulation logical subtrees, each with its own component version, and may gain fidelity, scenarios, and project learning throughout Product Formation. Simulation subtrees never nest inside one another.

Only after that foundation exists may Workflow and UI advance as equal product ends, independently. They may proceed concurrently, but each must produce real, runnable, inspectable results. Early Product Formation does not require Workflow and UI to be connected or all three elements to be jointly integrated. Continue semantic and scenario synchronization across all three without treating synchronization as cross-layer integration. Cross-layer Workflow-to-UI connection and end-to-end proof remain responsibilities of Feature Slice and UI-locked Integration.

### Workflow capability end

Workflow defines what the product actually does: actors, authority, states, transitions, inputs, outputs, rules, side effects, failure/recovery, external constraints, and reusable capabilities.

Workflow is not merely a plan, description, or flowchart of product capability. During the existing Workflow/UI/Simulation stage, AI must use Calabash and available Simulation Worlds to decompose Workflow into enough business lines to cover the product and progressively implement real, runnable business functions. Each implemented Workflow business line is a named logical subtree in the one project Git/GitHub repository, with its own component version and content hash. Early implementation may be scattered and need not immediately connect to UI, but plans, empty shells, mocks, or simulation-only results cannot substitute for real Workflow. Workflow may continue to iterate with Simulation and Calabash until the Mandatory Calabash Upgrade is complete.

Every Workflow business line is classified as `CORE` or `EXTRA`; this is product necessity, not a Workflow Core technical layer. CORE is confirmed in Calabash and by the Owner as required product capability. EXTRA is an enhancement derived from Calabash extension space, external research, or comparable-product analysis. AI should attempt EXTRA, but a technically difficult or infeasible EXTRA may remain a concept, requirement, deferred item, or infeasible item; it does not block Product Baseline and must not be claimed as existing product capability unless implemented and verified. An unimplemented EXTRA is only a registry entry: it has no empty subtree and no empty API or MCP claim. AI must not reclassify CORE as EXTRA to pass Product Baseline; every classification change returns to Calabash and requires Owner confirmation.

Every CORE Workflow and every implemented EXTRA Workflow directly provides both API and MCP calling contracts from that Workflow capability. API and MCP must use the same underlying product rules and evidence; they do not create a second implementation, mandatory microservice, Workflow Core engine, runtime, or deployment topology. UI and product backends may call the API contract, while Agent-facing use calls the MCP contract.

### UI product-surface end

UI includes every actor-facing surface: customer, staff, operator, support, review, fulfillment, administrator, configuration, notification, approval, audit, and status surfaces. A project may contain multiple named UI logical subtrees inside the total project repository, each with its own component version and content hash.

### Simulation World

Simulation is a versioned and resettable product world with realistic actors, data density, state, time, permissions, devices, external dependencies, failures, recovery, and history. Multiple Simulation logical subtrees are peers; no Simulation owns or nests another Simulation.

Simulation remains `VERSIONED_MUTABLE`: the minimum foundation is strengthened by versioned deltas as more scenarios and learning appear, never treated as a one-time complete freeze.

Workflow, UI, and Simulation are distinct but continuously synchronized in product meaning and scenario identity. UI-to-Workflow and Simulation-to-Workflow relations may be many-to-many and are recorded by IDs in the Workflow Map and Product Baseline, never inferred from directory nesting. That synchronization does not require early Workflow-to-UI wiring or joint integration. The same scenario identifiers should be reused in design, integration, Verification, and Owner Acceptance rather than copied into separate test catalogs.

When multiple logical subtrees exist, the Owner confirms one Primary product mainline that links at least one Simulation, one CORE Workflow, and one UI. It determines the first cross-layer proving direction and construction priority only. Every other CORE Workflow remains mandatory and cannot be downgraded to EXTRA. A controlled Calabash upgrade may re-confirm the selected mainline.

## 8. Mandatory Calabash Upgrade and Product Baseline

After Workflow, UI, and Simulation have exposed the product sufficiently, LCCoding requires one formal Mandatory Calabash Upgrade before Feature Integration.

The upgrade:

- consumes accumulated Owner decisions, findings, and synchronized artifacts;
- resolves or explicitly governs contradictions and open decisions;
- updates product meaning once, without repeating Proposal discovery;
- produces a versioned Product Baseline.

The Product Baseline is the engineering reference. Later verified learning may amend it through impact analysis, but it must never drift silently.

The Product Baseline implementation gate applies only to CORE Workflow. If any CORE business line is not yet implemented as real, runnable behavior with both API and MCP evidence, or is proved infeasible under the current product constraints, the project must not enter Product Baseline. Work must first adjust Calabash, narrow the direction, hold, or terminate under Owner authority. Incomplete or infeasible EXTRA does not block Product Baseline and remains a non-capability until implemented and verified.

Product Baseline Handoff freezes one total project repository at an exact project commit (full SHA) and locks every realized UI, Workflow, and Simulation logical subtree by name, safe relative path, component version, and deterministic content hash. Component versions use `MAJOR.MINOR.PATCH`. It also locks the ID relations among UI, Workflow, and Simulation and the Owner-confirmed Primary product mainline; the mainline ID and every `YES` / `NO` marker must match the canonical Workflow, UI, and Simulation Maps. Every locked row must match its Map identity, Workflow classification, API/MCP evidence, and relations. Commit and content hash are authoritative identity; component version is the human-readable label. Screenshots, exported images, previews, build artifacts, branch names, `HEAD`, or `latest` cannot replace the rebuildable source and exact identity. Worktree state is never a baseline identity.

All product logical subtrees use one content-hash algorithm. At the frozen commit, require the declared path to resolve to a Git tree, recursively enumerate tracked blobs, and form each manifest entry as `path UTF-8 bytes + NUL + Git mode + NUL + lowercase blob SHA-256 hex + LF`. Sort entries by path bytes, concatenate them, and record `sha256:<lowercase SHA-256 of the manifest bytes>`. This is the same algorithm for UI, Workflow, and Simulation. The validator must resolve the recorded commit and blobs from Git objects; current worktree content cannot replace them.

## 9. Feature Slice

Feature Slice is the LCCoding product-progress unit.

A Feature Slice must identify all already implemented and verified Workflow capabilities across CORE and EXTRA and inherit and reuse them wherever possible. It starts from the Owner-confirmed Primary product mainline unless impact evidence selects another governed path, and pins the applicable UI subtree to the same total-project commit/path/version/hash identity as Product Baseline. Because a Slice covers UI, Integration, state, data, permissions, exceptions, recovery, and actor-visible results more completely, it may supplement, adjust, and improve Workflow on that inherited base under the existing Impact Analysis and `CONTROLLED_MUTABLE` rules. In Engineering Runs, a Slice proves a real UI operation through an API/MCP-backed Workflow capability, real state/data/side effect, and a visible UI result. Its applicable Simulation scenario traces the same capability, state, and exception behavior; Simulation is not required to be the production backend. Static UI, mock, stub, or manually staged state remains Product Formation evidence only and cannot prove third-phase integration, delivery readiness, or D0-D3 acceptance. Only affected connected layers and evidence update together.

```text
Actor intent
→ UI entry and interaction
→ integration boundary
→ Workflow capability
→ data/state/side effects
→ actor-visible result
→ evidence
```

A component, API, database table, service refactor, or test group is not by itself a Feature Slice.

One Feature Slice contract is canonical. Loop Run plans, verification receipts, status, and acceptance records reference its ID and version rather than copying its definition.

### 9.1 Execution coverage preflight

Before a Slice enters SLK, CLK, or GLK, its Execution Coverage Preflight must be `PASS`. Goal-backward coverage includes actor outcome, Product Baseline, Workflow, UI, Simulation, state/data/permissions, exception/recovery, Impact Analysis, Integration Baseline, Required Runs, D0–D3 evidence, and Loop Owner Acceptance. A missing claim, uncovered link, duplicate responsibility, or unresolved coverage unknown produces `BLOCKED`.

The same Preflight must trace the total project repository, full exact baseline commit, applicable UI subtree ID/path/component version/content hash and manifest scope, and a `MATCH` comparison before the Slice or Run. Product Handoff, Integration Baseline, and Slice must name one locked identity tuple—project repository/commit plus applicable UI subtree identity—and any mismatch blocks admission unless an approved Baseline Change Request replaced the tuple. Preflight also requires a before-acceptance comparison route.

For any `HIGH` or `UNKNOWN` Project Fingerprint factor, the Slice records either deeper evidence or smaller independently verifiable Run boundaries. `recommended_loop` remains topology-only.

When a required cross-layer connection lacks trustworthy proof, the first Required Run is the thinnest production-quality proving path through one real end-to-end scenario. It is not a prototype or new task type. Its failure blocks expansion. Existing sufficient proof may be cited instead with a no-new-Run rationale.

## 10. Feature Integration and baseline lock

Before implementation, the active Feature Slice freezes an `INTEGRATION_BASELINE`:

```text
UI = LOCKED
Workflow = CONTROLLED_MUTABLE
Simulation = VERSIONED_MUTABLE
Calabash = LIVING_WITH_IMPACT_TRACE
```

Integration is a convergence phase, not a new design phase. AI must make the Workflow and engineering implementation reach the accepted UI across every required actor surface.

`UI = LOCKED` is not a textual declaration. It is one-way Owner authority: the Owner may initiate or explicitly approve a UI change, while Workflow, Simulation, integrations, Loops, Agents, runtimes, automation, and all other system actors must not autonomously modify a locked UI. `INTEGRATION_BASELINE` pins the total project repository/exact commit and the applicable UI subtree ID/path/component version/content hash without ambiguity and must match the Product Handoff identity tuple; a branch, tag, `HEAD`, working tree, worktree, design link, screenshot, export, or `latest` is not an immutable reference. Here `subtree` means a logical product path, not Git's external-repository subtree mechanism.

Before a Feature Slice or engineering Run starts, and again before acceptance, AI compares the current applicable UI subtree with the locked total-project commit and subtree content hash. A difference without Owner initiation or approval evidence blocks work or acceptance. Preserve the difference evidence and isolate it without changing the authoritative UI; AI must not silently overwrite user material, automatically restore it, or replace it.

A UI change requires the existing `BASELINE_CHANGE_REQUEST`, an impact delta, alternatives, and Owner approval. An Owner-initiated or Owner-approved request must explain why preservation is impossible, create a distinct total-project commit, update the affected UI subtree component version and content hash, update Product and Integration Baseline references to the same new identity, and re-verify affected evidence. Routine data binding, declared responsive behavior, accessibility metadata, and exact restoration of accepted UI do not require an unlock.

## 11. Impact and reuse analysis

Before a material change, AI creates one Impact Analysis covering the affected Calabash, Workflow, UI, Simulation, Feature Slices, shared capabilities, data, Verification, Loop plans, release, and rollback.

Downstream stages reference and update that analysis by delta. They do not recreate a full impact report unless scope, baseline, or architecture changes materially.

Product learning may be blank. Return it only when it changes a future decision, constraint, check, template, or evidence-reuse rule, and update one existing canonical artifact. LCCoding does not create a retrospective phase, learning repository, learning directory, or mandatory learning document.

Shared-capability search is performed once per Slice/Run and repeated only when dependency scope changes.

## 12. Cross-Phase Execution Methods

Any bounded work item in `INITIAL`, `PRODUCT_FORMATION`, `ENGINEERING_RUNS`, or `DELIVERY_PREPARATION` may use one or more Runs. Every Run has a fresh Run Supervisor and defines its LCCoding phase scope, phase-owned objective, authoritative phase contract, Run Scope, Run Feature, evidence return target, and acceptance conditions.

Workflow, UI, and Simulation are built separately during Product Formation, even though Owner meaning, Calabash, and shared scenarios create limited coordination. Their tight connection and integration testing belong to the real product integration phase.

LCCoding selects the lightest truthful method:

- **SLK**: one coherent serial execution stream;
- **CLK**: fixed Chains with ordered Stages and full synchronization barriers;
- **GLK**: a real GO-to-GO execution graph with free dependency structure.
- **another registered execution method** when its contract fits the bounded work better.

SLK, CLK, and GLK are important but not exhaustive. Another registered method is eligible only when it supplies a compatible evidence and acceptance interface for the calling LCCoding work contract. Selection is reassessed only when evidence proves the current topology invalid. LCCoding does not run several Loop methods inside one Run or duplicate their internal governance. Separate Runs may select different methods.

The calling phase owns the phase-owned objective, product meaning, required outcome, acceptance boundary, and phase gate. It hands the selected method only phase-appropriate frozen authority and inputs. Before Product Baseline this may be Owner statements, Proposal Readiness, Project Initialization, Calabash Draft, scenarios, or one product-end contract. Product Integration supplies the ready Slice, candidate/baseline, Integration identity, Required Run scope, and related conditions. Delivery Preparation supplies the accepted candidate, security finding, delivery decision, or package contract. The selected method exclusively owns GO/CELL, Chain/Stage/graph, task, retry, and execution topology details.

The method returns evidence to the calling phase. Completing or accepting a Run does not advance a phase; the phase gate advances only after all of its own required conditions are proved.

## 13. Verification architecture

Verification is evidence-driven and intentionally non-duplicative.

### D0 — Worker Self-Check

Question: did the implementation behave as the Worker intended inside the assigned work?

D0 is feedback, not acceptance.

### D1 — Checker CELL Acceptance

Question: does the immutable CELL candidate satisfy its frozen local contract and scope?

D1 is independent from Worker and does not prove the GO outcome.

### D2 — GO Verification

Question: do accepted CELLs compose into the declared GO outcome?

D2 is issued by the selected Loop standard's independent Verification authority/attempt. It must not be authored by the Worker, the CELL Checker, or the Run Supervisor. It consumes D0/D1 receipts and adds GO composition, outcome, and affected-regression evidence.

### D3 — Stage / Run / Final Verification

Question: do verified GO/Run results compose into the complete Stage, Run, or Feature claim?

D3 uses a fresh independent Verification context appropriate to the selected Loop. It does not inherit the Worker's implementation context or the Checker's acceptance conclusion. The Supervisor provisions the attempt and consumes the verdict, but cannot author it. D3 adds only cross-GO, cross-Run, end-to-end, locked-UI, invisible-system, and final-candidate evidence.

### Evidence inheritance

A higher layer reuses a lower receipt when:

- artifact/candidate identity is unchanged;
- contract version is unchanged;
- environment relevant to the claim is unchanged;
- evidence is current and complete;
- the lower layer had authority for that question;
- no contradictory evidence exists.

### Permitted repetition

A check may repeat only when:

- the candidate changed;
- evidence is stale, missing, or contradictory;
- the environment materially differs;
- composition can change the result;
- broader affected regression is required;
- a named security, migration, branch, join, fallback, cycle, concurrency, or recovery risk requires it.

Every repeated check records source layer, reason, scope difference, risk, and result.

### Feature-level promotion

If one Run D3 receipt covers the exact Feature Slice claim, candidate, UI baseline, and scenario pack, LCCoding promotes that receipt after identity and coverage checks; it does not rerun the technical suite.

If a Slice spans multiple Runs, final Verification tests only the seams, uncovered claims, and integrated actor journey.


## 13.1 Loop Owner Acceptance

Every normal SLK, CLK, or GLK Run keeps its own human acceptance boundary.

```text
Run D3 PASS
→ LOOP_OWNER_ACCEPTANCE_READY
→ Supervisor-guided Loop Owner Acceptance
```

The Owner accepts each completed Run while its scope and context are small. A Feature Slice that requires several Runs therefore produces several incremental acceptance receipts rather than one large late review.

Valid results:

```text
LOOP_OWNER_ACCEPTED
LOOP_PRODUCT_REWORK
LOOP_PRODUCT_DEFINITION_CHANGE
LOOP_OWNER_DEFERRED
```

Only after every required normal Run is accepted may LCCoding issue `ALL_REQUIRED_RUNS_ACCEPTED` and freeze the aggregate accepted candidate.

### Owner gap closure lineage

Any `LOOP_PRODUCT_REWORK`, `LOOP_PRODUCT_DEFINITION_CHANGE`, or `LOOP_OWNER_DEFERRED` creates a stable Owner gap ID linked to its source Acceptance, candidate, and scenario. Product rework routes through existing Impact Analysis and a correction Run; product-definition change routes to Calabash and returns through the normal baseline/Slice path; deferred gaps remain open.

A gap closes only after the new candidate has the affected D0–D3 evidence, delta re-verification, and delta Owner re-acceptance. The authoritative status indexes open gap IDs and evidence pointers only; full lineage stays in existing Acceptance, Impact Analysis, Run handoff, and receipts. A blocking open gap prevents `ALL_REQUIRED_RUNS_ACCEPTED`. Post-Security findings remain in the centralized security-remediation and Post-Security Owner Acceptance path.

## 13.2 Centralized Vulnerability Audit and Closure

Formal vulnerability assessment is centralized and begins immediately after `ALL_REQUIRED_RUNS_ACCEPTED`.

### Independent auditor

The Security Auditor must use a fresh isolated Agent context and workspace and must not have participated as Worker, Checker, GO/Stage/Run/Final Verifier, Run Supervisor, Loop acceptance preparer, or remediation implementer for the candidate.

The auditor discovers and verifies vulnerabilities. Separate engineering roles perform remediation.

### Procedure

1. Freeze the aggregate candidate and load all Loop Owner Acceptance receipts.
2. Build one complete declared attack-surface coverage map.
3. Reuse current D0–D3 security evidence where it answers the identical security question.
4. Execute every missing check required for complete coverage.
5. Produce a centralized Security Audit Report and finding ledger.
6. Route findings to bounded Security Remediation Runs.
7. Invalidate and restore only engineering evidence affected by remediation.
8. Security Auditor performs independent re-audit.
9. Issue `VULNERABILITY_CLOSURE_RECEIPT`.

The initial audit is coverage-complete for the final accepted candidate, not merely a changed-file scan. D0–D3 may include local security assertions, but they do not replace the centralized verdict.

`VULNERABILITY_CLOSED` requires zero open Critical/High findings, secret exposure, authentication bypass, privilege escalation, cross-customer/tenant data leakage, incomplete coverage, or auditor-independence violation.

## 14. Post-Security Owner Acceptance

Security remediation changes the final candidate, so a second Owner Acceptance is required after `VULNERABILITY_CLOSED`.

This acceptance is distinct from Loop Owner Acceptance and is deliberately narrow:

- reuse all `LOOP_OWNER_ACCEPTANCE_RECEIPT`s;
- review only UI/Workflow surfaces and Feature behavior changed by remediation;
- run one or more critical smoke paths;
- confirm final candidate identity and security closure;
- do not repeat unchanged prior product acceptance.

If no remediation changed the candidate, the Owner may perform a minimal identity and critical-route confirmation.

Valid results:

```text
POST_SECURITY_OWNER_ACCEPTED
POST_SECURITY_PRODUCT_REWORK
POST_SECURITY_OWNER_DEFERRED
```

Delivery preparation cannot continue until `POST_SECURITY_OWNER_ACCEPTED`.

## 15. Delivery

Delivery packages the Post-Security Owner-accepted product without exposing the internal LC development system. Delivery begins only after the customer-specific Delivery Method Q&A is complete and `DELIVERY_READY` has been issued.

### 15.1 Delivery Method Q&A

Every customer delivery is separately confirmed. Default or recommended settings must never be applied silently.

AI first loads Owner Policy, Project Profile, the accepted candidate, customer contract/material, and prior decisions. It then asks only unresolved customer-specific questions. Each question provides a recommended answer plus concise single-choice or multiple-choice options, and every answer is written immediately into `DELIVERY_DECISION`.

The Q&A confirms, as applicable:

- delivery model and hosting responsibility;
- included and excluded assets;
- source access, modification, deployment, transfer, and derivative rights;
- runtime, infrastructure, network, and offline/online constraints;
- data migration, ownership, backup, retention, and deletion;
- how internal dependencies such as LCagent and LCapi are consumed without being delivered;
- license term, seats/sites, activation, updates, support, and maintenance;
- credentials, launch, rollback, handover, and post-delivery operations.

Owner Policy may contain locked non-deliverable assets and prohibited rights. Those restrictions constrain the Q&A and are not presented as ordinary customer options. Ubuntu and no-source delivery are recommendations unless Owner Policy locks them or Owner confirms them for this customer.

Required delivery artifacts:

- Delivery Profile;
- Dependency Classification;
- Delivery Manifest;
- Runtime Certification;
- Delivery License Policy;
- Delivery Receipt.

Default internal/excluded components include LCagent, LCapi, LCCoding, Calabash, SLK, CLK, GLK, Project Intelligence tooling, Canonical assets, internal knowledge/workflow/recommendation logic, and development evidence.

Source code is excluded unless Owner explicitly authorizes it. Ubuntu is the preferred certified customer runtime. Docker is not required.

Delivery verification checks package integrity, exclusions, runtime, license binding, configuration, and startup. It reuses product Verification and does not rerun it unless packaging changes runtime behavior.

## 16. Version governance

```text
Initial NEW project version: 0.0.1
EXISTING project version: preserve the declared version; record UNKNOWN rather than invent one
Small upgrade: commit only; no version bump
Medium upgrade: 0.0.2, 0.0.3, ...
Large upgrade: 0.1.1, 0.2.1, ...
1.0.1 or above: explicit Owner authorization required
```

AI may recommend and prepare a version, but may not promote to a restricted version without Owner authority.

## 17. Friction control

LCCoding minimizes:

- internal friction: repeated reasoning, planning, testing, Agent conflict, context drift, redundant artifacts;
- external friction: repeated Owner questions, scans, network calls, model calls, tools, tokens, and handoffs.

Friction reduction never authorizes deletion of Workflow, UI, Simulation, Mandatory Calabash Upgrade, independent Verification, Owner Acceptance, or Delivery protection.

Friction reduction also requires reuse of sufficient evidence and proportional depth. It never authorizes shallow treatment of real risk or empty artifacts that merely imitate the mainline.

## 18. Built-in BI projection

LCCoding may ship a built-in, read-only BI projection as an Owner-visible cognition surface. It must preserve the canonical four-phase identifiers and may show fine-grained milestones, states, artifacts, and protected subreports without becoming a second status authority.

The 2.6.0 desktop surface keeps the compact standalone Windows window, 300×480 logical content baseline, English-first text, complete Chinese switch, and native Pin control. Pin may change only the actual window's always-on-top state and must confirm the host result. One current-user installation serves every project; projects contain no BI source or Node/Rust/Python build dependency.

The projection keeps the protected Product Baseline report on the existing `PRODUCT_BASELINE` step and the protected Execution Method Governance report on the compatibility `LOOP_RUN_D0_D3` step ID. That step is displayed as Real Product Integration proof; it does not place execution methods exclusively in Phase 3. Simulation, Workflow, and UI reports expose only sanitized plural-subtree and interface-completeness metrics. No phase, step, Gate, status field, lower-method authority, or control action is added.

CLI `lccoding-bi.exe --project <root>` and the native Folder Picker use one Rust-owned root validation and immutable one-project binding. The read-only Rust adapter consumes only the canonical allowlist, validates published Loop contracts, and serializes a strict Snapshot that excludes paths, commit/hash/evidence bodies, raw errors, and thread identifiers. `get_snapshot` takes no path argument, refreshes are single-flight, and invalid or missing evidence fails closed to fixed errors, `UNKNOWN`, or `NOT_RECORDED`. The BI never writes project data or becomes a second authority; `status.json` remains authoritative.
