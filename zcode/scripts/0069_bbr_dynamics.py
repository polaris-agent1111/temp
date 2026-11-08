# -*- coding: utf-8 -*-
"""0069 — BBRv1 拥塞控制在 Mininet 容器下的 BtlBw 与 RTprop 滤波动力学建模（离线仿真脚本 v3）。

平台口径（与仓库既有审计一致）:
  - 瓶颈 C = 100 Mbps -> mu = 10.42 pkt/ms（单包 1200 B）；业务路径 RTT_prop = 70 ms；BDP = 729 包
  - 交换机有效队列上限 Q_lim = 100 包（实测弹性界 B*=60 + 背景占用 ~40 校准，见 0066/0070）
  - 官方容器定时器量化 G = 4000 us
  - 整形模块 = 服务端 egress 的 pacing 硬钳位 R（max_pacing_rate / leak_rate 等），
    位于 QUIC 拥塞控制之下：BBR 的发送请求被钳到 min(BBR_pacing, R)

BBRv1 状态机（Cardwell et al. SIGCOMM'16 / draft-cardwell-iccrg-bbr）:
  - 递增速率样本 delivery_rate（按轮）；BtlBw = 最近 10 轮最大值滤波
  - RTprop = 10 s 窗口最小值滤波（app-limited 样本不计）
  - STARTUP: pacing gain 2/ln2≈2.885, cwnd gain 2/ln2；连续 3 轮增速<25% -> DRAIN
  - DRAIN: pacing gain ln2/2≈0.347；inflight<=BDP_est -> PROBE_BW
  - PROBE_BW: pacing gain 8 轮循环 [1.25,1,1,1,1,1,1,0.75]，cwnd gain 2
  - RTprop 10 s 未刷新 -> ProbeRTT: cwnd<=4 约 200 ms

轮级流体仿真（fidelity 声明见输出末尾）。仅 stdout 输出，不写任何文件。
"""
import math
import random
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MU = 10.42            # pkt/ms @100 Mbps, 1200 B
RTT_P = 70.0          # ms
BDP = MU * RTT_P      # 729.4 pkt
Q_LIM = 100.0         # 有效队列上限（校准）
G_TIMER = 4.0         # ms 定时器量化
GAIN_STARTUP = 2.0 / math.log(2.0)
GAIN_DRAIN = math.log(2.0) / 2.0
PROBE_CYCLE = [1.25, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.75]
WINDOW_BW = 10
WINDOW_RT = 10.0e3    # ms
PROBE_RTT_MS = 200.0
PROBE_RTT_CWND = 4
CWND_GAIN_PROBE = 2.0


