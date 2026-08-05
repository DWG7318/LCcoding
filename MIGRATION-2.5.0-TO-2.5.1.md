# Migration: LCCoding 2.5.0 to 2.5.1

LCCoding 2.5.1 is a release-identity patch. It does not change the LCCoding mainline, BI behavior, project schema semantics, Loop contracts, or installed product display name.

## Required change

- Build and distribute the installer as `LCCoding-BI_2.5.1_x64-setup.exe`.
- Require the downloaded basename, `provenance.asset`, `installer.sha256` basename, and GitHub workflow upload path to match exactly.
- Reject spaces, path separators, URI syntax, and characters outside `A-Z`, `a-z`, `0-9`, `.`, `_`, and `-` in the distributed basename.

The published LCCoding 2.5.0 tag, Release, assets, and provenance remain historical and unchanged.
