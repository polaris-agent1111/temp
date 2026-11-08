# -*- coding: utf-8 -*-
"""0249: IPv4/UDP/QUIC/HTTP3 各层报头损耗微积分与 Goodput 理论上限核算。

三部分：
  T  分层字节精算（含 QUIC varint 逐文件推导）→ 开销下界与载荷率带；
  V1 官方 v1/v1b 锚点零自由度预测检验（G=4000us + 载荷字节 → 预测总时长）；
  V2 本地 runs/results.jsonl 全量可行性检验（逐文件 goodput 不得超过理论上限）。

只读 runs/results.jsonl（红线允许读、禁止写）；输出 markdown 到 stdout。
"""
import json
import re
import sys
import time
import statistics
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "runs" / "results.jsonl"

# ---- 官方锚点（分析数据，非提交内容）：runs/submissions.jsonl + intel/raw/leaderboard_20261105-1628.json
OFFICIAL_V1 = 245.995   # 11-05 13:25 leak_bucket 9/30/1000us
OFFICIAL_V1B = 243.9583  # 11-05 14:23 同配置字节级一致
TOTAL_MB = 630.0        # 六份文件 10/20/40/80/160/320 MB（docs/extracted/六载穿柜.md）
MB = 1e6
G_US = 4000.0           # 量化粒度模型值（docs/knowledge/timer-granularity.md）


def varint_len(n: int) -> int:
    """QUIC 可变长整数编码长度：1/2/4/8 字节覆盖 6/14/30/62 位。"""
    for k, bits in ((1, 6), (2, 14), (4, 30), (8, 62)):
        if n < (1 << bits):
            return k
    raise ValueError(n)


def part_t():
    print("## T 分层字节精算（1200 B = IP 层满包口径，与 0198 一致）\n")
    print("| 层 | 字段 | 典型 (B) | 最小 (B) | 依据 |")
    print("|---|---|---|---|---|")
    rows = [
        ("IPv4", "固定头（无选项）", 20, 20, "RFC 791"),
        ("UDP", "固定头", 8, 8, "RFC 768"),
        ("QUIC 1-RTT 短头", "Flags 1 + DCID 8 + PN 编码 2", 11, "1+0+1=2", "RFC 9000 §32.1（PN 1-4B 采样编码，DCID 允许 0B）"),
        ("QUIC AEAD", "AES-128-GCM 认证标签", 16, 16, "RFC 9001 §5.4，强制"),
        ("QUIC STREAM 帧", "Type 1 + ID 1 + Offset 4 + Length 2", 8, "1+1+1+0=3", "RFC 9000 §19.8（无 LEN 位时帧吃满包尾）"),
        ("HTTP/3 DATA 帧", "Type 1 + Length 2（帧可跨 QUIC 包 → 摊销≈0）", "≈0（摊销）", "≈0", "RFC 9114 §4（流级抽象，不逐包重复）"),
    ]
    for layer, field, typ, mn, basis in rows:
        print(f"| {layer} | {field} | {typ} | {mn} | {basis} |")
    typ_total, min_total = 63, 49
    print(
        f"\n- **典型开销** = 20+8+11+16+8 = **{typ_total} B** → 载荷 1137 B，载荷率 γ_typ = **94.75%**"
        f"\n- **开销理论下界** = 20+8+2+16+3 = **{min_total} B** → γ_max = **95.92%**"
        f"\n- 0198 模型（STREAM 记 5 B，总 60 B）γ = 95.00%，落在本带内"
        f"\n- 载荷率带宽 = 95.92−94.75 = **1.17% ≤ 1.2% 核算门限**（模型不确定度本身受控）"
    )
    print("\n### QUIC varint 逐文件推导（Offset 字段随流偏移增长）\n")
    print("| 文件 | 大小 (MB) | 最大偏移 | <2^14(16.4KB) 段 | 其余段 Offset 字节 |")
    print("|---|---|---|---|---|")
    sizes = [10, 20, 40, 80, 160, 320]
    for i, mb in enumerate(sizes, 1):
        off = mb * MB
        print(f"| {i}.bin | {mb} | {off:,.0f} | 2 B（前 16.4 KB） | 4 B（<2^30=1.07 GB） |")
    print("\n（320 MB < 2^30，故全程 Offset ≤ 4 B，无 8 B 档；典型 8 B STREAM 控制字段成立。）")

    print("\n### Goodput 理论上限表（convention A：1200 B 满包；pps = rate/interval）\n")
    print("| 配置 (pkts/4ms) | 线速 (Mbps) | App 上限@γ_max (Mbps) | App 上限@γ_typ (Mbps) | 0198 口径 (Mbps) |")
    print("|---|---|---|---|---|")
    for r in (27, 36, 37, 40, 41):
        wire = r * 1200 * 8 / 0.004 / 1e6
        gmax = wire * 0.959167  # 1137+16=1151? no: gamma_max=(1200-49)/1200
        gtyp = wire * 1137 / 1200
        g0198 = wire * 1140 / 1200
        print(f"| {r} | {wire:.2f} | {gmax:.2f} | {gtyp:.2f} | {g0198:.2f} |")
    link_wire = 100.0
    print(
        f"| 100 Mbps 链路（与速率无关） | {link_wire:.2f} | {link_wire*(1200-49)/1200:.2f} "
        f"| {link_wire*1137/1200:.2f} | {link_wire*1140/1200:.2f} |"
    )
    print(
        "\n**尖锐结论**：r=41 的线速恰为 98.40 Mbps（< 100），但若采用「1200 B=QUIC 报文、"
        "IP/UDP 在外」的 convention B（线速 = 41×1228×8/4ms = **100.69 Mbps**）则已越过接入链路硬门限。"
        "两口径线速差 2.28%，是本模型唯一 >1.2% 的口径分歧点，V1 用官方锚点裁决。"
    )
    print(
        "\n**口径备注（L1 成帧）**：若平台按以太网成帧计时（前导 8 + MAC 14 + FCS 4 + 帧间隙 12 = 38 B/帧），"
        "r=41 的物理线速 = 41×1238×8/4ms ≈ 101.5 Mbps，convention A 下也越限；36/4ms（89.1 Mbps）不受影响。"
        "L1 计费口径不可观测（官方样本暂无 r=41 份额受限外的独立判据），列入待验证。"
    )


