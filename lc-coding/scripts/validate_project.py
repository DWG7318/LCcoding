#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json, re, subprocess

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
    errors=[]
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
    if phase_status.get('current_phase')!=status.get('current_phase'):
        errors.append('derived phase status disagrees with authoritative current_phase')
    gate_map={
        'INITIAL':('exit_gate','INITIAL_READY'),
        'PRODUCT_FORMATION':('exit_gate','CALABASH_UPGRADE_READY'),
        'ENGINEERING_RUNS':('aggregate_exit_gate','ALL_REQUIRED_RUNS_ACCEPTED'),
        'DELIVERY_PREPARATION':('exit_gate','DELIVERY_READY'),
    }
    for phase,(field,gate) in gate_map.items():
        derived=phase_status.get('phases',{}).get(phase,{}).get(field)
        authoritative=status.get('phase_gates',{}).get(gate)
        if derived!=authoritative:
            errors.append(f'derived phase status disagrees with authoritative gate {gate}')
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
    handoff=lc/'PRODUCT-BASELINE-HANDOFF.md'
    if handoff.exists():
        handoff_fields=parse_markdown_fields(handoff)
        repository=canonical_github_repository(handoff_fields.get('Project repository identity'))
        project_repository=canonical_github_repository(start.get('repository'))
        if not repository or (project_repository and repository!=project_repository):
            errors.append('Product Baseline Handoff must use the total project repository')
        frozen_commit=handoff_fields.get('Project frozen exact commit SHA','')
        errors.extend(validate_workflow_subtrees(workflow_rows,Path(args.project),frozen_commit))
        errors.extend(validate_product_subtree_baseline(
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
    if (lc/'INTERPRETATION-LOCK.json').exists():
        lock=json.loads((lc/'INTERPRETATION-LOCK.json').read_text(encoding='utf-8'))
        if lock.get('status')!='VALID': errors.append('Interpretation Lock is not VALID')
    if (Path(args.project)/'VERSION').exists():
        if not (Path(args.project)/'VERSION').read_text().strip(): errors.append('empty VERSION')
    elif start.get('initialization_mode','NEW')=='NEW': errors.append('missing project VERSION')
    if errors:
        print('FAIL'); print('\n'.join(errors)); raise SystemExit(1)
    print('PASS')
if __name__=='__main__': main()
