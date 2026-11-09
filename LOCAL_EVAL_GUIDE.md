# 在自己电脑上理解 / 优化 iDSN 题目一「六载穿柜」

> 这份指南面向的场景：**你不想用 WebSocket 连竞赛云主机，而是想把必要资料通过 GitHub 转到自己的电脑，先离线理解赛题、比较配置，再决定是否值得上官方评测/提交。**
>
> 目录：`local-eval/`（脚本、文档、冠军配置、官方二进制）。
> 一句话结论：**离线仿真今天就能跑；官方本地评测需要一台有 root + containernet + Docker 的 Linux 机器，不是把二进制复制过去就能跑。**

---

## 0. 三条路线，先选一条

| 路线 | 需要什么 | 能回答什么 | 代价 |
|---|---|---|---|
| **A. 离线仿真（推荐先做）** | 只要 Python 3.10+，纯标准库 | 配置的相对优劣、机制理解、参数扫描、候选筛选 | 免费；结果不是官方分 |
| **B. 官方本地评测** | Linux x86_64 + root + containernet + Docker + TrafficGenerator/http_server + `/home/openlab/Desktop` 路径 | 接近官方的单次耗时 | 环境重；不消耗提交额度；本机噪声大 |
| **C. 官方提交** | 竞赛云主机/桌面 + `local_send_client --token` | 官方榜单成绩（3 次平均） | **每天 5 次**；用完有封号风险 |

**建议顺序：A 先筛 → B 少量验证 → C 只在有把握时提交。**
离线仿真不能替代官方出分，但它能让你在 0 成本下把明显错误的配置排除掉。

---

## 1. 当前状态（截至 2026-11-09，历史记录，以榜单为准）

- 题目：6 个文件顺序下载，`1.bin`–`6.bin` = 10/20/40/80/160/320 MB，合计 **630 MB**。
- 瓶颈：s1–s2 汇聚链路 **100 Mbps**，双向 RTT **70 ms**；背景 WebSearch 流量目标也是 **100 Mbps**。
- 公平份额约 **50 Mbps**；630 MB @ 50 Mbps ≈ **100.8 s**；链路物理下限 630 MB @ 100 Mbps ≈ **50.4 s**。
- 当前冠军配置（历史最好 **122.0463 s**）：

  | 目录 | 模块 | rate / cap / interval |
  |---|---|---|
  | 1 | `leak_bucket` | 40 / 40 / 4000 µs |
  | 2 | `leak_bucket` | 40 / 40 / 4000 µs |
  | 3 | `leak_bucket` | 40 / 40 / 4000 µs |
  | 4 | `leak_bucket` | 37 / 37 / 4000 µs |
  | 5 | `leak_bucket` | 36 / 36 / 4000 µs |
  | 6 | `leak_bucket` | 36 / 36 / 4000 µs |

- 榜首集团在 116 s 左右；单漏桶的官方响应面谷底约 **133 s**，所以冠军的 122 s 已经用了“前 3 档 40、后 3 档递减”的非对称结构，不是单纯 uniform leak。
- 本地单次噪声很大（±7–15 s 很常见）；官方按 3 次平均，且随机种子序列固定，所以官方重复性远好于本地单次。
- **今天官方提交额度已用完（5/5）**；下一次提交窗口以竞赛平台为准。
- **不要和队友的评测并发**：`competition_question1` 会启动 containernet/OVS/Docker，两个评测互相污染。包装脚本已加并发检查。

> 历史文档里的排名/成绩都有时间戳（例如 `HANDOFF-2026-11-08.md` 写的是 11/08 的第 5），不要当成实时榜单。

---

## 2. 赛题机制速览

### 2.1 拓扑与流量

```
搜索服务器 d3 (10.0.0.3) ──10ms/100M──┐                    ┌──10ms/100M── d1 (10.0.0.1) 存储服务器 [发文件]
                                      s1 ═══15ms/100Mbps═══ s2
搜索客户端 d4 (10.0.0.4) ──10ms/100M──┘   【唯一共享瓶颈】   └──10ms/100M── d2 (10.0.0.2) 下载客户端 [收文件]
```

