#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re

CONTRACT_PATH=Path(__file__).resolve().parents[1]/'contracts/agent-configuration-baseline.json'
CONTRACT=json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))
TOP=set(CONTRACT['top_level_fields'])
KINDS=tuple(CONTRACT['agent_identity_kinds'])
AGENT_FIELDS={'applicability','agent_id'}|{suffix for kind in KINDS for suffix in (kind+'_id',kind+'_hash')}
ROOT_FIELDS={'authority_flow','root_authority_id','root_authority_hash','scorpion_policy_id','scorpion_policy_hash','secrets_storage','runtime_permission'}
VERIFY_FIELDS={'verification_id','candidate_id','candidate_hash','configuration_baseline_id','independent_verifier_id','evidence_id','evidence_hash','result'}
ACCEPT_FIELDS={'acceptance_id','owner_id','candidate_id','candidate_hash','configuration_baseline_id','verification_id','result'}
SAFE=re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$')
HASH=re.compile(r'^sha256:[0-9a-f]{64}$')
GENERIC={'','NONE','PENDING','UNKNOWN','NOT_APPLICABLE','PASS','DONE','READY','TEST','FAKE','MOCK','STUB','TODO','TBD','COMPLETE','INVALID'}
SECRET=re.compile(r'(?i)(?:^sk-|^ghp_|password\s*=|secret\s*=|-----BEGIN .*PRIVATE KEY-----)')

class DuplicateKeyError(ValueError): pass
def _pairs(pairs):
    out={}
    for key,value in pairs:
        if key in out: raise DuplicateKeyError('duplicate key')
        out[key]=value
    return out
def strict_json(path):
    return json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=_pairs,parse_constant=lambda value: (_ for _ in ()).throw(ValueError('non-finite number')))
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
def main():
    parser=argparse.ArgumentParser(); parser.add_argument('path'); args=parser.parse_args(); errors=validate_file(args.path)
    if errors:
        print('FAIL'); [print(error) for error in errors]; raise SystemExit(1)
    print('PASS')
if __name__=='__main__': main()
