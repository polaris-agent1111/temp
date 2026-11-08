import json

with open('runs/results.jsonl', 'r', encoding='utf-8') as f:
    lines = [json.loads(line) for line in f if line.strip()]

tags_to_check = [
    'test-anchor-shot2-leak-40x3-36x3',
    'test-leak-asym-40-40-37-37',
    'test-leak-asym-41-40-37-36',
    'test-leak-asym-40x3-38-37-36',
    'test-leak-asym-40-40-38-36',
    'test-leak-asym-41-40-38-36',
    'test-leak-asym-42-41-40-38-37',
    'test-leak-asym-40-all4-36-both',
]

print("=== CLOUD SIMULATION RESULTS (AS OF 03:00) ===")
for prefix in tags_to_check:
    matches = [r for r in lines if r.get('tag', '').startswith(prefix)]
    valid_runs = [r for r in matches if r.get('valid', True) and 'total_seconds' in r]
    if not valid_runs:
        continue
    totals = [r['total_seconds'] for r in valid_runs]
    n = len(totals)
    mean = sum(totals) / n
    std = (sum((x - mean)**2 for x in totals) / n)**0.5 if n > 1 else 0.0
    cv = (std / mean) * 100 if mean > 0 else 0.0
    se = std / (n**0.5) if n > 1 else 0.0
    ci_95_low = mean - 1.96 * se
    ci_95_high = mean + 1.96 * se
    print(f"\n{prefix:<35} | n={n:<2} | min={min(totals):6.2f}s | mean={mean:6.2f}s | max={max(totals):6.2f}s | std={std:5.2f}s | CV={cv:4.1f}% | 95%CI=[{ci_95_low:5.1f}, {ci_95_high:5.1f}]")
    for r in valid_runs:
        dl = r.get('downloads', {})
        t1 = dl.get('1.bin', 0)
        t2 = dl.get('2.bin', 0)
        t3 = dl.get('3.bin', 0)
        t4 = dl.get('4.bin', 0)
        t5 = dl.get('5.bin', 0)
        t6 = dl.get('6.bin', 0)
        print(f"   -> {r['tag']:<35} : {r['total_seconds']:6.2f}s (1:{t1:.1f} 2:{t2:.1f} 3:{t3:.1f} 4:{t4:.1f} 5:{t5:.1f} 6:{t6:.1f})")
