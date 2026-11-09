#!/usr/bin/env python3
"""Build research/to_human/progress-01.html (stdlib only, inline SVG)."""
import csv
import html
import json
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "research"


def bars(items, title, unit="s", w=560, color="#4a78b5", ref=None):
    h = 30 * len(items) + 40
    mx = max(v for _, v in items) * 1.15
    s = [f'<svg width="{w}" height="{h}" font-family="sans-serif" font-size="12">',
         f'<text x="0" y="14" font-weight="bold">{html.escape(title)}</text>']
    for i, (lab, v) in enumerate(items):
        y = 28 + 30 * i
        bw = (w - 230) * v / mx
        s.append(f'<text x="0" y="{y + 15}">{html.escape(lab)}</text>')
        s.append(f'<rect x="200" y="{y}" width="{bw:.1f}" height="20" fill="{color}"/>')
        s.append(f'<text x="{205 + bw:.1f}" y="{y + 15}">{v:.2f} {unit}</text>')
    if ref:
        x = 200 + (w - 230) * ref[1] / mx
        s.append(f'<line x1="{x:.1f}" y1="24" x2="{x:.1f}" y2="{h - 6}" stroke="#c33" stroke-dasharray="4"/>')
        s.append(f'<text x="{x + 3:.1f}" y="{h - 2}" fill="#c33">{html.escape(ref[0])}</text>')
    s.append("</svg>")
    return "\n".join(s)


def scatter(series, title, w=420, h=360, lo=115, hi=175):
    def X(v):
        return 50 + (w - 70) * (min(max(v, lo), hi) - lo) / (hi - lo)

    def Y(v):
        return h - 40 - (h - 70) * (min(max(v, lo), hi) - lo) / (hi - lo)
    s = [f'<svg width="{w}" height="{h}" font-family="sans-serif" font-size="11">',
         f'<text x="0" y="14" font-weight="bold">{html.escape(title)}</text>',
         f'<line x1="{X(lo)}" y1="{Y(lo)}" x2="{X(hi)}" y2="{Y(hi)}" stroke="#999" stroke-dasharray="3"/>',
         f'<text x="{w / 2 - 40}" y="{h - 8}">official (s)</text>',
         f'<text x="2" y="{h / 2}" transform="rotate(-90 10 {h / 2})">predicted (s)</text>']
    for v in range(lo, hi + 1, 10):
        s.append(f'<text x="{X(v) - 8}" y="{h - 26}">{v}</text><text x="22" y="{Y(v) + 4}">{v}</text>')
    for k, (name, pts, col) in enumerate(series):
        for t, p in pts:
            s.append(f'<circle cx="{X(t):.1f}" cy="{Y(p):.1f}" r="4" fill="{col}" opacity="0.8"/>')
        s.append(f'<circle cx="{w - 150}" cy="{30 + 16 * k}" r="4" fill="{col}"/><text x="{w - 140}" y="{34 + 16 * k}">{html.escape(name)}</text>')
    s.append("</svg>")
    return "\n".join(s)


