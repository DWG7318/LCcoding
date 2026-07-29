#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
root=Path(__file__).resolve().parents[2]
tests=sorted((root/'lc-coding/tests').glob('test_*.py'))
for test in tests:
    cp=subprocess.run([sys.executable,str(test)],capture_output=True,text=True)
    print(cp.stdout.strip())
    if cp.returncode:
        print(cp.stderr); raise SystemExit(cp.returncode)
print(f'PASS: {len(tests)} tests')
