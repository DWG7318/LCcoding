# Publish to GitHub

From the extracted repository root:

```bash
git init
git add .
git commit -m "release: LCCoding 3.0.0"
git branch -M main
git remote add origin <OWNER-CONFIRMED-REPOSITORY>
git push -u origin main
git tag -a v3.0.0 -m "LCCoding 3.0.0"
git push origin v3.0.0
```

Before creating or changing repository visibility, obtain the Owner's explicit Public/Private decision.

The source tag above does not itself create an installer or GitHub Release. For a formal LCCoding 3.0.0 Windows release, first create the verified current-user NSIS assets through the closed release workflow:

```powershell
lc-coding/bi/scripts/package-release.ps1 -OutputRoot <EXTERNAL-EMPTY-OUTPUT-DIRECTORY>
```

The command is allowed to finish only after the exact SLK, CLK, and GLK identities in the unique compatibility asset pass the formal-release dependency gate. Attach the generated `LCCoding-BI_3.0.0_x64-setup.exe`, `installer.sha256`, and `provenance.json` to the GitHub Release. The downloaded installer basename, `provenance.asset`, checksum basename, and workflow upload path must match exactly. Do not use `-AllowUnreleasedLoopCandidates` for a published asset.
