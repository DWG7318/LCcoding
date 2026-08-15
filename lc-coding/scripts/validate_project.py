#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timedelta, timezone
import argparse, hashlib, importlib.util, json, re, subprocess

_PHASE_VALIDATOR_PATH=Path(__file__).with_name('validate_phase_status.py')
_PHASE_VALIDATOR_SPEC=importlib.util.spec_from_file_location(
    'lccoding_validate_phase_status',_PHASE_VALIDATOR_PATH
)
_PHASE_VALIDATOR=importlib.util.module_from_spec(_PHASE_VALIDATOR_SPEC)
_PHASE_VALIDATOR_SPEC.loader.exec_module(_PHASE_VALIDATOR)
COMPLETED_PHASE_STATES=_PHASE_VALIDATOR.COMPLETED_PHASE_STATES
_completed_evidence=_PHASE_VALIDATOR.completed_evidence
_normalize_lifecycle_state=_PHASE_VALIDATOR.normalize_lifecycle_state
validate_phase_status_record=_PHASE_VALIDATOR.validate_phase_status

def normalize_lifecycle_state(value):
    if isinstance(value,dict) and set(value).issuperset({'state'}): value=value.get('state')
    return _normalize_lifecycle_state(value)

def completed_evidence(value):
    if isinstance(value,dict) and set(value).issuperset({'state'}): value=value.get('state')
    return _completed_evidence(value)

_METHOD_BASELINE_VALIDATOR_PATH=Path(__file__).with_name('validate_method_baseline.py')
_METHOD_BASELINE_VALIDATOR_SPEC=importlib.util.spec_from_file_location(
    'lccoding_validate_method_baseline',_METHOD_BASELINE_VALIDATOR_PATH
)
_METHOD_BASELINE_VALIDATOR=importlib.util.module_from_spec(_METHOD_BASELINE_VALIDATOR_SPEC)
_METHOD_BASELINE_VALIDATOR_SPEC.loader.exec_module(_METHOD_BASELINE_VALIDATOR)
validate_method_baseline_records=_METHOD_BASELINE_VALIDATOR.validate_method_baseline_records

_VULNERABILITY_VALIDATOR_PATH=Path(__file__).with_name('validate_vulnerability_closure.py')
_VULNERABILITY_VALIDATOR_SPEC=importlib.util.spec_from_file_location(
    'lccoding_validate_vulnerability_closure',_VULNERABILITY_VALIDATOR_PATH
)
_VULNERABILITY_VALIDATOR=importlib.util.module_from_spec(_VULNERABILITY_VALIDATOR_SPEC)
_VULNERABILITY_VALIDATOR_SPEC.loader.exec_module(_VULNERABILITY_VALIDATOR)
validate_vulnerability_receipt=_VULNERABILITY_VALIDATOR.validate_receipt
strict_vulnerability_json=_VULNERABILITY_VALIDATOR.strict_json
_AGENT_NATIVE_PATH=Path(__file__).with_name('validate_agent_native.py')
_AGENT_NATIVE_SPEC=importlib.util.spec_from_file_location('lccoding_validate_agent_native',_AGENT_NATIVE_PATH)
_AGENT_NATIVE=importlib.util.module_from_spec(_AGENT_NATIVE_SPEC)
_AGENT_NATIVE_SPEC.loader.exec_module(_AGENT_NATIVE)
VULNERABILITY_CONTRACT=json.loads(
    _VULNERABILITY_VALIDATOR.CONTRACT_PATH.read_text(encoding='utf-8')
)
LOOP_CONTROL_CONTRACT_PATH=Path(__file__).resolve().parents[1]/'contracts/loop-control-contract.json'
LOOP_CONTROL_BINDING_NAME='LOOP-CONTROL-BINDING.json'
LOOP_CONTROL_METHODS={'SLK','CLK','GLK'}
AGENT_CONFIGURATION_BASELINE_NAME='AGENT-CONFIGURATION-BASELINE.json'
PRODUCTION_EXECUTION_TOPOLOGY_NAME='PRODUCTION-EXECUTION-TOPOLOGY.json'
RUNTIME_ADAPTER_ATTESTATION_NAME='RUNTIME-ADAPTER-ATTESTATION.json'

def validate_agent_native_artifacts(lc,status):
    if status.get('status_schema_version')!='2.8.0': return []
    errors=validate_agent_slice_status(lc,status)
    path=lc/AGENT_CONFIGURATION_BASELINE_NAME
    if not path.exists() and not path.is_symlink(): return errors
    if path.is_symlink() or not path.is_file(): return errors+['Agent Configuration Baseline must be a regular project file']
    candidate=status.get('canonical_candidate',{})
    return errors+_AGENT_NATIVE.validate_file(path,candidate.get('candidate_id'),candidate.get('candidate_hash'))

REQUIRED=['PROJECT-START.json','OWNER-POLICY.md','PROJECT-PROFILE.md','PROJECT-FINGERPRINT.json','PROJECT-HEALTH.json','AGENT-RULE.md','CANONICAL-MANIFEST.json','INTERPRETATION-LOCK.json','WORKFLOW-MAP.md','UI-MAP.md','SIMULATION-WORLD.md','status.json','PHASE-STATUS.json']
COMPLEXITY_FACTORS=['product_uncertainty','system_coupling','real_risk','irreversibility','novelty']
COMPLEXITY_LEVELS={'LOW','MEDIUM','HIGH','UNKNOWN'}
RUNTIME_STATUS_FIELDS={'session','session_id','process','process_id','pid','agent','agent_id','queue','retry','retries','attempt','orchestration','model','effort','hook','cli'}
SLICE_INTERNAL_METHOD_FIELDS={'go plan','cell tasks','stage plan','wave','agent model','task graph','retry queue'}
SLICE_PREFLIGHT_REQUIRED=['Actor intent','Product outcome','Product Baseline trace','Workflow references','UI references','Scenario IDs / versions','State / data / permission trace','Exception / recovery trace','Impact Analysis ID','Integration Baseline ID','Required Run IDs','D0-D3 evidence plan','Normal Loop Owner Acceptance route(s)']
OPEN_GAP_INDEX_FIELDS={'gap_id','state','source_acceptance','evidence_pointers'}
NOT_APPLICABLE={'','NONE','NOT_APPLICABLE'}
COMPONENT_VERSION_RE=re.compile(r'^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)$')
CONTENT_HASH_RE=re.compile(r'^sha256:[0-9a-f]{64}$',re.IGNORECASE)
EXACT_HASH_RE=re.compile(r'^sha256:[0-9a-f]{64}$')
SEMVER_RE=re.compile(r'^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?$')
STABLE_ID_RE=re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$')
EXECUTION_METHOD_KEYS={
    'method_id','version','exact_hash','canonical_contract_reference',
    'run_evidence_mapping','owner_acceptance_mapping','required_control_binding',
    'compatibility_result',
}
START_REQUIRED_FIELDS={
    'Artifact role','Start Contract ID','Start Contract SHA-256','Run ID',
    'Status schema version','LCCoding phase scope','Phase-owned objective',
    'Calling phase authority / contract reference(s)','Frozen Run scope',
    'Explicit exclusions','Selected execution method ID',
    'Selected execution method version','Selected execution method exact hash',
    'Selected execution method canonical interface / contract reference',
    'Phase-appropriate input evidence / prerequisites',
    'Evidence return target in calling phase',
    'D0-D3 evidence / verification condition','Loop Owner Acceptance condition / route',
    'Risk / depth decision','Readiness result','Blocker evidence',
}
LEGACY_PHASE3_START_FIELDS={
    'Product Baseline trace (ENGINEERING_RUNS only)',
    'Feature Slice ID / version (ENGINEERING_RUNS only)',
    'Applicable UI / Integration Baseline (ENGINEERING_RUNS only)',
}
PHASE3_START_FIELDS={
    'Product Baseline trace (REAL_PRODUCT_INTEGRATION only)',
    'Feature Slice ID / version (REAL_PRODUCT_INTEGRATION only)',
    'Applicable UI / Integration Baseline (REAL_PRODUCT_INTEGRATION only)',
}
DEFINITION_START_FIELDS={
    'Meaning impact classification',
    'Definition basis / neutral Impact Analysis reference',
    'Applicable Snake / Scorpion disposition evidence reference',
}
START_REQUIRED_FIELDS=START_REQUIRED_FIELDS|DEFINITION_START_FIELDS
START_ALLOWED_FIELDS=START_REQUIRED_FIELDS|PHASE3_START_FIELDS|LEGACY_PHASE3_START_FIELDS
RECEIPT_REQUIRED_FIELDS={
    'Artifact role','Acceptance ID','Run ID','Run-start contract ID',
    'Run-start contract SHA-256','Status schema version','LCCoding phase scope','Phase-owned objective',
    'Candidate ID / hash','D3 Receipt','Entry / role / account','Scenario IDs',
    'Acceptance steps','Product questions','Prior accepted dependencies reused',
    'Invisible risks already verified','Known limits',
    'Evidence return target in the calling phase',
    'Calling phase gate remains independently evaluated','Owner result',
    'Owner Gap ID (blank when accepted)','Gap source Acceptance ID',
    'Gap source candidate / scenario','Gap route','Impact / definition reference',
    'Correction Run IDs','Affected D0-D3 receipts','Delta re-verification receipt',
    'Delta Owner re-acceptance receipt','Gap status',
    'Product learning / route (may be blank; only consequential learning that changes a future decision, constraint, check, template, or reuse rule; update one existing canonical artifact)',
    'Accepted at',
}
PHASE_IDS_BY_SCHEMA=_PHASE_VALIDATOR.SCHEMA_PHASE_ORDERS
PHASE_IDS=set(PHASE_IDS_BY_SCHEMA['2.8.0'])
LEGACY_METHOD_INTERFACES={
    'SLK':'LEGACY_SLK_RUN_CONTRACT',
    'CLK':'LEGACY_CLK_RUN_CONTRACT',
    'GLK':'LEGACY_GLK_RUN_CONTRACT',
}
CALABASH_HANDOFF_FIELDS={
    'Artifact role','Definition Handoff ID','Definition Baseline kind',
    'Definition Baseline ID','Definition Baseline semantic version',
    'Definition Baseline exact hash','Calabash standard version','Baseline status',
    'Applicable Definition clause references','Snake review status',
    'Snake review scope','Snake review evidence refs','Scorpion review status',
    'Scorpion review scope','Scorpion review evidence refs',
    'Meaning-change / invalidation rules reference','Upgrade Receipt ID',
    'Upgrade Receipt exact hash','Upgrade verdict','Owner change authority',
    'Handoff result',
}
IMPACT_REQUIRED_FIELDS={
    'Artifact role','Analysis ID / version','Trigger / proposed change',
    'Meaning impact classification','Calling phase contract / authority',
    'Neutral rationale / evidence','Definition Baseline ID / exact hash',
    'Affected Definition clause references','Definition invalidation effect',
    'Governed Calabash update route / Owner authority',
    'Snake / Scorpion applicability and effect references','Impact result',
}
IMPACT_ALLOWED_FIELDS=IMPACT_REQUIRED_FIELDS|{
    'Owner Gap IDs / source Acceptance (if applicable)','Baseline and Slice',
    'Affected Calabash','Affected Workflow','Affected UI',
    'Affected Simulation scenarios','Affected shared capabilities / data / APIs',
    'Affected accepted Slices / Runs / evidence',
    'Existing evidence reused / unknown / contradicted',
    'Fingerprint complexity and proportional-depth response','Regression scope',
    'Release / rollback','Delta history','Gap closure evidence pointers',
    'Owner decision',
}
SECURITY_IMPACT_FIELDS={
    'Security change timing','Prior candidate ID / exact hash',
    'Current candidate ID / exact hash','Security change classification',
    'Changed security surface categories','Affected security surface IDs',
    'Transitive affected surface IDs / evidence',
    'Prior Vulnerability Closure Receipt ID / reference',
    'Prior Post-Security Owner Acceptance ID / reference',
    'Security neutral / preservation evidence','Security invalidation evidence',
    'Required security action',
}
IMPACT_ALLOWED_FIELDS=IMPACT_ALLOWED_FIELDS|SECURITY_IMPACT_FIELDS
SECURITY_CHANGE_TIMINGS={
    'BEFORE_SECURITY_CLOSURE','AFTER_VULNERABILITY_CLOSED',
    'AFTER_POST_SECURITY_OWNER_ACCEPTED',
}
SECURITY_CHANGE_CLASSIFICATIONS={
    'MATERIAL_SECURITY_SURFACE_CHANGE','PROVEN_SECURITY_SURFACE_NEUTRAL',
    'EVIDENCE_EQUIVALENT_PACKAGING_TRANSFORMATION',
}
IMPACT_UNSTARTED_FIELD_VALUES={
    'Artifact role':'IMPACT_ANALYSIS',
    'Meaning impact classification':'MEANING_CHANGING / MEANING_NEUTRAL',
    'Definition invalidation effect':'INVALIDATES / NO_DEFINITION_INVALIDATION',
    'Security change timing':(
        'BEFORE_SECURITY_CLOSURE / AFTER_VULNERABILITY_CLOSED / '
        'AFTER_POST_SECURITY_OWNER_ACCEPTED'
    ),
    'Security change classification':(
        'MATERIAL_SECURITY_SURFACE_CHANGE / PROVEN_SECURITY_SURFACE_NEUTRAL / '
        'EVIDENCE_EQUIVALENT_PACKAGING_TRANSFORMATION'
    ),
    'Changed security surface categories':'NONE',
    'Affected security surface IDs':'NONE',
    'Transitive affected surface IDs / evidence':'NONE',
    'Prior Vulnerability Closure Receipt ID / reference':'NOT_APPLICABLE',
    'Prior Post-Security Owner Acceptance ID / reference':'NOT_APPLICABLE',
    'Security neutral / preservation evidence':'NOT_APPLICABLE',
    'Security invalidation evidence':'NOT_APPLICABLE',
    'Required security action':'PRESERVE_EXACT_CLOSURE / INVALIDATE_AND_RETURN_TO_AUDIT',
    'Impact result':'PASS / BLOCKED',
}
SECURITY_SURFACE_CATEGORIES={
    'PRODUCT_BEHAVIOR','DEPENDENCIES_SUPPLY_CHAIN','CONFIGURATION',
    'AUTHENTICATION_AUTHORIZATION','PRIVILEGE_BOUNDARIES',
    'DATA_HANDLING_ISOLATION','API_EXPOSURE','CLIENT_EXPOSURE',
    'INSTALLER_RUNTIME','MIGRATION_RECOVERY_LOGGING_OBSERVABILITY',
    'OTHER_DECLARED_SECURITY_SURFACE',
}
VULNERABILITY_STATUS_FIELDS={
    'state','candidate_id','candidate_hash','current_receipt_id',
    'current_receipt_reference','superseded_receipt_id',
    'superseded_receipt_reference','superseded_candidate_id',
    'superseded_candidate_hash',
}
POST_SECURITY_STATUS_FIELDS={
    'state','candidate_id','candidate_hash','current_acceptance_id',
    'current_acceptance_reference','vulnerability_closure_receipt_id',
    'vulnerability_closure_receipt_reference','superseded_acceptance_id',
    'superseded_acceptance_reference','superseded_candidate_id',
    'superseded_candidate_hash',
}
POST_SECURITY_RECEIPT_FIELDS={
    'Schema version','Artifact role','Acceptance ID',
    'Candidate ID / exact hash','Vulnerability Closure Receipt ID / reference',
    'Vulnerability Closure candidate ID / exact hash',
    'Covered remediation surface IDs','Changed remediation surface IDs',
    'Reused Loop Owner Acceptance Receipt IDs','Security Remediation Run IDs',
    'Critical smoke / delta evidence','Owner result','Supersession status',
    'Superseded by Acceptance ID / reference','Accepted at',
}
STATUS_FIELDS_270={
    'record_role','status_schema_version','project_id','updated_at',
    'initialization_mode','continuity_decision','takeover_readiness',
    'canonical_candidate','existing_project_attestation',
    'existing_project_classification','current_phase','phase_gates',
    'product_baseline','proposal','initialization','calabash_draft','workflow',
    'ui','simulation','mandatory_calabash_upgrade','active_slice',
    'integration_baseline','active_runs','loop_owner_acceptances',
    'open_owner_gaps','all_required_runs_accepted','centralized_security_audit',
    'security_remediation','vulnerability_closure',
    'post_security_owner_acceptance','delivery_method_qa','delivery',
    'last_material_change','next_action','evidence_pointers','blockers',
}
STATUS_FIELDS_280=STATUS_FIELDS_270|{'agent_product_formation','agent_slice_integration'}
AGENT_SLICE_INTEGRATION_FIELDS={
    'state','candidate_id','candidate_hash','product_baseline_id','product_baseline_hash',
    'configuration_baseline_id','configuration_baseline_hash',
    'production_topology_id','production_topology_hash',
    'runtime_adapter_attestation_id','runtime_adapter_attestation_hash',
    'runtime_adapter_id','runtime_adapter_version','dual_agent_isolation_state',
    'product_agent_applicability','product_integration_state',
    'product_agent_integration_state','operations_agent_integration_state',
    'accepted_product_slice_ids','accepted_operations_slice_ids',
    'required_operations_slice_id','current_product_slice_reference',
    'product_verification_reference','current_operations_slice_reference',
    'operations_verification_reference','integration_baseline_reference',
}
UNPROVED_AGENT_SLICE_INTEGRATION={
    'state':'UNPROVED','candidate_id':'NOT_APPLICABLE','candidate_hash':'NOT_APPLICABLE',
    'product_baseline_id':'NOT_APPLICABLE','product_baseline_hash':'NOT_APPLICABLE',
    'configuration_baseline_id':'NOT_APPLICABLE','configuration_baseline_hash':'NOT_APPLICABLE',
    'production_topology_id':'NOT_APPLICABLE','production_topology_hash':'NOT_APPLICABLE',
    'runtime_adapter_attestation_id':'NOT_APPLICABLE','runtime_adapter_attestation_hash':'NOT_APPLICABLE',
    'runtime_adapter_id':'NOT_APPLICABLE','runtime_adapter_version':'NOT_APPLICABLE',
    'dual_agent_isolation_state':'UNPROVED','product_agent_applicability':'UNPROVED',
    'product_integration_state':'UNPROVED','product_agent_integration_state':'UNPROVED',
    'operations_agent_integration_state':'UNPROVED','accepted_product_slice_ids':[],
    'accepted_operations_slice_ids':[],'required_operations_slice_id':'NOT_APPLICABLE',
    'current_product_slice_reference':'NOT_APPLICABLE','product_verification_reference':'NOT_APPLICABLE',
    'current_operations_slice_reference':'NOT_APPLICABLE','operations_verification_reference':'NOT_APPLICABLE',
    'integration_baseline_reference':'NOT_APPLICABLE',
}
AGENT_SLICE_REFERENCE_FIELDS=(
    'current_product_slice_reference','product_verification_reference',
    'current_operations_slice_reference','operations_verification_reference',
    'integration_baseline_reference',
)
DEFINITION_CLAUSE_RE=re.compile(
    r'^baseline:/(?:grandpa|product_architecture|ontology)(?:/[^,\s]+)*$'
    r'|^baseline:/full_layers/(?:contract|policy|workflow|action_catalog|adapter|eval_and_audit)(?:/[^,\s]+)*$'
)

def nested_forbidden_fields(value, forbidden, path=''):
    found=[]
    if isinstance(value,dict):
        for key,item in value.items():
            child=f'{path}.{key}' if path else key
            if key.lower() in forbidden: found.append(child)
            found.extend(nested_forbidden_fields(item,forbidden,child))
    elif isinstance(value,list):
        for index,item in enumerate(value):
            found.extend(nested_forbidden_fields(item,forbidden,f'{path}[{index}]'))
    return found

def exact_security_identity(candidate_id,candidate_hash):
    candidate_id=str(candidate_id or '').strip()
    candidate_hash=str(candidate_hash or '').strip()
    return (
        _VULNERABILITY_VALIDATOR.safe_id(candidate_id)
        and bool(EXACT_HASH_RE.fullmatch(candidate_hash))
    )

def _not_applicable_record(record,fields):
    return all(str(record.get(field,'')).strip()=='NOT_APPLICABLE' for field in fields)

def _agent_slice_status_shape(status):
    errors=[]; record=status.get('agent_slice_integration')
    if not isinstance(record,dict): return ['agent_slice_integration must be a closed object']
    missing=AGENT_SLICE_INTEGRATION_FIELDS-set(record); unknown=set(record)-AGENT_SLICE_INTEGRATION_FIELDS
    if missing: errors.append('agent_slice_integration missing fields '+', '.join(sorted(missing)))
    if unknown: errors.append('agent_slice_integration unknown fields '+', '.join(sorted(unknown)))
    if record.get('state')=='UNPROVED':
        if record!=UNPROVED_AGENT_SLICE_INTEGRATION:
            errors.append('UNPROVED agent_slice_integration must not claim completion evidence')
        return errors
    if record.get('state')!='AGENT_SLICES_ACCEPTED':
        errors.append('agent_slice_integration state is invalid')
    id_fields=(
        'candidate_id','product_baseline_id','configuration_baseline_id',
        'production_topology_id','runtime_adapter_attestation_id','runtime_adapter_id',
        'required_operations_slice_id',
    )
    hash_fields=(
        'candidate_hash','product_baseline_hash','configuration_baseline_hash',
        'production_topology_hash','runtime_adapter_attestation_hash',
    )
    for field in id_fields:
        if not _AGENT_NATIVE.safe_id(record.get(field)): errors.append('agent_slice_integration '+field+' is invalid')
    for field in hash_fields:
        if not _AGENT_NATIVE.exact_hash(record.get(field)): errors.append('agent_slice_integration '+field+' is invalid')
    if not isinstance(record.get('runtime_adapter_version'),str) or not SEMVER_RE.fullmatch(record.get('runtime_adapter_version','')):
        errors.append('agent_slice_integration runtime_adapter_version is invalid')
    if record.get('dual_agent_isolation_state')!='VERIFIED': errors.append('Agent Slice integration requires verified dual-Agent isolation')
    applicability=record.get('product_agent_applicability')
    if applicability not in _AGENT_NATIVE.PRODUCT_APPLICABILITY: errors.append('Agent Slice Product Agent applicability is invalid')
    if record.get('product_integration_state')!='ACCEPTED': errors.append('Agent Slice PRODUCT integration is not accepted')
    if record.get('operations_agent_integration_state')!='ACCEPTED': errors.append('Agent Slice OPERATIONS integration is not accepted')
    expected_product_agent_state='NOT_APPLICABLE' if applicability=='NOT_APPLICABLE' else 'ACCEPTED'
    if record.get('product_agent_integration_state')!=expected_product_agent_state:
        errors.append('Product Agent Slice integration disagrees with applicability')
    return errors

def _closed_agent_slice_ids(value,label):
    if not isinstance(value,list) or not value: return None,[label+' must be a non-empty list']
    if any(not _AGENT_NATIVE.safe_id(item) for item in value): return None,[label+' contains an invalid Slice ID']
    if len(value)!=len(set(value)): return None,[label+' contains duplicate Slice IDs']
    return value,[]

def _resolve_agent_slice_reference(lc,reference):
    text=str(reference or '').strip()
    if not text or text=='NOT_APPLICABLE' or '\\' in text or '://' in text or Path(text).is_absolute(): return None
    relative=Path(text)
    if any(part in {'','.','..'} or ':' in part for part in relative.parts): return None
    candidate=Path(lc)
    for part in relative.parts:
        candidate=candidate/part
        if candidate.is_symlink(): return None
    try:
        resolved=candidate.resolve(strict=True); root=Path(lc).resolve(strict=True)
        if not resolved.is_relative_to(root) or not resolved.is_file(): return None
    except (OSError,RuntimeError,ValueError): return None
    return resolved

def _agent_file_hash(path):
    return 'sha256:'+hashlib.sha256(Path(path).read_bytes()).hexdigest()

def validate_agent_slice_status(lc,status):
    errors=_agent_slice_status_shape(status)
    record=status.get('agent_slice_integration') if isinstance(status,dict) else None
    if not isinstance(record,dict) or record.get('state')!='AGENT_SLICES_ACCEPTED': return errors
    if errors: return errors
    lc=Path(lc); candidate=status.get('canonical_candidate',{})
    if not isinstance(candidate,dict) or (record.get('candidate_id'),record.get('candidate_hash'))!=(candidate.get('candidate_id'),candidate.get('candidate_hash')):
        errors.append('Agent Slice integration candidate disagrees with authoritative candidate')
    formation=status.get('agent_product_formation',{})
    if not isinstance(formation,dict) or formation.get('state')!='PRODUCT_FORMATION_AGENT_BOUND' or formation.get('product_agent_applicability')!=record.get('product_agent_applicability'):
        errors.append('Agent Slice integration applicability disagrees with Product Formation')
    product_ids,id_errors=_closed_agent_slice_ids(record.get('accepted_product_slice_ids'),'accepted PRODUCT Slice IDs'); errors.extend(id_errors)
    operations_ids,id_errors=_closed_agent_slice_ids(record.get('accepted_operations_slice_ids'),'accepted OPERATIONS Slice IDs'); errors.extend(id_errors)
    if product_ids and operations_ids and set(product_ids)&set(operations_ids): errors.append('PRODUCT and OPERATIONS accepted Slice IDs must be disjoint')
    if operations_ids and record.get('required_operations_slice_id') not in operations_ids: errors.append('required Operations Slice is absent from accepted Operations IDs')
    references={field:_resolve_agent_slice_reference(lc,record.get(field)) for field in AGENT_SLICE_REFERENCE_FIELDS}
    for field,path in references.items():
        if path is None: errors.append('agent_slice_integration '+field+' is missing, outside project, or symlinked')
    resolved=[str(path).casefold() for path in references.values() if path is not None]
    if len(resolved)!=len(set(resolved)): errors.append('Agent Slice Feature, Final, and Baseline references must be distinct')

    config_path=lc/AGENT_CONFIGURATION_BASELINE_NAME
    topology_path=lc/PRODUCTION_EXECUTION_TOPOLOGY_NAME
    adapter_path=lc/RUNTIME_ADAPTER_ATTESTATION_NAME
    fixed_paths=(
        ('Agent Configuration Baseline',config_path,record.get('configuration_baseline_hash')),
        ('Production Execution Topology',topology_path,record.get('production_topology_hash')),
        ('Runtime Adapter Attestation',adapter_path,record.get('runtime_adapter_attestation_hash')),
    )
    for label,path,expected_hash in fixed_paths:
        if path.is_symlink() or not path.is_file(): errors.append(label+' must be a regular project file')
        elif _agent_file_hash(path)!=expected_hash: errors.append(label+' file hash disagrees with agent_slice_integration')
    if errors: return errors
    try:
        configuration=_AGENT_NATIVE.strict_json(config_path)
        topology=_AGENT_NATIVE.strict_json(topology_path)
        attestation=_AGENT_NATIVE.strict_json(adapter_path)
    except (OSError,UnicodeError,ValueError) as error:
        return errors+['Agent Slice integration JSON evidence is not strict UTF-8: '+str(error)]
    configuration_hash=_agent_file_hash(config_path)
    if record.get('configuration_baseline_id')!=configuration.get('configuration_baseline_id'):
        errors.append('Agent Slice Configuration Baseline ID disagrees')
    if record.get('product_agent_applicability')!=configuration.get('product_agent',{}).get('applicability'):
        errors.append('Agent Slice applicability disagrees with Agent Configuration Baseline')
    errors.extend(_AGENT_NATIVE.validate_file(config_path,record.get('candidate_id'),record.get('candidate_hash')))
    if record.get('production_topology_id')!=topology.get('topology_id'):
        errors.append('Agent Slice Production Topology ID disagrees')
    errors.extend(_AGENT_NATIVE.validate_production_topology_file(
        topology_path,configuration,configuration_hash,
        record.get('product_baseline_id'),record.get('product_baseline_hash'),
    ))
    runtime=attestation.get('runtime_adapter',{}) if isinstance(attestation,dict) else {}
    if record.get('runtime_adapter_attestation_id')!=attestation.get('attestation_id'):
        errors.append('Agent Slice Runtime Adapter Attestation ID disagrees')
    if (record.get('runtime_adapter_id'),record.get('runtime_adapter_version'))!=(runtime.get('adapter_id'),runtime.get('adapter_version')):
        errors.append('Agent Slice Runtime Adapter identity/version disagrees')
    as_of=datetime.now(timezone.utc).replace(microsecond=0).strftime('%Y-%m-%dT%H:%M:%SZ')
    errors.extend(_AGENT_NATIVE.validate_runtime_adapter_attestation_file(
        adapter_path,configuration,configuration_hash,
        record.get('production_topology_id'),record.get('production_topology_hash'),as_of,
    ))
    if errors: return errors

    product_feature=references['current_product_slice_reference']
    product_final=references['product_verification_reference']
    operations_feature=references['current_operations_slice_reference']
    operations_final=references['operations_verification_reference']
    baseline=references['integration_baseline_reference']
    slice_args=(
        configuration,configuration_hash,record.get('product_baseline_id'),record.get('product_baseline_hash'),
        record.get('production_topology_id'),record.get('production_topology_hash'),
        record.get('runtime_adapter_attestation_id'),record.get('runtime_adapter_attestation_hash'),
    )
    errors.extend(_AGENT_NATIVE.validate_agent_slice_files(product_feature,product_final,baseline,*slice_args))
    errors.extend(_AGENT_NATIVE.validate_agent_slice_files(operations_feature,operations_final,baseline,*slice_args))
    product_fields,_=_AGENT_NATIVE.markdown_fields(product_feature.read_text(encoding='utf-8'))
    operations_fields,_=_AGENT_NATIVE.markdown_fields(operations_feature.read_text(encoding='utf-8'))
    baseline_fields,_=_AGENT_NATIVE.markdown_fields(baseline.read_text(encoding='utf-8'))
    product_id=product_fields.get('Agent Slice ID'); operations_id=operations_fields.get('Agent Slice ID')
    if product_fields.get('Agent Slice class')!='PRODUCT' or not product_ids or product_id not in product_ids:
        errors.append('current PRODUCT Feature Slice is absent or misclassified')
    if operations_fields.get('Agent Slice class')!='OPERATIONS' or not operations_ids or operations_id not in operations_ids:
        errors.append('current OPERATIONS Feature Slice is absent or misclassified')
    baseline_product_ids=_AGENT_NATIVE.slice_id_list(baseline_fields.get('Agent Slice Baseline accepted PRODUCT Slice IDs'))
    baseline_operations_ids=_AGENT_NATIVE.slice_id_list(baseline_fields.get('Agent Slice Baseline accepted OPERATIONS Slice IDs'))
    if baseline_product_ids!=product_ids or baseline_operations_ids!=operations_ids:
        errors.append('STATUS accepted Slice ID sets disagree with shared Integration Baseline')
    if baseline_fields.get('Agent Slice Baseline required Operations Slice ID')!=record.get('required_operations_slice_id'):
        errors.append('STATUS required Operations Slice disagrees with shared Integration Baseline')
    return errors

