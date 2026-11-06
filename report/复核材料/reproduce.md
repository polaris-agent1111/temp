# 逐步复现指南

> 前置：竞赛云主机（4 核及以上；单次评测约 3–4 分钟）。以下命令在云主机桌面 `/home/openlab/Desktop/` 下执行，程序名与路径不要改动。
> 本指南不含任何真实凭据；提交命令中 GUID 一律为 `<团队GUID>` 占位。

## 0. 环境与材料

- 复现包/规范：平台提供的《流量整形模块使用说明》《实验详细手册》（本工作区 `docs/extracted/` 有 markdown 提取版）。
- 待测配置：本包 `best-configs/<候选名>/1..6/pacer.txt`（或自行生成，生成后必过第 1 步）。

## 1. 配置就位

```
question/
├── 1/pacer.txt   ← [timestamp:1] 必须等于目录名
├── 2/pacer.txt
├── 3/            ← 目录必须都在；不需要换配置的目录可不放文件（沿用上一份）
├── 4/
├── 5/
└── 6/
```

三行格式（UTF-8、**LF 换行、无末尾换行**、行首尾无空白）：

```
[timestamp:1]
pacer_mode:leak_bucket
pacer_config:leak_rate=36,bucket_cap=40,leak_interval_us=4000
```

## 1.5 ⚠ 必须用 4 ms 及以上间隔（v2 新增，复核必读）

- **现象**：同一配置 `leak_bucket 9/30/1000µs`，本地 7 次实测 **123.81±7.19 s**，官方两次提交却是 **245.995 / 243.958 s（恰好 ×2）**；把 `leak_interval_us` 抬到 **4000** 后（`36/40/4000`），官方回到 **133.086 s**，与本地 132.45±6.73 一致（1:1）。
- **原因（反推值，待验证）**：官方评测环境的定时器实际粒度 ≈ **4 ms**——`leak_bucket` 是五个模块中唯一没有 `enable_n_in_flight` 旁路的，速率完全绑定漏出定时器；9 包/1 ms 在 4 ms 粒度下退化为 9 包/4 ms = 21.6 Mbps → 630 MB ≈ 233 s + 残差 ≈ 244 s，与实测吻合。完整证据链与定量模型见 **`docs/knowledge/timer-granularity.md`**（工具：`python tools/timer_model.py fit`）。
- **规避方法（复核配置选择规则）**：
  1. 用 `leak_bucket` 时 **`leak_interval_us ≥ 4000`**（本包 `leak-36-40-4000`、`leak-24-50-4000` 均满足）；
  2. 或改用带 `enable_n_in_flight` 旁路的模块（token_bucket / coarse / precise；origin 内建机制3），且标称速率留足余量（÷4 后仍 >41 Mbps 份额）；
  3. **禁止**用 1 ms 漏桶（`leak9-rate9`/`leak8-rate8`）做官方复测——本地会给出误导性的好成绩。

本地预检（可选但推荐，工作区执行，秒级）：

```bash
python tools/validate_pacer.py <question目录>     # exit 0 = 通过；--json 输出机器可读结果
```

## 2. 格式检查（官方）

```bash
cd /home/openlab/Desktop
./format_check_client                 # 终端列出全部不符合项；通过后才可评测/提交
./format_check_client ./check.log     # 可选：同时写日志
```

## 3. 本地评测

```bash
cd /home/openlab/Desktop
sudo ./competition_question1 \
  --output-dir ./results \
  --result-json ./results/evaluation_results.json \
  --format-log-dir ./results/logs
```

- 程序自动读取 `question/` 依次仿真 6 次下载（配置写入时间不计入耗时）。
- 单次约 3–4 分钟；**六个文件必须全部下载成功**，否则该次无成绩（`valid=false`）。

## 4. 结果文件含义

| 文件 | 含义 |
|---|---|
| `./results/*.log` | 评测过程日志 |
| `./results/*.txt` | 结果文本：6 个文件各自耗时 + 总时间 |
| `./results/evaluation_results.json` | 汇总 JSON（机器可读；`runs/results.jsonl` 每条记录即由它落盘） |
| `./results/logs/` | 格式检查日志 |

**有效性判读**：总时间 ≈ 80 s 且多个文件耗时恰为 10.00 s → CRLF 假成功（服务端解析失败），检查换行符后重跑（`checklist.md` 条目 3）。

## 5. 统计复跑（本工作区，E:\Download\iDSN）

```bash
python tools/config_stats.py
# 输出 report/实验结果-统计.md 第1–4节：
#   清洗计数(总/无效/读不通) → 配置族分组表 → 分文件位置表 → Welch t 显著性
```

- 数据源 `runs/results.jsonl`（只追加，不修改）；新增评测后重跑即更新。
- 图表复现见 `report/技术报告-v1.md` 附录 A（数据源相同则图相同）。

## 6.（可选）提交

```bash
cd /home/openlab/Desktop
./local_send_client --token <团队GUID>   # 16 位 GUID 见团队后台，勿写入任何文件
```

- 发送前自动再跑一次格式检查；**无论成败，连上服务端即消耗当日提交次数（5 次/天）**，故第 2 步必须先过。
- 每次成功提交桌面留下 `日期时间.log` 与 `日期时间.tar.gz`（该次快照，建议留存）。

## 7. 预期结果（对照表）

| 配置 | 本地预期 (s) | 备注 |
|---|---|---|
| 平台默认（question 不放任何 pacer.txt） | 170.0±2.3 | 基线 n=2 |
| `best-configs/leak-36-40-4000` | 132.5±6.7 | n=3；**官方 133.086 实测锚点** |
| `best-configs/leak-24-50-4000` | 126.9±6.2 | n=11，min 119.6；官方待投 |
| `best-configs/tb-100-200-20` | 136.2±7.6 | n=2；官方 140.927（1:1 对照） |
| `best-configs/leak9-rate9`（历史） | 123.8±7.2 | ⚠ 1 ms 陷阱：**官方 244–246**，仅作差异证据 |

跨环境提示：官方评测与本地的系统性差异已定位为**定时器粒度 ≈4 ms（反推）**——安全配置（interval≥4000 / 有旁路）官方≈本地×(1.03~1.15)，1 ms 漏桶官方≈×2；详见 §1.5 与 `docs/knowledge/timer-granularity.md`。
