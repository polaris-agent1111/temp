status: done
priority: 1
assignee: zcode
created: 2026-11-06 19:20

# 0042 — 官方 WebSearch 流长分布重尾碰撞高阶蒙特卡洛仿真与 5 发冲榜胜率量化

## 背景
根据官方赛题附件《背景流量模型说明》（`docs/official_markdown/02_websearch_model.md`），背景流量采用网页搜索流长分布，流长在 0B 至 30MB 之间按照 11 节点累积概率分布（CDF）进行线性插值，期望流长 1.7 MB，目标速率 100 Mbps。
实测中发现，6.bin（320 MB，传输耗时约 58s~77s）和 5.bin（160 MB，耗时约 27s~35s）的耗时波动完全取决于是否在传输窗口内撞击到了数 MB 乃至 30 MB 的长尾重流。明日 11/07 团队将使用 5 发额度逐发冲榜，必须精确量化：在 5 发提交中，至少有 1 发在 5.bin 和 6.bin 全流程避开 30 MB 重尾巨流的数理概率是多少？

## 目标
构建严密的高性能蒙特卡洛仿真模拟器（$N \ge 100,000$ 轮次），模拟官方背景流生成引擎，精确量化各文件传输时间窗口内的碰撞概率密度函数（PDF）、累积分布函数（CDF）以及 5 发提交下的极值分布（min-of-N distribution），输出具有深厚理论说服力的《WebSearch 背景流长尾碰撞蒙特卡洛仿真与冲榜胜率精算报告》。

## 允许写的路径
- `zcode/reports/0042-monte-carlo-websearch.md`
- `docs/analysis/monte-carlo-collision-simulation.md`
- `zcode/scripts/simulate_websearch.py`
- `zcode/scripts/` 目录下的其他辅助分析脚本

## 具体动作
1. **严格复刻官方流量分布数学模型**：
   - 参考 `docs/official_markdown/02_websearch_model.md` 的累积分布节点：
     - (0, 0), (10000, 0.15), (20000, 0.20), (30000, 0.30), (50000, 0.40), (80000, 0.53), (200000, 0.60), (1000000, 0.70), (2000000, 0.80), (5000000, 0.90), (10000000, 0.97), (30000000, 1.00)；
   - 编写高保真逆变换采样算法（Inverse Transform Sampling with linear interpolation）；
   - 验证采样样本均值是否严格贴合期望值 1.7 MB。
2. **构建时序流到达与排队冲突模型**：
   - 依据目标速率 100 Mbps（12.5 MB/s），流到达过程采用非齐次/复合泊松流到达模型（Compound Poisson Process）；
   - 模拟各文件的实测典型下载时间窗口：
     - $T_1 = 2.0\text{s}$, $T_2 = 2.8\text{s}$, $T_3 = 5.8\text{s}$, $T_4 = 13.0\text{s}$, $T_5 = 28.0\text{s}$, $T_6 = 60.0\text{s}$；
   - 统计在各时间窗口内：
     - 遭遇 $\ge 1\text{MB}$ 流的期望条数与概率；
     - 遭遇 $\ge 10\text{MB}$ 流的期望条数与概率；
     - 遭遇极端 30MB 巨流的命中概率 $P(\text{Hit 30M})$；
3. **5 发提交下的极值胜率精算（Extreme Value Simulation）**：
   - 模拟独立重复 5 次评测实验（相当于每日 5 次提交）；
   - 计算 5 发中：
     - 至少 1 发未撞击 30MB 巨流的概率 $P(\ge 1 \text{ clean run})$；
     - 至少 2 发未撞击 30MB 巨流的概率；
     - 结合我方冠军构型净传输时间（$T_{\text{clean}} \approx 111.5\text{s}$），预测 5 发中触达 $\le 116.5\text{s}$ 的理论置信度。
4. **生成报告与交付**：
   - 编写分析报告至 `docs/analysis/monte-carlo-collision-simulation.md`；
   - 编写 `zcode/reports/0042-monte-carlo-websearch.md` 并标记本任务为 `status: done`。

## 禁止
- 不登录平台、不提交榜单、不修改历史结果文件；
- 不操作云主机；
- 不修改工作区未经授权的系统核心代码。

## 交付
- `zcode/scripts/simulate_websearch.py`（完整可执行蒙特卡洛模拟器）
- `docs/analysis/monte-carlo-collision-simulation.md`（完整仿真数据分析与图表报告）
- `zcode/reports/0042-monte-carlo-websearch.md`（标准格式交付报告）
- 完成后把本文件头部 `status: done` 改为 `status: done`