- 下载流：`d1 → d2`，单连接、顺序 6 个文件。
- 背景流：`d3 → d4`，WebSearch 模型，长期目标 100 Mbps。
- RTT = 10 + 15 + 10 = 35 ms 单程 → **70 ms 往返**；BDP ≈ 875 KB。
- 背景流长分布（CDF）：

  | 流大小 | ≤10 KB | ≤20 KB | ≤30 KB | ≤50 KB | ≤80 KB | ≤200 KB | ≤1 MB | ≤2 MB | ≤5 MB | ≤10 MB | ≤30 MB |
  |---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
  | 概率 | 15% | 20% | 30% | 40% | 53% | 60% | 70% | 80% | 90% | 97% | 100% |

  均值约 1.7 MB，但尾部有 30 MB 巨流；一条 30 MB 流独占 100 Mbps 也要 2.4 s，和下载流竞争时会显著阻塞。

### 2.2 `pacer.txt` 格式（错一个字节就可能假成功）

每个 `question/N/pacer.txt` **恰好三行**：

```
[timestamp:N]
pacer_mode:<模块名>
pacer_config:k1=v1,k2=v2,...
```

硬性要求：

- UTF-8，**无 BOM**；
- **LF** 换行，不能 CRLF；
- **文件末尾不能有换行**；
- 三行顺序固定，行首/行尾不能有空白；
- `[timestamp:N]` 的 N 必须等于目录名；
- 参数名必须在 schema 里，类型为整数，满足模块内约束（如 `bucket_cap >= leak_rate`、`burst >= tokens`）。

用 `local-eval/tools/validate_pacer.py` 检查，不要只靠肉眼。

### 2.3 五个模块（详见 `docs/official/03_pacer_modules.md`）

| 模块 | 关键参数 | 行为 | 备注 |
|---|---|---|---|
| `origin` | `burst_tokens`, `max_pacing_rate`, `clock_granularity` | 默认模块；有 burst + 无在途包快速通路 | `rate=0` 近似不限速 |
| `token_bucket` | `tokens`, `burst`, `token_refill_rate`, `token_refill_interval_us`, `enable_n_in_flight` | 令牌桶；空档期可积攒令牌 | 有 `enable_n_in_flight` 旁路 |
| `coarse_grained_rate_based` | `max_pacing_rate`, `clock_granularity`, `enable_n_in_flight` | 按 tick 离散放行，有微突发 | 有旁路 |
| `precise_rate_based` | `max_pacing_rate`, `clock_granularity`, `enable_n_in_flight` | 逐包精确间隔，最平滑 | 有旁路；开销较大 |
| `leak_bucket` | `leak_rate`, `bucket_cap`, `leak_interval_us` | 每 interval 漏出 rate 个包；**没有** `enable_n_in_flight` 旁路 | 受官方定时器粒度影响最大 |

### 2.4 最重要的两个“红线”

1. **官方定时器粒度约 4 ms**：`leak_bucket` 的 `leak_interval_us` **不要小于 4000**。
   - 历史实测：`leak 9/30/1000µs` 本地 ~125 s，官方 **245.995 s / 243.958 s**（约 2 倍）。
   - 机制：1 ms 的漏出间隔被拉长到 4 ms 的整数倍，实际速率被除以 4。
   - 需要更快速率时，用 `leak_interval_us=4000` + 更大的 `leak_rate`，或改用带旁路的模块。
   - 详见 `docs/background/timer-granularity.md`。

2. **burst 红线约 40–42 包**：交换机浅队列下，单拍突发超过 40–42 容易自溢丢包，触发拥塞控制退避。
   - 历史实测：`burst=50` 的 token_bucket 官方约 145 s；`leak 41` 的微突发也出现过 124.66 s 的惩罚。
   - `leak_bucket` 的突发量约等于 `leak_rate`（每 interval 漏一批），所以 `leak_rate` 也尽量不超过 40–42。
   - 约束：`bucket_cap >= leak_rate`；`burst >= tokens`。

