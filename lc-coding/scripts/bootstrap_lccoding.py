#!/usr/bin/env python3
from pathlib import Path
import argparse, json, shutil, datetime

ROOT_DIRS = ['slices','impact','evidence','reviews','release','runs','security','delivery']

def copy_template(src_root, name, dst):
    src = src_root / 'templates' / name
    if src.exists() and not dst.exists():
        shutil.copy2(src, dst)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--project', required=True)
    ap.add_argument('--name', required=True)
    ap.add_argument('--repository', required=True)
    ap.add_argument('--visibility', choices=['public','private'], required=True)
    ap.add_argument('--owner', default='OWNER')
    args = ap.parse_args()

    project = Path(args.project).resolve()
    project.mkdir(parents=True, exist_ok=True)
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
        'initial_version': '0.0.1',
        'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status': 'INITIALIZED'
    }
    (lc/'PROJECT-START.json').write_text(json.dumps(start, indent=2), encoding='utf-8')
    (project/'VERSION').write_text('0.0.1\n', encoding='utf-8') if not (project/'VERSION').exists() else None
    print(lc)

if __name__ == '__main__':
    main()