def validate_security_status_shape(status):
    errors=[]
    closure=status.get('vulnerability_closure')
    acceptance=status.get('post_security_owner_acceptance')
    strict=isinstance(closure,dict) or isinstance(acceptance,dict)
    if not strict:
        return errors
    if not isinstance(closure,dict) or not isinstance(acceptance,dict):
        return ['current security status cannot mix scalar and structured authority']
    schema=status.get('status_schema_version')
    expected_fields=(
        STATUS_FIELDS_280 if schema=='2.8.0' else STATUS_FIELDS_270
        if schema in {'2.6.0','2.7.0'} else None
    )
    if expected_fields is None:
        return ['current security status has unsupported status_schema_version']
    missing=expected_fields-set(status); unknown=set(status)-expected_fields
    if missing:
        errors.append('current security status missing closed fields '+', '.join(sorted(missing)))
    if unknown:
        errors.append('current security status has unknown or second-authority fields '+', '.join(sorted(unknown)))
    if schema=='2.8.0':
        errors.extend(_AGENT_NATIVE.validate_product_formation_status(status.get('agent_product_formation')))
        errors.extend(_agent_slice_status_shape(status))
    for record,required,label in [
        (closure,VULNERABILITY_STATUS_FIELDS,'vulnerability_closure'),
        (acceptance,POST_SECURITY_STATUS_FIELDS,'post_security_owner_acceptance'),
    ]:
        missing=required-set(record); extra=set(record)-required
        if missing: errors.append(label+' missing closed identity fields '+', '.join(sorted(missing)))
        if extra: errors.append(label+' has unknown identity fields '+', '.join(sorted(extra)))
    if errors: return errors
    closure_state=closure.get('state')
    acceptance_state=acceptance.get('state')
    if closure_state not in {'PENDING','VULNERABILITY_CLOSED','INVALID'}:
        errors.append('vulnerability_closure state is invalid')
    if acceptance_state not in {'PENDING','POST_SECURITY_OWNER_ACCEPTED','INVALID'}:
        errors.append('post_security_owner_acceptance state is invalid')
    closure_identity_fields=VULNERABILITY_STATUS_FIELDS-{'state'}
    acceptance_identity_fields=POST_SECURITY_STATUS_FIELDS-{'state'}
    if closure_state=='PENDING' and acceptance_state=='PENDING':
        if not _not_applicable_record(closure,closure_identity_fields):
            errors.append('pending vulnerability_closure cannot claim receipt or candidate identity')
        if not _not_applicable_record(acceptance,acceptance_identity_fields):
            errors.append('pending Post-Security acceptance cannot claim receipt or candidate identity')
        return errors
    candidate=status.get('canonical_candidate')
    if not isinstance(candidate,dict) or not exact_security_identity(
        candidate.get('candidate_id'),candidate.get('candidate_hash')
    ):
        errors.append('current security status requires exact canonical candidate ID/hash')
        return errors
    current=(candidate.get('candidate_id'),candidate.get('candidate_hash'))
    invalid_states=(closure_state=='INVALID',acceptance_state=='INVALID')
    gate=status.get('phase_gates',{}).get('DELIVERY_READY')
    if any(invalid_states):
        for record,label in [(closure,'vulnerability_closure'),(acceptance,'post_security_owner_acceptance')]:
            if not exact_security_identity(record.get('candidate_id'),record.get('candidate_hash')):
                errors.append(label+' requires exact candidate ID/hash')
            elif (record.get('candidate_id'),record.get('candidate_hash'))!=current:
                errors.append(label+' security candidate identity disagrees with canonical candidate')
        if invalid_states!=(True,True) or gate!='INVALID':
            errors.append('security invalidation must atomically invalidate closure, Post-Security acceptance, and DELIVERY_READY')
        if not _not_applicable_record(closure,{'current_receipt_id','current_receipt_reference'}):
            errors.append('invalid closure cannot claim a current receipt')
        if not _not_applicable_record(
            acceptance,{
                'current_acceptance_id','current_acceptance_reference',
                'vulnerability_closure_receipt_id','vulnerability_closure_receipt_reference',
            }
        ):
            errors.append('invalid Post-Security acceptance cannot claim current receipts')
    elif closure_state=='VULNERABILITY_CLOSED':
        if (closure.get('candidate_id'),closure.get('candidate_hash'))!=current:
            errors.append('vulnerability_closure security candidate identity disagrees with canonical candidate')
        if any(
            str(closure.get(field,'')).strip() in {'','NOT_APPLICABLE'}
            for field in {'current_receipt_id','current_receipt_reference'}
        ):
            errors.append('current closure requires exact receipt identity/reference')
        if not _not_applicable_record(
            closure,{
                'superseded_receipt_id','superseded_receipt_reference',
                'superseded_candidate_id','superseded_candidate_hash',
            }
        ):
            errors.append('current closure cannot also claim superseded receipt identity')
        if acceptance_state=='POST_SECURITY_OWNER_ACCEPTED':
            if (acceptance.get('candidate_id'),acceptance.get('candidate_hash'))!=current:
                errors.append('post_security_owner_acceptance security candidate identity disagrees with canonical candidate')
            if any(
                str(acceptance.get(field,'')).strip() in {'','NOT_APPLICABLE'}
                for field in {
                    'current_acceptance_id','current_acceptance_reference',
                    'vulnerability_closure_receipt_id','vulnerability_closure_receipt_reference',
                }
            ):
                errors.append('current Post-Security acceptance requires exact receipt identity/reference')
            if not _not_applicable_record(
                acceptance,{
                    'superseded_acceptance_id','superseded_acceptance_reference',
                    'superseded_candidate_id','superseded_candidate_hash',
                }
            ):
                errors.append('current Post-Security acceptance cannot also claim superseded receipt identity')
        elif acceptance_state=='PENDING':
            if not _not_applicable_record(acceptance,acceptance_identity_fields):
                errors.append('pending Post-Security acceptance cannot claim receipt or candidate identity')
        else:
            errors.append('current Vulnerability Closure has an invalid Post-Security state relation')
    elif acceptance_state=='POST_SECURITY_OWNER_ACCEPTED':
        errors.append('Post-Security Owner Acceptance requires current Vulnerability Closure')
    return errors

def validate_status_authority(status,phase_status,health):
    errors=validate_phase_status_record(phase_status)
    status_schema=status.get('status_schema_version')
    phase_status_schema=phase_status.get('status_schema_version')
    phase_order=_PHASE_VALIDATOR.SCHEMA_PHASE_ORDERS.get(status_schema)
    if 'status_schema_version' not in status:
        errors.append('authoritative status_schema_version is required')
    elif phase_order is None:
        errors.append('unsupported authoritative status_schema_version')
    if phase_status_schema!=status_schema:
        errors.append('derived phase status schema disagrees with authoritative status schema')
    phase3=phase_order[2] if phase_order else None
    roles=[status.get('record_role'),phase_status.get('record_role'),health.get('record_role')]
    if roles.count('AUTHORITATIVE_PROJECT_STATUS')!=1:
        errors.append('single authoritative project status required')
    if status.get('record_role')!='AUTHORITATIVE_PROJECT_STATUS':
        errors.append('status.json must be the authoritative project status')
    if phase_status.get('record_role')!='DERIVED_VIEW' or phase_status.get('derived_from')!='status.json':
        errors.append('PHASE-STATUS.json must be a derived view of status.json')
    if health.get('record_role')!='ASSESSMENT_EVIDENCE':
        errors.append('Project Health must remain assessment evidence')
    for name,value in [('status.json',status),('PHASE-STATUS.json',phase_status),('PROJECT-HEALTH.json',health)]:
        for field in nested_forbidden_fields(value,RUNTIME_STATUS_FIELDS):
            errors.append(f'{name} contains runtime field {field}')
        for field in nested_forbidden_fields(value,{'product_baseline_ready'}):
            errors.append(f'{name} contains forbidden invented gate PRODUCT_BASELINE_READY at {field}')
        for field in nested_forbidden_fields(value,{'security_invalidation_ledger'}):
            errors.append(f'{name} contains forbidden second security invalidation authority at {field}')
    if phase_status.get('current_phase')!=status.get('current_phase'):
        errors.append('derived phase status disagrees with authoritative current_phase')
    gate_map={
        'INITIAL':('exit_gate','INITIAL_READY'),
        'DELIVERY_PREPARATION':('exit_gate','DELIVERY_READY'),
    }
    if phase3: gate_map[phase3]=('aggregate_exit_gate','ALL_REQUIRED_RUNS_ACCEPTED')
    for phase,(field,gate) in gate_map.items():
        derived=phase_status.get('phases',{}).get(phase,{}).get(field)
        authoritative=status.get('phase_gates',{}).get(gate)
        if normalize_lifecycle_state(authoritative) is None:
            errors.append(f'invalid authoritative boundary state: {gate}')
        if derived!=authoritative:
            errors.append(f'derived phase status disagrees with authoritative gate {gate}')
    formation=phase_status.get('phases',{}).get('PRODUCT_FORMATION',{})
    if 'exit_gate' in formation:
        errors.append('derived Product Formation must use exit_evidence, not exit_gate')
    derived_baseline=formation.get('exit_evidence')
    authoritative_baseline=status.get('product_baseline')
    if normalize_lifecycle_state(authoritative_baseline) is None:
        errors.append('invalid Product Baseline evidence state in status.json')
    if derived_baseline!=authoritative_baseline:
        errors.append('derived Product Formation exit evidence disagrees with authoritative product_baseline')
    authoritative_complete=completed_evidence(authoritative_baseline)
    derived_complete=completed_evidence(derived_baseline)
    if authoritative_complete and formation.get('status') not in COMPLETED_PHASE_STATES:
        errors.append('derived Product Formation completion is pending despite accepted Product Baseline')
    if not authoritative_complete and formation.get('status') in COMPLETED_PHASE_STATES:
        errors.append('derived Product Formation completion lacks accepted Product Baseline')
    if phase3 and status.get('current_phase') in {phase3,'DELIVERY_PREPARATION'}:
        if not authoritative_complete:
            errors.append(phase3+' requires accepted Product Baseline')
        if not derived_complete or formation.get('status') not in COMPLETED_PHASE_STATES:
            errors.append(phase3+' requires matching derived Product Formation completion')
    errors.extend(validate_security_status_shape(status))
    return errors

def validate_takeover_readiness(start,status,health):
    if start.get('initialization_mode','NEW')!='EXISTING': return []
    errors=[]
    readiness=start.get('takeover_readiness')
    if readiness not in {'READY','BLOCKED','NOT_CONTINUING'}:
        errors.append('existing takeover readiness must be READY, BLOCKED, or NOT_CONTINUING')
    if status.get('takeover_readiness')!=readiness or health.get('takeover_readiness')!=readiness:
        errors.append('takeover readiness disagrees across status and assessment evidence')
    continuity=start.get('continuity_decision')
    if continuity in {'HOLD','TERMINATE'}:
        if readiness!='NOT_CONTINUING': errors.append('HOLD or TERMINATE requires NOT_CONTINUING')
        return errors
    if continuity not in {'CONTINUE','NARROW_REDIRECT'}:
        errors.append('existing project continuity decision missing')
        return errors
    if readiness=='NOT_CONTINUING': errors.append('continuing project cannot be NOT_CONTINUING')
    candidate=start.get('source_candidate',{})
    if not all(candidate.get(name) for name in ['repository','version','commit']):
        errors.append('existing takeover requires frozen repository, version, and candidate')
    if candidate.get('version')!=start.get('source_version') or candidate.get('commit')!=start.get('source_head'):
        errors.append('frozen candidate disagrees with preserved source identity')
    if status.get('canonical_candidate')!=candidate:
        errors.append('canonical status candidate disagrees with takeover source candidate')
    if readiness=='READY':
        requirements={
            'attestation_status':'EVIDENCED',
            'historical_materials_status':'INVENTORIED',
            'evidence_inventory_status':'INVENTORIED',
            'product_mainline_status':'RECONSTRUCTED',
        }
        for field,expected in requirements.items():
            if start.get(field)!=expected: errors.append(f'READY requires {field} {expected}')
        if not start.get('evidence_inventory'):
            errors.append('READY requires evidence inventory pointers')
        if not start.get('product_mainline_evidence'):
            errors.append('READY requires product mainline evidence pointers')
        if status.get('existing_project_attestation')!='EVIDENCED':
            errors.append('READY requires authoritative attestation evidence')
        if health.get('existing_project_classification') not in {'ATTESTED_COMPLETE','NEEDS_GAP_CLOSURE','PARTIAL','DIRECTION_CHANGED'}:
            errors.append('READY requires a continued-project health classification')
        if status.get('blockers'):
            errors.append('READY requires no unresolved takeover blockers')
    return errors

def present(value):
    return value not in {None,'','PENDING','UNKNOWN','NONE'}

def canonical_github_repository(value):
    value=str(value or '').strip()
    patterns=[
        r'https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)',
        r'git@github\.com:([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)',
        r'github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)',
        r'([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)',
    ]
    for pattern in patterns:
        match=re.fullmatch(pattern,value,re.IGNORECASE)
        if match:
            owner,repository=match.groups()
            if repository.lower().endswith('.git'): repository=repository[:-4]
            if owner and repository: return f'github.com/{owner.lower()}/{repository.lower()}'
    return None

def safe_subtree_path(value):
    value=str(value or '').strip()
    if not value or value.upper() in NOT_APPLICABLE: return False
    if '\\' in value or '://' in value or value.startswith('/') or re.match(r'^[A-Za-z]:',value): return False
    parts=value.strip('/').split('/')
    return bool(parts) and all(part not in {'','.', '..'} for part in parts)

def evidence(value):
    return present(value) and str(value).strip().upper() not in NOT_APPLICABLE

def component_version(value):
    return bool(COMPONENT_VERSION_RE.fullmatch(str(value or '').strip()))

def resolve_frozen_commit(repository_path,commit):
    repository=Path(repository_path).resolve()
    commit=str(commit or '').strip()
    if not re.fullmatch(r'(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})',commit):
        return None,'Product Baseline Handoff requires a full exact project commit'
    top=subprocess.run(
        ['git','rev-parse','--show-toplevel'],cwd=repository,capture_output=True,text=True
    )
    if top.returncode or Path(top.stdout.strip()).resolve()!=repository:
        return None,'Product Baseline Handoff project path must be the total project Git repository root'
    resolved=subprocess.run(
        ['git','rev-parse','--verify',commit+'^{commit}'],cwd=repository,capture_output=True,text=True
    )
    if resolved.returncode or resolved.stdout.strip().lower()!=commit.lower():
        return None,'Product Baseline Handoff frozen commit does not resolve to that exact commit'
    return resolved.stdout.strip(),None

def frozen_subtree_content_hash(repository_path,commit,subtree_path):
    repository=Path(repository_path).resolve()
    subtree_path=str(subtree_path or '').strip().strip('/')
    if not safe_subtree_path(subtree_path):
        return None,'requires a safe relative subtree path'
    object_name=commit+':'+subtree_path
    object_type=subprocess.run(
        ['git','cat-file','-t',object_name],cwd=repository,capture_output=True,text=True
    )
    if object_type.returncode or object_type.stdout.strip()!='tree':
        return None,'does not exist as a tree at the frozen commit'
    listing=subprocess.run(
        ['git','ls-tree','-r','-z','--full-tree',commit,'--',':(literal)'+subtree_path],
        cwd=repository,capture_output=True,
    )
    if listing.returncode:
        return None,'could not read tracked subtree blobs at the frozen commit'
    entries=[]
    try:
        for record in listing.stdout.split(b'\0'):
            if not record: continue
            metadata,path=record.split(b'\t',1)
            mode,object_kind,object_id=metadata.split(b' ')
            path.decode('utf-8','strict')
            if object_kind!=b'blob':
                return None,'contains a non-blob tracked entry and cannot use the canonical subtree hash'
            blob=subprocess.run(
                ['git','cat-file','blob',object_id.decode('ascii')],
                cwd=repository,capture_output=True,
            )
            if blob.returncode:
                return None,'could not read a tracked subtree blob at the frozen commit'
            entries.append((path,mode,hashlib.sha256(blob.stdout).hexdigest().encode('ascii')))
    except (UnicodeDecodeError,ValueError):
        return None,'contains a path that cannot enter the canonical UTF-8 subtree manifest'
    if not entries:
        return None,'contains no tracked blobs at the frozen commit'
    manifest=b''.join(
        path+b'\0'+mode+b'\0'+digest+b'\n'
        for path,mode,digest in sorted(entries,key=lambda entry:entry[0])
    )
    return 'sha256:'+hashlib.sha256(manifest).hexdigest(),None

def verify_frozen_subtree_identity(repository_path,commit,row,prefix,path_field='Path'):
    path=str(row.get(path_field,'')).strip()
    expected=str(row.get('Content hash','')).strip().lower()
    actual,error=frozen_subtree_content_hash(repository_path,commit,path)
    if error: return [prefix+' '+error]
    if actual!=expected: return [prefix+' content hash does not match the frozen commit subtree']
    return []

def parse_closed_record(value,labels,label):
    raw_parts=[part.strip() for part in str(value or '').split(';')]
    parts=[part for part in raw_parts if part]
    record={}; errors=[]
    if any(not part for part in raw_parts): errors.append(label+' contains an empty field')
    for part in parts:
        key,separator,item=part.partition(':')
        key=key.strip(); item=item.strip()
        if not separator or key not in labels:
            errors.append(label+' has malformed or unknown fields'); continue
        if key in record: errors.append(label+' has duplicate '+key)
        record[key]=item
    if set(record)!=set(labels): errors.append(label+' must contain exactly '+', '.join(labels))
    for key,item in record.items():
        if not stable_id(item): errors.append(label+' '+key+' must be a safe evidence ID')
        elif not semantic_present(item) or item.upper() in {
            'PASS','READY','COMPLETE','IMPLEMENTED','EVIDENCE','CONTRACT','CAPABILITY','GENERIC','TBD','TODO'
        }: errors.append(label+' '+key+' cannot use placeholder evidence')
    return record,errors

def parse_closed_id_list(value,label):
    text=str(value or '').strip()
    if text=='NONE': return set(),[]
    raw_tokens=[token.strip() for token in text.split(',')]
    tokens=[token for token in raw_tokens if token]
    errors=[]
    if any(not token for token in raw_tokens): errors.append(label+' contains an empty ID')
    if not tokens: errors.append(label+' requires IDs or exact NONE')
    if len(tokens)!=len(set(tokens)): errors.append(label+' contains duplicate IDs')
    for token in tokens:
        if not stable_id(token): errors.append(label+' contains unsafe ID '+token)
    return set(tokens),errors

def workflow_map_uses_270(rows):
    markers={'Classification authority','Workflow Capability ID','Rules / state / side-effect trace'}
    return any(markers.intersection(row) for row in rows)

def validate_classification_authority(value,classification,prefix):
    record,errors=parse_closed_record(
        value,['CLASSIFICATION','CALABASH','OWNER_CONFIRMED'],prefix+' classification authority'
    )
    if record.get('CLASSIFICATION')!=classification:
        errors.append(prefix+' classification authority disagrees with CORE/EXTRA classification')
    return errors

def validate_workflow_subtrees(rows,repository_path=None,frozen_commit=None):
    errors=[]; ids=set(); paths=set(); capabilities=set(); strict=workflow_map_uses_270(rows)
    for index,row in enumerate(rows):
        prefix=f'Workflow row {index+1}'
        workflow_id=str(row.get('Workflow ID','')).strip()
        classification=str(row.get('Classification (CORE/EXTRA)','')).strip().upper()
        implementation=str(row.get('Implementation status','')).strip().upper()
        primary=str(row.get('Primary mainline','')).strip().upper()
        if not stable_id(workflow_id): errors.append(prefix+' requires a safe Workflow ID')
        elif workflow_id in ids: errors.append('duplicate Workflow ID '+workflow_id)
        ids.add(workflow_id)
        if classification not in {'CORE','EXTRA'}: errors.append(prefix+' requires CORE or EXTRA classification')
        if implementation not in {'IMPLEMENTED','UNIMPLEMENTED'}: errors.append(prefix+' requires implementation status')
        if primary not in {'YES','NO'}: errors.append(prefix+' Primary mainline must be YES or NO')
        if classification=='CORE' and implementation!='IMPLEMENTED': errors.append(prefix+' CORE must be implemented')
        if primary=='YES' and (classification!='CORE' or implementation!='IMPLEMENTED'):
            errors.append(prefix+' primary mainline Workflow must be implemented CORE')
        if strict:
            errors.extend(validate_classification_authority(
                row.get('Classification authority'),classification,prefix
            ))
        if implementation=='IMPLEMENTED':
            path=str(row.get('Subtree path','')).strip()
            if not safe_subtree_path(path): errors.append(prefix+' requires a safe relative subtree path')
            elif path in paths: errors.append('duplicate subtree path '+path)
            paths.add(path)
            if not component_version(row.get('Component version')): errors.append(prefix+' requires a three-part component version')
            hash_pattern=EXACT_HASH_RE if strict else CONTENT_HASH_RE
            if not hash_pattern.fullmatch(str(row.get('Content hash','')).strip()):
                errors.append(prefix+' requires content hash')
            if not evidence(row.get('API contract / evidence')): errors.append(prefix+' implemented Workflow requires API evidence')
            if not evidence(row.get('MCP contract / evidence')): errors.append(prefix+' implemented Workflow requires MCP evidence')
            if strict:
                capability=str(row.get('Workflow Capability ID','')).strip()
                if not stable_id(capability): errors.append(prefix+' requires a safe Workflow Capability ID')
                elif capability in capabilities: errors.append('duplicate Workflow Capability ID '+capability)
                capabilities.add(capability)
                rules,rule_errors=parse_closed_record(
                    row.get('Rules / state / side-effect trace'),
                    ['RULES','STATE','SIDE_EFFECTS'],prefix+' rules/state/side-effect trace'
                )
                errors.extend(rule_errors)
                for kind,field in [('API','API contract / evidence'),('MCP','MCP contract / evidence')]:
                    interface,interface_errors=parse_closed_record(
                        row.get(field),['CAPABILITY','CONTRACT','EVIDENCE'],prefix+' '+kind+' interface'
                    )
                    errors.extend(interface_errors)
                    if interface.get('CAPABILITY')!=capability:
                        errors.append(prefix+' '+kind+' interface must bind the same Workflow Capability ID')
                _,implementation_errors=parse_closed_record(
                    row.get('Evidence / attestation'),['IMPLEMENTATION','RUNNABLE'],
                    prefix+' implementation/runnable evidence'
                )
                errors.extend(implementation_errors)
            if repository_path is not None and frozen_commit is not None and safe_subtree_path(path):
                errors.extend(verify_frozen_subtree_identity(
                    repository_path,frozen_commit,row,prefix,path_field='Subtree path'
                ))
        elif classification=='EXTRA':
            absent=['Subtree path','Component version','Content hash','API contract / evidence','MCP contract / evidence']
            if strict:
                absent+=['Workflow Capability ID','Rules / state / side-effect trace','Evidence / attestation']
            for field in absent:
                if str(row.get(field,'')).strip().upper()!='NOT_APPLICABLE':
                    errors.append(prefix+' unimplemented EXTRA cannot claim '+field)
            if strict:
                for field in ['UI subtree references','Simulation subtree references']:
                    if str(row.get(field,'')).strip()!='NONE':
                        errors.append(prefix+' unimplemented EXTRA cannot claim '+field)
    return errors

def split_ids(value):
    return {item.strip() for item in str(value or '').split(',') if item.strip() and item.strip().upper()!='NONE'}

