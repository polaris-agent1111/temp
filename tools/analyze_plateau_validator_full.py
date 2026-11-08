import json
import numpy as np

with open('runs/results.jsonl', 'r', encoding='utf-8') as f:
    lines = [json.loads(line) for line in f if line.strip()]

groups = [
    ('test-anchor-shot2-leak-40x3-36x3', 'Shot 2 基准锚点 (1-3@40, 4-6@36)'),
    ('test-anchor-shot2-pert-40x3-37-36-36', 'Shot 2 微扰 +1 (4.bin 36->37)'),
    ('test-anchor-shot2-pert-39x3-36x3', 'Shot 2 微扰 -1 (1-3.bin 40->39)'),
    ('test-leak-asym-40-40-37-37', '超平稳双长文件 (1-4@40, 5-6@37)'),
    ('test-leak-asym-41-40-37-36', '前程提速冲榜 (1-3@41, 4@40, 5@37, 6@36)'),
    ('test-leak-asym-40x3-38-37-36', '平滑过渡阶梯 (1-3@40, 4@38, 5@37, 6@36)'),
    ('test-leak-asym-40x3-37-37-36', '深度平稳阶梯 (1-3@40, 4@37, 5@37, 6@36)'),
    ('test-leak-asym-40-40-38-36', '5.bin 尖点探索 (1-4@40, 5@38, 6@36)'),
    ('test-leak-asym-41-40-38-36', '高压尖点探索 (1-3@41, 4@40, 5@38, 6@36)'),
    ('test-leak-asym-42-41-40-38-37', '极致阶梯 (1-2@42, 3@41, 4@40, 5@38, 6@37)'),
]

print("=" * 110)
print(f"{'构型 Tag':<35} | {'说明':<22} | {'n':<2} | {'Min':<6} | {'Mean':<6} | {'Median':<6} | {'Max':<6} | {'Std':<5} | {'CV%':<5} | {'95% CI':<15}")
print("=" * 110)

anchor_mean = None

for prefix, desc in groups:
    matches = [r for r in lines if r.get('tag', '').startswith(prefix)]
    valid_runs = [r for r in matches if r.get('valid', True) and 'total_seconds' in r]
    if not valid_runs:
        continue
    totals = [r['total_seconds'] for r in valid_runs]
    n = len(totals)
    t_min = min(totals)
    t_max = max(totals)
    t_mean = float(np.mean(totals))
    t_med = float(np.median(totals))
    t_std = float(np.std(totals, ddof=1)) if n > 1 else 0.0
    cv = (t_std / t_mean) * 100 if t_mean > 0 else 0.0
    se = t_std / (n**0.5) if n > 1 else 0.0
    ci_low = t_mean - 1.96 * se
    ci_high = t_mean + 1.96 * se
    
    if prefix == 'test-anchor-shot2-leak-40x3-36x3':
        anchor_mean = t_mean

    ci_str = f"[{ci_low:5.1f}, {ci_high:5.1f}]"
    print(f"{prefix:<35} | {desc:<22} | {n:<2} | {t_min:6.2f} | {t_mean:6.2f} | {t_med:6.2f} | {t_max:6.2f} | {t_std:5.2f} | {cv:4.1f}% | {ci_str:<15}")

print("=" * 110)

print("\n--- 各构型分文件耗时均值拆解 (1.bin ~ 6.bin) ---")
print(f"{'构型 Tag':<35} | {'1.bin':<5} | {'2.bin':<5} | {'3.bin':<5} | {'4.bin':<5} | {'5.bin':<6} | {'6.bin':<6} | {'Total Mean':<10}")
print("-" * 90)

for prefix, desc in groups:
    matches = [r for r in lines if r.get('tag', '').startswith(prefix)]
    valid_runs = [r for r in matches if r.get('valid', True) and 'total_seconds' in r]
    if not valid_runs:
        continue
    n = len(valid_runs)
    avg_dl = {}
    for i in range(1, 7):
        k = f"{i}.bin"
        vals = [r.get('downloads', {}).get(k, 0) for r in valid_runs]
        avg_dl[k] = float(np.mean(vals)) if vals else 0.0
    
    t_mean = float(np.mean([r['total_seconds'] for r in valid_runs]))
    print(f"{prefix:<35} | {avg_dl['1.bin']:5.2f} | {avg_dl['2.bin']:5.2f} | {avg_dl['3.bin']:5.2f} | {avg_dl['4.bin']:5.2f} | {avg_dl['5.bin']:6.2f} | {avg_dl['6.bin']:6.2f} | {t_mean:6.2f}s (n={n})")
