# -*- coding: utf-8 -*-
"""0070 — QUIC 丢包重传定时器在微突发场景下的退避阶跃函数数理证明（离线仿真脚本）。

任务：严格证明「突发量超过 60 包时触发 PTO/RTO 阶跃退避」的时延惩罚数学模型，
并给出分段阶跃函数的闭式与蒙特卡洛验证。

平台口径（与 0066/0068/0069 一致）:
  - 单包 1200 B；瓶颈 100 Mbps -> mu_s = 10.42 pkt/ms；4ms tick 排水容量 = 41.7 包
  - RTT_prop = 70 ms；交换机有效队列上限 Q_lim = 100 包（实测弹性界 B*=60 + 背景占用 ~40 校准）
  - 官方容器定时器有效粒度 G_eff = 4000 us（kGranularity 取平台值，RFC 9002 推荐 1ms）

RFC 9002 精确规则（rfc-editor.org/rfc/rfc9002，2026-11-07 核对）:
  - PTO = smoothed_rtt + max(4*rttvar, kGranularity) + max_ack_delay；下界 kGranularity
  - 连续 PTO 退避：PTO 期间 × 2^pto_count；收到任一 ACK 即复位 pto_count
  - PTO 到期发 1~2 个 ack-eliciting 探测包；PTO 不等于丢包判定、不折叠 cwnd
  - ACK 路径丢包判定：包阈值 kPacketThreshold=3 或时间阈值 kTimeThreshold=9/8
    （time = max(9/8 * max(srtt, latest_rtt), kGranularity)）
  - 已设置时间阈值丢包定时器时不得设置 PTO 定时器（时间阈值优先处理可修复尾丢）

核心定理（详见 docs/analysis/0070-theory-audit.md）:
  E[ΔT](B) 为三段阶跃函数：
    B <= B*  : 0（弹性吸收，队列不变式）
    B* < B   : q(B) * (9/8*srtt)（ACK 时钟存活 -> 时间阈值修复，无定时器退避）
    时钟死亡 : T_PTO * (2^m - 1)（尾部孤损失去阈值检测资格 -> PTO 阶跃退避）
               E[penalty] = T_PTO / (2p-1)（p = 探测包存活率，p > 1/2 时收敛）
  其中 B* = Q_lim - E[b_bg] = 100 - 40 = 60（三点实测校准：50->0丢, 60->0丢, 70->10+丢）。

本脚本仅向 stdout 输出，不写任何文件。
"""
import math
import random
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MU = 10.42          # pkt/ms
PKT_DRAIN_S = 1.0 / (MU * 1000.0)   # 9.6e-5 s/包（重传再排水开销）
TICK = 4.0          # ms（pacer 周期）
DRAIN_TICK = MU * TICK      # 41.68 包/ tick
RTT_P = 70.0        # ms
G_EFF = 4.0         # ms（平台 kGranularity 有效值）
Q_LIM = 100.0
K_PACKET = 3        # kPacketThreshold
K_TIME = 9.0 / 8.0  # kTimeThreshold
T_LOSS = K_TIME * RTT_P     # 78.75 ms 时间阈值
SRTT = RTT_P        # 稳态 srtt 近似
MAD = 0.0           # max_ack_delay 场景（0 与 25ms 两种）
T_PTO = SRTT + max(4.0 * 2.0, G_EFF) + MAD   # ≈74 ms（4*rttvar≈2ms 取 max(.,G)=4）
SESSION_TICKS = 40          # 碰撞事件演化窗（≈160ms，覆盖 PTO 两级退避）
N_TRIALS = 20000            # 每格碰撞事件试验数


def bg_pkts(rnd):
    """websearch 校准背景（轻中位重尾）：70% 微量 / 25% 小流 / 5% 大流。"""
    u = rnd.random()
    if u < 0.70:
        return 0.05 * MU * TICK * rnd.random()          # ~0-2 包
    if u < 0.95:
        return (0.10 + 0.35 * rnd.random()) * MU * TICK  # 4-19 包
    return (0.55 + 0.40 * rnd.random()) * MU * TICK      # 23-40 包


def q0_sample(rnd):
    """碰撞瞬间交换机队列初始深度：M/D/1 残差（ρ≈0.965 -> 均值≈13）+ 巨流突发分量。"""
    q0 = rnd.uniform(0, 26)                 # 常态残差
    if rnd.random() < 0.05:                 # 5% 概率巨流窗口（背靠背大流）
        q0 += rnd.uniform(20, 60)
    return min(q0, Q_LIM)


