#!/usr/bin/env python3
from pathlib import Path
import argparse, json, html

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('project'); args=ap.parse_args()
    lc=Path(args.project)/'.lccoding'; data=json.loads((lc/'status.json').read_text(encoding='utf-8'))
    rows=''.join(f'<tr><th>{html.escape(str(k))}</th><td><pre>{html.escape(json.dumps(v,ensure_ascii=False,indent=2))}</pre></td></tr>' for k,v in data.items())
    doc=f'<!doctype html><meta charset="utf-8"><title>LCCoding Status</title><style>body{{font:14px system-ui;max-width:1100px;margin:auto;padding:24px}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ddd;padding:10px;text-align:left;vertical-align:top}}th{{width:220px}}pre{{white-space:pre-wrap;margin:0}}</style><h1>LCCoding Status</h1><table>{rows}</table>'
    (lc/'status.html').write_text(doc,encoding='utf-8'); print(lc/'status.html')
if __name__=='__main__': main()