class BbrSim:
    def __init__(self, r_module=None, seed=7, file_pkt=None):
        """r_module: 模块钳位速率 pkt/ms，None = 不钳位（origin 默认）。file_pkt: 文件总包数。"""
        self.rng = random.Random(seed)
        self.R = r_module
        self.file_pkt = file_pkt
        self.reset()

    def reset(self):
        self.q = 0.0
        self.f_ours = 1.0             # 队列中我方包占比
        self.phase = "STARTUP"
        self.phase_probe_rtt = False
        self.pacing_gain = GAIN_STARTUP
        self.bw_samples = []
        self.btlbw = 0.0
        self.rt_samples = []
        self.rtprop = None
        self.last_rtprop_t = 0.0
        self.cwnd = 32.0
        self.round_idx = 0
        self.t = 0.0
        self.cycle_pos = 0
        self.stall = 0
        self.prev_peak = 0.0
        self.drops = 0.0
        self.sent_total = 0.0
        self.delivered_total = 0.0
        self.probe_rtt_rounds = 0
        self.probe_rtt_start = 0.0
        self.n_probe_rtt = 0
        self.file_left = self.file_pkt
        self.history = []

    def push_bw(self, s):
        self.bw_samples.append(s)
        if len(self.bw_samples) > WINDOW_BW:
            self.bw_samples.pop(0)
        self.btlbw = max(self.bw_samples)

    def push_rt(self, rtt, now, app_limited):
        if app_limited:
            return
        self.rt_samples.append((now, rtt))
        self.rt_samples = [(ts, v) for (ts, v) in self.rt_samples if now - ts <= WINDOW_RT]
        m = min(v for _, v in self.rt_samples)
        # 等值样本同样刷新时间戳（Linux tcp_bbr 对 min_rtt 采用 <= 判据），
        # 否则 ProbeRTT 排空后 rtt==rtprop 无法续签 10s 窗口
        if self.rtprop is None or m <= self.rtprop:
            self.rtprop = m
            self.last_rtprop_t = now

    def step_round(self, bg_pkts):
        r = self
        r.round_idx += 1
        app_limited = False
        if r.phase_probe_rtt:
            sent = min(PROBE_RTT_CWND, r.file_left if r.file_left is not None else 1e9)
            r.probe_rtt_rounds += 1
            # ProbeRTT 期间数据仍可用（受状态机钳制而非应用钳制），
            # 其 RTT 样本正是 ProbeRTT 用来刷新 RTprop 的合法样本
            app_limited = False
            r.cwnd = PROBE_RTT_CWND
        else:
            req_rate = r.pacing_gain * r.btlbw if r.btlbw > 0 else r.cwnd / RTT_P
            rate = req_rate if r.R is None else min(req_rate, r.R)
            sent = min(rate * RTT_P, r.cwnd)
            if r.file_left is not None:
                sent = min(sent, r.file_left)
                r.file_left -= sent
            app_limited = r.file_left is not None and r.file_left <= 0
        r.sent_total += sent
        # FIFO 队列（一致核算：按我方占比分摊排水/丢包/余量）
        total_in = r.q + sent + bg_pkts
        f_new = (r.q * r.f_ours + sent) / max(total_in, 1e-9)
        drained = min(total_in, MU * RTT_P)
        q_new = total_in - drained
        drop = max(0.0, q_new - Q_LIM)
        q_new = min(q_new, Q_LIM)
        q_new = max(q_new, 0.0)
        drained_ours = drained * f_new
        q_new_ours = q_new * f_new
        ours_drop = max(0.0, (r.q * r.f_ours + sent) - drained_ours - q_new_ours)
        delivered = drained_ours
        r.delivered_total += delivered
        r.drops += ours_drop
        r.q = q_new
        r.f_ours = q_new_ours / q_new if q_new > 0 else 1.0
        # RTT 样本
        q_prev = r.history[-1]["q"] if r.history else 0.0
        rtt = RTT_P + (q_prev + q_new) / 2.0 / MU
        r.push_rt(rtt, r.t, app_limited)
        # 递增速率样本（G 量化：测得轮时 ∈ [T-G, T]）
        t_meas = max(rtt - G_TIMER * r.rng.random(), 1.0)
        r.push_bw(delivered / t_meas)
        # 状态机
        bdp_est = r.btlbw * r.rtprop if r.rtprop else r.cwnd
        if r.phase_probe_rtt:
            if (r.t - r.probe_rtt_start) >= PROBE_RTT_MS:
                r.phase_probe_rtt = False
                r.phase = "PROBE_BW"
                r.cycle_pos = 0
                r.pacing_gain = PROBE_CYCLE[0]
        elif r.phase == "STARTUP":
            r.cwnd = max(r.cwnd, GAIN_STARTUP * bdp_est)
            if r.round_idx >= 4 and r.prev_peak > 0:
                growth = (r.btlbw - r.prev_peak) / r.prev_peak
                r.stall = r.stall + 1 if growth < 0.25 else 0
                if r.stall >= 3:
                    r.phase = "DRAIN"
            r.prev_peak = r.btlbw
        elif r.phase == "DRAIN":
            r.pacing_gain = GAIN_DRAIN
            inflight = r.q * r.f_ours + sent      # 我方在途近似
            r.drain_rounds = getattr(r, "drain_rounds", 0) + 1
            if inflight <= bdp_est + 5 or r.drain_rounds >= 3:
                r.drain_rounds = 0
                r.phase = "PROBE_BW"
                r.cycle_pos = 0
                r.pacing_gain = PROBE_CYCLE[0]
        elif r.phase == "PROBE_BW":
            r.pacing_gain = PROBE_CYCLE[r.cycle_pos]
            r.cycle_pos = (r.cycle_pos + 1) % len(PROBE_CYCLE)
            r.cwnd = max(r.cwnd, CWND_GAIN_PROBE * bdp_est)
            if r.rtprop is not None and r.t - r.last_rtprop_t > WINDOW_RT:
                r.phase_probe_rtt = True
                r.probe_rtt_start = r.t
                r.n_probe_rtt += 1
        r.t += rtt
        r.history.append({
            "round": r.round_idx, "phase": "PROBE_RTT" if r.phase_probe_rtt else r.phase,
            "gain": r.pacing_gain, "sent": sent, "bg": bg_pkts, "q": q_new,
            "drop": ours_drop, "rtt": rtt, "btlbw": r.btlbw,
            "rtprop": r.rtprop if r.rtprop else 0.0, "t": r.t,
        })


