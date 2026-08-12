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

def validate_workflow_subtrees(rows,repository_path=None,frozen_commit=None):
    errors=[]; ids=set(); paths=set()
    for index,row in enumerate(rows):
        prefix=f'Workflow row {index+1}'
        workflow_id=str(row.get('Workflow ID','')).strip()
        classification=str(row.get('Classification (CORE/EXTRA)','')).strip().upper()
        implementation=str(row.get('Implementation status','')).strip().upper()
        primary=str(row.get('Primary mainline','')).strip().upper()
        if not workflow_id: errors.append(prefix+' missing Workflow ID')
        elif workflow_id in ids: errors.append('duplicate Workflow ID '+workflow_id)
        ids.add(workflow_id)
        if classification not in {'CORE','EXTRA'}: errors.append(prefix+' requires CORE or EXTRA classification')
        if implementation not in {'IMPLEMENTED','UNIMPLEMENTED'}: errors.append(prefix+' requires implementation status')
        if primary not in {'YES','NO'}: errors.append(prefix+' Primary mainline must be YES or NO')
        if classification=='CORE' and implementation!='IMPLEMENTED': errors.append(prefix+' CORE must be implemented')
        if primary=='YES' and (classification!='CORE' or implementation!='IMPLEMENTED'):
            errors.append(prefix+' primary mainline Workflow must be implemented CORE')
        if implementation=='IMPLEMENTED':
            path=str(row.get('Subtree path','')).strip()
            if not safe_subtree_path(path): errors.append(prefix+' requires a safe relative subtree path')
            elif path in paths: errors.append('duplicate subtree path '+path)
            paths.add(path)
            if not component_version(row.get('Component version')): errors.append(prefix+' requires a three-part component version')
            if not CONTENT_HASH_RE.fullmatch(str(row.get('Content hash','')).strip()):
                errors.append(prefix+' requires content hash')
            if not evidence(row.get('API contract / evidence')): errors.append(prefix+' implemented Workflow requires API evidence')
            if not evidence(row.get('MCP contract / evidence')): errors.append(prefix+' implemented Workflow requires MCP evidence')
            if repository_path is not None and frozen_commit is not None and safe_subtree_path(path):
                errors.extend(verify_frozen_subtree_identity(
                    repository_path,frozen_commit,row,prefix,path_field='Subtree path'
                ))
        elif classification=='EXTRA':
            for field in ['Subtree path','Component version','Content hash','API contract / evidence','MCP contract / evidence']:
                if str(row.get(field,'')).strip().upper()!='NOT_APPLICABLE':
                    errors.append(prefix+' unimplemented EXTRA cannot claim '+field)
    return errors

def split_ids(value):
    return {item.strip() for item in str(value or '').split(',') if item.strip() and item.strip().upper()!='NONE'}

def map_identity_rows(workflow_rows,ui_rows,simulation_rows):
    identities={}; errors=[]
    sources=[
        ('WORKFLOW',workflow_rows,'Workflow ID','Subtree path',('UI subtree references','Simulation subtree references')),
        ('UI',ui_rows,'UI ID','Subtree path',('Workflow subtree references','Simulation subtree references')),
        ('SIMULATION',simulation_rows,'Simulation ID','Subtree path',('Workflow subtree references','UI subtree references')),
    ]
    for subtree_type,rows,id_field,path_field,relation_fields in sources:
        for index,row in enumerate(rows):
            if subtree_type=='WORKFLOW' and str(row.get('Implementation status','')).strip().upper()!='IMPLEMENTED':
                continue
            prefix=f'{subtree_type} Map row {index+1}'
            subtree_id=str(row.get(id_field,'')).strip()
            primary=str(row.get('Primary mainline','')).strip().upper()
            if not subtree_id:
                errors.append(prefix+' missing subtree ID'); continue
            key=(subtree_type,subtree_id)
            if key in identities:
                errors.append(prefix+' duplicates a Map subtree ID'); continue
            if primary not in {'YES','NO'}: errors.append(prefix+' Primary mainline must be YES or NO')
            if not safe_subtree_path(row.get(path_field)): errors.append(prefix+' requires a safe relative subtree path')
            if not component_version(row.get('Component version')): errors.append(prefix+' requires a three-part component version')
            if not CONTENT_HASH_RE.fullmatch(str(row.get('Content hash','')).strip()): errors.append(prefix+' requires content hash')
            relations=set()
            for field in relation_fields: relations.update(split_ids(row.get(field)))
            identities[key]={
                'path':str(row.get(path_field,'')).strip(),
                'version':str(row.get('Component version','')).strip(),
                'hash':str(row.get('Content hash','')).strip().lower(),
                'classification':str(row.get('Classification (CORE/EXTRA)','NOT_APPLICABLE')).strip().upper(),
                'api':str(row.get('API contract / evidence','NOT_APPLICABLE')).strip(),
                'mcp':str(row.get('MCP contract / evidence','NOT_APPLICABLE')).strip(),
                'primary':primary,
                'relations':relations,
            }
    return identities,errors