### 2.5 官方怎么评分

- 官方服务器对每次提交**重复评测 3 次取平均**；榜单取历史最优。
- 官方随机种子序列固定，所以同配置重复提交的成绩很稳（历史两次相同配置差 0.83%）。
- 本地官方评测器每次只跑 1 次，且 `seed=None`（用系统时间），所以单次波动大；**本地必须跑多次看均值/标准差**。

---

## 3. 路线 A：离线仿真（5 分钟上手）

### 3.1 自检

```bash
cd ~/polaris/local-eval

python3 tools/validate_pacer.py --selftest
python3 tools/validate_pacer.py question
python3 tools/timer_model.py table
```

预期：

- 第一条最后输出 `SELFTEST PASS`；
- 第二条输出 `[PASS] 全部检查通过 ...`；
- 第三条打印不同定时器粒度 G 下的理论官方值表。

### 3.2 评估冠军配置

```bash
# 50 个种子先看量级（几十秒）
python3 tools/offline_pacer_sim.py \
  --configs configs/champion-1108-shot-steady.json \
  --seeds 50

# 稳定比较用 300 个种子，并把结果存 JSON
python3 tools/offline_pacer_sim.py \
  --configs configs/champion-1108-shot-steady.json \
  --seeds 300 \
  --json-out runs/sim-champion-300.json
```

输出字段：

- `mean / median / std / se / ci95`：总耗时统计；
- `per_file_mean`：6 个文件的平均耗时，用来判断是“前段慢”还是“后段慢”；
- `burst_unsafe`：静态 burst 红线检查；
- `errors`：无效跑数量（仿真里通常是 0）。

### 3.3 比较单点 leak 配置

```bash
# 六目录同配：40/40/4000，跑 200 个种子
python3 tools/offline_pacer_sim.py \
  --uniform leak_bucket:leak_rate=40,bucket_cap=40,leak_interval_us=4000 \
  --seeds 200

# 观察 1 ms 陷阱：仿真会把它判成远高于 200s
python3 tools/offline_pacer_sim.py \
  --uniform leak_bucket:leak_rate=9,bucket_cap=30,leak_interval_us=1000 \
  --seeds 50
```

### 3.4 自定义六目录配置

配置 JSON 的格式是：

```json
{
  "1": ["leak_bucket", {"leak_rate": 40, "bucket_cap": 40, "leak_interval_us": 4000}],
  "2": ["leak_bucket", {"leak_rate": 40, "bucket_cap": 40, "leak_interval_us": 4000}],
  "3": ["leak_bucket", {"leak_rate": 40, "bucket_cap": 40, "leak_interval_us": 4000}],
  "4": ["leak_bucket", {"leak_rate": 37, "bucket_cap": 37, "leak_interval_us": 4000}],
  "5": ["leak_bucket", {"leak_rate": 36, "bucket_cap": 36, "leak_interval_us": 4000}],
  "6": ["leak_bucket", {"leak_rate": 36, "bucket_cap": 36, "leak_interval_us": 4000}]
}
```

把它保存成 `configs/my-candidate.json`，然后：

```bash
# 1) 仿真
python3 tools/offline_pacer_sim.py --configs configs/my-candidate.json --seeds 300

# 2) 渲染成合法的 pacer.txt 树（不要手写，避免 CRLF/末尾换行）
python3 tools/render_configs.py --config configs/my-candidate.json --out candidates/my-candidate
python3 tools/validate_pacer.py candidates/my-candidate
```

> 仓库里的 `question/` 就是由 `configs/champion-1108-shot-steady.json` 渲染的；
> 不要直接手改 `question/` 再忘了同步 JSON，否则下次渲染会把改动覆盖掉。

