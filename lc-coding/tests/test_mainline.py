from pathlib import Path
import json
root=Path(__file__).resolve().parents[2]
contract=json.loads((root/'lc-coding/contracts/lifecycle.json').read_text())
expected=['LCCODING_APPLICABILITY_ASSESSMENT','PROPOSAL_READINESS','PRODUCT_SERVICE_STRATEGY','PROJECT_INITIALIZATION','CALABASH_DRAFT','SERVICE_ROUTE_MAP','WORKFLOW_ROUTE_SURFACES_SIMULATION','MANDATORY_CALABASH_UPGRADE','PRODUCT_BASELINE','FEATURE_SLICE','FEATURE_INTEGRATION','REAL_USER_JOURNEY_ACCEPTANCE','FINAL_VERIFICATION','OWNER_ACCEPTANCE','DELIVERY']
assert contract['mainline']==expected
assert contract['mainline_scope']=='WHOLE_PRODUCT_FIT_OR_BOUNDED_PRODUCT_FIT_ADMITTED_PATH'
assert contract['required_transitions']==dict(zip(expected[1:],expected[2:]))
assert 'LCCODING_APPLICABILITY_ASSESSMENT' not in contract['required_transitions']
routing=contract['applicability_routing']
assert set(routing['outcomes'])=={'WHOLE_PRODUCT_FIT','BOUNDED_PRODUCT_FIT','OTHER_METHOD_RECOMMENDED'}
for outcome in ['WHOLE_PRODUCT_FIT','BOUNDED_PRODUCT_FIT']:
    assert routing['outcomes'][outcome]['lccoding_lifecycle_admitted'] is True
    assert routing['outcomes'][outcome]['next']=='PROPOSAL_READINESS'
assert routing['outcomes']['OTHER_METHOD_RECOMMENDED']['disposition']=='TERMINAL_ASSESSMENT'
assert routing['outcomes']['OTHER_METHOD_RECOMMENDED']['lccoding_lifecycle_admitted'] is False
assert routing['outcomes']['OTHER_METHOD_RECOMMENDED']['next'] is None
assert routing['insufficient_facts']['disposition']=='PROPOSAL_INCOMPLETE'
assert routing['insufficient_facts']['applicability_outcome'] is None
assert contract['compatibility_aliases']['WORKFLOW_UI_SIMULATION']['canonical']=='WORKFLOW_ROUTE_SURFACES_SIMULATION'
assert contract['compatibility_aliases']['WORKFLOW_UI_SIMULATION']['read_only'] is True
con=(root/'CONSTITUTION.md').read_text(encoding='utf-8')
for x in ['Workflow capability end','UI product-surface end','Simulation World','Mandatory Calabash Upgrade','Feature Slice','Owner Acceptance','Delivery']:
    assert x in con

