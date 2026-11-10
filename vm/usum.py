import json, glob, os, statistics as st
root = os.path.expanduser('~/polaris/local-eval/evals')
for d in ['cand-U4-base', 'cand-U4-r24', 'cand-U4-i8k']:
    rs = []
    for f in sorted(glob.glob(f'{root}/{d}/u-*/run-*/result.json')):
        q = json.load(open(f))['question'][0]
        rs.append((q['total_seconds'], [x['seconds'] for x in q['downloads']]))
    if not rs: print(d, 'no results'); continue
    t = [r[0] for r in rs]
    sd = f'{st.stdev(t):.1f}' if len(t) > 1 else '-'
    f14 = st.mean(sum(r[1][:4]) for r in rs); f5 = st.mean(r[1][4] for r in rs); f6 = st.mean(r[1][5] for r in rs)
    print(f'{d:14s} n={len(t)} mean={st.mean(t):.2f} sd={sd} f1-4={f14:.1f} f5={f5:.1f} f6={f6:.1f} runs={[round(x,1) for x in t]}')
