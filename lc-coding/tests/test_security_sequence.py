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
print('PASS: security sequence and independence')
