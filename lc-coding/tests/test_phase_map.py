from pathlib import Path
import json
root=Path(__file__).resolve().parents[2]
contract=json.loads((root/'lc-coding/contracts/phases.json').read_text())
assert contract['mainline_unchanged'] is True
phases=contract['phases']
assert [p['id'] for p in phases]==['INITIAL','PRODUCT_FORMATION','ENGINEERING_RUNS','DELIVERY_PREPARATION']
assert phases[0]['end_before']=='CALABASH_DRAFT'
assert phases[1]['end_before']=='MANDATORY_CALABASH_UPGRADE'
assert phases[2]['per_run_end_before']=='LOOP_OWNER_ACCEPTANCE'
assert phases[2]['per_run_exit_gate']=='LOOP_OWNER_ACCEPTANCE_READY'
assert phases[2]['aggregate_exit_gate']=='ALL_REQUIRED_RUNS_ACCEPTED'
assert phases[3]['end_before']=='DELIVERY'
assert 'POST_SECURITY_OWNER_ACCEPTANCE' in phases[3]['required_subgates']
print('PASS: phase map')
