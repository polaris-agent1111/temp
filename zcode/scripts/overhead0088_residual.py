# -*- coding: utf-8 -*-
"""0088 — 官方 6 个独立下载任务间系统缓存与连接重置残余开销测定.

纯本地闭门计算（numpy/scipy + runs/results.jsonl 既有本地数据，无网络）。

四个层面：
  A1 口径层   官方明文：总时间 = 六次下载耗时相加，配置写入生效时间不计入
              → 任务间空闲期（socket 释放、buffer 回收、配置写入）**不进入官方计时**；
              能进入计时的只有每次下载耗时内部的非传输部分。
  A2 恒等式   max|Σ downloads − total| 核验（计时是否连续相加、边界是否被吞掉）。
  A3 经验包络 per-bin min 与回归截距（本地 391 valid 样本）：
              T_i = α_i + β_i·proxy_i + ε，proxy = Σ_{j≠i} T_j（样本级背景强度代理）；
              α_i 含慢启动折算（0087 H1：≈0.35-0.49s）→ α_i − SS 才是连接/栈层残余。
  A4 理论界   QUIC 握手（冷 1 RTT / 0-RTT ≈ 0）、TIME_WAIT 不适用于 QUIC、
              内核 socket buffer 回收 O(µs) 且与下一连接并行 → 每 bin ≤ 1 RTT，
              全程 ≤ 6×70ms = 420ms（冷）/ ≤70ms（持续连接），占比 ≤0.32%。

输出: zcode/scripts/_0088_out.md
"""
import json
import sys
from collections import defaultdict

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

OUT = r"E:/Download/iDSN/zcode/scripts/_0088_out.md"
SIZES = {1: 10e6, 2: 20e6, 3: 40e6, 4: 80e6, 5: 160e6, 6: 320e6}
C_BPS = 12.5e6
RTT = 0.070
SS_FOLD = {1: 0.44, 2: 0.44, 3: 0.45, 4: 0.46, 5: 0.37, 6: 0.35}  # 0087 H1 慢启动折算 (s)

out = []
w = out.append

recs = []
with open(r"E:/Download/iDSN/runs/results.jsonl", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if not r.get("valid"):
            continue
        if "downloads" not in r or "total_seconds" not in r:
            continue
        recs.append(r)

w("# 0088 计算输出（overhead0088_residual.py）")
w("")
w("## A2 恒等式核验（官方口径：总时间 = 六次下载耗时相加）")
w("")
w(f"- valid 样本：{len(recs)} 条")
full = [r for r in recs if len(r["downloads"]) == 6]
dev = max(abs(sum(r["downloads"].values()) - r["total_seconds"]) for r in full)
w(f"- 六 bin 齐全样本：{len(full)} 条；max|Σ downloads − total| = {dev:.6f} s")
w("- 判定：per-bin 计时**连续相加、无缝隙**——官方总时间里不存在「任务间空闲期」分项，")
w("  任务间开销要么为 0，要么已含在各 per-bin 计时内部（连接建立/首包延迟）。")
w("")

# ---------------- A3 经验包络与回归 ----------------
w("## A3 经验包络与回归截距（本地样本，仅作量级参照——本地与官方口径不同）")
w("")
w("| bin | n | min (s) | p50 (s) | 满速 (s) | α_lo = min−满速 (s) | SS 折算 (s) | α_lo−SS (s) |")
w("|---|---|---|---|---|---|---|---|")
mins = {}
for i in range(1, 7):
    key = f"{i}.bin"
    v = np.array([r["downloads"][key] for r in full if key in r["downloads"]])
    ideal = SIZES[i] / C_BPS
    a_lo = v.min() - ideal
    mins[i] = v
    w(f"| {key} | {len(v)} | {v.min():.3f} | {np.median(v):.3f} | {ideal:.2f} "
      f"| {a_lo:+.3f} | {SS_FOLD[i]:.2f} | {a_lo - SS_FOLD[i]:+.3f} |")
w("")
w("注（口径诚实性）：背景需求 a=λE[S]/C≈1 是**常态**（0083），即使最幸运样本也背着")
w("份额税——6.bin 的 α_lo−SS=+29.3s 就是背景税（对照 0086 开环份额地板 55.2s 与本地")
w("min 55.29s 的量级一致），**不是**连接层残余。唯一较干净的行是 1.bin（最短 bin、")
w("背景暴露最小）：α_lo−SS=+0.132s ≈ 2×RTT，与「冷连接握手 70ms + 首字节 70ms」")
w("的理论界 140ms 吻合——这是残余开销存在的唯一可用经验锚点。")
w("**结论：本地经验分解无法把连接层残余从背景税中分离（短 bin 除外）；残余的定量")
w("只能依赖 A4 理论界 + A2 恒等式。**")
w("")

w("### 回归 T_i = α_i + β_i·proxy + ε（proxy = Σ_{j≠i} T_j，样本级背景强度代理；bootstrap 95% CI）")
w("")
rng = np.random.default_rng(42)
w("| bin | n | α (s) | α 95% CI | β (s/s) | β 95% CI |")
w("|---|---|---|---|---|---|")
mat = np.array([[r["downloads"][f"{i}.bin"] for i in range(1, 7)] for r in full])
for idx in range(6):
    y = mat[:, idx]
    x = mat.sum(axis=1) - y
    A = np.column_stack([np.ones_like(x), x])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    boot = np.empty((2000, 2))
    n = len(y)
    for b in range(2000):
        ii = rng.integers(0, n, n)
        Ab, yb = A[ii], y[ii]
        cb, *_ = np.linalg.lstsq(Ab, yb, rcond=None)
        boot[b] = cb
    lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)
    w(f"| {idx+1}.bin | {n} | {coef[0]:.2f} | [{lo[0]:.2f}, {hi[0]:.2f}] | "
      f"{coef[1]:.3f} | [{lo[1]:.3f}, {hi[1]:.3f}] |")
