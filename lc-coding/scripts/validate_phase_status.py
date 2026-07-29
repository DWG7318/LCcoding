#!/usr/bin/env python3
from pathlib import Path
import argparse, json

ORDER=['INITIAL','PRODUCT_FORMATION','ENGINEERING_RUNS','DELIVERY_PREPARATION']

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('status'); args=ap.parse_args()
    data=json.loads(Path(args.status).read_text(encoding='utf-8'))
    errors=[]; current=data.get('current_phase'); phases=data.get('phases',{})
    if current not in ORDER: errors.append('invalid current_phase')
    for phase in ORDER:
        if phase not in phases: errors.append('missing phase '+phase)
    if current in ORDER:
        idx=ORDER.index(current)
        for prior in ORDER[:idx]:
            rec=phases.get(prior,{})
            gate=rec.get('exit_gate', rec.get('aggregate_exit_gate'))
            if gate!='PASS': errors.append('prior phase exit gate not PASS: '+prior)
    if errors:
        print('FAIL'); print('\n'.join(errors)); raise SystemExit(1)
    print('PASS')
if __name__=='__main__': main()
