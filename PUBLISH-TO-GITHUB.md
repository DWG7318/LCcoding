# Publish to GitHub

From the extracted repository root:

```bash
git init
git add .
git commit -m "release: LCCoding 2.5.0"
git branch -M main
git remote add origin <OWNER-CONFIRMED-REPOSITORY>
git push -u origin main
git tag -a v2.5.0 -m "LCCoding 2.5.0"
git push origin v2.5.0
```

Before creating or changing repository visibility, obtain the Owner's explicit Public/Private decision.

For LCCoding 2.5.0, create the verified current-user NSIS assets before the tag/Release:

```powershell
lc-coding/bi/scripts/package-release.ps1 -OutputRoot <EXTERNAL-EMPTY-OUTPUT-DIRECTORY>
```

The command is allowed to finish only after the SLK 2.5.0, CLK 2.5.0, and GLK 3.1.0 formal-release dependency gate passes. Attach the generated `LCCoding BI_2.5.0_*_setup.exe`, `installer.sha256`, and `provenance.json` to the GitHub Release. Do not use `-AllowUnreleasedLoopCandidates` for a published asset.
