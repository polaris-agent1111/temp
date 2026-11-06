# 项目工作指南

本仓库用于 iDSN 挑战赛「六载穿柜」的 QUIC 流量整形实验。六次连续下载使用 `question/1..6` 中的配置，目标是缩短总下载时间。

## 开始前

- 先读 `README.md` 和 `CONTRIBUTING.md`。需要进展时查 `hourly/INDEX.md` 和 `STATUS.md`，注意记录时间；历史结论不一定代表当前状态。
- `PLAN.md` 和根目录 `STATUS.md` 由 Lead 维护。`zcode/` 是独立的任务通道，其任务和写入范围见 `zcode/README.md` 与 `zcode/STATUS.md`。
- 非 Lead 不要使用共享云主机执行实验或提交。`client/submit_vm.py`、`tools/submit_batch.py`、`tools/adaptive_submit.py`、`tools/night_submit.py` 和 `tools/smart_adaptive_night.py` 涉及提交或调度，先检查参数及副作用。
- 不提交或输出密码、令牌、GUID、会话文件和个人信息。遵守 `.gitignore`，提交前检查 `git status`。

## 合规红线（官方明令，违反会取消成绩或封号）

官方「题目测评方式」把以下行为列为取消成绩项，仓库内任何脚本、实验或提交都不得触碰：

1. **不得修改评测环境。** 拓扑、地址、带宽、时延、主机数量、背景流端点均由平台固定；不得关闭背景流量、更换流长分布或修改目标速率。只允许提交 `pacer.txt` 参数。
2. **不得硬编码答案。** 不得把官方成绩、随机种子、标准答案配置写死进提交内容或脚本。历史成绩只能作为分析数据，不能作为提交的一部分。
3. **不得探测或攻击测评系统。** 不得访问远程调度器、种子、他人配置，不得构造异常请求、扫描端口、注入代码或绕过格式检查。阅读官方提供的本地评测器和文档属于分析；对远程系统的探测属于红线。
4. **不得利用评测漏洞。** 已知的 CRLF/末尾换行「~80s 假成功」只用于识别和拒绝，不得用于提分。发现新漏洞应记录并回避，不得利用。
5. **不得多账号、不得泄露 GUID。** GUID 只从 `client/secrets.json` 或环境变量读取，不入库、不输出、不分享。
6. **每日提交不得超过 5 次。** 超限可能导致账号封禁；失败的提交只要连上服务端并识别到团队也会计数。

## 测量口径与反过拟合纪律（必读）

官方测评流程第 ⑦ 步是 **「重复多次取平均，更新排行榜」**；公平性条款还明确 **「排行榜 top 提交将统一复测，防止针对特定随机种子的过拟合」**。因此：

- **本地单场最小值不是官方预期。** 例：`test-hybrid-tb4-p100M-p96M` 的 n=3 数据为 min 116.542s、mean 137.430s、std 18.42s；不能用 116.5s 去对比官方 133.086s。
- **选型按均值/中位数，不按最小值。** 候选至少 n≥3；最终主推至少 n≥8–10。同时报告标准差、标准误和 95% 置信区间。
- **要求邻域稳定。** 对关键参数做 ±1 包或 ±1 单位扰动，性能不应显著变差；只投「平台点」，不投「尖点」。
- **禁止 min-of-N / 极值红利。** 重复实验是为了估计方差，不是为了抽一个低分；这与官方 top 复测直接冲突。
- **本地与官方分开陈述。** 报告里同时写「本地单场最好」和「本地均值」，不得用前者替代后者。
- **统计前先清洗。** 本地结果必须过滤 `valid=false` 和 `load-*` 污染样本，再计算均值、方差和排名。
- **提交前过门禁。** 运行 `python tools/audit_plan.py --plan <plan>`；出现 `NO_LOCAL_SAMPLE`、`LOW_N`、`HIGH_CV`、`MIN_FAR_BELOW_MEAN` 或 `OVERFITTING_LANGUAGE` 时先修正，不要直接投。

详细数据与选型门槛见 `docs/analysis/overfitting-and-selection.md`。

## 提交与额度纪律

- 每天最多 5 发，串行执行，不并发。提交前查 `runs/submissions.jsonl` 的当日计数；不要依赖服务端的「已达到最大提交次数」兜底。
- 自动调度必须幂等：同一天只执行一次。`tools/smart_adaptive_night.py` 使用 `runs/adaptive_night_state.json` 和 `runs/.adaptive_night.lock`；不要手动删除锁文件后直接重跑，先核对当日提交记录。
- `tools/smart_adaptive_night.py` 默认 `--on-timeout abort`：超时未拿到 2 条新出分时不自动投 Wave 2。若确实要超时自动执行，必须显式传入 `--on-timeout bypass` 或 `--on-timeout fallback`，并先确认当日剩余额度。
- `tools/night_submit.py` 在检测到本 plan 已有今日提交时会拒绝自动重试，避免部分成功后重复提交。遇到该提示先人工核对，不要强行绕过。
- 本地 `./format_check_client` 免费；`./local_send_client` 一旦连上远程服务端就计数，即使最终提交失败。
- 格式测试不得 clobber `question/`。`tools/test_format_limits.py` 会先备份、结束后恢复；不要在共享云主机上与他人同时运行。
- 出分延迟通常 45–60 分钟。同配置 60 分钟内不重复投；重复投必须有明确假设（校准/方差估计），不能只为抽低分。

## 定位代码和数据

- `configs/params_schema.json` 是模块与参数约束的依据。`tools/validate_pacer.py` 校验配置。
- `harness/run_experiment.py` 生成配置并编排云端评测。`harness/sweep.py` 批量运行，`harness/analyze.py` 汇总 `runs/results.jsonl`。
- `client/api.py` 访问榜单，`client/trit.py` 访问竞赛平台，`client/vmssh.py` 提供 WebSSH。`tools/` 还包含榜单、统计和提交工具。
- `tools/summarize_hybrid_stats.py` 生成 `docs/analysis/hybrid-statistical-summary.md`；`tools/audit_plan.py` 是提交前门禁。
- `docs/extracted/` 包含官方资料文本，`docs/analysis/` 和 `docs/knowledge/` 包含分析，`report/` 包含报告与复核材料。`runs/` 同时包含被忽略的本地数据和已跟踪的提交计划，具体以 `.gitignore` 为准。

## 配置和验证

- 配置树必须有 `1` 至 `6` 六个目录。目录可不含 `pacer.txt`，此时沿用上一次配置；首次下载使用默认配置。
- `pacer.txt` 使用无 BOM 的 UTF-8 和 LF，恰好三行，末尾没有换行。`[timestamp:N]` 的 N 必须等于目录名。参考 `harness/run_experiment.py` 的 `render_pacer` 和 `build_tree`。
- 离线自测运行 `python tools/validate_pacer.py --selftest`。校验配置树运行 `python tools/validate_pacer.py <配置目录>`。
- 离线生成示例运行 `python harness/run_experiment.py --tag <新标签> --mode leak_bucket --params "leak_rate=9,bucket_cap=30,leak_interval_us=1000" --dry-run`。脚本会删除并重建该标签对应的 `runs/configs/` 目录，先确认标签未被使用。
- `run_experiment.py` 即使在 `--dry-run` 时也需要导入 `websocket-client`。依赖和安装说明见 `README.md`。
- 修改提交/统计工具后运行 `python -m unittest discover -s tests -v`。
- `.sh` 和其他文本的换行规则见 `.gitattributes`。不要仅凭单次结果判断配置优劣，并区分本地评测与官方成绩。
