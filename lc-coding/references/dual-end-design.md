# Workflow and UI Dual-End Design

Workflow and UI are equal product ends.

After at least one Simulation World foundation exists, Workflow and UI advance independently and may proceed concurrently. A project may contain multiple UI, Workflow, and peer Simulation logical subtrees inside one project repository. Each realized subtree has its own component version and content hash and must become independently runnable and inspectable; plans, shells, or mocks do not qualify. Cross-layer connection is not an early Product Formation condition and remains for Feature Slice and UI-locked Integration. Product meaning and scenario identifiers still synchronize through Map IDs.

Workflow defines capability, state, rules, authority, side effects, failure, and recovery.
UI defines every actor-facing entry, action, state, feedback, permission, and accepted visual result.

Each CORE Workflow and implemented EXTRA Workflow directly exposes both API and MCP contracts backed by the same capability. This does not create a Workflow Core layer, mandatory microservice, runtime, or deployment topology. Use IDs and traces rather than directory nesting or copied definitions; UI-to-Workflow and Simulation-to-Workflow relations may be many-to-many.

Select one Owner-confirmed Primary product mainline spanning at least one Simulation, one CORE Workflow, and one UI to set the first proving direction. Other CORE lines remain mandatory.
