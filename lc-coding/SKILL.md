---
name: lc-coding
description: Use when an Owner wants to direct AI or coding agents through an Owner-led product-development method; when Calabash, Workflow, multi-role UI/product surfaces, realistic simulation data, vertical Feature integration, impact analysis, AI Verification, Owner Acceptance, global consistency, convergence, or SLK/CLK/GLK execution must be coordinated without losing product direction.
---

# LCCoding

## Canonical Identity

- Product name: `LCCoding`.
- Skill invocation: `$lc-coding`.
- Skill folder: `lc-coding/`.
- Intended repository: `https://github.com/DWG7318/LCcoding`.
- Current specification version: `1.1.1`.
- Version source: repository `VERSION` file.

LCCoding is an Owner-led, AI-executed product-development method. It is a Human–AI
working contract, not a coding framework, Agent runtime, architecture pattern, test
framework, or replacement for Calabash, SLK, CLK, or GLK.

## Core Formula

```text
Calabash first and continuously living
                ↕
Workflow end  ← Feature Integration →  UI / surface end
                ↕
          Simulation world
                ↓
 AI Verification + Owner Acceptance
                ↓
 Impact Analysis + synchronized evolution
```

- `Calabash` is the product-definition axis.
- `Workflow` is the capability end.
- `UI` is the actor-facing product surface end.
- `Simulation` makes the product world observable before production reality exists.
- `Feature Integration` connects one actor-visible capability through every required
  layer.
- `AI Verification` proves the implementation satisfies the frozen claim.
- `Owner Acceptance` decides whether the product experience and definition are right.
- `Impact Analysis` lets the product change quickly without losing consistency.

Read `references/method-architecture.md`.

## Principle Zero — Human Decides, AI Completes The Engineering Loop

The Owner is the authority for:

- product direction and value judgment;
- Workflow intent and business behavior;
- UI/UX direction and accepted visual result;
- material scope and trade-off decisions;
- final product experience and Owner Acceptance;
- approval of material Calabash amendments.

AI is responsible for:

- evidence and source analysis;
- ambiguity detection and recommended options;
- planning and Feature Slice decomposition;
- Simulation World construction and maintenance;
- shared-capability and reuse analysis;
- impact analysis before material change;
- integration, implementation, debugging, and regression;
- AI Verification and evidence collection;
- Calabash, documentation, status, and trace synchronization;
- identifying affected prior work and executing approved updates.

AI must recommend a best answer when a material decision is unresolved, but must not
silently replace Owner product authority.

Routine technical decisions inside the frozen contract do not require Owner
confirmation. Generic prompts such as “please confirm the code,” “please check the
logs,” or “should I fix this ordinary defect?” are invalid escalation.

Read `references/human-ai-contract.md`.

## Required Project Artifacts

Every active LCCoding project keeps:

```text
.calabash/                         # authoritative product definition and lineage
.lccoding/
  WORKING-CONTRACT.md              # project-specific Human–AI contract
  PROJECT-START.md                 # project identity, profile, constraints
  WORKFLOW-MAP.md                  # capability end
  UI-MAP.md                        # actor-facing product surfaces
  SIMULATION-WORLD.md              # realistic product world
  SHARED-CAPABILITIES.md           # reusable capability registry
  status.json                      # current project navigation state
  status.html                      # lightweight visible status page
  slices/
    INDEX.md
    <slice-id>.md
  impact/
  evidence/
  observations/
  reviews/
  release/
```

The exact implementation may add files, but these meanings must remain visible.

## Project Start Gate

Before implementation:

1. Read `WORKING-CONTRACT.md` if it exists.
2. Find or establish the current Full or Minimum Calabash baseline.
3. Choose the LCCoding complexity profile.
4. Create the Workflow Map and UI Map at the level needed for the first product
   increment.
5. Establish the Simulation World and at least one realistic scenario pack.
6. Create the Feature Slice Index.
7. Select one first end-to-end slice that can visibly prove direction.
8. Create or refresh `status.json` and `status.html`.
9. Run cross-artifact consistency analysis before implementation.

