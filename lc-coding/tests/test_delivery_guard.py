
from pathlib import Path
import json, subprocess, sys, tempfile
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as td:
    good={'included':['frontend','client-runtime'],'excluded':['LCagent','LCapi'],'delivery_decision_id':'DD-1','delivery_method_confirmed':True,'qa_status':'COMPLETE','runtime_certification':'ubuntu-24.04','license_policy':'customer-license','owner_approval':'APPROVED'}
    p=Path(td)/'m.json'; p.write_text(json.dumps(good))
    cp=subprocess.run([sys.executable,str(root/'lc-coding/scripts/delivery_guard.py'),str(p)],capture_output=True,text=True)
    assert cp.returncode==0,cp.stdout+cp.stderr
    good['included'].append('LCapi'); p.write_text(json.dumps(good))
    cp=subprocess.run([sys.executable,str(root/'lc-coding/scripts/delivery_guard.py'),str(p)],capture_output=True,text=True)
    assert cp.returncode!=0
print('PASS: delivery guard')
