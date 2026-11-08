# -*- coding: utf-8 -*-
"""
[已作废 · SUPERSEDED] 2026-11-07

本脚本是 0235 任务在早前一次中断会话中遗留的草稿, 其参数与结论**无任何数据来源**:
  - 虚构我方构型均值 (Crown Fusion 116.5s / Defense Fortress 119.1s / shot1 117.2s 等),
    与我方真实 champ 家族本地均值 133.86s、真实官方出分 124.3683s 严重矛盾;
  - 虚构对手模型 Catnet N(119.5,1.5^2)+68% blowout、光明未来 N(118.2,1.6^2)、
    其他队 N(121.0,2.0^2), 无任何榜单/出分依据;
  - 由此得出的 P(top1)=70.66% / E[best]=115.458s 不可信, 严禁引用。

正式版(基于真实榜单 117.0257/119.8293、真实出分史、best-of-n 能力反推):
  - 脚本: zcode/scripts/game0235_preempt_nash_sim.py
  - 输出: zcode/scripts/game0235_sim_output.txt
  - 分析: docs/analysis/0235-theory-audit.md
  - 真实结论: 时序支配率(口径A)=100%; P(top1)(口径B)≈11%(固定)/≈18%(自适应),
    远达不到 95%, 夺冠瓶颈在能力而非时序。

本文件按「禁止删除/移动文件」红线保留为作废声明, 请 Lead 择机清理。
"""
print("SUPERSEDED: see zcode/scripts/game0235_preempt_nash_sim.py (0235 正式版)")
