#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, importlib.util, json, re, subprocess

_PHASE_VALIDATOR_PATH=Path(__file__).with_name('validate_phase_status.py')
_PHASE_VALIDATOR_SPEC=importlib.util.spec_from_file_location(
    'lccoding_validate_phase_status',_PHASE_VALIDATOR_PATH
)
_PHASE_VALIDATOR=importlib.util.module_from_spec(_PHASE_VALIDATOR_SPEC)
_PHASE_VALIDATOR_SPEC.loader.exec_module(_PHASE_VALIDATOR)
COMPLETED_PHASE_STATES=_PHASE_VALIDATOR.COMPLETED_PHASE_STATES
completed_evidence=_PHASE_VALIDATOR.completed_evidence
normalize_lifecycle_state=_PHASE_VALIDATOR.normalize_lifecycle_state
validate_phase_status_record=_PHASE_VALIDATOR.validate_phase_status

_METHOD_BASELINE_VALIDATOR_PATH=Path(__file__).with_name('validate_method_baseline.py')
_METHOD_BASELINE_VALIDATOR_SPEC=importlib.util.spec_from_file_location(
    'lccoding_validate_method_baseline',_METHOD_BASELINE_VALIDATOR_PATH
)
_METHOD_BASELINE_VALIDATOR=importlib.util.module_from_spec(_METHOD_BASELINE_VALIDATOR_SPEC)
_METHOD_BASELINE_VALIDATOR_SPEC.loader.exec_module(_METHOD_BASELINE_VALIDATOR)
validate_method_baseline_records=_METHOD_BASELINE_VALIDATOR.validate_method_baseline_records

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
    'LCCoding phase scope','Phase-owned objective',
    'Calling phase authority / contract reference(s)','Frozen Run scope',
    'Explicit exclusions','Selected execution method ID',
    'Selected execution method version','Selected execution method exact hash',
    'Selected execution method canonical interface / contract reference',
    'Phase-appropriate input evidence / prerequisites',
    'Evidence return target in calling phase',
    'D0-D3 evidence / verification condition','Loop Owner Acceptance condition / route',
    'Risk / depth decision','Readiness result','Blocker evidence',
}
PHASE3_START_FIELDS={
    'Product Baseline trace (ENGINEERING_RUNS only)',
    'Feature Slice ID / version (ENGINEERING_RUNS only)',
    'Applicable UI / Integration Baseline (ENGINEERING_RUNS only)',
}
DEFINITION_START_FIELDS={
    'Meaning impact classification',
    'Definition basis / neutral Impact Analysis reference',
    'Applicable Snake / Scorpion disposition evidence reference',
}
START_REQUIRED_FIELDS=START_REQUIRED_FIELDS|DEFINITION_START_FIELDS
START_ALLOWED_FIELDS=START_REQUIRED_FIELDS|PHASE3_START_FIELDS
RECEIPT_REQUIRED_FIELDS={
    'Artifact role','Acceptance ID','Run ID','Run-start contract ID',
    'Run-start contract SHA-256','LCCoding phase scope','Phase-owned objective',
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
PHASE_IDS={'INITIAL','PRODUCT_FORMATION','ENGINEERING_RUNS','DELIVERY_PREPARATION'}
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

def validate_status_authority(status,phase_status,health):
    errors=validate_phase_status_record(phase_status)
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
    if phase_status.get('current_phase')!=status.get('current_phase'):
        errors.append('derived phase status disagrees with authoritative current_phase')
    gate_map={
        'INITIAL':('exit_gate','INITIAL_READY'),
        'ENGINEERING_RUNS':('aggregate_exit_gate','ALL_REQUIRED_RUNS_ACCEPTED'),
        'DELIVERY_PREPARATION':('exit_gate','DELIVERY_READY'),
    }
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
    if status.get('current_phase') in {'ENGINEERING_RUNS','DELIVERY_PREPARATION'}:
        if not authoritative_complete:
            errors.append('ENGINEERING_RUNS requires accepted Product Baseline')
        if not derived_complete or formation.get('status') not in COMPLETED_PHASE_STATES:
            errors.append('ENGINEERING_RUNS requires matching derived Product Formation completion')
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

def validate_run_start_record(path,fields,eligible_methods,manifest,lock):
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
    phase=fields.get('LCCoding phase scope')
    if phase not in PHASE_IDS: errors.append(prefix+' has invalid phase')
    if phase=='ENGINEERING_RUNS':
        if PHASE3_START_FIELDS-set(fields) or any(not present(fields.get(field)) for field in PHASE3_START_FIELDS):
            errors.append(prefix+' Phase-3 integration identities missing')
    elif PHASE3_START_FIELDS.intersection(fields): errors.append(prefix+' fabricates Phase-3 identities outside ENGINEERING_RUNS')
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

def validate_terminal_receipt(path,fields):
    errors=[]; prefix='Loop Owner Acceptance '+str(path)
    missing=RECEIPT_REQUIRED_FIELDS-set(fields); unknown=set(fields)-RECEIPT_REQUIRED_FIELDS
    if missing: errors.append(prefix+' missing fields '+', '.join(sorted(missing)))
    if unknown: errors.append(prefix+' has unknown fields '+', '.join(sorted(unknown)))
    if fields.get('Artifact role')!='LOOP_OWNER_ACCEPTANCE_RECEIPT': errors.append(prefix+' role is invalid')
    for field in ['Acceptance ID','Run ID','Run-start contract ID','Run-start contract SHA-256','LCCoding phase scope','Phase-owned objective','Candidate ID / hash','D3 Receipt','Entry / role / account','Scenario IDs','Acceptance steps','Invisible risks already verified','Evidence return target in the calling phase','Accepted at']:
        if not present(fields.get(field)): errors.append(prefix+' missing terminal evidence '+field)
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
    runs_root=lc/'runs'; starts={}; start_contract_ids={}; receipts={}; receipt_ids={}; receipt_id_counts={}
    if runs_root.is_dir():
        for path in runs_root.rglob('*.md'):
            fields,field_errors=parse_markdown_fields_strict(path); errors.extend(field_errors)
            if path.name=='RUN-HANDOFF.md' or fields.get('Artifact role')=='RUN_START_CONTRACT':
                errors.extend(validate_run_start_record(path,fields,eligible,manifest,lock))
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
            errors.extend(field_errors); errors.extend(validate_terminal_receipt(path,fields))
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
    generic_collection=manifest.get('execution_methods')
    generic_mode=(
        bool(generic_collection)
        or bool(starts)
        or bool(receipts)
        or (has_collection and (aggregate_claimed or bool(raw_indexed)))
    )
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
        phase3_runs={run_id for run_id,(_,fields) in starts.items() if fields.get('LCCoding phase scope')=='ENGINEERING_RUNS'}
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
            start_ui_integration=exact_ui_integration_identity(start.get('Applicable UI / Integration Baseline (ENGINEERING_RUNS only)'))
            if start.get('Feature Slice ID / version (ENGINEERING_RUNS only)')!=slice_identity or start.get('Product Baseline trace (ENGINEERING_RUNS only)')!=baseline or start_ui_integration!=(ui_reference,integration):
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
UI_MAP_COLUMNS=(
    'UI ID','Subtree path','Component version','Content hash','Actor','Surface / state',
    'Actions / feedback','Workflow subtree references','Simulation subtree references',
    'Evidence / attestation','Lock status','Primary mainline',
)
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
    if (lc/'status.json').exists(): status=json.loads((lc/'status.json').read_text(encoding='utf-8'))
    if (lc/'PHASE-STATUS.json').exists(): phase_status=json.loads((lc/'PHASE-STATUS.json').read_text(encoding='utf-8'))
    if (lc/'PROJECT-HEALTH.json').exists(): health=json.loads((lc/'PROJECT-HEALTH.json').read_text(encoding='utf-8'))
    if status and phase_status and health:
        errors.extend(validate_status_authority(status,phase_status,health))
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
            ui_path,[('UI Map',(UI_MAP_COLUMNS,))]
        )
        ui_rows=tables.get('UI Map',[]); product_surface_errors.extend(table_errors)
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
