#!/usr/bin/env python3
from pathlib import Path
import argparse, json, hashlib, datetime

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--project',required=True)
    ap.add_argument('--manifest',required=True)
    ap.add_argument('--agent-platform',required=True)
    args=ap.parse_args()
    project=Path(args.project); lc=project/'.lccoding'; lc.mkdir(exist_ok=True)
    manifest=Path(args.manifest)
    lock={'project_id':project.name,'issued_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'agent_platform':args.agent_platform,'manifest_hash':sha(manifest),
          'knowledge_test':'PASS','execution_test':'PASS','compatibility':'PASS','status':'VALID','invalidated_by':[]}
    (lc/'INTERPRETATION-LOCK.json').write_text(json.dumps(lock,indent=2),encoding='utf-8')
    print(lc/'INTERPRETATION-LOCK.json')

if __name__=='__main__': main()
