from pathlib import Path
root=Path(__file__).resolve().parents[2]
text=(root/'lc-coding/references/loop-acceptance-boundary.md').read_text(encoding='utf-8')
assert 'Incremental acceptance belongs inside the Loop' in text
assert 'LOOP_OWNER_ACCEPTANCE_READY' in text
assert 'LOOP_OWNER_ACCEPTED' in text
assert 'ALL_REQUIRED_RUNS_ACCEPTED' in text
owner=(root/'lc-coding/references/owner-acceptance.md').read_text(encoding='utf-8')
assert 'Loop Owner Acceptance' in owner
assert 'Post-Security Owner Acceptance' in owner
skill=(root/'lc-coding/SKILL.md').read_text(encoding='utf-8')
assert 'Every normal SLK/CLK/GLK Run must end' in skill
assert 'Post-Security Owner Acceptance' in skill
start=(root/'lc-coding/templates/RUN-HANDOFF.md').read_text(encoding='utf-8')
receipt=(root/'lc-coding/templates/LOOP-OWNER-ACCEPTANCE.md').read_text(encoding='utf-8')
assert 'Artifact role: RUN_START_CONTRACT' in start
assert 'Owner result:' not in start and 'D3 Receipt:' not in start
assert 'Artifact role: LOOP_OWNER_ACCEPTANCE_RECEIPT' in receipt
assert 'Run-start contract ID:' in receipt and 'Run-start contract SHA-256:' in receipt
assert 'Calling phase gate remains independently evaluated: YES' in receipt
assert 'does not pass or advance the calling phase gate' in receipt
print('PASS: incremental and post-security acceptance boundaries')