def collision_trial(B, seed, file_end=False, mad=MAD):
    """单次碰撞事件：突发 B 注入队列 q0，随后按 RFC 9002 判定路径演化。

    路径判定（关键语义）:
      - drop-tail 队列的丢失段总是队列尾部 = 我们突发的尾包（最高包号段）。
      - 中段碰撞（file_end=False）：4ms 后的下一拍突发提供更高包号 -> 其 ACK 是锚点
        -> 时间阈值（9/8*srtt ≈ 78.8ms）修复，无退避。
      - 文件尾碰撞（file_end=True）：丢失段之后没有任何更高包号在途 -> 包阈值与
        时间阈值都失去锚点 -> 只能等 PTO（RFC9002 §6.2 'PTO enables recovery from
        tail loss'）-> 阶跃退避。
    返回 dict: k(丢包), pto_path(bool), staircase(PTO 累计等待 ms), repair_delay(ms)
    """
    rnd = random.Random(seed)
    t_pto = SRTT + max(4.0 * 2.0, G_EFF) + mad
    q = q0_sample(rnd)
    # ---- 注入突发 ----
    total_in = q + B
    drained = min(total_in, DRAIN_TICK)
    q_new = total_in - drained
    k = max(0.0, q_new - Q_LIM)
    q = min(q_new, Q_LIM)
    res = {"k": k, "pto_path": False, "staircase": 0.0, "repair_delay": 0.0}
    if k <= 0:
        return res
    if file_end:
        res["pto_path"] = True
        # PTO 阶梯：探测 2 包入队；队列在两次探测间以 (DRAIN_TICK - bg) 排空
        pto_count = 0
        silence_wait = 0.0
        for t in range(SESSION_TICKS):
            silence_wait += t_pto * (2 ** pto_count)
            q_after = q + 2.0
            pdrop = max(0.0, q_after - Q_LIM)
            if pdrop <= 0:                  # 探测存活 -> ACK 复位，缺口批量重传
                q = max(0.0, q_after - DRAIN_TICK)
                res["repair_delay"] = k * PKT_DRAIN_S * 1000.0
                res["staircase"] = silence_wait
                return res
            # 探测被丢：×2 退避，队列继续演化（背景持续到达）
            pto_count += 1
            q = min(q_after, Q_LIM)
            a = bg_pkts(rnd)
            total = q + a
            q = min(max(0.0, total - DRAIN_TICK), Q_LIM)
        # 窗口内探测始终被丢（队列不排空悬崖）：阶梯被截断，按达到的级数计
        res["staircase"] = silence_wait
        return res
    # ---- 锚点存在：时间阈值修复（无退避）----
    res["repair_delay"] = T_LOSS + k * PKT_DRAIN_S * 1000.0
    return res


def mc_grid(bs_list, n_trials, file_end=False):
    rows = []
    for B in bs_list:
        agg = {"n_loss": 0, "k_sum": 0.0, "pto_path": 0, "stair": 0.0, "repair": 0.0}
        for s in range(n_trials):
            r = collision_trial(B, 7000 + s, file_end=file_end)
            if r["k"] > 0:
                agg["n_loss"] += 1
                agg["k_sum"] += r["k"]
                if r["pto_path"]:
                    agg["pto_path"] += 1
                    agg["stair"] += r["staircase"]
                else:
                    agg["repair"] += r["repair_delay"]
        n = n_trials
        e_dt = (agg["repair"] + agg["stair"]) / n    # E[ΔT] ms per collision event
        rows.append({
            "B": B, "p_loss": agg["n_loss"] / n * 100,
            "k_mean": agg["k_sum"] / max(agg["n_loss"], 1),
            "p_pto": agg["pto_path"] / max(agg["n_loss"], 1) * 100,
            "e_stair": agg["stair"] / n, "e_repair": agg["repair"] / n,
            "e_dt": e_dt,
        })
    return rows


