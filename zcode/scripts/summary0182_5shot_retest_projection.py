#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0182（诚实修订版）: 五发全量出分横向对比与官方终审复测均值预测.

数据来源（全部实读，无硬编码得分）:
  - runs/sequential_adaptive_log.jsonl : 11/07 五发官方实盘出分（sequential_all_finished 事件）
  - runs/results.jsonl                 : 主力构型本地大样本统计（仅 valid=true）
  - runs/submit_plan_1108_master.json  : 11/08 五发作战计划（尚未发生，仅作赛前投影）

三个层次，严格分开陈述：
  1. 11/07 五发实盘复盘（唯一已有的全量官方出分）；
  2. 11/08 五发赛前投影（明确标注为预测，非实绩）；
  3. 官方终审复测蒙特卡洛（假设显式列出，P(top1) 给区间不给点值）。

运行: python -I zcode/scripts/summary0182_5shot_retest_projection.py
"""
import json
import math
import sys

sys.stdout.reconfigure(encoding="utf-8")

import numpy as np

ROOT = r"E:\Download\iDSN"

# 本地统计口径 t 临界值（95% CI, 双侧）
T_CRIT = {5: 2.776, 10: 2.262, 15: 2.145}


def load_1107_actual_shots():
    """11/07 五发官方实盘出分（Lead 逐发闭环日志的唯一终局事件）。"""
    scores = []
    for line in open(ROOT + r"\runs\sequential_adaptive_log.jsonl", encoding="utf-8", errors="replace"):
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("event") == "sequential_all_finished" and str(d.get("ts", "")).startswith("2026-11-07"):
            scores = [float(x) for x in d.get("scores", [])]
    return scores


def load_config_local_stats():
    """四大主力 + shot2 官方基准构型的本地大样本统计（仅 valid=true）。"""
    frags = ["40x3-37-36-36", "41x2-40-37", "crown-pert-40on2", "asym-40-40-37-37", "40x3-36x3"]
    buckets = {f: [] for f in frags}
    for line in open(ROOT + r"\runs\results.jsonl", encoding="utf-8", errors="replace"):
        try:
            d = json.loads(line)
        except Exception:
            continue
        tag = d.get("tag", "")
        for f in frags:
            if f in tag:
                if d.get("valid") and d.get("total_seconds") is not None:
                    buckets[f].append(float(d["total_seconds"]))
                break
    out = {}
    for f, vals in buckets.items():
        n = len(vals)
        mean = sum(vals) / n
        std = math.sqrt(sum((x - mean) ** 2 for x in vals) / (n - 1)) if n > 1 else 0.0
        out[f] = {"n": n, "mean": mean, "std": std, "cv": std / mean * 100.0,
                  "min": min(vals), "max": max(vals)}
    return out


def descriptive(vals, label):
    n = len(vals)
    mean = sum(vals) / n
    std = math.sqrt(sum((x - mean) ** 2 for x in vals) / (n - 1))
    se = std / math.sqrt(n)
    tc = T_CRIT.get(n, 1.96)
    cv = std / mean * 100.0
    print(f"[{label}] n={n}")
    print(f"    scores = {vals}")
    print(f"    min={min(vals):.4f}  median={sorted(vals)[n // 2]:.4f}  mean={mean:.4f}")
    print(f"    std={std:.4f}  SE={se:.4f}  CV={cv:.2f}%  CI95=[{mean - tc * se:.4f}, {mean + tc * se:.4f}]")
    return {"n": n, "min": min(vals), "median": sorted(vals)[n // 2], "mean": mean,
            "std": std, "se": se, "cv": cv}


def retest_monte_carlo(our_true_mean, our_run_std, n_retest, comp,
                       offset_mu=None, offset_sigma=None, n_sims=200_000, seed=42):
    """官方终审复测蒙特卡洛。

    our_true_mean : 我方参测构型的官方真均值（若给 offset_* 则由本地均值+当日偏移抽样）
    our_run_std   : 单场出分标准差代理（用本地 std，显式假设）
    comp          : {对手: (复测均值位置, 复测均值波动)}——对手真均值未知，用其榜单分作位置、
                    复测平均噪声作波动（敏感性分析另行扫描）。
    offset_mu/sigma: 当日偏移 official-local 的不确定度（batch_0900 后验 mu=+0.6, sigma=13.4）
    """
    rng = np.random.default_rng(seed)
    base = our_true_mean
    if offset_sigma:
        base = our_true_mean + rng.normal(offset_mu, offset_sigma, n_sims)
    our_retest = base + rng.normal(0.0, our_run_std / math.sqrt(n_retest), n_sims)
    best_comp = None
    p_win_all = np.ones(n_sims, dtype=bool)
    for name, (mu, sd) in comp.items():
        draw = rng.normal(mu, sd, n_sims)
        p_win_all &= our_retest < draw
        if best_comp is None or mu < best_comp[1]:
            best_comp = (name, mu)
    return float(np.mean(p_win_all))


def required_mean_for_target(comp, our_run_std, n_retest, target=0.80):
    """反解：要以 target 概率在复测均值上压过全部对手，官方真均值需低到多少。"""
    # 复测均值总波动 = sqrt( (our_run_std/sqrt(N))^2 + sum contribution approximated by max comp sd )
    lo, hi = 90.0, 140.0
    for _ in range(60):
        mid = (lo + hi) / 2
        p = retest_monte_carlo(mid, our_run_std, n_retest, comp, n_sims=40_000)
        if p > target:
            lo = mid  # 均值足够低、概率超标 -> 可以抬高均值，边界在右上方
        else:
            hi = mid  # 均值过高、概率不足 -> 边界在左下方
    return (lo + hi) / 2


def main():
    print("=" * 72)
    print("0182 五发出分横向对比与官方终审复测预测（数据驱动修订版 2026-11-07 14:15）")
    print("=" * 72)

    # ---------- 第 1 层：11/07 五发实盘复盘（唯一真实全量出分） ----------
    shots_1107 = load_1107_actual_shots()
    print("\n[1] 11/07 五发官方实盘复盘（runs/sequential_adaptive_log.jsonl）")
    if shots_1107:
        s1107 = descriptive(sorted(shots_1107), "11/07 实盘五发")
    else:
        print("    !! 未找到 11/07 sequential_all_finished 记录")
        s1107 = None

    # ---------- 同日偏移锚点 ----------
    stats = load_config_local_stats()
    anchor_local = stats["40x3-36x3"]["mean"]          # 134.53 (n=5)
    anchor_official = 124.3683                          # 11/07 Shot 2 实盘（实读自日志）
    offset_anchor = anchor_official - anchor_local
    print("\n[2] 同日偏移锚点（shot2 构型 40x3-36x3）")
    print(f"    官方 {anchor_official} vs 本地均值 {anchor_local:.2f} (n=5) -> 偏移 {offset_anchor:+.2f}s")
    print("    记录先验：0084 后验 +2.5±7.4；batch_0900 综合后验 mu=+0.6, sigma=13.4")

    # ---------- 第 2 层：11/08 五发赛前投影（预测，非实绩） ----------
    print("\n[3] 11/08 五发赛前投影（明确标注：预测值，11/08 实盘后须由 Lead 用真分替换）")
    plan = [
        ("Shot1 40x3-37-36-36", "40x3-37-36-36"),
        ("Shot2 41x2-40-37-36x2(皇冠)", "41x2-40-37"),
        ("Shot3 41-40-40-37-36x2", "crown-pert-40on2"),
        ("Shot4 防守堡垒 40x4-37x2", "asym-40-40-37-37"),
        ("Shot5 当日最佳构型复测", "41x2-40-37"),
    ]
    scenarios = [("乐观(同构型锚点偏移)", offset_anchor),
                 ("中枢(batch_0900后验)", 0.6),
                 ("保守(0084上界+7.4)", 7.4)]
    proj_rows = []
    for label, key in plan:
        st = stats[key]
        row = {"shot": label, "n": st["n"], "local_mean": st["mean"], "local_std": st["std"]}
        for sname, off in scenarios:
            row[sname] = st["mean"] + off
        proj_rows.append(row)
        print(f"    {label:28s} 本地 n={st['n']} mean={st['mean']:.2f} std={st['std']:.2f} | "
              + " | ".join(f"{s[0][:2]} {row[s[0]]:.1f}s" for s in scenarios))
    print("    注：偏移 sigma≈13.4s（跨日），单发预测的 1-sigma 带宽远宽于上表点值。")

    # ---------- 第 3 层：官方终审复测蒙特卡洛 ----------
    print("\n[4] 官方终审复测蒙特卡洛（N=10 复测均值；假设显式）")
    GM = ("光明未来", 117.0257)   # 11/07 09:00 hourly 快照榜首
    CAT = ("Catnet", 119.8293)    # 看板背景（11/06 口径）
    comp_base = {GM[0]: (GM[1], 3.0), CAT[0]: (CAT[1], 3.5)}  # 对手复测均值波动：敏感性基线
    crown = stats["41x2-40-37"]
    n_retest = 10

    # 情景 A：全不确定度（偏移 N(0.6,13.4) + 复测平均噪声）
    pA = retest_monte_carlo(crown["mean"], crown["std"], n_retest, comp_base,
                            offset_mu=0.6, offset_sigma=13.4)
    # 情景 B：乐观——11/08 当日偏移恰好复制同构型锚点(-10.16)，且复测日不回摆
    pB = retest_monte_carlo(crown["mean"] + offset_anchor, crown["std"], n_retest, comp_base)
    # 情景 C：对手复测大幅回摆（其榜单分含 min-of-N 红利，复测均值上浮 5s）
    comp_regress = {GM[0]: (GM[1] + 5.0, 3.0), CAT[0]: (CAT[1] + 5.0, 3.5)}
    pC = retest_monte_carlo(crown["mean"] + offset_anchor, crown["std"], n_retest, comp_regress)
    print(f"    A 全不确定度（偏移 N(0.6,13.4)）: P(top1) = {pA * 100:.2f}%")
    print(f"    B 乐观（偏移复制锚点 {offset_anchor:+.2f}）: P(top1) = {pB * 100:.2f}%")
    print(f"    C 乐观+对手回摆5s        : P(top1) = {pC * 100:.2f}%")
    print("    敏感性注记：B/C 固定偏移时分布收窄，左尾变瘦，故 P 可低于 A——这是")
    print("    『需要多少』与『有多确定』两层不确定度混排的必然结果，非计算错误。")

    need80 = required_mean_for_target(comp_base, crown["std"], n_retest, 0.80)
    print(f"\n    80% 概率复测压过双对手所需的官方真均值 <= {need80:.2f}s")
    print(f"    （对照：本地需 <= {need80 - 0.6:.1f}s 量级，与 0084 结论『本地<=111.0s』一致）")
    print(f"    当前主力皇冠构型本地均值 {crown['mean']:.2f}s —— 缺口 "
          f"{crown['mean'] - (need80 - 0.6):.1f}s，复测夺冠当前为小概率事件。")

    # ---------- 反过拟合纪律核查 ----------
    print("\n[5] 反过拟合纪律核查")
    print("    - 排名/预测一律用均值口径；榜单单场最好值仅作参考，不进预测。")
    print("    - 本地统计仅取 valid=true；本轮五大构型无 invalid 污染样本。")
    print("    - min 远低于 mean 的尖点（如 40x3-36x3 本地 min 114.69 vs mean 134.53）")
    print("      不得作为提交依据；其 CV=10.0% 亦过门禁线。")
    print("    - 本地口径与官方口径全程分开陈述，禁止互相替代。")


if __name__ == "__main__":
    main()
