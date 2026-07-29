#!/usr/bin/env python3
import argparse, re

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('current'); ap.add_argument('proposed'); ap.add_argument('--owner-approved',action='store_true'); args=ap.parse_args()
    pat=re.compile(r'^\d+\.\d+\.\d+$')
    if not pat.match(args.current) or not pat.match(args.proposed): raise SystemExit('invalid version')
    major,minor,patch=map(int,args.proposed.split('.'))
    if (major,minor,patch)>=(1,0,1) and not args.owner_approved:
        print('BLOCKED: Owner approval required'); raise SystemExit(1)
    print('PASS')
if __name__=='__main__': main()