phases=json.loads((root/'lc-coding/contracts/phases.json').read_text())
assert phases['mainline_unchanged'] is False
phase_by_id={phase['id']:phase for phase in phases['phases']}
assert list(phase_by_id)==['INITIAL','PRODUCT_FORMATION','REAL_PRODUCT_INTEGRATION','REAL_USER_JOURNEY_ACCEPTANCE','DELIVERY_PREPARATION']
initial=phase_by_id['INITIAL']
assert initial['start']=='LCCODING_APPLICABILITY_ASSESSMENT'
assert initial['fine_milestones']==expected[:4]
assert initial['fine_milestone_path_condition']=='LCCODING_LIFECYCLE_ADMITTED'
assert initial['applicability_outcomes']==['WHOLE_PRODUCT_FIT','BOUNDED_PRODUCT_FIT','OTHER_METHOD_RECOMMENDED']
assert initial['primary_product_service_strategies']==['PLATFORM_COMPLETION','AGENT_COLLABORATIVE']
assert initial['combined_product_service_strategy']=='MIXED'
assert initial['applicability_admission']=={
    'admitted_outcomes':['WHOLE_PRODUCT_FIT','BOUNDED_PRODUCT_FIT'],
    'terminal_outcome':'OTHER_METHOD_RECOMMENDED',
    'incomplete_disposition':'PROPOSAL_INCOMPLETE',
}
formation=phase_by_id['PRODUCT_FORMATION']
assert formation['start']=='CALABASH_DRAFT'
assert formation['fine_milestones']==expected[4:9]
assert formation['service_route_map']['authority']=='CALABASH'
assert formation['service_route_map']['route_kinds']==['DIRECT_PRODUCT','PERSONAL_AGENT','SERVICE_CENTER']
assert formation['service_route_map']['actor_classes']=={
    'HUMAN_PRINCIPAL':'HUMAN_BENEFICIARY',
    'PERSONAL_AGENT':'EXTERNAL_CUSTOMER_CONTROLLED',
    'PRODUCT_AGENT':'INTERNAL_DELIVERED_PRODUCT_BEHAVIOR',
    'OPERATIONS_AGENT':'INTERNAL_DELIVERED_OPERATIONS_BEHAVIOR',
    'SERVICE_CENTER_ACTOR':'AUTHORIZED_ASSISTED_SERVICE',
}
assert formation['service_route_map']['route_support_scope']=='PER_DELIVERED_JOURNEY'
assert formation['service_route_map']['shared_capability_system']=='WORKFLOW_BACKEND_CORE'
assert formation['formation_surface_contract']['selection_scope']=='PER_DELIVERED_JOURNEY'
assert formation['formation_surface_contract']['graphical_ui_required']=='ONLY_WHEN_PROMISED_BY_ROUTE'
assert formation['formation_surface_contract']['artificial_ui_forbidden'] is True
assert formation['end_after']=='PRODUCT_BASELINE'
assert formation['exit_evidence']['artifact']=='PRODUCT_BASELINE_HANDOFF'
assert 'exit_gate' not in formation
assert formation['internal_readiness']['phase_exit'] is False
integration=phase_by_id['REAL_PRODUCT_INTEGRATION']
assert integration['display_meaning']=='REAL_PRODUCT_INTEGRATION'
assert integration['start']=='FEATURE_SLICE'
assert integration['feature_slice_chain']==[
    'PROMISED_REAL_ENTRY','AUTHENTICATED_ACTOR_AND_VALID_AUTHORITY',
    'REAL_ROUTE_ADAPTER_OR_PRODUCT_SURFACE','REAL_WORKFLOW_AND_BACKEND_CORE_EFFECTS',
    'AUTHORITATIVE_STATE_DATA_SIDE_EFFECT','ROUTE_RESULT',
    'HUMAN_OBSERVABLE_BUSINESS_OUTCOME',
]
assert integration['required_route_evidence_scope']=='PER_DELIVERED_JOURNEY_ROUTE'
assert 'entry_gate' not in integration
assert integration['slice_run_admission']['phase_entry'] is False
assert integration['aggregate_exit_scope']=='REQUIRED_PHASE_3_INTEGRATION_RUNS'
journey=phase_by_id['REAL_USER_JOURNEY_ACCEPTANCE']
assert journey['start_after']=='ALL_REQUIRED_RUNS_ACCEPTED'
assert journey['route_faithful'] is True
assert journey['visible_actions_require_screenshots'] is True
assert journey['nonvisual_agent_first_hand_evidence']==['MESSAGE','TASK_TRANSITION','ARTIFACT','AUTHORIZATION_DECISION','PLATFORM_EFFECT','RESULT_DELIVERY','AUDIT_EVENT']
assert journey['final_human_observable_outcome_required'] is True
assert journey['complete_round_starts_at']=='ACTUAL_REQUIRED_ROUTE_ENTRY'
assert journey['repair_priority']==['USER_SERVICE_BOUNDARY','WORKFLOW_ORCHESTRATION','BACKEND_CORE']
assert journey['exit_gate']=='REAL_USER_JOURNEY_ACCEPTED'
assert phase_by_id['DELIVERY_PREPARATION']['start_after']=='REAL_USER_JOURNEY_ACCEPTED'
assert phase_by_id['DELIVERY_PREPARATION']['exit_gate']=='DELIVERY_READY'

