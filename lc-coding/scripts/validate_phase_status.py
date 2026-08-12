#!/usr/bin/env python3
from pathlib import Path
import argparse, json

ORDER=['INITIAL','PRODUCT_FORMATION','ENGINEERING_RUNS','DELIVERY_PREPARATION']
BOUNDARY_FIELDS={
    'INITIAL':'exit_gate',
    'PRODUCT_FORMATION':'exit_evidence',
    'ENGINEERING_RUNS':'aggregate_exit_gate',
    'DELIVERY_PREPARATION':'exit_gate',
}
DONE_STATES={
    'ACCEPTED','ALL_REQUIRED_RUNS_ACCEPTED','CLOSED','COMPLETE','COMPLETED',
    'DELIVERED','DELIVERY_READY','DONE','ESTABLISHED','EVIDENCED','INITIALIZED',
    'INVENTORIED','LOCKED','LOOP_OWNER_ACCEPTED','PASS','PASSED',
    'POST_SECURITY_OWNER_ACCEPTED','READY','RECONSTRUCTED','VERIFIED',
    'VULNERABILITY_CLOSED',
}
ACTIVE_STATES={'ACTIVE','EXECUTING','EXISTING_INTAKE_PENDING','IN_PROGRESS','RUNNING'}
PENDING_STATES={'PENDING'}
ERROR_STATES={
    'BLOCKED','ERROR','FAIL','FAILED','INVALID','NOT_CONTINUING','REJECTED',
}
PHASE_STATES={'PENDING','ACTIVE','COMPLETE','DONE','BLOCKED','INVALID'}
COMPLETED_PHASE_STATES={'COMPLETE','DONE'}

def normalize_lifecycle_state(value):
    if not isinstance(value,str): return None
    if value in DONE_STATES: return 'done'
    if value in ACTIVE_STATES: return 'active'
    if value in PENDING_STATES: return 'pending'
    if value in ERROR_STATES: return 'error'
    return None

def completed_evidence(value):
    return normalize_lifecycle_state(value)=='done'

def validate_phase_status(data):
    errors=[]; current=data.get('current_phase'); phases=data.get('phases',{})
    if data.get('record_role')!='DERIVED_VIEW' or data.get('derived_from')!='status.json':
        errors.append('PHASE-STATUS must remain a status.json DERIVED_VIEW')
    if current not in ORDER: errors.append('invalid current_phase')
    if not isinstance(phases,dict):
        return errors+['phases must be an object']
    for phase in phases:
        if phase not in ORDER: errors.append('unexpected phase '+phase)
    for phase in ORDER:
        if phase not in phases:
            errors.append('missing phase '+phase); continue
        record=phases.get(phase,{})
        if not isinstance(record,dict):
            errors.append('invalid phase record: '+phase); continue
        phase_state=record.get('status')
        if phase_state not in PHASE_STATES:
            errors.append('invalid phase status: '+phase)
        field=BOUNDARY_FIELDS[phase]
        value=record.get(field)
        if normalize_lifecycle_state(value) is None:
            label='exit evidence' if field=='exit_evidence' else 'exit gate'
            errors.append(f'invalid {label} state: {phase}')
    formation=phases.get('PRODUCT_FORMATION',{})
    if 'exit_gate' in formation:
        errors.append('Product Formation must derive exit evidence, not an exit gate')
    if current in ORDER:
        idx=ORDER.index(current)
        for prior in ORDER[:idx]:
            record=phases.get(prior,{})
            field=BOUNDARY_FIELDS[prior]
            if not completed_evidence(record.get(field)):
                errors.append('prior phase boundary not complete: '+prior)
            if record.get('status') not in COMPLETED_PHASE_STATES:
                errors.append('prior phase status not complete: '+prior)
        current_record=phases.get(current,{})
        if current_record.get('status')=='PENDING':
            errors.append('current phase status must not be PENDING: '+current)
        for future in ORDER[idx+1:]:
            record=phases.get(future,{})
            if record.get('status')!='PENDING':
                errors.append('future phase status must be PENDING: '+future)
            field=BOUNDARY_FIELDS[future]
            if normalize_lifecycle_state(record.get(field))!='pending':
                errors.append('future phase boundary must be PENDING: '+future)
    return errors

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('status'); args=ap.parse_args()
    data=json.loads(Path(args.status).read_text(encoding='utf-8'))
    errors=validate_phase_status(data)
    if errors:
        print('FAIL'); print('\n'.join(errors)); raise SystemExit(1)
    print('PASS')
if __name__=='__main__': main()
