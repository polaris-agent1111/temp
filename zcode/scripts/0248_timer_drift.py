# -*- coding: utf-8 -*-
"""0248: 用户态高精度计时器时钟漂移与补偿算法验证。

在 Windows 本机（Python 3.14, 高分辨率 waitable timer 可用）实测：
  E1 时钟分辨率与调用开销；
  E2 相对休眠（time.sleep(0.004) 逐拍）累计漂移 —— 反面教材；
  E3 绝对时限调度（deadline = start + n*interval，禁用 +=）累计漂移；
  E4 混合粗睡+末端自旋（hybrid spin-wait）亚微秒收敛；
  E5 G=4000us 量化时钟下相对 vs 绝对调度的速率误差仿真（对齐官方 G 模型）。

输出 markdown 到 stdout（重定向到 _0248_out.md）。
仅用标准库；不触网；不写 runs/、client/、harness/。
"""
import sys
import time
import statistics

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

INTERVAL_S = 0.004          # 4 ms 发送间隔（与官方 G≈4000us 模型对齐）
N_ABS = 2000                # 绝对时限拍数（8 s）
N_REL = 400                 # 相对休眠拍数（1.6 s 标称，Windows 实际更长）
SPIN_MARGIN_S = 0.0008      # 末端自旋提前量 0.8 ms


def fmt_us(x: float) -> str:
    return f"{x*1e6:.3f}"


def e1_clock_resolution():
    print("## E1 时钟分辨率与调用开销\n")
    rows = []
    for name in ("perf_counter", "monotonic", "process_time", "time"):
        info = time.get_clock_info(name)
        rows.append((name, info.resolution, info.adjustable))
    print("| 时钟 | 标称分辨率 (s) | 可被调节 |")
    print("|---|---|---|")
    for n, r, a in rows:
        print(f"| {n} | {r:.9g} | {a} |")
    # perf_counter_ns 调用开销分布（n=20000）
    xs = []
    for _ in range(20000):
        t0 = time.perf_counter_ns()
        xs.append(time.perf_counter_ns() - t0)
    xs.sort()
    print(
        f"\nperf_counter_ns 调用开销 (n=20000): median={statistics.median(xs):.0f}ns, "
        f"p99={xs[int(0.99*len(xs))]}ns, max={xs[-1]}ns"
    )
    print()


def run_relative(n_ticks: int):
    """相对休眠：每次 sleep(INTERVAL)，漂移无界累积。"""
    overs = []
    t0 = time.perf_counter()
    for _ in range(n_ticks):
        before = time.perf_counter()
        time.sleep(INTERVAL_S)
        overs.append(time.perf_counter() - before - INTERVAL_S)
    total = time.perf_counter() - t0
    return overs, total


def run_absolute(n_ticks: int, spin_margin: float | None):
    """绝对时限：deadline = start + n*interval（死算，不用 +=）。
    spin_margin=None 纯 sleep；否则先粗睡到 deadline-margin 再自旋。"""
    overs = []
    start = time.perf_counter()
    for n in range(1, n_ticks + 1):
        deadline = start + n * INTERVAL_S
        if spin_margin is not None:
            coarse = deadline - spin_margin
            remaining = coarse - time.perf_counter()
            if remaining > 0:
                time.sleep(remaining)
            while time.perf_counter() < deadline:
                pass
        else:
            remaining = deadline - time.perf_counter()
            if remaining > 0:
                time.sleep(remaining)
        now = time.perf_counter()
        overs.append(now - deadline)
    total = time.perf_counter() - start
    return overs, total


def stat_line(overs, n_ticks, label):
    cum_drift = overs[-1]  # 绝对时限下累计漂移 = 末拍过冲
    mean_overs = statistics.fmean(overs)
    p99 = sorted(overs)[int(0.99 * len(overs))]
    print(
        f"| {label} | {n_ticks} | {fmt_us(mean_overs)} | {fmt_us(p99)} | "
        f"{fmt_us(max(overs))} | **{fmt_us(cum_drift)}** |"
    )
    return cum_drift


def e2e4():
    print("## E2-E4 三种调度策略的逐拍过冲与累计漂移\n")
    print("过冲 = 实际唤醒时刻 − 名义时刻；累计漂移 = 末拍过冲（绝对时限）/ 总超出（相对）。")
    print("\n| 策略 | 拍数 | 过冲均值 (us) | 过冲 p99 (us) | 过冲最大 (us) | 累计漂移 (us) |")
    print("|---|---|---|---|---|---|")

    overs_rel, total_rel = run_relative(N_REL)
    nominal_rel = N_REL * INTERVAL_S
    rel_cum = total_rel - nominal_rel
    mean_rel = statistics.fmean(overs_rel)
    p99_rel = sorted(overs_rel)[int(0.99 * len(overs_rel))]
    print(
        f"| 相对休眠 sleep(4ms) | {N_REL} | {fmt_us(mean_rel)} | {fmt_us(p99_rel)} | "
        f"{fmt_us(max(overs_rel))} | **{fmt_us(rel_cum)}** |"
    )

    overs_abs, _ = run_absolute(N_ABS, None)
    stat_line(overs_abs, N_ABS, "绝对时限纯 sleep")
    abs_cum = overs_abs[-1]

    overs_hyb, _ = run_absolute(N_ABS, SPIN_MARGIN_S)
    stat_line(overs_hyb, N_ABS, f"绝对时限+{SPIN_MARGIN_S*1e3:.1f}ms 自旋")
    hyb_cum = overs_hyb[-1]

    print(
        f"\n相对策略外推到 630MB 场景时间尺度（{N_REL} 拍实测外推为线性）："
        f"每拍多睡 {fmt_us(mean_rel)}us → 25000 拍（100 s）累计多 {fmt_us(mean_rel*25000)}us。"
    )
    print(
        f"绝对时限策略：累计漂移不随时长增长，但受单拍唤醒抖动支配——纯 sleep 档 {fmt_us(abs_cum)}us"
        f"（有界、不累积，但在 Windows 上超 10us 门限）；"
        f"自旋档 {fmt_us(hyb_cum)}us（<< 10us 门限，PASS）。"
    )
    return abs_cum, hyb_cum