def map_identity_rows(workflow_rows,ui_rows,simulation_rows):
    identities={}; errors=[]; strict=workflow_map_uses_270(workflow_rows)
    sources=[
        ('WORKFLOW',workflow_rows,'Workflow ID','Subtree path',('UI subtree references','Simulation subtree references')),
        ('UI',ui_rows,'UI ID','Subtree path',('Workflow subtree references','Simulation subtree references')),
        ('SIMULATION',simulation_rows,'Simulation ID','Subtree path',('Workflow subtree references','UI subtree references')),
    ]
    declared={kind:set() for kind,_,_,_,_ in sources}; all_ids={}; realized={kind:set() for kind in declared}
    for subtree_type,rows,id_field,_,_ in sources:
        for index,row in enumerate(rows):
            subtree_id=str(row.get(id_field,'')).strip(); prefix=f'{subtree_type} Map row {index+1}'
            if not stable_id(subtree_id): errors.append(prefix+' requires a safe subtree ID'); continue
            if subtree_id in all_ids: errors.append('duplicate or ambiguous Map subtree ID '+subtree_id)
            all_ids[subtree_id]=subtree_type; declared[subtree_type].add(subtree_id)
            if subtree_type!='WORKFLOW' or str(row.get('Implementation status','')).strip().upper()=='IMPLEMENTED':
                realized[subtree_type].add(subtree_id)
    paths={}
    for subtree_type,rows,id_field,path_field,relation_fields in sources:
        for index,row in enumerate(rows):
            if subtree_type=='WORKFLOW' and str(row.get('Implementation status','')).strip().upper()!='IMPLEMENTED':
                continue
            prefix=f'{subtree_type} Map row {index+1}'
            subtree_id=str(row.get(id_field,'')).strip()
            primary=str(row.get('Primary mainline','')).strip().upper()
            if not stable_id(subtree_id): continue
            key=(subtree_type,subtree_id)
            if key in identities:
                errors.append(prefix+' duplicates a Map subtree ID'); continue
            if primary not in {'YES','NO'}: errors.append(prefix+' Primary mainline must be YES or NO')
            path=str(row.get(path_field,'')).strip()
            if not safe_subtree_path(path): errors.append(prefix+' requires a safe relative subtree path')
            elif strict:
                for other,other_key in paths.items():
                    if path==other or path.startswith(other.rstrip('/')+'/') or other.startswith(path.rstrip('/')+'/'):
                        errors.append(prefix+' subtree path must be a peer of '+other_key[1])
                paths[path]=key
            if not component_version(row.get('Component version')): errors.append(prefix+' requires a three-part component version')
            hash_pattern=EXACT_HASH_RE if strict else CONTENT_HASH_RE
            if not hash_pattern.fullmatch(str(row.get('Content hash','')).strip()): errors.append(prefix+' requires content hash')
            if strict and subtree_type=='UI':
                if not semantic_present(row.get('Evidence / attestation')):
                    errors.append(prefix+' requires UI implementation evidence')
                if str(row.get('Lock status','')).strip()!='LOCKED':
                    errors.append(prefix+' UI must be LOCKED at Product Baseline')
            if strict and subtree_type=='SIMULATION' and str(row.get('Foundation status','')).strip()!='RUNNABLE':
                errors.append(prefix+' Simulation must be RUNNABLE at Product Baseline')
            typed_relations={}; relations=set()
            relation_targets={
                'UI subtree references':'UI','Workflow subtree references':'WORKFLOW',
                'Simulation subtree references':'SIMULATION',
            }
            for field in relation_fields:
                if strict:
                    values,relation_errors=parse_closed_id_list(row.get(field),prefix+' '+field)
                    errors.extend(relation_errors)
                else: values=split_ids(row.get(field))
                target_type=relation_targets[field]; typed_relations[target_type]=values; relations.update(values)
                if strict:
                    for reference in values:
                        if reference not in realized[target_type]:
                            actual_type=all_ids.get(reference)
                            if actual_type: errors.append(prefix+' '+field+' contains wrong-type or unrealized ID '+reference)
                            else: errors.append(prefix+' '+field+' contains unknown ID '+reference)
            identities[key]={
                'path':str(row.get(path_field,'')).strip(),
                'version':str(row.get('Component version','')).strip(),
                'hash':str(row.get('Content hash','')).strip() if strict else str(row.get('Content hash','')).strip().lower(),
                'classification':str(row.get('Classification (CORE/EXTRA)','NOT_APPLICABLE')).strip().upper(),
                'classification_authority':str(row.get('Classification authority','NOT_APPLICABLE')).strip(),
                'capability':str(row.get('Workflow Capability ID','NOT_APPLICABLE')).strip(),
                'api':str(row.get('API contract / evidence','NOT_APPLICABLE')).strip(),
                'mcp':str(row.get('MCP contract / evidence','NOT_APPLICABLE')).strip(),
                'primary':primary,
                'relations':relations,
                'typed_relations':typed_relations,
                'strict':strict,
            }
    if strict:
        reciprocal=[('WORKFLOW','UI'),('WORKFLOW','SIMULATION'),('UI','SIMULATION')]
        for left_type,right_type in reciprocal:
            for (kind,item_id),item in identities.items():
                if kind!=left_type: continue
                for target in item['typed_relations'].get(right_type,set()):
                    peer=identities.get((right_type,target))
                    if peer and item_id not in peer['typed_relations'].get(left_type,set()):
                        errors.append(f'{left_type} {item_id} relation to {right_type} {target} is not reciprocal')
            for (kind,item_id),item in identities.items():
                if kind!=right_type: continue
                for target in item['typed_relations'].get(left_type,set()):
                    peer=identities.get((left_type,target))
                    if peer and item_id not in peer['typed_relations'].get(right_type,set()):
                        errors.append(f'{right_type} {item_id} relation to {left_type} {target} is not reciprocal')
        primary={kind:{item_id for (item_kind,item_id),item in identities.items() if item_kind==kind and item['primary']=='YES'} for kind in realized}
        primary_core={item_id for item_id in primary['WORKFLOW'] if identities[('WORKFLOW',item_id)]['classification']=='CORE'}
        if primary['WORKFLOW']-primary_core: errors.append('Primary product mainline Workflow must be implemented CORE')
        triples=[]
        for workflow_id in primary_core:
            workflow=identities[('WORKFLOW',workflow_id)]
            for ui_id in primary['UI']:
                ui=identities[('UI',ui_id)]
                for simulation_id in primary['SIMULATION']:
                    simulation=identities[('SIMULATION',simulation_id)]
                    if (
                        ui_id in workflow['typed_relations'].get('UI',set())
                        and simulation_id in workflow['typed_relations'].get('SIMULATION',set())
                        and workflow_id in ui['typed_relations'].get('WORKFLOW',set())
                        and simulation_id in ui['typed_relations'].get('SIMULATION',set())
                        and workflow_id in simulation['typed_relations'].get('WORKFLOW',set())
                        and ui_id in simulation['typed_relations'].get('UI',set())
                    ): triples.append((workflow_id,ui_id,simulation_id))
        if not triples: errors.append('Primary product mainline requires one mutually linked UI/CORE Workflow/Simulation route')
        else:
            joined={kind:set() for kind in primary}
            for workflow_id,ui_id,simulation_id in triples:
                joined['WORKFLOW'].add(workflow_id); joined['UI'].add(ui_id); joined['SIMULATION'].add(simulation_id)
            for kind in primary:
                if primary[kind]-joined[kind]: errors.append('Primary product mainline contains an unrelated '+kind+' claim')
    return identities,errors

def validate_map_handoff_identity(rows,workflow_rows,ui_rows,simulation_rows,primary_mainline_id,map_mainline_ids):
    expected,errors=map_identity_rows(workflow_rows,ui_rows,simulation_rows)
    for source,value in map_mainline_ids.items():
        if not stable_id(value): errors.append(source+' Map requires a safe Primary product mainline ID')
        elif str(value).strip()!=str(primary_mainline_id or '').strip():
            errors.append(source+' Map Primary product mainline ID does not match Product Baseline Handoff')
    actual={}
    for index,row in enumerate(rows):
        key=(str(row.get('Subtree type','')).strip().upper(),str(row.get('Subtree ID','')).strip())
        if key in actual:
            errors.append('duplicate Product Baseline Handoff subtree identity '+key[1]); continue
        relations,relation_errors=parse_closed_id_list(
            row.get('Related subtree IDs'),f'Baseline subtree row {index+1} relations'
        ) if expected and next(iter(expected.values())).get('strict') else (split_ids(row.get('Related subtree IDs')),[])
        errors.extend(relation_errors)
        actual[key]={
            'path':str(row.get('Path','')).strip(),
            'version':str(row.get('Component version','')).strip(),
            'hash':str(row.get('Content hash','')).strip() if expected and next(iter(expected.values())).get('strict') else str(row.get('Content hash','')).strip().lower(),
            'classification':str(row.get('Classification','')).strip().upper(),
            'classification_authority':str(row.get('Classification authority','NOT_APPLICABLE')).strip(),
            'capability':str(row.get('Workflow Capability ID','NOT_APPLICABLE')).strip(),
            'api':str(row.get('API evidence','')).strip(),
            'mcp':str(row.get('MCP evidence','')).strip(),
            'primary':str(row.get('Primary mainline','')).strip().upper(),
            'relations':relations,
        }
    missing=set(expected)-set(actual)
    extra=set(actual)-set(expected)
    for subtree_type,subtree_id in sorted(missing):
        errors.append(f'{subtree_type} Map subtree {subtree_id} is missing from Product Baseline Handoff')
    for subtree_type,subtree_id in sorted(extra):
        errors.append(f'Product Baseline Handoff subtree {subtree_id} is absent from the {subtree_type} Map')
    for key in sorted(set(expected).intersection(actual)):
        subtree_type,subtree_id=key
        fields=['path','version','hash','classification','api','mcp','primary','relations']
        if expected[key].get('strict'): fields+=['classification_authority','capability']
        for field in fields:
            if expected[key][field]!=actual[key][field]:
                errors.append(f'{subtree_type} Map / Product Baseline Handoff identity mismatch for {subtree_id}: {field}')
    return errors

def validate_product_subtree_baseline(
    rows,primary_mainline_id,owner_confirmation,
    repository_path=None,frozen_commit=None,
    workflow_rows=None,ui_rows=None,simulation_rows=None,map_mainline_ids=None,
):
    errors=[]; ids=set(); paths={}; by_type={'UI':set(),'WORKFLOW':set(),'SIMULATION':set()}; primary={key:set() for key in by_type}
    strict=workflow_map_uses_270(workflow_rows or [])
    if not stable_id(primary_mainline_id): errors.append('Primary product mainline ID required')
    confirmation=str(owner_confirmation or '').strip()
    if not re.fullmatch(r'OWNER_CONFIRMED:\s*\S(?:.*\S)?',confirmation):
        errors.append('Primary product mainline requires Owner confirmation')
    resolved_commit=None
    if repository_path is not None:
        resolved_commit,commit_error=resolve_frozen_commit(repository_path,frozen_commit)
        if commit_error: errors.append(commit_error)
    for index,row in enumerate(rows):
        prefix=f'Baseline subtree row {index+1}'
        subtree_type=str(row.get('Subtree type','')).strip().upper()
        subtree_id=str(row.get('Subtree ID','')).strip()
        path=str(row.get('Path','')).strip()
        if subtree_type not in by_type:
            errors.append(prefix+' has invalid subtree type'); continue
        if not stable_id(subtree_id): errors.append(prefix+' requires a safe Subtree ID')
        elif subtree_id in ids: errors.append('duplicate Subtree ID '+subtree_id)
        ids.add(subtree_id); by_type[subtree_type].add(subtree_id)
        if not safe_subtree_path(path): errors.append(prefix+' requires a safe relative subtree path')
        elif path in paths: errors.append('duplicate subtree path '+path)
        elif strict:
            for other,kind in paths.items():
                if path.startswith(other.rstrip('/')+'/') or other.startswith(path.rstrip('/')+'/'):
                    errors.append('realized product subtree paths must be peers, not nested')
        paths[path]=subtree_type
        if not component_version(row.get('Component version')): errors.append(prefix+' requires a three-part component version')
        hash_pattern=EXACT_HASH_RE if strict else CONTENT_HASH_RE
        if not hash_pattern.fullmatch(str(row.get('Content hash','')).strip()):
            errors.append(prefix+' requires content hash')
        if subtree_type=='WORKFLOW':
            if str(row.get('Classification','')).strip().upper() not in {'CORE','EXTRA'}:
                errors.append(prefix+' Workflow requires CORE or EXTRA classification')
            if not evidence(row.get('API evidence')): errors.append(prefix+' implemented Workflow requires API evidence')
            if not evidence(row.get('MCP evidence')): errors.append(prefix+' implemented Workflow requires MCP evidence')
            if strict:
                if not stable_id(row.get('Workflow Capability ID')): errors.append(prefix+' requires Workflow Capability ID')
                errors.extend(validate_classification_authority(
                    row.get('Classification authority'),str(row.get('Classification','')).strip().upper(),prefix
                ))
        elif strict:
            for field in ['Classification','Classification authority','Workflow Capability ID','API evidence','MCP evidence']:
                if str(row.get(field,'')).strip()!='NOT_APPLICABLE':
                    errors.append(prefix+' non-Workflow identity requires '+field+' NOT_APPLICABLE')
        primary_flag=str(row.get('Primary mainline','')).strip().upper()
        if primary_flag not in {'YES','NO'}: errors.append(prefix+' Primary mainline must be YES or NO')
        if primary_flag=='YES': primary[subtree_type].add(subtree_id)
        if resolved_commit and safe_subtree_path(path):
            errors.extend(verify_frozen_subtree_identity(repository_path,resolved_commit,row,prefix))
    simulation_paths=sorted(path for path,kind in paths.items() if kind=='SIMULATION')
    for index,path in enumerate(simulation_paths):
        for other in simulation_paths[index+1:]:
            if other.startswith(path.rstrip('/')+'/') or path.startswith(other.rstrip('/')+'/'):
                errors.append('Simulation subtrees must remain peers, not nested')
    if not primary['UI']: errors.append('Primary product mainline requires at least one UI subtree')
    primary_core={
        str(row.get('Subtree ID','')).strip() for row in rows
        if str(row.get('Subtree type','')).strip().upper()=='WORKFLOW'
        and str(row.get('Primary mainline','')).strip().upper()=='YES'
        and str(row.get('Classification','')).strip().upper()=='CORE'
    }
    if not primary_core: errors.append('Primary product mainline requires at least one CORE Workflow subtree')
    if not primary['SIMULATION']: errors.append('Primary product mainline requires at least one Simulation subtree')
    for row in rows:
        references=split_ids(row.get('Related subtree IDs'))
        missing=references-ids
        if missing: errors.append('subtree relation references unknown IDs '+', '.join(sorted(missing)))
        if str(row.get('Subtree type','')).strip().upper()=='WORKFLOW' and str(row.get('Primary mainline','')).strip().upper()=='YES':
            if not references.intersection(primary['UI']): errors.append('Primary Workflow must relate to a primary UI subtree')
            if not references.intersection(primary['SIMULATION']): errors.append('Primary Workflow must relate to a primary Simulation subtree')
    if all(value is not None for value in [workflow_rows,ui_rows,simulation_rows,map_mainline_ids]):
        errors.extend(validate_map_handoff_identity(
            rows,workflow_rows,ui_rows,simulation_rows,primary_mainline_id,map_mainline_ids
        ))
    return errors

def validate_ui_subtree_baseline_preflight(fields,product_repository=None):
    errors=[]
    repository_and_commit=str(fields.get('Project repository / exact baseline commit','')).strip()
    repository_text,separator,commit=repository_and_commit.partition('::')
    repository=canonical_github_repository(repository_text.strip())
    if not repository or not separator or not re.fullmatch(r'(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})',commit.strip()):
        errors.append('UI subtree baseline requires the project repository and full exact baseline commit')
    product=canonical_github_repository(product_repository)
    if not product: errors.append('product repository identity is required')
    elif repository and repository!=product: errors.append('UI subtree baseline must use the total project repository')
    subtree=str(fields.get('Applicable UI subtree ID / path','')).strip()
    subtree_id,subtree_separator,subtree_path=subtree.partition('::')
    if not present(subtree_id.strip()) or not subtree_separator or not safe_subtree_path(subtree_path.strip()):
        errors.append('UI subtree baseline requires an applicable UI ID and safe relative path')
    if not component_version(fields.get('UI component version')): errors.append('UI subtree baseline requires a three-part component version')
    content_hash=str(fields.get('UI content hash','')).strip()
    if not re.fullmatch(r'sha256:[0-9a-fA-F]{64}',content_hash,re.IGNORECASE):
        errors.append('UI baseline requires an exact SHA-256 content hash')
    hash_scope=str(fields.get('UI content hash scope / manifest evidence','')).strip()
    if not hash_scope.upper().startswith('HASH_SCOPE:') or not hash_scope.split(':',1)[1].strip():
        errors.append('UI baseline requires deterministic content hash scope evidence')
    identity=str(fields.get('UI Product / Integration Baseline identity','')).strip()
    if not identity.upper().startswith('MATCH:') or not identity.split(':',1)[1].strip():
        errors.append('UI Product and Integration Baseline identity must MATCH with evidence')
    comparison=str(fields.get('UI subtree comparison before Slice / Run','')).strip()
    if not comparison.upper().startswith('MATCH:') or not comparison.split(':',1)[1].strip():
        errors.append('UI baseline comparison before Slice or Run must MATCH with evidence')
    if fields.get('UI comparison before acceptance route')!='REQUIRED':
        errors.append('UI comparison before acceptance route must be REQUIRED')
    return errors

def validate_slice_execution_preflight(fields,fingerprint,product_repository=None):
    errors=[]
    for key in fields:
        if key.strip().lower() in SLICE_INTERNAL_METHOD_FIELDS:
            errors.append('Slice preflight contains internal method field '+key)
    if fields.get('Execution Coverage Preflight')!='PASS':
        errors.append('active Slice execution coverage preflight must PASS')
        return errors
    errors.extend(validate_ui_subtree_baseline_preflight(fields,product_repository))
    for field in SLICE_PREFLIGHT_REQUIRED:
        if not present(fields.get(field)): errors.append('Slice preflight missing '+field)
    gaps=str(fields.get('Coverage gaps / unknowns','')).strip().upper()
    if gaps not in {'NONE','NO_GAPS'}:
        errors.append('Slice preflight PASS requires no coverage gaps or unknowns')
    connection=str(fields.get('Cross-layer connection evidence','')).strip().upper()
    proving=str(fields.get('First Proving Run requirement','')).strip().upper()
    if connection.startswith('UNPROVEN'):
        if proving!='REQUIRED' or not present(fields.get('First Proving Run ID / evidence')):
            errors.append('unproven cross-layer connection requires a first proving Run')
        first_run=str(fields.get('First Proving Run ID / evidence','')).partition('/')[0].strip()
        required_runs,_=parse_closed_id_list(fields.get('Required Run IDs'),'Slice Required Run IDs')
        if first_run not in required_runs:
            errors.append('unproven cross-layer connection requires its first proving Run in Required Run IDs')
        if not present(fields.get('First Proving Run production E2E scenario')):
            errors.append('first proving Run requires a production E2E scenario')
        if fields.get('Failure expansion rule')!='HALT_EXPANSION':
            errors.append('first proving Run failure must halt expansion')
    elif connection.startswith('PROVEN'):
        if ':' not in connection or not connection.split(':',1)[1].strip():
            errors.append('PROVEN requires an evidence pointer')
    else:
        errors.append('cross-layer connection evidence must be PROVEN or UNPROVEN')
    complexity=fingerprint.get('complexity',{}) if isinstance(fingerprint,dict) else {}
    if any(str(complexity.get(factor,'')).upper() in {'HIGH','UNKNOWN'} for factor in COMPLEXITY_FACTORS):
        if fields.get('Fingerprint depth response') not in {'DEEPER_EVIDENCE','SMALLER_INDEPENDENT_RUNS'}:
            errors.append('HIGH or UNKNOWN complexity requires deeper evidence or smaller independent Runs')
    return errors

ROUTE_LINKS=(
    'UI_ACTION','WORKFLOW_RULES','STATE_TRANSITION','DATA_EFFECT','SIDE_EFFECT',
    'VISIBLE_UI_RESULT','FAILURE_PATH','RECOVERY_RESULT',
)
ROUTE_COMMON_FIELDS={
    'Slice ID / version','Integration Route ID','Integration candidate ID / exact hash',
    'Product Baseline identity / frozen commit','Primary product mainline ID',
    'Applicable UI identity','Workflow capability identity','Selected entry interface',
    'Simulation scenario identity','Connected route evidence',
}
SLICE_ROUTE_ALLOWED={
    'Artifact role',*ROUTE_COMMON_FIELDS,'Actor intent','Product outcome','Product Baseline trace',
    'Accepted integration candidate / baseline identity','Workflow references','UI references',
    'Primary product mainline ID / Owner confirmation','Project repository / exact baseline commit',
    'Applicable UI subtree ID / path','UI component version','UI content hash',
    'UI content hash scope / manifest evidence','UI Product / Integration Baseline identity',
    'UI subtree comparison before Slice / Run','UI comparison before acceptance route',
    'Scenario IDs / versions','Real integration route','Applicable Simulation scenario trace',
    'Phase-2-only demonstration evidence','State / data / permission trace',
    'Exception / recovery trace','Shared capability result','Impact Analysis ID',
    'Integration Baseline ID','Integration Baseline reference','Final Feature Verification reference',
    'Required Run IDs','Optional Run IDs','Superseded Run IDs','Invalidated Run IDs',
    'D0-D3 evidence plan','Visible completion','Invisible completion',
    'Normal Loop Owner Acceptance route(s)','Post-Security Owner Acceptance route',
    'Execution Coverage Preflight','Coverage gaps / unknowns','Cross-layer connection evidence',
    'First Proving Run requirement','First Proving Run ID / evidence',
    'First Proving Run production E2E scenario','Failure expansion rule',
    'Fingerprint depth response','State',
}
BASELINE_ROUTE_REQUIRED={
    'Artifact role','Baseline ID',*ROUTE_COMMON_FIELDS,'Feature Slice reference',
    'Integration candidate provenance','Product Handoff identity match','Branch / latest accepted',
    'Locked actor surfaces','Lock authority','System autonomous UI modification',
    'Owner-initiated / Owner-approved UI change route','Explicitly editable regions',
    'Workflow contract and controlled adjustment boundary','Simulation scenario versions',
    'Calabash/Product Baseline reference','Owner approval','Lock time',
    'UI change disposition','Baseline Change Request reference','Prior Integration Baseline ID',
}
BASELINE_ROUTE_ALLOWED=BASELINE_ROUTE_REQUIRED|{
    'Feature Slice ID / version','Primary product mainline ID','Project repository identity',
    'Project exact frozen commit SHA','Applicable UI subtree ID / path','UI component version',
    'UI content hash','UI content hash scope / manifest evidence','Real integration route / evidence',
}
FINAL_ROUTE_REQUIRED={
    'Artifact role','Verification ID',*ROUTE_COMMON_FIELDS,
    'Integration Baseline ID / reference','D3 / Loop Owner Acceptance evidence',
    'Phase-2-only evidence used as acceptance proof','Changed connected links',
    'Reused unchanged connected links','New / repeated connected links',
    'Evidence reuse basis','Final verdict',
}
FINAL_ROUTE_ALLOWED=FINAL_ROUTE_REQUIRED|{
    'Feature Slice ID / version','Candidate / locked total-project repository and exact commit',
    'Applicable UI subtree ID / path / component version / content hash',
    'UI Product / Integration Baseline identity','UI comparison before acceptance',
    'Unauthorized UI delta','Real integration route',
    'Phase-2-only static UI / mock / stub / manually staged state used as acceptance proof',
    'Run D3 receipts','Receipt coverage map','Promotion-only eligible',
    'New seam / uncovered-claim checks','Repeated checks and reasons','Security evidence coverage',
    'Normal Run D3 complete','Loop Owner Acceptance Receipt(s)',
    'Centralized Vulnerability Audit occurs after all normal Run acceptances',
    'Invisible behavior evidence',
}
GENERIC_EVIDENCE_IDS={
    'DONE','PASS','READY','COMPLETE','EVIDENCE','GENERIC','MOCK','STUB','SCRIPTED','MANUAL',
    'PENDING','UNKNOWN','NONE','NOT_APPLICABLE','TBD','TODO','PROOF','RESULT',
    'OWNER_APPROVED','OWNER_INITIATED','YES','NO','ALLOWED','FORBIDDEN',
}
BCR_FIELDS={
    'Artifact role','Request ID','Locked Integration Baseline ID','Requested UI change',
    'Change authority','Necessity / impact record','Prior accepted work affected',
    'Owner decision / approval evidence','Project repository identity',
    'Prior project commit SHA','New project commit SHA',
    'New project commit differs from prior lock','Prior UI identity','New UI identity',
    'Product Baseline Handoff update','Integration Baseline update',
    'Affected evidence set','Affected evidence invalidation',
    'Affected evidence re-verification','Unaffected evidence reuse basis',
    'Preservation route','New baseline version',
}

def parse_exact_record_values(value,keys,label):
    raw=[part.strip() for part in str(value or '').split(';')]
    record={}; errors=[]
    if any(not part for part in raw): errors.append(label+' contains an empty record field')
    for part in [part for part in raw if part]:
        key,separator,item=part.partition(':'); key=key.strip(); item=item.strip()
        if not separator or key not in keys:
            errors.append(label+' has malformed or unknown record fields'); continue
        if key in record: errors.append(label+' has duplicate '+key)
        record[key]=item
    if set(record)!=set(keys): errors.append(label+' must contain exactly '+', '.join(keys))
    return record,errors

def parse_slice_identity(value,label='Slice identity'):
    match=re.fullmatch(r'([A-Za-z0-9][A-Za-z0-9._-]{0,127}) / (\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)',str(value or '').strip())
    if not match or not stable_id(match.group(1)) or not SEMVER_RE.fullmatch(match.group(2)):
        return None,[label+' requires exact safe ID / semantic version']
    return match.groups(),[]

def parse_product_commit_identity(value):
    match=re.fullmatch(r'([A-Za-z0-9][A-Za-z0-9._-]{0,127}) / ([0-9a-f]{40}|[0-9a-f]{64})',str(value or '').strip())
    if not match: return None,['Product Baseline integration identity requires safe ID / exact lowercase commit']
    return match.groups(),[]

def parse_bound_route_evidence(value,candidate_identity,route_id,label):
    if (
        not isinstance(candidate_identity,tuple) or len(candidate_identity)!=2
        or not stable_id(candidate_identity[0]) or not EXACT_HASH_RE.fullmatch(str(candidate_identity[1] or ''))
    ):
        return None,[label+' requires the full current candidate ID/hash identity']
    match=re.fullmatch(
        r'([A-Za-z0-9][A-Za-z0-9._-]{0,127})~(sha256:[0-9a-f]{64})~([A-Za-z0-9][A-Za-z0-9._-]{0,127})~([A-Za-z0-9][A-Za-z0-9._-]{0,127})',
        str(value or '').strip(),
    )
    if not match or not all(stable_id(match.group(index)) for index in (1,3,4)):
        return None,[label+' requires exact candidate~sha256~route~evidence identity']
    bound_candidate,bound_hash,bound_route,evidence_id=match.groups(); errors=[]
    if (bound_candidate,bound_hash)!=candidate_identity or bound_route!=route_id:
        errors.append(label+' is not bound to the current candidate and Route')
    if evidence_id.upper() in GENERIC_EVIDENCE_IDS:
        errors.append(label+' cannot use a generic evidence token')
    return (bound_candidate,bound_hash,bound_route,evidence_id),errors

def parse_route_evidence_record(value,candidate_identity,route_id):
    record,errors=parse_exact_record_values(value,ROUTE_LINKS,'Connected route evidence')
    parsed={}
    for link,item in record.items():
        identity,item_errors=parse_bound_route_evidence(item,candidate_identity,route_id,link+' evidence')
        errors.extend(item_errors); parsed[link]=identity
    return parsed,errors

def parse_route_link_set(value,label):
    text=str(value or '').strip()
    if text=='NONE': return set(),[]
    raw=[item.strip() for item in text.split(',')]; values=[item for item in raw if item]
    errors=[]
    if any(not item for item in raw): errors.append(label+' contains an empty route link')
    if len(values)!=len(set(values)): errors.append(label+' contains duplicate route links')
    unknown=set(values)-set(ROUTE_LINKS)
    if unknown: errors.append(label+' contains unknown route links '+', '.join(sorted(unknown)))
    return set(values),errors

def parse_affected_route_evidence_record(value,affected,candidate_identity,route_id,label):
    keys=tuple(link for link in ROUTE_LINKS if link in affected)
    record,errors=parse_exact_record_values(value,keys,label)
    parsed={}
    for link,item in record.items():
        identity,item_errors=parse_bound_route_evidence(
            item,candidate_identity,route_id,label+' '+link
        )
        errors.extend(item_errors); parsed[link]=identity
    identities=[identity for identity in parsed.values() if identity]
    if len(identities)!=len(set(identities)):
        errors.append(label+' requires independent evidence for every affected link')
    return parsed,errors

