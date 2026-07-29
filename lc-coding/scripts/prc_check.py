#!/usr/bin/env python3
from pathlib import Path
import argparse, json

REQUIRED = ['problem','target_users','core_value','scope','constraints','success_criteria']

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('proposal_json')
    args=ap.parse_args()
    data=json.loads(Path(args.proposal_json).read_text(encoding='utf-8'))
    missing=[k for k in REQUIRED if not data.get(k)]
    conflicts=data.get('conflicts',[])
    result={'status':'PROPOSAL_READY' if not missing and not conflicts else 'PROPOSAL_INCOMPLETE',
            'missing_blockers':missing,'conflicts':conflicts,
            'questions':[{'field':k,'question':f'Please resolve {k}.','recommended_answer':''} for k in missing]}
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
