# Publish LCCoding 1.1.1 to GitHub

```bash
unzip LCCoding-1.1.1-github.zip
cd LCCoding-1.1.1-github

git init
git add .
git commit -m "feat: release LCCoding 1.1.1"
git branch -M main
git remote add origin https://github.com/DWG7318/LCcoding.git
git push -u origin main

git tag -a v1.1.1 -m "LCCoding 1.1.1"
git push origin v1.1.1
```

If the repository already exists, copy the files into a clean branch, review the diff,
commit, merge, and tag `v1.1.1`.