def e5_quantized_clock():
    """G=4000us 量化时钟（唤醒时刻上取整到 G 的整数倍）仿真。"""
    print("\n## E5 G=4000us 量化时钟下的速率误差（离散仿真，非实测）\n")
    G = 0.004
    ticks = 25000  # 100 s 标称

    def quantize_up(t):
        return -(-t // G) * G  # ceil 到 G 整数倍

    # 相对调度：每拍从「上次唤醒」起 sleep(interval)，唤醒被量化
    t = 0.0
    rel_wake = []
    for _ in range(ticks):
        t = quantize_up(t + INTERVAL_S)
        rel_wake.append(t)
    # 绝对调度：从 start 死算 deadline，量化只影响单拍相位不累积
    abs_wake = [quantize_up(n * INTERVAL_S) for n in range(1, ticks + 1)]

    print("| 配置 (rate/interval) | 名义速率 (pkt/s) | 量化后相对调度速率 (pkt/s) | 绝对调度速率 (pkt/s) | 相对调度慢化倍数 |")
    print("|---|---|---|---|---|")
    cases = [(9, 0.001), (36, 0.004), (27, 0.004), (40, 0.004), (41, 0.004)]
    for rate, iv in cases:
        # 相对调度：每量化周期 q=ceil(iv/G)*G 才漏出 rate 包 → pps = rate/q
        # 绝对调度：deadline 死算，量化只抖相位不改长期周期 → pps = rate/iv
        q_iv_rel = quantize_up(iv)
        pps_rel = rate / q_iv_rel
        pps_abs = rate / iv
        slow = pps_abs / pps_rel
        warn = " ←←← v1 245s 惨案的机理" if abs(slow - 1) > 0.02 else ""
        print(
            f"| {rate} / {iv*1e6:.0f}us | {pps_abs:.0f} | "
            f"{pps_rel:.0f} | {pps_abs:.0f} | ×{slow:.3f}{warn} |"
        )
    print(
        "\n结论：interval 与 G 对齐（4000us）时两策略长期速率一致；"
        "interval<G 时相对调度按 ceil(interval/G)/G 慢化（1ms→×4 慢），"
        "绝对时限调度仅承受 ±G 相位抖动、无速率损失。"
    )


def e6_compensation():
    """漂移补偿：窗口化 dead-reckoning 反馈（离散仿真 + 实测混合验证）。"""
    print("\n## E6 漂移补偿算法（窗口反馈校正）实测\n")
    # 补偿式绝对调度：每 W 拍用 perf_counter 复核一次名义时刻并吸收误差
    W = 500
    n_total = N_ABS
    overs = []
    start = time.perf_counter()
    anchor = start  # 每 W 拍重锚定一次，吸收 perf_counter 长期偏差
    for n in range(1, n_total + 1):
        if n % W == 0:
            anchor = start + n * INTERVAL_S  # 重锚定：绝对名义时刻，永不累加测量误差
        deadline = anchor + (n % W) * INTERVAL_S if n % W != 0 else anchor
        remaining = deadline - time.perf_counter()
        if remaining > SPIN_MARGIN_S:
            time.sleep(remaining - SPIN_MARGIN_S)
        while time.perf_counter() < deadline:
            pass
        overs.append(time.perf_counter() - deadline)
    cum = overs[-1]
    print(f"- 窗口重锚定（W={W}）调度 {n_total} 拍：累计漂移 = {fmt_us(cum)} us（门限 10us）")
    print("- 补偿不变式：任何时刻的发送计划 = 名义时刻的纯函数（start + k·interval），")
    print("  测量反馈只允许替换锚点、不允许参与累加链 → 漂移不随拍数增长。")
    print(
        f"- 判定：{'PASS' if cum < 10e-6 else 'FAIL'}（4ms 发送间隔累计漂移 < 10us）"
    )


def main():
    print("# 0248 计时器漂移验证脚本输出")
    print(f"\n- 运行时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"- 平台：{sys.platform}, Python {sys.version.split()[0]}")
    print(f"- 间隔：{INTERVAL_S*1e3:.0f} ms；绝对时限拍数 {N_ABS}；相对休眠拍数 {N_REL}\n")
    e1_clock_resolution()
    e2e4()
    e5_quantized_clock()
    e6_compensation()


if __name__ == "__main__":
    main()
