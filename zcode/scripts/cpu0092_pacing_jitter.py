# -*- coding: utf-8 -*-
"""0092 — 官方宿主机 CPU 亲和性与上下文切换对微秒级 Pacing 稳定性的干扰测度.

模型：leak_bucket interval 模式的唤醒路径抖动分解。
  每 tick（T=4000µs）唤醒一次发牌线程，随后按 T_e = T/rate 严格单包等间隔出包（0085 语义）。
  每次「计时器到点 → 包真正离开」之间存在 CPU 调度链延迟 δ：
    δ = δ_dispatch(定时器回调分发) + Σ(上下文切换直接/间接成本) + CFS 抢占等待 + (迁移成本, 若无亲和性)
  leak 语义下延迟不产生 token 超发（不发突发），唯一通道是「有效周期被拉长 → 速率折损」
  与「间隔抖动 → 出口微队列」（0066/0076/0085 口径）。

干扰测度定义：
  I1 速率折损  = E[δ] / T
  I2 聚簇触发  = P(δ > g)，g = clock_granularity = 1000µs（0076 聚簇下界之外的新增项）
  I3 间隔抖动  = 出包间隔的 P99 / 出口服务余量 (T_e − 96µs = 15µs @ r=36)
  I4 换算时延  = 下载全程的速率折损时间，与官方单发噪声 σ_d = 7.02s（0084）对比得无量纲比值

场景全部为「文献量级假设参数」的闭门推演，不声称任何实测；所有常量出处见
docs/analysis/0092-theory-audit.md 的参数表。
"""
import math
import numpy as np

rng = np.random.default_rng(42)

T_TICK = 4000.0        # µs，官方 tick 粒度 G（docs/knowledge/timer-granularity.md）
G_GRAN = 1000.0        # µs，clock_granularity 官方容差语义
RATE = 36.0            # 包/tick（Shot 2 后程构型）
T_E = T_TICK / RATE    # 111.1µs 单包间隔
SERVICE = 96.0         # µs，100Mbps egress 单包串行化（0085：1/96µs）
SLACK = T_E - SERVICE  # 15.1µs：间隔抖动不产生排队的安全余量
T_DOWNLOAD = 124.0     # s，当前官方锚点（Shot 2 = 124.3683）
SIGMA_D = 7.02         # s，官方单发噪声后验（0084）
N_TICKS = int(T_DOWNLOAD * 1e6 / T_TICK)  # 一次下载的 tick 数 ≈ 31_000


def draw_dispatch(n):
    """定时器回调分发基线：对数正态，中位 3µs、P99≈12µs（文献量级）。"""
    return rng.lognormal(mean=math.log(3.0), sigma=0.7, size=n)


def draw_cs_component(n, lam_cs, q_mig):
    """窗口内上下文切换叠加成本。
    lam_cs: 每核每秒切换次数（含本窗口内的所有入侵源：softirq/其他容器任务）
    直接成本 c_dir ~ U(1.2, 3) µs（存/恢复寄存器，Li et al. 量级）
    间接成本（cache/TLB 污染）以 q_ind=0.3 概率出现 ~ Exp(20µs)
    迁移成本（跨核 IPI + 冷 L3）以 q_mig 概率出现 ~ Exp(50µs)
    """
    lam_us = lam_cs * 1e-6
    k = rng.poisson(lam_us, size=n)             # 111µs 窗口内的切换次数
    total = np.zeros(n)
    if k.max() > 0:
        total += np.minimum(k, 8) * rng.uniform(1.2, 3.0, size=n)  # 直接成本，截断防长尾
        ind = rng.random(n) < 1 - np.exp(-lam_us * 0.3)            # 窗口内至少一次带污染的切换
        total += ind * rng.exponential(20.0, size=n)
    mig = rng.random(n) < q_mig
    total += mig * rng.exponential(50.0, size=n)
    return total


def draw_cfs_wait(n, rho, regime):
    """CFS 抢占等待。
    regime='normal'：唤醒时 CPU 被占的概率 rho，命中则等剩余片 ~ Exp(100µs)
    regime='pathological'：N_c 个等权任务公平轮转，等待 ~ U(0, sched_period)，period=24ms
    regime='none'：专用核（理想亲和）
    """
    if regime == 'none':
        return np.zeros(n)
    if regime == 'normal':
        hit = rng.random(n) < rho
        return hit * rng.exponential(100.0, size=n)
    if regime == 'pathological':
        hit = rng.random(n) < rho
        return hit * rng.uniform(0.0, 24000.0, size=n)
    raise ValueError(regime)


SCENARIOS = {
    # 名称: (lam_cs 每核切换/s, q_mig 无亲和迁移概率, rho, cfs regime)
    'S0 空闲主机·无亲和':        (150.0,  0.05, 0.05, 'normal'),
    'S1 空闲主机·绑核':          (150.0,  0.005, 0.05, 'normal'),
    'S2 中载 ρ=0.5·绑核':        (5000.0, 0.005, 0.50, 'normal'),
    'S3 中载 ρ=0.5·无亲和':      (5000.0, 0.10,  0.50, 'normal'),
    'S4 重载 ρ=0.9·无亲和':      (20000.0, 0.15, 0.90, 'normal'),
    'S5 公平轮转风暴(4任务)·绑核': (20000.0, 0.005, 0.90, 'pathological'),
}


