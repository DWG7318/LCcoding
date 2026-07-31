from pathlib import Path
import json
root=Path(__file__).resolve().parents[2]
contract=json.loads((root/'lc-coding/contracts/lifecycle.json').read_text())
expected=['PROPOSAL_READINESS','PROJECT_INITIALIZATION','CALABASH_DRAFT','WORKFLOW_UI_SIMULATION','MANDATORY_CALABASH_UPGRADE','PRODUCT_BASELINE','FEATURE_SLICE','FEATURE_INTEGRATION','LOOP_ENGINEERING','FINAL_VERIFICATION','OWNER_ACCEPTANCE','DELIVERY']
assert contract['mainline']==expected
con=(root/'CONSTITUTION.md').read_text(encoding='utf-8')
for x in ['Workflow capability end','UI product-surface end','Simulation World','Mandatory Calabash Upgrade','Feature Slice','Owner Acceptance','Delivery']:
    assert x in con
print('PASS: mainline')

phases=json.loads((root/'lc-coding/contracts/phases.json').read_text())
assert phases['mainline_unchanged'] is True
assert phases['phases'][2]['aggregate_exit_gate']=='ALL_REQUIRED_RUNS_ACCEPTED'
assert phases['phases'][3]['exit_gate']=='DELIVERY_READY'

spec=(root/'SPEC.md').read_text(encoding='utf-8')
skill=(root/'lc-coding/SKILL.md').read_text(encoding='utf-8')

semantic_checks=[
    (spec,'SPEC Workflow',[
        'Workflow is not merely a plan, description, or flowchart',
        'AI must use Calabash and the Simulation World',
        'real, runnable business functions',
        'simulation-only results cannot substitute for real Workflow',
    ]),
    (spec,'SPEC Product Baseline',[
        'must not enter Product Baseline',
        'proved infeasible under the current product constraints',
        'adjust Calabash, narrow the direction, hold, or terminate',
    ]),
    (spec,'SPEC Feature Slice',[
        'already implemented and verified Workflow capabilities',
        'inherit and reuse them wherever possible',
        'may supplement, adjust, and improve Workflow',
        'Impact Analysis and `CONTROLLED_MUTABLE` rules',
    ]),
    (skill,'SKILL Workflow',[
        'Use Calabash and the Simulation World to split Workflow into enough business lines',
        'real, runnable business functions',
        'cannot replace real Workflow',
        'until Mandatory Calabash Upgrade is complete',
    ]),
    (skill,'SKILL Product Baseline',[
        'Do not freeze Product Baseline while any required Workflow is not real and runnable',
        'proved infeasible under current product constraints',
        'adjust Calabash, narrow, hold, or terminate',
    ]),
    (skill,'SKILL Feature Slice',[
        'already implemented and verified Workflow capabilities',
        'inherit and reuse them wherever possible',
        'supplement, adjust, or improve Workflow',
        'Impact Analysis and `CONTROLLED_MUTABLE` rules',
    ]),
]
for document,label,markers in semantic_checks:
    for marker in markers:
        assert marker in document, f'missing {label} rule: {marker}'

status=json.loads((root/'lc-coding/templates/STATUS.json').read_text())
framework=json.dumps((contract,phases,status)).lower()
for forbidden in ['workflow_realization','workflow realization','workflow_feasibility','workflow feasibility']:
    assert forbidden not in framework
