# 贡献指南（CONTRIBUTING）

本仓库是团队「赛博coder」的比赛工作区。所有队友（含 AI 代理）提交代码/文档前，请先读完本文。
目标只有一个：**在 2026-11-16 榜冻结前稳定产出可复现的更快配置**，任何操作都不能危及账号、额度和官方复核。

---

## 1. 开始之前

1. 找 Lead 要两样东西（**私聊，不要发群/不要写进任何文件**）：
   - 私有仓库地址（clone 权限）
   - `client/secrets.json` 里的账号信息（团队密码 / 平台账号 / 团队 GUID / 云主机口令）
2. 环境按 [README.md](README.md) 第 3 节准备：Windows + PowerShell、Python 3.14、`requests` + `websocket-client`。
3. clone 后执行一次：

```powershell
git config core.autocrlf false
python -m pip install requests websocket-client
python tools/validate_pacer.py --selftest     # 预期 SELFTEST PASS
python client/api.py board                    # 只读查榜，不需要登录
```

## 2. 配置 client/secrets.json

`client/secrets.json` **已被 `.gitignore` 忽略**，每位队友在本地各自新建，**绝不提交、绝不外发**。
仓库当前尚未提供 `secrets.json.example`，请按下表自行创建（UTF-8 无 BOM）：

```json
{
  "team": "赛博coder",
  "password": "<榜单站团队密码>",
  "trit_username": "<平台登录手机号，可选>",
  "trit_password": "<平台密码>",
  "guid": "<团队 GUID，16 位>",
  "vm_password": "<云主机 openlab 口令>",
  "note": "<备注，可选>"
}
```

字段用途（与代码读取逻辑一致）：

| 字段 | 被谁读取 | 说明 |
|---|---|---|
| `team` | 人工参考 / `client/api.py`（默认值 `IDSN_TEAM`） | 团队名 |
| `password` | `client/api.py` 的 `read_secret()` | 榜单站登录密码；也可用环境变量 `IDSN_PASSWORD` 覆盖 |
| `trit_username` | `client/trit.py` | 平台用户名（可选，缺省回退到内置手机号） |
| `trit_password` | `client/trit.py` | 平台密码（缺省回退到 `password`） |
| `guid` | `client/submit_vm.py` | 官方提交令牌，缺失会直接拒绝提交 |
| `vm_password` | 云主机连接（Lead 已改为「环境变量 `IDSN_VM_PASS` 或本字段」） | 云主机 SSH 口令 |
| `note` | 无人读取 | 个人备注 |

安全底线：

- 密码/token/GUID 只存在于本地 `client/secrets.json` 与环境变量，**任何 md、代码、issue、PR、聊天记录里都不允许出现真实值**。
- 不要把 `client/secrets.json` 加进 git（不要 `git add -f`）；发现误提交立即告知 Lead 改密码。
- 榜单站登录**失败即停**：错误密码有当日锁定计数，脚本不会重试，也**不要手动反复试**。

## 3. 分支与提交

### 分支命名

| 前缀 | 用途 | 示例 |
|---|---|---|
| `feat/` | 新功能/新脚本 | `feat/board-diff-alert` |
| `exp/` | 实验性配置与搜索脚本（不影响主流程） | `exp/leak-4ms-granularity` |
| `fix/` | 修 bug | `fix/analyze-invalid-filter` |
| `docs/` | 文档 | `docs/repro-guide` |

- `main` 保持随时可跑；**不要直接 push 到 `main`**，一律开分支 + PR。
- 一个分支只做一件事，短生命周期，合并后删除。
- 动 `client/`、`harness/`、`tools/` 的核心逻辑前，先在 PR 里说明动机与验证命令。

### 提交信息（Conventional Commits，中英文均可）

```
<type>(<scope>): <一句话说明>
```

`type`：`feat` / `fix` / `docs` / `exp` / `refactor` / `chore`；`scope` 常用 `client`、`harness`、`tools`、`report`、`zcode`。

示例：

```
feat(client): 新增提交前额度预检
fix(harness): 修正无 tag 时的日志路径
exp(harness): leak_bucket 4ms 粒度重复实验队列
docs: 补充 pacer.txt 换行坑说明
```

要求：一个提交一个主题；不提交 `runs/` 下的实验数据；提交前 `git status` 复核没有敏感文件。

## 4. PR 流程

1. `git pull --rebase origin main` 同步最新代码。
2. 推送自己的分支，开 PR，标题同提交信息规范。
3. PR 描述必须包含：
   - **动机**：解决什么问题 / 哪个实验需求；
   - **改动**：涉及文件与行为变化；
   - **验证**：实际跑过的命令与结果（贴关键输出，数字要对得上 `runs/` 记录）；
   - **影响**：是否触碰提交额度、账号、评测流程。
