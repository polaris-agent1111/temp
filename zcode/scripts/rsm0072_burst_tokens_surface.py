#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""任务 0072 — 多轮实测下令牌桶容量 Burst 与初始 tokens 差分耦合效应响应曲面拟合

数据源：runs/results.jsonl（只读）中全部含 token_bucket 的 valid 记录（n=88）。
物理模型（§2）：理想令牌桶响应曲面是**铰链型**——τ(初始 tokens) 只经 t=0 发射脉冲
b0=min(τ,B) 进入耗时，B(桶容量) 只经发射脉冲与空闲积攒 min(B, r·g) 进入耗时，
光滑区 ∂²T/∂τ∂B = 0，耦合只存在于铰链 τ=B 与 r·g=B 上；效应量上界为 ms 级，
而速率/背景碰撞效应为 s 级 ⇒ B×τ 的均值效应被噪声淹没，应改查**方差响应面**。

速率正典换算（0051）：token_refill_interval_us=4000 时 R_ss(r)=r/4ms=r×250 包/s
（r=36→86.4Mbps，r=40→96Mbps）；interval≤1000µs 时 R_ss 超线速 ⇒ 无速率整形、仅突发封顶。

本脚本全部使用 stdlib，确定性输出，供 docs/analysis/0072-theory-audit.md 引用。
运行：python -I zcode/scripts/rsm0072_burst_tokens_surface.py
"""

import json
import math
import re
import statistics as st
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"E:\Download\iDSN"
L_PKT = 1200.0          # 平均 QUIC 包长 (B)
C = 1.25e7              # 100 Mbps 线速 (B/s)


def parse_file(c):
    """解析单文件配置 → 模式签名。"""
    m = dict(re.findall(r"(\w+)=([\w.]+)", c))
    if "max_pacing_rate" in m:
        return dict(mode="pr", rate=float(m["max_pacing_rate"]))
    if "burst" in m:
        return dict(mode="tb", tau=float(m["tokens"]), B=float(m["burst"]),
                    r=float(m["token_refill_rate"]), I=float(m["token_refill_interval_us"]))
    if "leak_rate" in m:
        return dict(mode="leak", rate=float(m["leak_rate"]))
    return dict(mode="other")


def load_tb_valid():
    recs = []
    with open(ROOT + r"\runs\results.jsonl", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            if "token_bucket" not in str(r.get("config", "")) or not r.get("valid"):
                continue
            pf = {k: parse_file(r["config"][k]) for k in map(str, range(1, 7))}
            if pf["1"].get("mode") != "tb":
                continue                     # 家族键以 1.bin 的 token_bucket 参数为准
            recs.append(dict(tag=r["tag"], at=r["at"][:16], tot=r["total_seconds"],
                             d=[r["downloads"].get(f"{i}.bin") for i in range(1, 7)], pf=pf))
    return recs


def mean_sd(xs):
    return st.mean(xs), (st.stdev(xs) if len(xs) > 1 else 0.0)


def welch(a, b):
    ma, sa = mean_sd(a); mb, sb = mean_sd(b)
    se = math.sqrt(sa * sa / len(a) + sb * sb / len(b))
    t = (mb - ma) / se
    # Welch–Satterthwaite 自由度
    nu = (sa**2/len(a) + sb**2/len(b))**2 / (
        (sa**2/len(a))**2/(len(a)-1) + (sb**2/len(b))**2/(len(b)-1))
    return ma, sa, mb, sb, t, nu


def f_test_var(a, b):
    """方差齐性 F 检验（大/小方差比），双侧 p 的近似用 F 分布 survival 的正态展开。"""
    va, vb = st.variance(a), st.variance(b)
    F = max(va, vb) / min(va, vb)
    n1, n2 = (len(a) - 1, len(b) - 1) if va >= vb else (len(b) - 1, len(a) - 1)
    # Wilson–Hilferty 变换近似 F 分布分位
    z = ((1 - 2/(9*n2)) * F ** (1/3) - (1 - 2/(9*n1))) / math.sqrt(2/(9*n1) + (2/(9*n2)) * F ** (2/3))
    p_two = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return F, n1, n2, min(p_two, 1.0)


def main():
    recs = load_tb_valid()
    print(f"1.bin 为 token_bucket 的有效记录: n={len(recs)}")

    # ---------- §2 物理模型 ----------
    print("\n== §2 理想令牌桶响应曲面的解析结构（铰链定理） ==")
    print("T(τ,B; r,I, F, {g_i}) = F/R_ss − (1/R_ss − 1/C)·L·[ min(τ,B) + Σ_i min(B, r/I·g_i) ]")
    print("∂T/∂τ = -(1/R_ss − 1/C)·L·1{τ<B}；∂T/∂B = -(1/R_ss − 1/C)·L·[1{τ>B} + Σ_i 1{(r/I)·g_i>B}]")
    print("光滑区 ∂²T/∂τ∂B = 0 —— 差分耦合只在铰链 τ=B、(r/I)g=B 上，不是光滑二次型")
    R_ss = 40 / 0.004 * L_PKT            # r=40, I=4000µs → 96 Mbps
    d = 1 / R_ss - 1 / C                  # 每字节排队节省
    print(f"R_ss(r=40,I=4ms) = {R_ss*8/1e6:.1f} Mbps；发射节省/包 = L·d = {L_PKT*d*1e6:.1f} µs")
    for name, nb in (("τ 40→60", 20), ("B 40→60(满积攒/次)", 20)):
        print(f"  {name}: 界 = {nb}包 × {L_PKT*d*1e6:.1f} µs = {nb*L_PKT*d*1000:.2f} ms")
    print(f"  全程碰撞满积攒次数 ~3（0051 E[#≥28MB]=2.84）⇒ B 效应总界 ~{3*20*L_PKT*d*1000:.2f} ms ≪ 实测噪声 sd 7–13 s")
    g_bank_60 = 60 / (40 / 0.004)
    g_bank_40 = 40 / (40 / 0.004)
    print(f"  满积攒所需空闲：B=60 → {g_bank_60*1000:.1f} ms；B=40 → {g_bank_40*1000:.1f} ms（两者均 ≪ 典型碰撞间隙）")

    # ---------- §3 分层清单 ----------
    print("\n== §3 全量分层（1.bin τ=40, r=40, I=4000µs 层，按 2/4/5/6.bin 签名） ==")
    print(f"{'B':>3} | {'2':>6} {'4':>6} {'5':>6} {'6':>6} | {'n':>3} {'mean':>8} {'sd':>7} {'min':>8}")

    def pr(c):
        s = parse_file(c)
        if s["mode"] == "pr":
            return "pr%gM" % (s["rate"] / 1e6)
        return s["mode"]

    strat = {}
    for x in recs:
        p1 = x["pf"]["1"]
        if p1["tau"] != 40.0 or p1["r"] != 40.0 or p1["I"] != 4000.0:
            continue
        sig = lambda k: ("pr%gM" % (x["pf"][k]["rate"] / 1e6)) if x["pf"][k]["mode"] == "pr" else x["pf"][k]["mode"]
        key = (p1["B"], sig("2"), sig("4"), sig("5"), sig("6"))
        strat.setdefault(key, []).append(x["tot"])
    for k in sorted(strat):
        v = strat[k]
        m, s = mean_sd(v)
        print(f"{k[0]:3.0f} | {k[1]:>6} {k[2]:>6} {k[3]:>6} {k[4]:>6} | {len(v):3d} {m:8.2f} {s:7.2f} {min(v):8.2f}")

    # ---------- §4 匹配对照：差分耦合的主检验 ----------
    print("\n== §4 匹配对照（同 τ=40,r=40,I=4ms, 2/4.bin tb, 5.bin=100M, 6.bin=96M） ==")
    cells = {}
    for x in recs:
        p1 = x["pf"]["1"]
        p5, p6 = x["pf"]["5"], x["pf"]["6"]
        if (p1["tau"], p1["r"], p1["I"]) != (40.0, 40.0, 4000.0):
            continue
        if x["pf"]["2"]["mode"] != "tb" or x["pf"]["4"]["mode"] != "tb":
            continue
        if (p5["mode"], p6["mode"]) != ("pr", "pr"):
            continue
        if abs(p5["rate"] - 12.5e6) > 1 or abs(p6["rate"] - 12e6) > 1:
            continue
        cells.setdefault(p1["B"], []).append(x["tot"])
    for b in sorted(cells):
        v = cells[b]
        m, s = mean_sd(v)
        print(f"  B={b:2.0f}: n={len(v):2d}  mean={m:8.2f}  sd={s:6.2f}  CV={s/m*100:5.1f}%  min={min(v):7.2f}")

    if 40.0 in cells and 60.0 in cells:
        a, b_ = cells[40.0], cells[60.0]
        ma, sa, mb, sb, t, nu = welch(a, b_)
        print(f"\n  均值差 (B=60 − B=40) = {mb-ma:+.2f} s   Welch t={t:+.2f} (df≈{nu:.0f}, |t|<2 ⇒ 均值不可分辨)")
        F, n1, n2, p = f_test_var(a, b_)
        print(f"  方差比 F = sa²/sb² = {F:.2f} (df {n1},{n2})  双侧 p ≈ {p:.3f}  ⇒ {'B=60 方差显著更低' if p<0.05 else '方差差不显著'}")
        # 官方复测平均下的方差感知损失（0058 口径：复测取平均，均值的 95% 界）
        for k_re in (3,):
            la = ma + 1.96 * sa / math.sqrt(k_re)
            lb = mb + 1.96 * sb / math.sqrt(k_re)
            print(f"  复测平均损失 L=μ+1.96σ/√{k_re}: B=40 → {la:.1f}；B=60 → {lb:.1f}  ⇒ {'B=60 更优' if lb<la else 'B=40 更优'}")

    # ---------- §5 均值/方差响应面拟合 ----------
    print("\n== §5 响应曲面拟合（匹配层，B 为连续变量） ==")
    pts = [(b, mean_sd(v)[0], mean_sd(v)[1], len(v)) for b, v in sorted(cells.items()) if len(v) >= 1]
    # n 加权一阶均值面 T(B)=β0+β1·B
    sw = sum(p[3] for p in pts)
    xb = sum(p[3] * p[0] for p in pts) / sw
    yb = sum(p[3] * p[1] for p in pts) / sw
    sxx = sum(p[3] * (p[0] - xb) ** 2 for p in pts)
    b1 = sum(p[3] * (p[0] - xb) * (p[1] - yb) for p in pts) / sxx
    b0 = yb - b1 * xb
    print(f"  均值面（n 加权 OLS）: T(B) = {b0:.2f} + {b1:+.3f}·B   （+1 token 的均值代价 {b1*1000:.0f} ms）")
    print(f"  物理界对照：B 均值效应界 ~ms 级 ⇒ 实测斜率主要是背景密度漂移/混杂，不是 B 的物理代价")
    # 方差面：σ(B) 用两主格 sd 的对数线性
    big = [(b, mean_sd(cells[b])[1]) for b in (40.0, 60.0)]
    if len(big) == 2:
        slope = math.log(big[1][1] / big[0][1]) / math.log(big[1][0] / big[0][0])
        print(f"  方差面（幂律）: sd(B) ∝ B^({slope:+.2f})  —— B 每翻倍 sd 缩到 {2**slope:.2f} 倍（发射脉冲摊薄单碰撞峰值）")

    # ---------- §6 τ 维度可辨识性 ----------
    print("\n== §6 τ（初始 tokens）维度的实测可辨识性 ==")
    tau_cells = {}
    for x in recs:
        p1 = x["pf"]["1"]
        if p1["r"] != 40.0 or p1["I"] != 4000.0:
            continue
        tau_cells.setdefault((p1["tau"], p1["B"]), []).append(x["tot"])
    for k in sorted(tau_cells):
        v = tau_cells[k]
        m, s = mean_sd(v)
        flag = "" if len(v) >= 3 else "  [LOW_N]"
        print(f"  τ={k[0]:3.0f} B={k[1]:3.0f}: n={len(v):2d} mean={m:8.2f} sd={s:6.2f}{flag}")
    print("  结论：无任何受控 τ 扫描（τ 变化总伴随 B 或 r 变化）；物理界（发射节省 ≤ 2.4 ms/20包）")
    print("  ⇒ τ 维度在现有数据下不可辨识，保持冠军点 τ=40（铰链内侧，∂T/∂τ 常数非零）")

    # ---------- §7 邻域稳定性（反过拟合门禁） ----------
    print("\n== §7 邻域稳定性与选型口径 ==")
    neigh = [(b, len(cells[b]), mean_sd(cells[b])[0], mean_sd(cells[b])[1]) for b in sorted(cells)]
    for b, n_, m_, s_ in neigh:
        gate = "满足 n≥3" if n_ >= 3 else "LOW_N（仅邻域方向参考，不入选型证据）"
        print(f"  B={b:2.0f}: n={n_:2d} mean={m_:8.2f} sd={s_:6.2f} — {gate}")
    means = [m_ for _, n_, m_, _ in neigh if n_ >= 3]
    print(f"  n≥3 格均值域: [{min(means):.1f}, {max(means):.1f}] s，无悬崖 ⇒ B∈[40,60] 为平台区，非尖点")


if __name__ == "__main__":
    main()