def validate_map_handoff_identity(rows,workflow_rows,ui_rows,simulation_rows,primary_mainline_id,map_mainline_ids):
    expected,errors=map_identity_rows(workflow_rows,ui_rows,simulation_rows)
    for source,value in map_mainline_ids.items():
        if not evidence(value): errors.append(source+' Map requires a Primary product mainline ID')
        elif str(value).strip()!=str(primary_mainline_id or '').strip():
            errors.append(source+' Map Primary product mainline ID does not match Product Baseline Handoff')
    actual={}
    for index,row in enumerate(rows):
        key=(str(row.get('Subtree type','')).strip().upper(),str(row.get('Subtree ID','')).strip())
        if key in actual: continue
        actual[key]={
            'path':str(row.get('Path','')).strip(),
            'version':str(row.get('Component version','')).strip(),
            'hash':str(row.get('Content hash','')).strip().lower(),
            'classification':str(row.get('Classification','')).strip().upper(),
            'api':str(row.get('API evidence','')).strip(),
            'mcp':str(row.get('MCP evidence','')).strip(),
            'primary':str(row.get('Primary mainline','')).strip().upper(),
            'relations':split_ids(row.get('Related subtree IDs')),
        }
    missing=set(expected)-set(actual)
    extra=set(actual)-set(expected)
    for subtree_type,subtree_id in sorted(missing):
        errors.append(f'{subtree_type} Map subtree {subtree_id} is missing from Product Baseline Handoff')
    for subtree_type,subtree_id in sorted(extra):
        errors.append(f'Product Baseline Handoff subtree {subtree_id} is absent from the {subtree_type} Map')
    for key in sorted(set(expected).intersection(actual)):
        subtree_type,subtree_id=key
        for field in ['path','version','hash','classification','api','mcp','primary','relations']:
            if expected[key][field]!=actual[key][field]:
                errors.append(f'{subtree_type} Map / Product Baseline Handoff identity mismatch for {subtree_id}: {field}')
    return errors

