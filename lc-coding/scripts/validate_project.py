#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re

REQUIRED=['PROJECT-START.json','OWNER-POLICY.md','PROJECT-PROFILE.md','PROJECT-FINGERPRINT.json','PROJECT-HEALTH.json','AGENT-RULE.md','CANONICAL-MANIFEST.json','INTERPRETATION-LOCK.json','WORKFLOW-MAP.md','UI-MAP.md','SIMULATION-WORLD.md','status.json','PHASE-STATUS.json']
COMPLEXITY_FACTORS=['product_uncertainty','system_coupling','real_risk','irreversibility','novelty']
COMPLEXITY_LEVELS={'LOW','MEDIUM','HIGH','UNKNOWN'}
RUNTIME_STATUS_FIELDS={'session','session_id','process','process_id','pid','agent','agent_id','queue','retry','retries','attempt','orchestration','model','effort','hook','cli'}
SLICE_INTERNAL_METHOD_FIELDS={'go plan','cell tasks','stage plan','wave','agent model','task graph','retry queue'}
SLICE_PREFLIGHT_REQUIRED=['Actor intent','Product outcome','Product Baseline trace','Workflow references','UI references','Scenario IDs / versions','State / data / permission trace','Exception / recovery trace','Impact Analysis ID','Integration Baseline ID','Required Run IDs','D0-D3 evidence plan','Normal Loop Owner Acceptance route(s)']
OPEN_GAP_INDEX_FIELDS={'gap_id','state','source_acceptance','evidence_pointers'}

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

def validate_ui_private_baseline_preflight(fields,product_repository=None):
    errors=[]
    repository_and_path=str(fields.get('UI independent GitHub repository / baseline path(s)','')).strip()
    repository_text,separator,baseline_path=repository_and_path.partition('::')
    repository=canonical_github_repository(repository_text.strip())
    if not repository or not separator or not present(baseline_path.strip()):
        errors.append('UI baseline requires an independent GitHub repository and baseline path')
    product=canonical_github_repository(product_repository)
    if not product:
        errors.append('product repository identity is required to prove UI repository independence')
    elif repository and repository==product:
        errors.append('UI baseline repository must be independent from the product repository')
    private=str(fields.get('UI Owner-control / PRIVATE evidence','')).strip()
    private_match=re.fullmatch(
        r'PRIVATE:\s*(\S.*?)\s*\|\s*OWNER_CONTROLLED:\s*(\S.*)',private,re.IGNORECASE
    )
    if not private_match:
        errors.append('UI baseline requires Owner-control and PRIVATE evidence pointer')
    commit=str(fields.get('UI frozen exact remote commit SHA','')).strip()
    if not re.fullmatch(r'(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})',commit):
        errors.append('UI baseline requires a full exact remote commit SHA')
    content_hash=str(fields.get('UI content hash','')).strip()
    if not re.fullmatch(r'sha256:[0-9a-fA-F]{64}',content_hash,re.IGNORECASE):
        errors.append('UI baseline requires an exact SHA-256 content hash')
    hash_scope=str(fields.get('UI content hash scope / manifest evidence','')).strip()
    if not hash_scope.upper().startswith('HASH_SCOPE:') or not hash_scope.split(':',1)[1].strip():
        errors.append('UI baseline requires deterministic content hash scope evidence')
    remote=str(fields.get('UI remote commit push / resolve evidence','')).strip()
    if not remote.upper().startswith('REMOTE_RESOLVED:') or not remote.split(':',1)[1].strip():
        errors.append('UI baseline requires remote commit push and resolve evidence')
    recovery=str(fields.get('UI recovery reference','')).strip()
    if not recovery.upper().startswith('RECOVERY:') or not recovery.split(':',1)[1].strip():
        errors.append('UI baseline requires a recovery reference')
    identity=str(fields.get('UI Product / Integration Baseline identity','')).strip()
    if not identity.upper().startswith('MATCH:') or not identity.split(':',1)[1].strip():
        errors.append('UI Product and Integration Baseline identity must MATCH with evidence')
    comparison=str(fields.get('UI baseline comparison before Slice / Run','')).strip()
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
    errors.extend(validate_ui_private_baseline_preflight(fields,product_repository))
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