> **模型局限（很重要）**：仿真器用 4 ms 粒度、WebSearch CDF、瓶颈队列和 cubic 拥塞控制近似官方，并用 `leak36/40/4000 @ 133.086s` 官方锚点拟合了一个全局 offset。它适合筛掉“1 ms 陷阱”“burst 过大”这类明显错误，但**不能很好地区分冠军阶梯和 uniform 36**。
>
> 实测（本机 100 seeds）：
> - champion `40/40/40/37/36/36` → 133.5 s
> - uniform `36/40/4000` → 132.9 s
> - uniform `40/40/4000` → 133.5 s
>
> 三者几乎一样；但官方成绩是 champion **122.0463 s**、uniform36 **133.086 s**。说明仿真器缺了“前段 40 的阶梯增益”。所以：**用仿真器做机制理解和粗筛，不要用它给阶梯做细排**；阶梯微调必须靠本地官方评测或官方提交验证。
>
> 想更保守，用 `--cc reno` 或 `--regime local` 做敏感性检查；绝对值不要当官方分。

### 3.5 仿真器的自校准

```bash
python3 tools/offline_pacer_sim.py --selftest --seeds 60
```

它会用 6 个校准点（leak36、leak9 陷阱、leak24/60、leak30/50/5000、token_bucket、leak40/60）检查模型是否还能命中历史官方值，并检查：
- `leak9` 仿真是否 > 220s；
- 冠军阶梯 `40/40/40/37/36/36` 是否接近 uniform 36；
- 静态 burst 规则是否能标出 `burst=50`。

低种子数下可能因随机波动 FAIL；用 `--seeds 300` 再试。

### 3.6 官方定时器模型

```bash
python3 tools/timer_model.py table       # 不同 G 下的理论值
python3 tools/timer_model.py equiv       # 各 interval 要写多少 leak_rate 才等效
python3 tools/timer_model.py fit         # 已知官方点 vs 模型
python3 tools/timer_model.py sweep-G     # 扫描 G 的可行域
```

重点看 `equiv`：它告诉你“如果非要改 interval，rate 应该怎么换算”。但在官方环境里，**最稳的做法仍是 `leak_interval_us=4000`**。

---

## 4. 路线 B：官方本地评测（重，按需）

### 4.1 官方二进制到底依赖什么

从进程、`--help`、字符串和历史上的逆向记录看，`competition_question1` 不是“单文件评测器”，它大致会：

1. 读取 `/home/openlab/Desktop/question/1..6/pacer.txt`；
2. 在 `/home/openlab/Desktop/question/1/topo.py` 生成/使用拓扑脚本；
3. 调用 containernet（`/root/containernet`）启动 `mn.d1`–`mn.d4` 等 Docker 容器；
4. 在 d3/d4 启动 `/home/TrafficGenerator/bin/server` 和 `client` 产生 WebSearch 背景流；
5. 在 d1 启动 `./http_server`（日志写到 `/home/http_server/http_server.log`）；
6. 在 d2 顺序下载 6 个文件，每个文件前应用对应目录的 pacer 配置；
7. 输出 `时间(competition).log`、`时间(competition).txt`、`evaluation_results.json`。

因此它需要：

- **Linux x86_64**（glibc；不是 macOS/Windows 原生）；
- **root/sudo**（containernet、网络命名空间、OVS、Docker）；
- **containernet + Mininet + Open vSwitch**；
- **Docker** 以及竞赛环境里的容器镜像（镜像里通常带 `/home/TrafficGenerator`、`http_server`、`lsquic` 等）；
- 硬编码路径 **`/home/openlab/Desktop/question`**（换用户名/路径会找不到配置）；
- 可写的 `/home/openlab/Desktop`（运行时会生成 `topo.py`、日志等）。

**结论：只把 `bin/competition_question1` 复制到自己电脑，通常跑不起来。** 二进制只有 17 MB，不可能自带 Docker 镜像、containernet 和 TrafficGenerator。

### 4.2 最省力的“官方评测”方式

如果只是要官方本地评测，**竞赛云主机仍然是最省力的**：环境已经装好，`question/` 也在正确路径。你可以：

- 用 GitHub 同步配置到云主机（如果云主机能访问 GitHub）；
- 或者在云主机的桌面/远程桌面上手动改 `question/`；
- 只在需要时启动一次 `sudo ./competition_question1`。