def validate_product_subtree_baseline(
    rows,primary_mainline_id,owner_confirmation,
    repository_path=None,frozen_commit=None,
    workflow_rows=None,ui_rows=None,simulation_rows=None,map_mainline_ids=None,
):
    errors=[]; ids=set(); paths={}; by_type={'UI':set(),'WORKFLOW':set(),'SIMULATION':set()}; primary={key:set() for key in by_type}
    if not evidence(primary_mainline_id): errors.append('Primary product mainline ID required')
    confirmation=str(owner_confirmation or '').strip()
    if not re.fullmatch(r'OWNER_CONFIRMED:\s*\S(?:.*\S)?',confirmation,re.IGNORECASE):
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
        if not subtree_id: errors.append(prefix+' missing Subtree ID')
        elif subtree_id in ids: errors.append('duplicate Subtree ID '+subtree_id)
        ids.add(subtree_id); by_type[subtree_type].add(subtree_id)
        if not safe_subtree_path(path): errors.append(prefix+' requires a safe relative subtree path')
        elif path in paths: errors.append('duplicate subtree path '+path)
        paths[path]=subtree_type
        if not component_version(row.get('Component version')): errors.append(prefix+' requires a three-part component version')
        if not CONTENT_HASH_RE.fullmatch(str(row.get('Content hash','')).strip()):
            errors.append(prefix+' requires content hash')
        if subtree_type=='WORKFLOW':
            if str(row.get('Classification','')).strip().upper() not in {'CORE','EXTRA'}:
                errors.append(prefix+' Workflow requires CORE or EXTRA classification')
            if not evidence(row.get('API evidence')): errors.append(prefix+' implemented Workflow requires API evidence')
            if not evidence(row.get('MCP evidence')): errors.append(prefix+' implemented Workflow requires MCP evidence')
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
    workflow_rows=parse_markdown_table(lc/'WORKFLOW-MAP.md','Workflow ID') if (lc/'WORKFLOW-MAP.md').exists() else []
    ui_rows=parse_markdown_table(lc/'UI-MAP.md','UI ID') if (lc/'UI-MAP.md').exists() else []
    simulation_rows=parse_markdown_table(lc/'SIMULATION-WORLD.md','Simulation ID') if (lc/'SIMULATION-WORLD.md').exists() else []
    handoff=lc/'PRODUCT-BASELINE-HANDOFF.md'; handoff_errors=[]
    if handoff.exists():
        handoff_fields=parse_markdown_fields(handoff)
        if str(handoff_fields.get('Handoff status','')).strip().upper()!='COMPLETE':
            handoff_errors.append('Product Baseline Handoff status must be COMPLETE')
        repository=canonical_github_repository(handoff_fields.get('Project repository identity'))
        project_repository=canonical_github_repository(start.get('repository'))
        if not repository or (project_repository and repository!=project_repository):
            handoff_errors.append('Product Baseline Handoff must use the total project repository')
        frozen_commit=handoff_fields.get('Project frozen exact commit SHA','')
        handoff_errors.extend(validate_workflow_subtrees(workflow_rows,Path(args.project),frozen_commit))
        handoff_errors.extend(validate_product_subtree_baseline(
            parse_markdown_table(handoff,'Subtree type'),
            handoff_fields.get('Primary product mainline ID'),
            handoff_fields.get('Primary mainline Owner confirmation'),
            Path(args.project),
            frozen_commit,
            workflow_rows,
            ui_rows,
            simulation_rows,
            {
                'Workflow':parse_markdown_fields(lc/'WORKFLOW-MAP.md').get('Primary product mainline ID') if (lc/'WORKFLOW-MAP.md').exists() else None,
                'UI':parse_markdown_fields(lc/'UI-MAP.md').get('Primary product mainline ID') if (lc/'UI-MAP.md').exists() else None,
                'Simulation':parse_markdown_fields(lc/'SIMULATION-WORLD.md').get('Primary product mainline ID') if (lc/'SIMULATION-WORLD.md').exists() else None,
            },
        ))
    else:
        errors.extend(validate_workflow_subtrees(workflow_rows))
    errors.extend(handoff_errors)
    if completed_evidence(status.get('product_baseline')):
        if not handoff.exists():
            errors.append('accepted Product Baseline requires PRODUCT-BASELINE-HANDOFF.md')
        elif handoff_errors:
            errors.append('accepted Product Baseline requires a mechanically valid and COMPLETE Product Baseline Handoff')
    if status.get('active_slice'):
        slice_path=resolve_active_slice(lc,status.get('active_slice'))
        if not slice_path: errors.append('active Slice artifact missing')
        else:
            fields=parse_markdown_fields(slice_path)
            errors.extend(validate_slice_execution_preflight(fields,fingerprint,start.get('repository')))
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
        errors.extend(validate_run_evidence(lc,status,manifest,lock,manifest_path))
    if (Path(args.project)/'VERSION').exists():
        if not (Path(args.project)/'VERSION').read_text().strip(): errors.append('empty VERSION')
    elif start.get('initialization_mode','NEW')=='NEW': errors.append('missing project VERSION')
    if errors:
        print('FAIL'); print('\n'.join(errors)); raise SystemExit(1)
    print('PASS')
if __name__=='__main__': main()
