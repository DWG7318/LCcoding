#!/usr/bin/env python3
from pathlib import Path
import argparse, json

REQUIRED=['receipt_id','layer','claim_id','claim_version','candidate_id','candidate_hash','authority','verdict']
REPEAT=['source_layer','reason','scope_difference','risk','result']
INDEPENDENCE=['executor_context_id','verification_context_id','verification_workspace_id']

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('receipt'); args=ap.parse_args()
    d=json.loads(Path(args.receipt).read_text(encoding='utf-8'))
    errors=[f'missing {x}' for x in REQUIRED if not d.get(x)]
    if d.get('layer') not in ['D0','D1','D2','D3']: errors.append('invalid layer')
    if d.get('layer') in ['D1','D2','D3']:
        for x in INDEPENDENCE:
            if not d.get(x): errors.append(f'missing independence field {x}')
        if d.get('executor_context_id') and d.get('executor_context_id')==d.get('verification_context_id'):
            errors.append('self-verification context collision')
    for i,r in enumerate(d.get('repeated_checks',[])):
        for x in REPEAT:
            if not r.get(x): errors.append(f'repeated_checks[{i}] missing {x}')
    if d.get('new_evidence')==[] and d.get('layer') in ['D2','D3'] and not d.get('reused_evidence'):
        errors.append('higher layer has neither reused nor new evidence')
    if errors:
        print('FAIL'); print('\n'.join(errors)); raise SystemExit(1)
    print('PASS')
if __name__=='__main__': main()