WebSocket 不稳定不影响“本地评测”本身；它只影响你从外部连进去的方式。你可以把“配置生成/离线仿真”放在自己电脑，“官方评测”放在云主机，二者用 GitHub 同步。

### 4.3 在自己的 Linux 机器上尝试（需要折腾）

建议用 **Ubuntu 22.04/20.04 的完整虚拟机**（不是 WSL 的默认模式），并给自己 root。高层步骤：

```bash
# 1) 基础依赖（具体以 containernet 官方安装文档为准）
sudo apt update
sudo apt install -y docker.io openvswitch-switch python3-pip git

# 2) 安装 containernet（按官方文档执行；不同版本命令不同）
#    https://github.com/containernet/containernet
#    常见方式是 clone 后用 ansible playbook 安装

# 3) 准备官方二进制和路径
sudo mkdir -p /home/openlab/Desktop
sudo chown -R "$USER":"$USER" /home/openlab/Desktop
cp -a ~/polaris/local-eval/bin/competition_question1 /home/openlab/Desktop/
cp -a ~/polaris/local-eval/bin/format_check_client /home/openlab/Desktop/
cp -a ~/polaris/local-eval/bin/local_send_client /home/openlab/Desktop/
cp -a ~/polaris/local-eval/question /home/openlab/Desktop/question

# 4) 格式检查
cd /home/openlab/Desktop
./format_check_client

# 5) 官方本地评测（会启动 containernet/Docker；不要在队友评测时跑）
sudo ./competition_question1 \
  --output-dir ./eval-out \
  --result-json ./eval-out/result.json \
  --format-log-dir ./eval-out/format-log
```

如果第 5 步失败，优先看：

- `eval-out/` 下的 `*.log` / `*.txt`；
- `/home/http_server/http_server.log`；
- `docker ps -a` 是否有 `mn.d1`–`mn.d4`；
- 是否缺 `/root/containernet`、TrafficGenerator 镜像、`lsquic`；
- 是否因为用户名不是 `openlab` 导致路径不对。

> 这条路的学习成本主要在 containernet/Docker/OVS，而不是 iDSN 配置本身。除非你确实需要大量本地官方评测，否则**离线仿真 + 云主机少量官方评测**性价比更高。

### 4.4 包装脚本

仓库里提供了一个包装脚本，负责备份/恢复 `/home/openlab/Desktop/question`、并发检查、跑 N 次、汇总：

```bash
cd ~/polaris/local-eval

# 跑 1 次
./scripts/run_official_eval.sh

# 跑 3 次取平均（推荐）
TAG=my-candidate REPEAT=3 ./scripts/run_official_eval.sh

# 跑完保留评测配置在 Desktop（默认会恢复原配置）
KEEP=1 TAG=my-candidate REPEAT=3 ./scripts/run_official_eval.sh
```

它会：

- 检查 `bin/competition_question1`、`question/1..6/pacer.txt`；
- 检查是否已有 `competition_question1` 在跑（有则退出，除非 `FORCE=1`）；
- 备份 `/home/openlab/Desktop/question`；
- 把 `local-eval/question` 复制过去；
- 调官方二进制，结果落到 `local-eval/evals/<tag>/run-*/`；
- 退出时恢复原 `question`（`KEEP=1` 可跳过）。

**它不会安装依赖，也不会帮你输入 sudo 密码。** 如果环境没装好，它只能把错误日志留在 `run.log` 里。

### 4.5 本地官方评测的判读

- 单次总耗时 < 50.4 s：**无效跑**（低于物理下限，通常是下载失败被误判成功）。
- 单次 110–150 s：正常范围，但噪声大；至少 3 次，最好 5–10 次。
- 看均值/标准差/变异系数，不看单次最好值。
- 同一配置在不同时间跑，可能因为机器负载差 5–15 s；不要在队友跑评测时做对比实验。
- 本地官方评测**不消耗**提交额度；但它会占用机器和网络，仍然要避免并发。

