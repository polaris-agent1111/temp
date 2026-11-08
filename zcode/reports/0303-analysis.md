# 0303 报告：Shot 5 终局压轴发全油门冲击策略裁决

- 完成时间：2026-11-07 22:17
- 执行者：zcode
- 结论：**总裁决 PASS**。对 `tools/sequential_adaptive_1108.py` 三层验证：AST 循环有界性
  （2 个 while 均有界出口，0 无界死循环）、真实模块 `decide_next_shot` 全决策空间枚举
  （11,110 输入，0 非法裁决，两遍哈希一致=确定性，覆盖全部 4 构型 × 12 分支）、
  封闭环沙盒仿真 500 轮含全超时退化注入（全部恰在第 5 发终止）。墙钟上界 ≈5.6h，有界。

## 具体动作

- 只读审读 `tools/sequential_adaptive_1108.py`（476 行）全文，定位 `decide_next_shot`
  五段门限、`wait_until`/`poll_for_new_score` 两个 while、主循环 `for k in range(...)`。
- 编写并运行 `python -I zcode/scripts/verify0303_shot5_verdict.py`：
  - A. AST 分析全部 8 个循环的有界性 + `decide_next_shot` 纯度（无 IO/日志）；
  - B. importlib 导入真实模块（模块级无副作用），枚举 next_idx=2..5 × 全部
    status×score 历史前缀共 11,110 输入，验证全函数性与确定性；
  - C. 沙盒复刻闭环 500 轮（seed=20261108，含全超时退化注入）验证恒 ≤5 发终止；
  - D. 墙钟上界核算（65min×5 + 3min×4 ≈ 337min）。
- 全程未调用 `run_sequential_pipeline`/`execute_single_shot`（dry-run 也无条件写
  state，见审计 F4），未触碰 `runs/`。
- 形成审计写入 `docs/analysis/0303-theory-audit.md`（含 6 条发现 F1–F6）。

## 产出文件

- `zcode/scripts/verify0303_shot5_verdict.py`（可复跑验证脚本）
- `zcode/scripts/verify0303_output.json`（结构化验证结果，verdict=PASS）
- `docs/analysis/0303-theory-audit.md`
- 本报告 `zcode/reports/0303-analysis.md`

## 未完成/风险

- 实弹期跑 `--dry-run` 会用 mock 覆盖当日真实 state（F4，最重要操作纪律）；
- 轮询间隔 45s 可能漏 10s 级榜首窗口（F1，建议出分窗口 ≤10s）；
- `LOCK_FILE` 定义但从未 acquire，双实例无互斥（F3）；state 写盘非原子（F5）；
- Shot 3 改进判定在超时穿插场景基线漂移（F2，语义怪癖不崩溃）。

## 给 Lead 的建议

- 11/08 实弹开始后严禁再跑任何 `--dry-run`（会污染当日 state）；如需演练先备份 state；
- 出分窗口期把轮询压到 ≤10s（0296 + 本次 F1 一致结论）；
- 决策输入必须来自真实出分（0302 的 mock 三重指纹隔离是前置闸门）。