def main():
    v1 = json.loads((R / "experiments/H0-baseline-fidelity/results/v1_cubic_100.json").read_text("utf-8"))
    grid = json.loads((R / "experiments/H1-sim2-mechanistic/results/grid1.json").read_text("utf-8"))
    best = min(grid, key=lambda r: r["loo_rmse"])
    med = st.median(r["loo_rmse"] for r in grid)
    crn = json.loads((R / "experiments/H3-crn-sensitivity/results/crn.json").read_text("utf-8"))
    raw = crn["raw"]
    eff_sd = st.mean(st.stdev([raw[f"pert|{s}|{k}"] - raw[f"base|{s}|0"] for s in range(100, 106)]) for k in range(6))

    fid = bars([("v1 (existing sim)", v1["loo_rmse"]), ("sim_v2 median of 24", med),
                ("sim_v2 best of 24", best["loo_rmse"]), ("constant (predict mean)", 9.04)],
               "LOO-RMSE vs 10 official points (lower = better)", ref=("constant", 9.04))
    sc = scatter([("v1", [(p["target"], p["pred"]) for p in v1["points"] if p["id"] != "v1_leak9_1000"], "#d08030"),
                  ("sim_v2 best", [(p["target"], p["pred"]) for p in best["points"] if p["id"] != "v1_leak9_1000"], "#3070c0")],
                 "predicted vs official (perfect = dashed diagonal)")
    noise = bars([("local: across bg seeds (sim)", crn["bg_seed_sd"]), ("local evaluator, 1 run (measured)", 11.58),
                  ("±1-pkt effect, sd across seeds (sim)", eff_sd), ("official: fit residual", 1.48),
                  ("sim: same seed, jitter only", crn["repeat_sd_mean"]), ("official: identical repeat", 0.47)],
                 "Where the variance is (sd, seconds)", color="#5a9a5a")
    body = f"""<!doctype html><html><head><meta charset="utf-8"><title>iDSN Q1 research progress 01</title>
<style>body{{font-family:sans-serif;max-width:900px;margin:2em auto;line-height:1.5}}td,th{{border:1px solid #ccc;padding:3px 8px}}table{{border-collapse:collapse}}</style></head><body>
<h1>iDSN 题目1：离线评测可信度研究（进展 01，2026-11-09）</h1>
<h2>问题</h2>
<p>本地仿真器能否替代官方评测来给 pacer 配置排序？官方分数里多大的差异才算真实？</p>
<h2>结论 1：两个仿真器都无法对官方结果排序</h2>
{fid}
<p>指标是 10 个官方点的留一 RMSE（加一个全局偏移）。现有仿真器 v1 为 22.7 s，不如“直接预测均值”的 9.0 s，秩相关为 −0.06。
新写的机理仿真器 sim_v2 跑了 24 个结构变体（逐流 TCP 背景流、显式队列/拥塞控制/定时器），最好的一个也只有 9.8 s。
两者都缺少“40–44 包突发变慢”的右壁，<code>30/50/5000</code> 也预测错。</p>
{sc}
<h2>结论 2：官方是固定种子基准，±1 包微调的效果只对这组种子成立</h2>
{noise}
<ul>
<li>官方同配置重复提交：标准差约 0.47 s。本地评测器单次：约 11.6 s（用系统时间做种子）。</li>
<li>在 sim_v2 中固定背景种子后，方差下降约 20 倍。这与官方表现一致：固定种子有效。</li>
<li>对冠军阶梯做 ±1 包修改，平均效果只有约 0.4 s。但在任意一组固定种子下，同一修改会表现出 ±2 s（标准差）、最大 4.6 s 的效果。</li>
<li>所以 S2−S1 = +2.6 s 和 S3−S1 = +2.7 s 很可能是“这组种子特有”的效应，不能证明“41 包越过红线”。规则写明头部提交会换种子复测，微调带来的提升预计会消失。</li>
<li>阶梯相对 uniform 36/40 的 −11.0 s 远大于所有噪声源（z ≥ 5），是唯一可信的结构性官方结论。</li>
</ul>
<h2>建议</h2>
<ol>
<li>不要用仿真器（v1 或 sim_v2）的数值或排序来选择提交。</li>
<li>不要把官方额度花在 ±1 包的阶梯微调上。只有 ≥ 5 s 的差异，或者被结构不同的配置复现的差异，才算可迁移的证据。</li>
<li>本地 A/B 测试应固定背景种子并比较配对差值（TrafficGenerator 支持 <code>-s</code>；本地评测器是否暴露这个参数还没确认）。这样噪声可降约 20 倍。这只改本地测量方法，不改提交内容。</li>
<li>最大的信息缺口是：带旁路的模块（token_bucket / precise，<code>enable_n_in_flight=1</code>）在官方 4 ms 定时器下的表现。目前只有一个官方点（burst=200，140.9 s）。榜首的 116 s 很可能在这个方向上。</li>
</ol>
<h2>下一步</h2>
<p>设计按信息量排序的官方提交方案：只做结构性对照，每发预期差异 ≥ 5 s。同时用配对种子的 sim_v2 做定性的机制检查。</p>
<p>代码与数据：<code>research/</code>（findings.md、experiments/H0–H3、src/）。</p>
</body></html>"""
    out = R / "to_human/progress-01.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, "utf-8")
    print(out)


if __name__ == "__main__":
    main()