spec=(root/'SPEC.md').read_text(encoding='utf-8')
skill=(root/'lc-coding/SKILL.md').read_text(encoding='utf-8')
readme=(root/'README.md').read_text(encoding='utf-8')
readme_zh=(root/'README.zh-CN.md').read_text(encoding='utf-8')

semantic_checks=[
    (spec,'SPEC Workflow',[
        'Workflow is not merely a plan, description, or flowchart',
        'AI must use Calabash and available Simulation Worlds',
        'real, runnable business functions',
        'simulation-only results cannot substitute for real Workflow',
        'Every Workflow business line is classified as `CORE` or `EXTRA`',
        'CORE is confirmed in Calabash and by the Owner as required product capability',
        'EXTRA is an enhancement derived from Calabash extension space, external research, or comparable-product analysis',
        'must not be claimed as existing product capability unless implemented and verified',
        'must not reclassify CORE as EXTRA to pass Product Baseline',
    ]),
    (spec,'SPEC Product Baseline',[
        'must not enter Product Baseline',
        'proved infeasible under the current product constraints',
        'adjust Calabash, narrow the direction, hold, or terminate',
        'Product Baseline implementation gate applies only to CORE Workflow',
        'Incomplete or infeasible EXTRA does not block Product Baseline',
    ]),
    (spec,'SPEC Feature Slice',[
        'already implemented and verified Workflow capabilities',
        'inherit and reuse them wherever possible',
        'may supplement, adjust, and improve Workflow',
        'Impact Analysis and `CONTROLLED_MUTABLE` rules',
        'all already implemented and verified Workflow capabilities across CORE and EXTRA',
    ]),
    (skill,'SKILL Workflow',[
        'Use Calabash and available Simulation Worlds to split Workflow into enough business lines',
        'real, runnable business functions',
        'cannot replace real Workflow',
        'until Mandatory Calabash Upgrade is complete',
        'Mark each Workflow business line `CORE` or `EXTRA`',
        'CORE means Calabash and Owner confirmation make the business line required product capability',
        'EXTRA comes from Calabash extension space, external research, or comparable-product analysis',
        'Do not claim unimplemented EXTRA as product capability',
        'Never reclassify CORE as EXTRA to pass Product Baseline',
    ]),
    (skill,'SKILL Product Baseline',[
        'Freeze Product Baseline only after every CORE business line is real, runnable, and proved feasible',
        'proved infeasible under current product constraints',
        'adjust Calabash, narrow, hold, or terminate',
        'Product Baseline gate applies only to CORE Workflow',
        'EXTRA does not block Product Baseline',
    ]),
    (skill,'SKILL Feature Slice',[
        'already implemented and verified Workflow capabilities',
        'inherit and reuse them wherever possible',
        'supplement, adjust, or improve Workflow',
        'Impact Analysis and `CONTROLLED_MUTABLE` rules',
        'all already implemented and verified Workflow capabilities across CORE and EXTRA',
    ]),
]
for document,label,markers in semantic_checks:
    for marker in markers:
        assert marker in document, f'missing {label} rule: {marker}'

mainline_marker='[Simulation World foundation first → Workflow capability end ∥ applicable route/service-surface and human-outcome ends]'
for relative in ['CONSTITUTION.md','SPEC.md']:
    mainline_text=(root/relative).read_text(encoding='utf-8')
    assert mainline_marker in mainline_text, relative
    assert 'Workflow/UI/Simulation [Simulation' not in mainline_text, relative
