# LCCoding BI GitHub Windows Release Design

**Status:** Owner-approved release-channel design.

## Purpose and boundary

LCCoding 2.5.0 needs one auditable GitHub Actions path that builds the formal Windows BI assets on the exact reviewed `main` commit. The channel changes release automation only: it does not change React, Rust, BI behavior, lifecycle semantics, Loop identities, tags, Releases, or existing assets.

The workflow is manually invoked with `workflow_dispatch` and has only `contents: read`. It accepts no project or release input, runs only on `windows-latest`, and fails unless the selected ref is `refs/heads/main`, checkout `HEAD` equals `github.sha`, the worktree is clean, and `VERSION` is `2.5.0`.

## Build and evidence flow

1. Checkout `${{ github.sha }}` with full Git identity on the selected `main` ref.
2. Select Python 3.12, Node 24, and Rust 1.96.0 without installing Docker or another runtime.
3. Run repository validation, all Python tests, the NSIS packaging contract, release-integrity, and the production SLK/CLK/GLK release verifier.
4. Set `GH_TOKEN=${{ github.token }}` only for read-only GitHub release verification and invoke `package-release.ps1` without candidate or dirty flags. `OutputRoot` is the fixed external directory `$RUNNER_TEMP\lccoding-bi-formal`.
5. Require the release directory to contain exactly `LCCoding BI_2.5.0_x64-setup.exe`, `installer.sha256`, and `provenance.json`. Verify the PE header, checksum, exact source commit, `FORMAL_GITHUB_ACTIONS` mode, workflow/run/repository/ref identity, Windows target triple, and verified Loop dependency proof.
6. Upload only those three files as one immutable run artifact. Missing or extra files fail the job.

The workflow never runs `git push`, creates or moves a tag, creates or edits a GitHub Release, or uploads to an existing Release. A failed run leaves only its failed Actions record.

## Release sequence

After this workflow candidate is independently accepted, the reviewed feature branch may fast-forward into `main`. Dispatch the workflow on that exact `main` commit, wait for success, download the run artifact, and independently verify provenance, SHA-256, NSIS installation, source-free launch, 300×480 behavior, project immutability, and uninstall cleanup. Only then create the new annotated `v2.5.0` tag and the new GitHub Release with the verified three-file asset set. Existing tags, Releases, and assets remain untouched.

## Failure and security rules

- A non-main dispatch, SHA mismatch, dirty checkout, wrong version, unavailable Loop Release, identity mismatch, build failure, provenance mismatch, extra asset, or checksum mismatch fails closed.
- The job has no write permission and no release-creation step.
- The GitHub token is exposed only to the formal package step and is used by the existing read-only verifier.
- All build dependencies and artifacts stay under GitHub runner-managed directories; no build output is committed.

## Verification

A repository contract test mechanically rejects non-manual triggers, non-Windows runners, in-repository output, candidate flags, missing build identity checks, incomplete or broad artifact upload, write permissions, and any tag/Release mutation command. Existing Python, hash, repository, formal dependency, diff, secret, physical-file-set, and clean-worktree gates remain mandatory.
