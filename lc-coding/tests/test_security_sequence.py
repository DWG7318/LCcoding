from pathlib import Path
import json
root=Path(__file__).resolve().parents[2]
life=json.loads((root/'lc-coding/contracts/lifecycle.json').read_text())
bind=life['semantic_bindings']
assert 'LOOP_OWNER_ACCEPTANCE_PER_NORMAL_RUN' in bind['FEATURE_INTEGRATION']
assert bind['FINAL_VERIFICATION'][0]=='CENTRALIZED_VULNERABILITY_AUDIT'
assert bind['OWNER_ACCEPTANCE']==['POST_SECURITY_OWNER_ACCEPTANCE']
text=(root/'lc-coding/references/vulnerability-closure.md').read_text(encoding='utf-8')
assert 'immediately after every required normal Loop Run' in text
assert 'does not implement its own fixes' in text
status=json.loads((root/'lc-coding/templates/STATUS.json').read_text(encoding='utf-8'))
assert status['record_role']=='AUTHORITATIVE_PROJECT_STATUS'
assert status['vulnerability_closure']['state']=='PENDING'
assert status['post_security_owner_acceptance']['state']=='PENDING'
impact=(root/'lc-coding/templates/IMPACT-ANALYSIS.md').read_text(encoding='utf-8')
assert 'MATERIAL_SECURITY_SURFACE_CHANGE' in impact
assert 'INVALIDATE_AND_RETURN_TO_AUDIT' in impact
post=(root/'lc-coding/templates/POST-SECURITY-OWNER-ACCEPTANCE.md').read_text(encoding='utf-8')
assert 'POST_SECURITY_OWNER_ACCEPTANCE_RECEIPT' in post
assert 'Vulnerability Closure candidate ID / exact hash' in post
print('PASS: security sequence and independence')