If product-affecting work has no valid Calabash baseline, stop implementation and
establish one. A narrow technical task may use a Calabash exemption only under the
rules of the active Calabash method.

## Complexity Profiles

Choose the lightest profile that preserves product clarity.

### EXPRESS

Use for a narrow, already-defined change with one clear user behavior and no material
product-definition ambiguity.

Required minimum:

- frozen Calabash trace or valid exemption;
- one Feature Slice;
- focused Simulation scenarios;
- impact and reuse checks;
- AI Verification and Owner Acceptance when actor-visible.

### PRODUCT

Default for a product feature, multiple UI states, or a Workflow with meaningful
business behavior.

Requires all standard LCCoding artifacts, global review triggers, and a versioned
Simulation World.

### SYSTEM

Use when several roles, modules, Workflows, shared capabilities, or dependent product
areas are involved.

Requires formal traceability and an execution method appropriate to the structure:
SLK for one bounded execution stream, CLK for fixed Chains and Level barriers, or GLK
for a free GO Graph.

Complexity changes as evidence changes. Record profile changes before expanding work.

Read `references/complexity-profiles.md`.

## Calabash First, Calabash Always Living

A project begins from a frozen Calabash baseline, but the Calabash lineage evolves
throughout design, simulation, integration, and acceptance.

Confirmed product learning must be written through promptly:

```text
Owner decision or verified product learning
→ impact analysis
→ Calabash amendment or working definition update
→ affected Workflow/UI/Simulation/Slice updates
→ Git record
→ status refresh
```

Do not wait until a final review to update Calabash. Do not mutate the baseline
silently. Active implementation must identify the exact baseline or working revision
it follows.

Read `references/calabash-lifecycle.md`.

## Dual-End Design

Workflow and UI are two equal design ends.

### Workflow End

Define what the product can actually do:

- actors and authority;
- business states and transitions;
- inputs, outputs, data, and side effects;
- core rules and failure/recovery behavior;
- tool, device, model, and external-service constraints;
- reusable capabilities and boundaries.

### UI End

Define what each relevant actor sees and can accomplish. `UI` includes all product
surfaces, not only the customer/client interface:

- customer or client app surfaces;
- staff, operator, support, review, fulfillment, and finance consoles;
- administrator and configuration surfaces;
- notification, approval, audit, and status surfaces;
- role-specific entry points;
- pages, panels, states, and information hierarchy;
- action affordances and feedback;
- loading, empty, success, error, recovery, and permission states;
- accepted visual direction and protected UI scope;
- the visible completion of the actor's task.

Neither end may be treated as a decorative layer over the other.

An accepted UI is a protected product artifact. AI must not broadly redesign, restyle,
rename, or restructure accepted UI outside the active Feature Slice without a material
Owner decision and impact analysis.

Internal staff and administrator UIs are first-class product surfaces. If a Feature
depends on internal action, queue handling, approval, configuration, audit, or recovery,
those surfaces must be mapped, simulated, verified, and protected by the same rules as
customer-facing UI.

An accepted Workflow is also protected. AI must not change product behavior merely to
make implementation easier. Record `WORKFLOW_CONTRACT_CONFLICT` when the frozen
Workflow cannot be implemented as defined.

Read `references/dual-end-design.md`.

## Simulation World

Simulation is mandatory for product-facing work unless real, safe, representative
production-like data and actors are already available.

Simulation is not a random seed script or a test-only fixture. It is a versioned,
resettable product world containing enough realistic entities, roles, states, time,
volume, devices, tools, permissions, errors, and recovery paths to make Workflow and
UI observable.

A useful Simulation World covers, as relevant:

- normal cases;
- boundary cases;
- failure and recovery cases;
- role and permission differences;
- time progression and stale state;
- realistic data volume and density;
- device/tool availability and maturity;
- external dependency degradation;
- historical records and linked objects.