4. 至少 1 名队友 review 后合并；涉及 `client/`、`harness/` 核心流程的改动由 Lead 把关。
5. 合并后删除分支；不要 `force push` 到共享分支。

## 5. 跑实验的纪律

1. **先拉最新**：`git pull --rebase origin main`，避免用旧脚本跑出新数据。
2. **先离线校验再连云主机**：
   ```powershell
   python harness/run_experiment.py --tag mytag --mode leak_bucket --params "leak_rate=9,bucket_cap=30,leak_interval_us=1000" --dry-run
   python tools/validate_pacer.py runs/configs/mytag
   ```
3. **本地噪声 ±7 s，单点结论不可信**：正式结论至少 n≥3（`--repeat 3` 或队列里重复）。
4. 实验记录只写 `runs/`（**不入库**）：`runs/results.jsonl` 由脚本追加，不要手改；`runs/configs/<tag>/` 是配置快照。
5. 汇总分析：
   ```powershell
   python harness/analyze.py
   python tools/config_stats.py        # 重写 report/实验结果-统计.md 的自动生成段
   ```
6. 报告类产出：技术报告与图表写 `report/`；zcode 通道的交付写 `zcode/reports/`，不要覆盖别人的报告。
7. **官方提交只由 Lead 执行**（`client/submit_vm.py --yes`）：每次消耗全队 1/5 额度，脚本有本地硬上限 5 次/天。队友不要自行提交。

## 6. 编码与换行规范

- 文本文件一律 **UTF-8（无 BOM）+ LF**；仓库已用 [.gitattributes](.gitattributes) 固定换行策略。
- Windows 下写文本不要依赖默认编码/换行：

```python
# 写 pacer.txt 与配置：必须 LF 且末尾无换行（参考 harness/run_experiment.py）
path.write_bytes(text.encode("utf-8"))
# 写 JSON：显式 UTF-8
path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), "utf-8")
```

- `.sh` 脚本必须 LF（官方评测对换行敏感，CRLF 会导致解析失败）。
- 修改 `tools/validate_pacer.py` 的校验规则前，先跑 `python tools/validate_pacer.py --selftest`，三样例必须仍 PASS。

## 7. 不要入库的东西

| 类别 | 例子 |
|---|---|
| 凭据 | `client/secrets.json`、`runs/.session.pkl`、`runs/trit_*.json`、`runs/login_redirect.json` |
| 实验数据 | `runs/*.jsonl`、`runs/evals/`、`runs/configs/*.tar.gz` |
| 大文件 | `docs/*.zip`、`docs/*.tar*`、`env/*.tar*`、`env/*.zip`（>10 MB 一律先问 Lead） |
| 缓存 | `__pycache__/`、`*.pyc` |

`.gitignore` 已覆盖上述大部分；新增敏感路径时**改 `.gitignore` 要单独发 PR**。

## 8. 目录所有权（避免互相覆盖）

| 路径 | 维护者 | 说明 |
|---|---|---|
| `PLAN.md`、`STATUS.md` | Lead | 其他人不要改；进展用 PR/消息汇报 |
| `README.md`、`CONTRIBUTING.md`、`.gitattributes` | 文档负责人 | 改前先 issue/说明 |
| `hourly/` | Lead | 每小时快照 |
| `zcode/` | zcode 通道 | 按 `zcode/README.md` 协议，只写 `requests/`、`reports/`、`inbox/` |
| `client/`、`harness/`、`tools/`、`scripts/`、`configs/` | 代码贡献者 | 开分支 + PR，改动需附验证命令 |
| `intel/`、`docs/`、`report/` | 全员（追加为主） | 新快照/新报告可加，不覆盖他人文件 |
| `runs/` | 本机 | 不入库，不共享 |

## 9. 常见问题

- **没权限克隆 / 缺 secrets.json 字段**：找 Lead，不要在公开渠道贴敏感信息。
- **本地评测失败**：先看 `runs/evals/<tag>.log`；`result.json` 缺失多半是格式检查未过。
- **不清楚还剩几次提交额度**：`python client/api.py status` 看今日已用次数；本地提交历史在 `runs/submissions.jsonl`。
- **不确定某文件该不该提交**：先 `git status` 看是否在忽略列表；拿不准就问 Lead，不要 `git add -f`。

---

有疑问先读 [README.md](README.md) → [STATUS.md](STATUS.md) → 再问人。变更流程本身就是比赛的一部分：**可复现、可审计、不碰账号与额度。**
