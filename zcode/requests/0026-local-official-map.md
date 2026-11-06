status: open
priority: 2
assignee: zcode
created: 2026-11-05 22:45

# 0026 — 本地→官方映射拟合（含不确定性）

## 为什么

我们所有策略都建立在「官方 ≈ 本地 × (1+δ)」上，但 δ 在 +2.1% ~ +14.8% 之间跳。如果不能量化 δ 的分布，就没法判断「本地差 1 s」值不值得投。

## 任务

产出 `tools/local_official_map.py` + `docs/analysis/local-official-map.md`：

1. **数据对齐**：官方点来自 `/api/leaderboard` 的 attempts（team=赛博coder）+ 我们的 `runs/submissions.jsonl` 配对；本地均值来自 `runs/results.jsonl`（同配置 6 个目录全部相同、valid=true 的样本）。11/06 自适应模式的 5 个新点要自动纳入。
2. **拟合三档模型**（都给出残差与留一交叉验证误差）：
   - M0：官方 = 本地 + c（常数平移）
   - M1：官方 = a × 本地 + b（线性）
   - M2：官方 = a × 本地 + b + c × rate（带 rate 交互）
3. **δ 的分解**：δ 是否随 rate / interval / cap / 提交时段（小时）变化？每个维度给分组表 + 极差。
4. **预测器**：给一个 CLI `python tools/local_official_map.py --predict 24,60,4000`，输出该配置的官方预测区间（用残差分布给 80% 区间）。
5. **结论**：我们现在「本地降 1 s」对官方的期望收益是多少？是否还值得继续本地调参？
6. **一句话结论**。

## 输入

`runs/results.jsonl`、`runs/submissions.jsonl`、`runs/official_results.jsonl`、`/api/leaderboard`（只读）、`report/官方探测分析.md`。

## 禁止

不提交、不登录、不碰云主机、不改 `runs/`；样本量小必须显式标注置信度，不许假装精确。

## 交付

`tools/local_official_map.py` + `docs/analysis/local-official-map.md` + `zcode/reports/0026-map.md`。
