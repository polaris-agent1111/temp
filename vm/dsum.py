import json, glob, os, statistics as st
root = os.path.expanduser('~/polaris/local-eval/evals')
for d in ['champion-1109-1922', 'cand-D1-back33', 'cand-D2-back39', 'cand-D3-back-tb36']:
    for label, pat in [('d-only', 'd-*'), ('all', '**')]:
        rs = []
        for f in sorted(glob.glob(f'{root}/{d}/{pat}/run-*/result.json', recursive=True)):
            q = json.load(open(f))['question'][0]
            rs.append((q['total_seconds'], [x['seconds'] for x in q['downloads']]))
        if not rs: continue
        t = [r[0] for r in rs]
        sd = f'{st.stdev(t):.1f}' if len(t) > 1 else '-'
        f5 = st.mean(r[1][4] for r in rs); f6 = st.mean(r[1][5] for r in rs); f14 = st.mean(sum(r[1][:4]) for r in rs)
        print(f'{d:22s} {label:6s} n={len(t)} mean={st.mean(t):.2f} sd={sd} f1-4={f14:.1f} f5={f5:.1f} f6={f6:.1f} runs={[round(x,1) for x in t]}')
