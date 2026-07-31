from pathlib import Path
import subprocess, sys
root=Path(__file__).resolve().parents[2]
script=str(root/'lc-coding/scripts/version_guard.py')
assert subprocess.run([sys.executable,script,'0.1.1','1.0.1'],capture_output=True).returncode!=0
assert subprocess.run([sys.executable,script,'0.1.1','1.0.1','--owner-approved'],capture_output=True).returncode==0
assert subprocess.run([sys.executable,script,'2.2.0','2.2.1'],capture_output=True).returncode!=0
assert subprocess.run([sys.executable,script,'2.2.0','2.2.1','--owner-approved'],capture_output=True).returncode==0
assert subprocess.run([sys.executable,script,'2.2.1','2.2.2'],capture_output=True).returncode!=0
assert subprocess.run([sys.executable,script,'2.2.1','2.2.2','--owner-approved'],capture_output=True).returncode==0
print('PASS: version guard')
