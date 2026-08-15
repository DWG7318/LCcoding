# LCCoding BI Single-Build Formal Release Design

**Status:** Owner-approved architecture; this historical design awaits independent Supervisor review before an implementation plan may be written.

**Base:** LCCoding `2.8.0`, commit `164eb5b30c65121df8cd90fdce7d95f334c01f27`.

**Document role:** historical design provenance only. It does not change either workflow, implement CI behavior, authorize a tag or Release, deploy the global Skill, install BI, or create current release evidence.

## 1. Problem statement

LCCoding 2.8 has two individually valid but non-composable release paths:

- Validate run `31912966291` built and passed the real ephemeral-standard-user smoke with installer SHA-256 `3fecc16f0e7c7e1c11e6e55c4dedd94e376ec624be800295b2e490e80859b6cf`.
- Formal release run `31913444348` built installer SHA-256 `0df26207bb47bffddeb89fd2914f82b98095b90b201dd4253c3574b236fa0f3e` and did not run the standard-user smoke.

The two hashes differ. A successful smoke for one installer cannot prove a different installer safe, even when both builds use the same repository commit. Run `31913444348` is therefore rejected unpublished evidence. Its installer, checksum, and provenance must not be tagged, attached to a GitHub Release, or used as a formal LCCoding 2.8 asset.

The defect is architectural: formal publication and real installation proof do not share one artifact lineage. The release workflow must build once, smoke-test that exact installer byte-for-byte, and upload that exact same installer.

## 2. Locked decision

The later implementation must add exactly one repository-owned reusable Windows CI parent/orchestrator entry:

`lc-coding/bi/tests/packaging/run-standard-user-install-smoke.ps1`

That parent owns only host-side ephemeral-runner responsibilities:

1. create one temporary local standard user with a random in-memory credential;
2. resolve built-in Users and Administrators groups by well-known SID, require membership in Users exactly once, and require no Administrators membership;
3. grant the minimum ACLs needed for the checked-out repository, exact package directory, evidence directory, and smoke temporary root;
4. launch the child under the temporary user's loaded profile and credential;
5. require the child's real process result, SID, non-admin token, interactive session, exact PATH roundtrip, uninstall result, and zero-residue result;
6. collect bounded evidence; and
7. remove the temporary user and verify cleanup before returning PASS.

The parent must call the existing child:

`lc-coding/bi/tests/packaging/standard-user-install-smoke.ps1`

The child continues to call the original `lc-coding/bi/tests/packaging/install-smoke.ps1`. The implementation must not duplicate either existing script or move their semantic responsibilities into a workflow. The child remains responsible for standard-user-local repository/package preparation, source and provenance identity checks, baseline PATH construction, invocation of the original smoke, raw PATH/type comparison, and product residue evidence. The original smoke remains the product install, launch, window, interaction, uninstall, and source-immutability authority.

This extraction creates one reusable parent, not a general CI framework.

## 3. Workflow architecture

### 3.1 Validate workflow

`.github/workflows/validate.yml` must replace its large inline temporary-user parent orchestration with one call to `run-standard-user-install-smoke.ps1`.

Validate still builds and validates its own candidate package. It proves that ordinary pushes retain the real standard-user path. It is not the formal publication source, and its artifact must never be substituted for the formal release artifact.

### 3.2 Formal release workflow

`.github/workflows/release-bi.yml` must execute this exact fail-closed order:

```text
checkout exact main commit
→ validate repository and formal Loop dependencies
→ invoke package-release.ps1 exactly once into one new output root
→ validate the exact three files in that release directory
→ freeze installer absolute path, basename, and pre-smoke SHA-256
→ invoke run-standard-user-install-smoke.ps1 against that exact release directory
→ validate the parent and child PASS evidence and cleanup
→ re-hash the same absolute installer path
→ require post-smoke SHA-256 == pre-smoke SHA-256 == checksum == provenance SHA-256
→ upload the same three files from the same release directory
→ upload smoke evidence as a separate CI evidence artifact
```

The formal workflow may invoke `package-release.ps1` once and only once. It must not rebuild after smoke, copy another installer into the formal release directory, change the upload path after smoke, or use a Validate artifact as a formal input. The absolute installer path observed before smoke, after smoke, and by the formal three-file upload step must be identical.

The formal asset artifact remains exactly:

1. `LCCoding-BI_2.8.0_x64-setup.exe`
2. `installer.sha256`
3. `provenance.json`

Smoke evidence must be uploaded under a different artifact name and must never be included in the GitHub Release asset set.

## 4. Evidence contract

The reusable parent must emit one closed, atomic result bound to:

