# -*- coding: utf-8 -*-
"""
buffer0298_shallow_nash_squeeze.py — 任务 0298 验证脚本 (v2, 时步化引擎)
浅缓冲区（30 包 drop-tail）纳什均衡与多租户挤出效应微观建模

引擎: 时步化仿真，dt = 1/C（单包服务槽）。每槽: 各流按轮转顺序产生到达
（确定性留数累积），入队（容量 K=30，溢出即丢），然后服务 1 包。
无事件堆、无调度 tie-breaking 偏置；同构流以相位错开保证对称性可审计。

物理口径（单位锚点）:
  C = 100 Mbps / 1200 B = 10416.67 pkt/s（p100M 临界档）; K = 30 包; T = 60 s
流形态:
  steady : 确定性匀速（匀速漏桶发射形态）
  pulsed : 每 period 发 k 包连续脉冲（激进脉冲流）
  aimd   : 拥塞窗口 c，每 RTT 发 min(c,...) 连续包，窗口内丢包→c←c/2，否则 c←c+1

场景:
  R1 共存基线    S=6800 (65.3%C) vs 脉冲 B=3617 (k=25)      总 offered=100%C
  R2 激进对手    S=6800 vs 脉冲 B=5400 (k=60)               总 offered=117%C
  R3 AIMD 竞争   S=6800 vs AIMD                             剩余留给 AIMD
  R4 多租户      S=6800 + 官方背景1500 + 2×AIMD             过载压力测试
  R5/R5b Nash    双方 offered 均 4500, 策略{匀速,脉冲}, k=100 / k=40 扰动

输出: zcode/scripts/out/0298_shallow_buffer_results.json
"""
import json
import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(ROOT, "zcode", "scripts", "out")
os.makedirs(OUT_DIR, exist_ok=True)

C = 100e6 / (1200 * 8)      # 10416.67 pkt/s
K = 30
T_SIM = 60.0
DT = 1.0 / C
N_SLOTS = int(T_SIM * C)    # 625,000 槽


def make_flow(name, kind, **kw):
    return {"name": name, "kind": kind, **kw}


def simulate(flows, T=T_SIM):
    n_slots = int(T * C)
    names = [f["name"] for f in flows]
    nf = len(flows)
    offered = [0] * nf
    accepted = [0] * nf
    dropped = [0] * nf

    # 每流状态
    st = []
    for f in flows:
        if f["kind"] == "steady":
            st.append({"residue": 0.0, "rate_per_slot": f["rate"] * DT})
        elif f["kind"] == "pulsed":
            period_slots = max(1, round(f["period"] * C))
            st.append({"phase": f.get("phase", 0) * C, "k": f["k"],
                       "period_slots": period_slots, "in_burst": 0, "next_burst": int(f.get("phase", 0) * C) + period_slots})
        elif f["kind"] == "aimd":
            st.append({"cwnd": float(f.get("cwnd0", 10.0)), "in_burst": 0,
                       "win_drops": 0, "next_win": int(f.get("start", 0.5) * C),
                       "rtt_slots": max(1, round(f.get("rtt_base", 0.010) * C)),
                       "min_gap": int(f.get("start", 0.5) * C)})

    queue_head = 0
    queue = [0] * (K + 1)   # 环形缓冲存流索引
    qsize = 0

    for slot in range(n_slots):
        # 1) 到达（轮转起始流, 消除固定顺序偏置）
        order = [(slot + j) % nf for j in range(nf)]
        for i in order:
            f = flows[i]; s = st[i]
            if f["kind"] == "steady":
                s["residue"] += s["rate_per_slot"]
                while s["residue"] >= 1.0:
                    s["residue"] -= 1.0
                    offered[i] += 1
                    if qsize < K:
                        queue[(queue_head + qsize) % (K + 1)] = i; qsize += 1
                        accepted[i] += 1
                    else:
                        dropped[i] += 1
            elif f["kind"] == "pulsed":
                if slot >= s["next_burst"]:
                    s["in_burst"] = s["k"]
                    s["next_burst"] += s["period_slots"]
                if s["in_burst"] > 0:
                    s["in_burst"] -= 1
                    offered[i] += 1
                    if qsize < K:
                        queue[(queue_head + qsize) % (K + 1)] = i; qsize += 1
                        accepted[i] += 1
                    else:
                        dropped[i] += 1
            else:  # aimd
                if slot >= s["next_win"] and slot >= s["min_gap"]:
                    # 结算上一窗口
                    if offered[i] > 0:
                        s["cwnd"] = max(1.0, s["cwnd"] / 2.0) if s["win_drops"] > 0 else s["cwnd"] + 1.0
                    s["win_drops"] = 0
                    s["in_burst"] = int(round(s["cwnd"]))
                    s["next_win"] = slot + max(s["rtt_slots"], int(round(s["cwnd"])))
                if s["in_burst"] > 0:
                    s["in_burst"] -= 1
                    offered[i] += 1
                    if qsize < K:
                        queue[(queue_head + qsize) % (K + 1)] = i; qsize += 1
                        accepted[i] += 1
                    else:
                        dropped[i] += 1
                        s["win_drops"] += 1
        # 2) 服务 1 包
        if qsize > 0:
            queue_head = (queue_head + 1) % (K + 1)
            qsize -= 1

    total_acc = sum(accepted)
    total_off = sum(offered)
    out = {}
    for i, f in enumerate(flows):
        off_share = offered[i] / total_off if total_off else 0
        recv_share = accepted[i] / total_acc if total_acc else 0
        out[f["name"]] = {
            "kind": f["kind"],
            "offered_rate": round(offered[i] / T, 1),
            "accepted_rate": round(accepted[i] / T, 1),
            "loss_rate": round(dropped[i] / offered[i], 6) if offered[i] else 0.0,
            "share_offered": round(off_share, 4),
            "share_received": round(recv_share, 4),
            "amplification": round(recv_share / off_share, 4) if off_share else None,
        }
    return out


