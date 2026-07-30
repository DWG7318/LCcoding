#!/usr/bin/env python3
from pathlib import Path
import argparse, json, shutil, datetime, subprocess

ROOT_DIRS = ['slices','impact','evidence','reviews','release','runs','security','delivery']

def copy_template(src_root, name, dst):
    src = src_root / 'templates' / name
    if src.exists() and not dst.exists():
        shutil.copy2(src, dst)

def git_head(project):
    cp = subprocess.run(
        ['git', '-C', str(project), 'rev-parse', 'HEAD'],
        capture_output=True, text=True
    )
    if cp.returncode:
        raise SystemExit('existing mode requires a readable Git HEAD')
    return cp.stdout.strip()

def update_json(path, values):
    data = json.loads(path.read_text(encoding='utf-8'))
    data.update(values)
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--project', required=True)
    ap.add_argument('--name', required=True)
    ap.add_argument('--repository', required=True)
    ap.add_argument('--visibility', choices=['public','private'], required=True)
    ap.add_argument('--owner', default='OWNER')
    ap.add_argument('--mode', choices=['new','existing'], default='new')
    ap.add_argument('--continuity', choices=['continue','narrow_redirect','hold','terminate'], default='continue')
    ap.add_argument('--claimed-state', choices=['none','partial','near_complete','complete','unknown'], default='none')
    args = ap.parse_args()

    project = Path(args.project).resolve()
    if args.mode == 'existing':
        if not project.exists() or not (project/'.git').exists():
            ap.error('existing mode requires an existing Git repository')
    else:
        project.mkdir(parents=True, exist_ok=True)

    source_version = None
    source_head = None
    if args.mode == 'existing':
        version_file = project/'VERSION'
        source_version = version_file.read_text(encoding='utf-8').strip() if version_file.exists() else 'UNKNOWN'
        source_head = git_head(project)

    lc = project / '.lccoding'
    lc.mkdir(exist_ok=True)
    for d in ROOT_DIRS:
        (lc/d).mkdir(exist_ok=True)

    skill_root = Path(__file__).resolve().parents[1]
    mappings = {
        'OWNER-POLICY.md':'OWNER-POLICY.md', 'PROJECT-PROFILE.md':'PROJECT-PROFILE.md',
        'PROJECT-FINGERPRINT.json':'PROJECT-FINGERPRINT.json', 'PROJECT-HEALTH.json':'PROJECT-HEALTH.json',
        'AGENT-RULE.md':'AGENT-RULE.md', 'CANONICAL-MANIFEST.json':'CANONICAL-MANIFEST.json',
        'INTERPRETATION-LOCK.json':'INTERPRETATION-LOCK.json', 'PROPOSAL-READINESS.md':'PROPOSAL-READINESS.md',
        'WORKING-CONTRACT.md':'WORKING-CONTRACT.md','WORKFLOW-MAP.md':'WORKFLOW-MAP.md',
        'UI-MAP.md':'UI-MAP.md','SIMULATION-WORLD.md':'SIMULATION-WORLD.md','STATUS.json':'status.json','PHASE-STATUS.json':'PHASE-STATUS.json'
    }
    for src, dst in mappings.items():
        copy_template(skill_root, src, lc/dst)

    start = {
        'project_id': project.name,
        'name': args.name,
        'owner': args.owner,
        'repository': args.repository,
        'visibility': args.visibility,
        'initialization_mode': args.mode.upper(),
        'initial_version': '0.0.1' if args.mode == 'new' else None,
        'source_version': source_version,
        'source_head': source_head,
        'continuity_decision': args.continuity.upper(),
        'reported_project_state': args.claimed_state.upper(),
        'completion_claim_status': 'NO_CLAIM' if args.claimed_state == 'none' else 'CLAIMED_UNATTESTED',
        'attestation_status': 'NOT_APPLICABLE' if args.mode == 'new' else 'PENDING',
        'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status': 'INITIALIZED' if args.mode == 'new' else 'EXISTING_INTAKE_PENDING_ATTESTATION'
    }
    start_path = lc/'PROJECT-START.json'
    first_initialization = not start_path.exists()
    if first_initialization:
        start_path.write_text(json.dumps(start, indent=2), encoding='utf-8')
        update_json(lc/'status.json', {
            'initialization_mode': args.mode.upper(),
            'continuity_decision': args.continuity.upper(),
            'existing_project_attestation': 'PENDING' if args.mode == 'existing' else 'NOT_APPLICABLE',
            'existing_project_classification': 'PENDING' if args.mode == 'existing' else 'NOT_APPLICABLE',
            'initialization': 'EXISTING_INTAKE_PENDING' if args.mode == 'existing' else 'INITIALIZED'
        })
        update_json(lc/'PROJECT-HEALTH.json', {
            'initialization_mode': args.mode.upper(),
            'continuity_decision': args.continuity.upper(),
            'completion_claim_status': start['completion_claim_status'],
            'existing_project_classification': 'PENDING' if args.mode == 'existing' else 'NOT_APPLICABLE'
        })
    if args.mode == 'new' and not (project/'VERSION').exists():
        (project/'VERSION').write_text('0.0.1\n', encoding='utf-8')
    print(lc)

if __name__ == '__main__':
    main()
