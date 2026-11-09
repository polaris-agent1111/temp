#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""timer_model.py — 「官方定时器粒度」定量模型（标准库，零依赖）

背景（见 docs/knowledge/timer-granularity.md）:
  leak_bucket 是五模块中唯一没有 enable_n_in_flight 旁路的模块，速率完全绑定
  leak_interval_us 定时器。若官方运行时定时器实际粒度为 G µs，则实际漏出间隔
  被抬升到 ceil(interval/G)*G，速率按比例衰减；当衰减后的标称速率跌破本地实测
  有效份额（≈41 Mbps）时，整形器从「非绑定」翻转为「绑定」，总时长暴涨。

模型（3 个经验拟合参数，均可溯源）:
  eff_interval = ceil(interval_us / G) * G                     (µs)
  cap_mbps     = (rate / eff_interval_s) * pkt_bytes * 8 / 1e6
  T_pred       = TOTAL_MB*8 / min(cap_mbps, share) + delta     (秒)
  TOTAL_MB=630, pkt_bytes=1200(拟合), share=41 Mbps(本地实测 630*8/123.81),
  delta=+11 s(官方残差, 拟合自 leak9@G=4000: 244.5-233.3)

用法:
  python tools/timer_model.py table    [--G 2000,4000,10000] [--pkt 1200] [--share 41] [--delta 11]
  python tools/timer_model.py equiv    [--targets 9000,4271]
  python tools/timer_model.py fit      # 用 5 个已知官方成绩反推/校验 G
  python tools/timer_model.py sweep-G  # 扫描 G, 看哪个 G 同时命中 v1(244) 与 S4(133)