# ---------------------------------------------------------------- 场景
scenarios = {}

r1 = simulate([
    make_flow("S_steady(ours)", "steady", rate=6800),
    make_flow("B_pulsed", "pulsed", k=25, period=25 / 3617),
])
scenarios["R1_coexistence"] = {"util_of_C": "S=65.3%C + B=34.7%C = 100%", "flows": r1}

r2 = simulate([
    make_flow("S_steady(ours)", "steady", rate=6800),
    make_flow("B_pulsed", "pulsed", k=60, period=60 / 5400),
])
scenarios["R2_aggressive_pulse"] = {"util_of_C": "S=65.3%C + B=51.8%C = 117% (过载)", "flows": r2}

r3 = simulate([
    make_flow("S_steady(ours)", "steady", rate=6800),
    make_flow("B_aimd", "aimd", cwnd0=10.0, rtt_base=0.010, start=0.5),
])
scenarios["R3_aimd_competitor"] = {"util_of_C": "S=65.3%C + AIMD 自适应取剩余", "flows": r3}

r4 = simulate([
    make_flow("S_steady(ours)", "steady", rate=6800),
    make_flow("BG_official", "steady", rate=1500),
    make_flow("T1_aimd", "aimd", cwnd0=10.0, rtt_base=0.010, start=0.7),
    make_flow("T2_aimd", "aimd", cwnd0=10.0, rtt_base=0.013, start=1.3),
])
scenarios["R4_multitenant_overload"] = {"util_of_C": "S=65.3%C + BG=14.4%C + 2×AIMD(无界) = 过载", "flows": r4}

# R5 Nash 2×2: 双方 offered 均 4500, 脉冲相位错开 period/2
def r5_cell(s_st, b_st, k):
    def mk(name, strategy):
        if strategy == "steady":
            return make_flow(name, "steady", rate=4500)
        return make_flow(name, "pulsed", k=k, period=k / 4500,
                         phase=(0.0 if name == "P1" else k / 4500 / 2))
    return simulate([mk("P1", s_st), mk("P2", b_st)])

