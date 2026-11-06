# 复核自检清单

> 逐条打勾；交付/复测/答辩前各过一遍。工具：`python tools/validate_pacer.py <question目录>`（8 项自动检查）+ 人工项。

## A. 配置文件格式（自动，validate_pacer.py 覆盖）

- [ ] **A1** question/ 下恰有子目录 `1`…`6`，无多无少、无前导零、根级无多余文件。
- [ ] **A2** 每个子目录至多一个普通文件 `pacer.txt`；无子目录、无其它文件。
- [ ] **A3** **换行**：纯 LF、无 CRLF、无孤立 CR、**无末尾换行**、无 BOM（UTF-8）。
      ⚠ 已知坑：CRLF → 服务端解析失败 → 本地/官方出现 ~80 s「假成功」（特征：total≈80、多个文件恰 10.00 s、valid=false）。历史坑配置 `runs/configs/ctl-tokenbucket-default` 可作负样本，校验器实测报 18 处错误。
- [ ] **A4** 恰好 3 行、顺序 `[timestamp:N]` / `pacer_mode:<模块>` / `pacer_config:...`，行首尾无空白。
- [ ] **A5** `timestamp=N` **等于所在目录名**（目录 2 必须是 `[timestamp:2]`）。
- [ ] **A6** `pacer_mode` ∈ {token_bucket, coarse_grained_rate_based, precise_rate_based, origin, leak_bucket}。
- [ ] **A7** 参数名属于该模块、正整数/范围合法、**`burst ≥ tokens`**、**`bucket_cap ≥ leak_rate`**、无重复参数、无未知参数名。
- [ ] **A8** 空 `pacer_config:`（=模块默认）与空目录（=沿用上一份）为合法用法，确认是**有意为之**而非漏写。

## B. 提交流程

- [ ] **B1** 本地 `python tools/validate_pacer.py <question>` exit 0。
- [ ] **B2** 云主机 `./format_check_client` 输出「检查结果: 通过 / 不符合规定的信息: 无」。
- [ ] **B3** `./local_send_client` 前确认当日剩余次数（5 次/天，超限可能封号）；提交后记录 `日期时间.tar.gz` 快照。
- [ ] **B4** 出分延迟 ~45–60 min：同一配置 1 小时内不重复投；提交时间尽量错开 13–14 点高峰（观测见 `docs/analysis/leaderboard-timing.md`）。

## C. 结果可复现

- [ ] **C1** 本地评测 `valid=true`（六文件全部成功；非 80 s 假成功形态）。
- [ ] **C2** `runs/results.jsonl` 已落盘该条记录（tag/config/分文件耗时/valid 齐全）。
- [ ] **C3** `python tools/config_stats.py` 可重跑，清洗计数与报告一致（总/无效/读不通）。
- [ ] **C4** 报告/答辩中每个数字可回溯到 `runs/results.jsonl`、`report/实验结果-统计.md` 或 `intel/raw/leaderboard_*.json`；无数据处标「待补」。
- [ ] **C5** `best-configs/` 复制件与 `runs/configs/` 源 sha256 一致（本轮 18 文件已核对全 OK）。

## D. 合规与安全

- [ ] **D1** 材料中**无真实凭据**：GUID=`<团队GUID>`、无密码/token/个人信息。
- [ ] **D2** 未硬编码答案、未探测评测系统、未多账号（赛规红线）。
- [ ] **D3** 引用官方成绩处注明快照时间与来源文件；未定论的归因（官方 2× 差异）只陈述事实、标「分析中」。
- [ ] **D4** 候选配置的「本地成绩」与「官方状态」分开陈述（leak 族本地最优但官方不推荐——见 best-configs/README.md）。

## E. 答辩/复核材料

- [ ] **E1** `report/复核材料/` 五件套齐全（README / best-configs / reproduce / methodology / checklist）+ `review-manifest.json`。
- [ ] **E2** `report/技术报告-v2.md` 数字与统计报告一致；图表 PNG 可打开、中文无乱码。
- [ ] **E3** 队友（如参与）按 reproduce.md 独立复跑成功一次。

## F. 跨环境鲁棒（v2 新增，0017）

- [ ] **F1** **所有 `leak_bucket` 配置的 `leak_interval_us ≥ 4000`**（1 ms 间隔在官方会被定时器粒度腰斩：本地 124 s → 官方 244–246 s；见 reproduce.md §1.5、`docs/knowledge/timer-granularity.md`）。历史 1 ms 样本（leak9/leak8）只作差异证据，不作复测推荐。
- [ ] **F2** 若用 token_bucket / coarse_grained_rate_based / precise_rate_based：**确认 `enable_n_in_flight` 未被显式置 0**（默认 1；该旁路是官方环境下免疫定时器粒度的关键机制之一），且标称速率 ÷4 后仍高于 ~41 Mbps 实际份额。
