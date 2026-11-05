# iDSN 挑战赛 · 赛博coder 工作区

围绕 **iDSN（智能领域定制网络）挑战赛 题目一「六载穿柜」** 的工程化工作区：
在云主机上复现官方评测、用脚本批量搜索 QUIC 流量整形参数配置、按提交纪律上分并盯榜。

> 项目计划见 [PLAN.md](PLAN.md)，最新进展/榜单/评分异常排查见 [STATUS.md](STATUS.md)，
> 每小时快照见 [hourly/INDEX.md](hourly/INDEX.md)。
> 队友协作区（加入流程 / 任务认领 / 每日同步）见 [Discussions #1](https://github.com/YunHai121/idsn-challenge/discussions/1)。

---

## 1. 赛事速览

| 项 | 内容 |
|---|---|
| 任务 | 基于主办方 QUIC 协议库的**可配置流量整形参数**，为「多文件连续下载」场景生成配置，使总传输时间最短 |
| 题目形态 | `question/1..6/pacer.txt`，每个目录控制第 N 次下载生效的模块与参数 |
| 可选模块 | `token_bucket` / `coarse_grained_rate_based` / `precise_rate_based` / `origin` / `leak_bucket`（参数规格见 [configs/params_schema.json](configs/params_schema.json)） |
| 场景规模 | 6 个文件 10/20/40/80/160/320 MB，共 **630 MB**；瓶颈链路 100 Mbps（≈12.5 MB/s），理论下界约 **50.4 s** |
| 评分 | 官方统一环境对每次提交**重复评测 3 次取平均**，按总传输时间升序排名；榜单每 30 分钟刷新 |
| 额度 | **每队每天 5 次提交**，脚本内置本地硬上限；榜上取历史最优 |
| 截止 | 2026-11-16 23:59:59 榜冻结 → 11/18 前复核 → 11/20–22 厦门 CCF ChinaNet 颁奖 |

## 2. 目录结构

| 路径 | 用途 |
|---|---|
| `PLAN.md` / `STATUS.md` | 作战计划 / 最新进展（**只由 Lead 维护**） |
| `hourly/` | 每小时工作快照，`INDEX.md` 始终是最新一版 |
| `client/` | 榜单站 API 客户端（`api.py`）、竞赛平台客户端（`trit.py`）、云主机 WebSSH 客户端（`vmssh.py`）、官方提交（`submit_vm.py`） |
| `harness/` | 评测编排：`run_experiment.py`（单次）、`sweep.py`（队列批量）、`analyze.py`（统计）、`upload_config.py`、`make_report_data.py`、`import_vm_result.py` |
| `tools/` | 本地校验器 `validate_pacer.py`、盯榜 `watch_board.py`、统计 `config_stats.py`、云主机负载 `vm_load.py` |
| `configs/params_schema.json` | 五个模块的参数名/类型/默认值/约束（唯一权威 schema） |
| `intel/` | 赛情材料、公众号原文、榜单 JSON 快照与榜单时序 CSV |
| `docs/` | 官方下载资料（`extracted/` 为 docx 抽取出的 Markdown，可直接检索；压缩包/大文件不入库） |
| `report/` | 技术报告、复现说明、实验结果数据表与图表 |
| `runs/` | **本机实验记录，不入库**：`results.jsonl`、`submissions.jsonl`、`configs/`、`evals/`、`leaderboard/` 等 |
| `zcode/` | 与 zcode 的异步任务通道（协议见 `zcode/README.md`） |
| `scripts/` | 云主机侧辅助脚本（`.sh`，**必须保持 LF**） |
| `env/` | 预留给 WSL 复现环境；当前流程不依赖 WSL（git 不跟踪空目录） |

## 3. 环境要求

- **Windows 10/11 + PowerShell**（本机验证：PowerShell 7.6.6、Git 2.53.0、Python 3.14.3）
- **Python 3.14.x**（本机 3.14.3；代码同时使用 `from __future__ import annotations`）
- Python 依赖：
  - 必需：`requests`、`websocket-client`（WebSSH 通道）
  - 可选：`scipy`（`tools/config_stats.py` 的 Welch t 检验，缺失时自动退化）、`python-docx`（`scripts/extract_docs.py`）、`playwright`（`scripts/trit_browser.py`、`scripts/trit_topo_meta.py`）
- **云主机**：由竞赛平台 WebSSH 下发，本地无需 Docker / 虚拟化；WSL2 可选
- 网络：能访问榜单站 `47.120.64.152:5000` 与竞赛平台 `218.2.108.11:40000` 等

```powershell
python -m pip install requests websocket-client
# 可选（用到再装）
python -m pip install scipy python-docx playwright
```

## 4. 10 分钟上手（新队友路径）

### 第 0 步：克隆并关闭自动换行转换

```powershell
git clone <私有仓库地址> iDSN
cd iDSN
git config core.autocrlf false   # 仓库用 .gitattributes 统一 LF，不要再让 git 自动转换
```

### 第 1 步：不联网、不需要账号的自检（约 30 秒）

```powershell
python tools/validate_pacer.py --selftest
```

预期最后一行输出 `SELFTEST PASS`：校验器会用三个内置样例（合法 / CRLF / 非法）自测。

再生成一棵本地配置树（`--dry-run` 不连云主机、不消耗额度）：

```powershell
python harness/run_experiment.py --tag demo --mode leak_bucket --params "leak_rate=9,bucket_cap=30,leak_interval_us=1000" --dry-run
python tools/validate_pacer.py runs/configs/demo
```

第一条命令会在 `runs/configs/demo/1..6/pacer.txt` 生成配置（`runs/` 不入库）；
第二条命令验证目录结构、UTF-8/LF、三行格式、`[timestamp:N]`、模块名与参数约束，预期 `[PASS] 全部检查通过`。

### 第 2 步：看榜（公开接口，无需登录）

```powershell
python client/api.py board          # 终端渲染总排名 + 逐题排名 + 最近提交日志
python client/api.py board --save   # 额外保存快照到 intel/raw/ 并追加流水到 runs/leaderboard/ledger.csv
```

### 第 3 步：登录与额度（谨慎）

```powershell
python client/api.py login          # 密码来源：--password > 环境变量 IDSN_PASSWORD > client/secrets.json > 交互输入
python client/api.py status         # 会话状态 + 今日已提交次数 / 5
```

> ⚠ 密码错误有**当日锁定计数**，脚本登录失败**绝不重试**。密码写在 `client/secrets.json`（不入库，向 Lead 私聊索取）。
> 平台账号（`client/trit.py`）同理：`python client/trit.py login` / `status`。

### 第 4 步：跑一次真实本地评测（需要云主机可用）

```powershell
python harness/run_experiment.py --tag leak9 --mode leak_bucket --params "leak_rate=9,bucket_cap=30,leak_interval_us=1000"
```

- `--mode` + `--params` 对 `1`–`6` 六个目录统一生效；按目录差异化配置用 `--configs-file`。
- 流程（脚本自动完成）：本地生成 `runs/configs/<tag>/` → 打 tar.gz → 上传云主机 → `format_check_client` 校验 → 后台跑 `competition_question1` → 短连接轮询 → 拉回结果 JSON/日志。
- 结果追加到 `runs/results.jsonl`，原始结果在 `runs/evals/`；单次约 2.5–5 分钟。
- 评测启动会短暂打断 WebSSH，脚本采用「短连接轮询」，**不要自己保持长连接**。

自定义 6 个目录的配置（`--configs-file`，JSON）：

```json
{
  "1": ["token_bucket", {"tokens": 100, "burst": 200}],
  "2": ["token_bucket", {"tokens": 100, "burst": 200}],
  "3": ["origin", {}],
  "4": ["origin", {}],
  "5": ["origin", {}],
  "6": ["origin", {}]
}
```

### 第 5 步：批量扫参与统计

```powershell
python harness/sweep.py --queue runs/queue1.json          # 按队列顺序跑，单个失败不中断
python harness/sweep.py --queue runs/queue1.json --only A B   # 只跑指定 tag
python harness/analyze.py                                # 按配置分组：n/均值/标准差/最快/vs 基线、分文件耗时
python harness/analyze.py --json                         # 机器可读输出
```

队列文件格式（JSON 数组，`repeat` 表示每个配置重复次数）：

```json
[
  {"tag": "A", "note": "precise 12.5MB/s", "all": ["precise_rate_based", {"max_pacing_rate": 12500000}], "repeat": 2},
  {"tag": "B", "note": "分文件配置", "configs": {"1": ["origin", {"burst_tokens": 100}]}, "repeat": 2}
]
```

### 第 6 步：盯榜与官方提交

```powershell
python tools/watch_board.py --team 赛博coder --interval 120 --max-min 300 --want 2
```

盯官方榜单，发现我们队第 2 条 attempts 即退出；新发现追加到 `runs/board_watch.jsonl`。

```powershell
python client/submit_vm.py                                  # dry-run：读当前 question 配置 + 跑格式检查
python client/submit_vm.py --yes --note "leak36/cap40/int4000"   # 真提交，消耗 1 次额度
```

> 提交前脚本自动执行 `./format_check_client`，未通过不提交；每日 5 次硬上限（本地计数 `runs/submissions.jsonl`）。
> **官方提交只由 Lead 执行**，队友不要动。

## 5. 脚本速查

| 命令 | 作用 | 是否联网/连云主机 |
|---|---|---|
| `python tools/validate_pacer.py <question目录> [--json]` | 校验 pacer.txt 树（结构/换行/格式/参数约束） | 否 |
| `python tools/validate_pacer.py --selftest` | 校验器自测 | 否 |
| `python harness/run_experiment.py --tag T ... [--dry-run] [--repeat N] [--poll 20] [--timeout 900]` | 单次评测编排 | `--dry-run` 否，否则连云主机 |
| `python harness/sweep.py --queue Q [--only TAG...]` | 队列批量评测 | 云主机 |
| `python harness/analyze.py [--json] [--tag T...] [--include-invalid]` | 汇总 `runs/results.jsonl` | 否 |
| `python harness/upload_config.py --tag T --mode M --params ...` | 只上传配置到云主机 + 格式检查（不评测） | 云主机 |
| `python harness/import_vm_result.py <vm_tag> [note]` | 补录云主机上已完成评测的结果 | 云主机 |
| `python harness/make_report_data.py` | 生成 `report/实验结果-数据表.md` | 否 |
| `python tools/config_stats.py` | 重写 `report/实验结果-统计.md` 第 1–4 节 | 否 |
| `python client/api.py board [--save]` | 查榜 | 是（公开接口） |
| `python client/api.py login` / `status` | 登录 / 会话与额度 | 是 |
| `python client/submit_vm.py [--yes]` | 官方提交（dry-run 默认） | 云主机 + 平台 |
| `python tools/watch_board.py` | 盯榜 | 是（公开接口） |
| `python tools/vm_load.py start 4` / `stop` / `status` | 云主机 CPU 争抢负载（测鲁棒性） | 云主机 |

云主机内手动评测与提交命令（由 `harness/` 与 `client/submit_vm.py` 自动调用，手动排查时用）：

```bash
cd /home/openlab/Desktop
./format_check_client
sudo ./competition_question1 --output-dir ./results --result-json ./results/evaluation_results.json --format-log-dir ./results/logs
./local_send_client --token <团队GUID>   # 只有 Lead 执行，消耗当日额度
```

## 6. 环境变量

| 变量 | 默认值 / 说明 |
|---|---|
| `IDSN_BASE` | 榜单站，默认 `http://47.120.64.152:5000` |
| `IDSN_TEAM` | 团队名，默认 `赛博coder` |
| `IDSN_PASSWORD` | 榜单站密码（优先级高于 secrets.json） |
| `IDSN_TRIT_BASE` | 竞赛平台，默认 `https://218.2.108.11:40000` |
| `IDSN_VM_HOST` / `IDSN_VM_USER` / `IDSN_VM_PASS` | 云主机 SSH 参数（默认值见 `client/vmssh.py`） |
| `IDSN_WS_TIMEOUT` | WebSSH 读写超时秒数，默认 900 |

## 7. 数据与敏感信息（不入库）

- `client/secrets.json`：团队密码、平台账号、团队 GUID、云主机口令
- `runs/.session.pkl`：榜单站会话 Cookie；`runs/trit_*.json`：平台 access/refresh token
- `runs/*.jsonl`：实验与提交流水；`runs/` 下的评测原始结果、配置 tar 包
- `docs/*.zip`、`docs/*.tar*`、`env/*.tar*`、`__pycache__/`、`*.pyc`

提交前务必用 `git status` 复核，**任何密码/token/GUID 都不允许进仓库**。
规则见 [.gitignore](.gitignore)，换行与二进制策略见 [.gitattributes](.gitattributes)。

## 8. 已知坑与纪律

1. **pacer.txt 必须 UTF-8、LF 换行、恰好三行、行尾无空白、末尾无换行**；Windows 下写文件用 `write_bytes`，否则 `write_text` 会转成 CRLF 导致评测解析失败。
2. `[timestamp:N]` 的 N 必须等于所在目录号；缺 `pacer.txt` 的目录表示沿用上一份配置。
3. 本地评测噪声约 ±7 s，**单点结论不可信**，实验默认 n≥3；官方每次提交 3 次取平均，方差同样重要。
4. 本地与官方口径可能存在系统性偏差（如 `leak_bucket` 定时器粒度问题），提交前先看 [STATUS.md](STATUS.md) 的结论。
5. 官方出分有 50–70 分钟延迟，每日 5 次额度要省着用；提交策略由 Lead 统一决策。
6. 红线：不攻击/探测官方评测系统、不硬编码答案、不多账号、密码错误不重试。

## 9. 文档索引

| 文档 | 内容 |
|---|---|
| [PLAN.md](PLAN.md) | 12 天作战计划、打法总纲、日程与风险 |
| [STATUS.md](STATUS.md) | 最新进展、官方计分规则、评分异常排查、榜单 |
| [hourly/INDEX.md](hourly/INDEX.md) | 每小时进度快照 |
| [report/复现说明.md](report/复现说明.md) | 从零复现提交配置与评测结果的完整步骤 |
| [report/技术报告-v1.md](report/技术报告-v1.md) | 技术报告（方法、实验、稳定性） |
| [intel/article.md](intel/article.md) | 赛事规则原文要点 |
| [docs/extracted/](docs/extracted/) | 官方资料抽取文本（流量整形模块说明、实验详细手册等） |
| [zcode/README.md](zcode/README.md) | AI 异步任务通道协议 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 团队协作规范（分支、提交、PR、密文管理） |
