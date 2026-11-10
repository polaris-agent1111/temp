import json, glob, os, statistics as st
root = os.path.expanduser('~/polaris/local-eval/evals')
for d in ['champion-1109-1922', 'cand-C3-front-tokenbypass']:
    rs = []
    for f in sorted(glob.glob(f'{root}/{d}/**/run-*/result.json', recursive=True)):
        q = json.load(open(f))['question'][0]
        rs.append((round(q['total_seconds'], 1), [round(x['seconds'], 1) for x in q['downloads']]))
    print(d)
    for t, p in rs:
        print('  total', t, 'files', p)
    for i in range(6):
        v = [r[1][i] for r in rs]
        print(f'  file{i+1} mean={st.mean(v):.1f} sd={st.stdev(v):.1f} min={min(v)} max={max(v)}')