Every Feature Slice names the scenarios it uses.

Mocked or simulated success must be visibly distinguished from real integration.
A UI connected only to a stub cannot be accepted as a completed integrated Feature.

Read `references/simulation-world.md`.

## Product Progress Unit — Feature Slice

LCCoding measures progress in actor-visible, end-to-end capability slices.

A valid Feature Slice connects:

```text
actor intent
→ UI entry and interaction
→ integration boundary
→ Workflow capability
→ state/data/side effects
→ visible result
→ evidence
```

A Feature Slice is not merely:

- a button;
- a component;
- an API;
- a database table;
- a service refactor;
- a group of tests;
- a technical layer.

A slice must be small enough to implement, observe, and accept, but complete enough
that a real user or product operator can perceive meaningful progress.

Infrastructure work may be recorded as an enabling task, but it does not count as
product progress until consumed by a named Feature Slice.

Read `references/feature-slice-protocol.md`.

## Feature Slice Readiness Gates

Before implementation, every slice must pass:

### 1. Calabash Trace Gate

Identify the exact product claims, roles, Journey, Ontology, Workflow, and UI intent
that authorize the slice.

### 2. Clarification Gate

AI must identify ambiguity, missing states, contradictory artifacts, and unresolved
Owner decisions. Ask only material product questions that cannot be resolved from
verified evidence. Present concise options and one recommended answer.

### 3. Simulation Gate

Define the realistic scenario pack required to see and exercise the slice.

### 4. Shared Capability Gate

Search the capability registry and existing implementation before creating new
cross-cutting behavior.

### 5. Impact Analysis Gate

Identify all affected Workflow, UI, Calabash, Simulation, data, shared capabilities,
accepted slices, evidence, and regression surfaces.

### 6. Implementation Plan Gate

Specify exact scope, files or modules when knowable, protected areas, sequence,
verification commands, UI evidence, rollback, and completion criteria.

### 7. Consistency Gate

Cross-check Calabash, Workflow, UI, Simulation, slice specification, and plan. Resolve
contradictions before implementation.

## Integration Baseline Lock

Feature Integration is a convergence phase, not a second design phase. Before code
changes begin, the active Feature Slice must declare a frozen `INTEGRATION_BASELINE`.

The default lock policy is:

```text
UI = LOCKED
Workflow = CONTROLLED_MUTABLE
Simulation = VERSIONED_MUTABLE
Calabash = LIVING_WITH_IMPACT_TRACE
```

The UI is the default fixed target because it represents the Owner-approved actor-facing
outcome. During integration, AI must make the engineering and Workflow implementation
reach every locked role surface in that target rather than simplifying, redesigning,
renaming, deleting, or moving UI to reduce implementation difficulty.

Every locked baseline records:

- Feature Slice identity;
- accepted UI reference, Git commit, artifact path, or reproducible snapshot;
- baseline hash or immutable version identifier;
- locked and explicitly editable UI surfaces by actor and context;
- accepted interaction, content, and state behavior;
- Workflow contract and allowed controlled adjustments;
- Simulation scenario-pack version;
- Owner approval and lock time.

A locked UI may be changed only through `BASELINE_CHANGE_REQUEST`. The request must
state the technical or product reason, prove why the current target cannot or should not
be preserved, list affected accepted work, offer alternatives, and receive explicit Owner
approval. Until approval, implementation stops at the conflict rather than modifying UI.

Allowed without unlock:

- exact data binding and state wiring;
- accessibility attributes that do not change accepted behavior or appearance materially;
- declared responsive adaptations already covered by the accepted UI contract;
- correction of an obvious implementation defect that restores the accepted UI;
- changes inside an explicitly listed editable region.

Not allowed without unlock:

- layout restructuring, visual restyling, or component replacement;
- renaming labels, actions, or information architecture;
- removing states, actions, fields, or feedback;
- changing the interaction sequence;
- using a different UI because the original is harder to connect;
- hiding incomplete Workflow behavior behind altered UI.