def bg_profile(kind, rnd, n):
    """背景占用。websearch 校准：中位我方份额 ~40-50%（对应 0068 实测 6.bin 中位 36%）。"""
    out = []
    if kind == "none":
        out = [0.0] * n
    elif kind == "fair50":
        out = [0.5 * MU * RTT_P] * n
    elif kind == "websearch":
        for _ in range(n):
            u = rnd.random()
            if u < 0.10:                      # 空闲轮（大流间隙）
                out.append(0.05 * MU * RTT_P * rnd.random())
            elif u < 0.75:                    # 小流轮（数 KB~数 MB 响应）
                out.append((0.30 + 0.25 * rnd.random()) * MU * RTT_P)
            else:                             # 大流轮（数 MB~30MB）
                out.append((0.55 + 0.40 * rnd.random()) * MU * RTT_P)
    elif kind == "monster":
        out = [0.98 * MU * RTT_P] * n
    else:
        raise ValueError(kind)
    return out


def run_exp(title, r_module, bg_kind, nrounds, seed=7, file_pkt=None, quiet=False):
    s = BbrSim(r_module=r_module, seed=seed, file_pkt=file_pkt)
    rnd = random.Random(seed + 1)
    bg = bg_profile(bg_kind, rnd, nrounds)
    for i in range(nrounds):
        s.step_round(bg[i])
    q_peak = max(h["q"] for h in s.history)
    q_mean = sum(h["q"] for h in s.history) / nrounds
    loss = s.drops / max(s.sent_total, 1) * 100
    good = s.delivered_total / (nrounds * RTT_P)
    if not quiet:
        rlab = "None(不钳位)" if r_module is None else f"{r_module:.2f}"
        print(f"### {title}")
        print(f"- 模块钳位 R={rlab} pkt/ms ｜ 背景={bg_kind} ｜ 轮数={nrounds}")
        print(f"- 终态: {s.phase}{'(ProbeRTT 进行中)' if s.phase_probe_rtt else ''}"
              f" ｜ BtlBw 估计 {s.btlbw:.2f}（线速 {MU:.2f}） ｜ RTprop {s.rtprop if s.rtprop else -1:.1f} ms")
        print(f"- 队列 峰值/均值 {q_peak:.0f}/{q_mean:.0f} 包 ｜ 我方丢包率 {loss:.2f}%"
              f" ｜ goodput {good:.2f} pkt/ms = {good/MU*100:.1f}% 线速"
              f" ｜ ProbeRTT 次数 {s.n_probe_rtt}（{s.probe_rtt_rounds} 轮）")
    return {"sim": s, "q_peak": q_peak, "q_mean": q_mean, "loss": loss, "good": good,
            "good_pct": good / MU * 100, "rtprop": s.rtprop if s.rtprop else -1,
            "phase": s.phase, "n_probe": s.n_probe_rtt}


