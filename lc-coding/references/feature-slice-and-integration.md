# Feature Slice and Integration

The Feature Slice contract is the canonical product claim for the increment. Run plans and receipts reference it.

## Readiness

A Slice must have:

- Product Baseline trace;
- actor and outcome;
- Workflow/UI boundaries;
- scenario pack;
- shared-capability result;
- material impact analysis;
- Integration Baseline;
- completion and acceptance criteria.

It must also pass Execution Coverage Preflight before Loop execution. The preflight checks the product claim end to end: actor outcome, Baseline, Workflow/UI/Simulation, state/data/permissions, exceptions/recovery, Impact Analysis, Integration Baseline, Required Runs, D0–D3, and Owner Acceptance. It does not define GO/CELL, tasks, waves, retries, or other Loop internals.

`HIGH` or `UNKNOWN` complexity must deepen evidence or reduce the Run boundary. When cross-layer wiring is not already proved, the first Required Run is a thin production-quality E2E proving path and expansion halts on failure. Trustworthy existing proof may be cited instead.

## Integration

Implement one visible vertical path at a time. Enabling work is attached to the Slice but does not count as product progress until consumed by the path.
