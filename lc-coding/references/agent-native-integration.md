# Agent-native integration

This focused explanation summarizes the existing Agent-native method mechanics. SPEC.md is the sole complete semantic authority; this page is navigation and operator context, not a second specification, and it does not describe Runtime implementation.

<a id="agent-classes-and-applicability"></a>
## Agent classes and applicability

Source clauses: [LC-AGENT-001](../../SPEC.md#lc-agent-001)

A Construction Agent builds or verifies the product and never becomes delivered Agent state. Calabash classifies a Product Agent as `APPLICABLE_CORE`, `APPLICABLE_EXTRA`, or `NOT_APPLICABLE`; an Operations Agent is present in every 2.8 project. Applicable Product and Operations Agents remain distinct logical Agents.

<a id="configuration-authority-and-runtime-neutrality"></a>
## Configuration authority and Runtime neutrality

Source clauses: [LC-AGENT-002](../../SPEC.md#lc-agent-002)

Configuration authority flows from Owner decision through Calabash definition, LCCoding construction, independent Verification, Owner acceptance, and mechanical loading by an authorized Runtime Adapter. The accepted configuration is versioned, hash-bound, Runtime-neutral, and reference-only for secrets.

<a id="dual-agent-isolation-and-typed-events"></a>
## Dual-Agent isolation and typed events

Source clauses: [LC-AGENT-003](../../SPEC.md#lc-agent-003)

Product and Operations Agents keep separate identity, session/context, private memory, retriever/vector boundary, credentials, prompts, Policy, Action Catalog, audit, and Kill Switch. Their only cross-Agent communication is minimal, typed events with Policy checks, redaction, provenance, and audit; natural-language messages do not convey administrator authority.

<a id="topology-slices-and-shared-baseline"></a>
## Topology, Slices, and shared baseline

Source clauses: [LC-INTEG-004](../../SPEC.md#lc-integ-004)

The production topology exhaustively resolves discovered services as `SELECT`, `COMPOSE`, `FEDERATE`, or `RETIRE` while retaining explicit behavior, state, data, identity, permission, consistency, recovery, and calling authority. `PRODUCT` and `OPERATIONS` Feature Slices prove their distinct real routes and converge on one shared Integration Baseline for the candidate.

<a id="security-degradation-replacement-and-delivery"></a>
## Security, degradation, replacement, and Delivery

Source clauses: [LC-SEC-003](../../SPEC.md#lc-sec-003)

Agent attack surfaces, isolation, degradation, fallback, rollback, recovery, Kill Switch, audit, model or Adapter drift, and replacement remain bound to current candidate evidence. Changed identities invalidate affected proof; Delivery consumes the current security, Runtime Adapter, responsibility, recovery, and package-protection evidence without shipping private Agent state.
