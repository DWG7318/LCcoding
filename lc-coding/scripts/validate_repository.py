#!/usr/bin/env python3
from pathlib import Path
import sys

REQUIRED=[
'VERSION','README.md','README.zh-CN.md','CONSTITUTION.md','SPEC.md','CHANGELOG.md','MIGRATION-1.1.1-TO-2.0.0.md','MIGRATION-2.0.0-TO-2.1.0.md','MIGRATION-2.1.0-TO-2.2.0.md','MIGRATION-2.2.0-TO-2.2.1.md','MIGRATION-2.2.1-TO-2.2.2.md','MIGRATION-2.2.2-TO-2.2.3.md','MIGRATION-2.2.3-TO-2.3.0.md','MIGRATION-2.3.0-TO-2.4.0.md','MIGRATION-2.4.0-TO-2.4.1.md','MIGRATION-2.4.1-TO-2.5.0.md','MIGRATION-2.5.0-TO-2.5.1.md','MIGRATION-2.5.1-TO-2.5.2.md','MIGRATION-2.5.2-TO-2.6.0.md',
'lc-coding/SKILL.md','lc-coding/references/verification-de-duplication.md',
'lc-coding/contracts/loop-control-contract.json','lc-coding/templates/LOOP-CONTROL-BINDING.json','lc-coding/references/loop-control-contract.md',
'lc-coding/references/delivery-governance.md','lc-coding/references/feature-slice-and-integration.md','lc-coding/templates/FEATURE-SLICE.md','lc-coding/templates/INTEGRATION-BASELINE.md',
'lc-coding/templates/VERIFICATION-RECEIPT.json','lc-coding/scripts/bootstrap_lccoding.py','lc-coding/scripts/validate_project.py',
'lc-coding/tests/run_tests.py','lc-coding/contracts/lifecycle.json','lc-coding/contracts/phases.json',
'lc-coding/references/lifecycle-phases.md','lc-coding/references/vulnerability-closure.md','lc-coding/references/delivery-method-qa.md',
'lc-coding/templates/LOOP-OWNER-ACCEPTANCE.md','lc-coding/templates/POST-SECURITY-OWNER-ACCEPTANCE.md',
'lc-coding/templates/SECURITY-AUDIT-REPORT.json','lc-coding/templates/VULNERABILITY-CLOSURE.json',
'lc-coding/templates/DELIVERY-METHOD-QA.md','lc-coding/templates/DELIVERY-DECISION.json','lc-coding/references/project-initialization.md','lc-coding/templates/PROJECT-FINGERPRINT.json']
MARKERS=['Workflow capability end','UI product-surface end','Simulation World','Mandatory Calabash Upgrade','Product Baseline','Feature Slice','UI-locked Real Product Integration','Cross-Phase Execution Methods','Independent layered Verification','Owner Acceptance','Delivery','INITIAL','PRODUCT_FORMATION','ENGINEERING_RUNS','DELIVERY_PREPARATION','Loop Owner Acceptance','Centralized Vulnerability Audit','Post-Security Owner Acceptance','Delivery Method Q&A','Existing engineering mode','Fixed lifecycle, proportional depth','authoritative durable project status','Execution Coverage Preflight','Owner gap']

def main():
    root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve(); errors=[]
    for x in REQUIRED:
        if not (root/x).is_file(): errors.append('missing '+x)
    if (root/'VERSION').is_file() and (root/'VERSION').read_text().strip()!='2.6.0': errors.append('bad VERSION')
    con=(root/'CONSTITUTION.md').read_text(encoding='utf-8') if (root/'CONSTITUTION.md').is_file() else ''
    alltext=con+'\n'+((root/'README.zh-CN.md').read_text(encoding='utf-8') if (root/'README.zh-CN.md').is_file() else '')
    for m in MARKERS:
        if m not in alltext: errors.append('canonical docs missing '+m)
    if errors:
        print('FAIL'); print('\n'.join(errors)); raise SystemExit(1)
    print('PASS: LCCoding repository structure, mainline, acceptance, and security sequence are valid.')
if __name__=='__main__': main()
