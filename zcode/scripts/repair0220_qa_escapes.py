#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0220 repair tool: fix the escape-mangling planted by the v1 QA generator and
swap the mangled Q7 block for the corrected v2 answer.

The v1 generator built its markdown template inside a non-raw Python string, so
\\rho -> CR, \\tau -> TAB, \\approx -> BEL were already interpreted before writing.
This tool repairs those artifacts everywhere (Q1-Q6 included) and replaces the Q7
block in place. Idempotent: control-char repairs no-op once applied.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

QA = Path(__file__).resolve().parents[2] / "docs" / "analysis" / "0190-expert-defense-qa-database.md"

NEW_Q7 = """### 问题 7（专家提问：发包自相关函数的衰减速度）：
**专家问**：“在高并发网络环境下，如果发包具有强长程相关性（Long-range Dependence），会导致重尾排队。你们如何证明漏桶 pacing 消除了自相关性？”

**团队标准回答**（2026-11-07 v2 修订：以任务 0219 v2 已证明的死拍定理替换原指数衰减叙事）：
1. **一步死拍收敛（强于指数衰减）**：饱和工况下（$q_n \\ge y_n$，六个大文件发端恒有数据）令牌维映射为 $y_{n+1}=\\min(b,\\,y_n-y_n+r)=\\min(b,r)=r$（全部认证构型 $r\\le b$）。任意初值至多 2 拍（8ms）后发包速率**恒等于** $r$——任务 0219 T1b 在全部 5 个认证梯位 $(41,41)/(40,40)/(40,37)/(37,37)/(36,36)$ 数值验证通过；
2. **自相关精确为零**：稳态段发包速率过程为常数，其自相关函数在所有滞后 $\\tau\\ge 1$ 拍处**精确为 0**（不是衰减到 0.05，是恒等式）；不存在 Hurst $H>0.5$ 长程相关的载体；
3. **一般工况的有界修正**：AIMD 欠载拍令牌回灌至桶帽（幅值 $\\le b-r\\le 3$ 包，即任务 0085 的 gust-scissor），一拍内重新死拍回 $r$；速率过程始终有界、以 $r$ 为锚，无二频源 → 无拟周期（0219 T4 结构性论证），最大 Lyapunov 实测为负（无奇异吸引子）。

---

"""


def main() -> int:
    raw = QA.read_bytes().decode("utf-8")
    ctrl_before = sorted({hex(ord(c)) for c in raw if ord(c) < 32 and c != "\n"})
    print("control chars before:", ctrl_before)

    t = raw
    # escape-mangling repairs (TAB/CR/BEL planted where \text \tau \approx \rho \times belonged);
    # all control chars expressed as explicit escapes, never as literal bytes in this source
    t = t.replace("\text{", r"\text{")
    t = t.replace("\tau", r"\tau")
    t = t.replace("\rho", r"\rho")
    t = t.replace("\times", r"\times")
    t = t.replace("\x07pprox", r"\approx")
    t = t.replace("\x07lpha", r"\alpha")

    # replace the whole Q7 block (from its header up to the 问题 8 header) with the v2 answer
    pattern = re.compile(r"### 问题 7.*?(?=### 问题 8)", re.S)
    t2, n = pattern.subn(lambda _m: NEW_Q7, t)
    print("Q7 blocks replaced:", n)

    # normalize EOL to LF (v1's Windows-text-mode append left the file mixed CRLF/LF)
    t2 = t2.replace("\r\n", "\n")
    QA.write_text(t2, encoding="utf-8", newline="\n")

    back = QA.read_bytes().decode("utf-8")
    crlf = back.count("\r\n")
    lone_cr = back.count("\r") - crlf
    ctrl_after = sorted({hex(ord(c)) for c in back if ord(c) < 32 and c != "\n"})
    print("CRLF remaining:", crlf, "| lone CR:", lone_cr, "| control chars:", ctrl_after)
    print("rho/tau/approx counts:", back.count(r"\rho"), back.count(r"\tau"), back.count(r"\approx"))
    print("Q7 v2 present:", "一步死拍收敛" in back, "| old gamma 57.7 present:", "57.7" in back)
    ok = not ctrl_after and lone_cr == 0 and n == 1 and "一步死拍收敛" in back and "57.7" not in back
    print("REPAIR:", "OK" if ok else "NEEDS REVIEW")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
