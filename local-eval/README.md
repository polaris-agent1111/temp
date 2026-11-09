# local-eval · iDSN 题目一「六载穿柜」离线评测工具集

这个目录是 `~/polaris` 里**可独立运行、尽量不依赖云主机/WebSocket**的最小工具集。
目标不是把 3,240 个历史文件全搬过来，而是保留：

1. **能离线跑**的仿真/校验/分析脚本；
2. **官方原始文档**和关键机制结论；
3. **当前冠军配置**；
4. **官方二进制**（可选，见 `bin/README.md`）；
5. 一个在 Linux 上尝试官方本地评测的包装脚本。

## 30 秒自检

```bash
cd ~/polaris/local-eval

# 1) 校验器自测（不需要网络/root）
python3 tools/validate_pacer.py --selftest

# 2) 校验当前冠军配置树
python3 tools/validate_pacer.py question

# 3) 官方定时器粒度模型
python3 tools/timer_model.py table

# 4) 离线仿真（先跑 50 个种子，约几十秒）
python3 tools/offline_pacer_sim.py \
  --configs configs/champion-1108-shot-steady.json \
  --seeds 50
```

详细说明见仓库根目录的 [`../LOCAL_EVAL_GUIDE.md`](../LOCAL_EVAL_GUIDE.md)。

## 目录

| 路径 | 内容 |
|---|---|
| `tools/offline_pacer_sim.py` | **核心**：纯标准库的逐 tick 流体仿真，模拟 pacer + WebSearch 背景流 + 瓶颈队列 |
| `tools/timer_model.py` | 官方 4 ms 定时器粒度的定量模型（`table` / `equiv` / `fit` / `sweep-G`） |
| `tools/validate_pacer.py` | `question/1..6/pacer.txt` 格式/参数/编码校验器（含自测） |
| `tools/render_configs.py` | 把 6 目录配置 JSON 渲染成合法的 `question/` 树（UTF-8/LF/无末尾换行） |
| `tools/collect_results.py` | 汇总 `evals/*/result.json`，输出均值/标准差/分文件耗时 |
| `tools/analyze.py` | 历史 `runs/results.jsonl` 的按配置聚合（原 `harness/analyze.py`） |
| `tools/config_stats.py` | 更完整的历史统计（可选 scipy） |
| `tools/audit_plan.py` | 提交前样本数/方差/过拟合话术审计 |
| `tools/check_all_configs.py` | 批量体检 `runs/configs/**/pacer.txt` |
| `tools/monte_carlo_websearch.py` | WebSearch 背景流蒙特卡洛（需要 `numpy`，可选） |
| `configs/params_schema.json` | 五个模块的权威参数 schema |
| `configs/champion-1108-shot-steady.json` | 当前冠军配置 `40/40/40/37/36/36 @4000µs` |
| `question/1..6/pacer.txt` | 与冠军配置对应的可直接评测目录树 |
| `docs/official/` | 官方 4 份文档（规则 / WebSearch 模型 / 模块说明 / 实验手册） |
| `docs/background/` | 历史机制分析、技术报告、HANDOFF（历史快照，注意时效） |
| `bin/` | 官方二进制 + SHA256；**需要完整 containernet 环境才能真正跑** |
| `scripts/` | 校验、仿真、官方评测包装、结果汇总脚本 |

## 重要边界

- `offline_pacer_sim.py` 是**模型**，不是官方评测器。它适合理解机制、筛掉明显错误（1 ms 陷阱、burst 过大），但**对冠军阶梯不敏感**：100 seeds 下 champion `40/40/40/37/36/36` 与 uniform36 都在 ~133 s，而官方分别是 122.0 s 和 133.1 s。阶梯细排必须靠本地官方评测/官方提交。
- 官方本地评测器 `competition_question1` **不是单文件可移植程序**：它依赖 Linux x86_64、root、containernet、Docker、`/root/containernet`、`/home/TrafficGenerator`、`/home/http_server`，并且硬编码 `/home/openlab/Desktop/question`。详见指南第 4 节。
- 不要在队友正在评测的机器上并发启动官方评测；会互相干扰。
- `local_send_client` 会消耗**每天 5 次**的官方提交额度；本地仿真/本地评测不消耗额度。