def predict_v1_time(payload_b: float) -> float:
    """leak 9/1000us 在 G=4000us 量化下：9 包/4ms = 2250 pkt/s × payload → 总时长（零自由度）。"""
    pps = 9.0 / (G_US * 1e-6)  # 相对调度被量化：实际漏出周期 = G
    return TOTAL_MB * MB * 8 / (pps * payload_b * 8)


def part_v1():
    print("\n## V1 官方锚点零自由度检验（leak 9/1000us，G=4000us 量化 → 2250 pkt/s）\n")
    print("| 载荷模型 | 载荷 (B) | 载荷率 | 预测总时长 (s) | 残差 vs 245.995 | 残差 vs 243.958 | 判定(≤1.2%) |")
    print("|---|---|---|---|---|---|---|")
    models = [
        ("开销下界 49B（γ_max）", 1200 - 49),
        ("本任务典型 63B（γ_typ）", 1200 - 63),
        ("0198 模型 60B", 1200 - 60),
        ("convention B 35B(QUIC内)+28B(外)", 1200 - 35),  # payload within 1200 datagram
        ("timer-granularity 旧口径（载荷=1200，靠残差拟合）", 1200),
    ]
    for name, pay in models:
        t = predict_v1_time(pay)
        r1 = (t - OFFICIAL_V1) / OFFICIAL_V1 * 100
        r2 = (t - OFFICIAL_V1B) / OFFICIAL_V1B * 100
        ok = "✓" if (abs(r1) <= 1.2 or abs(r2) <= 1.2) else "✗（需残差补偿）"
        print(f"| {name} | {pay} | {pay/1200*100:.2f}% | {t:.1f} | {r1:+.2f}% | {r2:+.2f}% | {ok} |")
    print(
        "\n- 载荷 1137–1151 B（本任务带）与 1140 B（0198）均在 ±1.2% 内命中官方双锚点"
        "（最大相对残差 −1.11%，即 ≤3 s）——**这就是「实测偏差 ≤1.2%」的可核验形态**：整条因果链"
        "（rate → G 量化 → pps → 载荷字节 → 时长）零自由度预测，误差即模型偏差。"
    )
    print(
        "- convention B（载荷 1165 B）偏离 2.3%，被官方锚点否决 → 平台口径支持"
        "「1200 B = IP 满包」（与 0198、与 timer-granularity 的 21.6 Mbps 换算一致）。"
    )
    print(
        "- 旧口径（载荷 1200 B）需 +11 s 人为残差才能命中（timer-granularity §2.3 已声明）；"
        "本任务把该残差吸收进 5% 报头开销后残差近零，模型更简洁。"
    )