def simulate(name, lam_cs, q_mig, rho, regime, n=N_TICKS):
    disp = draw_dispatch(n)
    cs = draw_cs_component(n, lam_cs, q_mig)
    cfs = draw_cfs_wait(n, rho, regime)
    delta = disp + cs + cfs                      # 每次 tick 唤醒的调度链延迟
    rate_loss = delta.mean() / T_TICK            # I1：E[δ]/T
    p_gran = float((delta > G_GRAN).mean())      # I2：P(δ>g)
    dT_rate = T_DOWNLOAD * rate_loss             # 速率折损换算的全程时延
    # I3：包间隔抖动 → 出口微队列（间隔抖动≈相邻两次唤醒延迟之差 + slot 内 cs 抖动）
    jit = np.abs(np.diff(delta)) / RATE + cs[1:] / RATE   # 粗略分配到每个 slot
    q_depth = np.where(jit > SLACK, np.ceil((jit - SLACK) / SERVICE), 0.0)
    ratio = dT_rate / SIGMA_D
    return dict(
        name=name,
        mean_delta_us=delta.mean(),
        p99_delta_us=np.percentile(delta, 99),
        p_gran_ppm=p_gran * 1e6,
        rate_loss_ppm=rate_loss * 1e6,
        dT_rate_s=dT_rate,
        q_depth_p99=np.percentile(q_depth, 99),
        ratio_vs_sigma_d=ratio,
    )


def analytic_bounds():
    """闭式上界（不依赖 MC 抽样误差）：
    灾难情形 P(δ>4ms)=10⁻³（每千 tick 一次双 tick 合并）时的速率折损上界。
    """
    worst_miss_ppm = 1000.0                       # 10⁻³ per tick
    rate_loss_worst = worst_miss_ppm * 1e-6 * (T_TICK / T_TICK)  # 每次合并丢一个 tick 产出
    dT_worst = T_DOWNLOAD * rate_loss_worst
    return worst_miss_ppm, rate_loss_worst * 1e6, dT_worst, dT_worst / SIGMA_D


def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    out = []
    out.append('=== 0092 CPU 亲和性/上下文切换干扰测度 MC（seed=42, N=%d ticks/download）===' % N_TICKS)
    out.append(f'参数: T_tick={T_TICK:.0f}µs rate={RATE:.0f}/tick T_e={T_E:.1f}µs service={SERVICE:.0f}µs '
               f'slack={SLACK:.1f}µs g={G_GRAN:.0f}µs')
    out.append(f'下载锚点 T_dl={T_DOWNLOAD:.1f}s  官方单发噪声 σ_d={SIGMA_D:.2f}s (0084)')
    out.append('')
    hdr = (f"{'场景':<22}{'E[δ] µs':>9}{'P99 δ µs':>10}{'P(δ>g) ppm':>12}"
           f"{'速率折损 ppm':>13}{'ΔT_rate s':>11}{'队列深 P99':>11}{'ΔT/σ_d':>9}")
    out.append(hdr)
    for name, (lam, qm, rho, reg) in SCENARIOS.items():
        r = simulate(name, lam, qm, rho, reg)
        out.append(f"{name:<22}{r['mean_delta_us']:>9.1f}{r['p99_delta_us']:>10.1f}"
                   f"{r['p_gran_ppm']:>12.1f}{r['rate_loss_ppm']:>13.1f}{r['dT_rate_s']:>11.3f}"
                   f"{r['q_depth_p99']:>11.1f}{r['ratio_vs_sigma_d']:>9.4f}")
    out.append('')
    ppm, rl, dtw, ratio = analytic_bounds()
    out.append('=== 闭式灾难上界：P(δ>4ms)=10⁻³/tick（双 tick 合并） ===')
    out.append(f'P_miss={ppm:.0f} ppm/tick → 速率折损={rl:.0f} ppm → ΔT={dtw:.3f}s → ΔT/σ_d={ratio:.4f}')
    out.append('')
    out.append('=== 亲和性净收益分解（S3 − S1 同参数对照） ===')
    r_no = simulate('x', 5000.0, 0.10, 0.50, 'normal')
    r_aff = simulate('x', 5000.0, 0.005, 0.50, 'normal')
    gain = r_no['dT_rate_s'] - r_aff['dT_rate_s']
    out.append(f"无亲和 ΔT={r_no['dT_rate_s']:.4f}s → 绑核 ΔT={r_aff['dT_rate_s']:.4f}s，净收益={gain:.4f}s")
    out.append(f"（迁移项期望 = q_mig×E[Exp(50µs)] = {0.10*50:.1f}µs/wake × {N_TICKS} wakes "
               f"≈ {0.10*50*N_TICKS/1e6:.3f}s，与 MC 净收益同量级）")
    print('\n'.join(out))


if __name__ == '__main__':
    main()
