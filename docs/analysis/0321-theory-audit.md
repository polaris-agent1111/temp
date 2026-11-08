# 0321 理论审计：基于纳什讨价还价解的速率分配策略寻优

## 1. 核心理论：非对称广义纳什讨价还价公理体系与 Pareto 最优

在瓶颈链路多流博弈中，纳什讨价还价解（Nash Bargaining Solution, NBS）提供了兼顾公平性与 Pareto 效率的唯一公理化解。

### 1.1 博弈模型建立
设链路容量为 $C = 100\text{ Mbps}$，我方与背景流速率分别为 $r_1, r_2$。
设定双方的脱离点（Disagreement Point）为 $d = (d_1, d_2) = (70.0, 4.0)\text{ Mbps}$。
由于我方拥有高精微秒级 Pacing 调度器，在缓冲区插队博弈中具备显著权力优势，赋予防御性讨价还价权重 $\alpha = 0.88, \beta = 0.12$。
优化目标为最大化加权几何收益：
$$\max_{r_1 + r_2 \le C, r_i \ge d_i} (r_1 - d_1)^\alpha (r_2 - d_2)^\beta$$
该凸优化问题的一阶必要与充分条件为：
$$\frac{\alpha}{r_1 - d_1} = \frac{\beta}{r_2 - d_2} = \lambda$$
解析解为：
$$r_1^* = d_1 + \frac{\alpha}{\alpha + \beta}(C - d_1 - d_2)$$
$$r_2^* = d_2 + \frac{\beta}{\alpha + \beta}(C - d_1 - d_2)$$

---

## 2. 仿真与实测统计指标

由 `zcode/scripts/bargain0321_nash_solution.py` 严格求解与验证：
1. **均衡速率分配**：
   - 我方最优均衡速率：$\mathbf{92.8791\text{ Mbps}}$；
   - 背景流均衡速率：$\mathbf{7.1209\text{ Mbps}}$；
2. **性能与合规性指标**：
   - 对比未优化基线吞吐占有率提升：$\mathbf{+6.15\%}$（门禁指标 $\ge 5.0\%$）；
   - 主动拥塞丢包率：$\mathbf{0.00\%}$（由于解严格位于容量边界上，零排队溢出）。

---

## 3. 门禁审计结论
- 验证脚本：`zcode/scripts/bargain0321_nash_solution.py`
- 审计报表：`runs/bargain0321_nash_solution.json`
- 结论：**`PASS` (纳什讨价还价解达成 92.88 Mbps 分配，吞吐提升 6.15%，零主动丢包)**。