w("")
w("β>0 说明背景强度跨 bin 正相关（同一场次共享背景状态）；α 即回归意义下的固定部分，")
w("但长 bin 的 α 由**背景份额地板**主导（6.bin α=59.3s ≈ 0086 开环份额地板量级），")
w("连接层残余在 α 中不可辨识——回归只能给出「残余 ≪ α」的弱界。1.bin 的 α−SS≈0.8s")
w("（CI 上界 2.4s−0.44s）与 2 RTT 理论界同量级，是唯一可用经验锚点。")
w("")

# wall - total（本地 harness 编排开销，官方不计）
dw_all = np.array([r["wall_seconds"] - r["total_seconds"] for r in full if "wall_seconds" in r])
dw = dw_all[dw_all >= 0]   # 排除批量导入记录（wall 字段跨批次不可比，负值即此类）
if len(dw):
    w(f"### 本地 harness 编排开销（wall − total ≥ 0 子集，官方计时不含此类开销）")
    w("")
    w(f"- 全体 n={len(dw_all)}（其中 {len(dw_all)-len(dw)} 条为批量导入记录 wall<total，已剔除），"
      f"干净子集 n={len(dw)}")
    w(f"- 干净子集：mean={dw.mean():.1f}s，p50={np.median(dw):.1f}s，min={dw.min():.1f}s")
    w("- 含配置写入、tar 分发、评测器编排等；官方口径「配置写入生效时间不计入下载耗时」，")
    w("  且总时间=六次相加 → 这些一律在官方计时之外。仅用于说明本地与官方计时边界不同。")
w("")

# ---------------- A4 理论界 ----------------
w("## A4 理论界（socket/内核层，每 bin 边界）")
w("")
w("| 开销项 | 冷连接假设 | 持续连接假设 | 是否进入官方计时 | 依据 |")
w("|---|---|---|---|---|")
w("| QUIC 握手（Initial+Handshake） | 1 RTT = 70 ms | 0（复用）/ 0-RTT ≈ 0 | **是**（含在 per-bin 内） | RFC 9002；RTT=70ms 官方拓扑 |")
w("| TLS/证书验证 | 并行于握手窗内 | 0 | 是（同上） | 已含 1 RTT 口径 |")
w("| 请求-响应首字节（服务端 pacer 重配后首包） | ≤1 RTT | ≤1 RTT | 是 | 官方：配置写入不计入，但生效后首包计入 |")
w("| 连接关闭（QUIC CONNECTION_CLOSE drain） | 1 RTT | 1 RTT | **否**（末字节后） | 计时止于最后数据字节 |")
w("| TCP TIME_WAIT | 不适用 | 不适用 | 否 | QUIC/UDP 无 TIME_WAIT；连接 ID 状态由空闲超时管理（≈30s 量级，不阻塞新连接） |")
w("| 内核 socket buffer 回收（skb free） | O(µs) | O(µs) | 否（与下一连接并行） | 批量释放，不占关键路径 |")
w("| 端口/四元组复用冲突 | 0（QUIC CID 机制） | 0 | 否 | 无 TCP 四元组耗尽问题 |")
w("")
w("**每 bin 残余上界：**")
w("")
w("- 冷连接假设：握手 70ms + 首字节 ≤70ms → **≤ 140 ms/bin**（保守双计）；现实单 RTT 内完成握手+请求 → **70 ms/bin**")
w("- 持续连接假设：仅 1.bin 冷启动 70ms，其余 ≈ 0 → **全程 ≤ 70 ms**")
w("- 全程合计（冷连接 6 bin）：≤ 420 ms（保守）/ 70 ms（现实）；相对官方锚点 133.086s 占比 **≤ 0.32%**")
w("- 相对官方单发噪声 σ_d≈7.0s（0084）：残余 ≤ σ_d 的 6% —— **在官方分辨率下不可辨识**")
w("")

w("## A5 与官方成绩的分解对照（量级核算）")
w("")
t_ideal = sum(SIZES.values()) / C_BPS
w(f"- 满速总时间（630MB 独占线速）：{t_ideal:.1f}s")
w(f"- 官方锚点 133.086s：差值 {133.086 - t_ideal:.1f}s = 背景份额税（主导，0083/0086）")
w("  + 慢启动基线 6×≈0.37s ≈ 2.2s（0087 H1）+ 残余开销 ≤0.42s + 实现残差")
w("- 残余开销在差值中的占比 <0.5%：官方总时间的方差结构由背景与 CC 行为主导，")
w("  连接/socket 层残余不是优化对象（任何针对它的「优化」都不可能产生可测收益）。")
w("")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(out) + "\n")
print("written", OUT)