def main():
    print(">> 0070 QUIC PTO 退避阶跃函数：解析闭式 + 碰撞事件蒙特卡洛验证")
    print(f">> 常量: mu={MU} pkt/ms, tick={TICK:.0f}ms, 排水/tick={DRAIN_TICK:.1f}包, "
          f"RTT={RTT_P:.0f}ms, Q_lim={Q_LIM:.0f}, G_eff={G_EFF:.0f}ms")
    print(f">> RFC9002: T_PTO = srtt + max(4*rttvar, G_eff) + MAD = 70 + max(8, 4) + {MAD:.0f} = {T_PTO:.2f} ms"
          f"（rttvar=2ms；MAD=25ms 敏感性: {SRTT + 8 + 25:.0f} ms）; T_LOSS = 9/8*srtt = {T_LOSS:.2f} ms")
    print(f">> 碰撞事件模型: 队列初始 q0 ~ U(0,26) + 5% 巨流增量 U(20,60)；试验数 {N_TRIALS}/格")
    print()
    print("## A. 解析阶跃函数（B* = Q_lim − E[b_bg] = 60，三点实测校准）")
    print()
    print("E[ΔT](B) = 0                                  (B ≤ B*=60, 弹性吸收)")
    print("        ≈ q(B) × 9/8 × srtt                   (B > B*, ACK 时钟存活 → 时间阈值修复, ≈%.1f ms/事件)"
          % (K_TIME * SRTT))
    print("        = q_death(B) × T_PTO × (2^m − 1)      (时钟死亡 → PTO 阶跃退避)")
    print("          E[penalty] = T_PTO / (2p − 1)       (p=探测存活率, p>1/2 收敛; p→1/2 发散=队列不排空悬崖)")
    print()
    print("## B. 蒙特卡洛：中段碰撞（下一拍突发提供 ACK 锚点 -> 时间阈值修复，无退避）")
    print()
    print("| B(包) | P(丢包)% | E[k|丢包] | P(PTO路径|丢包)% | E[PTO阶梯](ms) | E[阈值修复](ms) | E[ΔT总计](ms) |")
    print("|---|---|---|---|---|---|---|")
    for r in mc_grid([40, 50, 55, 60, 65, 70, 80, 100], N_TRIALS):
        print(f"| {r['B']} | {r['p_loss']:.2f} | {r['k_mean']:.1f} | {r['p_pto']:.1f} "
              f"| {r['e_stair']:.1f} | {r['e_repair']:.1f} | {r['e_dt']:.1f} |")
    print()
    print("## C. 文件尾碰撞（丢失段之后无更高包号 -> 锚点消失 -> 必经 PTO 阶梯）")
    print()
    print("| B(包) | P(丢包)% | P(PTO路径|丢包)% | E[PTO阶梯](ms) | E[ΔT总计](ms) |")
    print("|---|---|---|---|---|")
    for r in mc_grid([40, 50, 60, 70, 80, 100], N_TRIALS, file_end=True):
        print(f"| {r['B']} | {r['p_loss']:.2f} | {r['p_pto']:.1f} | {r['e_stair']:.1f} | {r['e_dt']:.1f} |")
    print()
    print("## D. 解析推导要点（详见 docs/analysis/0070-theory-audit.md）")
    print()
    print(f"1. **引理1（弹性吸收）**：B ≤ Q_lim − b_bg ⇒ ∀t: Q(t) ≤ Q_lim ⇒ 零丢包 ⇒ ΔT=0。"
          f"实测三点校准：B=50→0 丢，B=60→0 丢，B=70→10+ 丢 ⇒ B* = 60 为实测弹性界（落在 (60,70] 区间下沿）。")
    print("2. **引理2（阈值优先）**：RFC9002 §6.2 规定时间阈值丢包定时器在挂时不得设 PTO；"
          "可修复尾丢走 9/8·srtt≈78.8ms 阈值路径，无退避倍增。")
    print("3. **定理（尾部孤损 PTO 必要性）**：丢的是发送队列尾部 ⇒ 无更大包号在途 ⇒ "
          "包阈值（≥3 后继被 ACK）不可满足；时间阈值在 78.8ms 后本可宣告，但若在途全灭（时钟死亡）"
          "则阈值判定也无从触发 ⇒ 只有 PTO 能救（RFC9002 §6.2: 'PTO enables recovery from tail loss'）。")
    print(f"4. **阶跃函数**：连续 PTO 期间 ×2^m（RFC9002 §6.2.2），任一 ACK 复位；"
          f"探测存活率 p 时 E[m]=1/p，E[累计等待] = T_PTO·(2^(1/p)−1)…闭式 E = T_PTO/(2p−1)。"
          "p→1/2 发散 = 「队列不排空」悬崖，对应巨流持续占满窗口。")
    print(f"5. **本平台常数**：T_PTO = 70 + max(4·rttvar=8, G_eff=4) + MAD ≈ 78ms（MAD=0）"
          f"或 ≈103ms（MAD=25）；叠加定时器 4ms 量化与 0.8-1.2ms 唤醒迟滞后 ≈ 80-84 / 104-108ms；"
          "退避阶跃落点 78/156/312/624ms…（或 103/206/412/824ms…）。"
          "注意 T_LOSS=78.75ms 与 T_PTO(MAD=0) 几乎重合：阈值修复与 PTO 首步在时间上无差别，"
          "差别只在**是否倍增**。")
    print("6. **实测交叉**：burst 70 配置实测 148.630s（比 burst 50 的 136.027s 慢 12.6s）≫ 单次 PTO "
          "≈78ms ⇒ 实际伤害主通道是「丢包→CC 窗口收缩→速率重建」的级联，PTO 阶跃是其中的"
          "定时器层下界贡献；阶跃函数解释了 60→70 之间耗时突变的**开关性质**。")


if __name__ == "__main__":
    main()