def parse_route_common(fields,label):
    errors=[]; parsed={}
    missing=ROUTE_COMMON_FIELDS-set(fields)
    if missing: errors.append(label+' missing route fields '+', '.join(sorted(missing)))
    slice_identity,slice_errors=parse_slice_identity(fields.get('Slice ID / version'),label+' Slice')
    errors.extend(slice_errors); parsed['slice']=slice_identity
    route_id=str(fields.get('Integration Route ID','')).strip()
    if not stable_id(route_id): errors.append(label+' requires a safe Integration Route ID')
    parsed['route']=route_id
    candidate=exact_id_hash(fields.get('Integration candidate ID / exact hash'))
    if not candidate: errors.append(label+' requires candidate ID / exact lowercase sha256 identity')
    parsed['candidate']=candidate
    product,product_errors=parse_product_commit_identity(fields.get('Product Baseline identity / frozen commit'))
    errors.extend(product_errors); parsed['product']=product
    mainline=str(fields.get('Primary product mainline ID','')).strip()
    if not stable_id(mainline): errors.append(label+' requires a safe Primary product mainline ID')
    parsed['mainline']=mainline

    ui,ui_errors=parse_exact_record_values(
        fields.get('Applicable UI identity'),('ID','PATH','VERSION','HASH'),label+' UI identity'
    ); errors.extend(ui_errors)
    if ui:
        if not stable_id(ui.get('ID')) or not safe_subtree_path(ui.get('PATH')):
            errors.append(label+' UI identity requires safe ID and subtree path')
        if not component_version(ui.get('VERSION')) or not EXACT_HASH_RE.fullmatch(str(ui.get('HASH',''))):
            errors.append(label+' UI identity requires semantic version and lowercase content hash')
    parsed['ui']=ui
    workflow,workflow_errors=parse_exact_record_values(
        fields.get('Workflow capability identity'),('WORKFLOW','CAPABILITY'),label+' Workflow identity'
    ); errors.extend(workflow_errors)
    if workflow and not all(stable_id(workflow.get(key)) for key in ('WORKFLOW','CAPABILITY')):
        errors.append(label+' Workflow identity requires safe IDs')
    parsed['workflow']=workflow
    interface,interface_errors=parse_exact_record_values(
        fields.get('Selected entry interface'),
        ('TYPE','CAPABILITY','CONTRACT','MAP_EVIDENCE','INVOCATION'),label+' selected interface'
    ); errors.extend(interface_errors)
    if interface:
        if interface.get('TYPE') not in {'API','MCP'}:
            errors.append(label+' selected interface type must be API or MCP')
        for key in ('CAPABILITY','CONTRACT','MAP_EVIDENCE'):
            if not stable_id(interface.get(key)) or str(interface.get(key,'')).upper() in GENERIC_EVIDENCE_IDS:
                errors.append(label+' selected interface '+key+' requires a non-generic safe ID')
        if candidate:
            invocation_identity,invocation_errors=parse_bound_route_evidence(
                interface.get('INVOCATION'),candidate,route_id,label+' interface invocation'
            ); errors.extend(invocation_errors); parsed['invocation']=invocation_identity
    parsed['interface']=interface
    scenario,scenario_errors=parse_exact_record_values(
        fields.get('Simulation scenario identity'),('SIMULATION','SCENARIO','VERSION'),label+' Simulation scenario'
    ); errors.extend(scenario_errors)
    if scenario:
        if not stable_id(scenario.get('SIMULATION')) or not stable_id(scenario.get('SCENARIO')) or not component_version(scenario.get('VERSION')):
            errors.append(label+' Simulation scenario requires safe IDs and semantic version')
    parsed['scenario']=scenario
    if candidate:
        evidence_record,evidence_errors=parse_route_evidence_record(
            fields.get('Connected route evidence'),candidate,route_id
        ); errors.extend(evidence_errors); parsed['evidence']=evidence_record
    else: parsed['evidence']={}
    return parsed,errors

def validate_route_against_product(parsed,workflow_rows,ui_rows,simulation_rows,scenario_rows,handoff_fields):
    errors=[]
    if parsed.get('product'):
        baseline_id=str(handoff_fields.get('Baseline ID / version / hash','')).partition('/')[0].strip()
        if parsed['product']!=(baseline_id,str(handoff_fields.get('Project frozen exact commit SHA','')).strip()):
            errors.append('integration route Product Baseline identity/commit mismatch')
    if parsed.get('mainline')!=str(handoff_fields.get('Primary product mainline ID','')).strip():
        errors.append('integration route Primary product mainline mismatch')
    ui=parsed.get('ui',{}); ui_rows_by_id={str(row.get('UI ID','')).strip():row for row in ui_rows}
    ui_row=ui_rows_by_id.get(ui.get('ID'))
    if not ui_row or any(str(ui_row.get(field,'')).strip()!=ui.get(key) for field,key in (
        ('Subtree path','PATH'),('Component version','VERSION'),('Content hash','HASH')
    )): errors.append('integration route UI identity disagrees with UI Map')
    workflow=parsed.get('workflow',{}); workflow_rows_by_id={str(row.get('Workflow ID','')).strip():row for row in workflow_rows}
    workflow_row=workflow_rows_by_id.get(workflow.get('WORKFLOW'))
    if not workflow_row or str(workflow_row.get('Workflow Capability ID','')).strip()!=workflow.get('CAPABILITY'):
        errors.append('integration route Workflow Capability disagrees with Workflow Map')
    else:
        interface=parsed.get('interface',{}); kind=interface.get('TYPE')
        map_interface,_=parse_closed_record(
            workflow_row.get(kind+' contract / evidence') if kind in {'API','MCP'} else '',
            ['CAPABILITY','CONTRACT','EVIDENCE'],'Workflow Map selected interface'
        )
        if (
            interface.get('CAPABILITY')!=workflow.get('CAPABILITY')
            or map_interface.get('CAPABILITY')!=interface.get('CAPABILITY')
            or map_interface.get('CONTRACT')!=interface.get('CONTRACT')
            or map_interface.get('EVIDENCE')!=interface.get('MAP_EVIDENCE')
        ): errors.append('selected interface must exactly bind the mapped Workflow Capability record')
    scenario=parsed.get('scenario',{}); simulation_ids={str(row.get('Simulation ID','')).strip() for row in simulation_rows}
    if scenario.get('SIMULATION') not in simulation_ids:
        errors.append('integration route Simulation identity disagrees with Simulation Map')
    scenario_matches=[row for row in scenario_rows if str(row.get('Simulation ID','')).strip()==scenario.get('SIMULATION') and str(row.get('Scenario ID','')).strip()==scenario.get('SCENARIO')]
    if len(scenario_matches)!=1 or str(scenario_matches[0].get('Scenario version','')).strip()!=scenario.get('VERSION'):
        errors.append('integration route requires the exact Simulation scenario ID/version')
    elif scenario_matches:
        scenario_row=scenario_matches[0]
        for field in ('Path','Failure/recovery','Visible / invisible evidence'):
            value=str(scenario_row.get(field,'')).strip()
            if not semantic_present(value) or value.upper() in GENERIC_EVIDENCE_IDS:
                errors.append('integration Simulation scenario requires real '+field+' evidence')
        if str(scenario_row.get('Fidelity','')).strip() not in {'REAL','PRODUCTION_EQUIVALENT'}:
            errors.append('integration Simulation scenario must have real/production-equivalent fidelity')
        slice_id=parsed.get('slice')[0] if parsed.get('slice') else None
        used_by={token for token in re.split(r'[\s,;/]+',str(scenario_row.get('Used by Slice/Run/Acceptance','')).strip()) if token}
        if slice_id not in used_by:
            errors.append('integration Simulation scenario must be explicitly used by the current Slice')
    return errors

def parse_bcr_reference(value,label):
    text=str(value or '').strip()
    if text=='NONE': return None,[]
    parts=text.split(' / ',1)
    if len(parts)!=2 or not stable_id(parts[0]) or not safe_subtree_path(parts[1]):
        return None,[label+' requires NONE or exact Request ID / contained relative path']
    return (parts[0],parts[1]),[]

def validate_ui_map_change_authority(rows):
    errors=[]
    for index,row in enumerate(rows):
        if 'UI change authority' not in row and 'Baseline Change Request' not in row:
            continue
        prefix=f'UI Map row {index+1}'
        if row.get('UI change authority')!='OWNER_ONLY':
            errors.append(prefix+' UI change authority must be exact OWNER_ONLY')
        _,reference_errors=parse_bcr_reference(
            row.get('Baseline Change Request'),prefix+' Baseline Change Request'
        ); errors.extend(reference_errors)
    return errors

def parse_ui_lock_identity(value,label):
    keys=('REPOSITORY','COMMIT','ID','PATH','VERSION','HASH')
    record,errors=parse_exact_record_values(value,keys,label)
    repository=canonical_github_repository(record.get('REPOSITORY'))
    if not repository: errors.append(label+' requires the total GitHub repository identity')
    commit=str(record.get('COMMIT','')).strip()
    if not re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})',commit):
        errors.append(label+' requires an exact lowercase project commit')
    if not stable_id(record.get('ID')) or not safe_subtree_path(record.get('PATH')):
        errors.append(label+' requires a safe UI ID and subtree path')
    if not component_version(record.get('VERSION')):
        errors.append(label+' requires a semantic component version')
    if not EXACT_HASH_RE.fullmatch(str(record.get('HASH',''))):
        errors.append(label+' requires an exact lowercase content hash')
    record['REPOSITORY']=repository
    return record,errors

def _meaningful_bcr_value(value):
    text=str(value or '').strip()
    return bool(text) and text.upper() not in GENERIC_EVIDENCE_IDS

def _component_version_order(value):
    if not component_version(value): return None
    return tuple(int(part) for part in str(value).split('.'))

def _commit_is_ancestor(repository,prior_commit,new_commit):
    result=subprocess.run(
        ['git','merge-base','--is-ancestor',prior_commit,new_commit],
        cwd=repository,capture_output=True,text=True,
    )
    if result.returncode==0: return True,None
    if result.returncode==1: return False,None
    return False,'could not verify BCR project commit ancestry'

def validate_one_way_ui_lock(
    lc,baseline_path,baseline_fields,slice_parsed,ui_rows,handoff_fields,final_fields
):
    errors=[]
    exact_lock_values={
        'Lock authority':'ONE_WAY_OWNER_AUTHORITY',
        'System autonomous UI modification':'FORBIDDEN',
        'Owner-initiated / Owner-approved UI change route':'BASELINE_CHANGE_REQUEST',
    }
    for field,expected in exact_lock_values.items():
        if baseline_fields.get(field)!=expected:
            errors.append('Integration Baseline '+field+' must be '+expected)
    ui_identity=slice_parsed.get('ui',{})
    ui_id=ui_identity.get('ID')
    matches=[row for row in ui_rows if str(row.get('UI ID','')).strip()==ui_id]
    if len(matches)!=1: return errors+['one-way UI lock requires exactly one current UI Map row']
    ui_row=matches[0]
    if ui_row.get('UI change authority')!='OWNER_ONLY':
        errors.append('UI Map change authority must be exact OWNER_ONLY')
    map_bcr,map_bcr_errors=parse_bcr_reference(
        ui_row.get('Baseline Change Request'),'UI Map Baseline Change Request'
    ); errors.extend(map_bcr_errors)
    disposition=str(baseline_fields.get('UI change disposition','')).strip()
    baseline_bcr,baseline_bcr_errors=parse_bcr_reference(
        baseline_fields.get('Baseline Change Request reference'),
        'Integration Baseline Change Request reference',
    ); errors.extend(baseline_bcr_errors)
    if disposition=='UNCHANGED':
        if map_bcr is not None or baseline_bcr is not None:
            errors.append('unchanged locked UI must not claim a Baseline Change Request')
        if baseline_fields.get('Prior Integration Baseline ID')!='NOT_APPLICABLE':
            errors.append('unchanged locked UI must not fabricate a prior Integration Baseline')
        return errors
    if disposition not in {'OWNER_INITIATED','OWNER_APPROVED'}:
        errors.append('locked UI change disposition must be UNCHANGED, OWNER_INITIATED, or OWNER_APPROVED')
        return errors
    if not map_bcr or not baseline_bcr or map_bcr!=baseline_bcr:
        errors.append('Owner UI change requires one exact matching Map/Baseline BCR reference')
        return errors
    _,bcr_path=_safe_lccoding_evidence(baseline_path,baseline_bcr[1])
    if not bcr_path:
        errors.append('Owner UI change requires a contained Baseline Change Request')
        return errors
    bcr,bcr_errors=parse_markdown_fields_strict(bcr_path); errors.extend(bcr_errors)
    missing=BCR_FIELDS-set(bcr); unknown=set(bcr)-BCR_FIELDS
    if missing: errors.append('Baseline Change Request missing fields '+', '.join(sorted(missing)))
    if unknown: errors.append('Baseline Change Request has unknown fields '+', '.join(sorted(unknown)))
    if bcr.get('Artifact role')!='UI_BASELINE_CHANGE_REQUEST': errors.append('BCR artifact role mismatch')
    if (
        bcr.get('Request ID')!=baseline_bcr[0]
        or not stable_id(bcr.get('Request ID'))
        or not _meaningful_bcr_value(bcr.get('Request ID'))
    ): errors.append('BCR Request ID disagrees with lock reference or is not a safe evidence ID')
    if (
        not stable_id(bcr.get('Locked Integration Baseline ID'))
        or not _meaningful_bcr_value(bcr.get('Locked Integration Baseline ID'))
    ):
        errors.append('BCR requires the exact prior Integration Baseline ID')
    elif bcr.get('Locked Integration Baseline ID')!=baseline_fields.get('Prior Integration Baseline ID'):
        errors.append('BCR prior lock ID disagrees with the Integration Baseline reference')
    if bcr.get('Change authority')!=disposition:
        errors.append('BCR Change authority must equal the explicit Owner disposition')
    for field in ('Requested UI change','Necessity / impact record','Prior accepted work affected','Owner decision / approval evidence'):
        if not _meaningful_bcr_value(bcr.get(field)):
            errors.append('BCR '+field+' requires non-generic evidence')
    if not stable_id(bcr.get('Necessity / impact record')) or not stable_id(bcr.get('Owner decision / approval evidence')):
        errors.append('BCR impact and Owner decision evidence must be safe stable IDs')
    repository=canonical_github_repository(bcr.get('Project repository identity'))
    expected_repository=canonical_github_repository(handoff_fields.get('Project repository identity'))
    if not repository or repository!=expected_repository:
        errors.append('BCR must retain the same total project repository')
    prior_commit=str(bcr.get('Prior project commit SHA','')).strip()
    new_commit=str(bcr.get('New project commit SHA','')).strip()
    if bcr.get('New project commit differs from prior lock')!='YES' or prior_commit==new_commit:
        errors.append('BCR new project commit must be distinct from the prior lock')
    prior,prior_errors=parse_ui_lock_identity(bcr.get('Prior UI identity'),'BCR prior UI identity')
    new,new_errors=parse_ui_lock_identity(bcr.get('New UI identity'),'BCR new UI identity')
    handoff_update,handoff_errors=parse_ui_lock_identity(
        bcr.get('Product Baseline Handoff update'),'BCR Product Handoff update'
    )
    baseline_update,baseline_errors=parse_ui_lock_identity(
        bcr.get('Integration Baseline update'),'BCR Integration Baseline update'
    )
    errors.extend(prior_errors+new_errors+handoff_errors+baseline_errors)
    if prior.get('COMMIT')!=prior_commit or new.get('COMMIT')!=new_commit:
        errors.append('BCR prior/new UI identities must bind their exact project commits')
    if prior.get('REPOSITORY')!=repository or new.get('REPOSITORY')!=repository:
        errors.append('BCR prior/new UI identities must use the same total repository')
    if prior.get('ID')!=new.get('ID') or prior.get('PATH')!=new.get('PATH'):
        errors.append('BCR must change the same locked UI ID and subtree path')
    if prior.get('HASH')==new.get('HASH'):
        errors.append('BCR must contain a real UI subtree content hash change')
    prior_version=_component_version_order(prior.get('VERSION'))
    new_version=_component_version_order(new.get('VERSION'))
    if prior_version is not None and new_version is not None and new_version<=prior_version:
        errors.append('BCR new UI component version must advance beyond the prior version')
    current={
        'REPOSITORY':expected_repository,
        'COMMIT':slice_parsed.get('product')[1] if slice_parsed.get('product') else None,
        'ID':ui_identity.get('ID'),'PATH':ui_identity.get('PATH'),
        'VERSION':ui_identity.get('VERSION'),'HASH':ui_identity.get('HASH'),
    }
    if new!=current or handoff_update!=current or baseline_update!=current:
        errors.append('UI Map, Product Handoff, Integration Baseline, and BCR must converge on the exact new UI tuple')
    if new_commit!=str(handoff_fields.get('Project frozen exact commit SHA','')).strip():
        errors.append('BCR new commit must equal the current Product Baseline frozen commit')
    resolved_commits={}
    if repository:
        for label,identity,commit in (
            ('prior',prior,prior_commit),('new',new,new_commit)
        ):
            resolved,commit_error=resolve_frozen_commit(lc.parent,commit)
            if commit_error: errors.append('BCR '+label+' '+commit_error); continue
            resolved_commits[label]=resolved
            identity_row={'Path':identity.get('PATH'),'Content hash':identity.get('HASH')}
            errors.extend(verify_frozen_subtree_identity(
                lc.parent,resolved,identity_row,'BCR '+label+' UI identity'
            ))
    if set(resolved_commits)=={'prior','new'}:
        is_ancestor,ancestry_error=_commit_is_ancestor(
            lc.parent,resolved_commits['prior'],resolved_commits['new']
        )
        if ancestry_error: errors.append(ancestry_error)
        elif not is_ancestor:
            errors.append('BCR prior project commit must be an ancestor of the new commit')
    affected,affected_errors=parse_route_link_set(
        bcr.get('Affected evidence set'),'BCR affected evidence set'
    ); errors.extend(affected_errors)
    prior_affected,prior_errors=parse_route_link_set(
        bcr.get('Prior accepted work affected'),'BCR prior accepted work affected'
    ); errors.extend(prior_errors)
    if not affected or prior_affected!=affected:
        errors.append('BCR affected evidence set must exactly identify prior accepted work affected')
    candidate=slice_parsed.get('candidate'); route=slice_parsed.get('route')
    invalidation={}; reverified={}
    if candidate and affected:
        invalidation,invalidation_errors=parse_affected_route_evidence_record(
            bcr.get('Affected evidence invalidation'),affected,candidate,route,
            'BCR affected invalidation'
        )
        reverified,reverify_errors=parse_affected_route_evidence_record(
            bcr.get('Affected evidence re-verification'),affected,candidate,route,
            'BCR affected re-verification'
        )
        errors.extend(invalidation_errors+reverify_errors)
        for link in affected:
            if invalidation.get(link) and invalidation.get(link)==reverified.get(link):
                errors.append('BCR '+link+' invalidation and re-verification must be distinct evidence')
    final_changed,final_changed_errors=parse_route_link_set(
        final_fields.get('Changed connected links'),'Final changed connected links'
    ); errors.extend(final_changed_errors)
    final_reused,final_reused_errors=parse_route_link_set(
        final_fields.get('Reused unchanged connected links'),'Final reused connected links'
    ); errors.extend(final_reused_errors)
    final_new,final_new_errors=parse_route_link_set(
        final_fields.get('New / repeated connected links'),'Final new connected links'
    ); errors.extend(final_new_errors)
    if affected!=final_changed or affected!=final_new:
        errors.append('BCR affected evidence must be reverified in current-candidate Final Verification')
    if candidate:
        for link in affected:
            if reverified.get(link)!=slice_parsed.get('evidence',{}).get(link):
                errors.append('BCR '+link+' re-verification must equal current connected-link evidence')
    reuse,reuse_errors=parse_exact_record_values(
        bcr.get('Unaffected evidence reuse basis'),
        ('CANDIDATE','ROUTE','LINKS','SCOPE','REASON'),'BCR unaffected reuse basis'
    ); errors.extend(reuse_errors)
    reuse_candidate=exact_id_hash(reuse.get('CANDIDATE'))
    reuse_links,reuse_link_errors=parse_route_link_set(reuse.get('LINKS'),'BCR reused links')
    errors.extend(reuse_link_errors)
    scope_identity,scope_errors=parse_bound_route_evidence(
        reuse.get('SCOPE'),candidate,route,'BCR reuse scope'
    ) if candidate else (None,[])
    errors.extend(scope_errors)
    if (
        reuse_candidate!=candidate or reuse.get('ROUTE')!=route
        or reuse.get('REASON')!='UNCHANGED_EQUIVALENT' or not scope_identity
        or affected.intersection(reuse_links) or reuse_links!=final_reused
    ): errors.append('BCR reuse is limited to exact unaffected current-candidate proof')
    if bcr.get('Preservation route')!='PRESERVE_HISTORY_NO_SILENT_OVERWRITE_NO_AUTOMATIC_RESTORE':
        errors.append('BCR must preserve history without silent overwrite or automatic restore')
    if not component_version(bcr.get('New baseline version')):
        errors.append('BCR requires a semantic new baseline version')
    elif bcr.get('New baseline version')!=new.get('VERSION'):
        errors.append('BCR new baseline version must equal the new UI component version')
    return errors

def validate_real_product_integration(
    lc,slice_path,slice_fields,workflow_rows,ui_rows,simulation_rows,scenario_rows,handoff_fields
):
    errors=[]
    if not present(slice_fields.get('Integration Route ID')): return errors
    unknown=set(slice_fields)-SLICE_ROUTE_ALLOWED; missing=SLICE_ROUTE_ALLOWED-set(slice_fields)
    if unknown: errors.append('Feature Slice has unknown integration fields '+', '.join(sorted(unknown)))
    if missing: errors.append('Feature Slice missing integration fields '+', '.join(sorted(missing)))
    slice_parsed,slice_errors=parse_route_common(slice_fields,'Feature Slice')
    errors.extend(slice_errors)
    connection=str(slice_fields.get('Cross-layer connection evidence','')).strip()
    if connection=='UNPROVEN': return errors
    if not connection.startswith('PROVEN:') or not slice_parsed.get('candidate'):
        errors.append('Feature Slice real integration must be PROVEN by current route evidence')
    else:
        connection_identity,connection_errors=parse_bound_route_evidence(
            connection.split(':',1)[1].strip(),slice_parsed['candidate'],slice_parsed['route'],
            'Feature Slice connection proof'
        ); errors.extend(connection_errors)
        slice_parsed['connection']=connection_identity
    errors.extend(validate_route_against_product(
        slice_parsed,workflow_rows,ui_rows,simulation_rows,scenario_rows,handoff_fields
    ))
    candidate=slice_parsed.get('candidate'); product=slice_parsed.get('product')
    ui=slice_parsed.get('ui',{}); workflow=slice_parsed.get('workflow',{}); scenario=slice_parsed.get('scenario',{})
    if candidate and slice_fields.get('Accepted integration candidate / baseline identity')!=str(slice_fields.get('Integration candidate ID / exact hash','')).strip():
        errors.append('Feature Slice accepted candidate identity disagrees with integration candidate')
    if product and str(slice_fields.get('Product Baseline trace','')).strip()!=product[0]:
        errors.append('Feature Slice Product Baseline trace disagrees with route identity')
    workflow_references,workflow_reference_errors=parse_closed_id_list(
        slice_fields.get('Workflow references'),'Feature Slice Workflow references'
    ); errors.extend(workflow_reference_errors)
    ui_references,ui_reference_errors=parse_closed_id_list(
        slice_fields.get('UI references'),'Feature Slice UI references'
    ); errors.extend(ui_reference_errors)
    if workflow and workflow_references!={workflow.get('WORKFLOW')}:
        errors.append('Feature Slice Workflow references must equal the connected Workflow')
    if ui and ui_references!={ui.get('ID')}:
        errors.append('Feature Slice UI references must equal the connected UI')
    expected_scenario=(scenario.get('SCENARIO')+' / '+scenario.get('VERSION')) if scenario else None
    if expected_scenario and str(slice_fields.get('Scenario IDs / versions','')).strip()!=expected_scenario:
        errors.append('Feature Slice Scenario ID/version disagrees with connected Simulation scenario')
    expected_mainline=str(slice_parsed.get('mainline',''))+' / OWNER_CONFIRMED'
    if str(slice_fields.get('Primary product mainline ID / Owner confirmation','')).strip()!=expected_mainline:
        errors.append('Feature Slice Primary mainline/Owner confirmation disagrees with route')
    repository_commit=str(slice_fields.get('Project repository / exact baseline commit','')).split('::',1)
    if len(repository_commit)!=2 or not product or repository_commit[1].strip()!=product[1] or canonical_github_repository(repository_commit[0].strip())!=canonical_github_repository(handoff_fields.get('Project repository identity')):
        errors.append('Feature Slice repository/commit disagrees with Product Baseline')
    if ui and (
        str(slice_fields.get('Applicable UI subtree ID / path','')).strip()!=ui.get('ID')+' :: '+ui.get('PATH')
        or str(slice_fields.get('UI component version','')).strip()!=ui.get('VERSION')
        or str(slice_fields.get('UI content hash','')).strip()!=ui.get('HASH')
    ): errors.append('Feature Slice legacy UI tuple disagrees with connected UI identity')
    if str(slice_fields.get('Real integration route','')).strip()!=slice_parsed.get('route'):
        errors.append('Feature Slice real integration route must equal Integration Route ID')
    phase2=str(slice_fields.get('Phase-2-only demonstration evidence','')).strip()
    demonstration_identity=None
    if phase2!='NONE':
        prefix,separator,item=phase2.partition(':')
        if prefix!='NON_ACCEPTANCE' or not separator or not slice_parsed.get('candidate'):
            errors.append('Phase-2 demonstration evidence must be NONE or explicit NON_ACCEPTANCE evidence')
        else:
            demonstration_identity,demo_errors=parse_bound_route_evidence(
                item,slice_parsed['candidate'],slice_parsed['route'],'Phase-2 demonstration evidence'
            ); errors.extend(demo_errors)
            if demonstration_identity in set(slice_parsed.get('evidence',{}).values()):
                errors.append('Phase-2 demonstration evidence cannot satisfy connected route evidence')
            if demonstration_identity in {slice_parsed.get('invocation'),slice_parsed.get('connection')}:
                errors.append('Phase-2 demonstration evidence cannot satisfy interface or connection proof')
    route_bound_slice_fields=(
        'Applicable Simulation scenario trace','State / data / permission trace',
        'Exception / recovery trace','Shared capability result','D0-D3 evidence plan',
        'Visible completion','Invisible completion','Normal Loop Owner Acceptance route(s)',
        'Post-Security Owner Acceptance route',
    )
    if candidate:
        for field in route_bound_slice_fields:
            identity,item_errors=parse_bound_route_evidence(
                slice_fields.get(field),candidate,slice_parsed['route'],'Feature Slice '+field
            ); errors.extend(item_errors)
            if identity==demonstration_identity:
                errors.append('Phase-2 demonstration evidence cannot satisfy '+field)
        first_run_parts=str(slice_fields.get('First Proving Run ID / evidence','')).split(' / ',1)
        if len(first_run_parts)!=2 or not stable_id(first_run_parts[0]):
            errors.append('First Proving Run requires exact Run ID / candidate-bound evidence')
        else:
            first_identity,first_errors=parse_bound_route_evidence(
                first_run_parts[1],candidate,slice_parsed['route'],'First Proving Run evidence'
            ); errors.extend(first_errors)
            if first_identity==demonstration_identity:
                errors.append('Phase-2 demonstration evidence cannot satisfy First Proving Run proof')
        if expected_scenario and str(slice_fields.get('First Proving Run production E2E scenario','')).strip()!=expected_scenario:
            errors.append('First Proving Run must use the exact connected Simulation scenario')

    _,baseline_path=_safe_lccoding_evidence(slice_path,slice_fields.get('Integration Baseline reference'))
    _,final_path=_safe_lccoding_evidence(slice_path,slice_fields.get('Final Feature Verification reference'))
    if not baseline_path: errors.append('Feature Slice requires a contained Integration Baseline reference')
    if not final_path: errors.append('Feature Slice requires a contained Final Feature Verification reference')
    if not baseline_path or not final_path: return errors
    baseline_fields,baseline_field_errors=parse_markdown_fields_strict(baseline_path)
    final_fields,final_field_errors=parse_markdown_fields_strict(final_path)
    errors.extend(baseline_field_errors+final_field_errors)
    for label,fields,allowed,required in (
        ('Integration Baseline',baseline_fields,BASELINE_ROUTE_ALLOWED,BASELINE_ROUTE_REQUIRED),
        ('Final Feature Verification',final_fields,FINAL_ROUTE_ALLOWED,FINAL_ROUTE_REQUIRED),
    ):
        unknown=set(fields)-allowed; missing=required-set(fields)
        if unknown: errors.append(label+' has unknown integration fields '+', '.join(sorted(unknown)))
        if missing: errors.append(label+' missing integration fields '+', '.join(sorted(missing)))
    if baseline_fields.get('Artifact role')!='INTEGRATION_BASELINE': errors.append('Integration Baseline artifact role mismatch')
    if final_fields.get('Artifact role')!='FINAL_FEATURE_VERIFICATION': errors.append('Final Feature Verification artifact role mismatch')
    baseline_parsed,baseline_errors=parse_route_common(baseline_fields,'Integration Baseline')
    final_parsed,final_errors=parse_route_common(final_fields,'Final Feature Verification')
    errors.extend(baseline_errors+final_errors)
    for field in ROUTE_COMMON_FIELDS:
        if baseline_fields.get(field)!=slice_fields.get(field) or final_fields.get(field)!=slice_fields.get(field):
            errors.append('integration artifacts disagree on '+field)
    baseline_id=str(baseline_fields.get('Baseline ID','')).strip()
    if not stable_id(baseline_id) or baseline_id!=str(slice_fields.get('Integration Baseline ID','')).strip():
        errors.append('Integration Baseline ID disagrees with Feature Slice')
    _,slice_reference=_safe_lccoding_evidence(baseline_path,baseline_fields.get('Feature Slice reference'))
    if not slice_reference or slice_reference.resolve()!=slice_path.resolve():
        errors.append('Integration Baseline must reference the exact Feature Slice')
    provenance,provenance_errors=parse_exact_record_values(
        baseline_fields.get('Integration candidate provenance'),('PROJECT_COMMIT','EVIDENCE'),
        'Integration candidate provenance'
    ); errors.extend(provenance_errors)
    if slice_parsed.get('product') and provenance.get('PROJECT_COMMIT')!=slice_parsed['product'][1]:
        errors.append('Integration candidate provenance must use the frozen Product commit')
    if slice_parsed.get('candidate'):
        provenance_identity,provenance_evidence_errors=parse_bound_route_evidence(
            provenance.get('EVIDENCE'),slice_parsed['candidate'],slice_parsed['route'],
            'Integration candidate provenance evidence'
        ); errors.extend(provenance_evidence_errors)
        if provenance_identity==demonstration_identity:
            errors.append('Phase-2 evidence cannot satisfy candidate provenance')
    if baseline_fields.get('Branch / latest accepted')!='NO':
        errors.append('Integration Baseline rejects branch, tag, HEAD, latest and worktree substitution')
    handoff_match=str(baseline_fields.get('Product Handoff identity match','')).strip()
    if not handoff_match.startswith('MATCH:') or not slice_parsed.get('candidate'):
        errors.append('Integration Baseline requires candidate-bound Product Handoff MATCH evidence')
    else:
        match_identity,match_errors=parse_bound_route_evidence(
            handoff_match.split(':',1)[1],slice_parsed['candidate'],slice_parsed['route'],
            'Product Handoff identity match'
        ); errors.extend(match_errors)
        if match_identity==demonstration_identity:
            errors.append('Phase-2 evidence cannot satisfy Product Handoff proof')

    baseline_reference=str(final_fields.get('Integration Baseline ID / reference','')).split(' / ',1)
    if len(baseline_reference)!=2 or baseline_reference[0]!=baseline_id:
        errors.append('Final Verification Integration Baseline identity mismatch')
    else:
        _,resolved_baseline=_safe_lccoding_evidence(final_path,baseline_reference[1])
        if not resolved_baseline or resolved_baseline.resolve()!=baseline_path.resolve():
            errors.append('Final Verification must reference the exact Integration Baseline')
    terminal,terminal_errors=parse_exact_record_values(
        final_fields.get('D3 / Loop Owner Acceptance evidence'),('D3','OWNER'),
        'Final terminal evidence'
    ); errors.extend(terminal_errors)
    if slice_parsed.get('candidate'):
        for key,value in terminal.items():
            identity,item_errors=parse_bound_route_evidence(
                value,slice_parsed['candidate'],slice_parsed['route'],'Final '+key+' evidence'
            ); errors.extend(item_errors)
            if identity==demonstration_identity: errors.append('Phase-2 evidence cannot satisfy Final terminal proof')
    if final_fields.get('Phase-2-only evidence used as acceptance proof')!='NO':
        errors.append('Final Verification must exclude Phase-2-only evidence from acceptance')
    if (
        'Phase-2-only static UI / mock / stub / manually staged state used as acceptance proof' in final_fields
        and final_fields.get('Phase-2-only static UI / mock / stub / manually staged state used as acceptance proof')!='NO'
    ): errors.append('Final Verification legacy Phase-2 projection must remain exact NO')
    changed,changed_errors=parse_route_link_set(final_fields.get('Changed connected links'),'Changed connected links')
    reused,reused_errors=parse_route_link_set(final_fields.get('Reused unchanged connected links'),'Reused unchanged connected links')
    new,new_errors=parse_route_link_set(final_fields.get('New / repeated connected links'),'New / repeated connected links')
    errors.extend(changed_errors+reused_errors+new_errors)
    if not changed.issubset(new): errors.append('every changed connected link requires new or repeated evidence')
    if changed.intersection(reused): errors.append('changed connected links cannot reuse stale evidence')
    if reused.intersection(new): errors.append('connected links cannot be both reused and new')
    if reused.union(new)!=set(ROUTE_LINKS): errors.append('Final Verification must cover every connected route link')
    reuse_basis,reuse_errors=parse_exact_record_values(
        final_fields.get('Evidence reuse basis'),('CANDIDATE','ROUTE','SCOPE','ENVIRONMENT','REASON'),
        'Evidence reuse basis'
    ); errors.extend(reuse_errors)
    if slice_parsed.get('candidate'):
        reuse_candidate=exact_id_hash(reuse_basis.get('CANDIDATE'))
        scope_identity,scope_errors=parse_bound_route_evidence(
            reuse_basis.get('SCOPE'),slice_parsed['candidate'],slice_parsed['route'],
            'reuse scope evidence'
        )
        environment_identity,environment_errors=parse_bound_route_evidence(
            reuse_basis.get('ENVIRONMENT'),slice_parsed['candidate'],slice_parsed['route'],
            'reuse environment evidence'
        )
        errors.extend(scope_errors+environment_errors)
        if (
            reuse_candidate!=slice_parsed['candidate']
            or reuse_basis.get('ROUTE')!=slice_parsed['route']
            or reuse_basis.get('REASON')!='UNCHANGED_EQUIVALENT'
            or not scope_identity or not environment_identity
        ): errors.append('reused evidence requires exact candidate/route/scope/environment unchanged proof')
    if final_fields.get('Final verdict')!='PASS':
        errors.append('current real integration Final verdict must PASS or remain blocked')
    errors.extend(validate_one_way_ui_lock(
        lc,baseline_path,baseline_fields,slice_parsed,ui_rows,handoff_fields,final_fields
    ))
    return errors

