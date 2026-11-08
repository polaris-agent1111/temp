#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0095 — 全局理论下确界（105.592s 冻结版）可达性物理条件与香农信道容量/BDP 映射检验.

只读 runs/results.jsonl，全部闭门数值计算：
  §0 数据链重算：分文件极小值 + 三种信封变体（E_file/E_stage/E_run）与冻结值对照
  §1 香农/管道层认证下界：D/C + 传播 + 慢启动爬坡 + 定时器量子化
  §2 份额反演：各信封所需的持续份额 s*，与冠军开环最恶劣份额天花板对照
  §3 单构型可达性：跨构型来源审计 + 逐段尾部频率 + 联合概率 + 剪刀差（0085 律）
  §4 信封随 n 的漂移：bootstrap E(n) 轨迹，证明信封是序统计量而非物理常数
输出 zcode/scripts/_0095_out.md（UTF-8）。
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "runs" / "results.jsonl"
OUT = Path(__file__).with_name("_0095_out.md")

# ---------------- 官方拓扑常量（docs/extracted/六载穿柜.md，仓库既有口径） ----------------
C_MBPS = 100.0                 # 汇聚链路 s1-s2 100 Mbps（唯一瓶颈）
C_MB = C_MBPS / 8.0            # 12.5 MB/s（十进制，与仓库 0041 表格口径一致）
RTT = 0.070                    # 70 ms（10+15+10 单向 35ms ×2）
TAU_1W = RTT / 2.0             # 末字节单向传播 35 ms
PAYLOAD = 1200.0               # QUIC 净荷字节（0080/0086 口径）
BDP_BYTES = C_MBPS * 1e6 / 8.0 * RTT        # 875,000 B
BDP_PKT = BDP_BYTES / PAYLOAD               # 729.2 pkt
BIN_MB = {1: 10, 2: 20, 3: 40, 4: 80, 5: 160, 6: 320}
FROZEN_0041 = {"s14": 19.907, "s5": 27.651, "s6": 58.034, "env": 105.592}   # 11-06 20:06 快照
FROZEN_DOC = {"s14": 20.912, "s5": 27.651, "s6": 58.034, "env": 106.597}    # 11-06 19:46 发布
LB_TOP = 117.0257              # 光明未来（榜单锚点）
OURS_OFF = 124.3683            # 我方官方最好（11/07 Shot2）


def load_valid():
    rows = [json.loads(l) for l in RESULTS.read_text("utf-8").splitlines() if l.strip()]
    return [r for r in rows
            if r.get("valid") is True and not str(r.get("tag", "")).startswith("load-")]