---

## 5. 路线 C：GitHub 作为桥

### 5.1 从这台机器推到 GitHub

当前 `~/polaris` 是一个干净仓库，已经加入：

- `LOCAL_EVAL_GUIDE.md`
- `local-eval/`（脚本、文档、冠军配置、官方二进制）
- `.gitattributes`（强制 LF，保护 `pacer.txt`）
- `.gitignore`（排除运行产物/凭据）

提交并推送：

```bash
cd ~/polaris
git status
git add .gitattributes .gitignore LOCAL_EVAL_GUIDE.md local-eval
git commit -m "feat(local-eval): add offline simulator, official docs, champion config"
git push origin HEAD
```

如果推送失败：

- HTTPS 需要 PAT（GitHub token），不要把 token 写进仓库；
- 或者改用 SSH：`git remote set-url origin git@github.com:polaris-agent1111/temp.git`；
- 如果 `bin/` 的 43 MB 让推送太慢，可以先 `git rm --cached local-eval/bin/competition_question1 ...`（见 `local-eval/bin/README.md`）。

### 5.2 在自己的电脑上拉下来

```bash
git clone https://github.com/polaris-agent1111/temp.git
cd temp

python3 local-eval/tools/validate_pacer.py --selftest
python3 local-eval/tools/validate_pacer.py local-eval/question
python3 local-eval/tools/offline_pacer_sim.py \
  --configs local-eval/configs/champion-1108-shot-steady.json \
  --seeds 100
```

Windows 建议用 WSL2/Ubuntu；macOS 可以直接跑离线 Python 工具（官方二进制不行）。拉下来后先确认：

```bash
file local-eval/question/1/pacer.txt
# 应该是 UTF-8 text，不能有 CRLF；.gitattributes 已强制 LF
```

### 5.3 配置同步回云主机

如果云主机能访问 GitHub：

```bash
# 云主机上
cd ~/polaris   # 或你的 clone 目录
git pull
# 把 local-eval/question 复制到 /home/openlab/Desktop/question
```

如果云主机不能访问 GitHub，就只能用竞赛平台自带的上传/桌面方式；这时 GitHub 仍然可以作为“自己电脑之间的版本管理”，但不能当云主机的传输通道。

---

## 6. 优化 playbook

### 6.1 先建立基线

```bash
cd ~/polaris/local-eval
python3 tools/offline_pacer_sim.py \
  --configs configs/champion-1108-shot-steady.json --seeds 300
```

记下 `mean`、`per_file_mean`。后面所有候选都用**同一组种子**（默认 `seed0=42`）比较，减少随机差异。

> 注意：基线仿真大约 133 s，而官方冠军是 122 s；这不是配置错了，而是仿真器对“前段 40 的阶梯增益”建模不足（见 3.4 的局限说明）。所以**仿真基线只用于相对比较**，不要拿 133 s 去反推官方一定也是 133 s。

### 6.2 理解冠军为什么是“阶梯”

- `1–4.bin`：文件较小，时间里有明显的握手/慢启动/管路填充固定成本；前段用 40 的速率可以更快抢到空档。
- `5–6.bin`：大文件稳态，主要和背景长尾流竞争；后段降到 37/36，减少微突发和队列溢出，避免拥塞控制退避。
- 这不是“全局最优的单一 leak 速率”，而是**前段激进、后段收敛**的非对称结构。

### 6.3 可以试的方向

1. **微调阶梯**（最稳，但必须用官方评测验证）：
   - `40/40/40/38/37/36`
   - `40/40/39/37/36/36`
   - `40/40/40/37/37/36`
   - `41/41/40/37/36/36`（41 有微突发风险，历史上出现过 124.66 s）
   每次只改 1–2 个目录，保持其余不变，便于归因。
   **不要用离线仿真给这些阶梯排名**：模型会把它们算得几乎一样（见 3.4）。要比较阶梯，直接做本地官方评测 `REPEAT=3` 或官方提交。

