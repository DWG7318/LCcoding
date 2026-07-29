
#!/usr/bin/env python3
from pathlib import Path
import argparse, json

FORBIDDEN={'LCagent','LCapi','LCCoding','Calabash','SLK','CLK','GLK','Project Intelligence','Canonical Assets','Development Evidence'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('manifest'); args=ap.parse_args()
    d=json.loads(Path(args.manifest).read_text(encoding='utf-8'))
    included=set(d.get('included',[])); errors=[]
    bad=sorted(FORBIDDEN & included)
    if bad: errors.append('forbidden internal assets included: '+', '.join(bad))
    if d.get('qa_status')!='COMPLETE': errors.append('Delivery Method Q&A incomplete')
    if d.get('delivery_method_confirmed') is not True: errors.append('delivery method not confirmed')
    if not d.get('delivery_decision_id'): errors.append('delivery decision missing')
    if not d.get('runtime_certification'): errors.append('runtime certification missing')
    if not d.get('license_policy'): errors.append('license policy missing')
    if d.get('owner_approval')!='APPROVED': errors.append('Owner approval missing')
    if errors:
        print('FAIL'); print('\n'.join(errors)); raise SystemExit(1)
    print('PASS')
if __name__=='__main__': main()
