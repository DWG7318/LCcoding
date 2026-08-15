#!/usr/bin/env python3
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, re
from datetime import datetime, timezone, timedelta

CONTRACT_PATH=Path(__file__).resolve().parents[1]/'contracts/agent-configuration-baseline.json'
CONTRACT=json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))
ACTION_CONTRACT_PATH=Path(__file__).resolve().parents[1]/'contracts/agent-action-catalog.json'
ACTION_CONTRACT=json.loads(ACTION_CONTRACT_PATH.read_text(encoding='utf-8'))
RUNTIME_CONTRACT_PATH=Path(__file__).resolve().parents[1]/'contracts/runtime-adapter-attestation.json'
RUNTIME_CONTRACT=json.loads(RUNTIME_CONTRACT_PATH.read_text(encoding='utf-8'))
TOPOLOGY_CONTRACT_PATH=Path(__file__).resolve().parents[1]/'contracts/production-execution-topology.json'
TOPOLOGY_CONTRACT=json.loads(TOPOLOGY_CONTRACT_PATH.read_text(encoding='utf-8'))
TOP=set(CONTRACT['top_level_fields'])
SHAREABLE_KINDS=tuple(CONTRACT['shareable_identity_kinds'])
PRIVATE_KINDS=tuple(CONTRACT['private_identity_kinds'])
KINDS=SHAREABLE_KINDS+PRIVATE_KINDS
AGENT_FIELDS={'applicability','agent_id'}|{suffix for kind in KINDS for suffix in (kind+'_id',kind+'_hash')}
ROOT_FIELDS={'authority_flow','root_authority_id','root_authority_hash','scorpion_policy_id','scorpion_policy_hash','secrets_storage','runtime_permission'}
VERIFY_FIELDS={'verification_id','candidate_id','candidate_hash','configuration_baseline_id','independent_verifier_id','evidence_id','evidence_hash','result'}
ACCEPT_FIELDS={'acceptance_id','owner_id','candidate_id','candidate_hash','configuration_baseline_id','verification_id','result'}
SAFE=re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$')
HASH=re.compile(r'^sha256:[0-9a-f]{64}$')
GENERIC={'','NONE','PENDING','UNKNOWN','NOT_APPLICABLE','PASS','DONE','READY','TEST','FAKE','MOCK','STUB','TODO','TBD','COMPLETE','INVALID'}
SECRET=re.compile(r'(?i)(?:^sk-|^ghp_|password\s*=|secret\s*=|-----BEGIN .*PRIVATE KEY-----)')
RUNTIME_SECRET=re.compile(r'(?i)(?:^(?:AKIA|ASIA)[0-9A-Z]{16}$|^xox[baprs]-|^github_pat_|bearer\s+)')
SEMVER=re.compile(r'^[0-9]+\.[0-9]+\.[0-9]+$')
UTC=re.compile(r'^[0-9]{4}-(0[1-9]|1[0-2])-([012][0-9]|3[01])T([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]Z$')
CATALOG_TOP=set(ACTION_CONTRACT['top_level_fields'])
ACTION_FIELDS=set(ACTION_CONTRACT['action_fields'])
TARGET_FIELDS=set(ACTION_CONTRACT['target_fields'])
INPUT_FIELDS=set(ACTION_CONTRACT['input_schema_fields'])
CONDITION_FIELDS=set(ACTION_CONTRACT['condition_fields'])
AUTHORITY_FIELDS=set(ACTION_CONTRACT['authority_fields'])
ADAPTER_OPERATION_FIELDS=set(ACTION_CONTRACT['adapter_operation_fields'])
ACTION_VERIFY_FIELDS=set(ACTION_CONTRACT['verification_fields'])
ROLLBACK_FIELDS=set(ACTION_CONTRACT['rollback_fields'])
FREE_FORM_TOKENS={'SHELL','COMMAND','COMMANDS','POWERSHELL','BASH','CMD','EXEC','EXECUTE','EXECUTION','EVAL','DISCOVER','DISCOVERY','DYNAMIC','ARBITRARY'}
PREAUTH_FORBIDDEN_TOKENS={'DELETE','DELETION','PERMISSION','PERMISSIONS','RELEASE','UPGRADE','MIGRATE','MIGRATION','CREDENTIAL','CREDENTIALS','ROOT','KILL','IRREVERSIBLE'}
BROAD_TARGETS={'ALL','ANY','GLOBAL','BROAD','WILDCARD'}
RUNTIME_TOP=set(RUNTIME_CONTRACT['top_level_fields'])
RUNTIME_ADAPTER_FIELDS=set(RUNTIME_CONTRACT['runtime_adapter_fields'])
RUNTIME_PROVIDER_FIELDS=set(RUNTIME_CONTRACT['runtime_provider_fields'])
RUNTIME_CONFIGURATION_FIELDS=set(RUNTIME_CONTRACT['configuration_fields'])
RUNTIME_TOPOLOGY_FIELDS=set(RUNTIME_CONTRACT['topology_fields'])
RUNTIME_CAPABILITY_FIELDS=set(RUNTIME_CONTRACT['capability_fields'])
RUNTIME_AUTHORITY_FIELDS=set(RUNTIME_CONTRACT['authority_boundary_fields'])
RUNTIME_EVENT_FIELDS=set(RUNTIME_CONTRACT['typed_event_fields'])
RUNTIME_VALIDITY_FIELDS=set(RUNTIME_CONTRACT['validity_fields'])
RUNTIME_EVIDENCE_FIELDS=set(RUNTIME_CONTRACT['evidence_fields'])
RUNTIME_FALLBACK_FIELDS=set(RUNTIME_CONTRACT['fallback_fields'])
RUNTIME_KILL_SWITCH_FIELDS=set(RUNTIME_CONTRACT['kill_switch_fields'])
RUNTIME_CONFORMANCE_FIELDS=set(RUNTIME_CONTRACT['conformance_fields'])
EVENT_FORBIDDEN_VALUE=re.compile(r'(?i)(?:^|[._-])(?:RAW|PAYLOAD|SESSION|MEMORY|PROMPT|CREDENTIAL|SECRET|ADMIN_AUTHORIZATION|ADMINISTRATOR_AUTHORIZATION)(?:$|[._-])')
TOPOLOGY_TOP=set(TOPOLOGY_CONTRACT['top_level_fields'])
TOPOLOGY_PRODUCT_BASELINE_FIELDS=set(TOPOLOGY_CONTRACT['product_baseline_fields'])
TOPOLOGY_CONFIGURATION_FIELDS=set(TOPOLOGY_CONTRACT['configuration_fields'])
TOPOLOGY_MEMBER_FIELDS=set(TOPOLOGY_CONTRACT['member_fields'])
TOPOLOGY_DISPOSITION_FIELDS=set(TOPOLOGY_CONTRACT['disposition_fields'])
TOPOLOGY_DEPENDENCY_FIELDS=set(TOPOLOGY_CONTRACT['dependency_fields'])
TOPOLOGY_AUTHORITY_FIELDS=set(TOPOLOGY_CONTRACT['authority_fields'])
TOPOLOGY_ROUTE_FIELDS=set(TOPOLOGY_CONTRACT['route_fields'])
TOPOLOGY_EVIDENCE_FIELDS=set(TOPOLOGY_CONTRACT['evidence_fields'])
TOPOLOGY_VERIFICATION_FIELDS=set(TOPOLOGY_CONTRACT['verification_fields'])
PRODUCT_FORMATION_STATUS_FIELDS={
    'state','product_agent_applicability','calabash_definition_handoff_id',
    'calabash_definition_handoff_hash','configuration_baseline_id',
    'configuration_baseline_hash','product_agent_capability_state',
    'operations_agent_state',
}
UNPROVED_PRODUCT_FORMATION_STATUS={
    'state':'UNPROVED','product_agent_applicability':'UNPROVED',
    'calabash_definition_handoff_id':'NOT_APPLICABLE',
    'calabash_definition_handoff_hash':'NOT_APPLICABLE',
    'configuration_baseline_id':'NOT_APPLICABLE',
    'configuration_baseline_hash':'NOT_APPLICABLE',
    'product_agent_capability_state':'UNPROVED',
    'operations_agent_state':'UNPROVED',
}
PRODUCT_APPLICABILITY={'NOT_APPLICABLE','APPLICABLE_EXTRA','APPLICABLE_CORE'}
AGENT_RULE_FIELDS={
    'Agent Product applicability authority':'CALABASH_DEFINITION_HANDOFF',
    'Agent Product CORE proof':'REAL_RUNNABLE_WORKFLOW_API_MCP_SIMULATION',
    'Agent Product mock/prompt/demo substitution':'FORBIDDEN',
    'Agent Construction substitution':'FORBIDDEN',
    'Agent Operations Product Formation maximum':'PREPARED_NOT_INTEGRATED',
    'Agent Operations integration / execution / Slice claim':'FORBIDDEN',
    'Agent identity alias':'FORBIDDEN','Agent lifecycle effect':'NO_NEW_GATE',
}
AGENT_HANDOFF_FIELDS={
    'Agent Product Formation candidate ID / exact hash','Product Agent applicability',
    'Product Agent applicability Calabash basis','Agent Configuration Baseline ID / exact hash',
    'Product Agent ID','Product Agent capability state','Product Agent proof actor kind',
    'Product Agent Workflow Capability ID','Product Agent runnable evidence',
    'Product Agent API evidence','Product Agent MCP evidence',
    'Product Agent Simulation scenario/recovery evidence',
    'Product Agent Product Baseline ID / exact hash','Operations Agent ID',
    'Operations Agent Product Formation state','Operations Agent prepared configuration evidence',
    'Operations Agent prepared Action Catalog evidence','Operations Agent telemetry evidence',
    'Operations Agent audit evidence','Operations Agent fallback evidence',
    'Operations Agent Kill Switch evidence','Operations Agent Runtime Adapter requirement evidence',
    'Agent Product Formation result',
}
PRODUCT_PROOF_FIELDS={
    'Product Agent proof actor kind','Product Agent Workflow Capability ID',
    'Product Agent runnable evidence','Product Agent API evidence','Product Agent MCP evidence',
    'Product Agent Simulation scenario/recovery evidence',
    'Product Agent Product Baseline ID / exact hash',
}
PROOF_FORBIDDEN_TOKENS={'MOCK','STUB','PROMPT','DEMO','CONSTRUCTION'}

