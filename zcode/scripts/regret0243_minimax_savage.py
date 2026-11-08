# -*- coding: utf-8 -*-
"""任务 0243：极小极大遗憾（Savage 准则）在极端网络对抗下的最坏情况分析。

候选集 = 11/08 决选 5 发对应的 3 个 distinct 配置树（取自 runs/seq_1108_shot_*.json，
与其本地证据族在 results.jsonl 中的 config 做逐目录一致性校验后取样本）。

状态构造（两层，全部基于真实数据/已发表审计，无虚构物理）：
  Layer A（数据态）：候选自身本地样本的经验分位数态 q∈{P25,P50,P75,P90,max}。
    解释：同一冲击强度作用于所有候选（共同分位水平），regret(c,q)=Q_c(q)−min_c' Q_c'(q)。
  Layer B（机制态）：引用 0085/0086 已审计的实测数字做差分界——
    - 定理1（共模抵消）：环境态若对所有候选加同一偏移 δ，regret 不变。
      官方-本地同日偏移（0084：+2.5±7.4s；11/06 同日 −7.8/−10.2s）即共模 → 不改变排序。
    - 定理2（差分上界，0085 实测）：候选仅在 bin1-3 速率不同（40/41，尾部全 36/36）。
      0085 柯尔莫哥洛夫解给出 70ms 阵风窗累计丢包 leak36=37 pkts、leak40=85 pkts
      → 最坏线性梯度 12 pkts/窗/+1 rate。对 bin1-2 体积（10+20MB）施加
      「每窗都在阵风」的最坏假设，算出 C2/C3 相对 C1 的额外丢包时间代价上界
      （1200B/pkt、瓶颈 12.5MB/s、开环窗 CC 放大 ≤2，出处 0085/0086）。
    - 巨流/永久饱和态（0086）：份额地板 0.464C 对全 leak 候选共模；bin5/6 全 36/36
      → 按定理1差分为零。
  官方态矩阵：三棵树无任何真实官方出分（11/07 night 5 发是其它构型；
    sequential_1108_state.json 118.13 系列为 dry-run mock，按红线纪律排除）——
    如实声明为数据缺口，不虚构。

判定：Savage 选择 = argmin_c max_state regret(c,·)；核对其总最大遗憾是否 ≤ 2.5s。
bootstrap（族内重采样 B=10000，seed=42）给出 max-regret 的抽样分布与 P(≤2.5)。

输出：stdout + zcode/scripts/_0243_out.md。
合规：纯本地计算，只读 runs/ 与 docs/，不联网、不提交。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"
OUT_MD = ROOT / "zcode" / "scripts" / "_0243_out.md"

# ---- 0085/0086 已审计常量（引用，非新假设）----
PKT_BYTES = 1200.0            # QUIC 净荷（0085）
C_MBPS = 12.5                 # 瓶颈 100 Mbps（0085/0086）
GUST_WIN_S = 0.070            # 阵风反应窗 70ms（0085，开环有效性窗口）
LEAK36_LOSS_PKTS = 37.0       # 0085 实测：70ms 阵风窗 leak36 累计丢包
LEAK40_LOSS_PKTS = 85.0       # 0085 实测：70ms 阵风窗 leak40 累计丢包
CC_AMPLIFY = 2.0              # 开环窗内 CC 反应放大上界（0085 开环窗口径，保守）
BIN_MB = [10.0, 20.0, 40.0, 80.0, 160.0, 320.0]  # 官方文件（docs/extracted/六载穿柜.md）
LEAK_INTERVAL_US = 4000

# 决选候选：tag → (seq 文件, 本地证据族 tag 基名)
CANDIDATES = {
    "C1-steady-40x3-37-36x2": ("seq_1108_shot_1.json",
                               "test-anchor-shot2-pert-40x3-37-36-36"),
    "C2-crown-41x2-40-37-36x2": ("seq_1108_shot_2.json",
                                 "test-leak-asym-41x2-40-37-36x2"),
    "C3-crown-pert-40on2": ("seq_1108_shot_3.json",
                            "test-crown-pert-40on2"),
}
QUANTILE_STATES = [0.25, 0.50, 0.75, 0.90, 1.00]
TARGET = 2.5


def load_shot_tree(seq_name: str) -> dict[int, tuple[str, dict]]:
    d = json.load(open(RUNS / seq_name, encoding="utf-8"))
    cfgs = d[0]["configs"]
    return {int(k): (v[0], v[1]) for k, v in cfgs.items()}


def load_family_samples(base_tag: str):
    """从 results.jsonl 取该族全部有效样本（含 -rN 后缀），并校验 config 与决选树一致。"""
    samples, ref_cfg = [], None
    for ln in (RUNS / "results.jsonl").read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        r = json.loads(ln)
        tag = r.get("tag", "")
        if not re.fullmatch(re.escape(base_tag) + r"(-r\d+)?", tag):
            continue
        if not r.get("valid") or tag.startswith("load-"):
            continue
        if ref_cfg is None:
            ref_cfg = r["config"]
        samples.append(float(r["total_seconds"]))
    return samples, ref_cfg


def cfg_to_tree(cfg: dict) -> dict[int, tuple[str, dict]]:
    out = {}
    for k, v in cfg.items():
        mode, param_str = v.split(":", 1)
        params = {}
        for kv in param_str.split(","):
            if kv:
                a, b = kv.split("=", 1)
                params[a] = int(b)
        out[int(k)] = (mode, params)
    return out


def tree_diff(a: dict[int, tuple[str, dict]], b: dict[int, tuple[str, dict]]):
    """返回 [(bin, rate_a, rate_b)]，仅列速率不同的 bin。"""
    out = []
    for n in range(1, 7):
        ra, rb = a[n][1]["leak_rate"], b[n][1]["leak_rate"]
        if ra != rb:
            out.append((n, ra, rb))
    return out


def gust_diff_bound(cand_tree, base_tree):
    """0085 机制差分上界：候选相对基准在速率不同 bin 上的额外丢包时间代价（秒）。

    最坏假设：bin 传输的每个 70ms 窗都在阵风；速率 +1 的窗内额外丢包按
    (85−37)/(40−36)=12 pkts 线性外推；丢包代价 = 重传体积/瓶颈速率 × CC 放大 ≤2。
    """
    diff_bins = tree_diff(cand_tree, base_tree)  # [(bin, rate_cand, rate_base)]
    grad = (LEAK40_LOSS_PKTS - LEAK36_LOSS_PKTS) / (40.0 - 36.0)  # pkts/window/rate
    extra_pkts = 0.0
    for n, rate_cand, rate_base in diff_bins:
        pkt_rate = rate_cand / LEAK_INTERVAL_US * 1e6          # pkts/s（T_e=interval/rate）
        goodput_MBps = pkt_rate * PKT_BYTES / 1e6
        n_windows = BIN_MB[n - 1] / goodput_MBps / GUST_WIN_S
        extra_pkts += n_windows * grad * abs(rate_cand - rate_base)
    extra_s = extra_pkts * PKT_BYTES / 1e6 / C_MBPS * CC_AMPLIFY
    return extra_s, extra_pkts, diff_bins


def regret_matrix(quant: dict[str, np.ndarray]):
    states = {}
    for q in QUANTILE_STATES:
        vals = {c: float(np.quantile(x, q)) for c, x in quant.items()}
        best = min(vals.values())
        states[f"q={q:.2f}"] = {c: vals[c] - best for c in vals}
    return states, {c: vals for c, vals in quant.items()}


def main() -> int:
    lines = []
    w = lines.append
    w("# 0243 输出 — 极小极大遗憾（Savage）最坏情况分析（真实数据）\n")
    w(f"生成时间：{__import__('datetime').datetime.now():%Y-%m-%d %H:%M:%S}\n")

    # ---- 0. 候选装载与一致性校验
    w("## 0. 候选装载与配置一致性校验\n")
    trees, samples = {}, {}
    for name, (seq_name, base_tag) in CANDIDATES.items():
        tree = load_shot_tree(seq_name)
        fam, ref_cfg = load_family_samples(base_tag)
        if ref_cfg is None or len(fam) == 0:
            raise SystemExit(f"[FATAL] 证据族 {base_tag} 无有效样本")
        ev_tree = cfg_to_tree(ref_cfg)
        diffs = tree_diff(tree, ev_tree)
        ok = not diffs
        w(f"- **{name}** ← `{seq_name}` + 证据族 `{base_tag}`（n={len(fam)}）："
          f"逐目录 config {'完全一致 ✓' if ok else f'不一致 ✗ {diffs}'}")
        if not ok:
            raise SystemExit(f"[FATAL] {name} 决选树与本地证据族配置不一致：{diffs}")
        trees[name] = tree
        samples[name] = np.array(fam)
    w("")

    # ---- 1. Layer A 数据态
    w("## 1. Layer A（数据态）：经验分位数遗憾矩阵\n")
    quant = {c: np.quantile(x, QUANTILE_STATES) for c, x in samples.items()}
    w("| 候选 | n | mean | std | min | P50 | P90 | max |")
    w("|---|---|---|---|---|---|---|---|")
    for c, x in samples.items():
        w(f"| {c} | {len(x)} | {x.mean():.2f} | {x.std(ddof=1):.2f} | "
          f"{x.min():.2f} | {np.quantile(x, .5):.2f} | {np.quantile(x, .9):.2f} | "
          f"{x.max():.2f} |")
    w("")
    states, _ = regret_matrix(samples)
    w("| 状态 | " + " | ".join(CANDIDATES) + " |")
    w("|---|" + "---|" * len(CANDIDATES))
    for sname, row in states.items():
        w(f"| {sname} | " + " | ".join(f"{row[c]:.2f}" for c in CANDIDATES) + " |")
    w("")
    max_regret = {c: max(row[c] for row in states.values()) for c in CANDIDATES}
    savage = min(max_regret, key=max_regret.get)
    w("### Layer A 最大遗憾与 Savage 选择\n")
    for c in CANDIDATES:
        w(f"- {c}: max regret = {max_regret[c]:.2f}s")
    w(f"- **Savage 选择（Layer A）：{savage}**（最大遗憾 {max_regret[savage]:.2f}s）")
    w("")

    # ---- 2. Layer B 机制态
    w("## 2. Layer B（机制态）：0085/0086 实测机制差分界\n")
    w("- **定理1（共模抵消）**：官方-本地同日偏移（0084 同日 +2.5±7.4s；11/06 −7.8/−10.2s）"
      "对所有候选共模加 δ → regret(c, s+δ)=regret(c, s)，Savage 排序不变。")
    w("- **巨流/永久饱和态（0086）**：份额地板 0.464C 对全 leak 候选共模，"
      "且三候选 bin5/6 全为 36/36（长尾体积 480MB 完全同构）→ 该态差分为零。")
    w("- **阵风态差分（0085 实测梯度外推，最坏「每窗都在阵风」假设）**：")
    base = trees["C1-steady-40x3-37-36x2"]
    layer_b = {}
    for c, tree in trees.items():
        s, pk, diffs = gust_diff_bound(tree, base)
        layer_b[c] = s
        diff_desc = ", ".join(f"bin{n}:{rc}vs{rb}" for n, rc, rb in diffs) or "（无差分 bin）"
        w(f"  - {c} vs C1 差分 bin：{diff_desc} → 额外丢包 {pk:.0f} pkts → "
          f"时间代价上界 **{s:.3f}s**")
    w("  （常量出处：1200B/pkt、C=12.5MB/s、70ms 阵风窗、leak36/40 窗丢包 37/85 pkts、"
      "CC 放大 ≤2 —— 均为 0085/0086 已审计数字；梯度线性外推偏保守。）")
    w("")

    total_max_regret = {c: max_regret[c] + layer_b[c] for c in CANDIDATES}
    savage_b = min(total_max_regret, key=total_max_regret.get)
    w("### Layer A+B 合并最大遗憾\n")
    for c in CANDIDATES:
        w(f"- {c}: {max_regret[c]:.2f}s (数据态) + {layer_b[c]:.3f}s (机制态) "
          f"= **{total_max_regret[c]:.2f}s**")
    w(f"- **Savage 选择（A+B）：{savage_b}**，总最大遗憾 {total_max_regret[savage_b]:.2f}s")
    w("")

    # ---- 3. bootstrap 校准
    rng = np.random.default_rng(42)
    B = 10000
    boot_max = {c: [] for c in CANDIDATES}
    savage_hits = 0
    for _ in range(B):
        bs = {c: rng.choice(samples[c], size=len(samples[c]), replace=True)
              for c in CANDIDATES}
        st, _ = regret_matrix(bs)
        mr = {c: max(row[c] for row in st.values()) for c in CANDIDATES}
        for c in CANDIDATES:
            boot_max[c].append(mr[c])
        if min(mr, key=mr.get) == savage:
            savage_hits += 1
    w("## 3. Bootstrap 校准（族内重采样 B=%d，seed=42）\n" % B)
    w("| 候选 | max-regret P50 | P95 | P(max≤2.5s) |")
    w("|---|---|---|---|")
    for c in CANDIDATES:
        v = np.array(boot_max[c])
        w(f"| {c} | {np.quantile(v, .5):.2f} | {np.quantile(v, .95):.2f} | "
          f"{(v <= TARGET).mean() * 100:.1f}% |")
    w(f"- Savage 选择 {savage} 在 bootstrap 中的复制率：{savage_hits / B * 100:.1f}%")
    v_sav = np.array(boot_max[savage])
    w(f"- Savage 选择 max-regret 的 95% 区间：[{np.quantile(v_sav, .025):.2f}, "
      f"{np.quantile(v_sav, .975):.2f}]s")
    w("")

    # ---- 4. 判定
    w("## 4. 考核目标判定（所有极端对抗态最大遗憾 ≤ 2.5s）\n")
    ok_pt = total_max_regret[savage_b] <= TARGET
    p_ok = (np.array(boot_max[savage_b]) <= TARGET).mean()
    w(f"1. **点估计**：Savage 候选 {savage_b} 在全部已构造状态（数据态 5 档 + 机制态 3 类）下"
      f"总最大遗憾 = **{total_max_regret[savage_b]:.2f}s**，"
      f"{'≤ 2.5s，目标点估计成立' if ok_pt else '> 2.5s，目标点估计不成立'}。")
    w(f"2. **抽样校准**：bootstrap 下 P(max regret ≤ 2.5s) = {p_ok * 100:.1f}%；"
      f"95% 区间 [{np.quantile(v_sav, .025):.2f}, {np.quantile(v_sav, .975):.2f}]s。"
      + ("小样本方差是主要不确定性来源。" if p_ok < 0.95 else
         "即便族内重抽样扰动，≤2.5s 依然稳健。"))
    w("3. **覆盖声明**：官方态矩阵缺失（三棵决选树无真实官方出分；dry-run mock 已剔除），"
      "故「所有极端对抗状态」只能覆盖到：本地实证分位态 + 0085 阵风差分态 + "
      "0086 巨流/饱和共模态。任何超出该集合的对抗形态（如官方侧未知调度突变）不在本审计能力内。")
    w("4. 若目标被解读为「任意候选在任意态下 regret ≤ 2.5s」，则数据态 q=0.90/1.00 处"
      f"非 Savage 候选（如 crown 族）遗憾可达 {max(max_regret.values()):.2f}s —— 该强解读"
      "不成立；Savage 准则的本义是**选最小化最大遗憾的那个候选**，本审计按本义判定。")

    text = "\n".join(lines) + "\n"
    OUT_MD.write_text(text, encoding="utf-8")
    print(text)
    print(f"[OK] 已写出 {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