2. **cap 与 rate 解耦**：
   - 冠军用 `cap=rate`；可以试 `cap=40` 固定、rate 递减（如 `40/40/40/37/36/36` 且 cap 全 40），观察 cap 是否有独立影响。
   - 约束仍是 `bucket_cap >= leak_rate`；cap 太大会增加突发风险。

3. **后段换模块**（历史方向，需重新验证）：
   - `token_bucket` / `precise_rate_based` 带 `enable_n_in_flight=1` 旁路，理论上能绕过 4 ms 定时器，做更平滑的稳态。
   - 历史上技术报告 v4 记录过 119.268 s 的混合方案（前段 token_bucket + 后段 precise），但后续官方成绩和本地复现需要重新核对；不要直接把它当结论。
   - 换模块时先用离线仿真比较，再本地官方评测 n≥3。

4. **不要做的事**：
   - 不要用 `leak_interval_us < 4000`；
   - 不要用 `burst > 40–42`（尤其 token_bucket 的 `burst`）；
   - 不要用单次本地最好值选配置；
   - 不要为了“看起来更快”改 `pacer.txt` 的换行/末尾换行；
   - 不要在一天额度用完后继续提交。

### 6.4 测量协议（建议写进实验记录）

- 离线仿真：`seeds=100` 快筛，`seeds=300` 复筛；比较 `mean` 和 `ci95`，不比较单次 `min`。
- 本地官方评测：`REPEAT=3` 起步，重要候选 `REPEAT=5`；记录 `mean/std/min/max` 和无效跑数量。
- 官方提交：只提交在离线 + 本地都稳定优于冠军的配置；官方 3 次平均，单次本地优势 < 3 s 基本不够。
- 任何“提升”都要问：是配置变了，还是机器负载/随机种子变了？同一天、同一负载窗口内做 A/B 才有意义。

---

## 7. 文件地图 / 常用命令

```text
~/polaris/
├── LOCAL_EVAL_GUIDE.md              ← 本文
├── deep-research-report.md          ← 早期泛化调研（注意：不是本赛题 6 文件版）
├── 题目1附件/                        ← 官方 DOCX 附件
└── local-eval/
    ├── README.md
    ├── tools/
    │   ├── offline_pacer_sim.py     ← 核心离线仿真
    │   ├── timer_model.py           ← 4ms 定时器模型
    │   ├── validate_pacer.py        ← 格式校验
    │   ├── render_configs.py        ← 配置 JSON -> question/ 树
    │   ├── collect_results.py       ← 汇总 evals/*/result.json
    │   ├── analyze.py               ← 历史 results.jsonl 聚合
    │   ├── config_stats.py
    │   ├── audit_plan.py
    │   ├── check_all_configs.py
    │   └── monte_carlo_websearch.py ← 需要 numpy（可选）
    ├── configs/
    │   ├── params_schema.json
    │   └── champion-1108-shot-steady.json
    ├── question/1..6/pacer.txt      ← 当前冠军配置
    ├── docs/official/               ← 官方 4 份文档
    ├── docs/background/             ← 历史机制分析/报告
    ├── bin/                         ← 官方二进制（可选，43MB）
    ├── scripts/
    │   ├── validate.sh
    │   ├── sim_champion.sh
    │   ├── sim_uniform.sh
    │   └── run_official_eval.sh
    ├── evals/                       ← 本地官方评测输出（git 忽略）
    └── runs/                        ← 仿真输出（git 忽略）
```

常用命令速查：

```bash
# 校验
python3 tools/validate_pacer.py --selftest
python3 tools/validate_pacer.py question

# 配置 JSON -> question 树
python3 tools/render_configs.py --config configs/my-candidate.json --out candidates/my-candidate

# 冠军仿真
python3 tools/offline_pacer_sim.py --configs configs/champion-1108-shot-steady.json --seeds 300

# 单点 leak
python3 tools/offline_pacer_sim.py --uniform leak_bucket:leak_rate=40,bucket_cap=40,leak_interval_us=4000 --seeds 200

# 定时器模型
python3 tools/timer_model.py table
python3 tools/timer_model.py equiv

# 汇总本地官方评测
python3 tools/collect_results.py --evals-dir evals
python3 tools/collect_results.py --evals-dir evals --min-n 3

# 官方本地评测包装（重）
TAG=my-candidate REPEAT=3 ./scripts/run_official_eval.sh
```

