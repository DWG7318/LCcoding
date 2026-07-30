#!/usr/bin/env python3
from pathlib import Path
import argparse, json

REQUIRED=['PROJECT-START.json','OWNER-POLICY.md','PROJECT-PROFILE.md','AGENT-RULE.md','CANONICAL-MANIFEST.json','INTERPRETATION-LOCK.json','WORKFLOW-MAP.md','UI-MAP.md','SIMULATION-WORLD.md','status.json','PHASE-STATUS.json']
COMPLEXITY_FACTORS=['product_uncertainty','system_coupling','real_risk','irreversibility','novelty']
COMPLEXITY_LEVELS={'LOW','MEDIUM','HIGH'}

def validate_complexity_depth(fingerprint):
    errors=[]
    complexity=fingerprint.get('complexity')
    depth=fingerprint.get('depth',{})
    if not isinstance(complexity,dict):
        return ['Project Fingerprint complexity must record five factors']
    values=[]
    for factor in COMPLEXITY_FACTORS:
        value=str(complexity.get(factor,'')).upper()
        if value not in COMPLEXITY_LEVELS: errors.append('invalid complexity factor '+factor)
        else: values.append(value)
    if any(value!='LOW' for value in values) and not depth.get('rationale'):
        errors.append('non-low complexity requires a depth rationale')
    if 'HIGH' in values and not any(depth.get(name) for name in ['analysis','materials','evidence']):
        errors.append('high complexity requires deeper coverage in analysis, materials, or evidence')
    return errors

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('project'); args=ap.parse_args()
    lc=Path(args.project)/'.lccoding'; errors=[]
    for x in REQUIRED:
        if not (lc/x).exists(): errors.append('missing '+x)
    start={}
    if (lc/'PROJECT-START.json').exists():
        start=json.loads((lc/'PROJECT-START.json').read_text(encoding='utf-8'))
        mode=start.get('initialization_mode','NEW')
        if mode not in {'NEW','EXISTING'}: errors.append('invalid initialization_mode')
        if mode=='EXISTING':
            if not start.get('source_head'): errors.append('existing project source_head missing')
            if not start.get('source_version'): errors.append('existing project source_version missing')
            if start.get('continuity_decision') not in {'CONTINUE','NARROW_REDIRECT','HOLD','TERMINATE'}:
                errors.append('existing project continuity decision missing')
            if start.get('completion_claim_status') not in {'NO_CLAIM','CLAIMED_UNATTESTED'}:
                errors.append('existing completion claim crossed the evidence boundary')
            if start.get('attestation_status')!='PENDING':
                errors.append('existing project attestation must begin PENDING')
    if (lc/'PROJECT-FINGERPRINT.json').exists():
        fingerprint=json.loads((lc/'PROJECT-FINGERPRINT.json').read_text(encoding='utf-8'))
        errors.extend(validate_complexity_depth(fingerprint))
    if (lc/'INTERPRETATION-LOCK.json').exists():
        lock=json.loads((lc/'INTERPRETATION-LOCK.json').read_text(encoding='utf-8'))
        if lock.get('status')!='VALID': errors.append('Interpretation Lock is not VALID')
    if (Path(args.project)/'VERSION').exists():
        if not (Path(args.project)/'VERSION').read_text().strip(): errors.append('empty VERSION')
    elif start.get('initialization_mode','NEW')=='NEW': errors.append('missing project VERSION')
    if errors:
        print('FAIL'); print('\n'.join(errors)); raise SystemExit(1)
    print('PASS')
if __name__=='__main__': main()