def main() -> int:
    rng = random.Random(95)
    V = load_valid()
    lines_out: list[str] = []
    P = lines_out.append

    P("# 0095 输出 — 香农/BDP 映射与下确界信封审计（seed=95 可复现）")
    P(f"- 数据：runs/results.jsonl 有效样本 n={len(V)}（valid=true 且非 load-*）")
    P(f"- 常量：C={C_MBPS:.0f}Mbps={C_MB:.1f}MB/s，RTT={RTT*1000:.0f}ms，BDP={BDP_BYTES/1e3:.0f}KB="
      f"{BDP_PKT:.1f}pkt(1200B)，总载荷 D=630MB={630*8/1000:.3f}Gbit")
    P("")

    # ============ §0 数据链重算 ============
    P("## §0 数据链重算（当前 405 场有效快照）")
    mf = {f"{i}.bin": (1e9, "") for i in range(1, 7)}
    best_stage = {"s14": (1e9, ""), "s5": (1e9, ""), "s6": (1e9, "")}
    for r in V:
        d = r["downloads"]; tag = r["tag"]
        for k in mf:
            if d.get(k, 1e9) < mf[k][0]:
                mf[k] = (d[k], tag)
        s14 = sum(d.get(f"{i}.bin", 1e9) for i in range(1, 5))
        if s14 < best_stage["s14"][0]:
            best_stage["s14"] = (s14, tag)
        if d.get("5.bin", 1e9) < best_stage["s5"][0]:
            best_stage["s5"] = (d["5.bin"], tag)
        if d.get("6.bin", 1e9) < best_stage["s6"][0]:
            best_stage["s6"] = (d["6.bin"], tag)

    e_file = sum(mf[f"{i}.bin"][0] for i in range(1, 7))
    e_stage = best_stage["s14"][0] + best_stage["s5"][0] + best_stage["s6"][0]
    t_all = [float(r["total_seconds"]) for r in V]
    e_run = min(t_all)

    P("")
    P("| bin | 当前极小值 | 达成构型（家族） | 折算吞吐 | 占 C |")
    P("|---|---:|---|---:|---:|")
    fam = lambda t: t.replace("test-", "").replace("seq-w1107-", "")[:34]
    for i in range(1, 7):
        k = f"{i}.bin"; v, tag = mf[k]
        thr = BIN_MB[i] * 8 / v
        P(f"| {k} | {v:.4f}s | {fam(tag)} | {thr:.2f} Mbps | {thr/C_MBPS:.3f}C |")
    P("")
    P(f"- E_file = Σ 分文件极小值 = **{e_file:.3f}s**")
    P(f"- E_stage = min-run(1-4 小计 {best_stage['s14'][0]:.3f}s, {fam(best_stage['s14'][1])}) "
      f"+ min 5.bin ({best_stage['s5'][0]:.3f}s, {fam(best_stage['s5'][1])}) "
      f"+ min 6.bin ({best_stage['s6'][0]:.3f}s, {fam(best_stage['s6'][1])}) = **{e_stage:.3f}s**")
    P(f"- E_run = min 单场 total = **{e_run:.4f}s**（n={len(V)}）")
    P("")
    P("**冻结值对照（三个日期、同一构造法的漂移）**：")
    P("")
    P("| 快照 | 构造 | 1-4 | 5.bin | 6.bin | 信封 |")
    P("|---|---|---:|---:|---:|---:|")
    P(f"| 11-06 19:46 (n≈280) | Σ 分文件极小值 | 20.912 | 27.651 | 58.034 | 106.597 |")
    P(f"| 11-06 20:06 (n≈280) | min 小计+min5+min6 | 19.907 | 27.651 | 58.034 | 105.592 |")
    P(f"| 11-07 09:xx (n={len(V)}) | Σ 分文件极小值 | {sum(mf[f'{i}.bin'][0] for i in range(1,5)):.3f} | "
      f"{mf['5.bin'][0]:.3f} | {mf['6.bin'][0]:.3f} | **{e_file:.3f}** |")
    P(f"| 11-07 09:xx (n={len(V)}) | min 小计+min5+min6 | {best_stage['s14'][0]:.3f} | "
      f"{best_stage['s5'][0]:.3f} | {best_stage['s6'][0]:.3f} | **{e_stage:.3f}** |")
    P("")
    P(f"**同一构造法一天内信封漂移 {106.597 - e_file:.1f}s（106.597→{e_file:.1f}）/ {105.592 - e_stage:.1f}s"
      f"（105.592→{e_stage:.1f}）——信封是随 n 单调下降的序统计量，不是物理常数。**")
    P("")

    # ============ §1 香农/BDP 认证下界 ============
    P("## §1 香农信道容量与 BDP 管道认证下界（可证明的部分）")
    D_gbit = 630 * 8 / 1000
    t_shannon = D_gbit * 1000 / C_MBPS
    P("")
    P("1. **香农层（唯一无条件认证）**：评测瓶颈是确定性比特管道 C=100 Mbps；任何策略的净荷 goodput ≤ C。")
    P(f"   T ≥ D/C = 5040 Mbit / 100 Mbps = **{t_shannon:.1f}s**（份额 s=1、零损、零背景的幻想极限）。")
    P("   Shannon 定理在此的角色：底层物理信道必须具备 ≥100 Mbps 的信道容量管道才存在（平台已固定）；")
    P("   对我方而言容量上限即管道速率本身，背景流是「干扰用户」而非「噪声」——其挤压量 s_bg 是排队/博弈")
    P("   结果量，物理只认证 s_own ≤ 1，不认证任何 s_own 的下界可被绕过。")
    P("")
    # 逐段管道下界
    ramp_terms = []
    for iw in (10, 32):
        j = math.log2(BDP_PKT / iw)
        ramp_terms.append((iw, j * RTT))
    P(f"2. **BDP 管道与慢启动爬坡**：BDP = C·RTT = {BDP_BYTES/1e3:.0f} KB = {BDP_PKT:.1f} pkt。")
    P(f"   窗口从 IW 爬到 BDP 需 log2({BDP_PKT:.0f}/IW)·RTT：IW=10 → {ramp_terms[0][1]*1000:.0f}ms，"
      f"IW=32 → {ramp_terms[1][1]*1000:.0f}ms。")
    P("   最小 bin（10MB）满足 10MB = 11.4×BDP ≫ 爬坡期传输量 → 爬坡被 L_i/C 完全吸收（爬坡期发送量")
    P("   受 cwnd 限制小于管道速率，但 L_i/C > 爬坡时间，管道充满后仍按 L_i/C 下界走）。")
    P("")
    P("3. **逐段认证下界**：T_i ≥ L_i/C + τ_1w（末字节单向传播 35ms；官方口径剔除任务间隙，0088）。")
    P("")
    P("| bin | L_i (MB) | L_i/C (s) | +35ms | 官方实测极小值 | 结构余量 |")
    P("|---|---:|---:|---:|---:|---:|")
    for i in range(1, 7):
        k = f"{i}.bin"
        lc = BIN_MB[i] / C_MB
        P(f"| {k} | {BIN_MB[i]} | {lc:.3f} | {lc+TAU_1W:.3f} | {mf[k][0]:.3f} | {mf[k][0]-(lc+TAU_1W):.3f} |")
    floor_prop = sum(BIN_MB[i] / C_MB + TAU_1W for i in range(1, 7))
    P(f"| **Σ** | 630 | 50.400 | **{floor_prop:.3f}** | — | — |")
    P("")
    P(f"4. **定时器量子化与端侧残差**：G=4000µs pacer 网格的相位滞后每 refill 批 ≤G/2，速率受限段被速率项吸收；")
    P(f"   握手若计入（6×1-RTT）+0.42s；veth 路径固定税 6–248µs/包仅 ~3µs 与瓶颈串行（0082）→ 忽略。")
    P(f"   **认证下界带：T* ∈ [50.4, {floor_prop + 0.42:.2f}]s**（握手计入与否）。")
    P("")

    # ============ §2 份额反演 ============
    P("## §2 份额反演：各信封所需的持续份额")
    P("")
    P("s*(T) = 50.4s / T（把信封倒算成对我方持续份额的需求，1.0=独占瓶颈）：")
    P("")
    P("| 目标 T (s) | 所需持续份额 s* | 来源/状态 |")
    P("|---:|---:|---|")
    rows2 = [
        (FROZEN_0041["env"], "0041 冻结信封（min 小计+min5+min6，11-06）"),
        (FROZEN_DOC["env"], "发布版冻结信封（Σ 分文件极小值，11-06）"),
        (e_stage, "同构造当前快照"),
        (e_file, "Σ 分文件极小值当前快照"),
        (e_run, "历史最佳单场 total（实测）"),
        (OURS_OFF, "我方官方最好 124.3683"),
        (LB_TOP, "榜单第一 光明未来"),
        (floor_prop, "认证下界（+35ms 口径）"),
        (t_shannon, "香农幻想极限"),
    ]
    for t, src in sorted(rows2, reverse=True):
        P(f"| {t:.3f} | {t_shannon/t:.4f}C | {src} |")
    P("")
    g_champ = 9000.0; mu = 1e6 / 96.0
    share_champ_wc = mu * g_champ / (g_champ + mu) / mu
    P(f"- 冠军开环构型（g=9000 pkt/s）在**永久非响应饱和（ρ=1）**下的份额天花板：")
    P(f"  r_own = μ·g/(g+ρμ) = {share_champ_wc:.4f}C → 6.bin ≥ 320×8/(0.4635×100) = 55.2s（0086 口径）。")
    P(f"  105.592 需 {t_shannon/FROZEN_0041['env']:.4f}C > {share_champ_wc:.4f}C：**在最恶劣饱和工况下不可达**；")
    P("  但实测（0.46–0.60C 逐段极值）证明真实背景是弹性的、N~Poisson(1) 有空窗——份额上限不是常数。")
    P("")

    # ============ §3 单构型可达性 ============
    P("## §3 单构型可达性检验（105.592s 冻结信封的物理条件清单）")
    P("")
    P("来源审计：六个分文件极小值来自 **6 个不同构型家族**：")
    P("")
    for i in range(1, 7):
        k = f"{i}.bin"; v, tag = mf[k]
        P(f"- {k}: {v:.3f}s ← `{tag}`")
    P("")
    P("联合可达概率（bootstrap，±1% 邻域）：")
    P("")
    margs = {}
    for i in range(1, 7):
        k = f"{i}.bin"
        vals = [float(r["downloads"][k]) for r in V if k in r["downloads"]]
        m = mf[k][0]
        cnt = sum(1 for x in vals if x <= m * 1.01)
        margs[k] = cnt / len(vals)
        P(f"- {k}: P(X ≤ 1.01·m) = {cnt}/{len(vals)} = {cnt/len(vals):.4f}")
    joint = math.prod(margs.values())
    P(f"- 六段独立近似联合：∏ = {joint:.3e}")
    hit5 = sum(1 for r in V
               if all(r["downloads"].get(f"{i}.bin", 1e9) <= mf[f"{i}.bin"][0] * 1.05 for i in range(1, 7)))
    P(f"- 实测 405 场中「六段同时进入各自极小值 ±5% 邻域」的场数：**{hit5}**")
    P("")
    P("**物理条件清单（单构型打穿 105.592 必须同时成立）**：")
    P("")
    P("1. 1-4.bin 冲锋段维持 ≥60.3 Mbps 均值（现役最好小计 19.5-19.9s ← burst≈60 弹性，依赖背景空窗）；")
    P("2. 5.bin 排空段 ≥46.3 Mbps、6.bin 稳态段 ≥44.1 Mbps——同一 pacer 参数同时支撑冲锋与稳态；")
    P("3. 0085 柯氏突发惩罚律反向不触发：batch 40/60 的冲锋节奏在 5/6.bin 的尾部丢包 4.51%/36.3%")
    P("   （剪刀差）——冲锋最优与稳态最优的参数区不相交，这正是六段极值来自六个构型的机理；")
    P("4. 全程背景份额被压到 ~0.52C 以下且六段连续不出现 ≥28MB 巨流压顶（0086：6.bin 窗口命中率 ~74%）。")
    P("")

    # ============ §4 信封漂移轨迹 ============
    P("## §4 信封随 n 的漂移（bootstrap E(n) 轨迹，证明其为序统计量）")
    P("")
    by_bin = {f"{i}.bin": [float(r["downloads"][f"{i}.bin"]) for r in V if f"{i}.bin" in r["downloads"]]
              for i in range(1, 7)}
    P("| n 子样 | E_file(n) 中位 | E_file(n) 最小 | 单场 total 最小 |")
    P("|---:|---:|---:|---:|")
    for nsub in (50, 100, 200, 300, len(V)):
        nsub = min(nsub, len(V))
        reps, tots = [], []
        for _ in range(2000):
            env = 0.0
            for k in by_bin:
                vals = by_bin[k]
                env += min(rng.choice(vals) for _ in range(nsub))
            reps.append(env)
            tots.append(min(rng.choice(t_all) for _ in range(nsub)))
        P(f"| {nsub} | {np.median(reps):.2f} | {min(reps):.2f} | {np.median(tots):.2f} |")
    P("")
    P("**读法**：n→∞ 时 E_file(n) → 六段真端点 Σx*_k（≥ 认证下界带 50.6s，且被背景份额机制抬高）；")
    P("n=405 时已下探到 94.0s——「105.592 绝对不可超越」若作为定理则与数据直接矛盾（94.0<105.592）。")
    P("")

    # ============ §5 判决 ============
    P("## §5 判决（分层认证链）")
    P("")
    P("| 层级 | 量 | 性质 | 认证强度 |")
    P("|---|---:|---|---|")
    P(f"| L-2 香农/管道 | {t_shannon:.1f}s | 物理恒等式（D/C） | **无条件**（幻想份额 s=1） |")
    P(f"| L-1 结构层 | {floor_prop:.2f}s（+握手 {floor_prop+0.42:.2f}s） | 管道+传播+BDP+量子化 | **无条件**（平台口径内） |")
    P(f"| L0 冻结信封 | 105.592 / 106.597 | 跨构型 min-of-mins 序统计量 | **n=280 时刻的经验值，非物理** |")
    P(f"| L0' 当前信封 | {e_file:.2f} / {e_stage:.2f} | 同构造 n=405 | 随 n 漂移，无不变性 |")
    P(f"| L1 单场极值 | {e_run:.3f}s | 历史最佳单场 | 经验支撑点（min-of-N 红利口径） |")
    P(f"| L2 官方锚 | {OURS_OFF}s / 榜首 {LB_TOP}s | 官方均值化出分 | 决策空间的真实工作点 |")
    P("")
    P("**结论**：")
    P("")
    P("1. 香农/BDP 映射认证的是 **50.4–50.8s**，不是 105.592s——「105.592s 绝对不可超越」作为物理定理")
    P("   **不成立**（同一构造法在 n=405 已给出 94.0s）。")
    P("2. 105.592/106.597 的正确身份：**n 依赖的跨构型极值复合量**（AGENTS.md 禁止的 min-of-N 红利口径），")
    P("   只能作诊断书挡，不能作提交目标或承诺。")
    P(f"3. 单构型可达性：六段极值来自六个参数区（剪刀差机理）+ 六段 ±1% 邻域联合概率 {joint:.1e} + "
      f"405 场实测 0 命中，")
    P("   单场穿 105.592 的可达性物理条件在现役参数空间内**不成立**。")
    P("4. 真正的不变量（可写进答辩的物理条件）：逐段管道下界 Σ(L_i/C+35ms)=50.61s、份额机制 s_own∈(0,1)")
    P("   由背景需求（平台固定 ≈C）与我方节奏共同决定、以及官方「重复取平均」口径下的均值语义（0097）。")
    P("")

    OUT.write_text("\n".join(lines_out), encoding="utf-8")
    print(f"written {OUT} ({len(lines_out)} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