def part_v2():
    print("\n## V2 本地全量可行性检验（runs/results.jsonl，只读）\n")
    sizes = [10, 20, 40, 80, 160, 320]
    link_cap_typ = 100.0 * 1137 / 1200
    link_cap_max = 100.0 * (1200 - 49) / 1200
    n_total = n_valid = 0
    viol = []
    best = (0.0, None, None)  # goodput, tag, file
    champ = []
    per_file_max = [0.0] * 6
    for line in RESULTS.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        n_total += 1
        if not rec.get("valid") or rec.get("invalid_reason"):
            continue
        dl = rec.get("downloads") or {}
        if len(dl) != 6:
            continue
        n_valid += 1
        tag = rec.get("tag", "?")
        for i in range(1, 7):
            t = dl.get(f"{i}.bin")
            if not t or t <= 0:
                continue
            gp = sizes[i - 1] * MB * 8 / t / 1e6
            if gp > per_file_max[i - 1]:
                per_file_max[i - 1] = gp
            if gp > best[0]:
                best = (gp, tag, i)
            if gp > link_cap_max:
                viol.append((tag, i, gp))
        if re.fullmatch(r"test-hybrid-tb4-p100M-p96M-r\d+", tag):
            champ.append(rec["total_seconds"])
    print(f"- 样本：共 {n_total} 行，valid 且 6 文件齐全 {n_valid} 行（清洗口径：valid=true，load-* 污染样本由 valid 标志排除）")
    print(f"- 链路 App 上限：γ_max 口径 {link_cap_max:.2f} Mbps、γ_typ 口径 {link_cap_typ:.2f} Mbps")
    print(f"- **逐文件 goodput 超上限违例数：{len(viol)}**（物理上不可能超链路上限；违例即模型或 MB 口径错误）")
    if viol:
        for tag, i, gp in viol[:10]:
            print(f"  - 违例：{tag} {i}.bin {gp:.2f} Mbps")
    print(f"- 全库单文件 goodput 峰值：{best[0]:.2f} Mbps（{best[1]} {best[2]}.bin）→ 上限裕量 {(link_cap_max-best[0])/link_cap_max*100:.1f}%")
    print("- 逐文件峰值（Mbps）：" + ", ".join(f"{i}.bin={v:.1f}" for i, v in enumerate(per_file_max, 1)))
    if champ:
        mu = statistics.fmean(champ)
        sd = statistics.stdev(champ) if len(champ) > 1 else 0.0
        print(
            f"\n- 冠军族 test-hybrid-tb4-p100M-p96M-r*：n={len(champ)}，均值 {mu:.2f} s，σ={sd:.2f} s，"
            f"均值口径吞吐 {630*MB*8/mu/1e6:.2f} Mbps（< 链路上限 {link_cap_max:.2f} ✓，"
            f"缺口由背景搜索流份额解释，非报头核算可消除）"
        )
    print(
        "\n**可识别性局限（诚实声明）**：在份额受限的实测中，γ 与背景流份额 ρ 在纯应用层计时下不可分离"
        "（measured_app = ρ·100·γ，(ρ,γ) 简并）；γ 的实测隔离依赖 V1 的速率受限锚点（pacer 为唯一瓶颈的场）。"
    )


def main():
    print("# 0249 Goodput 分层微积分与实测核对脚本输出")
    print(f"\n- 运行时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"- 数据：{RESULTS.name}（只读），官方锚点 245.995/243.9583 s（11-05 leak 9/30/1000us 两次独立提交）")
    print(f"- 口径：MB=1e6 B；总下载 630 MB；G={G_US:.0f} us\n")
    part_t()
    part_v1()
    part_v2()


if __name__ == "__main__":
    main()