---

## 8. FAQ

**Q1：为什么本地官方评测和官方榜单差很多？**
本地每次用系统时间当随机种子，背景流长尾的到达时刻每次不同；官方固定种子序列并跑 3 次平均。再加上本地机器负载、容器/OVS 状态，单次差 7–15 s 很正常。看均值，不看单次。

**Q2：为什么 `competition_question1` 在我 Mac 上跑不了？**
它是 Linux x86_64 的 Nuitka 二进制，依赖 containernet、Docker、OVS、root 和 `/home/openlab/Desktop/question`。macOS 原生不行；Windows 建议 WSL2 或 Linux 虚拟机，而且 WSL2 的嵌套 Docker/OVS 也不保证。

**Q3：我只想理解赛题，不想装 containernet，够吗？**
够。用 `offline_pacer_sim.py` + `timer_model.py` + 官方 4 份文档即可理解机制和比较配置。真实官方分还是要在云主机/完整环境跑。

**Q4：`leak_interval_us` 能不能写 1000？**
不要。官方定时器粒度约 4 ms，1 ms 会被拉成 4 ms，实际速率除以 4，历史官方成绩约 244 s。用 4000。

**Q5：`burst` 能不能大一点抢空档？**
40–42 是历史红线。`token_bucket burst=50` 出现过约 145 s 的官方惩罚；`leak 41` 也出现过 124.66 s。想抢空档，优先调 rate/模块，不要盲目加 burst。

**Q6：本地官方评测消耗提交额度吗？**
不消耗。只有 `local_send_client --token ...` 成功连上服务端才消耗每天 5 次额度。但本地评测会占用机器，别和队友并发。

**Q7：怎么提交？**
在竞赛云主机桌面（或能访问服务端的机器）运行：
```bash
./local_send_client --token <你的16位GUID>
```
提交前先 `./format_check_client`。**GUID 不要写进 GitHub。** 额度 5/天，超量提交有封号风险。

**Q8：仿真器的绝对值和官方差多少？**
它用官方锚点拟合了 offset，历史校准点误差在几秒内；但它是模型，不是官方。更具体地说：它把冠军阶梯算成 ~133.5 s，而官方是 122.0 s——**它低估了前段 40 的阶梯增益**。所以：A/B 粗筛可以，阶梯细排/绝对预测不行。

**Q9：为什么 `format_check_client` 说只检查 1–5？**
官方帮助文本是通用模板（手册里也写“子目录个数因赛题而异”）；本赛题实际是 1–6。以 `validate_pacer.py` 和实际 `question/1..6` 为准。

**Q10：GitHub 推送 43 MB 二进制太慢怎么办？**
离线仿真不需要二进制。可以在 push 前把 `local-eval/bin/` 从索引移除（保留本地文件），或者把二进制放到 GitHub Release/网盘。见 `local-eval/bin/README.md`。

---

## 9. 建议的下一步

1. 先跑 `validate.sh` 和 `sim_champion.sh`，确认工具链正常。
2. 用 `offline_pacer_sim.py` 跑冠军 + 3 个阶梯候选，各 300 seeds，记录 `mean/per_file_mean`。
3. 选 1–2 个在仿真里稳定优于冠军的候选，去云主机做 `REPEAT=3` 的官方本地评测。
4. 只有本地官方评测也稳定更优，才考虑第二天的官方提交额度。
5. 把每次实验的配置、命令、结果写进一个 `local-eval/runs/NOTES.md`（不入库也行），避免“凭感觉记住”。

> 最后提醒：**离线仿真负责“想清楚”，官方评测负责“验证”，官方提交负责“上分”。** 三者不要混在一起，尤其不要用单次本地最好值直接提交。
