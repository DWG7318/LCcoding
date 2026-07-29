
#!/usr/bin/env python3
from pathlib import Path
import argparse, json

GROUPS=['delivery_model','assets','source_and_modification_rights','runtime_and_infrastructure','data','internal_dependencies','license','operations']

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decision'); args=ap.parse_args()
    data=json.loads(Path(args.decision).read_text(encoding='utf-8'))
    errors=[]
    if data.get('qa_status')!='COMPLETE': errors.append('Q&A incomplete')
    if data.get('owner_confirmed') is not True: errors.append('Owner confirmation missing')
    decisions=data.get('decisions',{})
    for group in GROUPS:
        if group not in decisions or decisions[group] in (None,'',[],{}): errors.append('missing decision group: '+group)
    if not data.get('delivery_decision_id'): errors.append('delivery_decision_id missing')
    if not data.get('customer'): errors.append('customer missing')
    if errors:
        print('FAIL'); print('\n'.join(errors)); raise SystemExit(1)
    print('PASS')
if __name__=='__main__': main()
