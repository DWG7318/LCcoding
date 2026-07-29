# Publish to GitHub

From the extracted repository root:

```bash
git init
git add .
git commit -m "release: LCCoding 2.0.0"
git branch -M main
git remote add origin <OWNER-CONFIRMED-REPOSITORY>
git push -u origin main
git tag -a v2.0.0 -m "LCCoding 2.0.0"
git push origin v2.0.0
```

Before creating or changing repository visibility, obtain the Owner's explicit Public/Private decision.