def validate_owner_gap_lineage(status,records):
    errors=[]; indexed={}
    for item in status.get('open_owner_gaps',[]):
        if not isinstance(item,dict):
            errors.append('open_owner_gaps entries must be indexes'); continue
        extras=set(item)-OPEN_GAP_INDEX_FIELDS
        if extras: errors.append('open_owner_gaps may only index gap identity and evidence pointers')
        gap_id=item.get('gap_id')
        if not present(gap_id) or item.get('state') not in {'OPEN','IN_CLOSURE'}:
            errors.append('open_owner_gaps entry requires gap_id and open state')
        if not present(item.get('source_acceptance')) or not item.get('evidence_pointers'):
            errors.append('open_owner_gaps entry requires source acceptance and evidence pointers')
        if gap_id in indexed: errors.append('duplicate open Owner gap '+str(gap_id))
        indexed[gap_id]=item
    record_by_id={record.get('Owner Gap ID'):record for record in records if present(record.get('Owner Gap ID'))}
    for gap_id,item in indexed.items():
        record=record_by_id.get(gap_id)
        if not record:
            errors.append('open Owner gap missing lineage record '+str(gap_id)); continue
        if record.get('Gap status')=='CLOSED':
            errors.append('CLOSED gap remains in open_owner_gaps')
        if record.get('Gap source Acceptance ID')!=item.get('source_acceptance'):
            errors.append('Owner gap source acceptance disagrees with status index')
    for gap_id,record in record_by_id.items():
        state=record.get('Gap status')
        route=record.get('Gap route')
        if state not in {'OPEN','IN_CLOSURE','CLOSED'}:
            errors.append('Owner gap requires OPEN, IN_CLOSURE, or CLOSED status')
        if route not in {'IMPACT_CORRECTION','CALABASH_DEFINITION_CHANGE','OWNER_DEFERRED'}:
            errors.append('Owner gap requires an LCCoding handoff route')
        for field in ['Gap source Acceptance ID','Gap source candidate / scenario']:
            if not present(record.get(field)): errors.append('Owner gap missing '+field)
        if state in {'OPEN','IN_CLOSURE'} and gap_id not in indexed:
            errors.append('open Owner gap missing from authoritative status index')
        if state=='CLOSED':
            required=['Impact / definition reference','Correction Run IDs','Affected D0-D3 receipts','Delta re-verification receipt','Delta Owner re-acceptance receipt']
            missing=[field for field in required if not present(record.get(field))]
            if missing: errors.append('CLOSED requires '+', '.join(missing))
            if gap_id in indexed and 'CLOSED gap remains in open_owner_gaps' not in errors:
                errors.append('CLOSED gap remains in open_owner_gaps')
            if route=='OWNER_DEFERRED': errors.append('deferred Owner gap cannot be CLOSED without a new route')
    return errors

def parse_markdown_fields(path):
    fields={}
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('- ') and ':' in line:
            key,value=line[2:].split(':',1)
            fields[key.strip()]=value.strip()
    return fields

def parse_markdown_fields_strict(path):
    fields={}; errors=[]
    try: lines=path.read_text(encoding='utf-8').splitlines()
    except (OSError,UnicodeError): return {},['cannot read UTF-8 evidence record '+str(path)]
    for line in lines:
        if not line.startswith('- ') or ':' not in line: continue
        key,value=line[2:].split(':',1); key=key.strip()
        if key in fields: errors.append('duplicate evidence field '+key)
        else: fields[key]=value.strip()
    return fields,errors

def exact_manifest_hash(path):
    return 'sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()

def semantic_present(value):
    return str(value or '').strip().upper() not in {'','PENDING','UNKNOWN','NONE','NOT_APPLICABLE'}

def stable_id(value):
    text=str(value or '').strip()
    return bool(STABLE_ID_RE.fullmatch(text)) and text not in {'.','..'}

def exact_id_hash(value):
    text=str(value or '').strip()
    match=re.fullmatch(r'([A-Za-z0-9][A-Za-z0-9._-]{0,127}) / (sha256:[0-9a-f]{64})',text)
    if not match or match.group(1) in {'.','..'}: return None
    return match.group(1),match.group(2)

def exact_ui_integration_identity(value):
    parts=[part.strip() for part in str(value or '').split('/')]
    if len(parts)!=2 or not all(stable_id(part) for part in parts): return None
    return parts[0],parts[1]

def comma_values(value):
    return [item.strip() for item in str(value or '').split(',') if item.strip()]

def non_generic_evidence(value):
    return _VULNERABILITY_VALIDATOR.safe_id(value)

LOOP_CONTROL_CONTRACT_KEYS={
    'contract_id','contract_version','owner','is_loop_method',
    'runtime_execution_owner','method_consumers','worker_wake','run_patrol',
    'heartbeat_separation','runtime_attestation_policy','supervisor_wait',
    'prohibitions','progress','capacity','model_policy',
}
LOOP_CONTROL_BINDING_KEYS={
    'artifact_type','binding_version','contract','runtime_attestation',
    'method_mapping','model_binding','local_control',
}
LOOP_CONTROL_MAPPING_KEYS={
    'method','topology_owned_progress_fields','topology_owned_capacity_fields',
    'topology_owned_model_fields','topology_owned_evidence_fields',
}
LOOP_CONTROL_ATTESTATION_KEYS={
    'runtime_owner','runtime_adapter_id','attestation_root','evidence_digest',
    'observed_at','validated_at','expires_at','currentness','result',
}
LOOP_CONTROL_MODEL_KEYS={
    'role_kind','actual_model','reference_model','capability_class','reasoning_effort',
    'selection_reason','equivalence','owner_ultra_authorization',
}

def loop_closed_object(value,keys,label,errors):
    if not isinstance(value,dict):
        errors.append('LOOP_CONTROL_BINDING_'+label+'_INVALID'); return {}
    if set(value)!=set(keys): errors.append('LOOP_CONTROL_BINDING_'+label+'_INVALID')
    return value

def loop_exact_hash(value):
    return bool(EXACT_HASH_RE.fullmatch(str(value or '').strip()))

