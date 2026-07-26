#!/usr/bin/env python3
from pathlib import Path
import argparse, json, shutil

FILES = {
 'WORKING-CONTRACT.md':'WORKING-CONTRACT.md',
 'SIMULATION-WORLD.md':'SIMULATION-WORLD.md',
}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--project', required=True)
    ap.add_argument('--name', required=True)
    ap.add_argument('--profile', default='PRODUCT', choices=['EXPRESS','PRODUCT','SYSTEM'])
    a=ap.parse_args()
    root=Path(a.project).resolve(); lc=root/'.lccoding'; lc.mkdir(parents=True,exist_ok=True)
    tpl=Path(__file__).resolve().parents[1]/'templates'
    for out,src in FILES.items():
        dst=lc/out
        if not dst.exists(): shutil.copy2(tpl/src,dst)
    defaults={
      'PROJECT-START.md':f'# Project Start\n\n- Project: {a.name}\n- Profile: `{a.profile}`\n- Calabash baseline:\n',
      'WORKFLOW-MAP.md':'# Workflow Map\n',
      'UI-MAP.md':'# UI Map\n\n## Actor Surfaces\n\n| Surface | Actor | Purpose | Data Visible | Actions | Lock State |\n|---|---|---|---|---|---|\n| Customer/client | | | | | |\n| Staff/operator | | | | | |\n| Administrator/configuration | | | | | |\n| Notification/status/audit | | | | | |\n',
      'SHARED-CAPABILITIES.md':'# Shared Capabilities\n',
      'slices/INDEX.md':'# Feature Slice Index\n',
    }
    for rel,content in defaults.items():
        p=lc/rel; p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists(): p.write_text(content,encoding='utf-8')
    for d in ['impact','evidence','observations','reviews','release','baselines']:
        (lc/d).mkdir(exist_ok=True)
    status={'project':a.name,'profile':a.profile,'version':'1.1.1','active_slice':None,'integration_baseline':None}
    (lc/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'LCCODING_BOOTSTRAPPED {root}')
if __name__=='__main__': main()
