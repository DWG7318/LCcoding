# Project Initialization

Initialization establishes a durable enterprise project environment before product implementation.

Use one project Git/GitHub repository by default. Initialization records that total repository but does not pre-create empty UI, Workflow, or Simulation product subtrees. Real product units appear later as logical subtrees inside the repository. A worktree is optional for parallel construction or environment isolation; it is never a permanent product asset, subtree identity, or baseline.

## Modes

`NEW` initializes a new project and starts its project version at `0.0.1`.

`EXISTING` admits a half-complete, near-complete, claimed-complete but unattested, dormant, or redirected engineering project. It is a mode of Project Initialization, not a lifecycle or mainline branch.

Existing mode:

- freezes and records the current repository, Git HEAD, declared version, materials, and candidate before engineering;
- preserves history and verified assets and never resets the project to `0.0.1`;
- treats every inherited completion statement as `CLAIMED_UNATTESTED`, never as LCCoding completion evidence;
- asks the Owner for `CONTINUE`, `NARROW_REDIRECT`, `HOLD`, or `TERMINATE` before engineering; AI supplies facts but does not optimize the Owner's product or commercial direction;
- uses runnable UI as the first Owner-visible cognition anchor, not proof of completion;
- reconstructs Workflow, state, data, permissions, failure, and recovery from visible entries and independently evidences invisible behavior;
- reuses evidence only when identity, scope, environment, authority, and currency remain valid; unknown remains unknown;
- turns only real gaps into the existing Feature Slice and SLK/CLK/GLK Run path.
- inventories historical material and evidence without overwriting it, reconstructs the product mainline, and records every unresolved fact as unknown or blocker;
- outputs only `READY`, `BLOCKED`, or `NOT_CONTINUING`. `READY` requires a frozen repository/version/candidate, completed inventories, evidenced attestation, reconstructed mainline, a continued-project classification, and no takeover blocker.

Project Health classifies the result as `ATTESTED_COMPLETE`, `NEEDS_GAP_CLOSURE`, `PARTIAL`, `DIRECTION_CHANGED`, or `NOT_CONTINUING`. Continued work then follows the unchanged LCCoding mainline.

`status.json` is the single authoritative durable project status. Project Health supplies assessment evidence. `PHASE-STATUS.json` is a derived navigation view and must be reconstructible from status. These artifacts never own runtime, session, process, Agent, queue, retry, model, hook, or orchestration state.

## Required once

- one project Git and GitHub repository;
- Owner-confirmed visibility;
- initial version and commit for NEW, or preserved version and Git history for EXISTING;
- Agents Rule;
- skills and capabilities;
- canonical versions/hashes;
- Owner Policy, Project Profile, Fingerprint, and Health.

## Revalidation triggers

Repeat only the affected check after:

- repository identity/visibility change;
- skill version/hash change;
- Agent platform change;
- tool/capability availability change;
- credential/permission change;
- architecture or language change affecting intelligence tools.

Do not rescan every tool and skill on every project entry.