def loop_timestamp(value):
    text=str(value or '').strip()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z',text): return None
    try: return datetime.strptime(text,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    except ValueError: return None

def validate_loop_control_contract(contract):
    errors=[]
    value=loop_closed_object(contract,LOOP_CONTROL_CONTRACT_KEYS,'CONTRACT',errors)
    if value.get('contract_id')!='LCCODING_LOOP_CONTROL' or value.get('contract_version')!='1.0.0':
        errors.append('LOOP_CONTROL_CONTRACT_IDENTITY_INVALID')
    if value.get('owner')!='LCCoding' or value.get('is_loop_method') is not False:
        errors.append('LOOP_CONTROL_CONTRACT_BOUNDARY_INVALID')
    if value.get('runtime_execution_owner')!='LCagent_or_trusted_runtime' or value.get('method_consumers')!=['SLK','CLK','GLK']:
        errors.append('LOOP_CONTROL_CONTRACT_RUNTIME_OR_METHODS_INVALID')
    if value.get('worker_wake')!={
        'initiator':'WORKER','receiver':'CHECKER','retry_interval_seconds':120,
        'levels':['DIRECT_SEND','SAME_TASK_READ_LIST_UNARCHIVE','CHECKER_WAKE_HEARTBEAT','PENDING_WAKE_PATROL_FALLBACK'],
        'ack':'RUN_GO_CELL_ROUND_BOUND_WAKE_ACK','heartbeat_kind':'CHECKER_WAKE_HEARTBEAT',
        'maximum_temporary_heartbeats_per_delivery_wake_incident':1,
        'terminal_action':'REMOVE_ON_WAKE_ACK_OR_TERMINAL_FALLBACK',
    }:
        errors.append('LOOP_CONTROL_CONTRACT_WORKER_WAKE_INVALID')
    if value.get('run_patrol')!={
        'role':'RUN_PATROL','maximum_conversations_per_run':1,
        'heartbeat_kind':'RUN_PATROL_HEARTBEAT','maximum_run_patrol_heartbeats_per_run':1,
        'interval_minutes':{'LOW':10,'MEDIUM':15,'HIGH':30},
        'may_create_conversations':False,'may_report_engineering_progress':False,
        'terminal_action':'ARCHIVE_AND_DELETE_HEARTBEAT',
        'checks':['UNEXPLAINED_LOOP_STOPPAGE','PENDING_WAKE','ACTUAL_SUBAGENT_USE','SUPERVISOR_FORBIDDEN_WAIT','DUPLICATE_PATROL_OR_HEARTBEAT','PIN_PROVENANCE','TERMINAL_CLOSURE'],
    }:
        errors.append('LOOP_CONTROL_CONTRACT_RUN_PATROL_INVALID')
    if value.get('heartbeat_separation')!={
        'shared_id':'FORBIDDEN','shared_lifecycle':'FORBIDDEN',
        'shared_counting':'FORBIDDEN','shared_evidence_claim':'FORBIDDEN',
    }:
        errors.append('LOOP_CONTROL_CONTRACT_HEARTBEAT_SEPARATION_INVALID')
    if value.get('runtime_attestation_policy')!={
        'required_owner':'LCagent_or_trusted_runtime','required_result':'PASS',
        'required_currentness':'CURRENT','max_validated_age_minutes':30,
        'max_validity_minutes':60,
    }:
        errors.append('LOOP_CONTROL_CONTRACT_ATTESTATION_POLICY_INVALID')
    if value.get('supervisor_wait')!={
        'positive_duration_wait_threads':'FORBIDDEN','looping_wait_threads':'FORBIDDEN',
        'wait_all':'FORBIDDEN','zero_timeout_snapshot':'ALLOWED',
    }:
        errors.append('LOOP_CONTROL_CONTRACT_SUPERVISOR_WAIT_INVALID')
    if value.get('prohibitions')!={
        'actual_subagent_operations':['spawn_agent','delegate_task','hidden_agent','background_agent'],
        'agent_pin':'FORBIDDEN','owner_pin':'EXPLICIT_OWNER_UI_OR_ITEM_AUTHORIZATION_ONLY',
    }:
        errors.append('LOOP_CONTROL_CONTRACT_PROHIBITIONS_INVALID')
    if value.get('progress')!={
        'worker':'DELIVERED_CELL_N_OVER_N_TO_CHECKER',
        'checker':'ACCEPTED_CELL_N_OVER_N_TO_SUPERVISOR',
        'supervisor':'GO_LEVEL_RUN_AND_MATERIAL_STATE',
        'patrol':'NO_ENGINEERING_PROGRESS',
    }:
        errors.append('LOOP_CONTROL_CONTRACT_PROGRESS_INVALID')
    if value.get('capacity')!={
        'gate_before_dispatch':True,
        'outcomes':['PASS','SPLIT_REQUIRED','CAPACITY_BLOCKED'],
        'worker_may_self_split':False,
    }:
        errors.append('LOOP_CONTROL_CONTRACT_CAPACITY_INVALID')
    if value.get('model_policy')!={
        'patrol':{'reference_model':'gpt-5.6-luna','capability_class':'FASTEST_NONTECHNICAL','reasoning_effort':'xhigh'},
        'technical':{'reference_model':'gpt-5.6-terra','capability_class':'NORMAL_TECHNICAL','reasoning_effort':'xhigh'},
        'high_difficulty_correction':{'reference_model':'gpt-5.6-sol','capability_class':'DIFFICULT_CORRECTION','reasoning_effort':'xhigh'},
        'ultra':{
            'requires':'ITEM_SPECIFIC_OWNER_AUTHORIZATION',
            'allowed_role_kind':'HIGH_DIFFICULTY_CORRECTION',
            'authorization_fields':['item_id','owner_authorization_id','authorization_evidence_digest','result'],
            'authorization_result':'OWNER_APPROVED_ULTRA',
        },
        'forbidden_model_maximum':'gpt-5.5',
    }:
        errors.append('LOOP_CONTROL_CONTRACT_MODEL_POLICY_INVALID')
    return errors

def validate_loop_control_mapping(mapping,method,model_binding,errors):
    value=loop_closed_object(mapping,LOOP_CONTROL_MAPPING_KEYS,'METHOD_MAPPING',errors)
    if value.get('method') not in LOOP_CONTROL_METHODS:
        errors.append('LOOP_CONTROL_BINDING_METHOD_INVALID'); return
    method=value.get('method')
    all_values=[]
    for key in sorted(LOOP_CONTROL_MAPPING_KEYS-{'method'}):
        fields=value.get(key)
        if not isinstance(fields,list) or not fields:
            errors.append('LOOP_CONTROL_BINDING_METHOD_MAPPING_INVALID'); continue
        for field in fields:
            if not non_generic_evidence(field) or not str(field).startswith(method+'_'):
                errors.append('LOOP_CONTROL_BINDING_METHOD_MAPPING_INVALID')
            if any(token in str(field) for token in ('HEARTBEAT','PENDING_WAKE','PATROL','SUPERVISOR_WAIT','CHECKER_WAKE')):
                errors.append('LOOP_CONTROL_BINDING_COMMON_RULE_SUBSTITUTION')
            all_values.append(field)
    if len(all_values)!=len(set(all_values)):
        errors.append('LOOP_CONTROL_BINDING_METHOD_MAPPING_INVALID')
    if model_binding.get('role_kind')=='PATROL' and any('ENGINEERING_PROGRESS' in str(field) for field in value.get('topology_owned_progress_fields',[])):
        errors.append('LOOP_CONTROL_BINDING_PATROL_PROGRESS_INVALID')

def validate_loop_control_model(value,errors):
    model=loop_closed_object(value,LOOP_CONTROL_MODEL_KEYS,'MODEL_BINDING',errors)
    role=model.get('role_kind')
    expected={
        'PATROL':('gpt-5.6-luna','FASTEST_NONTECHNICAL','PATROL_NONTECHNICAL'),
        'TECHNICAL':('gpt-5.6-terra','NORMAL_TECHNICAL','NORMAL_TECHNICAL'),
        'HIGH_DIFFICULTY_CORRECTION':('gpt-5.6-sol','DIFFICULT_CORRECTION','HIGH_DIFFICULTY_CORRECTION'),
    }.get(role)
    if not expected:
        errors.append('LOOP_CONTROL_BINDING_MODEL_ROLE_INVALID'); return model
    reference,capability,reason=expected
    if model.get('reference_model')!=reference or model.get('capability_class')!=capability or model.get('selection_reason')!=reason:
        errors.append('LOOP_CONTROL_BINDING_MODEL_PURPOSE_INVALID')
    actual=str(model.get('actual_model') or '')
    if not non_generic_evidence(actual) or re.match(r'^gpt-(?:[0-4](?:\.\d+)?|5(?:\.[0-5](?:\.\d+)?)?)(?:$|[_-])',actual,re.IGNORECASE):
        errors.append('LOOP_CONTROL_BINDING_MODEL_MINIMUM_INVALID')
    effort=model.get('reasoning_effort')
    if effort not in {'xhigh','ultra'}: errors.append('LOOP_CONTROL_BINDING_MODEL_EFFORT_INVALID')
    equivalence=loop_closed_object(model.get('equivalence'),{'status','evidence_id','evidence_digest'},'MODEL_EQUIVALENCE',errors)
    if actual==reference:
        if equivalence.get('status')!='EXACT_REFERENCE' or equivalence.get('evidence_id')!='NOT_APPLICABLE' or equivalence.get('evidence_digest')!='NOT_APPLICABLE':
            errors.append('LOOP_CONTROL_BINDING_MODEL_EQUIVALENCE_INVALID')
    elif equivalence.get('status')!='TRUSTED_EQUIVALENT' or not non_generic_evidence(equivalence.get('evidence_id')) or not loop_exact_hash(equivalence.get('evidence_digest')):
        errors.append('LOOP_CONTROL_BINDING_MODEL_EQUIVALENCE_INVALID')
    ultra_authorization=model.get('owner_ultra_authorization')
    if effort=='ultra':
        authorization=loop_closed_object(
            ultra_authorization,
            {'item_id','owner_authorization_id','authorization_evidence_digest','result'},
            'ULTRA_AUTHORIZATION',errors,
        )
        if role!='HIGH_DIFFICULTY_CORRECTION' or not non_generic_evidence(authorization.get('item_id')) or not non_generic_evidence(authorization.get('owner_authorization_id')) or not loop_exact_hash(authorization.get('authorization_evidence_digest')) or authorization.get('result')!='OWNER_APPROVED_ULTRA':
            errors.append('LOOP_CONTROL_BINDING_ULTRA_UNAUTHORIZED')
    elif ultra_authorization!='NOT_APPLICABLE': errors.append('LOOP_CONTROL_BINDING_ULTRA_UNAUTHORIZED')
    return model

def validate_loop_control_retirement(local_control,method,errors):
    state=local_control.get('state') if isinstance(local_control,dict) else None
    if state in {'ACTIVE','RETAINED'}:
        loop_closed_object(local_control,{'state'},'LOCAL_CONTROL',errors); return
    if state!='RETIRED':
        errors.append('LOOP_CONTROL_BINDING_LOCAL_CONTROL_INVALID'); return
    value=loop_closed_object(local_control,{'state','retirement_evidence'},'LOCAL_CONTROL',errors)
    retirement=loop_closed_object(value.get('retirement_evidence'),{'runtime_conformance','historical_receipts','owner_approved_release'},'RETIREMENT_EVIDENCE',errors)
    conformance=loop_closed_object(retirement.get('runtime_conformance'),{'positive','negative'},'RETIREMENT_CONFORMANCE',errors)
    evidence_ids=[]
    for key in ('positive','negative'):
        item=loop_closed_object(conformance.get(key),{'evidence_id','evidence_digest','result'},'RETIREMENT_'+key.upper(),errors)
        if not non_generic_evidence(item.get('evidence_id')) or not loop_exact_hash(item.get('evidence_digest')) or item.get('result')!='PASS':
            errors.append('LOOP_CONTROL_BINDING_RETIREMENT_CONFORMANCE_INVALID')
        evidence_ids.append(item.get('evidence_id'))
    if len(evidence_ids)!=len(set(evidence_ids)): errors.append('LOOP_CONTROL_BINDING_RETIREMENT_CONFORMANCE_INVALID')
    history=loop_closed_object(retirement.get('historical_receipts'),{'status','evidence_id','evidence_digest'},'HISTORICAL_RECEIPTS',errors)
    if history.get('status')!='READABLE' or not non_generic_evidence(history.get('evidence_id')) or not loop_exact_hash(history.get('evidence_digest')):
        errors.append('LOOP_CONTROL_BINDING_HISTORICAL_RECEIPTS_INVALID')
    release=loop_closed_object(retirement.get('owner_approved_release'),{'release_id','approval_evidence_id','approval_evidence_digest','result'},'OWNER_RELEASE',errors)
    if method not in LOOP_CONTROL_METHODS or not non_generic_evidence(release.get('release_id')) or not str(release.get('release_id')).startswith(method+'-') or not non_generic_evidence(release.get('approval_evidence_id')) or not loop_exact_hash(release.get('approval_evidence_digest')) or release.get('result')!='LOCAL_CONTROL_RETIRED':
        errors.append('LOOP_CONTROL_BINDING_OWNER_RELEASE_INVALID')

def validate_loop_control_binding(lc,contract_path=LOOP_CONTROL_CONTRACT_PATH,as_of=None):
    binding_path=Path(lc)/LOOP_CONTROL_BINDING_NAME
    if not binding_path.exists(): return []
    errors=[]
    try: contract=strict_vulnerability_json(contract_path)
    except (OSError,UnicodeError,ValueError): return ['LOOP_CONTROL_CONTRACT_INVALID']
    errors.extend(validate_loop_control_contract(contract))
    try: binding=strict_vulnerability_json(binding_path)
    except (OSError,UnicodeError,ValueError): return errors+['LOOP_CONTROL_BINDING_INVALID_JSON']
    value=loop_closed_object(binding,LOOP_CONTROL_BINDING_KEYS,'ROOT',errors)
    if value.get('artifact_type')!='LOOP_CONTROL_BINDING' or value.get('binding_version')!='1.0.0':
        errors.append('LOOP_CONTROL_BINDING_IDENTITY_INVALID')
    contract_binding=loop_closed_object(value.get('contract'),{'contract_id','contract_version','contract_sha256'},'CONTRACT',errors)
    if contract_binding.get('contract_id')!=contract.get('contract_id') or contract_binding.get('contract_version')!=contract.get('contract_version') or contract_binding.get('contract_sha256')!=exact_manifest_hash(contract_path):
        errors.append('LOOP_CONTROL_BINDING_CONTRACT_MISMATCH')
    attestation=loop_closed_object(value.get('runtime_attestation'),LOOP_CONTROL_ATTESTATION_KEYS,'RUNTIME_ATTESTATION',errors)
    policy=contract.get('runtime_attestation_policy',{}) if isinstance(contract,dict) else {}
    if attestation.get('runtime_owner')!=policy.get('required_owner') or not non_generic_evidence(attestation.get('runtime_adapter_id')) or not non_generic_evidence(attestation.get('attestation_root')) or not loop_exact_hash(attestation.get('evidence_digest')):
        errors.append('LOOP_CONTROL_BINDING_ATTESTATION_IDENTITY_INVALID')
    observed=loop_timestamp(attestation.get('observed_at')); validated=loop_timestamp(attestation.get('validated_at')); expires=loop_timestamp(attestation.get('expires_at'))
    now=as_of or datetime.now(timezone.utc)
    if any(item is None for item in (observed,validated,expires)) or observed>validated or validated>now or expires<=now or expires>validated+timedelta(minutes=policy.get('max_validity_minutes',0)) or now-validated>timedelta(minutes=policy.get('max_validated_age_minutes',-1)):
        errors.append('LOOP_CONTROL_BINDING_ATTESTATION_CURRENTNESS_INVALID')
    if attestation.get('currentness')!=policy.get('required_currentness') or attestation.get('result')!=policy.get('required_result'):
        errors.append('LOOP_CONTROL_BINDING_ATTESTATION_RESULT_INVALID')
    model=validate_loop_control_model(value.get('model_binding'),errors)
    method=value.get('method_mapping',{}).get('method') if isinstance(value.get('method_mapping'),dict) else None
    validate_loop_control_mapping(value.get('method_mapping'),method,model,errors)
    validate_loop_control_retirement(value.get('local_control'),method,errors)
    return errors

def exact_security_id_hash(value):
    identity=exact_id_hash(value)
    return identity if identity and non_generic_evidence(identity[0]) else None

def parse_security_id_set(value,label,allowed=None,allow_none=False):
    text=str(value or '').strip()
    if allow_none and text=='NONE': return set(),[]
    raw=[item.strip() for item in text.split(',')]
    values=[item for item in raw if item]
    errors=[]
    if not values or any(not item for item in raw):
        errors.append(label+' requires a closed non-empty ID set')
    if len(values)!=len(set(values)):
        errors.append(label+' contains duplicate IDs')
    for item in values:
        if not non_generic_evidence(item): errors.append(label+' contains unsafe or generic ID '+item)
        elif allowed is not None and item not in allowed:
            errors.append(label+' contains unknown value '+item)
    return set(values),errors

def parse_id_reference(value,label,allow_not_applicable=False):
    text=str(value or '').strip()
    if allow_not_applicable and text=='NOT_APPLICABLE': return None,[]
    parts=text.split(' / ')
    if len(parts)!=2 or not non_generic_evidence(parts[0]) or not safe_subtree_path(parts[1]):
        return None,[label+' requires exact safe ID / contained-reference form']
    return (parts[0],parts[1]),[]

def parse_transitive_security_evidence(value,current_identity):
    text=str(value or '').strip()
    if text=='NONE': return {},[]
    records={}; errors=[]
    raw=[item.strip() for item in text.split(',')]
    if not raw or any(not item for item in raw):
        return {},['Transitive affected surface evidence is malformed']
    for item in raw:
        parts=item.split('@')
        if len(parts)!=4:
            errors.append('Transitive affected surface evidence requires SURFACE@CANDIDATE@HASH@EVIDENCE')
            continue
        surface_id,candidate_id,candidate_hash,evidence_id=parts
        if not stable_id(surface_id): errors.append('Transitive affected surface has unsafe ID')
        elif surface_id in records: errors.append('Transitive affected surface has duplicate ID '+surface_id)
        if (candidate_id,candidate_hash)!=current_identity:
            errors.append('Transitive affected surface evidence binds the wrong candidate')
        if not non_generic_evidence(evidence_id):
            errors.append('Transitive affected surface evidence requires non-generic evidence ID')
        records[surface_id]=evidence_id
    return records,errors

def parse_security_preservation(value,classification,prior_identity,current_identity):
    text=str(value or '').strip(); records={}; errors=[]
    for item in [part.strip() for part in text.split(';') if part.strip()]:
        parts=item.split('@'); key=parts[0]
        if key in records: errors.append('Security preservation evidence has duplicate '+key); continue
        if key in {'PRIOR','CURRENT'}:
            if len(parts)!=3 or not exact_security_identity(parts[1],parts[2]):
                errors.append('Security preservation '+key+' identity is malformed'); continue
            records[key]=(parts[1],parts[2])
        elif len(parts)==2:
            records[key]=parts[1]
        else: errors.append('Security preservation evidence is malformed')
    if classification=='PROVEN_SECURITY_SURFACE_NEUTRAL':
        expected={'MODE','EVIDENCE','PRIOR','CURRENT'}
        if set(records)!=expected or records.get('MODE')!='NEUTRAL':
            errors.append('neutral preservation requires one closed evidence record')
        if not non_generic_evidence(records.get('EVIDENCE')):
            errors.append('neutral preservation requires non-generic evidence')
    else:
        expected={'MODE','TRANSFORMATION','SECURITY_EQUIVALENCE','PRIOR','CURRENT'}
        if set(records)!=expected or records.get('MODE')!='PACKAGING_EQUIVALENCE':
            errors.append('packaging preservation requires closed transformation and security equivalence evidence')
        for field in ['TRANSFORMATION','SECURITY_EQUIVALENCE']:
            if not non_generic_evidence(records.get(field)):
                errors.append('packaging preservation requires non-generic '+field+' evidence')
    if records.get('PRIOR')!=prior_identity or records.get('CURRENT')!=current_identity:
        errors.append('Security preservation evidence candidate identities mismatch')
    return errors

def parse_bound_security_records(value,label,with_evidence=False,allow_none=False):
    text=str(value or '').strip()
    if allow_none and text=='NONE': return {},[]
    records={}; errors=[]
    parts=[part.strip() for part in text.split(';')]
    if not parts or any(not part for part in parts):
        return {},[label+' requires closed candidate/surface-bound records']
    expected_parts=5 if with_evidence else 4
    for part in parts:
        fields=part.split('@')
        if len(fields)!=expected_parts:
            errors.append(label+' record must use exact ID@CANDIDATE@HASH@SURFACES'+('@EVIDENCE' if with_evidence else '')+' form')
            continue
        record_id,candidate_id,candidate_hash,surface_text=fields[:4]
        evidence_id=fields[4] if with_evidence else None
        if not non_generic_evidence(record_id):
            errors.append(label+' record requires a safe non-generic ID')
        elif record_id in records:
            errors.append(label+' contains duplicate record ID '+record_id)
        if not exact_security_identity(candidate_id,candidate_hash):
            errors.append(label+' record requires exact candidate ID/hash')
        surface_tokens=surface_text.split('+')
        surfaces=set(surface_tokens)
        if (
            not surface_tokens or any(not non_generic_evidence(item) for item in surface_tokens)
            or len(surface_tokens)!=len(surfaces)
        ):
            errors.append(label+' record requires a unique non-empty surface set')
        if with_evidence and not non_generic_evidence(evidence_id):
            errors.append(label+' remediation record requires non-generic evidence ID')
        records[record_id]={
            'candidate':(candidate_id,candidate_hash),'surfaces':surfaces,
            'evidence_id':evidence_id,
        }
    return records,errors

def closure_candidate_evidence(data):
    records={}
    sources=[]
    for field in ['new_checks','reused_security_evidence','affected_receipts']:
        value=data.get(field,[]) if isinstance(data,dict) else []
        if isinstance(value,list): sources.extend(value)
    reaudit=data.get('reaudit',{}) if isinstance(data,dict) else {}
    if isinstance(reaudit,dict) and isinstance(reaudit.get('receipt_evidence'),list):
        sources.extend(reaudit['receipt_evidence'])
    for value in sources:
        if not isinstance(value,dict): continue
        evidence_id=value.get('evidence_id')
        if not non_generic_evidence(evidence_id): continue
        surfaces=value.get('surface_ids')
        if not isinstance(surfaces,list): continue
        records[evidence_id]={
            'candidate':(value.get('candidate_id'),value.get('candidate_hash')),
            'surfaces':set(surfaces),'evidence_id':None,
        }
    return records

def validate_security_impact_fields(fields,required=False):
    present_fields=SECURITY_IMPACT_FIELDS.intersection(fields)
    if not present_fields:
        return None,(['referenced Impact Analysis requires a closed security delta'] if required else [])
    completed_general_record=(
        fields.get('Meaning impact classification') in {'MEANING_CHANGING','MEANING_NEUTRAL'}
        or fields.get('Impact result') in {'PASS','BLOCKED'}
    )
    activated=(
        required or completed_general_record
        or fields.get('Security change timing') in SECURITY_CHANGE_TIMINGS
        or fields.get('Security change classification') in SECURITY_CHANGE_CLASSIFICATIONS
        or exact_security_id_hash(fields.get('Prior candidate ID / exact hash')) is not None
        or exact_security_id_hash(fields.get('Current candidate ID / exact hash')) is not None
        or fields.get('Required security action') in {
            'PRESERVE_EXACT_CLOSURE','INVALIDATE_AND_RETURN_TO_AUDIT'
        }
    )
    if not activated: return None,[]
    errors=[]; missing=SECURITY_IMPACT_FIELDS-set(fields)
    if missing: errors.append('Impact Analysis security delta missing fields '+', '.join(sorted(missing)))
    timing=fields.get('Security change timing')
    classification=fields.get('Security change classification')
    if timing not in SECURITY_CHANGE_TIMINGS: errors.append('Security change timing is invalid')
    if classification not in SECURITY_CHANGE_CLASSIFICATIONS:
        errors.append('Security change classification is invalid')
    prior=exact_security_id_hash(fields.get('Prior candidate ID / exact hash'))
    current=exact_security_id_hash(fields.get('Current candidate ID / exact hash'))
    if not prior: errors.append('Security delta requires exact prior candidate ID/hash')
    if not current: errors.append('Security delta requires exact current candidate ID/hash')
    categories,category_errors=parse_security_id_set(
        fields.get('Changed security surface categories'),
        'Changed security surface categories',SECURITY_SURFACE_CATEGORIES,allow_none=True
    )
    affected,affected_errors=parse_security_id_set(
        fields.get('Affected security surface IDs'),'Affected security surface IDs',allow_none=True
    )
    errors.extend(category_errors); errors.extend(affected_errors)
    transitive,transitive_errors=parse_transitive_security_evidence(
        fields.get('Transitive affected surface IDs / evidence'),current or ('','')
    )
    errors.extend(transitive_errors)
    closure_reference,reference_errors=parse_id_reference(
        fields.get('Prior Vulnerability Closure Receipt ID / reference'),
        'Prior Vulnerability Closure Receipt'
    )
    acceptance_reference,acceptance_errors=parse_id_reference(
        fields.get('Prior Post-Security Owner Acceptance ID / reference'),
        'Prior Post-Security Owner Acceptance',allow_not_applicable=True
    )
    errors.extend(reference_errors); errors.extend(acceptance_errors)
    if timing=='AFTER_POST_SECURITY_OWNER_ACCEPTED' and acceptance_reference is None:
        errors.append('post-acceptance security delta requires the prior Owner acceptance reference')
    if timing=='AFTER_VULNERABILITY_CLOSED' and acceptance_reference is not None:
        errors.append('pre-acceptance security delta must not fabricate a prior Owner acceptance')
    preservation=str(fields.get('Security neutral / preservation evidence','')).strip()
    invalidation=str(fields.get('Security invalidation evidence','')).strip()
    action=fields.get('Required security action')
    if classification=='MATERIAL_SECURITY_SURFACE_CHANGE':
        if timing not in {'AFTER_VULNERABILITY_CLOSED','AFTER_POST_SECURITY_OWNER_ACCEPTED'}:
            errors.append('material post-closure change requires an after-closure timing')
        if not prior or not current or prior==current:
            errors.append('material security change requires distinct exact prior/current candidates')
        if not categories or not affected or not transitive:
            errors.append('material security change requires explicit categories, affected surfaces, and transitive evidence')
        if preservation!='NOT_APPLICABLE': errors.append('material change cannot claim preservation evidence')
        if not non_generic_evidence(invalidation):
            errors.append('material change requires non-generic invalidation evidence')
        if action!='INVALIDATE_AND_RETURN_TO_AUDIT':
            errors.append('material change must return to audit')
    elif classification in {
        'PROVEN_SECURITY_SURFACE_NEUTRAL','EVIDENCE_EQUIVALENT_PACKAGING_TRANSFORMATION'
    }:
        if categories or affected or transitive:
            errors.append('preserved security closure requires exact NONE surface delta')
        if invalidation!='NOT_APPLICABLE': errors.append('preservation cannot claim invalidation evidence')
        if action!='PRESERVE_EXACT_CLOSURE': errors.append('preservation requires PRESERVE_EXACT_CLOSURE')
        if prior and current:
            if classification=='PROVEN_SECURITY_SURFACE_NEUTRAL' and prior!=current:
                errors.append('security-neutral preservation requires unchanged candidate identity')
            if classification=='EVIDENCE_EQUIVALENT_PACKAGING_TRANSFORMATION' and prior==current:
                errors.append('packaging transformation requires explicit prior/current candidate relationship')
            errors.extend(parse_security_preservation(
                preservation,classification,prior,current
            ))
    return {
        'timing':timing,'classification':classification,'prior':prior,'current':current,
        'categories':categories,'affected':affected,'transitive':set(transitive),
        'closure_reference':closure_reference,'acceptance_reference':acceptance_reference,
    },errors

def impact_analysis_started(fields):
    for field,value in fields.items():
        text=str(value or '').strip()
        if not text: continue
        if IMPACT_UNSTARTED_FIELD_VALUES.get(field)==text: continue
        return True
    return False

def validate_definition_clause_refs(value,label,allow_none=False):
    text=str(value or '').strip()
    if allow_none and text=='NONE': return []
    refs=comma_values(text); errors=[]
    if not refs: return [label+' requires Definition clause references']
    if len(refs)!=len(set(refs)): errors.append(label+' contains duplicate Definition clause references')
    for ref in refs:
        if not DEFINITION_CLAUSE_RE.fullmatch(ref):
            errors.append(label+' contains invalid Definition clause reference '+ref)
    return errors

def parse_narrow_handoff_table(path,expected_columns,label):
    try: lines=path.read_text(encoding='utf-8').splitlines()
    except (OSError,UnicodeError): return [],['cannot read UTF-8 '+label+' table']
    headers=[]; errors=[]; expected=list(expected_columns); known=set(expected)
    for index,line in enumerate(lines):
        if not line.startswith('|'): continue
        cells=[cell.strip() for cell in line.strip().strip('|').split('|')]
        if cells and cells[0]==expected[0]:
            headers.append(index)
            if cells!=expected: errors.append(label+' table header has unknown or missing columns')
        elif expected[0] in cells or len(known.intersection(cells))>=3:
            errors.append('unexpected additional '+label+' row-shaped table/header')
    if len(headers)!=1:
        errors.append('Calabash Definition Handoff requires exactly one '+label+' table')
    if not headers: return [],errors
    start=headers[0]
    if start+1>=len(lines):
        errors.append(label+' table separator missing'); return [],errors
    separators=[cell.strip() for cell in lines[start+1].strip().strip('|').split('|')]
    if not lines[start+1].startswith('|') or len(separators)!=len(expected) or any(not re.fullmatch(r'-+',cell) for cell in separators):
        errors.append(label+' table separator is malformed')
    rows=[]
    for line in lines[start+2:]:
        if not line.strip() or line.startswith('## '): break
        if not line.startswith('|'):
            errors.append(label+' table contains malformed non-pipe row'); continue
        cells=[cell.strip() for cell in line.strip().strip('|').split('|')]
        if len(cells)!=len(expected):
            errors.append(label+' table contains malformed row with wrong column count'); continue
        rows.append(dict(zip(expected,cells)))
    return rows,errors

def validate_closed_handoff_pipe_surface(path,table_headers):
    try: lines=path.read_text(encoding='utf-8').splitlines()
    except (OSError,UnicodeError): return ['cannot read UTF-8 Calabash Definition Handoff']
    allowed=set()
    for expected_columns in table_headers:
        expected=list(expected_columns); starts=[]
        for index,line in enumerate(lines):
            if not line.startswith('|'): continue
            cells=[cell.strip() for cell in line.strip().strip('|').split('|')]
            if cells==expected: starts.append(index)
        if len(starts)==1:
            index=starts[0]
            while index<len(lines) and lines[index].startswith('|'):
                allowed.add(index); index+=1
    return [
        'Calabash Definition Handoff contains pipe-delimited content outside closed Snake/Scorpion tables'
        for index,line in enumerate(lines)
        if line.lstrip().startswith('|') and index not in allowed
    ]

def exact_artifact_hash(path):
    try: return 'sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError: return None

def parse_exact_blocker_ids(value):
    raw=[item.strip() for item in str(value or '').split(',') if item.strip()]
    errors=[]
    if not raw: return set(),['Blocker evidence requires exact blocker IDs']
    if len(raw)!=len(set(raw)): errors.append('Blocker evidence contains duplicate blocker IDs')
    for blocker_id in raw:
        if not stable_id(blocker_id): errors.append('Blocker evidence contains invalid blocker ID '+blocker_id)
    return set(raw),errors

def _calabash_definition_handoff_record(path):
    fields,errors=parse_markdown_fields_strict(path)
    missing=CALABASH_HANDOFF_FIELDS-set(fields); unknown=set(fields)-CALABASH_HANDOFF_FIELDS
    if missing: errors.append('Calabash Definition Handoff missing fields '+', '.join(sorted(missing)))
    if unknown: errors.append('Calabash Definition Handoff has unknown fields '+', '.join(sorted(unknown)))
    exact_values={
        'Artifact role':'CALABASH_DEFINITION_HANDOFF',
        'Definition Baseline kind':'CALABASH_DEFINITION_BASELINE',
        'Calabash standard version':'2.5.0','Baseline status':'FROZEN',
        'Upgrade verdict':'CALABASH_UPGRADE_PASS','Owner change authority':'OWNER',
    }
    for field,expected in exact_values.items():
        if fields.get(field)!=expected: errors.append('Calabash Definition Handoff '+field+' must be '+expected)
    for field in ['Definition Handoff ID','Definition Baseline ID','Upgrade Receipt ID']:
        if not stable_id(fields.get(field)): errors.append('Calabash Definition Handoff '+field+' must be a safe stable ID')
    if not SEMVER_RE.fullmatch(str(fields.get('Definition Baseline semantic version',''))):
        errors.append('Calabash Definition Handoff Definition Baseline semantic version is invalid')
    for field in ['Definition Baseline exact hash','Upgrade Receipt exact hash']:
        if not EXACT_HASH_RE.fullmatch(str(fields.get(field,''))):
            errors.append('Calabash Definition Handoff '+field+' must be lowercase SHA-256')
    errors.extend(validate_definition_clause_refs(
        fields.get('Applicable Definition clause references'),'Calabash Definition Handoff'
    ))
    for field in [
        'Snake review scope','Snake review evidence refs','Scorpion review scope',
        'Scorpion review evidence refs','Meaning-change / invalidation rules reference',
    ]:
        if not semantic_present(fields.get(field)): errors.append('Calabash Definition Handoff '+field+' required')
    for field in ['Snake review scope','Scorpion review scope']:
        scope=comma_values(fields.get(field))
        allowed={'Grandpa','Product Architecture','Ontology','Contract','Policy','Workflow','Action Catalog','Adapter','Eval & Audit'}
        if len(scope)!=len(set(scope)) or not scope or not set(scope).issubset(allowed):
            errors.append('Calabash Definition Handoff '+field+' is invalid')
    snake_status=fields.get('Snake review status')
    scorpion_status=fields.get('Scorpion review status')
    if snake_status not in {'IDENTIFIED','NONE_IDENTIFIED'}: errors.append('Snake review status is invalid')
    if scorpion_status not in {'IDENTIFIED','NONE_IDENTIFIED'}: errors.append('Scorpion review status is invalid')
    snake_columns=['Snake ID','Disposition','Guard / verification reference','Evidence refs','Affected Definition clause refs']
    scorpion_columns=['Scorpion ID','Status','Blocking semantics','Hit condition reference','Evidence refs','Affected Definition clause refs']
    snake_rows,snake_table_errors=parse_narrow_handoff_table(path,snake_columns,'Snake')
    scorpion_rows,scorpion_table_errors=parse_narrow_handoff_table(path,scorpion_columns,'Scorpion')
    errors.extend(snake_table_errors); errors.extend(scorpion_table_errors)
    errors.extend(validate_closed_handoff_pipe_surface(path,[snake_columns,scorpion_columns]))
    blockers=[]
    snake_ids=set()
    for index,row in enumerate(snake_rows):
        prefix=f'Snake row {index+1}'
        snake_id=str(row.get('Snake ID','')).strip()
        if not stable_id(snake_id): errors.append(prefix+' requires a safe stable ID')
        elif snake_id in snake_ids: errors.append('duplicate Snake ID '+snake_id)
        snake_ids.add(snake_id)
        disposition=row.get('Disposition')
        if disposition not in {'OPEN','GUARDED','ACCEPTED_WITH_EVIDENCE','INVALIDATED'}:
            errors.append(prefix+' has invalid disposition')
        for field in ['Guard / verification reference','Evidence refs']:
            if not semantic_present(row.get(field)): errors.append(prefix+' '+field+' required')
        errors.extend(validate_definition_clause_refs(row.get('Affected Definition clause refs'),prefix))
        if disposition=='OPEN' and snake_id: blockers.append(snake_id)
    if snake_status=='IDENTIFIED' and not snake_rows: errors.append('IDENTIFIED Snake review requires records')
    if snake_status=='NONE_IDENTIFIED' and snake_rows: errors.append('NONE_IDENTIFIED Snake review must not contain records')
    scorpion_ids=set()
    for index,row in enumerate(scorpion_rows):
        prefix=f'Scorpion row {index+1}'
        scorpion_id=str(row.get('Scorpion ID','')).strip()
        if not stable_id(scorpion_id): errors.append(prefix+' requires a safe stable ID')
        elif scorpion_id in scorpion_ids: errors.append('duplicate Scorpion ID '+scorpion_id)
        scorpion_ids.add(scorpion_id)
        status=row.get('Status')
        if status not in {'CLEAR','HIT','INVALIDATED'}: errors.append(prefix+' has invalid status')
        if row.get('Blocking semantics')!='HARD_BLOCK': errors.append(prefix+' must use HARD_BLOCK')
        for field in ['Hit condition reference','Evidence refs']:
            if not semantic_present(row.get(field)): errors.append(prefix+' '+field+' required')
        errors.extend(validate_definition_clause_refs(row.get('Affected Definition clause refs'),prefix))
        if status=='HIT' and scorpion_id: blockers.append(scorpion_id)
    if scorpion_status=='IDENTIFIED' and not scorpion_rows: errors.append('IDENTIFIED Scorpion review requires records')
    if scorpion_status=='NONE_IDENTIFIED' and scorpion_rows: errors.append('NONE_IDENTIFIED Scorpion review must not contain records')
    result=fields.get('Handoff result')
    if result not in {'PASS','BLOCKED'}: errors.append('Calabash Definition Handoff result must be PASS or BLOCKED')
    if result=='PASS' and blockers: errors.append('Calabash Definition Handoff PASS cannot override OPEN/HIT evidence')
    return fields,blockers,errors

def validate_calabash_definition_handoff(path,require_pass=False):
    fields,blockers,errors=_calabash_definition_handoff_record(path)
    if require_pass:
        if fields.get('Handoff result')!='PASS': errors.append('Calabash Definition Handoff must PASS')
        if blockers: errors.append('Calabash Definition Handoff has blocking Snake/Scorpion evidence: '+', '.join(blockers))
    return errors

def validate_impact_analysis(path):
    fields,errors=parse_markdown_fields_strict(path)
    missing=IMPACT_REQUIRED_FIELDS-set(fields); unknown=set(fields)-IMPACT_ALLOWED_FIELDS
    if missing: errors.append('Impact Analysis missing fields '+', '.join(sorted(missing)))
    if unknown: errors.append('Impact Analysis has unknown fields '+', '.join(sorted(unknown)))
    if fields.get('Artifact role')!='IMPACT_ANALYSIS': errors.append('Impact Analysis artifact role is invalid')
    identity=str(fields.get('Analysis ID / version','')).split('/')
    if len(identity)!=2 or not stable_id(identity[0].strip()) or not SEMVER_RE.fullmatch(identity[1].strip()):
        errors.append('Impact Analysis ID / version is invalid')
    for field in ['Trigger / proposed change','Calling phase contract / authority','Snake / Scorpion applicability and effect references']:
        if not semantic_present(fields.get(field)): errors.append('Impact Analysis '+field+' required')
    classification=fields.get('Meaning impact classification')
    if classification not in {'MEANING_CHANGING','MEANING_NEUTRAL'}:
        errors.append('Meaning impact classification is invalid')
    if fields.get('Impact result') not in {'PASS','BLOCKED'}: errors.append('Impact result must be PASS or BLOCKED')
    if classification=='MEANING_CHANGING':
        if not exact_id_hash(fields.get('Definition Baseline ID / exact hash')):
            errors.append('meaning-changing work requires exact Definition Baseline identity')
        errors.extend(validate_definition_clause_refs(fields.get('Affected Definition clause references'),'Impact Analysis'))
        if fields.get('Definition invalidation effect')!='INVALIDATES': errors.append('meaning-changing work must record INVALIDATES')
        if fields.get('Governed Calabash update route / Owner authority')!='CALABASH_UPDATE / OWNER':
            errors.append('meaning-changing work requires governed Calabash update route and Owner authority')
    if classification=='MEANING_NEUTRAL':
        if fields.get('Definition Baseline ID / exact hash')!='NONE' or fields.get('Affected Definition clause references')!='NONE':
            errors.append('meaning-neutral work must not fabricate a Definition Baseline')
        if fields.get('Definition invalidation effect')!='NO_DEFINITION_INVALIDATION':
            errors.append('meaning-neutral work must record no Definition invalidation')
        if fields.get('Governed Calabash update route / Owner authority')!='NOT_APPLICABLE':
            errors.append('meaning-neutral work must not fabricate a Calabash update route')
        if not semantic_present(fields.get('Neutral rationale / evidence')):
            errors.append('meaning-neutral work requires evidence-backed neutral rationale')
    _,security_errors=validate_security_impact_fields(fields)
    errors.extend(security_errors)
    return errors

def _safe_lccoding_evidence(path,reference):
    lc=next((parent for parent in path.parents if parent.name=='.lccoding'),None)
    if lc is None: return None,None
    text=str(reference or '').strip()
    if not text or '\\' in text or '://' in text or Path(text).is_absolute(): return lc,None
    resolved=(lc/text).resolve()
    try: contained=resolved.is_relative_to(lc.resolve())
    except AttributeError: contained=str(resolved).startswith(str(lc.resolve())+str(Path('/')))
    return lc,resolved if contained and resolved.is_file() else None

def resolve_security_reference(lc,reference):
    _,resolved=_safe_lccoding_evidence(lc/'status.json',reference)
    return resolved

def validate_post_security_receipt(
    path,expected_candidate,expected_closure,expected_closure_data=None
):
    fields,errors=parse_markdown_fields_strict(path)
    missing=POST_SECURITY_RECEIPT_FIELDS-set(fields); unknown=set(fields)-POST_SECURITY_RECEIPT_FIELDS
    if missing: errors.append('Post-Security Owner Acceptance missing fields '+', '.join(sorted(missing)))
    if unknown: errors.append('Post-Security Owner Acceptance has unknown fields '+', '.join(sorted(unknown)))
    if errors: return fields,errors
    if fields.get('Schema version')!='2.7.0': errors.append('Post-Security Owner Acceptance schema must be 2.7.0')
    if fields.get('Artifact role')!='POST_SECURITY_OWNER_ACCEPTANCE_RECEIPT':
        errors.append('Post-Security Owner Acceptance artifact role is invalid')
    if not non_generic_evidence(fields.get('Acceptance ID')):
        errors.append('Post-Security Owner Acceptance requires a safe Acceptance ID')
    candidate=exact_security_id_hash(fields.get('Candidate ID / exact hash'))
    closure_candidate=exact_security_id_hash(fields.get('Vulnerability Closure candidate ID / exact hash'))
    if candidate!=expected_candidate:
        errors.append('Post-Security Owner Acceptance candidate identity mismatch')
    if closure_candidate!=expected_candidate:
        errors.append('Post-Security Owner Acceptance closure candidate identity mismatch')
    closure_reference,reference_errors=parse_id_reference(
        fields.get('Vulnerability Closure Receipt ID / reference'),
        'Post-Security Vulnerability Closure Receipt'
    )
    errors.extend(reference_errors)
    if closure_reference!=expected_closure:
        errors.append('Post-Security Owner Acceptance closure receipt mismatch')
    covered,covered_errors=parse_security_id_set(
        fields.get('Covered remediation surface IDs'),'Covered remediation surface IDs',
        allow_none=True
    )
    changed,changed_errors=parse_security_id_set(
        fields.get('Changed remediation surface IDs'),'Changed remediation surface IDs',allow_none=True
    )
    errors.extend(covered_errors); errors.extend(changed_errors)
    if not changed.issubset(covered):
        errors.append('changed remediation surfaces must be covered')
    closure_data=expected_closure_data if isinstance(expected_closure_data,dict) else {}
    required_surfaces=set(closure_data.get('required_surface_ids',[]))
    if not required_surfaces or not covered.issubset(required_surfaces):
        errors.append('Post-Security remediation surfaces must stay inside Vulnerability Closure coverage')
    owner_records,owner_errors=parse_bound_security_records(
        fields.get('Reused Loop Owner Acceptance Receipt IDs'),
        'Reused Loop Owner Acceptance Receipt IDs'
    )
    remediation_records,remediation_errors=parse_bound_security_records(
        fields.get('Security Remediation Run IDs'),'Security Remediation Run IDs',
        with_evidence=True,allow_none=True
    )
    critical_records,critical_errors=parse_bound_security_records(
        fields.get('Critical smoke / delta evidence'),'Critical smoke / delta evidence'
    )
    errors.extend(owner_errors); errors.extend(remediation_errors); errors.extend(critical_errors)
    expected_owners={}
    for record in closure_data.get('pre_audit_loop_owner_acceptance_receipts',[]):
        if isinstance(record,dict):
            expected_owners[record.get('evidence_id')]={
                'candidate':(record.get('candidate_id'),record.get('candidate_hash')),
                'surfaces':set(record.get('surface_ids',[])),'evidence_id':None,
            }
    if owner_records!=expected_owners:
        errors.append('reused Loop Owner acceptance records do not exactly match Vulnerability Closure evidence')
    expected_remediation={}; remediated_surfaces=set()
    for record in closure_data.get('remediation_runs',[]):
        if isinstance(record,dict):
            record_surfaces=set(record.get('surface_ids',[])); remediated_surfaces.update(record_surfaces)
            expected_remediation[record.get('run_id')]={
                'candidate':(record.get('candidate_id'),record.get('candidate_hash')),
                'surfaces':record_surfaces,'evidence_id':record.get('evidence_id'),
            }
    if remediation_records!=expected_remediation:
        errors.append('security remediation Run records do not exactly match Vulnerability Closure evidence')
    if changed!=remediated_surfaces:
        errors.append('changed remediation surfaces must exactly equal Vulnerability Closure remediation surfaces')
    focused_surfaces=set(remediated_surfaces)
    for record in closure_data.get('affected_receipts',[]):
        if isinstance(record,dict): focused_surfaces.update(record.get('surface_ids',[]))
    if covered!=focused_surfaces:
        errors.append('Post-Security covered surfaces must exactly equal remediation-affected focused scope')
    known_critical=closure_candidate_evidence(closure_data); critical_surfaces=set()
    for evidence_id,record in critical_records.items():
        if known_critical.get(evidence_id)!=record:
            errors.append('critical smoke/delta evidence is not exact candidate-bound Vulnerability Closure evidence')
        critical_surfaces.update(record.get('surfaces',set()))
    if not critical_records or not focused_surfaces.issubset(critical_surfaces):
        errors.append('critical smoke/delta evidence must cover every remediation-affected focused surface')
    if fields.get('Owner result') not in {
        'POST_SECURITY_OWNER_ACCEPTED','POST_SECURITY_PRODUCT_REWORK',
        'POST_SECURITY_OWNER_DEFERRED',
    }:
        errors.append('Post-Security Owner Acceptance result is invalid')
    supersession=fields.get('Supersession status')
    if supersession!='CURRENT':
        errors.append('referenced Post-Security Owner Acceptance receipt must remain CURRENT immutable evidence')
    superseded_reference=fields.get('Superseded by Acceptance ID / reference')
    if supersession=='CURRENT' and superseded_reference!='NOT_APPLICABLE':
        errors.append('current Post-Security acceptance cannot claim supersession')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z',fields.get('Accepted at','')):
        errors.append('Post-Security Owner Acceptance requires an exact accepted-at timestamp')
    return fields,errors

def _expected_agent_security_binding(lc,status):
    fields=VULNERABILITY_CONTRACT['agent_security_binding_fields']
    not_applicable={field:'NOT_APPLICABLE' for field in fields}
    if not isinstance(status,dict) or status.get('status_schema_version')!='2.8.0':
        return not_applicable,[]
    agent_slice=status.get('agent_slice_integration')
    if not isinstance(agent_slice,dict) or agent_slice.get('state')!='AGENT_SLICES_ACCEPTED':
        return not_applicable,[]
    errors=[]; lc=Path(lc)
    config_path=lc/AGENT_CONFIGURATION_BASELINE_NAME
    adapter_path=lc/RUNTIME_ADAPTER_ATTESTATION_NAME
    for label,path,expected_hash in (
        ('Agent Configuration Baseline',config_path,agent_slice.get('configuration_baseline_hash')),
        ('Runtime Adapter Attestation',adapter_path,agent_slice.get('runtime_adapter_attestation_hash')),
    ):
        if path.is_symlink() or not path.is_file(): errors.append(label+' is required for Agent security binding')
        elif _agent_file_hash(path)!=expected_hash: errors.append(label+' hash disagrees with authoritative Agent Slice status')
    if errors: return None,errors
    try:
        configuration=_AGENT_NATIVE.strict_json(config_path)
        attestation=_AGENT_NATIVE.strict_json(adapter_path)
    except (OSError,UnicodeError,ValueError) as error:
        return None,['Agent security identity evidence is not strict UTF-8: '+str(error)]
    operations=configuration.get('operations_agent',{})
    product=configuration.get('product_agent',{})
    runtime=attestation.get('runtime_adapter',{})
    binding={
        'state':'BOUND','candidate_id':agent_slice.get('candidate_id'),
        'candidate_hash':agent_slice.get('candidate_hash'),
        'configuration_baseline_id':agent_slice.get('configuration_baseline_id'),
        'configuration_baseline_hash':agent_slice.get('configuration_baseline_hash'),
        'production_topology_id':agent_slice.get('production_topology_id'),
        'production_topology_hash':agent_slice.get('production_topology_hash'),
        'runtime_adapter_attestation_id':agent_slice.get('runtime_adapter_attestation_id'),
        'runtime_adapter_attestation_hash':agent_slice.get('runtime_adapter_attestation_hash'),
        'runtime_adapter_id':agent_slice.get('runtime_adapter_id'),
        'runtime_adapter_version':agent_slice.get('runtime_adapter_version'),
        'runtime_adapter_digest':runtime.get('adapter_digest'),
        'product_agent_applicability':agent_slice.get('product_agent_applicability'),
        'product_agent_id':(
            'NOT_APPLICABLE' if agent_slice.get('product_agent_applicability')=='NOT_APPLICABLE'
            else product.get('agent_id')
        ),
        'operations_agent_id':operations.get('agent_id'),'identity_status':'CURRENT',
    }
    return binding,errors

def load_vulnerability_reference(
    lc,reference,expected_id,expected_candidate,expected_agent_binding=None
):
    errors=[]
    if not expected_candidate or not exact_security_identity(*expected_candidate):
        return None,['Vulnerability Closure expected candidate identity is invalid']
    path=resolve_security_reference(lc,reference)
    if path is None: return None,['Vulnerability Closure reference is missing or escapes .lccoding']
    try: data=strict_vulnerability_json(path)
    except (OSError,UnicodeError,ValueError) as error:
        return None,['Vulnerability Closure receipt is unreadable or not strict JSON: '+str(error)]
    if data.get('closure_id')!=expected_id:
        errors.append('Vulnerability Closure receipt ID mismatch')
    required=data.get('required_surface_ids') if isinstance(data.get('required_surface_ids'),list) else None
    errors.extend(validate_vulnerability_receipt(
        data,VULNERABILITY_CONTRACT,expected_candidate[0],expected_candidate[1],required,
        expected_agent_binding
    ))
    return data,errors

def load_post_security_reference(
    lc,reference,expected_id,expected_candidate,expected_closure,expected_closure_data=None
):
    if not expected_candidate or not exact_security_identity(*expected_candidate):
        return None,['Post-Security expected candidate identity is invalid']
    path=resolve_security_reference(lc,reference)
    if path is None: return None,['Post-Security Owner Acceptance reference is missing or escapes .lccoding']
    fields,errors=validate_post_security_receipt(
        path,expected_candidate,expected_closure,expected_closure_data
    )
    if fields.get('Acceptance ID')!=expected_id:
        errors.append('Post-Security Owner Acceptance ID mismatch')
    if fields.get('Owner result')!='POST_SECURITY_OWNER_ACCEPTED':
        errors.append('prior/current Post-Security receipt is not Owner accepted')
    return fields,errors

def _status_reference_matches(record,id_field,reference_field,expected,label):
    if expected is None:
        if record.get(id_field)!='NOT_APPLICABLE' or record.get(reference_field)!='NOT_APPLICABLE':
            return [label+' must be NOT_APPLICABLE']
        return []
    if (record.get(id_field),record.get(reference_field))!=expected:
        return [label+' identity/reference mismatch']
    return []

def _validate_status_pointer_set(lc,status,expected):
    pointers=status.get('evidence_pointers')
    if not isinstance(pointers,list) or len(pointers)!=len(set(pointers)):
        return ['security evidence_pointers must be one unique closed list']
    if set(pointers)!=set(expected):
        return ['security evidence_pointers do not exactly preserve current/superseded evidence']
    errors=[]
    for pointer in pointers:
        if not isinstance(pointer,str) or resolve_security_reference(lc,pointer) is None:
            errors.append('security evidence pointer is missing, generic, or outside .lccoding')
    return errors

def validate_security_invalidation(lc,status):
    lc=Path(lc); errors=validate_security_status_shape(status)
    closure=status.get('vulnerability_closure'); acceptance=status.get('post_security_owner_acceptance')
    strict=isinstance(closure,dict) or isinstance(acceptance,dict)
    impact_path=lc/'IMPACT-ANALYSIS.md'; impact_fields={}; impact_record=None
    required_security_delta=bool(str(status.get('last_material_change','')).strip())
    if impact_path.exists():
        impact_fields,impact_parse_errors=parse_markdown_fields_strict(impact_path)
        errors.extend(impact_parse_errors)
        started_impact=impact_analysis_started(impact_fields)
        security_decision_current=(
            isinstance(closure,dict) and closure.get('state')!='PENDING'
        ) or (
            isinstance(acceptance,dict) and acceptance.get('state')!='PENDING'
        )
        security_delta_required=(
            required_security_delta or (started_impact and security_decision_current)
        )
        if started_impact or required_security_delta:
            errors.extend(validate_impact_analysis(impact_path))
        if security_delta_required:
            impact_record,impact_errors=validate_security_impact_fields(
                impact_fields,required=security_delta_required
            )
            errors.extend(impact_errors)
    elif required_security_delta:
        errors.append('last_material_change requires a contained Impact Analysis security delta')
    if not strict:
        if impact_record is not None:
            errors.append('2.7 security delta requires one structured authoritative status')
        return errors
    if errors and (not isinstance(closure,dict) or not isinstance(acceptance,dict)):
        return errors
    closure_state=closure.get('state'); acceptance_state=acceptance.get('state')
    if closure_state=='PENDING' and acceptance_state=='PENDING':
        if impact_record is not None and impact_record.get('timing')!='BEFORE_SECURITY_CLOSURE':
            errors.append('post-closure security delta cannot remain a pending bootstrap')
        return errors
    canonical=status.get('canonical_candidate',{})
    current=(canonical.get('candidate_id'),canonical.get('candidate_hash'))
    expected_agent_binding,agent_binding_errors=_expected_agent_security_binding(lc,status)
    errors.extend(agent_binding_errors)
    last_change=str(status.get('last_material_change','')).strip()
    if impact_record is None:
        if last_change:
            errors.append('current security state with a material-change pointer requires a closed security Impact Analysis')
        if closure_state=='INVALID' or acceptance_state=='INVALID':
            errors.append('invalid security state requires exact Impact Analysis evidence')
            return errors
        closure_reference=(closure.get('current_receipt_id'),closure.get('current_receipt_reference'))
        closure_data,closure_errors=load_vulnerability_reference(
            lc,closure_reference[1],closure_reference[0],current,expected_agent_binding
        )
        errors.extend(closure_errors)
        if acceptance_state=='PENDING':
            errors.extend(_validate_status_pointer_set(
                lc,status,[closure_reference[1]]
            ))
            return errors
        post_reference=(acceptance.get('current_acceptance_id'),acceptance.get('current_acceptance_reference'))
        _,post_errors=load_post_security_reference(
            lc,post_reference[1],post_reference[0],current,closure_reference,
            closure_data
        )
        errors.extend(post_errors)
        errors.extend(_status_reference_matches(
            acceptance,'vulnerability_closure_receipt_id',
            'vulnerability_closure_receipt_reference',closure_reference,
            'current Post-Security closure receipt'
        ))
        errors.extend(_validate_status_pointer_set(
            lc,status,[closure_reference[1],post_reference[1]]
        ))
        return errors
    analysis_identity=str(impact_fields.get('Analysis ID / version','')).split(' / ')[0]
    expected_change=(analysis_identity,'IMPACT-ANALYSIS.md')
    parsed_change,change_errors=parse_id_reference(last_change,'last_material_change')
    errors.extend(change_errors)
    if parsed_change!=expected_change:
        errors.append('last_material_change must bind the exact current Impact Analysis')
    prior=impact_record.get('prior'); impact_current=impact_record.get('current')
    if impact_current!=current:
        errors.append('security Impact current candidate disagrees with canonical candidate')
    prior_closure=impact_record.get('closure_reference')
    prior_acceptance=impact_record.get('acceptance_reference')
    prior_closure_data=None
    if prior_closure:
        prior_closure_data,closure_errors=load_vulnerability_reference(
            lc,prior_closure[1],prior_closure[0],prior
        )
        errors.extend(closure_errors)
    if prior_acceptance:
        _,post_errors=load_post_security_reference(
            lc,prior_acceptance[1],prior_acceptance[0],prior,prior_closure,
            prior_closure_data
        )
        errors.extend(post_errors)
    classification=impact_record.get('classification')
    expected_pointers=['IMPACT-ANALYSIS.md',prior_closure[1] if prior_closure else '']
    if prior_acceptance: expected_pointers.append(prior_acceptance[1])
    expected_pointers=[pointer for pointer in expected_pointers if pointer]
    errors.extend(_validate_status_pointer_set(lc,status,expected_pointers))
    if classification=='MATERIAL_SECURITY_SURFACE_CHANGE':
        if (
            closure_state!='INVALID' or acceptance_state!='INVALID'
            or status.get('phase_gates',{}).get('DELIVERY_READY')!='INVALID'
        ):
            errors.append(
                'material security change must invalidate closure, Post-Security acceptance, and DELIVERY_READY'
            )
        errors.extend(_status_reference_matches(
            closure,'superseded_receipt_id','superseded_receipt_reference',prior_closure,
            'superseded Vulnerability Closure receipt'
        ))
        if (closure.get('superseded_candidate_id'),closure.get('superseded_candidate_hash'))!=prior:
            errors.append('superseded Vulnerability Closure candidate identity mismatch')
        errors.extend(_status_reference_matches(
            acceptance,'superseded_acceptance_id','superseded_acceptance_reference',
            prior_acceptance,'superseded Post-Security acceptance'
        ))
        if prior_acceptance is None:
            if not _not_applicable_record(
                acceptance,{'superseded_candidate_id','superseded_candidate_hash'}
            ): errors.append('pre-acceptance invalidation must not fabricate a superseded Owner candidate')
        elif (acceptance.get('superseded_candidate_id'),acceptance.get('superseded_candidate_hash'))!=prior:
            errors.append('superseded Post-Security candidate identity mismatch')
        if status.get('blockers')!=['SECURITY_EVIDENCE_INVALIDATED:'+analysis_identity]:
            errors.append('material security invalidation requires one exact blocker')
        if status.get('next_action')!=(
            'FRESH_INDEPENDENT_SECURITY_REAUDIT_THEN_NEW_CLOSURE_'
            'THEN_FOCUSED_POST_SECURITY_OWNER_ACCEPTANCE'
        ):
            errors.append('material security invalidation requires fresh re-audit, closure, and focused Owner acceptance')
    elif classification in {
        'PROVEN_SECURITY_SURFACE_NEUTRAL','EVIDENCE_EQUIVALENT_PACKAGING_TRANSFORMATION'
    }:
        if impact_fields.get('Impact result')!='PASS':
            errors.append('security preservation requires Impact result PASS')
        if closure_state!='VULNERABILITY_CLOSED' or acceptance_state!='POST_SECURITY_OWNER_ACCEPTED':
            errors.append('explicit preservation requires current closed/accepted status')
        if status.get('phase_gates',{}).get('DELIVERY_READY')=='INVALID':
            errors.append('explicitly preserved closure cannot claim an invalid Delivery boundary')
        if status.get('blockers') not in ([],None):
            errors.append('explicit preservation cannot retain a security invalidation blocker')
        if status.get('next_action')!='PRESERVE_EXACT_SECURITY_CLOSURE':
            errors.append('explicit preservation requires exact next action evidence')
        current_closure=(closure.get('current_receipt_id'),closure.get('current_receipt_reference'))
        current_acceptance=(acceptance.get('current_acceptance_id'),acceptance.get('current_acceptance_reference'))
        if current_closure!=prior_closure:
            errors.append('preserved status must cite the exact prior Vulnerability Closure')
        if current_acceptance!=prior_acceptance:
            errors.append('preserved status must cite the exact prior Post-Security acceptance')
        if isinstance(prior_closure_data,dict) and prior_closure_data.get('agent_security_binding')!=expected_agent_binding:
            errors.append('preserved Agent security binding disagrees with authoritative Agent Slice status')
        errors.extend(_status_reference_matches(
            acceptance,'vulnerability_closure_receipt_id',
            'vulnerability_closure_receipt_reference',prior_closure,
            'preserved Post-Security closure receipt'
        ))
    return errors

def validate_product_definition_basis(lc,handoff_fields):
    errors=[]; gate=lc/'CALABASH-UPGRADE-GATE.md'
    if not gate.is_file(): return ['Product Baseline COMPLETE requires Calabash Definition Handoff']
    errors.extend(validate_calabash_definition_handoff(gate,require_pass=True))
    fields,_,_= _calabash_definition_handoff_record(gate)
    citation=exact_id_hash(handoff_fields.get('Calabash Definition Handoff ID / exact hash'))
    expected=(fields.get('Definition Handoff ID'),exact_artifact_hash(gate))
    if not citation or citation!=expected: errors.append('Product Baseline Calabash Definition Handoff identity/hash mismatch')
    if handoff_fields.get('Calabash Definition Handoff result')!='PASS':
        errors.append('Product Baseline requires Calabash Definition Handoff PASS')
    product_identity=str(handoff_fields.get('Baseline ID / version / hash','')).strip()
    if product_identity.startswith('CALABASH_DEFINITION_BASELINE'):
        errors.append('Product Baseline identity cannot be a Definition Baseline')
    return errors

def validate_run_definition_basis(path,fields):
    errors=[]
    classification=fields.get('Meaning impact classification')
    if classification not in {'MEANING_CHANGING','MEANING_NEUTRAL'}:
        return ['Run start Meaning impact classification is invalid']
    lc,impact_path=_safe_lccoding_evidence(path,fields.get('Definition basis / neutral Impact Analysis reference'))
    if not impact_path: return ['Run start requires a contained Impact Analysis reference']
    impact_fields=parse_markdown_fields(impact_path)
    errors.extend(validate_impact_analysis(impact_path))
    if impact_fields.get('Meaning impact classification')!=classification:
        errors.append('Run start meaning classification disagrees with Impact Analysis')
    _,disposition_path=_safe_lccoding_evidence(path,fields.get('Applicable Snake / Scorpion disposition evidence reference'))
    if not disposition_path: errors.append('Run start requires contained Snake/Scorpion disposition evidence')
    elif disposition_path.name!='CALABASH-UPGRADE-GATE.md': errors.append('Run start disposition evidence must cite the Definition Handoff')
    handoff_fields={}; blockers=[]
    if disposition_path and disposition_path.name=='CALABASH-UPGRADE-GATE.md':
        handoff_fields,blockers,handoff_errors=_calabash_definition_handoff_record(disposition_path)
        errors.extend(handoff_errors)
    if classification=='MEANING_CHANGING' and disposition_path:
        impact_identity=exact_id_hash(impact_fields.get('Definition Baseline ID / exact hash'))
        expected=(handoff_fields.get('Definition Baseline ID'),handoff_fields.get('Definition Baseline exact hash'))
        if impact_identity!=expected: errors.append('meaning-changing Run Definition Baseline disagrees with current handoff')
    if classification=='MEANING_NEUTRAL' and impact_fields.get('Definition Baseline ID / exact hash')!='NONE':
        errors.append('meaning-neutral Run fabricates Definition basis')
    if disposition_path:
        applicable_blockers=set(blockers)
        if impact_fields.get('Impact result')=='BLOCKED':
            analysis_parts=[part.strip() for part in str(impact_fields.get('Analysis ID / version','')).split('/')]
            if analysis_parts and stable_id(analysis_parts[0]): applicable_blockers.add(analysis_parts[0])
        if fields.get('Readiness result')=='READY':
            if fields.get('Blocker evidence')!='NONE': errors.append('READY Run requires Blocker evidence NONE')
            if impact_fields.get('Impact result')!='PASS': errors.append('READY Run requires Impact result PASS')
            if handoff_fields.get('Handoff result')!='PASS' or blockers:
                errors.append('READY Run is blocked by applicable Definition evidence')
        elif fields.get('Readiness result')=='BLOCKED':
            if applicable_blockers:
                blocker_ids,blocker_errors=parse_exact_blocker_ids(fields.get('Blocker evidence'))
                errors.extend(blocker_errors)
                if blocker_ids!=applicable_blockers:
                    errors.append('BLOCKED Run blocker IDs must exactly match applicable Definition blockers')
        else: errors.append('Run start readiness is invalid for Definition basis')
    return errors

def validate_execution_method_registry(manifest,lock,manifest_path):
    errors=[]; eligible={}; candidates={}; collection=manifest.get('execution_methods')
    if collection is None:
        return errors,eligible,False
    if not isinstance(collection,list):
        return ['Canonical Manifest execution_methods must be a list'],eligible,True
    ids=set(); duplicate_ids=set()
    for index,record in enumerate(collection):
        prefix=f'execution method record {index+1}'
        if not isinstance(record,dict):
            errors.append(prefix+' must be an object'); continue
        record_valid=True
        def reject(message):
            nonlocal record_valid
            record_valid=False; errors.append(message)
        unknown=set(record)-EXECUTION_METHOD_KEYS
        missing=EXECUTION_METHOD_KEYS-set(record)
        if unknown: reject(prefix+' has unknown fields '+', '.join(sorted(unknown)))
        if missing: reject(prefix+' missing fields '+', '.join(sorted(missing)))
        method_id=str(record.get('method_id','')).strip()
        if not stable_id(method_id): reject(prefix+' method_id must be a safe stable ID')
        elif method_id in ids:
            duplicate_ids.add(method_id); reject('duplicate execution method ID '+method_id)
        ids.add(method_id)
        if not SEMVER_RE.fullmatch(str(record.get('version',''))): reject(prefix+' version must be semantic')
        if not EXACT_HASH_RE.fullmatch(str(record.get('exact_hash',''))): reject(prefix+' exact_hash must be lowercase SHA-256')
        for field in ['canonical_contract_reference','run_evidence_mapping','owner_acceptance_mapping']:
            if not semantic_present(record.get(field)): reject(prefix+' '+field+' required')
        if record.get('run_evidence_mapping')!='RUN_START_CONTRACT -> D0-D3':
            reject(prefix+' run evidence mapping must bind Run start to D0-D3')
        if record.get('owner_acceptance_mapping')!='LOOP_OWNER_ACCEPTANCE_RECEIPT':
            reject(prefix+' Owner acceptance mapping is invalid')
        if record.get('required_control_binding')!='LCCODING_LOOP_CONTROL':
            reject(prefix+' must bind LCCODING_LOOP_CONTROL')
        compatibility=record.get('compatibility_result')
        if compatibility not in {'PASS','BLOCKED'}: reject(prefix+' compatibility result must be PASS or BLOCKED')
        if record_valid and compatibility=='PASS': candidates[method_id]=record
    for method_id in duplicate_ids: candidates.pop(method_id,None)
    if not collection: return errors,eligible,True
    lock_valid=True
    def reject_lock(message):
        nonlocal lock_valid
        lock_valid=False; errors.append(message)
    if lock.get('status')!='VALID': reject_lock('Interpretation Lock status must be VALID')
    if lock.get('knowledge_test')!='PASS': reject_lock('Interpretation Lock knowledge test must PASS')
    if lock.get('execution_test')!='PASS': reject_lock('Interpretation Lock execution test must PASS')
    if lock.get('compatibility')!='PASS': reject_lock('Interpretation Lock compatibility must PASS')
    if lock.get('manifest_reference')!='CANONICAL-MANIFEST.json':
        reject_lock('Interpretation Lock must reference CANONICAL-MANIFEST.json')
    try: actual_hash=exact_manifest_hash(manifest_path)
    except OSError: actual_hash=None
    if lock.get('manifest_hash')!=actual_hash:
        reject_lock('Interpretation Lock manifest hash mismatch')
    validated=lock.get('validated_execution_method_ids')
    if not isinstance(validated,list) or any(not stable_id(value) for value in validated):
        reject_lock('Interpretation Lock validated method IDs must be a list of stable IDs')
    elif len(validated)!=len(set(validated)) or set(validated)!=set(candidates):
        reject_lock('Interpretation Lock validated method IDs disagree with eligible Manifest records')
    if lock_valid: eligible=candidates
    return errors,eligible,True

def canonical_run_start_hash(text):
    lines=text.splitlines(keepends=True); matches=0; canonical=[]
    for line in lines:
        ending='\r\n' if line.endswith('\r\n') else ('\n' if line.endswith('\n') else '')
        body=line[:-len(ending)] if ending else line
        if body.startswith('- Start Contract SHA-256:'):
            matches+=1; body='- Start Contract SHA-256:'
        canonical.append(body+ending)
    if matches!=1: return None
    return 'sha256:'+hashlib.sha256(''.join(canonical).encode('utf-8')).hexdigest()

def validate_run_start_record(path,fields,eligible_methods,manifest,lock,expected_status_schema=None):
    errors=[]; prefix='Run start '+str(path)
    missing=START_REQUIRED_FIELDS-set(fields); unknown=set(fields)-START_ALLOWED_FIELDS
    if missing: errors.append(prefix+' missing fields '+', '.join(sorted(missing)))
    if unknown: errors.append(prefix+' has unknown fields '+', '.join(sorted(unknown)))
    if fields.get('Artifact role')!='RUN_START_CONTRACT': errors.append(prefix+' role must be RUN_START_CONTRACT')
    for field in START_REQUIRED_FIELDS-{'Artifact role','Start Contract SHA-256','Readiness result','Blocker evidence'}:
        if field in fields and not semantic_present(fields.get(field)):
            errors.append(prefix+' missing mandatory start fact '+field)
    for field in ['Start Contract ID','Run ID']:
        if field in fields and not stable_id(fields.get(field)):
            errors.append(prefix+' '+field+' must be a safe stable ID')
    schema=fields.get('Status schema version')
    phase_order=PHASE_IDS_BY_SCHEMA.get(schema)
    if phase_order is None: errors.append(prefix+' has unsupported Status schema version')
    if expected_status_schema is not None and schema!=expected_status_schema:
        errors.append(prefix+' Status schema version disagrees with authoritative status')
    phase=fields.get('LCCoding phase scope')
    if not phase_order or phase not in phase_order: errors.append(prefix+' has invalid phase for Status schema version')
    phase3=phase_order[2] if phase_order else None
    expected_phase3_fields=(PHASE3_START_FIELDS if schema=='2.8.0' else LEGACY_PHASE3_START_FIELDS)
    all_phase3_fields=PHASE3_START_FIELDS|LEGACY_PHASE3_START_FIELDS
    phase3_fields=all_phase3_fields&set(fields)
    if phase==phase3:
        if phase3_fields!=expected_phase3_fields or any(not present(fields.get(field)) for field in expected_phase3_fields):
            errors.append(prefix+' Phase-3 integration identities missing')
    elif phase3_fields: errors.append(prefix+' fabricates Phase-3 identities outside schema-selected Phase 3')
    readiness=fields.get('Readiness result')
    if readiness not in {'READY','BLOCKED'}: errors.append(prefix+' readiness must be READY or BLOCKED')
    if readiness=='READY' and fields.get('Blocker evidence')!='NONE': errors.append(prefix+' READY requires blocker NONE')
    if readiness=='BLOCKED' and not present(fields.get('Blocker evidence')): errors.append(prefix+' BLOCKED requires evidence')
    try: text=path.read_bytes().decode('utf-8')
    except (OSError,UnicodeError): text=''
    actual_hash=canonical_run_start_hash(text)
    if not actual_hash or fields.get('Start Contract SHA-256')!=actual_hash:
        errors.append(prefix+' Start Contract SHA-256 mismatch')
    method_id=fields.get('Selected execution method ID')
    method=eligible_methods.get(method_id)
    if method:
        comparisons={
            'Selected execution method version':'version',
            'Selected execution method exact hash':'exact_hash',
            'Selected execution method canonical interface / contract reference':'canonical_contract_reference',
        }
        for start_field,manifest_field in comparisons.items():
            if fields.get(start_field)!=method.get(manifest_field): errors.append(prefix+' method identity mismatch: '+start_field)
    elif str(method_id or '').upper() in LEGACY_METHOD_INTERFACES:
        legacy_id=str(method_id).upper(); legacy=manifest.get(legacy_id.lower(),{})
        if not isinstance(legacy,dict) or not SEMVER_RE.fullmatch(str(legacy.get('version',''))) or not EXACT_HASH_RE.fullmatch(str(legacy.get('hash',''))):
            errors.append(prefix+' selected legacy method identity is incomplete')
        else:
            if fields.get('Selected execution method version')!=legacy.get('version') or fields.get('Selected execution method exact hash')!=legacy.get('hash') or fields.get('Selected execution method canonical interface / contract reference')!=LEGACY_METHOD_INTERFACES[legacy_id]:
                errors.append(prefix+' selected legacy method does not match dual-read adapter')
    else: errors.append(prefix+' selected method is not registered and eligible')
    errors.extend(validate_run_definition_basis(path,fields))
    return errors

def validate_terminal_receipt(path,fields,expected_status_schema=None):
    errors=[]; prefix='Loop Owner Acceptance '+str(path)
    missing=RECEIPT_REQUIRED_FIELDS-set(fields); unknown=set(fields)-RECEIPT_REQUIRED_FIELDS
    if missing: errors.append(prefix+' missing fields '+', '.join(sorted(missing)))
    if unknown: errors.append(prefix+' has unknown fields '+', '.join(sorted(unknown)))
    if fields.get('Artifact role')!='LOOP_OWNER_ACCEPTANCE_RECEIPT': errors.append(prefix+' role is invalid')
    for field in ['Acceptance ID','Run ID','Run-start contract ID','Run-start contract SHA-256','Status schema version','LCCoding phase scope','Phase-owned objective','Candidate ID / hash','D3 Receipt','Entry / role / account','Scenario IDs','Acceptance steps','Invisible risks already verified','Evidence return target in the calling phase','Accepted at']:
        if not present(fields.get(field)): errors.append(prefix+' missing terminal evidence '+field)
    schema=fields.get('Status schema version')
    phase_order=PHASE_IDS_BY_SCHEMA.get(schema)
    if phase_order is None: errors.append(prefix+' has unsupported Status schema version')
    if expected_status_schema is not None and schema!=expected_status_schema:
        errors.append(prefix+' Status schema version disagrees with authoritative status')
    if not phase_order or fields.get('LCCoding phase scope') not in phase_order:
        errors.append(prefix+' has invalid phase for Status schema version')
    if fields.get('Candidate ID / hash') is not None and not exact_id_hash(fields.get('Candidate ID / hash')):
        errors.append(prefix+' Candidate ID / hash must be exact stable ID / lowercase SHA-256')
    if fields.get('Calling phase gate remains independently evaluated')!='YES': errors.append(prefix+' attempts to advance the calling phase')
    if fields.get('Owner result') not in {'LOOP_OWNER_ACCEPTED','LOOP_PRODUCT_REWORK','LOOP_PRODUCT_DEFINITION_CHANGE','LOOP_OWNER_DEFERRED'}:
        errors.append(prefix+' Owner result is invalid')
    return errors

def parse_closed_id_set(value,label):
    tokens=[token.strip() for token in str(value or '').split(',') if token.strip() and token.strip().upper()!='NONE']
    errors=[]
    if len(tokens)!=len(set(tokens)): errors.append(label+' contains duplicate Run IDs')
    for token in tokens:
        if not stable_id(token): errors.append(label+' contains unsafe Run ID '+token)
    return set(tokens),errors

def validate_run_evidence(lc,status,manifest,lock,manifest_path):
    errors,eligible,has_collection=validate_execution_method_registry(manifest,lock,manifest_path)
    status_schema=status.get('status_schema_version')
    runs_root=lc/'runs'; starts={}; start_contract_ids={}; receipts={}; receipt_ids={}; receipt_id_counts={}
    if runs_root.is_dir():
        for path in runs_root.rglob('*.md'):
            fields,field_errors=parse_markdown_fields_strict(path); errors.extend(field_errors)
            if path.name=='RUN-HANDOFF.md' or fields.get('Artifact role')=='RUN_START_CONTRACT':
                errors.extend(validate_run_start_record(path,fields,eligible,manifest,lock,status_schema))
                run_id=str(fields.get('Run ID','')).strip()
                if run_id in starts: errors.append('duplicate Run start for '+run_id)
                elif run_id: starts[run_id]=(path,fields)
                contract_id=str(fields.get('Start Contract ID','')).strip()
                if contract_id in start_contract_ids: errors.append('duplicate Run-start contract ID '+contract_id)
                elif contract_id: start_contract_ids[contract_id]=path
    reviews=lc/'reviews'
    if reviews.is_dir():
        for path in reviews.rglob('*.md'):
            fields,field_errors=parse_markdown_fields_strict(path)
            if fields.get('Artifact role')!='LOOP_OWNER_ACCEPTANCE_RECEIPT': continue
            errors.extend(field_errors); errors.extend(validate_terminal_receipt(path,fields,status_schema))
            run_id=str(fields.get('Run ID','')).strip()
            receipts.setdefault(run_id,[]).append((path,fields))
            acceptance_id=str(fields.get('Acceptance ID','')).strip()
            receipt_id_counts[acceptance_id]=receipt_id_counts.get(acceptance_id,0)+1
            if acceptance_id in receipt_ids: errors.append('duplicate Loop Owner Acceptance ID '+acceptance_id)
            elif acceptance_id: receipt_ids[acceptance_id]=path
    for run_id,items in receipts.items():
        if len(items)>1: errors.append('Run has more than one formal Loop Owner Acceptance receipt: '+run_id)
    raw_indexed=status.get('loop_owner_acceptances',[])
    if not isinstance(raw_indexed,list):
        errors.append('status acceptance index must be a list'); indexed=[]
    else:
        indexed=raw_indexed
        for acceptance_id in indexed:
            if not isinstance(acceptance_id,str) or not stable_id(acceptance_id):
                errors.append('status acceptance index contains invalid Acceptance ID')
    aggregate_gate=status.get('phase_gates',{}).get('ALL_REQUIRED_RUNS_ACCEPTED')
    aggregate_direct=status.get('all_required_runs_accepted')
    aggregate_claimed=completed_evidence(aggregate_gate) or completed_evidence(aggregate_direct)
    generic_mode=(
        has_collection
        or bool(starts)
        or bool(receipts)
    )
    schema_required=generic_mode or aggregate_claimed or bool(raw_indexed)
    if not schema_required: return errors
    phase_order=PHASE_IDS_BY_SCHEMA.get(status_schema)
    if phase_order is None: errors.append('Run evidence requires a supported authoritative status_schema_version')
    phase3=phase_order[2] if phase_order else None
    if not generic_mode: return errors
    if not has_collection and not any(str(fields.get('Selected execution method ID','')).upper() in LEGACY_METHOD_INTERFACES for _,fields in starts.values()):
        errors.append('Run evidence requires Canonical Manifest execution method registry')
    safe_indexed=[acceptance_id for acceptance_id in indexed if isinstance(acceptance_id,str) and stable_id(acceptance_id)]
    if len(safe_indexed)!=len(set(safe_indexed)): errors.append('status acceptance index contains duplicates')
    indexed_set=set(safe_indexed)
    for acceptance_id in safe_indexed:
        count=receipt_id_counts.get(acceptance_id,0)
        if count==0: errors.append('status acceptance index has no terminal receipt: '+acceptance_id)
        elif count!=1: errors.append('status acceptance index does not resolve exactly one terminal receipt: '+acceptance_id)
    for acceptance_id,count in receipt_id_counts.items():
        if not stable_id(acceptance_id):
            errors.append('formal receipt has invalid Acceptance ID')
        elif acceptance_id not in indexed_set:
            errors.append('formal terminal receipt is absent from status acceptance index: '+acceptance_id)
    for run_id,items in receipts.items():
        start_item=starts.get(run_id)
        if not start_item: errors.append('terminal receipt has no Run start: '+run_id); continue
        start=start_item[1]
        for _,receipt in items:
            bindings={
                'Run-start contract ID':'Start Contract ID',
                'Run-start contract SHA-256':'Start Contract SHA-256',
                'Status schema version':'Status schema version',
                'LCCoding phase scope':'LCCoding phase scope',
                'Phase-owned objective':'Phase-owned objective',
                'Evidence return target in the calling phase':'Evidence return target in calling phase',
            }
            for receipt_field,start_field in bindings.items():
                if receipt.get(receipt_field)!=start.get(start_field): errors.append('receipt/start mismatch for '+run_id+': '+receipt_field)
            if receipt.get('Acceptance ID') not in indexed_set: errors.append('terminal receipt is absent from status acceptance index: '+run_id)
    if aggregate_claimed:
        if not completed_evidence(aggregate_gate) or not completed_evidence(aggregate_direct):
            errors.append('Phase-3 aggregate representations disagree')
        if status.get('open_owner_gaps'): errors.append('open Owner gaps block Phase-3 aggregate')
        slice_path=resolve_active_slice(lc,status.get('active_slice'))
        if not slice_path: errors.append('Phase-3 aggregate requires active Feature Slice'); return errors
        slice_fields=parse_markdown_fields(slice_path)
        sets={}
        for field in ['Required Run IDs','Optional Run IDs','Superseded Run IDs','Invalidated Run IDs']:
            sets[field],set_errors=parse_closed_id_set(slice_fields.get(field),field); errors.extend(set_errors)
        required=sets['Required Run IDs']
        if not required: errors.append('Phase-3 aggregate requires non-empty Required Run IDs')
        names=list(sets)
        for index,left in enumerate(names):
            for right in names[index+1:]:
                overlap=sets[left]&sets[right]
                if overlap: errors.append('Run classification sets overlap: '+', '.join(sorted(overlap)))
        phase3_runs={run_id for run_id,(_,fields) in starts.items() if phase3 and fields.get('LCCoding phase scope')==phase3}
        classified=set().union(*sets.values())
        if phase3_runs-classified: errors.append('unclassified Phase-3 Runs: '+', '.join(sorted(phase3_runs-classified)))
        if required-phase3_runs: errors.append('missing required Phase-3 Run starts: '+', '.join(sorted(required-phase3_runs)))
        candidate=str(slice_fields.get('Accepted integration candidate / baseline identity','')).strip()
        candidate_identity=exact_id_hash(candidate)
        if not candidate_identity: errors.append('accepted integration candidate requires exact ID / sha256 identity')
        slice_identity=str(slice_fields.get('Slice ID / version','')).strip()
        baseline=str(slice_fields.get('Product Baseline trace','')).strip()
        integration=str(slice_fields.get('Integration Baseline ID','')).strip()
        ui_reference=str(slice_fields.get('Applicable UI subtree ID / path','')).partition('::')[0].strip()
        if not stable_id(ui_reference) or not stable_id(integration):
            errors.append('active Slice requires stable UI and Integration Baseline IDs')
        for run_id in sorted(required):
            start_item=starts.get(run_id); receipt_items=receipts.get(run_id,[])
            if not start_item: continue
            start=start_item[1]
            if len(receipt_items)!=1:
                errors.append('required Run requires exactly one receipt: '+run_id); continue
            receipt=receipt_items[0][1]
            suffix=PHASE_IDS_BY_SCHEMA[status_schema][2]
            start_ui_integration=exact_ui_integration_identity(start.get(f'Applicable UI / Integration Baseline ({suffix} only)'))
            if start.get(f'Feature Slice ID / version ({suffix} only)')!=slice_identity or start.get(f'Product Baseline trace ({suffix} only)')!=baseline or start_ui_integration!=(ui_reference,integration):
                errors.append('required Run start disagrees with active Slice: '+run_id)
            if start.get('Readiness result')!='READY' or start.get('Blocker evidence')!='NONE':
                errors.append('required Run start is not READY: '+run_id)
            receipt_candidate=str(receipt.get('Candidate ID / hash','')).strip()
            if not exact_id_hash(receipt_candidate) or not candidate_identity or receipt_candidate!=candidate or receipt.get('Owner result')!='LOOP_OWNER_ACCEPTED' or not present(receipt.get('D3 Receipt')):
                errors.append('required Run terminal evidence is not accepted/current: '+run_id)
    return errors

WORKFLOW_MAP_COLUMNS_260=(
    'Workflow ID','Classification (CORE/EXTRA)','Implementation status','Subtree path',
    'Component version','Content hash','Actors','Trigger','States / rules',
    'Data / permissions','Failure / recovery','API contract / evidence',
    'MCP contract / evidence','UI subtree references','Simulation subtree references',
    'Evidence / attestation','Calabash trace','Primary mainline',
)
WORKFLOW_MAP_COLUMNS_270=(
    'Workflow ID','Classification (CORE/EXTRA)','Implementation status',
    'Classification authority','Subtree path','Component version','Content hash',
    'Workflow Capability ID','Actors','Trigger','Rules / state / side-effect trace',
    'Data / permissions','Failure / recovery','API contract / evidence',
    'MCP contract / evidence','UI subtree references','Simulation subtree references',
    'Evidence / attestation','Primary mainline',
)
UI_MAP_COLUMNS_260=(
    'UI ID','Subtree path','Component version','Content hash','Actor','Surface / state',
    'Actions / feedback','Workflow subtree references','Simulation subtree references',
    'Evidence / attestation','Lock status','Primary mainline',
)
UI_MAP_COLUMNS_270=UI_MAP_COLUMNS_260+('UI change authority','Baseline Change Request')
SIMULATION_MAP_COLUMNS=(
    'Simulation ID','Subtree path','Component version','Content hash','Foundation status',
    'Workflow subtree references','UI subtree references','Primary mainline',
)
SCENARIO_COLUMNS=(
    'Simulation ID','Scenario ID','Actors','Data/state/time','Path','Failure/recovery',
    'Fidelity','Visible / invisible evidence','Used by Slice/Run/Acceptance',
    'Scenario version',
)
HANDOFF_COLUMNS_260=(
    'Subtree type','Subtree ID','Path','Component version','Content hash','Classification',
    'API evidence','MCP evidence','Primary mainline','Related subtree IDs',
)
HANDOFF_COLUMNS_270=(
    'Subtree type','Subtree ID','Path','Component version','Content hash','Classification',
    'Classification authority','Workflow Capability ID','API evidence','MCP evidence',
    'Primary mainline','Related subtree IDs',
)

def _markdown_pipe_cells(line):
    stripped=line.strip()
    if not stripped.startswith('|') or not stripped.endswith('|'): return None
    return tuple(cell.strip() for cell in stripped[1:-1].split('|'))

def parse_closed_product_tables(path,specifications):
    """Parse only the four product identity surfaces; every pipe line is accounted for."""
    try: lines=path.read_text(encoding='utf-8').splitlines()
    except (OSError,UnicodeError): return {},['cannot read UTF-8 product identity record '+str(path)]
    parsed={}; errors=[]; occupied=set()
    malformed_pipe_lines={index for index,line in enumerate(lines) if line.strip().startswith('|') and _markdown_pipe_cells(line) is None}
    for index in sorted(malformed_pipe_lines):
        errors.append(f'malformed product identity pipe row at line {index+1}')
    pipe_cells={index:_markdown_pipe_cells(line) for index,line in enumerate(lines)}
    pipe_cells={index:cells for index,cells in pipe_cells.items() if cells is not None}
    for specification in specifications:
        label,allowed_headers=specification[:2]
        required=specification[2] if len(specification)>2 else True
        matches=[
            (index,cells) for index,cells in pipe_cells.items()
            if cells in allowed_headers
        ]
        if len(matches)>1 or (required and len(matches)!=1):
            errors.append(f'{label} requires exactly one closed table header')
        if not matches:
            parsed[label]=[]; continue
        header_index,headers=matches[0]
        occupied.add(header_index)
        separator_index=header_index+1
        separator=pipe_cells.get(separator_index)
        if separator is None or len(separator)!=len(headers) or any(cell!='---' for cell in separator):
            errors.append(f'{label} requires one exact table separator')
            parsed[label]=[]; continue
        occupied.add(separator_index)
        rows=[]; row_index=separator_index+1
        while row_index<len(lines):
            cells=pipe_cells.get(row_index)
            if cells is None: break
            occupied.add(row_index)
            if len(cells)!=len(headers):
                errors.append(f'{label} contains a malformed table row at line {row_index+1}')
            elif all(cell=='---' for cell in cells):
                errors.append(f'{label} contains an unexpected table separator at line {row_index+1}')
            elif cells in allowed_headers:
                errors.append(f'{label} contains a duplicate table header at line {row_index+1}')
            else:
                rows.append(dict(zip(headers,cells)))
            row_index+=1
        parsed[label]=rows
    for index in sorted(set(pipe_cells)-occupied):
        errors.append(f'unexpected product identity pipe row at line {index+1}')
    return parsed,errors

def parse_markdown_table(path,first_header):
    lines=path.read_text(encoding='utf-8').splitlines(); headers=None; rows=[]
    for index,line in enumerate(lines):
        if not line.startswith('|'): continue
        cells=[cell.strip() for cell in line.strip().strip('|').split('|')]
        if cells and cells[0]==first_header:
            headers=cells
            for row_line in lines[index+2:]:
                if not row_line.startswith('|'): break
                values=[cell.strip() for cell in row_line.strip().strip('|').split('|')]
                if len(values)==len(headers): rows.append(dict(zip(headers,values)))
            break
    return rows

def resolve_active_slice(lc,active):
    reference=active.get('path') or active.get('id') if isinstance(active,dict) else str(active)
    if not reference: return None
    root=lc.resolve()
    def contained_file(candidate):
        resolved=candidate.resolve()
        return resolved if resolved.is_relative_to(root) and resolved.is_file() else None
    candidate=contained_file(lc/reference)
    if candidate: return candidate
    candidate=contained_file(lc/'slices'/(reference if reference.lower().endswith('.md') else reference+'.md'))
    if candidate: return candidate
    matches=list((lc/'slices').glob('*'+reference+'*.md'))
    return matches[0] if len(matches)==1 else None

def validate_complexity_depth(fingerprint):
    errors=[]
    complexity=fingerprint.get('complexity')
    depth=fingerprint.get('depth',{})
    if not isinstance(complexity,dict):
        return ['Project Fingerprint complexity must record five factors']
    values=[]; unresolved=[]
    for factor in COMPLEXITY_FACTORS:
        value=str(complexity.get(factor,'')).upper()
        if value not in COMPLEXITY_LEVELS: errors.append('invalid complexity factor '+factor)
        else:
            values.append(value)
            if value=='UNKNOWN': unresolved.append(factor)
    if unresolved:
        errors.append('complexity unresolved for '+', '.join(unresolved)+'; requires depth assessment')
    if any(value!='LOW' for value in values) and not depth.get('rationale'):
        errors.append('non-low complexity requires a depth rationale')
    if any(value in {'HIGH','UNKNOWN'} for value in values) and not any(depth.get(name) for name in ['analysis','materials','evidence']):
        errors.append('high or unresolved complexity requires deeper coverage in analysis, materials, or evidence')
    return errors

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('project'); args=ap.parse_args()
    lc=Path(args.project)/'.lccoding'; errors=[]
    for x in REQUIRED:
        if not (lc/x).exists(): errors.append('missing '+x)
    start={}; status={}; phase_status={}; health={}
    if (lc/'PROJECT-START.json').exists():
        start=json.loads((lc/'PROJECT-START.json').read_text(encoding='utf-8'))
        mode=start.get('initialization_mode','NEW')
        if mode not in {'NEW','EXISTING'}: errors.append('invalid initialization_mode')
        if mode=='EXISTING':
            if not start.get('source_head'): errors.append('existing project source_head missing')
            if not start.get('source_version'): errors.append('existing project source_version missing')
            if start.get('completion_claim_status') not in {'NO_CLAIM','CLAIMED_UNATTESTED'}:
                errors.append('existing completion claim crossed the evidence boundary')
    if (lc/'status.json').exists():
        try: status=strict_vulnerability_json(lc/'status.json')
        except (OSError,UnicodeError,ValueError) as error:
            errors.append('status.json is not strict JSON: '+str(error)); status={}
    errors.extend(validate_loop_control_binding(lc))
    if (lc/'PHASE-STATUS.json').exists(): phase_status=json.loads((lc/'PHASE-STATUS.json').read_text(encoding='utf-8'))
    if (lc/'PROJECT-HEALTH.json').exists(): health=json.loads((lc/'PROJECT-HEALTH.json').read_text(encoding='utf-8'))
    if status and phase_status and health:
        errors.extend(validate_status_authority(status,phase_status,health))
    if status:
        errors.extend(validate_agent_native_artifacts(lc,status))
    if start and status and health:
        errors.extend(validate_takeover_readiness(start,status,health))
    fingerprint={}
    if (lc/'PROJECT-FINGERPRINT.json').exists():
        fingerprint=json.loads((lc/'PROJECT-FINGERPRINT.json').read_text(encoding='utf-8'))
        errors.extend(validate_complexity_depth(fingerprint))
    workflow_rows=[]; ui_rows=[]; simulation_rows=[]; scenario_rows=[]
    workflow_fields={}; ui_fields={}; simulation_fields={}; product_surface_errors=[]
    workflow_path=lc/'WORKFLOW-MAP.md'; ui_path=lc/'UI-MAP.md'; simulation_path=lc/'SIMULATION-WORLD.md'
    if workflow_path.exists():
        workflow_fields,field_errors=parse_markdown_fields_strict(workflow_path)
        product_surface_errors.extend(field_errors)
        if 'Primary product mainline ID' not in workflow_fields:
            product_surface_errors.append('Workflow Map requires exactly one Primary product mainline ID')
        tables,table_errors=parse_closed_product_tables(
            workflow_path,
            [('Workflow Map',(WORKFLOW_MAP_COLUMNS_260,WORKFLOW_MAP_COLUMNS_270))],
        )
        workflow_rows=tables.get('Workflow Map',[]); product_surface_errors.extend(table_errors)
    if ui_path.exists():
        ui_fields,field_errors=parse_markdown_fields_strict(ui_path)
        product_surface_errors.extend(field_errors)
        if 'Primary product mainline ID' not in ui_fields:
            product_surface_errors.append('UI Map requires exactly one Primary product mainline ID')
        tables,table_errors=parse_closed_product_tables(
            ui_path,[('UI Map',(UI_MAP_COLUMNS_260,UI_MAP_COLUMNS_270))]
        )
        ui_rows=tables.get('UI Map',[]); product_surface_errors.extend(table_errors)
        product_surface_errors.extend(validate_ui_map_change_authority(ui_rows))
    if simulation_path.exists():
        simulation_fields,field_errors=parse_markdown_fields_strict(simulation_path)
        product_surface_errors.extend(field_errors)
        if 'Primary product mainline ID' not in simulation_fields:
            product_surface_errors.append('Simulation World requires exactly one Primary product mainline ID')
        tables,table_errors=parse_closed_product_tables(
            simulation_path,
            [
                ('Simulation subtree registry',(SIMULATION_MAP_COLUMNS,)),
                ('Scenario registry',(SCENARIO_COLUMNS,),False),
            ],
        )
        simulation_rows=tables.get('Simulation subtree registry',[])
        scenario_rows=tables.get('Scenario registry',[])
        product_surface_errors.extend(table_errors)
    calabash_handoff=lc/'CALABASH-UPGRADE-GATE.md'
    if calabash_handoff.exists():
        calabash_fields=parse_markdown_fields(calabash_handoff)
        if semantic_present(calabash_fields.get('Definition Baseline ID')) or calabash_fields.get('Handoff result') in {'PASS','BLOCKED'}:
            errors.extend(validate_calabash_definition_handoff(calabash_handoff,require_pass=False))
    impact_path=lc/'IMPACT-ANALYSIS.md'
    if impact_path.exists():
        impact_fields=parse_markdown_fields(impact_path)
        if impact_fields.get('Meaning impact classification') in {'MEANING_CHANGING','MEANING_NEUTRAL'}:
            errors.extend(validate_impact_analysis(impact_path))
    if status:
        errors.extend(validate_security_invalidation(lc,status))
    handoff=lc/'PRODUCT-BASELINE-HANDOFF.md'; handoff_errors=[]; handoff_fields={}; handoff_rows=[]; handoff_complete=False
    if handoff.exists():
        handoff_errors.extend(product_surface_errors)
        handoff_fields,handoff_field_errors=parse_markdown_fields_strict(handoff)
        handoff_errors.extend(handoff_field_errors)
        handoff_tables,handoff_table_errors=parse_closed_product_tables(
            handoff,[('Product Baseline locked subtrees',(HANDOFF_COLUMNS_260,HANDOFF_COLUMNS_270))]
        )
        handoff_rows=handoff_tables.get('Product Baseline locked subtrees',[])
        handoff_errors.extend(handoff_table_errors)
        handoff_status=str(handoff_fields.get('Handoff status','')).strip().upper()
        handoff_complete=handoff_status=='COMPLETE'
        if handoff_status not in {'BLOCKED','COMPLETE'}:
            handoff_errors.append('Product Baseline Handoff status must be BLOCKED or COMPLETE')
        definition_citation_fields={'Calabash Definition Handoff ID / exact hash','Calabash Definition Handoff result'}
        if handoff_complete:
            if not definition_citation_fields.issubset(handoff_fields):
                handoff_errors.append('Product Baseline COMPLETE requires Calabash Definition Handoff citation and result')
            handoff_errors.extend(validate_product_definition_basis(lc,handoff_fields))
            repository=canonical_github_repository(handoff_fields.get('Project repository identity'))
            project_repository=canonical_github_repository(start.get('repository'))
            if not repository or (project_repository and repository!=project_repository):
                handoff_errors.append('Product Baseline Handoff must use the total project repository')
            frozen_commit=handoff_fields.get('Project frozen exact commit SHA','')
            handoff_errors.extend(validate_workflow_subtrees(workflow_rows,Path(args.project),frozen_commit))
            handoff_errors.extend(validate_product_subtree_baseline(
                handoff_rows,
                handoff_fields.get('Primary product mainline ID'),
                handoff_fields.get('Primary mainline Owner confirmation'),
                Path(args.project),
                frozen_commit,
                workflow_rows,
                ui_rows,
                simulation_rows,
                {
                    'Workflow':workflow_fields.get('Primary product mainline ID'),
                    'UI':ui_fields.get('Primary product mainline ID'),
                    'Simulation':simulation_fields.get('Primary product mainline ID'),
                },
            ))
    else:
        errors.extend(product_surface_errors)
        errors.extend(validate_workflow_subtrees(workflow_rows))
    errors.extend(handoff_errors)
    if completed_evidence(status.get('product_baseline')):
        if not handoff.exists():
            errors.append('accepted Product Baseline requires PRODUCT-BASELINE-HANDOFF.md')
        elif not handoff_complete or handoff_errors:
            errors.append('accepted Product Baseline requires a mechanically valid and COMPLETE Product Baseline Handoff')
    if status.get('active_slice'):
        slice_path=resolve_active_slice(lc,status.get('active_slice'))
        if not slice_path: errors.append('active Slice artifact missing')
        else:
            fields,slice_field_errors=parse_markdown_fields_strict(slice_path)
            errors.extend(slice_field_errors)
            errors.extend(validate_slice_execution_preflight(fields,fingerprint,start.get('repository')))
            errors.extend(validate_real_product_integration(
                lc,slice_path,fields,workflow_rows,ui_rows,simulation_rows,scenario_rows,handoff_fields
            ))
    gap_records=[]
    if (lc/'reviews').is_dir():
        for review in (lc/'reviews').rglob('*.md'):
            fields=parse_markdown_fields(review)
            if present(fields.get('Owner Gap ID')): gap_records.append(fields)
    if status:
        errors.extend(validate_owner_gap_lineage(status,gap_records))
    manifest={}; lock={}
    manifest_path=lc/'CANONICAL-MANIFEST.json'
    if manifest_path.exists(): manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    if (lc/'INTERPRETATION-LOCK.json').exists():
        lock=json.loads((lc/'INTERPRETATION-LOCK.json').read_text(encoding='utf-8'))
        if lock.get('status')!='VALID': errors.append('Interpretation Lock is not VALID')
    if manifest_path.exists() and (lc/'INTERPRETATION-LOCK.json').exists():
        errors.extend(validate_method_baseline_records(manifest,lock))
        errors.extend(validate_run_evidence(lc,status,manifest,lock,manifest_path))
    if (Path(args.project)/'VERSION').exists():
        if not (Path(args.project)/'VERSION').read_text().strip(): errors.append('empty VERSION')
    elif start.get('initialization_mode','NEW')=='NEW': errors.append('missing project VERSION')
    if errors:
        print('FAIL'); print('\n'.join(errors)); raise SystemExit(1)
    print('PASS')
if __name__=='__main__': main()