- `DWG7318/LCcoding`;
- the exact checked-out commit;
- workflow identity;
- workflow run ID and run attempt;
- installer basename;
- the formal release directory's exact absolute installer path;
- pre-smoke installer SHA-256;
- post-smoke installer SHA-256;
- child result identity and hash;
- child process exit code;
- standard-user SID, non-admin result, and interactive session result;
- raw PATH and registry-kind roundtrip result;
- uninstall parent exit code;
- preflight and postflight product residue results;
- temporary-user cleanup result; and
- overall result `PASS`.

The result must not contain the temporary password or raw user PATH value. The password may exist only in process memory and must not enter arguments, logs, artifacts, or environment persistence.

Missing evidence, an unknown or duplicate field, repository/commit/workflow/run/attempt drift, a wrong installer basename or path, a pre/post/checksum/provenance hash mismatch, a nonzero child or uninstall exit, an administrator token, a missing interactive session, a PATH mismatch, product residue, temporary-user cleanup failure, or any non-PASS result must prevent both formal artifact uploads. A later Release Cell must treat the absence of both the formal three-file artifact and its matching smoke evidence artifact as a hard block on tag or GitHub Release creation.

## 5. Security and environment boundary

All temporary-account activity must occur only on an ephemeral GitHub-hosted Windows runner. The implementation and release procedure must reject:

- local temporary-account creation;
- local UAC or elevation routes;
- Windows Sandbox;
- Docker or another container/VM substitute;
- use of the machine's persistent LCCoding BI 2.7 installation;
- local evidence substituted for `FORMAL_GITHUB_ACTIONS` provenance; and
- a smoke result copied from another run, attempt, commit, package directory, or installer hash.

The formal workflow's runner-admin process may perform the narrow account/ACL bootstrap. Product installation and the original smoke must execute under the child standard user's own token, HKCU hive, profile, and interactive session.

## 6. Non-goals and unchanged boundaries

This design does not change:

- the NSIS installer or `hooks.nsh`;
- `install-smoke.ps1` behavior or acceptance thresholds;
- the child `standard-user-install-smoke.ps1` semantic responsibilities;
- the exact three-file formal release contract;
- provenance meaning, formal Loop dependency verification, or package contents;
- the installed LCCoding BI 2.7 product;
- LCCoding lifecycle, Agent-native method semantics, BI UI, Runtime behavior, or Deployment Cell B; or
- tag, GitHub Release, or global Skill deployment authority.

No new Runtime, publication state, general CI abstraction, second installer builder, or alternate release channel is introduced.

## 7. Rejected alternatives

1. **Reuse the Validate installer as the formal release artifact.** Rejected because Validate is not the formal publication source and its provenance names a different workflow run.
2. **Accept equal commit identity when installer hashes differ.** Rejected because installation proof binds bytes, not source intent.
3. **Build again after smoke.** Rejected because the second installer would be untested.
4. **Copy another installer into the upload directory after smoke.** Rejected because it breaks the observed-path and byte lineage.
5. **Run the formal installer through a local temporary user, UAC, or Windows Sandbox.** Rejected because formal provenance and isolation belong to the ephemeral GitHub-hosted runner, and the local persistent BI 2.7 installation must remain untouched.
6. **Add a broad reusable CI framework.** Rejected because one narrow parent/orchestrator is sufficient.

## 8. Compatibility and migration

The later implementation is a release-pipeline correction after `164eb5b`; it does not reinterpret prior project evidence or modify the 2.7-to-2.8 project migration. Existing 2.7 release, tag, assets, installation, and compatibility support remain unchanged.

Validate evidence created before the correction remains evidence for its own installer only. Formal run `31913444348` remains rejected unpublished evidence and cannot be grandfathered; its successful workflow conclusion does not make its unsmoked installer releasable. A new formal run after accepted implementation must build once and produce new, run-bound package and smoke evidence.

## 9. Acceptance criteria

The implementation is acceptable only when mechanical tests and one real formal workflow run prove all of the following:

1. The formal workflow contains exactly one package build invocation.
2. Before smoke, after smoke, checksum validation, provenance validation, and formal upload all refer to the same absolute installer path.
3. Pre-smoke, post-smoke, checksum, provenance, and downloaded artifact SHA-256 values are identical.
4. Validate and formal release workflows both call the same reusable parent/orchestrator.
5. The parent calls the existing child, and the child calls the original smoke.
6. The smoke executes as an ephemeral non-admin standard user and returns an actual PASS.
7. Raw PATH/type restoration, uninstall, product residue, and temporary-user cleanup all PASS.
8. The formal artifact contains exactly three files, while the run uploads one separate smoke evidence artifact.
9. A failing or missing smoke, a cleanup failure, an identity mismatch, or any hash drift prevents formal artifact upload and therefore blocks tag and GitHub Release creation.
10. Run `31913444348` remains untagged and unpublished.

This design produces one narrow implementation plan. It does not authorize that plan, workflow dispatch, tag creation, Release creation, installation, or deployment.