compatibility_marker='[Simulation World foundation first → Workflow capability end ∥ UI product-surface end]'
for relative in ['README.md','lc-coding/SKILL.md']:
    assert compatibility_marker in (root/relative).read_text(encoding='utf-8'), relative
assert '[先建立 Simulation World foundation → Workflow 能力端 ∥ UI 产品呈现端分别推进]' in readme_zh
assert 'Workflow/UI/Simulation [先建立 Simulation' not in readme_zh
assert 'applicable route/service-surface and human-outcome ends' in con

simulation_first_checks=[
    (spec,'SPEC Simulation-first',[
        'Before actual Workflow or route-specific surface or adapter construction begins',
        'minimal, real, runnable, versioned Simulation World foundation',
        'Workflow and the applicable route ends advance independently',
        'each required end must produce real, runnable, inspectable results',
        'does not require Workflow and those ends to be connected or jointly integrated',
        'Cross-layer Workflow-to-route connection and end-to-end proof remain responsibilities of Feature Slice and route-bound Integration',
        'Simulation remains `VERSIONED_MUTABLE`',
    ]),
    (skill,'SKILL Simulation-first',[
        'Build at least one minimal, real, runnable, versioned Simulation World foundation before actual Workflow or UI construction',
        'Then advance Workflow and UI as equal product ends, independently; they may proceed in parallel',
        'real, runnable, inspectable result',
        'Do not require early Workflow-to-UI connection or three-way joint integration',
        'Continue semantic and scenario synchronization without treating it as early integration',
        'Keep cross-layer connection and end-to-end proof in Feature Slice and UI-locked Integration',
        'Never treat the foundation as a complete or frozen Simulation',
    ]),
    (readme,'README Simulation-first',[
        'A minimal, real, runnable, versioned Simulation World foundation comes first',
        'Workflow and UI then advance independently',
        'Feature Slice and UI-locked Integration own the later cross-layer connection and proof',
    ]),
    (readme_zh,'README.zh Simulation-first',[
        '最小、真实可运行、带版本的 Simulation World foundation',
        'Workflow 与 UI 才作为同等产品端分别独立向前建设',
        '跨层连接与贯通证明仍由后续 Feature Slice 和 UI-locked Integration 负责',
    ]),
]
for document,label,markers in simulation_first_checks:
    for marker in markers:
        assert marker in document, f'missing {label} rule: {marker}'

status=json.loads((root/'lc-coding/templates/STATUS.json').read_text())
framework=json.dumps((contract,phases,status)).lower()
for forbidden in [
    'workflow_realization','workflow realization','workflow_feasibility','workflow feasibility',
    'simulation_foundation','simulation_first_gate','simulation_ready_state',
]:
    assert forbidden not in framework

workflow_map=(root/'lc-coding/templates/WORKFLOW-MAP.md').read_text(encoding='utf-8')
assert '| Workflow ID | Classification (CORE/EXTRA) | Implementation status |' in workflow_map
assert workflow_map.count('Classification (CORE/EXTRA)')==1
example_workflow_map=(root/'lc-coding/examples/enterprise-clinic/.lccoding/WORKFLOW-MAP.md').read_text(encoding='utf-8')
assert '| Workflow ID | Classification (CORE/EXTRA) | Implementation status |' in example_workflow_map
for marker in ['API contract / evidence','MCP contract / evidence','UI subtree references','Simulation subtree references','Primary mainline']:
    assert marker in workflow_map
ui_map=(root/'lc-coding/templates/UI-MAP.md').read_text(encoding='utf-8')
simulation_map=(root/'lc-coding/templates/SIMULATION-WORLD.md').read_text(encoding='utf-8')
assert 'UI ID | Subtree path | Component version | Content hash' in ui_map
assert 'Simulation ID | Subtree path | Component version | Content hash' in simulation_map
assert 'Peer simulations do not nest' in simulation_map
print('PASS: mainline')