def snap(s, k):
    print()
    print("| 轮 | 相位 | 增益 | 发送 | 背景 | 队列 | 丢包 | RTT | BtlBw | RTprop |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for h in s.history[:k]:
        print(f"| {h['round']} | {h['phase']} | {h['gain']:.2f} | {h['sent']:.0f} | {h['bg']:.0f} "
              f"| {h['q']:.0f} | {h['drop']:.0f} | {h['rtt']:.1f} | {h['btlbw']:.2f} | {h['rtprop']:.1f} |")
    print()


def main():
    print(">> 0069 BBRv1 滤波动力学轮级仿真 v3")
    print(f">> 常量: mu={MU} pkt/ms, RTT={RTT_P:.0f}ms, BDP={BDP:.0f}包, Q_lim={Q_LIM:.0f}, G={G_TIMER:.0f}ms")
    print()
    print("## A. 状态机动力学四景")
    print()
    r = run_exp("A1 origin 默认（不钳位，BBR 自由爬坡，空背景）", None, "none", 40)
    snap(r["sim"], 14)
    r = run_exp("A2 origin 默认 + websearch 背景", None, "websearch", 60)
    snap(r["sim"], 14)
    r = run_exp("A3 precise 96 Mbps（R=8.00 pkt/ms）+ websearch 背景", 8.0, "websearch", 60)
    snap(r["sim"], 14)
    r = run_exp("A4 origin 默认 + 巨流窗口（monster 98% 占用）", None, "monster", 30)
    snap(r["sim"], 10)
    print("## B. 钳位速率 R 扫描（websearch 背景，60 轮，种子固定）")
    print()
    print("| R(Mbps) | goodput(%线速) | 丢包率 | 队列峰值 | RTprop(ms) | 终态 |")
    print("|---|---|---|---|---|---|")
    for mbps in (100, 96, 90, 85, 70, 50):
        r_pkt = mbps * 1e6 / 8 / 1200 / 1000
        res = run_exp(f"B{mbps}", r_pkt, "websearch", 60, quiet=True)
        print(f"| {mbps} | {res['good_pct']:.1f}% | {res['loss']:.2f}% | {res['q_peak']:.0f} "
              f"| {res['rtprop']:.1f} | {res['phase']} |")
    print()
    print("## C. 长文件视角（6.bin ≈ 21s = 300 轮，R=8.0）：RTprop 窗口续签对照实验")
    print()
    n6 = int(320 * 1024 * 1024 / 1200)
    r = run_exp("C1 巨流窗口（monster，队列常驻 -> 强制 ProbeRTT）", 8.0, "monster", 300, file_pkt=None)
    print()
    r = run_exp("C2 websearch 间歇空闲（空闲轮续签 min 滤波 -> ProbeRTT 不触发）", 8.0, "websearch", 300, file_pkt=n6)
    print()
    print("> 对照结论：仅当队列在整个 10s RTprop 窗口不排空时才触发 ProbeRTT（约 200ms 吞吐塌坑，"
          "代价 ≈200ms/10s = 2.0%）；websearch 的重尾间隙（10% 空闲轮）足以持续续签 min 滤波，"
          "ProbeRTT 不触发、RTprop 保持真实传播 RTT 70ms。这解释了为何碰撞窗口外的长文件稳态"
          "不会被 ProbeRTT 周期性打断。")
    print()
    print("## D. 解析验证")
    print()
    print(f"1. **BtlBw 最大滤波收敛**：冷启动 log2({BDP:.0f}/32)≈{math.log2(BDP/32):.1f} 轮"
          f"={math.log2(BDP/32)*RTT_P/1000:.2f}s 到达 BDP；钳位 R 下样本上界 = min(R, (1-rho_t)*mu)，"
          "10 轮（~0.7s）窗口过期后旧峰值失效。")
    print(f"2. **泵幅恒等式**：独占链路且 BtlBw 锁 C 时泵相超额 = 0.25*mu*RTT = {0.25*BDP:.0f} 包"
          f" > Q_lim={Q_LIM:.0f} -> 必然自致尾丢；模块钳位后泵速率 = min(1.25*BtlBw, R)，"
          "超额重写为 (min(1.25*BtlBw,R) - 可用排水)*RTT。")
    print(f"3. **泵相安全带**：不钳位且 BtlBw=mu 时安全条件 1.25*mu - mu ≤ (Q_lim-q_bg)/RTT "
          f"=> Q_lim ≥ {0.25*BDP:.0f} 包（不满足，BBRv1 在浅缓冲独占链路必然泵丢）；"
          "钳位 R ≤ mu 时泵被钳，风险退化为持续超额 R-share。")
    print(f"4. **RTprop 偏置定理**：仅当队列 10s 窗口不排空才偏置（偏置=q_min/mu）；"
          f"此时 ProbeRTT 每 10s 强制 cwnd<=4 约 {PROBE_RTT_MS:.0f}ms，窗口期吞吐代价 "
          f"{(PROBE_RTT_MS/1000)/(WINDOW_RT/1000)*100:.1f}%；队列间歇排空时 min 滤波被续签、"
          "ProbeRTT 不触发（C1/C2 对照）。")
    print(f"5. **G 量化偏差**：BtlBw 上偏因子 T/(T-G) = {RTT_P/(RTT_P-G_TIMER):.3f}"
          f"（+{(RTT_P/(RTT_P-G_TIMER)-1)*100:.1f}%）；RTprop 为 min 滤波，对量化噪声不敏感。")
    print("6. **fidelity 声明**：轮级流体模型（非逐包）；FIFO 尾丢按到达比例分摊；PTO/ACK 细节由 0070 承担；"
          "背景为三态近似（10% 空闲 / 65% 小流 30-55% / 25% 大流 55-95%）；"
          "样本语义为 delivered/RTT（真实 BBR 用 send-phase 区间，本模型在稳态等价、DRAIN 相有半轮偏差）。")


if __name__ == "__main__":
    main()