After Owner Acceptance, the slice baseline becomes an accepted product reference. The
next design cycle may propose a new UI version, but prior accepted behavior remains
protected until impact analysis and approval produce a superseding baseline.

Read `references/integration-baseline-lock.md`.

## Isolated Implementation

Use a dedicated branch, worktree, or equivalent isolated workspace for material work.
Verify the clean baseline before changing files.

During implementation:

- one active slice per integration stream by default;
- no silent scope expansion;
- no unrelated UI cleanup;
- no duplicate shared capability;
- no bypass around the authoritative Workflow;
- no fake success hidden behind Simulation or mocks;
- no completion claim based only on tests or code volume;
- preserve accepted artifacts outside the declared impact scope.

Implementation tasks should be small, exact, and evidence-oriented. Each task must
identify what it changes and how its result contributes to the active slice.

LCCoding may delegate execution to SLK, CLK, GLK, or another agent workflow, but the
Feature Slice contract remains the product-level authority.

## AI Verification

AI Verification is independent of Owner Acceptance.

It proves the slice behaves according to its frozen contract through reproducible
evidence, including as relevant:

- UI screenshots or browser recordings;
- interaction and accessibility checks;
- Workflow transitions;
- persisted state and side effects;
- role and permission behavior;
- normal, boundary, failure, and recovery scenarios;
- API, event, audit, and data evidence;
- regression results;
- absence of disconnected UI, dead actions, or mock-only success.

Verification has two ordered reviews:

1. `PRODUCT_COMPLIANCE_REVIEW`: Does the result match Calabash, Workflow, UI,
   Simulation, and the Feature Slice claim?
2. `ENGINEERING_QUALITY_REVIEW`: Is the implementation safe, maintainable,
   consistent, performant enough, and free from material technical defects?

Engineering quality cannot compensate for failed product compliance.

Tests are evidence, not the definition of progress. Every added test must map to a
Feature Slice claim, shared-capability contract, regression risk, or release gate.

Read `references/verification-and-owner-acceptance.md`.

## Owner Acceptance

Owner Acceptance uses the running product and realistic Simulation scenarios.

The Owner judges:

- whether the UI communicates the right thing;
- whether the user journey feels right;
- whether the visible behavior matches product intent;
- whether the Workflow itself should change;
- whether new product learning should amend Calabash;
- whether the slice is accepted, requires rework, or reveals a definition defect.

Valid results:

```text
OWNER_ACCEPTED
OWNER_REWORK
OWNER_DEFINITION_CHANGE
OWNER_DEFERRED
```

Owner Acceptance is not code review. AI must present the smallest useful running
experience, evidence summary, and known trade-offs, not a wall of technical logs.

## Impact-Aware Evolution

Before any material change, AI produces an `IMPACT_ANALYSIS` that covers:

- Calabash clauses and version;
- Workflow states, rules, and side effects;
- UI pages, components, states, and visual baselines;
- Simulation scenarios and seed data;
- active and accepted Feature Slices;
- shared capabilities and consumers;
- data contracts and migrations;
- verification and regression evidence;
- SLK/CLK/GLK plans when used;
- release and rollback implications.

AI recommends the safest coherent change set. The Owner decides material product
changes. After approval, AI performs the deterministic synchronization work and
records what changed.

Fast Calabash evolution is not a defect. Untraced evolution is a defect.

Read `references/impact-analysis.md`.

## Shared Capability Governance

Before adding authentication, permissions, uploads, search, messaging, state,
notifications, audit, payments, files, model access, or any reusable behavior, AI
must inspect `SHARED-CAPABILITIES.md` and the existing implementation.

For each shared capability record:

- identity and purpose;
- authoritative contract;
- owner and implementation location;
- consumers;
- extension points;
- evidence and known limitations.

A Feature Slice may consume or extend a shared capability. It must not create a
private duplicate merely to finish faster.

## Global Consistency Review

Run a global review when any of these occurs:

