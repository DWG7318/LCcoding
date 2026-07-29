
from pathlib import Path
import json, subprocess, sys, tempfile
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'d.json'
    groups=['delivery_model','assets','source_and_modification_rights','runtime_and_infrastructure','data','internal_dependencies','license','operations']
    good={'delivery_decision_id':'DD-1','delivery_id':'D-1','customer':'Customer A','candidate_id':'C-1','owner_policy_version':'1','locked_exclusions':['LCapi'],'decisions':{g:{'selected':'confirmed'} for g in groups},'qa_status':'COMPLETE','owner_confirmed':True,'confirmed_at':'now'}
    p.write_text(json.dumps(good),encoding='utf-8')
    cp=subprocess.run([sys.executable,str(root/'lc-coding/scripts/validate_delivery_decision.py'),str(p)],capture_output=True,text=True)
    assert cp.returncode==0,cp.stdout+cp.stderr
    good['decisions']['license']=None
    p.write_text(json.dumps(good),encoding='utf-8')
    cp=subprocess.run([sys.executable,str(root/'lc-coding/scripts/validate_delivery_decision.py'),str(p)],capture_output=True,text=True)
    assert cp.returncode!=0
print('PASS: delivery Q&A')
