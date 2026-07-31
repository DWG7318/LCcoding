from pathlib import Path
import json
root=Path(__file__).resolve().parents[2]
lifecycle_path=root/'lc-coding/contracts/lifecycle.json'
phases_path=root/'lc-coding/contracts/phases.json'
status_template_path=root/'lc-coding/templates/STATUS.json'
contract=json.loads(lifecycle_path.read_text())
expected=['PROPOSAL_READINESS','PROJECT_INITIALIZATION','CALABASH_DRAFT','WORKFLOW_UI_SIMULATION','MANDATORY_CALABASH_UPGRADE','PRODUCT_BASELINE','FEATURE_SLICE','FEATURE_INTEGRATION','LOOP_ENGINEERING','FINAL_VERIFICATION','OWNER_ACCEPTANCE','DELIVERY']
assert contract['mainline']==expected
assert contract['required_transitions']==dict(zip(expected,expected[1:]))
assert contract['phase_contract']=='phases.json'
con=(root/'CONSTITUTION.md').read_text(encoding='utf-8')
for x in ['Workflow capability end','UI product-surface end','Simulation World','Mandatory Calabash Upgrade','Feature Slice','Owner Acceptance','Delivery']:
    assert x in con
print('PASS: mainline')

phases=json.loads(phases_path.read_text())
assert phases['mainline_unchanged'] is True
assert phases['phases'][2]['aggregate_exit_gate']=='ALL_REQUIRED_RUNS_ACCEPTED'
assert phases['phases'][3]['exit_gate']=='DELIVERY_READY'

# This definition-only change must preserve the canonical lifecycle order,
# phase boundaries, and existing STATUS lifecycle keys without freezing whole
# files against unrelated future edits.
expected_phase_ids=['INITIAL','PRODUCT_FORMATION','ENGINEERING_RUNS','DELIVERY_PREPARATION']
assert [phase['id'] for phase in phases['phases']]==expected_phase_ids
boundaries={
    f"{phase['id']}.{key}": value
    for phase in phases['phases']
    for key,value in phase.items()
    if key in {'start','start_after','end_before','per_run_end_before'}
}
assert boundaries=={
    'INITIAL.start':'PROPOSAL_READINESS',
    'INITIAL.end_before':'CALABASH_DRAFT',
    'PRODUCT_FORMATION.start':'CALABASH_DRAFT',
    'PRODUCT_FORMATION.end_before':'MANDATORY_CALABASH_UPGRADE',
    'ENGINEERING_RUNS.start':'MANDATORY_CALABASH_UPGRADE',
    'ENGINEERING_RUNS.per_run_end_before':'LOOP_OWNER_ACCEPTANCE',
    'DELIVERY_PREPARATION.start_after':'ALL_REQUIRED_RUNS_ACCEPTED',
    'DELIVERY_PREPARATION.end_before':'DELIVERY',
}
gates={
    f"{phase['id']}.{key}": tuple(value) if isinstance(value,list) else value
    for phase in phases['phases']
    for key,value in phase.items()
    if key in {'entry_gate','exit_gate','per_run_exit_gate','aggregate_exit_gate','required_subgates'}
}
assert gates=={
    'INITIAL.exit_gate':'INITIAL_READY',
    'PRODUCT_FORMATION.exit_gate':'CALABASH_UPGRADE_READY',
    'ENGINEERING_RUNS.entry_gate':'FEATURE_SLICE_EXECUTION_COVERAGE_PASS',
    'ENGINEERING_RUNS.per_run_exit_gate':'LOOP_OWNER_ACCEPTANCE_READY',
    'ENGINEERING_RUNS.aggregate_exit_gate':'ALL_REQUIRED_RUNS_ACCEPTED',
    'DELIVERY_PREPARATION.required_subgates':(
        'CENTRALIZED_VULNERABILITY_AUDIT',
        'SECURITY_REMEDIATION',
        'INDEPENDENT_SECURITY_REAUDIT',
        'VULNERABILITY_CLOSURE',
        'POST_SECURITY_OWNER_ACCEPTANCE',
        'DELIVERY_METHOD_QA',
        'DELIVERY_PACKAGE_GUARD',
    ),
    'DELIVERY_PREPARATION.exit_gate':'DELIVERY_READY',
}

status=json.loads(status_template_path.read_text())
assert contract['version']==phases['version']==status['status_schema_version']=='2.2.0'
assert status['record_role']=='AUTHORITATIVE_PROJECT_STATUS'
assert status['current_phase']=='INITIAL'
assert tuple(status['phase_gates'])==(
    'INITIAL_READY',
    'CALABASH_UPGRADE_READY',
    'ALL_REQUIRED_RUNS_ACCEPTED',
    'DELIVERY_READY',
)
assert set(status['phase_gates'].values())=={'PENDING'}
assert [key for key in status if 'workflow' in key.lower()]==['workflow']
serialized=json.dumps((contract,phases,status)).lower()
assert 'workflow_realization' not in serialized
assert 'workflow_feasibility' not in serialized

spec=(root/'SPEC.md').read_text(encoding='utf-8')

# Workflow is real product behavior, not a design-only placeholder.
for marker in [
    'Workflow is not merely a plan, description, or flowchart',
    'AI must use Calabash and the Simulation World',
    'enough business lines to cover the product',
    'real, runnable business functions',
    'Early implementation may be scattered and need not immediately connect to UI',
    'plans, empty shells, mocks, or simulation-only results cannot substitute for real Workflow',
    'until the Mandatory Calabash Upgrade is complete',
]:
    assert marker in spec

skill=(root/'lc-coding/SKILL.md').read_text(encoding='utf-8')

# The Agent-facing skill must carry the same three operational definitions.
for marker in [
    'Use Calabash and the Simulation World to split Workflow into enough business lines',
    'real, runnable business functions',
    'may start scattered and need not yet connect to UI',
    'Plans, empty shells, mocks, and simulation-only results cannot replace real Workflow',
    'until Mandatory Calabash Upgrade is complete',
]:
    assert marker in skill, f'missing Workflow realization rule in SKILL.md: {marker}'

for marker in [
    'Do not freeze Product Baseline while any required Workflow is not real and runnable',
    'proved infeasible under current product constraints',
    'adjust Calabash, narrow, hold, or terminate',
]:
    assert marker in skill, f'missing Product Baseline rule in SKILL.md: {marker}'

for marker in [
    'already implemented and verified Workflow capabilities',
    'inherit and reuse them wherever possible',
    'UI, Integration, state, data, permissions, exceptions, recovery, and visible results',
    'supplement, adjust, or improve Workflow',
    'Impact Analysis and `CONTROLLED_MUTABLE`',
]:
    assert marker in skill, f'missing Feature Slice inheritance rule in SKILL.md: {marker}'

# Product Baseline cannot admit a required Workflow that is unrealized or
# proved infeasible under the current product constraints.
for marker in [
    'must not enter Product Baseline',
    'not yet implemented as real, runnable behavior',
    'proved infeasible under the current product constraints',
    'adjust Calabash, narrow the direction, hold, or terminate',
]:
    assert marker in spec

# Feature Slice inherits prior Workflow proof but remains allowed to improve
# Workflow under the existing impact and controlled-mutable rules.
for marker in [
    'already implemented and verified Workflow capabilities',
    'inherit and reuse them wherever possible',
    'UI, Integration, state, data, permissions, exceptions, recovery, and actor-visible results',
    'may supplement, adjust, and improve Workflow',
    'Impact Analysis and `CONTROLLED_MUTABLE` rules',
]:
    assert marker in spec
