from pathlib import Path
import importlib.util, json, subprocess, sys, tempfile
root=Path(__file__).resolve().parents[2]
validator_path=root/'lc-coding/scripts/validate_project.py'
spec=importlib.util.spec_from_file_location('validate_project',validator_path)
validator=importlib.util.module_from_spec(spec); spec.loader.exec_module(validator)
receipt={'receipt_id':'r','layer':'D3','claim_id':'FS-1','claim_version':'1','candidate_id':'c','candidate_hash':'h','environment_id':'e','authority':'fresh verifier','executor_context_id':'worker-1','verification_context_id':'verifier-1','verification_workspace_id':'verify-ws-1','model_binding_id':'model-v1','reused_evidence':['d2'],'new_evidence':['seam'],'repeated_checks':[{'source_layer':'D2','reason':'environment materially differs','scope_difference':'production package','risk':'runtime','result':'PASS'}],'coverage':['FS-1'],'risks_remaining':[],'verdict':'PASS','issued_at':'now'}
with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'r.json'; p.write_text(json.dumps(receipt))
    cp=subprocess.run([sys.executable,str(root/'lc-coding/scripts/validate_verification.py'),str(p)],capture_output=True,text=True)
    assert cp.returncode==0, cp.stdout+cp.stderr

candidate=('CANDIDATE-1','sha256:'+'a'*64)
candidate_b=('CANDIDATE-1','sha256:'+'b'*64)
evidence_a='CANDIDATE-1~sha256:'+'a'*64+'~ROUTE-1~E-UNCHANGED'
identity,errors=validator.parse_bound_route_evidence(
    evidence_a,candidate,'ROUTE-1','reuse evidence'
)
assert identity and errors==[]
assert validator.parse_bound_route_evidence(
    evidence_a,candidate_b,'ROUTE-1','reuse evidence'
)[1]
assert validator.parse_bound_route_evidence(
    'CANDIDATE-1~sha256:'+'b'*64+'~ROUTE-1~E-UNCHANGED',candidate,'ROUTE-1','reuse evidence'
)[1]
assert validator.parse_bound_route_evidence(
    'CANDIDATE-1@ROUTE-1@E-UNCHANGED',candidate,'ROUTE-1','reuse evidence'
)[1]
changed,errors=validator.parse_route_link_set('VISIBLE_UI_RESULT','changed links')
reused,reuse_errors=validator.parse_route_link_set(
    'UI_ACTION, WORKFLOW_RULES, STATE_TRANSITION, DATA_EFFECT, SIDE_EFFECT, FAILURE_PATH, RECOVERY_RESULT',
    'reused links',
)
new,new_errors=validator.parse_route_link_set('VISIBLE_UI_RESULT','new links')
assert errors+reuse_errors+new_errors==[]
assert not changed.intersection(reused)
assert changed.issubset(new)
assert reused.union(new)==set(validator.ROUTE_LINKS)
print('PASS: verification reuse')
