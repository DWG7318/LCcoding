from pathlib import Path
import json
root=Path(__file__).resolve().parents[2]
contract=json.loads((root/'lc-coding/contracts/phases.json').read_text())
compatibility=json.loads((root/'lc-coding/bi/release/loop-contract-identities.json').read_text())
phase_projection=json.loads((root/'lc-coding/templates/PHASE-STATUS.json').read_text())
assert contract['mainline_unchanged'] is False
phases=contract['phases']
assert [p['id'] for p in phases]==[
    'INITIAL','PRODUCT_FORMATION','REAL_PRODUCT_INTEGRATION',
    'REAL_USER_JOURNEY_ACCEPTANCE','DELIVERY_PREPARATION',
]
phase_ids=[p['id'] for p in phases]
adapter_400=compatibility['status_adapters']['4.0.0']
assert list(adapter_400['phase_steps'])==phase_ids
assert adapter_400['phase_steps']['INITIAL'][:4]==[
    'LCCODING_APPLICABILITY_ASSESSMENT','PROPOSAL_READINESS',
    'PRODUCT_SERVICE_STRATEGY','PROJECT_INITIALIZATION',
]
assert adapter_400['phase_steps']['PRODUCT_FORMATION'][:2]==[
    'CALABASH_DRAFT','SERVICE_ROUTE_MAP_READY',
]
assert phase_projection['status_schema_version']=='3.0.0'
assert list(phase_projection['phases'])==phase_ids
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
    'INITIAL_RUNS','PRODUCT_FORMATION_RUNS','REAL_USER_JOURNEY_ACCEPTANCE_RUNS',
    'DELIVERY_PREPARATION_RUNS',
    'OPTIONAL_RUNS','SUPERSEDED_RUNS','INVALIDATED_RUNS',
}
journey=phase_by_id['REAL_USER_JOURNEY_ACCEPTANCE']
assert journey['start_after']=='ALL_REQUIRED_RUNS_ACCEPTED'
assert journey['candidate_bound'] is True
assert journey['route_faithful'] is True
assert journey['visible_product_operation'] is True
assert journey['visible_actions_require_screenshots'] is True
assert journey['nonvisual_agent_first_hand_evidence']==[
    'MESSAGE','TASK_TRANSITION','ARTIFACT','AUTHORIZATION_DECISION',
    'PLATFORM_EFFECT','RESULT_DELIVERY','AUDIT_EVENT',
]
assert journey['final_human_observable_outcome_required'] is True
assert journey['complete_round_starts_at']=='ACTUAL_REQUIRED_ROUTE_ENTRY'
assert journey['repair_priority']==[
    'USER_SERVICE_BOUNDARY','WORKFLOW_ORCHESTRATION','BACKEND_CORE',
]
assert journey['owner_results']==[
    'REAL_USER_JOURNEY_ACCEPTED',
    'REAL_USER_JOURNEY_REWORK',
    'REAL_USER_JOURNEY_DEFERRED',
]
assert journey['exit_gate']=='REAL_USER_JOURNEY_ACCEPTED'
delivery=phase_by_id['DELIVERY_PREPARATION']
assert delivery['start_after']=='REAL_USER_JOURNEY_ACCEPTED'
assert delivery['end_before']=='DELIVERY'
assert 'POST_SECURITY_OWNER_ACCEPTANCE' in delivery['required_subgates']
print('PASS: phase map')
