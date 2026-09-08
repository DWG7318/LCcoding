# Proposal Readiness Check

PRC reads the Owner's existing proposal once, first tests whether the full LCCoding lifecycle fits the proposed engineering object, and then tests whether an admitted scope can support a meaningful Calabash Draft. Applicability judges method fit, not project value or technical merit.

## Applicability evidence

Record explicit `true` or `false` evidence for these six facts:

1. `human_beneficiary`: an identifiable human beneficiary or authorized representative.
2. `complete_journey`: a complete product or service journey from intent to an observable outcome.
3. `real_workflow`: business Workflow with actors, rules, state changes, effects, and recovery.
4. `actor_facing_surface`: an actual UI, result, Agent-service, CLI, or assisted-service surface.
5. `integration_need`: a reason to join the surface, Workflow, Simulation, and Backend/Core as a delivered product.
6. `real_acceptance_entry`: a feasible acceptance path from a real promised entry to a human-observable outcome.

Also record `bounded_product_scope`: `true` when the supplied facts describe one complete product-facing scope inside a larger engineering object, otherwise `false`.

When all six fit facts are true, recommend `WHOLE_PRODUCT_FIT` or `BOUNDED_PRODUCT_FIT` according to that scope decision. When complete evidence shows one or more required fit facts are false, recommend `OTHER_METHOD_RECOMMENDED` for use of the full method and explain that the underlying project is not rejected. Missing, non-boolean, or conflicting evidence issues no recommendation: keep `PROPOSAL_INCOMPLETE` and ask a focused question for each unresolved fact.

The legacy `status` reports proposal evidence completeness only; `applicability_recommendation` controls LCCoding admission. `PROPOSAL_READY` alone never admits a scope. `OTHER_METHOD_RECOMMENDED` is terminal for the LCCoding assessment, requires no service-strategy discussion, and recommends a component-focused or otherwise scope-appropriate engineering approach without stopping the underlying project.

After an admitted recommendation, load [Service Topology](service-topology.md) for the Initial product service strategy discussion. Do not require that reference merely to collect missing applicability facts.

## One-pass method

1. Index all supplied material.
2. Mark present, conflicting, uncertain, and missing topics.
3. Rank only gaps that block product definition or create material risk.
4. Ask one focused question at a time, with a recommended answer and concise alternatives.
5. Persist the answer immediately.
6. Never ask a settled question again unless new evidence contradicts it.
7. Recalculate readiness from the same record.

PRC does not optimize the business plan or replace Owner judgment.
