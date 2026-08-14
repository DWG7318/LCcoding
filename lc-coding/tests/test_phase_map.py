from pathlib import Path
import json
root=Path(__file__).resolve().parents[2]
contract=json.loads((root/'lc-coding/contracts/phases.json').read_text())
assert contract['mainline_unchanged'] is True
phases=contract['phases']
assert [p['id'] for p in phases]==['INITIAL','PRODUCT_FORMATION','REAL_PRODUCT_INTEGRATION','DELIVERY_PREPARATION']
phase_by_id={phase['id']:phase for phase in phases}
assert phase_by_id['INITIAL']['end_before']=='CALABASH_DRAFT'
formation=phase_by_id['PRODUCT_FORMATION']
assert formation['start']=='CALABASH_DRAFT'
assert formation['end_after']=='PRODUCT_BASELINE'
assert formation['exit_evidence']['artifact']=='PRODUCT_BASELINE_HANDOFF'
assert formation['exit_evidence']['mechanical_validation']=='PASS'
assert formation['exit_evidence']['owner_acceptance']=='ACCEPTED'
assert formation['internal_readiness']['id']=='CALABASH_UPGRADE_READY'
assert formation['internal_readiness']['meaning']=='READY_TO_BEGIN_MANDATORY_CALABASH_UPGRADE'
assert formation['internal_readiness']['compatibility_readable'] is True
assert formation['internal_readiness']['phase_exit'] is False
assert 'exit_gate' not in formation
integration=phase_by_id['REAL_PRODUCT_INTEGRATION']
assert integration['display_meaning']=='REAL_PRODUCT_INTEGRATION'
assert integration['start']=='FEATURE_SLICE'
assert 'entry_gate' not in integration
assert integration['slice_run_admission']['relation']=='FEATURE_SLICE_EXECUTION_COVERAGE_PASS'
assert integration['slice_run_admission']['scope']==['PER_SLICE','PER_INTEGRATION_RUN']
assert integration['slice_run_admission']['phase_entry'] is False
assert integration['per_run_end_before']=='LOOP_OWNER_ACCEPTANCE'
assert integration['per_run_exit_gate']=='LOOP_OWNER_ACCEPTANCE_READY'
assert integration['aggregate_exit_gate']=='ALL_REQUIRED_RUNS_ACCEPTED'
assert integration['aggregate_exit_scope']=='REQUIRED_PHASE_3_INTEGRATION_RUNS'
assert set(integration['aggregate_excludes'])=={
    'INITIAL_RUNS','PRODUCT_FORMATION_RUNS','DELIVERY_PREPARATION_RUNS',
    'OPTIONAL_RUNS','SUPERSEDED_RUNS','INVALIDATED_RUNS',
}
delivery=phase_by_id['DELIVERY_PREPARATION']
assert delivery['end_before']=='DELIVERY'
assert 'POST_SECURITY_OWNER_ACCEPTANCE' in delivery['required_subgates']
print('PASS: phase map')