nash_cells = {}
for tag, k in (("R5_nash_2x2_k100", 100), ("R5b_nash_k40_perturbation", 40)):
    M = {}
    for s_st in ("steady", "pulsed"):
        for b_st in ("steady", "pulsed"):
            cell = r5_cell(s_st, b_st, k)
            M[f"{s_st}|{b_st}"] = {p: {"goodput": cell[p]["accepted_rate"],
                                       "loss": cell[p]["loss_rate"]} for p in ("P1", "P2")}
    vs_steady = "steady" if M["steady|steady"]["P1"]["goodput"] >= M["pulsed|steady"]["P1"]["goodput"] else "pulsed"
    vs_pulsed = "steady" if M["steady|pulsed"]["P1"]["goodput"] >= M["pulsed|pulsed"]["P1"]["goodput"] else "pulsed"
    best_vs = {"steady": vs_steady, "pulsed": vs_pulsed}
    ne = [f"{a}|{b}" for a in ("steady", "pulsed") for b in ("steady", "pulsed")
          if best_vs[b] == a and best_vs[a] == b]
    nash_cells[tag] = {"offered_each": 4500, "k_burst": k, "matrix": M,
                       "best_response_vs_steady": vs_steady,
                       "best_response_vs_pulsed": vs_pulsed,
                       "nash_equilibria": ne}
scenarios.update(nash_cells)

# ---------------------------------------------------------------- 汇总
ours_key = "S_steady(ours)"
gate_rows = {}
for name in ("R1_coexistence", "R2_aggressive_pulse", "R3_aimd_competitor", "R4_multitenant_overload"):
    fl = scenarios[name]["flows"]
    gate_rows[name] = {"S_share_received": fl[ours_key]["share_received"],
                       "S_loss_rate": fl[ours_key]["loss_rate"],
                       "S_amplification": fl[ours_key]["amplification"]}

results = {
    "task": "0298 浅缓冲区纳什均衡与多租户挤出效应微观建模",
    "executed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "engine": "时步化 dt=1/C, 逐槽轮转到达顺序, 环形 FIFO K=30 drop-tail",
    "physics": {"C_pkt_s": round(C, 2), "K_packets": K, "pkt_bytes": 1200,
                "T_sim_s": T_SIM, "n_slots": N_SLOTS},
    "scenarios": scenarios,
    "gate_summary": gate_rows,
    "claims": {
        "active_loss": "主动丢包恒为 0（客户端匀速 pacer 按构造不丢弃任何自发包）；"
                       "被动队列丢失按场景实测，见 gate_summary",
    },
}

out_path = os.path.join(OUT_DIR, "0298_shallow_buffer_results.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------- console
print("=" * 76)
print("0298 浅缓冲区纳什均衡与多租户挤出效应微观建模 — 结果摘要 (时步化引擎)")
print(f"C={C:.1f} pkt/s (100Mbps@1200B)  K={K}包  T={T_SIM:.0f}s  槽数={N_SLOTS}")
print("=" * 76)
for name in ("R1_coexistence", "R2_aggressive_pulse", "R3_aimd_competitor", "R4_multitenant_overload"):
    print(f"\n[{name}] {scenarios[name]['util_of_C']}")
    for fn, v in scenarios[name]["flows"].items():
        print(f"  {fn:<16s} off={v['offered_rate']:>7.1f} acc={v['accepted_rate']:>7.1f} "
              f"loss={v['loss_rate']*100:>9.4f}% share_recv={v['share_received']:.4f} amp={v['amplification']}")
for tag in ("R5_nash_2x2_k100", "R5b_nash_k40_perturbation"):
    nc = scenarios[tag]
    print(f"\n[{tag}] 双方 offered={nc['offered_each']}, 脉冲 k={nc['k_burst']}（相位错开半周期）")
    for cell, v in nc["matrix"].items():
        print(f"  {cell:<16s} P1={v['P1']['goodput']:>7.1f} ({v['P1']['loss']*100:>8.4f}%)  "
              f"P2={v['P2']['goodput']:>7.1f} ({v['P2']['loss']*100:>8.4f}%)")
    print(f"  最优响应: vs匀速->{nc['best_response_vs_steady']}  vs脉冲->{nc['best_response_vs_pulsed']}"
          f"  纯策略NE: {nc['nash_equilibria']}")
print(f"\n门禁摘要 (S=我方定步长流):")
for name, g in gate_rows.items():
    print(f"  {name:<26s} share={g['S_share_received']:.4f}  loss={g['S_loss_rate']*100:>9.4f}%  amp={g['S_amplification']}")
print(f"\n结果JSON: {os.path.relpath(out_path, ROOT)}")
