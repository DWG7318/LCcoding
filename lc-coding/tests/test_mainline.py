from pathlib import Path
import json
root=Path(__file__).resolve().parents[2]
contract=json.loads((root/'lc-coding/contracts/lifecycle.json').read_text())
expected=['PROPOSAL_READINESS','PROJECT_INITIALIZATION','CALABASH_DRAFT','WORKFLOW_UI_SIMULATION','MANDATORY_CALABASH_UPGRADE','PRODUCT_BASELINE','FEATURE_SLICE','FEATURE_INTEGRATION','LOOP_ENGINEERING','FINAL_VERIFICATION','OWNER_ACCEPTANCE','DELIVERY']
assert contract['mainline']==expected
assert contract['required_transitions']==dict(zip(expected,expected[1:]))
con=(root/'CONSTITUTION.md').read_text(encoding='utf-8')
for x in ['Workflow capability end','UI product-surface end','Simulation World','Mandatory Calabash Upgrade','Feature Slice','Owner Acceptance','Delivery']:
    assert x in con
print('PASS: mainline')

phases=json.loads((root/'lc-coding/contracts/phases.json').read_text())
assert phases['mainline_unchanged'] is True
assert phases['phases'][1]=={
    'id':'PRODUCT_FORMATION','start':'CALABASH_DRAFT',
    'end_before':'MANDATORY_CALABASH_UPGRADE','exit_gate':'CALABASH_UPGRADE_READY',
}
assert phases['phases'][2]['aggregate_exit_gate']=='ALL_REQUIRED_RUNS_ACCEPTED'
assert phases['phases'][3]['exit_gate']=='DELIVERY_READY'

spec=(root/'SPEC.md').read_text(encoding='utf-8')
skill=(root/'lc-coding/SKILL.md').read_text(encoding='utf-8')
readme=(root/'README.md').read_text(encoding='utf-8')
readme_zh=(root/'README.zh-CN.md').read_text(encoding='utf-8')
method_mainline=(root/'lc-coding/references/method-mainline.md').read_text(encoding='utf-8')
dual_end=(root/'lc-coding/references/dual-end-design.md').read_text(encoding='utf-8')
simulation=(root/'lc-coding/references/simulation-world.md').read_text(encoding='utf-8')

semantic_checks=[
    (spec,'SPEC Workflow',[
        'Workflow is not merely a plan, description, or flowchart',
        'AI must use Calabash and the Simulation World',
        'real, runnable business functions',
        'simulation-only results cannot substitute for real Workflow',
        'every business line is classified as `CORE` or `EXTRA`',
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
        'Use Calabash and the Simulation World to split Workflow into enough business lines',
        'real, runnable business functions',
        'cannot replace real Workflow',
        'until Mandatory Calabash Upgrade is complete',
        'mark every business line `CORE` or `EXTRA`',
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

mainline_marker='[Simulation World foundation first → Workflow capability end ∥ UI product-surface end]'
for relative in ['CONSTITUTION.md','SPEC.md','README.md','lc-coding/SKILL.md','lc-coding/references/method-mainline.md']:
    mainline_text=(root/relative).read_text(encoding='utf-8')
    assert mainline_marker in mainline_text, relative
    assert 'Workflow/UI/Simulation [Simulation' not in mainline_text, relative
assert '[先建立 Simulation World foundation → Workflow 能力端 ∥ UI 产品呈现端分别推进]' in readme_zh
assert 'Workflow/UI/Simulation [先建立 Simulation' not in readme_zh
assert 'Calabash Draft → [Simulation foundation first → Workflow ∥ UI]' in con

simulation_first_checks=[
    (spec,'SPEC Simulation-first',[
        'Before actual Workflow or UI construction begins',
        'minimal, real, runnable, versioned Simulation World foundation',
        'Workflow and UI advance as equal product ends',
        'each must produce real, runnable, inspectable results',
        'does not require Workflow and UI to be connected or all three elements to be jointly integrated',
        'Cross-layer Workflow-to-UI connection and end-to-end proof remain responsibilities of Feature Slice and UI-locked Integration',
        'Simulation remains `VERSIONED_MUTABLE`',
    ]),
    (skill,'SKILL Simulation-first',[
        'Build a minimal, real, runnable, versioned Simulation World foundation before actual Workflow or UI construction',
        'Then advance Workflow and UI as equal product ends, independently; they may proceed in parallel',
        'real, runnable, inspectable result',
        'Do not require early Workflow-to-UI connection or three-way joint integration',
        'Continue semantic and scenario synchronization without treating it as early integration',
        'Keep cross-layer connection and end-to-end proof in Feature Slice and UI-locked Integration',
        'never treat the foundation as a complete or frozen Simulation',
    ]),
    (dual_end,'dual-end reference',[
        'After the Simulation World foundation exists',
        'independently runnable and inspectable',
        'Cross-layer connection is not an early Product Formation condition',
    ]),
    (simulation,'Simulation reference',[
        'minimum real, runnable, versioned foundation',
        'before actual Workflow or UI construction',
        'not a one-time complete freeze',
        '`VERSIONED_MUTABLE`',
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
assert '| Workflow ID | Classification (CORE/EXTRA) |' in workflow_map
assert workflow_map.count('Classification (CORE/EXTRA)')==1
example_workflow_map=(root/'lc-coding/examples/enterprise-clinic/.lccoding/WORKFLOW-MAP.md').read_text(encoding='utf-8')
assert '| Workflow ID | Classification (CORE/EXTRA) |' in example_workflow_map
