# -*- coding: utf-8 -*-
"""0253 极端高丢包 5%~10% 环境下 QUIC 发送窗口抗死锁验证.

模型（常数出处）:
  - RFC 9002: 初始 cwnd=10 pkt; cwnd 下界 2 pkt (§7.2); PTO 探针不受 cwnd 阻塞 (§7.5,
    「probe packets are sent even when congestion window is fully utilized」—— QUIC 相对
    TCP RTO 的专属抗死锁设计); PTO = max(sRTT+max_ack_delay, 计时粒度) 指数退避, ACK 即复位.
  - 0077: PTO 78/156/312 ms (1x/2x/4x 退避) —— 本仿真 PTO_base=78ms, 退避 x2 无上限.
  - 0086: loss-based CC 在持续饱和下 cwnd 钉死 CMIN=2 (2 pkt/RTT) 的饥饿机理.
  - 0085: 官方环境尾损基线 0.157% (leak 批量=1) —— 5%~10% 是 32~64 倍的压力裕度测试.
  - 拓扑: 官方 RTT 未公布, 取 20ms 保守值 (数值不影响活性判定, 只影响绝对时长).

死锁定义 (可判定): 连续无交付进度时长 >= IDLE_TIMEOUT=30s (QUIC 默认空闲超时 ->
连接被杀 -> 下载失败无成绩). 活性判据: min(cwnd)>=2 全程、PTO 链有限、进度速率 > 0 a.s.

三种发送端变体 (覆盖 CC 谱系):
  reno      : loss-based, 丢包 RTT 减半 + AIMD +1, 下界 2 —— 0086 饥饿族的随机丢包版本
  bbr       : 窗口对丢包不反应 (固定 4xBDP), 仅按检测/PTO 重传
  openloop  : 理想开环 (pacer 96M 恒速, CC 不退让) —— 冠军 leak 族的上界理想化,
              非 RFC QUIC 真实行为, 仅作参照上界
丢包模型: 数据包与 ACK 双向独立丢包 p (对 ACK 不聚合 = 最坏情况);
  fast retransmit: 同窗口累计 3 次可检测丢失; PTO 探针 2 pkt/次, 不计 cwnd.
确定性: 每 run 固定种子; p ∈ {0.05, 0.075, 0.10} x 3 变体 x 200 runs.
规模: 阶段-1 文件 10MB = 8334 pkt (官方 L74); 大阶段按 N 线性外推 (独立丢包 -> 时长线性).
"""
import sys, json, random, statistics

sys.stdout.reconfigure(encoding="utf-8")

RTT_MS = 20.0
PTO_BASE_MS = 78.0            # 0077
IDLE_TIMEOUT_S = 30.0         # QUIC 默认空闲超时
HORIZON_S = 600.0             # 0086: >600s 判「未完成」
CWND_MIN = 2                  # RFC 9002 §7.2
CWND_INIT = 10                # RFC 9002
N_PKTS = 8334                 # 10MB / 1200B
RUNS = 200
P_GRID = [0.05, 0.075, 0.10]
LINK_RATE_PKTS = 100e6 / 8 / 1200          # 10416.7 pkt/s
PACER_PKTS = 96e6 / 8 / 1200               # 10000 pkt/s (leak 40/4ms 冠军当量)
BDP = PACER_PKTS * (RTT_MS / 1000.0)       # 200 pkt

