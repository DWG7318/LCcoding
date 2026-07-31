from pathlib import Path
import hashlib
import json
root=Path(__file__).resolve().parents[2]
lifecycle_path=root/'lc-coding/contracts/lifecycle.json'
phases_path=root/'lc-coding/contracts/phases.json'
status_template_path=root/'lc-coding/templates/STATUS.json'
contract=json.loads(lifecycle_path.read_text())
expected=['PROPOSAL_READINESS','PROJECT_INITIALIZATION','CALABASH_DRAFT','WORKFLOW_UI_SIMULATION','MANDATORY_CALABASH_UPGRADE','PRODUCT_BASELINE','FEATURE_SLICE','FEATURE_INTEGRATION','LOOP_ENGINEERING','FINAL_VERIFICATION','OWNER_ACCEPTANCE','DELIVERY']
assert contract['mainline']==expected
con=(root/'CONSTITUTION.md').read_text(encoding='utf-8')
for x in ['Workflow capability end','UI product-surface end','Simulation World','Mandatory Calabash Upgrade','Feature Slice','Owner Acceptance','Delivery']:
    assert x in con
print('PASS: mainline')

phases=json.loads(phases_path.read_text())
assert phases['mainline_unchanged'] is True
assert phases['phases'][2]['aggregate_exit_gate']=='ALL_REQUIRED_RUNS_ACCEPTED'
assert phases['phases'][3]['exit_gate']=='DELIVERY_READY'

# This definition-only change must not add or alter lifecycle nodes, phases,
# states, or gates.
assert hashlib.sha256(lifecycle_path.read_bytes()).hexdigest() == 'cd0ab53fc091fef5900a760243fbf66d0c377b22baa866deda79262975c551d0'
assert hashlib.sha256(phases_path.read_bytes()).hexdigest() == '2a198156a0fb1d3ec07b4079fa51282b463f2bea1096cade24a6f56f4c257877'
assert hashlib.sha256(status_template_path.read_bytes()).hexdigest() == '86003c4e100a4fd22237e820795f738ff4d76b96c20ad5ab70bca1894f8d340d'

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
