from pathlib import Path
import json, subprocess, sys, tempfile
root=Path(__file__).resolve().parents[2]
receipt={'receipt_id':'r','layer':'D3','claim_id':'FS-1','claim_version':'1','candidate_id':'c','candidate_hash':'h','environment_id':'e','authority':'fresh verifier','executor_context_id':'worker-1','verification_context_id':'verifier-1','verification_workspace_id':'verify-ws-1','model_binding_id':'model-v1','reused_evidence':['d2'],'new_evidence':['seam'],'repeated_checks':[{'source_layer':'D2','reason':'environment materially differs','scope_difference':'production package','risk':'runtime','result':'PASS'}],'coverage':['FS-1'],'risks_remaining':[],'verdict':'PASS','issued_at':'now'}
with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'r.json'; p.write_text(json.dumps(receipt))
    cp=subprocess.run([sys.executable,str(root/'lc-coding/scripts/validate_verification.py'),str(p)],capture_output=True,text=True)
    assert cp.returncode==0, cp.stdout+cp.stderr
print('PASS: verification reuse')