- one coherent user journey has been completed;
- a material Calabash amendment affects prior work;
- a new role, module, Workflow, or shared capability is introduced;
- UI or Workflow drift is observed;
- the project changes complexity profile;
- before a milestone, release, or major handoff.

Review:

- product language and Ontology;
- UI patterns and information hierarchy;
- Workflow states and transitions;
- roles, permissions, and data ownership;
- shared-capability reuse;
- Simulation realism and coverage;
- accepted slice compatibility;
- unresolved observations and impact debt;
- Calabash trace freshness.

Read `references/shared-capability-and-global-review.md`.

## Systematic Debugging

When a slice fails:

1. reproduce it in a named Simulation scenario;
2. preserve evidence;
3. locate the failing boundary: UI, integration, Workflow, data, tool, environment,
   or specification;
4. trace the root cause before patching;
5. choose the smallest coherent fix;
6. rerun focused and affected regression evidence;
7. update Calabash or the slice contract when the definition was wrong.

Do not respond to repeated failure by adding arbitrary tests, speculative guards,
unrelated refactors, or UI workarounds.

## Convergence

A slice or project is not complete merely because tests pass.

Convergence requires proof that:

- the intended actor tasks complete end to end;
- UI and Workflow agree across every in-scope customer, staff, administrator,
  notification, audit, and status surface;
- realistic Simulation scenarios pass;
- no critical UI is empty, dead, misleading, or mock-only;
- shared capabilities remain coherent;
- accepted prior slices still work;
- Calabash and status records match current reality;
- Owner Acceptance is recorded for product-facing work;
- remaining gaps are explicit and intentionally deferred.

Use `CONVERGENCE_REPORT.md` before branch completion or release.

Read `references/debugging-and-convergence.md`.

## Navigation and Visible Progress

On every project entry, AI must read:

1. `WORKING-CONTRACT.md`;
2. current Calabash baseline and active amendment;
3. `status.json`;
4. active Feature Slice;
5. latest Impact Analysis and acceptance result.

The status surface must show:

- current product definition version;
- active Workflow area and UI area;
- active Simulation scenario pack;
- current Feature Slice and state;
- last accepted slice;
- next recommended action;
- blockers and impact warnings;
- latest Owner decision;
- global review and release status.

AI updates status after every material decision, implementation handoff, verification,
Owner Acceptance, Calabash amendment, or review.

The LCCoding status surface complements rather than replaces Calabash BI. Keep the
Calabash BI path visible so the Owner can see product-definition evolution beside
current delivery progress.

## Relationship To Loop Skills

LCCoding chooses the product increment and acceptance path. Loop methods may organize
execution.

### SLK

Use for one bounded execution stream implementing one or more sequential slices or
supporting tasks.

### CLK

Use when several fixed Chains can implement independently startable slices or domains
inside ordered Level barriers.

### GLK

Use when GO dependencies require conditional paths, partial unlock, joins, fallback,
or Grapher-controlled navigation.

A Loop result cannot override LCCoding Owner Acceptance or Calabash product meaning.
A completed GO that does not produce the active Feature Slice outcome is not product
completion.

Read `references/loop-method-integration.md`.

## Forty-Nine Hard Rules