"""
import argparse
import math

TOTAL_MB = 630.0
PKT = 1200          # 有效载荷字节/包（拟合值，待验证）
SHARE = 41.0        # 本地实测有效份额 Mbps = 630*8/123.81
DELTA_OFF = 11.0    # 官方固定残差（秒），拟合自 leak9@G=4000
DELTA_LOC = 1.0     # 本地残差（秒）

# 已知观测（来源: runs/submissions.jsonl + intel/raw/leaderboard_*.json + STATUS.md）
# name, leak_rate, leak_interval_us, 本地(提交时单次), 官方
OBSERVED = [
    ("v1/v1b leak9/1000", 9, 1000, 121.5, 244.98),   # 官方=245.995/243.958 均值
    ("S3 tb 20/1000(refill)", 20, 1000, 128.6, 140.927),  # token_bucket 走 refill 定时器，同模型
    ("S4 leak36/4000", 36, 4000, 122.95, 133.086),
    ("S5 leak27/4000", 27, 4000, 123.41, None),      # 16:24 提交，截至 16:28 未出分
]


def eff_interval(interval_us, g):
    return math.ceil(interval_us / g) * g


def cap_mbps(rate, interval_us, g, pkt=PKT):
    pps = rate / (eff_interval(interval_us, g) / 1e6)
    return pps * pkt * 8 / 1e6


def predict_total(cap, share=SHARE, delta=DELTA_OFF):
    return TOTAL_MB * 8 / min(cap, share) + delta


def equiv_rate(target_pps, interval_us):
    return math.ceil(target_pps * interval_us / 1e6)


def cmd_table(args):
    gs = [int(x) for x in args.G.split(",")]
    configs = [(9, 1000), (18, 2000), (27, 4000), (36, 4000), (24, 4000), (20, 1000)]
    print(f"包长={args.pkt}B  份额={args.share}Mbps  官方残差=+{args.delta}s  总量={TOTAL_MB}MB")
    print(f"{'配置':26s} " + " ".join(f"G={g:<6d}" for g in gs))
    print(f"{'':26s} " + " ".join(f"{'cap/T(官)':>13s}" for _ in gs))
    for rate, itv in configs:
        cells = []
        for g in gs:
            c = cap_mbps(rate, itv, g, args.pkt)
            t = predict_total(c, args.share, args.delta)
            cells.append(f"{c:5.1f}/{t:6.1f}s")
        name = f"leak {rate}/{itv}"
        print(f"{name:26s} " + " ".join(f"{c:>13s}" for c in cells))
    print("\n读法: cap=衰减后标称速率(Mbps), T=预测官方总耗时; cap<份额 时 T 随 cap 崩塌。")


def cmd_equiv(args):
    targets = [int(x) for x in args.targets.split(",")]
    intervals = [1000, 2000, 3000, 4000, 5000, 10000]
    print(f"{'interval_us':>12s} " + " ".join(f"rate@{t}pps" .rjust(12) for t in targets))
    for itv in intervals:
        row = [equiv_rate(t, itv) for t in targets]
        print(f"{itv:>12d} " + " ".join(str(r).rjust(12) for r in row))
    print("\n目标 9000pps = 本地 leak9 标称(9包/ms); 目标 4271pps = 41Mbps 份额@1200B。")
    print("约束: bucket_cap >= leak_rate（cap 至少取该行 rate）。")


def cmd_fit(args):
    print(f"{'配置':26s} {'本地':>8s} {'官方实测':>9s} {'G=1000':>8s} {'G=4000':>8s} {'G=10000':>9s}")
    for name, rate, itv, loc, off in OBSERVED:
        row = []
        for g in (1000, 4000, 10000):
            t = predict_total(cap_mbps(rate, itv, g), SHARE, DELTA_OFF)
            row.append(f"{t:7.1f}s")
        off_s = f"{off:8.3f}s" if off else "  待出分"
        print(f"{name:26s} {loc:7.1f}s {off_s:>9s} " + " ".join(row))
    print("\n结论读法: v1 官方 244.98 只有 G=4000 列能命中(233+11); G=10000 时 S4 的 cap=34.6<41")
    print("会预测 156.8s ≠ 实测 133.086, 故被 S4 排除; G=1000/2000 时 v1 不崩塌(133.9)亦被排除。")


def cmd_sweep(args):
    print("扫描 G: 目标同时命中 v1(244.98±2) 与 S4(133.086±3)")
    print(f"{'G(us)':>8s} {'v1预测':>9s} {'S4预测':>9s} {'S5预测':>9s}  命中")
    for g in range(1000, 12001, 500):
        t1 = predict_total(cap_mbps(9, 1000, g))
        t4 = predict_total(cap_mbps(36, 4000, g))
        t5 = predict_total(cap_mbps(27, 4000, g))
        hit = "OK" if abs(t1 - 244.98) <= 6 and abs(t4 - 133.086) <= 6 else ""
        print(f"{g:>8d} {t1:8.1f}s {t4:8.1f}s {t5:8.1f}s  {hit}")
    print("\n命中区间即 G 的可行域（含 ±6s 模型残差容差）；中心期望值 4000µs(HZ=250)。")


def main():
    ap = argparse.ArgumentParser(description="官方定时器粒度定量模型")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("table", help="配置×粒度 理论官方值对照表")
    p.add_argument("--G", default="2000,4000,10000")
    p.add_argument("--pkt", type=int, default=PKT)
    p.add_argument("--share", type=float, default=SHARE)
    p.add_argument("--delta", type=float, default=DELTA_OFF)
    p.set_defaults(fn=cmd_table)
    p = sub.add_parser("equiv", help="等效速率表: 各 interval 要写多少 leak_rate")
    p.add_argument("--targets", default="9000,4271")
    p.set_defaults(fn=cmd_equiv)
    p = sub.add_parser("fit", help="5 个已知官方成绩 vs 模型")
    p.set_defaults(fn=cmd_fit)
    p = sub.add_parser("sweep-G", help="扫描 G 寻找同时命中 v1 与 S4 的可行域")
    p.set_defaults(fn=cmd_sweep)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