class DuplicateKeyError(ValueError): pass
def _pairs(pairs):
    out={}
    for key,value in pairs:
        if key in out: raise DuplicateKeyError('duplicate key')
        out[key]=value
    return out
def strict_json_bytes(raw):
    return json.loads(raw.decode('utf-8'),object_pairs_hook=_pairs,parse_constant=lambda value: (_ for _ in ()).throw(ValueError('non-finite number')))
def strict_json(path): return strict_json_bytes(Path(path).read_bytes())
def closed(value,fields,label,errors):
    if not isinstance(value,dict): errors.append(label+' must be an object'); return {}
    missing=fields-set(value); unknown=set(value)-fields
    if missing: errors.append(label+' missing fields '+', '.join(sorted(missing)))
    if unknown: errors.append(label+' unknown fields '+', '.join(sorted(unknown)))
    return value
def safe_id(value):
    if not isinstance(value,str): return False
    text=value.strip(); head=re.split(r'[._-]',text,1)[0].upper()
    return bool(SAFE.fullmatch(text)) and text.upper() not in GENERIC and head not in GENERIC and not SECRET.search(text)
def exact_hash(value): return isinstance(value,str) and bool(HASH.fullmatch(value))
def tokens(value): return set(re.findall(r'[A-Z0-9]+',str(value or '').upper()))
def forbidden_operation(value): return bool(tokens(value)&FREE_FORM_TOKENS)
def future_utc(value):
    if not isinstance(value,str) or not UTC.fullmatch(value): return False
    try: observed=datetime.strptime(value,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    except ValueError: return False
    return observed>datetime.now(timezone.utc)
def validate_agent(value,label,allowed,errors):
    record=closed(value,AGENT_FIELDS,label,errors); applicability=record.get('applicability')
    if applicability not in allowed: errors.append(label+' applicability is invalid')
    if applicability=='NOT_APPLICABLE':
        if any(record.get(field)!='NOT_APPLICABLE' for field in AGENT_FIELDS-{'applicability'}): errors.append(label+' NOT_APPLICABLE record must not claim identities')
        return None
    if not safe_id(record.get('agent_id')): errors.append(label+' agent_id requires a safe non-generic ID')
    for kind in KINDS:
        if not safe_id(record.get(kind+'_id')): errors.append(label+' '+kind+'_id is invalid')
        if not exact_hash(record.get(kind+'_hash')): errors.append(label+' '+kind+'_hash must be lowercase sha256')
    private_ids=[str(record.get(kind+'_id','')).casefold() for kind in PRIVATE_KINDS]
    if len(set(private_ids))!=len(PRIVATE_KINDS): errors.append(label+' private identity IDs must be unique')
    return record.get('agent_id')
def validate_configuration(value,expected_candidate_id=None,expected_candidate_hash=None):
    errors=[]; record=closed(value,TOP,'configuration baseline',errors)
    if record.get('schema_version')!='2.8.0': errors.append('schema_version must be 2.8.0')
    if record.get('artifact_role')!='AGENT_CONFIGURATION_BASELINE': errors.append('artifact_role is invalid')
    for field in ('configuration_baseline_id','candidate_id'):
        if not safe_id(record.get(field)): errors.append(field+' requires a safe non-generic ID')
    if not exact_hash(record.get('candidate_hash')): errors.append('candidate_hash must be lowercase sha256')
    if expected_candidate_id is not None and record.get('candidate_id')!=expected_candidate_id: errors.append('candidate_id disagrees with authoritative candidate')
    if expected_candidate_hash is not None and record.get('candidate_hash')!=expected_candidate_hash: errors.append('candidate_hash disagrees with authoritative candidate')
    root=closed(record.get('root_authority'),ROOT_FIELDS,'root_authority',errors)
    if root.get('authority_flow')!=CONTRACT['root_authority_flow']: errors.append('root authority flow is invalid')
    if root.get('secrets_storage')!='REFERENCES_ONLY_NO_INLINE_SECRETS' or root.get('runtime_permission')!='CANNOT_EXPAND_AUTHORITY': errors.append('root authority boundaries are invalid')
    for field in ('root_authority_id','scorpion_policy_id'):
        if not safe_id(root.get(field)): errors.append(field+' is invalid')
    for field in ('root_authority_hash','scorpion_policy_hash'):
        if not exact_hash(root.get(field)): errors.append(field+' must be lowercase sha256')
    operations_id=validate_agent(record.get('operations_agent'),'operations_agent',{'REQUIRED'},errors)
    product_id=validate_agent(record.get('product_agent'),'product_agent',set(CONTRACT['product_applicability']),errors)
    if operations_id and product_id and operations_id.casefold()==product_id.casefold(): errors.append('Product and Operations Agents must not alias')
    if operations_id and product_id:
        operations=record.get('operations_agent',{})
        product=record.get('product_agent',{})
        operations_private_ids={str(operations.get(kind+'_id','')).casefold() for kind in PRIVATE_KINDS}
        product_private_ids={str(product.get(kind+'_id','')).casefold() for kind in PRIVATE_KINDS}
        operations_private_hashes={operations.get(kind+'_hash') for kind in PRIVATE_KINDS}
        product_private_hashes={product.get(kind+'_hash') for kind in PRIVATE_KINDS}
        if operations_private_ids&product_private_ids: errors.append('Product and Operations private identity IDs must be disjoint')
        if operations_private_hashes&product_private_hashes: errors.append('Product and Operations private identity hashes must be disjoint')
    verification=closed(record.get('verification'),VERIFY_FIELDS,'verification',errors)
    acceptance=closed(record.get('owner_acceptance'),ACCEPT_FIELDS,'owner_acceptance',errors)
    for label,item,id_field in (('verification',verification,'verification_id'),('owner_acceptance',acceptance,'acceptance_id')):
        for field in (id_field,'candidate_id','configuration_baseline_id'):
            if not safe_id(item.get(field)): errors.append(label+' '+field+' is invalid')
        if not exact_hash(item.get('candidate_hash')): errors.append(label+' candidate_hash is invalid')
        if item.get('candidate_id')!=record.get('candidate_id') or item.get('candidate_hash')!=record.get('candidate_hash') or item.get('configuration_baseline_id')!=record.get('configuration_baseline_id'): errors.append(label+' must bind exact candidate and baseline')
    for field in ('independent_verifier_id','evidence_id'):
        if not safe_id(verification.get(field)): errors.append('verification '+field+' is invalid')
    verifier_id=verification.get('independent_verifier_id')
    if isinstance(verifier_id,str) and any(
        isinstance(agent_id,str) and verifier_id.casefold()==agent_id.casefold()
        for agent_id in (operations_id,product_id)
    ): errors.append('independent verifier must not be a configured Agent')
    if not exact_hash(verification.get('evidence_hash')) or verification.get('result')!='PASS': errors.append('independent verification is incomplete')
    if not safe_id(acceptance.get('owner_id')) or acceptance.get('verification_id')!=verification.get('verification_id') or acceptance.get('result')!='OWNER_ACCEPTED': errors.append('Owner acceptance is invalid')
    def secret_walk(item):
        if isinstance(item,dict): return any(secret_walk(v) for v in item.values())
        if isinstance(item,list): return any(secret_walk(v) for v in item)
        return isinstance(item,str) and bool(SECRET.search(item))
    if secret_walk(record): errors.append('inline secret-like value is forbidden')
    return errors
def validate_file(path,expected_candidate_id=None,expected_candidate_hash=None):
    try: return validate_configuration(strict_json(Path(path)),expected_candidate_id,expected_candidate_hash)
    except (OSError,UnicodeError,ValueError) as error: return ['Agent Configuration Baseline is not strict UTF-8 JSON: '+str(error)]

def validate_condition_list(value,label,errors):
    if not isinstance(value,list) or not value:
        errors.append(label+' must be a non-empty list'); return
    seen=set()
    for index,item in enumerate(value):
        record=closed(item,CONDITION_FIELDS,label+' item '+str(index+1),errors)
        for field in ('condition_id','evidence_schema_id'):
            if not safe_id(record.get(field)): errors.append(label+' '+field+' is invalid')
        if not exact_hash(record.get('evidence_schema_hash')): errors.append(label+' evidence_schema_hash is invalid')
        if record.get('result_required')!='PASS': errors.append(label+' result_required must be PASS')
        identity=record.get('condition_id')
        if isinstance(identity,str):
            normalized=identity.casefold()
            if normalized in seen: errors.append(label+' condition IDs must be unique')
            seen.add(normalized)

def validate_action_catalog(value,expected_catalog_id=None,expected_candidate_id=None,expected_candidate_hash=None,expected_baseline_id=None):
    errors=[]; record=closed(value,CATALOG_TOP,'action catalog',errors)
    if record.get('schema_version')!='2.8.0': errors.append('action catalog schema_version must be 2.8.0')
    if record.get('artifact_role')!='AGENT_ACTION_CATALOG': errors.append('action catalog artifact_role is invalid')
    for field in ('catalog_id','candidate_id','configuration_baseline_id'):
        if not safe_id(record.get(field)): errors.append('action catalog '+field+' is invalid')
    if not exact_hash(record.get('candidate_hash')): errors.append('action catalog candidate_hash is invalid')
    for field,expected in (
        ('catalog_id',expected_catalog_id),('candidate_id',expected_candidate_id),
        ('candidate_hash',expected_candidate_hash),('configuration_baseline_id',expected_baseline_id),
    ):
        if expected is not None and record.get(field)!=expected: errors.append('action catalog '+field+' disagrees with accepted identity')
    actions=record.get('actions')
    if not isinstance(actions,list) or not actions:
        errors.append('actions must be a non-empty list'); actions=[]
    action_ids=set()
    for index,item in enumerate(actions):
        label='action '+str(index+1); action=closed(item,ACTION_FIELDS,label,errors)
        action_id=action.get('action_id')
        if not safe_id(action_id): errors.append(label+' action_id is invalid')
        elif action_id.casefold() in action_ids: errors.append('action IDs must be unique')
        else: action_ids.add(action_id.casefold())
        if not isinstance(action.get('action_version'),str) or not SEMVER.fullmatch(action['action_version']): errors.append(label+' action_version is invalid')
        if not exact_hash(action.get('action_hash')): errors.append(label+' action_hash is invalid')
        if action.get('definition_authority') not in {'OWNER','CALABASH'}: errors.append(label+' definition authority must not be Agent-authored')
        if action.get('risk') not in ACTION_CONTRACT['risk_levels']: errors.append(label+' risk is invalid')
        target=closed(action.get('bounded_target'),TARGET_FIELDS,label+' bounded_target',errors)
        for field in TARGET_FIELDS:
            if not safe_id(target.get(field)): errors.append(label+' bounded_target '+field+' is invalid')
        if any(str(target.get(field) or '').upper() in BROAD_TARGETS for field in TARGET_FIELDS): errors.append(label+' bounded_target is broad')
        operation=action.get('operation')
        if not safe_id(operation) or forbidden_operation(operation): errors.append(label+' operation must be a deterministic catalog ID')
        input_schema=closed(action.get('input_schema'),INPUT_FIELDS,label+' input_schema',errors)
        if not safe_id(input_schema.get('schema_id')) or not exact_hash(input_schema.get('schema_hash')): errors.append(label+' typed input schema identity is invalid')
        validate_condition_list(action.get('preconditions'),label+' preconditions',errors)
        validate_condition_list(action.get('postconditions'),label+' postconditions',errors)
        authority=closed(action.get('authority'),AUTHORITY_FIELDS,label+' authority',errors)
        mode=authority.get('mode')
        if mode not in ACTION_CONTRACT['authority_modes']: errors.append(label+' authority mode is invalid')
        for field in ('item_id','evidence_id','target_id','scope_id'):
            if not safe_id(authority.get(field)): errors.append(label+' authority '+field+' is invalid')
        if not exact_hash(authority.get('evidence_hash')): errors.append(label+' authority evidence_hash is invalid')
        if authority.get('target_id')!=target.get('target_id') or authority.get('scope_id')!=target.get('scope_id'): errors.append(label+' authority target/scope is not exact')
        if mode=='OWNER_APPROVAL_REQUIRED':
            if authority.get('author_kind')!='OWNER' or authority.get('result')!='OWNER_APPROVED' or authority.get('expires_at')!='NOT_APPLICABLE': errors.append(label+' Owner approval evidence is invalid')
        if mode=='CALABASH_PREAUTHORIZED_BOUNDED':
            surface=tokens(operation)|tokens(target.get('target_id'))|tokens(target.get('target_kind'))|tokens(target.get('scope_id'))
            if authority.get('author_kind')!='CALABASH' or authority.get('result')!='CALABASH_PREAUTHORIZED': errors.append(label+' Calabash pre-authorization evidence is invalid')
            if action.get('risk')!='LOW': errors.append(label+' pre-authorization requires LOW risk')
            if not future_utc(authority.get('expires_at')): errors.append(label+' pre-authorization expiry is invalid or expired')
            if surface&PREAUTH_FORBIDDEN_TOKENS: errors.append(label+' pre-authorization covers a forbidden action class')
        adapter=closed(action.get('adapter_operation'),ADAPTER_OPERATION_FIELDS,label+' adapter_operation',errors)
        if not safe_id(adapter.get('operation_id')) or forbidden_operation(adapter.get('operation_id')) or adapter.get('determinism')!='DETERMINISTIC': errors.append(label+' Adapter operation is not deterministic')
        verification=closed(action.get('verification'),ACTION_VERIFY_FIELDS,label+' verification',errors)
        for field in ('verification_id','evidence_schema_id'):
            if not safe_id(verification.get(field)): errors.append(label+' verification '+field+' is invalid')
        if not exact_hash(verification.get('evidence_schema_hash')) or verification.get('result_required')!='PASS': errors.append(label+' verification contract is incomplete')
        rollback=closed(action.get('rollback'),ROLLBACK_FIELDS,label+' rollback',errors)
        if not safe_id(rollback.get('operation_id')) or forbidden_operation(rollback.get('operation_id')) or rollback.get('trigger')!='VERIFICATION_FAIL' or rollback.get('result')!='AVAILABLE': errors.append(label+' rollback is incomplete')
        if action.get('audit_events')!=ACTION_CONTRACT['audit_events']: errors.append(label+' audit events are incomplete or unordered')
        timeout=action.get('timeout_seconds'); retries=action.get('max_retries')
        if isinstance(timeout,bool) or not isinstance(timeout,int) or not 1<=timeout<=3600: errors.append(label+' timeout is invalid')
        if isinstance(retries,bool) or not isinstance(retries,int) or not 0<=retries<=3: errors.append(label+' retry bound is invalid')
    if isinstance(record,dict) and any(SECRET.search(item) for item in _strings(record)): errors.append('action catalog contains a secret-like inline value')
    return errors

def _strings(value):
    if isinstance(value,dict):
        for item in value.values(): yield from _strings(item)
    elif isinstance(value,list):
        for item in value: yield from _strings(item)
    elif isinstance(value,str): yield value

def strict_utc(value):
    if not isinstance(value,str) or not UTC.fullmatch(value): return None
    try: return datetime.strptime(value,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    except ValueError: return None

def contained_evidence_path(value):
    if not isinstance(value,str) or not value or '\\' in value or ':' in value: return False
    path=PurePosixPath(value)
    return (
        not path.is_absolute() and str(path)==value and len(path.parts)>=2
        and path.parts[0]=='evidence' and all(part not in {'','.','..'} for part in path.parts)
    )

def validate_production_topology(
    value,configuration,configuration_hash,
    expected_product_baseline_id,expected_product_baseline_hash,
):
    errors=validate_configuration(configuration)
    config=configuration if isinstance(configuration,dict) else {}
    record=closed(value,TOPOLOGY_TOP,'Production Execution Topology',errors)
    if record.get('schema_version')!='2.8.0': errors.append('Production Execution Topology schema_version must be 2.8.0')
    if record.get('artifact_role')!='PRODUCTION_EXECUTION_TOPOLOGY': errors.append('Production Execution Topology artifact_role is invalid')
    for field in ('topology_id','candidate_id'):
        if not safe_id(record.get(field)): errors.append('Production Execution Topology '+field+' is invalid')
    if not exact_hash(record.get('candidate_hash')): errors.append('Production Execution Topology candidate_hash is invalid')
    if record.get('candidate_id')!=config.get('candidate_id') or record.get('candidate_hash')!=config.get('candidate_hash'): errors.append('Production Execution Topology candidate identity disagrees with configuration')

    baseline=closed(record.get('product_baseline'),TOPOLOGY_PRODUCT_BASELINE_FIELDS,'product_baseline',errors)
    if not safe_id(baseline.get('product_baseline_id')) or not exact_hash(baseline.get('product_baseline_hash')): errors.append('Product Baseline identity is invalid')
    if not safe_id(expected_product_baseline_id) or not exact_hash(expected_product_baseline_hash): errors.append('expected Product Baseline identity is invalid')
    if baseline.get('product_baseline_id')!=expected_product_baseline_id or baseline.get('product_baseline_hash')!=expected_product_baseline_hash: errors.append('Production Execution Topology Product Baseline identity disagrees')
    configuration_baseline=closed(record.get('configuration_baseline'),TOPOLOGY_CONFIGURATION_FIELDS,'configuration_baseline',errors)
    if not safe_id(configuration_baseline.get('configuration_baseline_id')) or not exact_hash(configuration_baseline.get('configuration_baseline_hash')): errors.append('Agent Configuration Baseline topology identity is invalid')
    if not exact_hash(configuration_hash): errors.append('accepted Agent Configuration Baseline file hash is invalid')
    if configuration_baseline.get('configuration_baseline_id')!=config.get('configuration_baseline_id') or configuration_baseline.get('configuration_baseline_hash')!=configuration_hash: errors.append('Production Execution Topology configuration identity disagrees')

    members=record.get('discovered_members')
    if not isinstance(members,list) or not members:
        errors.append('discovered_members must be a non-empty list'); members=[]
    member_ids=[]; member_hashes=set()
    for index,item in enumerate(members):
        label='discovered member '+str(index+1)
        member=closed(item,TOPOLOGY_MEMBER_FIELDS,label,errors)
        identity=member.get('member_id')
        if not safe_id(identity): errors.append(label+' member_id is invalid')
        elif identity in member_ids: errors.append('discovered member IDs must be unique')
        else: member_ids.append(identity)
        if member.get('member_kind') not in TOPOLOGY_CONTRACT['member_kinds']: errors.append(label+' member_kind is invalid')
        identity_hash=member.get('identity_hash')
        if not exact_hash(identity_hash): errors.append(label+' identity_hash is invalid')
        elif identity_hash in member_hashes: errors.append('discovered member hashes must be unique')
        else: member_hashes.add(identity_hash)
    member_set=set(member_ids)

    dispositions=record.get('dispositions')
    if not isinstance(dispositions,list): errors.append('dispositions must be a list'); dispositions=[]
    disposition_by_member={}; disposition_ids=[]
    for index,item in enumerate(dispositions):
        label='member disposition '+str(index+1)
        disposition=closed(item,TOPOLOGY_DISPOSITION_FIELDS,label,errors)
        identity=disposition.get('member_id'); result=disposition.get('disposition')
        if identity not in member_set: errors.append(label+' references an unknown member')
        if identity in disposition_by_member: errors.append('each discovered member must have exactly one disposition')
        else: disposition_by_member[identity]=result
        disposition_ids.append(identity)
        if result not in TOPOLOGY_CONTRACT['dispositions']: errors.append(label+' disposition is invalid')
    if len(disposition_ids)!=len(set(disposition_ids)) or set(disposition_ids)!=member_set: errors.append('disposition member set must exactly equal discovered member set')
    active={identity for identity,result in disposition_by_member.items() if result!='RETIRE'}
    active_results=[disposition_by_member.get(identity) for identity in active]
    valid_selection=(len(active)==1 and set(active_results)=={'SELECT'})
    valid_composition=(len(active)>=2 and set(active_results)=={'COMPOSE'})
    valid_federation=(len(active)>=2 and set(active_results)=={'FEDERATE'})
    if not (valid_selection or valid_composition or valid_federation): errors.append('active member dispositions do not resolve to one SELECT, COMPOSE, or FEDERATE topology')

    dependencies=record.get('dependencies')
    if not isinstance(dependencies,list): errors.append('dependencies must be a list'); dependencies=[]
    dependency_keys=set(); edge_pairs=set(); graph={identity:set() for identity in active}
    for index,item in enumerate(dependencies):
        label='topology dependency '+str(index+1)
        dependency=closed(item,TOPOLOGY_DEPENDENCY_FIELDS,label,errors)
        source=dependency.get('source_member_id'); target=dependency.get('target_member_id'); kind=dependency.get('edge_kind')
        if source not in member_set or target not in member_set: errors.append(label+' references an unknown member')
        if source==target: errors.append(label+' must not self-reference')
        if source not in active or target not in active: errors.append(label+' must only join active members')
        if kind not in TOPOLOGY_CONTRACT['edge_kinds']: errors.append(label+' edge_kind is invalid')
        key=(source,target,kind)
        if key in dependency_keys: errors.append('topology dependencies must be unique')
        else: dependency_keys.add(key)
        if source in active and target in active and source!=target:
            graph[source].add(target); edge_pairs.add((source,target))
    visiting=set(); visited=set()
    def visit(identity):
        if identity in visiting: return False
        if identity in visited: return True
        visiting.add(identity)
        if any(not visit(target) for target in graph.get(identity,set())): return False
        visiting.remove(identity); visited.add(identity); return True
    if any(not visit(identity) for identity in active): errors.append('active topology dependencies must be acyclic')

    authorities=record.get('logical_authorities')
    if not isinstance(authorities,list): errors.append('logical_authorities must be a list'); authorities=[]
    domains=[]; authority_by_domain={}
    for index,item in enumerate(authorities):
        label='logical authority '+str(index+1)
        authority=closed(item,TOPOLOGY_AUTHORITY_FIELDS,label,errors)
        domain=authority.get('domain'); identity=authority.get('authority_member_id')
        domains.append(domain)
        if domain in authority_by_domain: errors.append('each logical authority domain must have exactly one authority')
        else: authority_by_domain[domain]=identity
        if domain not in TOPOLOGY_CONTRACT['authority_domains']: errors.append(label+' domain is invalid')
        if identity not in active: errors.append(label+' authority must be one active discovered member')
    if domains!=TOPOLOGY_CONTRACT['authority_domains']: errors.append('logical authority domains are incomplete, duplicated, unknown, or unordered')

    routes=record.get('routes')
    if not isinstance(routes,list): errors.append('routes must be a list'); routes=[]
    route_kinds=[]
    expected_agents={
        'PRODUCT':config.get('product_agent',{}),
        'OPERATIONS':config.get('operations_agent',{}),
    }
    calling_authority=authority_by_domain.get('calling')
    for index,item in enumerate(routes):
        label='production route '+str(index+1)
        route=closed(item,TOPOLOGY_ROUTE_FIELDS,label,errors)
        kind=route.get('route_kind'); route_kinds.append(kind)
        agent=expected_agents.get(kind,{}) if kind in expected_agents else {}
        if kind not in TOPOLOGY_CONTRACT['route_kinds']: errors.append(label+' route_kind is invalid')
        product_not_applicable=(kind=='PRODUCT' and agent.get('applicability')=='NOT_APPLICABLE')
        for field in ('agent_id','configuration_id'):
            if product_not_applicable:
                if route.get(field)!='NOT_APPLICABLE': errors.append(label+' '+field+' must be NOT_APPLICABLE')
            elif not safe_id(route.get(field)): errors.append(label+' '+field+' is invalid')
        if product_not_applicable:
            if route.get('configuration_hash')!='NOT_APPLICABLE': errors.append(label+' configuration_hash must be NOT_APPLICABLE')
        elif not exact_hash(route.get('configuration_hash')): errors.append(label+' configuration_hash is invalid')
        if any(route.get(field)!=agent.get(field) for field in ('agent_id','configuration_id','configuration_hash')): errors.append(label+' Agent/configuration identity disagrees with accepted baseline')
        if route.get('candidate_id')!=record.get('candidate_id') or route.get('candidate_hash')!=record.get('candidate_hash'): errors.append(label+' candidate identity disagrees')
        if route.get('calling_authority_member_id')!=calling_authority: errors.append(label+' calling authority disagrees')
        path=route.get('member_path')
        if not isinstance(path,list) or not path: errors.append(label+' member_path must be non-empty'); path=[]
        if len(path)!=len(set(path)): errors.append(label+' member_path must not repeat a member')
        if any(identity not in active for identity in path): errors.append(label+' member_path must contain only active discovered members')
        if calling_authority not in path: errors.append(label+' member_path must include the calling authority')
        if any((source,target) not in edge_pairs for source,target in zip(path,path[1:])): errors.append(label+' member_path is not joined by declared directed dependencies')
    if route_kinds!=TOPOLOGY_CONTRACT['route_kinds']: errors.append('Product and Operations routes are incomplete, duplicated, unknown, or unordered')

    evidence=record.get('evidence')
    if not isinstance(evidence,list) or not evidence:
        errors.append('Production Execution Topology evidence must be a non-empty list'); evidence=[]
    evidence_ids=[]; evidence_paths=set()
    for index,item in enumerate(evidence):
        label='topology evidence '+str(index+1)
        proof=closed(item,TOPOLOGY_EVIDENCE_FIELDS,label,errors)
        identity=proof.get('evidence_id'); path=proof.get('evidence_path')
        if not safe_id(identity): errors.append(label+' evidence_id is invalid')
        elif identity in evidence_ids: errors.append('topology evidence IDs must be unique')
        else: evidence_ids.append(identity)
        if not contained_evidence_path(path): errors.append(label+' path is not contained')
        elif path.casefold() in evidence_paths: errors.append('topology evidence paths must be unique')
        else: evidence_paths.add(path.casefold())
        if not exact_hash(proof.get('evidence_hash')): errors.append(label+' hash is invalid')
        if proof.get('producer_kind')!='INDEPENDENT_VERIFIER' or proof.get('independence')!='INDEPENDENT' or proof.get('result')!='PASS': errors.append(label+' is not independent PASS evidence')
    verification=closed(record.get('verification'),TOPOLOGY_VERIFICATION_FIELDS,'topology verification',errors)
    for field in ('verification_id','independent_verifier_id'):
        if not safe_id(verification.get(field)): errors.append('topology verification '+field+' is invalid')
    if verification.get('candidate_id')!=record.get('candidate_id') or verification.get('candidate_hash')!=record.get('candidate_hash'): errors.append('topology verification candidate identity disagrees')
    if verification.get('topology_id')!=record.get('topology_id'): errors.append('topology verification identity disagrees')
    if verification.get('evidence_ids')!=evidence_ids: errors.append('topology verification must bind every independent evidence item exactly once and in order')
    if verification.get('result')!='PASS': errors.append('topology verification result must be exact PASS')
    if any(SECRET.search(item) or RUNTIME_SECRET.search(item) for item in _strings(record)): errors.append('Production Execution Topology contains secret-like inline material')
    return errors

def validate_production_topology_file(
    path,configuration,configuration_hash,
    expected_product_baseline_id,expected_product_baseline_hash,
):
    target=Path(path)
    if target.is_symlink() or not target.is_file(): return ['Production Execution Topology must be a regular file']
    try: value=strict_json_bytes(target.read_bytes())
    except (OSError,UnicodeError,ValueError) as error: return ['Production Execution Topology is not strict UTF-8 JSON: '+str(error)]
    return validate_production_topology(
        value,configuration,configuration_hash,
        expected_product_baseline_id,expected_product_baseline_hash,
    )

def validate_typed_event_attestations(
    value,configuration,candidate_id,candidate_hash,
    observed_at_utc,validated_at_utc,as_of_utc,
):
    errors=validate_configuration(configuration)
    config=configuration if isinstance(configuration,dict) else {}
    product=config.get('product_agent',{}) if isinstance(config.get('product_agent'),dict) else {}
    operations=config.get('operations_agent',{}) if isinstance(config.get('operations_agent'),dict) else {}
    if product.get('applicability')=='NOT_APPLICABLE':
        if value!=[]: errors.append('typed event attestations must be empty when Product Agent is not applicable')
        return errors
    if not isinstance(value,list):
        errors.append('typed_event_attestations must be a list'); return errors
    if len(value)!=len(RUNTIME_CONTRACT['event_kinds']):
        errors.append('typed event attestations must contain each allowed event exactly once')
    expected={
        'MAINTENANCE_REQUEST':(product,operations),
        'SERVICE_STATUS_UPDATE':(operations,product),
    }
    observed=strict_utc(observed_at_utc); validated=strict_utc(validated_at_utc); as_of=strict_utc(as_of_utc)
    if observed is None or validated is None or as_of is None or not observed<=validated<=as_of:
        errors.append('typed event attestation time window is invalid')
    kinds=[]; event_ids=set(); schema_ids=set(); provenance_ids=set()
    for index,item in enumerate(value):
        label='typed event attestation '+str(index+1)
        event=closed(item,RUNTIME_EVENT_FIELDS,label,errors)
        kind=event.get('event_kind'); kinds.append(kind)
        for field,seen in (
            ('event_id',event_ids),('event_schema_id',schema_ids),
            ('provenance_id',provenance_ids),
        ):
            identity=event.get(field)
            if not safe_id(identity): errors.append(label+' '+field+' is invalid')
            elif identity.casefold() in seen: errors.append('typed event '+field+' values must be unique')
            else: seen.add(identity.casefold())
        for field in ('source_agent_id','target_agent_id','policy_id'):
            if not safe_id(event.get(field)): errors.append(label+' '+field+' is invalid')
        for field in ('event_schema_hash','provenance_hash','policy_hash'):
            if not exact_hash(event.get(field)): errors.append(label+' '+field+' is invalid')
        source,target=expected.get(kind,({},{}))
        if kind not in expected: errors.append(label+' event_kind is invalid')
        if event.get('source_agent_id')==event.get('target_agent_id'): errors.append(label+' source and target Agents must differ')
        if event.get('source_agent_id')!=source.get('agent_id') or event.get('target_agent_id')!=target.get('agent_id'): errors.append(label+' direction disagrees with accepted Agent roles')
        if event.get('candidate_id')!=candidate_id or event.get('candidate_hash')!=candidate_hash: errors.append(label+' candidate identity disagrees')
        if event.get('candidate_id')!=config.get('candidate_id') or event.get('candidate_hash')!=config.get('candidate_hash'): errors.append(label+' candidate identity disagrees with configuration')
        if event.get('policy_id')!=source.get('policy_id') or event.get('policy_hash')!=source.get('policy_hash'): errors.append(label+' Policy identity disagrees with source Agent')
        if event.get('payload_classification')!='MINIMAL_NON_SENSITIVE_METADATA': errors.append(label+' payload classification is invalid')
        if event.get('policy_result')!='PASS' or event.get('redaction_result')!='PASS': errors.append(label+' Policy and redaction results must be exact PASS')
        event_at=strict_utc(event.get('event_at_utc'))
        if event_at is None: errors.append(label+' event_at_utc must be strict UTC')
        elif observed is not None and validated is not None and not observed<=event_at<=validated: errors.append(label+' timestamp is outside the attested observation window')
        if any(EVENT_FORBIDDEN_VALUE.search(item) or SECRET.search(item) or RUNTIME_SECRET.search(item) for item in _strings(event)): errors.append(label+' contains raw, privileged, or secret-like material')
    if kinds!=RUNTIME_CONTRACT['event_kinds']:
        errors.append('typed event kinds are incomplete, duplicated, unknown, or unordered')
    return errors

def validate_runtime_adapter_attestation(
    value,configuration,configuration_hash,expected_topology_id,
    expected_topology_hash,as_of_utc,
):
    errors=validate_configuration(configuration)
    config=configuration if isinstance(configuration,dict) else {}
    record=closed(value,RUNTIME_TOP,'Runtime Adapter Attestation',errors)
    if record.get('schema_version')!='2.8.0': errors.append('Runtime Adapter Attestation schema_version must be 2.8.0')
    if record.get('artifact_role')!='RUNTIME_ADAPTER_ATTESTATION': errors.append('Runtime Adapter Attestation artifact_role is invalid')
    for field in ('attestation_id','candidate_id'):
        if not safe_id(record.get(field)): errors.append('Runtime Adapter Attestation '+field+' is invalid')
    if not exact_hash(record.get('candidate_hash')): errors.append('Runtime Adapter Attestation candidate_hash is invalid')
    if record.get('candidate_id')!=config.get('candidate_id') or record.get('candidate_hash')!=config.get('candidate_hash'): errors.append('Runtime Adapter Attestation candidate identity disagrees with configuration')

    adapter=closed(record.get('runtime_adapter'),RUNTIME_ADAPTER_FIELDS,'runtime_adapter',errors)
    if not safe_id(adapter.get('adapter_id')): errors.append('runtime_adapter adapter_id is invalid')
    if not isinstance(adapter.get('adapter_version'),str) or not SEMVER.fullmatch(adapter.get('adapter_version','')): errors.append('runtime_adapter version is invalid')
    if not exact_hash(adapter.get('adapter_digest')): errors.append('runtime_adapter digest must be lowercase sha256')

    provider=closed(record.get('runtime_provider'),RUNTIME_PROVIDER_FIELDS,'runtime_provider',errors)
    for field in ('provider_id','identity_evidence_id'):
        if not safe_id(provider.get(field)): errors.append('runtime_provider '+field+' is invalid')
    if provider.get('provider_kind') not in RUNTIME_CONTRACT['provider_kinds']: errors.append('runtime_provider kind is invalid')
    if not exact_hash(provider.get('identity_evidence_hash')) or provider.get('verification_result')!='PASS': errors.append('runtime_provider requires independently verified identity evidence')

    baseline=closed(record.get('configuration_baseline'),RUNTIME_CONFIGURATION_FIELDS,'configuration_baseline',errors)
    if not safe_id(baseline.get('configuration_baseline_id')) or not exact_hash(baseline.get('configuration_baseline_hash')): errors.append('configuration_baseline identity is invalid')
    if not exact_hash(configuration_hash): errors.append('accepted configuration file hash is invalid')
    if baseline.get('configuration_baseline_id')!=config.get('configuration_baseline_id') or baseline.get('configuration_baseline_hash')!=configuration_hash: errors.append('Runtime Adapter Attestation configuration identity disagrees with accepted baseline')

    topology=closed(record.get('production_topology'),RUNTIME_TOPOLOGY_FIELDS,'production_topology',errors)
    if not safe_id(topology.get('production_topology_id')) or not exact_hash(topology.get('production_topology_hash')): errors.append('production_topology opaque identity is invalid')
    if not safe_id(expected_topology_id) or not exact_hash(expected_topology_hash): errors.append('expected production topology identity is invalid')
    if topology.get('production_topology_id')!=expected_topology_id or topology.get('production_topology_hash')!=expected_topology_hash: errors.append('Runtime Adapter Attestation topology identity disagrees')
    if record.get('loaded_result')!='PASS': errors.append('loaded_result must be exact PASS')

    expected_agents={'OPERATIONS_AGENT':config.get('operations_agent',{})}
    product=config.get('product_agent',{})
    if isinstance(product,dict) and product.get('applicability')!='NOT_APPLICABLE': expected_agents['PRODUCT_AGENT']=product
    capabilities=record.get('capability_attestations')
    if not isinstance(capabilities,list) or not capabilities:
        errors.append('capability_attestations must be a non-empty list'); capabilities=[]
    seen_roles=set(); seen_capabilities=set()
    for index,item in enumerate(capabilities):
        label='capability attestation '+str(index+1)
        capability=closed(item,RUNTIME_CAPABILITY_FIELDS,label,errors)
        role=capability.get('agent_role')
        if role not in expected_agents: errors.append(label+' agent_role is unexpected')
        elif role in seen_roles: errors.append('capability Agent roles must be unique')
        else: seen_roles.add(role)
        capability_id=capability.get('capability_id')
        if not safe_id(capability_id): errors.append(label+' capability_id is invalid')
        elif capability_id.casefold() in seen_capabilities: errors.append('capability IDs must be unique')
        else: seen_capabilities.add(capability_id.casefold())
        for field in ('agent_id','policy_id','action_catalog_id','configuration_id'):
            if not safe_id(capability.get(field)): errors.append(label+' '+field+' is invalid')
        for field in ('policy_hash','action_catalog_hash','configuration_hash'):
            if not exact_hash(capability.get(field)): errors.append(label+' '+field+' is invalid')
        agent=expected_agents.get(role,{}) if role in expected_agents else {}
        if any(capability.get(field)!=agent.get(field) for field in ('agent_id','policy_id','policy_hash','action_catalog_id','action_catalog_hash','configuration_id','configuration_hash')): errors.append(label+' expands or disagrees with the accepted Agent boundary')
        if capability.get('authorization_result')!='AUTHORIZED_CONFIGURATION_BOUNDARY': errors.append(label+' authorization is invalid')
    if seen_roles!=set(expected_agents): errors.append('capability attestations must cover each applicable Agent exactly once')

    authority=closed(record.get('authority_boundaries'),RUNTIME_AUTHORITY_FIELDS,'authority_boundaries',errors)
    exact_authority={
        'runtime_permission':'CANNOT_EXPAND_AUTHORITY',
        'agent_separation':'DISTINCT_LOGICAL_AGENTS',
        'scorpion_result':'ENFORCED',
        'environment_fallback':'FORBIDDEN',
        'provider_authority':'NO_VENDOR_SELF_AUTHORITY',
        'secret_loading':'REFERENCES_ONLY_NO_INLINE_SECRETS',
    }
    if any(authority.get(field)!=expected for field,expected in exact_authority.items()): errors.append('Runtime Adapter authority boundaries are invalid')
    root=config.get('root_authority',{}) if isinstance(config.get('root_authority',{}),dict) else {}
    if authority.get('scorpion_policy_id')!=root.get('scorpion_policy_id') or authority.get('scorpion_policy_hash')!=root.get('scorpion_policy_hash'): errors.append('Runtime Adapter Scorpion boundary disagrees with configuration')
    if not safe_id(authority.get('isolation_evidence_id')) or not exact_hash(authority.get('isolation_evidence_hash')): errors.append('Runtime Adapter isolation evidence identity is invalid')
    if authority.get('private_boundary_result')!='PASS' or authority.get('shared_execution_result')!='PASS': errors.append('Runtime Adapter isolation results must be exact PASS')

    validity=closed(record.get('validity'),RUNTIME_VALIDITY_FIELDS,'validity',errors)
    as_of=strict_utc(as_of_utc)
    observed=strict_utc(validity.get('observed_at_utc'))
    validated=strict_utc(validity.get('validated_at_utc'))
    expires=strict_utc(validity.get('expires_at_utc'))
    if as_of is None: errors.append('validation as-of UTC is invalid')
    if any(item is None for item in (observed,validated,expires)): errors.append('Runtime Adapter validity timestamps must be strict UTC')
    elif as_of is not None:
        if not observed<=validated<=as_of: errors.append('Runtime Adapter evidence is future-dated or unordered')
        if expires<=as_of: errors.append('Runtime Adapter Attestation is expired')
        maximum=timedelta(seconds=RUNTIME_CONTRACT['max_observation_age_seconds'])
        if as_of-observed>maximum or as_of-validated>maximum: errors.append('Runtime Adapter Attestation evidence is stale')

    errors.extend(validate_typed_event_attestations(
        record.get('typed_event_attestations'),configuration,
        record.get('candidate_id'),record.get('candidate_hash'),
        validity.get('observed_at_utc'),validity.get('validated_at_utc'),as_of_utc,
    ))

    evidence=record.get('evidence')
    if not isinstance(evidence,list) or not evidence:
        errors.append('Runtime Adapter evidence must be a non-empty list'); evidence=[]
    evidence_ids=set(); evidence_paths=set(); evidence_bindings=set()
    for index,item in enumerate(evidence):
        label='Runtime Adapter evidence '+str(index+1)
        item=closed(item,RUNTIME_EVIDENCE_FIELDS,label,errors)
        identity=item.get('evidence_id'); path=item.get('evidence_path')
        if not safe_id(identity): errors.append(label+' evidence_id is invalid')
        elif identity.casefold() in evidence_ids: errors.append('Runtime Adapter evidence IDs must be unique')
        else: evidence_ids.add(identity.casefold())
        if not contained_evidence_path(path): errors.append(label+' path is not contained')
        elif path.casefold() in evidence_paths: errors.append('Runtime Adapter evidence paths must be unique')
        else: evidence_paths.add(path.casefold())
        if not exact_hash(item.get('evidence_hash')): errors.append(label+' hash is invalid')
        if item.get('producer_kind')!='INDEPENDENT_VERIFIER' or item.get('independence')!='INDEPENDENT' or item.get('result')!='PASS': errors.append(label+' is not independent PASS evidence')
        if isinstance(identity,str) and isinstance(item.get('evidence_hash'),str): evidence_bindings.add((identity,item.get('evidence_hash')))
    if (authority.get('isolation_evidence_id'),authority.get('isolation_evidence_hash')) not in evidence_bindings: errors.append('Runtime Adapter isolation evidence is not bound to independent evidence')

    operations=config.get('operations_agent',{}) if isinstance(config.get('operations_agent',{}),dict) else {}
    fallback=closed(record.get('fallback'),RUNTIME_FALLBACK_FIELDS,'fallback',errors)
    if not safe_id(fallback.get('fallback_id')) or not contained_evidence_path(fallback.get('evidence_path')) or not exact_hash(fallback.get('evidence_hash')) or fallback.get('result')!='PASS': errors.append('Runtime Adapter fallback proof is invalid')
    if fallback.get('fallback_id')!=operations.get('fallback_id') or fallback.get('evidence_hash')!=operations.get('fallback_hash'): errors.append('Runtime Adapter fallback proof disagrees with configuration')
    kill_switch=closed(record.get('kill_switch'),RUNTIME_KILL_SWITCH_FIELDS,'kill_switch',errors)
    if not safe_id(kill_switch.get('kill_switch_id')) or not contained_evidence_path(kill_switch.get('evidence_path')) or not exact_hash(kill_switch.get('evidence_hash')) or kill_switch.get('result')!='PASS': errors.append('Runtime Adapter Kill Switch proof is invalid')
    if kill_switch.get('kill_switch_id')!=operations.get('kill_switch_id') or kill_switch.get('evidence_hash')!=operations.get('kill_switch_hash'): errors.append('Runtime Adapter Kill Switch proof disagrees with configuration')

    conformance=record.get('conformance')
    if not isinstance(conformance,list): errors.append('Runtime Adapter conformance must be a list'); conformance=[]
    case_ids=[]; conformance_evidence=set()
    for index,item in enumerate(conformance):
        label='Runtime Adapter conformance '+str(index+1)
        item=closed(item,RUNTIME_CONFORMANCE_FIELDS,label,errors)
        case_ids.append(item.get('case_id'))
        for field in ('harness_id','evidence_id'):
            if not safe_id(item.get(field)): errors.append(label+' '+field+' is invalid')
        evidence_id=item.get('evidence_id')
        if isinstance(evidence_id,str):
            if evidence_id.casefold() in conformance_evidence: errors.append('Runtime Adapter conformance evidence IDs must be unique')
            conformance_evidence.add(evidence_id.casefold())
        if not exact_hash(item.get('evidence_hash')) or item.get('result')!='PASS': errors.append(label+' result is not PASS evidence')
    if case_ids!=RUNTIME_CONTRACT['conformance_cases']: errors.append('Runtime Adapter positive/negative conformance cases are incomplete or unordered')
    if any(SECRET.search(item) or RUNTIME_SECRET.search(item) for item in _strings(record)): errors.append('Runtime Adapter Attestation contains secret-like inline material')
    return errors

def validate_runtime_adapter_attestation_file(
    path,configuration,configuration_hash,expected_topology_id,
    expected_topology_hash,as_of_utc,
):
    target=Path(path)
    if target.is_symlink() or not target.is_file(): return ['Runtime Adapter Attestation must be a regular file']
    try: value=strict_json_bytes(target.read_bytes())
    except (OSError,UnicodeError,ValueError) as error: return ['Runtime Adapter Attestation is not strict UTF-8 JSON: '+str(error)]
    return validate_runtime_adapter_attestation(
        value,configuration,configuration_hash,expected_topology_id,
        expected_topology_hash,as_of_utc,
    )

def validate_action_catalog_file(path,configuration,agent_slot='operations_agent'):
    errors=validate_configuration(configuration)
    if agent_slot not in {'operations_agent','product_agent'}: return errors+['action catalog agent slot is invalid']
    config=configuration if isinstance(configuration,dict) else {}
    agent=config.get(agent_slot,{})
    if not isinstance(agent,dict) or agent.get('applicability')=='NOT_APPLICABLE': return errors+['action catalog requires an applicable Agent slot']
    target=Path(path)
    if target.is_symlink() or not target.is_file(): return errors+['Agent Action Catalog must be a regular file']
    try:
        raw=target.read_bytes(); value=strict_json_bytes(raw)
    except (OSError,UnicodeError,ValueError) as error:
        return errors+['Agent Action Catalog is not strict UTF-8 JSON: '+str(error)]
    errors.extend(validate_action_catalog(
        value,agent.get('action_catalog_id'),config.get('candidate_id'),
        config.get('candidate_hash'),config.get('configuration_baseline_id'),
    ))
    content_hash='sha256:'+hashlib.sha256(raw).hexdigest()
    if agent.get('action_catalog_hash')!=content_hash: errors.append('action catalog file hash disagrees with Agent Configuration Baseline')
    return errors

def markdown_fields(text):
    fields={}; errors=[]
    if not isinstance(text,str): return fields,['markdown artifact must be text']
    for line in text.splitlines():
        if not line.startswith('- ') or ':' not in line: continue
        name,value=line[2:].split(':',1)
        if name in fields: errors.append('duplicate markdown field '+name)
        else: fields[name]=value.strip()
    return fields,errors

def exact_id_hash(value):
    if not isinstance(value,str): return None
    parts=[part.strip() for part in value.split('/')]
    if len(parts)!=2 or not safe_id(parts[0]) or not exact_hash(parts[1]): return None
    return parts[0],parts[1]

def baseline_identity(value):
    if not isinstance(value,str): return None
    parts=[part.strip() for part in value.split('/')]
    if len(parts)!=3 or not safe_id(parts[0]) or not SEMVER.fullmatch(parts[1]) or not exact_hash(parts[2]): return None
    return parts[0],parts[2]

def capability_evidence(value,simulation=False):
    if not isinstance(value,str): return None
    identity,digest=(value.rsplit('/',1)+[None])[:2] if '/' in value else (None,None)
    if identity is None or not exact_hash(str(digest or '').strip()): return None
    parts=[part.strip() for part in identity.split('@')]
    expected=3 if simulation else 2
    if len(parts)!=expected or any(not safe_id(part) for part in parts): return None
    if any(tokens(part)&PROOF_FORBIDDEN_TOKENS for part in parts): return None
    return tuple(parts)+(str(digest).strip(),)

def validate_product_formation_status(value):
    errors=[]; record=closed(value,PRODUCT_FORMATION_STATUS_FIELDS,'agent_product_formation status',errors)
    if record.get('state')=='UNPROVED':
        if record!=UNPROVED_PRODUCT_FORMATION_STATUS: errors.append('unproved Agent Product Formation status must not claim evidence')
        return errors
    if record.get('state')!='PRODUCT_FORMATION_AGENT_BOUND': errors.append('Agent Product Formation state is invalid')
    if record.get('product_agent_applicability') not in PRODUCT_APPLICABILITY: errors.append('Product Agent applicability is invalid')
    for field in ('calabash_definition_handoff_id','configuration_baseline_id'):
        if not safe_id(record.get(field)): errors.append('Agent Product Formation '+field+' is invalid')
    for field in ('calabash_definition_handoff_hash','configuration_baseline_hash'):
        if not exact_hash(record.get(field)): errors.append('Agent Product Formation '+field+' is invalid')
    allowed_states={'NOT_APPLICABLE','UNIMPLEMENTED_EXTRA','REAL_RUNNABLE_EXTRA','REAL_RUNNABLE_CORE'}
    if record.get('product_agent_capability_state') not in allowed_states: errors.append('Product Agent capability state is invalid')
    if record.get('operations_agent_state')!='PREPARED_NOT_INTEGRATED': errors.append('Operations Agent may only be PREPARED_NOT_INTEGRATED in Product Formation')
    return errors

def validate_product_formation(rule_text,handoff_text,status,configuration,configuration_hash):
    errors=[]
    rule,rule_errors=markdown_fields(rule_text); handoff,handoff_errors=markdown_fields(handoff_text)
    errors.extend(rule_errors); errors.extend(handoff_errors)
    relevant_rule={name:value for name,value in rule.items() if name.startswith('Agent ')}
    if relevant_rule!=AGENT_RULE_FIELDS: errors.append('Agent Rule Product Formation contract is not closed')
    relevant_handoff={name for name in handoff if name.startswith(('Agent Product','Product Agent','Operations Agent','Agent Configuration'))}
    missing=AGENT_HANDOFF_FIELDS-relevant_handoff; unknown=relevant_handoff-AGENT_HANDOFF_FIELDS
    if missing: errors.append('Product Baseline Handoff missing Agent fields '+', '.join(sorted(missing)))
    if unknown: errors.append('Product Baseline Handoff unknown Agent fields '+', '.join(sorted(unknown)))
    if not isinstance(status,dict) or status.get('status_schema_version')!='2.8.0': errors.append('Product Formation Agent join requires exact 2.8 status'); status={}
    candidate=status.get('canonical_candidate',{}) if isinstance(status.get('canonical_candidate',{}),dict) else {}
    errors.extend(validate_configuration(configuration,candidate.get('candidate_id'),candidate.get('candidate_hash')))
    config=configuration if isinstance(configuration,dict) else {}
    if not exact_hash(configuration_hash): errors.append('Agent Configuration Baseline file hash is invalid')
    state=status.get('agent_product_formation')
    errors.extend(validate_product_formation_status(state))
    state=state if isinstance(state,dict) else {}
    if state.get('state')!='PRODUCT_FORMATION_AGENT_BOUND': errors.append('Product Formation Agent evidence is not bound')
    applicability=state.get('product_agent_applicability')
    configured_product=config.get('product_agent',{})
    if not isinstance(configured_product,dict): configured_product={}
    if handoff.get('Product Agent applicability')!=applicability: errors.append('Product Agent applicability disagrees with status')
    if configured_product.get('applicability')!=applicability: errors.append('Product Agent applicability disagrees with configuration')
    candidate_identity=exact_id_hash(handoff.get('Agent Product Formation candidate ID / exact hash'))
    if candidate_identity!=(candidate.get('candidate_id'),candidate.get('candidate_hash')): errors.append('Agent Product Formation candidate identity disagrees')
    definition=exact_id_hash(handoff.get('Calabash Definition Handoff ID / exact hash'))
    basis=exact_id_hash(handoff.get('Product Agent applicability Calabash basis'))
    if not definition or definition!=basis or handoff.get('Calabash Definition Handoff result')!='PASS': errors.append('Product Agent applicability lacks exact Calabash basis')
    if definition!=(state.get('calabash_definition_handoff_id'),state.get('calabash_definition_handoff_hash')): errors.append('Calabash basis disagrees with status')
    config_identity=exact_id_hash(handoff.get('Agent Configuration Baseline ID / exact hash'))
    expected_config=(config.get('configuration_baseline_id'),configuration_hash)
    if config_identity!=expected_config or config_identity!=(state.get('configuration_baseline_id'),state.get('configuration_baseline_hash')): errors.append('Agent Configuration Baseline identity disagrees')
    product_baseline=baseline_identity(handoff.get('Baseline ID / version / hash'))
    if not product_baseline: errors.append('Product Baseline identity is invalid')
    operations=config.get('operations_agent',{}) if isinstance(config.get('operations_agent',{}),dict) else {}
    if handoff.get('Operations Agent ID')!=operations.get('agent_id'): errors.append('Operations Agent identity disagrees with configuration')
    if handoff.get('Operations Agent Product Formation state')!='PREPARED_NOT_INTEGRATED' or state.get('operations_agent_state')!='PREPARED_NOT_INTEGRATED': errors.append('Operations Agent integration is falsely claimed in Product Formation')
    operations_joins={
        'Operations Agent prepared configuration evidence':'configuration',
        'Operations Agent prepared Action Catalog evidence':'action_catalog',
        'Operations Agent telemetry evidence':'interface',
        'Operations Agent audit evidence':'audit_stream',
        'Operations Agent fallback evidence':'fallback',
        'Operations Agent Kill Switch evidence':'kill_switch',
    }
    for field,kind in operations_joins.items():
        if exact_id_hash(handoff.get(field))!=(operations.get(kind+'_id'),operations.get(kind+'_hash')): errors.append(field+' disagrees with configuration')
    if not exact_id_hash(handoff.get('Operations Agent Runtime Adapter requirement evidence')): errors.append('Operations Agent Runtime Adapter requirement evidence is invalid')
    product=configured_product
    if tokens(product.get('agent_id'))&{'CONSTRUCTION'}: errors.append('Construction Agent cannot substitute for Product Agent')
    capability_state=handoff.get('Product Agent capability state')
    if capability_state!=state.get('product_agent_capability_state'): errors.append('Product Agent capability state disagrees with status')
    if applicability=='NOT_APPLICABLE':
        if handoff.get('Product Agent ID')!='NOT_APPLICABLE' or any(handoff.get(field)!='NOT_APPLICABLE' for field in PRODUCT_PROOF_FIELDS): errors.append('NOT_APPLICABLE Product Agent cannot claim identity or capability')
    elif applicability=='APPLICABLE_EXTRA' and capability_state=='UNIMPLEMENTED_EXTRA':
        if handoff.get('Product Agent ID')!=product.get('agent_id') or any(handoff.get(field)!='NOT_APPLICABLE' for field in PRODUCT_PROOF_FIELDS): errors.append('unimplemented EXTRA cannot claim Product Agent capability')
    else:
        expected_state='REAL_RUNNABLE_CORE' if applicability=='APPLICABLE_CORE' else 'REAL_RUNNABLE_EXTRA'
        if capability_state!=expected_state: errors.append('applicable Product Agent real capability state is invalid')
        if handoff.get('Product Agent ID')!=product.get('agent_id') or handoff.get('Product Agent proof actor kind')!='PRODUCT_AGENT': errors.append('Product Agent proof uses an invalid or Construction actor')
        capability=handoff.get('Product Agent Workflow Capability ID')
        if not safe_id(capability): errors.append('Product Agent Workflow Capability ID is invalid')
        evidence=[capability_evidence(handoff.get(field)) for field in ('Product Agent runnable evidence','Product Agent API evidence','Product Agent MCP evidence')]
        simulation=capability_evidence(handoff.get('Product Agent Simulation scenario/recovery evidence'),True)
        if any(item is None or item[0]!=capability for item in evidence) or simulation is None or simulation[0]!=capability: errors.append('Product Agent real Workflow/API/MCP/Simulation proof is incomplete or not same-capability')
        if exact_id_hash(handoff.get('Product Agent Product Baseline ID / exact hash'))!=product_baseline: errors.append('Product Agent proof is not bound to Product Baseline')
    if isinstance(product.get('agent_id'),str) and isinstance(operations.get('agent_id'),str) and product.get('agent_id').casefold()==operations.get('agent_id').casefold(): errors.append('Product and Operations Agent identities alias')
    if handoff.get('Agent Product Formation result')!='PASS' or handoff.get('Handoff status')!='COMPLETE': errors.append('Agent Product Formation handoff is incomplete')
    return errors

def validate_product_formation_files(rule_path,handoff_path,status_path,configuration_path):
    paths=[Path(item) for item in (rule_path,handoff_path,status_path,configuration_path)]
    if any(path.is_symlink() or not path.is_file() for path in paths): return ['Agent Product Formation inputs must be regular files']
    try:
        rule=paths[0].read_text(encoding='utf-8'); handoff=paths[1].read_text(encoding='utf-8')
        status=strict_json(paths[2]); config_raw=paths[3].read_bytes(); configuration=strict_json_bytes(config_raw)
    except (OSError,UnicodeError,ValueError) as error:
        return ['Agent Product Formation input is not strict UTF-8: '+str(error)]
    config_hash='sha256:'+hashlib.sha256(config_raw).hexdigest()
    return validate_product_formation(rule,handoff,status,configuration,config_hash)
def main():
    parser=argparse.ArgumentParser(); parser.add_argument('path'); args=parser.parse_args(); errors=validate_file(args.path)
    if errors:
        print('FAIL'); [print(error) for error in errors]; raise SystemExit(1)
    print('PASS')
if __name__=='__main__': main()