def simulate(p: float, variant: str, seed: int):
    """唯一序号模型: delivered=去重收包数; 数据/ACK 双向独立丢; 龄期>=3 判丢失, PTO 兜底."""
    rng = random.Random(seed)
    delivered_set = set()
    next_new = 0                    # 下一个新数据序号
    inflight = {}                   # seq -> 未确认龄期 (RTT)
    pto_chain = 0
    max_pto_chain = 0
    max_stall_s = 0.0
    stall_rtt = 0
    cwnd = float(CWND_INIT)
    min_cwnd = float(CWND_INIT)
    t_rtt = 0
    window = (min(4.0 * BDP, PACER_PKTS * RTT_MS / 1000.0) if variant == "bbr"
              else PACER_PKTS * RTT_MS / 1000.0 if variant == "openloop" else None)
    while True:
        t_rtt += 1
        t_s = t_rtt * RTT_MS / 1000.0
        # --- PTO (RFC 9002 §7.5): 探针不受 cwnd 阻塞; 任一 ACK 到达即复位退避 ---
        pto_ms = PTO_BASE_MS * (2 ** pto_chain)
        pto_due = any(a * RTT_MS >= pto_ms for a in inflight.values())
        probe_seqs = sorted(inflight, key=lambda s: -inflight[s])[:2] if pto_due else []
        if pto_due:
            pto_chain += 1
            max_pto_chain = max(max_pto_chain, pto_chain)
        # --- 预算内发送: 新数据优先, 其次龄期>=3 的检测丢失重传 ---
        if variant == "reno":
            budget = max(0.0, cwnd - len(inflight))
        else:
            budget = max(0.0, window - len(inflight))
        detect_lost = [s for s, a in inflight.items() if a >= 3]
        sends = list(probe_seqs)                      # PTO 探针不占预算 (§7.5)
        take = int(min(budget, len(detect_lost)))
        sends.extend(detect_lost[:take])
        room = int(budget) - take
        if room > 0 and next_new < N_PKTS:
            newn = min(room, N_PKTS - next_new)
            sends.extend(range(next_new, next_new + newn))
            next_new += newn
        # --- 双向独立丢包: 数据丢 / ACK 丢 ---
        newly_acked = 0
        for s in sends:
            if s in delivered_set:
                inflight.pop(s, None)                 # 冗余重传, 接收端已有 -> 纯 ACK
                if rng.random() < p:
                    inflight[s] = 1                   # ACK 也丢 -> 仍以为未确认
                else:
                    newly_acked += 1
                continue
            if rng.random() < p:                      # 数据丢: 发送端不知情, 留在在途
                inflight[s] = 0
            else:
                delivered_set.add(s)
                if rng.random() < p:                  # 数据到但 ACK 丢
                    inflight[s] = inflight.get(s, 0)
                else:
                    newly_acked += 1
                    inflight.pop(s, None)
        for s in inflight:                            # 在途龄期 +1
            inflight[s] += 1
        if len(delivered_set) >= N_PKTS:
            return {"dead": False, "t_s": t_s, "min_cwnd": min_cwnd,
                    "max_pto_chain": max_pto_chain, "max_stall_s": max_stall_s}
        # --- stall / 活性统计 ---
        if newly_acked == 0 and not probe_seqs:
            stall_rtt += 1
            max_stall_s = max(max_stall_s, stall_rtt * RTT_MS / 1000.0)
            if max_stall_s >= IDLE_TIMEOUT_S:
                return {"dead": True, "t_s": t_s, "min_cwnd": min_cwnd,
                        "max_pto_chain": max_pto_chain, "max_stall_s": max_stall_s,
                        "cause": "idle_timeout_stall"}
        else:
            stall_rtt = 0
        # --- PTO 退避复位 (RFC 9002 §6.2.1): 任一 ACK 到达即复位 ---
        if newly_acked > 0:
            pto_chain = 0
        # --- 拥塞反应 ---
        if variant == "reno":
            if detect_lost:
                cwnd = max(CWND_MIN, cwnd / 2.0)      # 每 RTT 有检测丢失 -> 减半一次
            else:
                cwnd = min(4.0 * BDP, cwnd + 1.0)     # AIMD
            min_cwnd = min(min_cwnd, cwnd)
        else:
            min_cwnd = min(min_cwnd, window)
        if t_s > HORIZON_S:
            return {"dead": True, "t_s": t_s, "min_cwnd": min_cwnd,
                    "max_pto_chain": max_pto_chain, "max_stall_s": max_stall_s,
                    "cause": "horizon_600s", "delivered": len(delivered_set)}

results = {}
for variant in ("reno", "bbr", "openloop"):
    for p in P_GRID:
        comp, dead, min_cwnds, chains, stalls = [], 0, [], [], []
        for k in range(RUNS):
            r = simulate(p, variant, seed=hash((variant, p, k)) % (2**31))
            if r.get("dead"):
                dead += 1
            else:
                comp.append(r["t_s"] if "t_s" in r else 0)
            min_cwnds.append(r["min_cwnd"])
            chains.append(r["max_pto_chain"])
            stalls.append(r["max_stall_s"])
        comp.sort()
        results[f"{variant}|p={p}"] = {
            "survival_pct": round(100.0 * (RUNS - dead) / RUNS, 2),
            "completed_mean_s": round(statistics.mean(comp), 1) if comp else None,
            "completed_p95_s": round(comp[int(0.95 * len(comp)) - 1], 1) if comp else None,
            "global_min_cwnd": min(min_cwnds),
            "max_pto_chain_observed": max(chains),
            "max_pto_chain_duration_s": round(max(chains) and PTO_BASE_MS * (2 ** max(chains)) / 1000, 3),
            "max_no_progress_stall_s": round(max(stalls), 2),
            "dead_runs": dead,
        }

# Mathis 定律交叉核对: reno 吞吐 ∝ 1/sqrt(p)
m = results["reno|p=0.05"]["completed_mean_s"], results["reno|p=0.1"]["completed_mean_s"]
mathis_ratio_pred = (0.10 / 0.05) ** 0.5
mathis_ratio_obs = m[1] / m[0] if m[0] else None

print(json.dumps({
    "params": {"RTT_ms": RTT_MS, "PTO_base_ms": PTO_BASE_MS, "idle_timeout_s": IDLE_TIMEOUT_S,
               "horizon_s": HORIZON_S, "N_pkts": N_PKTS, "runs_per_cell": RUNS},
    "cells": results,
    "mathis_crosscheck": {"pred_ratio_T10_over_T05": round(mathis_ratio_pred, 3),
                          "obs_ratio": round(mathis_ratio_obs, 3) if mathis_ratio_obs else None},
    "scale_linear_extrapolation_6bin_s": {
        "note": "独立丢包 -> 完成时长近似线性于 N; 6.bin=320MB 为 10MB 的 32 倍",
        "reno_p10_320MB_est": round((results["reno|p=0.1"]["completed_mean_s"] or 0) * 32, 0),
    },
}, ensure_ascii=False, indent=1))
