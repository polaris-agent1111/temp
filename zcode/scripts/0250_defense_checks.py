# -*- coding: utf-8 -*-
"""0250: 答辩手册 Q11-Q15 引用数字一致性校验。

每一条被引用的数字都对源文件做文本断言 + 算术复推；任何一条失败脚本退出码非 0。
只读仓库文件；不触网；不写 runs/、client/、harness/。
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
FAILS = []


def check(name: str, ok: bool, detail: str = ""):
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILS.append(name)


def src(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


def has_text(rel: str, needles: list[str], name: str):
    text = src(rel)
    missing = [n for n in needles if n not in text]
    check(name, not missing, ("缺失: " + "; ".join(missing)) if missing else f"{len(needles)} 项全部命中 ({rel})")


# ---- 1. 文本断言：每个引用数字的源 ----
has_text("docs/extracted/六载穿柜.md",
         ["| 1.bin | 10 MB |", "| 6.bin | 320 MB |", "六份合计 630 MB"],
         "Q11/Q12/Q14: 六份文件大小与总量（六载穿柜.md）")

has_text("docs/analysis/0085-theory-audit.md",
         ["0.157%", "4.513%", "36.342%", "29 倍"],
         "Q11: 批量惩罚律三档数值（0085）")

has_text("docs/analysis/0160-theory-audit.md",
         ["3.64"],
         "Q12/Q14: ±1 包邻域梯度 3.64 s/pkt（0160）")

has_text("docs/analysis/0185-theory-audit.md",
         ["89.14%", "24.49%", "40.16%"],
         "Q12: 前段收益归因（0185）")

has_text("docs/analysis/0219-theory-audit.md",
         ["至多 2 拍", "B=64", "谱半径"],
         "Q11/Q12: 死拍收敛、带顶 64、谱半径（0219）")

has_text("docs/analysis/delta-model.md",
         ["141.727", "+14.8%", "+22.4%", "+15.3%", "2.9"],
         "Q13/Q15: δ 曲面各点与 LOOCV 2.9pp（delta-model.md）")

has_text("docs/knowledge/timer-granularity.md",
         ["245.995", "243.958", "133.086", "133.9", "±11"],
         "Q15: G 模型锚点与 S5 前瞻预测 133.9±11（timer-granularity.md）")

has_text("zcode/scripts/_0248_out.md",
         ["0.100 us", "PASS", "0.000"],
         "Q13/Q15: 0248 漂移实测 PASS（_0248_out.md）")

has_text("zcode/scripts/_0249_out.md",
         ["违例数：0", "-1.11%", "2.3%", "70.77", "94.75", "95.92"],
         "Q11/Q15: 0249 可行性检验与锚点残差（_0249_out.md）")

has_text("docs/extracted/流量整形模块使用说明.md",
         ["没有在途包", "拥塞恢复"],
         "Q11: 突发令牌重置条件（模块使用说明）")

# ---- 2. 算术复推 ----
sizes = [10, 20, 40, 80, 160, 320]
check("Q12: 文件求和 10+20+40+80+160+320 = 630 MB", sum(sizes) == 630)

g1, g40, g60 = 0.157, 4.513, 36.342
check("Q11: 批量梯度 29×/231× 复推",
      abs(g40 / g1 - 28.7) < 0.5 and abs(g60 / g1 - 231.5) < 1.0,
      f"40/1={g40/g1:.1f}×, 60/1={g60/g1:.1f}×")

check("Q12: 0185 归因分解求和 24.49+24.49+40.16 = 89.14",
      abs(24.49 + 24.49 + 40.16 - 89.14) < 0.01)

cheb = 1 - 2.21**2 / (10 * 9)
check("Q14(v1 Q8 复用一致性): 切比雪夫 1−2.21²/(10·9) = 94.57%",
      abs(cheb - 0.9457) < 1e-3, f"{cheb*100:.2f}%")

check("Q12: 大段数据量占比 (80+160+320)/630 = 88.9%",
      abs((sum(sizes[3:]) / 630) - 0.8889) < 1e-3)

check("Q13: G 量化机理 9包/1000us → 2250 pkt/s（×4 慢化）",
      abs(9 / 0.004 - 2250) < 1e-9)

w41 = 41 * 1200 * 8 / 0.004 / 1e6
w40 = 40 * 1200 * 8 / 0.004 / 1e6
check("Q13/Q14: 线速 r=41→98.40、r=40→96.00 Mbps（全口径安全上界 40）",
      abs(w41 - 98.4) < 1e-9 and abs(w40 - 96.0) < 1e-9, f"{w41:.2f}/{w40:.2f}")

gmax = (1200 - 49) / 1200 * 100
gtyp = (1200 - 63) / 1200 * 100
check("Q13: 载荷率带 94.75%–95.92%，带宽 1.17pp ≤ 1.2",
      abs(gmax - 95.9167) < 1e-3 and abs(gtyp - 94.75) < 1e-9 and abs(gmax - gtyp - 1.1667) < 1e-3,
      f"{gtyp:.2f}–{gmax:.2f}")

# ---- 3. 段间边际不稳定性：现场从 results.jsonl 重算（Q12 的 144 vs −108 Mbps）----
sizes_mb = sizes
marginals = {}
for line in (ROOT / "runs" / "results.jsonl").read_text(encoding="utf-8", errors="replace").splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
    except json.JSONDecodeError:
        continue
    tag = d.get("tag", "")
    if re.fullmatch(r"test-hybrid-tb4-p100M-p96M-r\d+", tag) and d.get("valid") and not d.get("invalid_reason"):
        t = [d["downloads"][f"{i}.bin"] for i in range(1, 7)]
        m1 = (sizes_mb[1] - sizes_mb[0]) * 8 / (t[1] - t[0])
        marginals[tag] = m1
r1 = marginals.get("test-hybrid-tb4-p100M-p96M-r1")
r2 = marginals.get("test-hybrid-tb4-p100M-p96M-r2")
check("Q12: 段间边际不稳定性 r1/r2 重算（一正一负、|值|>50）",
      r1 is not None and r2 is not None and r1 > 50 and r2 < -50,
      f"r1 1→2 段边际 {r1:.1f} Mbps, r2 {r2:.1f} Mbps")

# ---- 汇总 ----
print()
if FAILS:
    print(f"校验失败 {len(FAILS)} 条：{'; '.join(FAILS)}")
    sys.exit(1)
print("全部核验通过：手册 Q11–Q15 的每个引用数字与源文件一致，算术复推无误。")
