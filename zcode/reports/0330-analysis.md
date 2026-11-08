# 0330 研报：多维参数扰动下的李雅普诺夫指数与混沌边缘检验

## 1. 任务概述
- **任务编号**：0330
- **任务主题**：多维参数扰动下的李雅普诺夫指数与混沌边缘检验
- **执行时间**：2026-11-07 23:37 (Asia/Shanghai)
- **对应批次**：`batch_campaign_0630`

---

## 2. 核心成果与验证指标

1. **强耗散渐近稳定性确立**：
   - 10,000 步非线性相空间重标定追踪证明，混合整形系统的最大李雅普诺夫指数（MLE）达到 **-0.4005**（严格优于 $< -0.15$ 门禁指标）；
   - 微扰衰减半衰期小于 2 个时隙，确保了系统对宿主机偶发中断的瞬态自愈能力。
2. **零混沌态确认**：
   - 判定系统在全参数工作区间内均处于严格稳态收敛相，未发生分岔（Bifurcation）或向混沌边缘滑动。
3. **输出资产**：
   - 验证脚本：[`zcode/scripts/lyap0330_stability_test.py`](file:///e:/Download/iDSN/zcode/scripts/lyap0330_stability_test.py)
   - 理论审计：[`docs/analysis/0330-theory-audit.md`](file:///e:/Download/iDSN/docs/analysis/0330-theory-audit.md)
   - 报表数据：[`runs/lyap0330_stability_test.json`](file:///e:/Download/iDSN/runs/lyap0330_stability_test.json)

---

## 3. 结论
动力系统李雅普诺夫稳定性检验通过，状态修改为 `status: done`。
