# -*- coding: utf-8 -*-
"""0080 — Ethernet+IP+UDP+QUIC 每包协议头开销对 100 Mbps 净荷吞吐的绝对衰减精算.

确定性计算（stdlib-only，无随机数）：
  A. 报头解剖与每包线上开销 W 的构成；
  B. 净荷占比 / 100 Mbps 净荷天花板 / 绝对衰减（Mbps）对 P 的敏感表；
  C. pacer 计账口径歧义表：名义速率 × (W/L_counted) 的线上需求与积压增速；
  D. 冠军配置（token_bucket refill r/4000µs）突发占空比核算；
  E. QUIC long header（握手期）占比与可忽略性证明。

输出写入 zcode/scripts/_0080_out.md（UTF-8）。
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

OUT = Path(__file__).resolve().parent / "_0080_out.md"

LINK_MBPS = 100.0
LINK_BPS = LINK_MBPS * 1e6 / 8.0  # bytes/s

# ---------- A. 报头解剖（字节） ----------
ETH = {
    "preamble+SFD": 8,   # 7 + 1（物理层前导，不计入 FCS 但占线上时间）
    "MAC header": 14,    # 6+6+2
    "FCS": 4,
    "IFG": 12,           # 96 bit-time @100M = 0.96 µs
}
ETH_TOTAL = sum(ETH.values())          # 38
IP_UDP = 20 + 8                        # 28
QUIC_SHORT = 1 + 8 + 4 + 16            # form+DCID(8)+PN(4)+AEAD tag(16) = 29
QUIC_SHORT_CID16 = 1 + 16 + 4 + 16     # 37
QUIC_LONG = 1 + 4 + 1 + 4 + 8 + 4 + 16 # ver+dcid8+pn4+tag = 38（Initial 还要再加 token/AEAD 扩展）

def wire_bytes(P: int, quic_hdr: int = QUIC_SHORT) -> int:
    return ETH_TOTAL + IP_UDP + quic_hdr + P

# ---------- B. 净荷天花板敏感表 ----------
rows_b = []
for P in (1200, 1252, 1300, 1350, 1400, 1440, 1460):
    W = wire_bytes(P)
    frac = P / W
    ceil_payload = LINK_MBPS * frac
    rows_b.append((P, W, frac * 100, ceil_payload, LINK_MBPS - ceil_payload))

# ---------- C. pacer 计账口径歧义 ----------
# max_pacing_rate 单位是字节/秒（params_schema）。四口径：L_counted。
CONV = {
    "a) 净荷 1200B": 1200,
    "b) QUIC 数据报 1229B": 1200 + QUIC_SHORT,
    "c) IP+UDP+QUIC 1257B": IP_UDP + QUIC_SHORT + 1200,
    "d) 全线上 1295B": wire_bytes(1200),
}
NOMINAL_MBPS = [96.0, 98.0, 100.0]  # 对应 12.0/12.25/12.5 MB/s

rows_c = []
for conv_name, Lc in CONV.items():
    for Rm in NOMINAL_MBPS:
        R = Rm * 1e6 / 8.0          # bytes/s
        pps = R / Lc
        wire_mbps = pps * wire_bytes(1200) * 8 / 1e6
        payload_mbps = pps * 1200 * 8 / 1e6
        growth = max(0.0, wire_mbps - LINK_MBPS)
        fill_s = (40 * wire_bytes(1200)) / (growth * 1e6 / 8) if growth > 0 else None
        rows_c.append((conv_name, Lc, Rm, pps, wire_mbps, payload_mbps, growth, fill_s))

# ---------- D. 冠军配置占空比 ----------
REFILLS = [40, 38, 36]
rows_d = []
for r in REFILLS:
    W = wire_bytes(1200)
    burst_ms = r * W * 8 / (LINK_MBPS * 1e6) * 1000
    duty = burst_ms / 4.0
    rows_d.append((r, W, burst_ms, duty))
# 运行点（份额 41 Mbps / 高档 50 Mbps）下的平均占空比
share_mbps = 41.0
avg_us = wire_bytes(1200) * 8 / (share_mbps * 1e6) * 1e6  # 每包线上时间 (µs)
duty_op = share_mbps / LINK_MBPS * 100

# ---------- E. 握手期 long-header 占比 ----------
# 一次 QUIC 握手（Initial+Handshake，估算）：ClientHello ~1.2 KB 载荷分 1 包，
# Initial 载荷 ~1160B + 重传 1 次；握手包 2-3 个。粗算 long-header 包 ~6 个 vs 全程 ~52 万包。
TOTAL_PKTS = 630 * 1e6 / 1200  # 630 MB / 1200 B ≈ 52.5 万包
LONG_PKTS = 12                 # Initial×4 + Handshake×4 + 1-RTT 早期×4（高估）
long_share = LONG_PKTS / TOTAL_PKTS * 100

# ---------- 输出 ----------
L = []
L.append("# 0080 计算输出 — 每包协议头开销的净荷吞吐衰减\n")
L.append(f"线速 {LINK_MBPS:.0f} Mbps = {LINK_BPS:,.0f} B/s 线上预算\n")

L.append("## A. 报头解剖（每包线上字节）\n")
L.append("| 段 | 字节 |")
L.append("|---|---|")
for k, v in ETH.items():
    L.append(f"| {k} | {v} |")
L.append(f"| **Eth 框架合计** | **{ETH_TOTAL}** |")
L.append(f"| IPv4 头 | 20 |")
L.append(f"| UDP 头 | 8 |")
L.append(f"| QUIC short header（1+8 DCID+4 PN+16 AEAD） | {QUIC_SHORT} |")
L.append(f"| QUIC short（16B CID 变体） | {QUIC_SHORT_CID16} |")
L.append(f"| QUIC long header（握手期，下界） | {QUIC_LONG} |")
L.append(f"| **每包线上开销合计（short, 8B CID）** | **{ETH_TOTAL + IP_UDP + QUIC_SHORT}** |")
L.append(f"| **每包线上 W（P=1200）** | **{wire_bytes(1200)}** |")
L.append("")

L.append("## B. 净荷天花板与绝对衰减（100 Mbps，P 扫描）\n")
L.append("| P (B) | 线上 W (B) | 净荷占比 | 净荷天花板 (Mbps) | 绝对衰减 (Mbps) |")
L.append("|---|---|---|---|---|")
for P, W, frac, cp, att in rows_b:
    L.append(f"| {P} | {W} | {frac:.2f}% | {cp:.2f} | {att:.2f} |")
L.append("")
L.append(f"绝对衰减带宽区间 **{rows_b[-1][4]:.2f}–{rows_b[0][4]:.2f} Mbps**（{rows_b[-1][3]:.2f}%–{rows_b[0][3]:.2f}%）。\n")

L.append("## C. pacer 计账口径歧义：名义速率 × 线上放大\n")
L.append("W = {W}（P=1200, short header）。积压增速与 40 包 qdisc 灌满时间按满需求持续假设。\n".format(W=wire_bytes(1200)))
L.append("| 口径 | L_counted | 名义 (Mbps) | pps | 线上需求 (Mbps) | 净荷交付 (Mbps) | 积压增速 (Mbps) | 40 包灌满 |")
L.append("|---|---|---|---|---|---|---|---|")
for conv_name, Lc, Rm, pps, wire_mbps, payload_mbps, growth, fill_s in rows_c:
    fill = f"{fill_s*1000:.0f} ms" if fill_s else "—"
    L.append(f"| {conv_name} | {Lc} | {Rm:.0f} | {pps:,.0f} | {wire_mbps:.2f} | {payload_mbps:.2f} | {growth:.2f} | {fill} |")
L.append("")
L.append("口径 c/d（计数含 Eth 框架，罕见）96M 可持续；口径 a/b（最常见）96M 满需求时线上需求 >100 Mbps，"
         "持续灌满 40 包 qdisc 需 100–350 ms，随后必然丢包 → CC 退避。运行点实际平均份额 ≈41 Mbps（duty 41%），满需求假设不成立，"
         "故官方实测未见自拥塞塌方——税负只在「试图长期逼近名义速率」时兑现。\n")

L.append("## D. 冠军配置突发占空比（token_bucket refill r/4000µs）\n")
L.append("| refill r (pkt/4ms) | W (B) | 满需求突发线上时间 (ms) | 占空比 |")
L.append("|---|---|---|---|")
for r, W, burst_ms, duty in rows_d:
    flag = "✗ 超线速" if duty > 1.0 else "✓"
    L.append(f"| {r} | {W} | {burst_ms:.3f} | {duty*100:.1f}% {flag} |")
L.append("")
L.append(f"运行点口径：平均份额 ≈{share_mbps:.0f} Mbps → 平均占空比 {duty_op:.1f}%"
         f"（每包线上时间 {avg_us:.1f} µs）。\n")
L.append("关键发现：r=40 的满需求突发（4.144 ms）**超过** 4 ms 补充周期（占空比 103.6%）；"
         "r=38（3.937 ms, 98.4%）与 r=36（3.730 ms, 93.2%）恰好回到 1 以下——"
         "冠军配置后程把 refill 降到 38/36 获得了第二重物理保险（头开销税使 40/4ms 在 P=1200 口径下线速不可持续）。\n")

L.append("## E. 握手期 long-header 可忽略性\n")
L.append(f"- 全程估算 {TOTAL_PKTS:,.0f} 包；long/Initial 包 ≤{LONG_PKTS} 个（含重传高估）。")
L.append(f"- 占比 ≈ {long_share:.5f}% — 对总吞吐影响可忽略（<0.001 Mbps 级）。\n")

L.append("## F. 敏感性：CID/PN 变体对天花板的影响（P=1200）\n")
for name, H in (("short 8B CID + 4B PN", QUIC_SHORT), ("short 16B CID + 4B PN", QUIC_SHORT_CID16),
                ("short 8B CID + 2B PN", 1 + 8 + 2 + 16)):
    W = wire_bytes(1200, H)
    L.append(f"- {name}: W={W}, 净荷占比 {1200/W*100:.2f}%, 天花板 {LINK_MBPS*1200/W:.2f} Mbps")
L.append("")

L.append("## G. 限速域敏感性：100 Mbps 在哪一层执行（P=1200, short 8B CID）\n")
L.append("官方 Containernet 拓扑用 tc/netem|tbf|htb 在 veth 上限速，计数对象是 skb->len（含帧头不含 preamble/FCS/IFG）；"
         "只有物理网卡才吃满 38B 框架。三种执行域的天花板：\n")
L.append("| 执行域 | 每包开销 (B) | W (B) | 净荷占比 | 天花板 (Mbps) | 绝对衰减 (Mbps) |")
L.append("|---|---|---|---|---|---|")
DOMAINS = [
    ("L3 计数（净 IP 转发域，下界）", IP_UDP + QUIC_SHORT),
    ("L2-in-skb（veth/tc 计 skb->len）", 14 + IP_UDP + QUIC_SHORT),
    ("全物理框架（真实 NIC 线上，上界）", ETH_TOTAL + IP_UDP + QUIC_SHORT),
]
for name, oh in DOMAINS:
    W = 1200 + oh
    L.append(f"| {name} | {oh} | {W} | {1200/W*100:.2f}% | {LINK_MBPS*1200/W:.2f} | {LINK_MBPS-LINK_MBPS*1200/W:.2f} |")
L.append("")
L.append(f"→ 绝对衰减带宽最终口径 **4.53–7.34 Mbps**（1.6× 因子取决于限速域）；skb 域（官方最可能）≈5.59%，天花板 ≈94.41 Mbps。\n")

txt = "\n".join(L)
OUT.write_text(txt, encoding="utf-8")
print(f"written: {OUT} ({len(txt)} chars)")
