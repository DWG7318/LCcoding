#!/usr/bin/env python3
from pathlib import Path
import sys

REQUIRED = [
    '.lccoding/WORKING-CONTRACT.md',
    '.lccoding/WORKFLOW-MAP.md',
    '.lccoding/UI-MAP.md',
    '.lccoding/SIMULATION-WORLD.md',
    '.lccoding/SHARED-CAPABILITIES.md',
    '.lccoding/slices/INDEX.md',
]

def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
    missing = [x for x in REQUIRED if not (root / x).exists()]
    if missing:
        print('LCCODING_PROJECT_INVALID')
        for x in missing:
            print(f'MISSING {x}')
        return 1
    print('LCCODING_PROJECT_VALID')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
