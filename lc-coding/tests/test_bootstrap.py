from pathlib import Path
import subprocess, sys, tempfile
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as td:
    cp=subprocess.run([sys.executable,str(root/'lc-coding/scripts/bootstrap_lccoding.py'),'--project',td,'--name','Test','--repository','owner/test','--visibility','private'],capture_output=True,text=True)
    assert cp.returncode==0, cp.stdout+cp.stderr
    lc=Path(td)/'.lccoding'
    for f in ['PROJECT-START.json','AGENT-RULE.md','CANONICAL-MANIFEST.json','WORKFLOW-MAP.md','UI-MAP.md','SIMULATION-WORLD.md','status.json']:
        assert (lc/f).exists(), f
    assert (Path(td)/'VERSION').read_text().strip()=='0.0.1'
print('PASS: bootstrap')
