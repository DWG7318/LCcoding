# Publish to GitHub

From the extracted repository root:

```bash
git init
git add .
git commit -m "release: LCCoding 2.2.2"
git branch -M main
git remote add origin <OWNER-CONFIRMED-REPOSITORY>
git push -u origin main
git tag -a v2.2.2 -m "LCCoding 2.2.2"
git push origin v2.2.2
```

Before creating or changing repository visibility, obtain the Owner's explicit Public/Private decision.