1. LCCoding is an Owner-led working method, not an autonomous product authority.
2. Human product decisions and AI engineering duties must remain explicit.
3. Product-affecting work begins from a valid Calabash baseline.
4. Calabash evolves throughout work; confirmed learning is not postponed to the end.
5. Workflow and UI are equal design ends.
6. Accepted Workflow cannot be changed for implementation convenience.
7. Accepted UI cannot be broadly redesigned outside declared scope.
8. Product-facing work requires a realistic Simulation World or equivalent reality.
9. Simulated success must never be presented as real integration.
10. Product progress is measured by actor-visible end-to-end Feature Slices.
11. A component, API, table, refactor, or test group is not automatically a Feature Slice.
12. Enabling work does not count as product progress until consumed by a named slice.
13. Every slice must trace to Calabash.
14. Every slice must define Workflow and UI outcomes.
15. Every slice must name its Simulation scenarios.
16. Material ambiguity must be resolved before implementation.
17. AI asks only Owner-exclusive product questions and gives a recommended answer.
18. Routine technical work must not wait for Owner confirmation.
19. Shared-capability reuse is checked before new implementation.
20. Material changes require impact analysis before modification.
21. Cross-artifact consistency is checked before implementation.
22. Material implementation uses an isolated branch or workspace.
23. One active slice per integration stream is the default.
24. AI may not silently expand scope.
25. AI may not alter unrelated accepted UI.
26. AI may not bypass the authoritative Workflow.
27. AI may not duplicate a shared capability to finish locally.
28. Every implementation task must contribute to the active slice or a named enabler.
29. AI Verification and Owner Acceptance are distinct and both required when applicable.
30. Product compliance is checked before engineering quality.
31. Tests are evidence, not product progress.
32. Owner Acceptance is performed on a running experience with realistic scenarios.
33. Owner feedback may revise UI, Workflow, and Calabash.
34. AI synchronizes approved change impacts across all affected artifacts.
35. Fast iteration is allowed; untraced iteration is not.
36. Repeated defects require root-cause analysis, not random patching.
37. Global reviews are trigger-based, not postponed until project end.
38. Project status must remain visible and current.
39. Completion requires convergence, not merely green tests.
40. A Loop execution verdict cannot replace Owner product acceptance.
41. Every Feature Integration must declare an immutable Integration Baseline.
42. UI is locked by default during Integration.
43. UI includes customer, staff, administrator, notification, audit, and status surfaces when they are in scope.
44. Integration must adapt engineering and controlled Workflow details to the locked UI target.
45. AI may not reduce implementation difficulty by redesigning or simplifying locked UI.
46. Every baseline lock must identify immutable UI references and allowed editable scope by actor surface.
47. A locked-baseline conflict requires a Baseline Change Request, impact analysis, and Owner approval.
48. Unapproved locked-UI modification invalidates the implementation candidate and its acceptance claim.
49. A new design iteration supersedes an accepted baseline only through explicit versioning and traceable approval.

## Required Outputs

For a substantial project, produce or maintain:

1. project-specific Working Contract;
2. Calabash baseline reference;
3. Workflow Map;
4. UI Map;
5. Simulation World and scenario packs;
6. Shared Capability Registry;
7. Feature Slice Index and active slice contract;
8. Impact Analyses;
9. AI Verification evidence;
10. Owner Acceptance records;
11. Global Review records;
12. current status page;
13. Convergence Report and Git delivery record.

## Common Mistakes

- Treating LCCoding as a linear “Workflow then UI” process.
- Continuing to redesign UI after the Feature enters Integration.
- Building UI against empty or random data.
- Creating a polished UI that is disconnected from the real Workflow.
- Letting AI redesign accepted UI while “integrating.”
- Calling backend completion product completion.
- Counting tests, files, or commits as product progress.
- Splitting work by technical layer instead of actor-visible capability.
- Reusing mocks after the real integration should exist.
- Asking the Owner to approve routine technical actions.
- Updating one page without analyzing prior accepted slices.
- Changing Calabash without synchronizing affected artifacts.
- Using SLK, CLK, or GLK as a substitute for product advancement.

## Invocation Examples

```text
Use $lc-coding to bootstrap this project, establish or locate Calabash, map the
Workflow and UI ends, create a realistic Simulation World, and propose the first
end-to-end Feature Slice.
```

```text
Use $lc-coding to prepare the next Feature Slice. Run clarification, reuse, impact,
Simulation, consistency, and implementation-plan gates before changing code.
```

```text
Use $lc-coding to verify the active slice, present the running result for Owner
Acceptance, synchronize approved changes, and refresh project status.
```

```text
Use $lc-coding to run a global consistency review and produce a convergence report.
```
