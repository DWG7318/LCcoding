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
print('PASS: incremental and post-security acceptance boundaries')
