# GitHub 发布前安全审计报告

- 审计对象：`E:\Download\iDSN`（iDSN 竞赛工作仓库）
- 审计时间：2026-11-05
- 审计范围：全仓库 1069 个文件（含被 `.gitignore` 忽略的）、22.4 MB
- 审计方法：PowerShell 全量文件枚举 + 多模式正则扫描 + `git check-ignore` 精确判定（仓库已 `git init` 但**零 commit**，`git ls-files` 为空，故 `check-ignore` 可用）
- 只读扫描：**未登录任何账号、未联网提交任何数据、未修改仓库任何文件**
- 报告中所有真实密码 / token / 手机号 / 邮箱 / 姓名均已打码，不出现原文

---

## 一、结论

### ⛔ 当前状态：不可推送（`git add -A` 会泄露凭据与个人隐私）

量化结论：

| 指标 | 数值 |
|---|---|
| 仓库文件总数 | 1069 |
| 当前 `.gitignore` 实际忽略 | **10 个文件**（6 类规则） |
| `git add -A` 会纳入 | **1059 个文件 / 18.62 MB** |
| 其中含真实凭据的文件 | 6 个（4 个 JWT/登录态 + 2 个抓包） |
| 其中含个人隐私（手机号/姓名/学号/邮箱）的文件 | 9 个 |
| 单文件 > 10 MB | 0 个（最大 3.68 MB） |
| 超过 GitHub 100 MB 硬限制 | 无 |
| 含私钥 / `.env` / `id_rsa` | 无 |

**核心问题不是"代码写错了"，而是 `.gitignore` 只覆盖了 2 个真正的凭据文件（`client/secrets.json`、`runs/.session.pkl`），其余登录态、SSH 密码、抓包、截图、榜单原始数据全部会入库。**

> 好消息：仓库**尚无任何 commit**，只要在第一次 `git add` 之前修正 `.gitignore`，**无需 rewrite history**，风险完全可消除。

### ✅ 修复后结论

完成下方 **P0（8 项）+ P1（4 项）** 处置后，**可以推送到 GitHub 私有仓库**。P0 全部是"加 `.gitignore` 或删默认值"即可完成，无架构改动，预计 15 分钟。

---

## 二、判定口径："这个文件明天会不会被 git 提交"

由于仓库已 init，我直接用了权威判定而非推测：

```powershell
git -C E:\Download\iDSN check-ignore -v -- <file>
git -C E:\Download\iDSN status --ignored --porcelain
```

当前 `.gitignore` 仅 9 行，实际生效忽略 10 个文件：

```
runs/.session.pkl          (1 文件)
client/secrets.json        (1 文件)
runs/*.jsonl               (3 文件：results/submissions/board_watch)
docs/*.zip                 (1 文件：题目1附件.zip)
docs/*.tar*  env/*.tar*  env/*.zip   (0 文件)
__pycache__/  *.pyc        (4 文件)
```

**关键误区**：`runs/*.jsonl` 的通配只覆盖 `.jsonl`，**`.json` 一个都不覆盖**。因此 `runs/trit_token.json`、`runs/queue*.json`、`runs/leaderboard_full.json`、`runs/browser/*.json` 全部处于"待提交"状态。

---

## 三、P0 —— 阻断项（必须修复后才能推送）

### P0-1 JWT 登录凭据明文入库（3 个文件，最高危）

| 文件 | 行 | 命中（脱敏） | 说明 |
|---|---|---|---|
| `runs/trit_token.json` | 2,3 | `eyJhbGciOi***`（311 字符） | access_token + refresh_token 全量 |
| `runs/trit_token.json` | 4,5,6 | `f485****` / `赛博****` / `金****` | uuid、用户名、**真实姓名** |
| `runs/trit_login.json` | 2,3,11 | 同上 + realname | 登录态完整快照 |
| `runs/trit_login.backup.json` | 2,3,11 | 同上 | 备份副本，同样有效 |

- **风险：极高**。JWT 带 `Authorization: Bearer` 即可访问竞赛平台全部个人接口（`/api/competition/my`、`/api/user/info` 等），含 refresh_token 还能无限续期。
- **`git check-ignore` 判定：NOT-IGNORED → 会提交。**
- **处置**：`.gitignore` 增加 `runs/trit_*.json`；并确认这三份本地文件不要出现在任何 `git add` 里。

### P0-2 云主机 SSH 明文密码硬编码在源码里（即使 gitignore 也拦不住）

| 文件:行 | 命中（脱敏） | 说明 |
|---|---|---|
| `client/vmssh.py:36` | `VM_HOST = "192.168.***.***"` | 云主机内网 IP |
| `client/vmssh.py:37` | `VM_USER = "openlab"` | SSH 账号 |
| `client/vmssh.py:38` | `VM_PASS = "nu**@******"` | **明文 SSH 密码作为默认值** |
| `client/vmssh.py:39` | `PLATFORM = "https://218.***.***.***:40000"` | 竞赛平台地址 |
| `client/trit.py:34` | `BASE = "...218.***.***.***:40000"` | 同上 |
| `client/api.py:34` | `BASE = "...47.***.***.***:5000"` | 榜单站地址 |
| `scripts/vm_probe.sh:20` | 平台地址 | 同上 |

- **风险：极高**。这是唯一"改了 `.gitignore` 也无效"的一类——**源码本身就要入库**。密码 `nu**@******` 同时出现在 `client/secrets.json` 的 `vm_password` 字段（该文件已忽略，但源码里的默认值没被忽略）。
- **处置（必须改代码，不是加 gitignore）**：删除 `os.environ.get(..., "<默认密码>")` 中的默认值，改为：

```python
VM_PASS = os.environ.get("IDSN_VM_PASS") or read_secrets().get("vm_password")
if not VM_PASS:
    raise SystemExit("缺少 IDSN_VM_PASS（不应硬编码）")
```

`vmssh.py:66` 把密码塞进 base64 再拼 URL（`sshInfo=`），也建议改走环境变量。

### P0-3 浏览器抓包 JSON：明文 SSH 密码 + 手机号 + 邮箱 + 密码 MD5 + 真实姓名

| 文件:行 | 命中（脱敏） |
|---|---|
| `runs/browser/practice2_network.json:24` | `cellphone: 1**********`、`password: <32位MD5>`、`realname: 金****`、`email: mih****@g****.com` |
| `runs/browser/practice2_network.json:110,118,126` | `"username":"openlab","password":"nu**@******"`（明文） |
| `runs/browser/practice3_network.json:24` | 同上个人资料 |
| `runs/browser/practice3_network.json` | 明文 SSH 密码 **10 处** |
| `runs/browser/practice2_page.html:156`、`practice3_page.html:156` | 真实姓名 |

- **风险：极高**。这是 `https://<平台>/api/account/user/<uuid>/` 的原始响应，把平台返回的用户对象**含密码 MD5 和手机号**整个落盘了。
- 同一目录还有 30+ 张平台页面截图（`practice*_t*.png`、`webssh_test.png`、`diag.png` 等），页面里必然显示账号信息。
- **处置**：`.gitignore` 增加 `runs/browser/`（整个目录都不该入库）。

### P0-4 公众号/账户页 HTML：手机号 + 邮箱 + 真实姓名

| 文件:行 | 命中（脱敏） |
|---|---|
| `intel/raw/auth/page_account.html:40` | `realname: 金****` |
| `intel/raw/auth/page_account.html:58` | `<dt>手机号</dt><dd>1**********</dd>` |
| `intel/raw/auth/page_account.html:67` | `<dt>邮箱</dt><dd>mih****@g****.com</dd>` |

- **风险：高**（纯 PII，无凭据）。
- **处置**：`.gitignore` 增加 `intel/raw/`。

### P0-5 实验详情 JSON：手机号 + 学号 + 姓名

| 文件:行 | 命中（脱敏） |
|---|---|
| `intel/raw/trit/expt_detail.json:52-56` | `owner_name: 赛博****`、`owner_cellphone: 1**********`、`owner_career_id: U2024****`（学号） |
| `intel/raw/trit/schedule_user.json:9` | `realname: 金****` |
| `intel/raw/trit/train_enter_comp.json:4` | `realname: 金****` |

- **风险：高**（学号 + 手机号 + 姓名三件套）。
- 备注：`intel/raw/trit/topo_detail.json:58,156` 的 `password` 字段**已被替换为 `<redacted>`**（审计时已是脱敏状态，无需再处理）。
- **处置**：随 `intel/raw/` 一起忽略。

### P0-6 报名成功截图（含姓名/手机号的图片）

| 文件 | 大小 | 说明 |
|---|---|---|
| `intel/raw/registration_success.png` | 436 KB | 报名成功页截图，按页面结构必然含姓名 + 手机号 |

- **风险：高**。图片无法用正则扫描，但同目录 `page_account.html` 已证明页面含手机号/邮箱/姓名；未做 OCR 是不想引入额外依赖，按最坏情况处置。
- **处置**：随 `intel/raw/` 忽略。

### P0-7 排行榜/提交运行产物（竞赛策略 + 他人数据）

| 文件 | 数量 | 说明 |
|---|---|---|
| `runs/queue*.json` | 20 个 | 实验队列，含调参策略与预期分数 |
| `runs/leaderboard_full.json` | 1 | 完整榜单（含其他队伍数据） |
| `runs/official/` | 4 个 | 官方提交产物 `v1.tar.gz`/`v1b.tar.gz`/`v1.log`/`board.html` |
| `runs/leaderboard/` | 2 个 | `ledger.csv`、`monitor.md` 含团队名与排名 |
| `runs/login_redirect.json` | 1 | 登录跳转记录 |

- **风险：中高**。不泄露凭据，但泄露比赛策略、提交节奏、他人榜单数据；对私有仓库危害可控，但属于"运行产物不该入库"的典型。
- 已验证：`runs/configs/**/*.tar.gz` 与 `runs/official/*.tar.gz` 内部**只有 `pacer.txt`**，无凭据（可选择性入库）。
- **处置**：忽略 `runs/queue*.json`、`runs/leaderboard*.json`、`runs/leaderboard/`、`runs/official/`。

### P0-8 真实手机号作为代码默认值

| 文件:行 | 命中（脱敏） |
|---|---|
| `client/trit.py:12` | docstring 示例：`--username 1**********` |
| `client/trit.py:154` | `username = args.username or sec.get("trit_username") or "1**********"` |
| `client/secrets.json:3` | `trit_username: 1**********`（已忽略 ✓） |
| `PLAN.md:145` | 真实姓名 `金****` |

- **风险：中**。手机号是登录账号，与密码同等级别敏感；写死在源码 = 永久入库。
- **处置**：删除 `client/trit.py` 的第三个 `or "1***"` 兜底，改为从 secrets/环境变量取，取不到就报错；`PLAN.md:145` 的真实姓名替换为 `金**`（或团队代号）。

---

## 四、P1 —— 建议处理（不阻断推送）

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| P1-1 | `docs/题目1附件/` 下 3 个乱码文件名 docx：`ʵ����ϸ�ֲ�.docx`、`��������ģ��ʹ��˵��.docx`、`websearch��������ģ��.docx` | SHA256 与正常文件名版本**完全相同**（`87DCB5***`、`D816CF***`、`5B3545***`），共 3.76 MB 纯重复 | 直接删除这 3 个乱码副本（已证实逐字节重复），或 `docs/题目1附件/` 整体忽略 |
| P1-2 | `docs/` 全目录 11.95 MB | 竞赛官方材料 + 已忽略的 zip；`docs/*.zip` 已忽略但解压后的 docx 仍入库 | 私有仓库可保留；若要精简，忽略 `docs/题目1附件/` |
| P1-3 | `report/figures/_fonttest.png` | 字体测试残留图 | 删除 |
| P1-4 | `intel/raw/wechat_article.html` 3.47 MB | 公众号文章快照（第三方内容，含大量内联 JS） | 无凭据，**但建议忽略**；注意其中 3 处疑似"身份证号"经核实为**误报**（分别是 `nonce="972369333"` 与 `appmsg_listen_id: '150455098322573886'`） |
| P1-5 | `.gitattributes` / `README.md` / `CONTRIBUTING.md` | 审计期间由其他成员新增（并发写入），本身无风险 | 请 Lead 在最终 diff 中确认 |

---

## 五、大文件与仓库体积

- **单文件 > 10 MB：无**。最大 `docs/题目1附件.zip` 3.68 MB（且已被 `.gitignore` 忽略）。
- **单文件 > 100 MB：无**，不触发 GitHub 硬限制，无需 Git LFS。
- 预计首次提交体积：**18.62 MB / 1059 文件**；按 P0 处置后约 **9–10 MB**（主要剩 `docs/` 的 docx + `report/figures/*.png`）。
- `runs/` 目录本身 5.60 MB / 928 文件，其中 900+ 是 `runs/configs/*/N/pacer.txt` 这类自动生成产物，会显著膨胀 commit 噪音——建议忽略。

---

## 六、建议 `.gitignore` 全文（可直接整文件覆盖，UTF-8 无 BOM）

> 这份是**完整可粘贴版**，在现有 9 行基础上补齐 P0/P1 全部条目。请 Lead 直接替换 `.gitignore`。

```gitignore
# ============================================================
# iDSN 仓库 .gitignore  （安全审计 2026-11-05 加固版）
# 原则：凭据 / 登录态 / 抓包 / 个人隐私 / 运行产物 一律不入库
# ============================================================

# ---------- P0：凭据与密钥（任何情况都不得入库）----------
client/secrets.json
client/secrets*.json
*.secrets.json
runs/.session.pkl
*.pkl
*.pickle
runs/trit_token.json
runs/trit_login.json
runs/trit_login.backup.json
runs/trit_*.json
*.token
*.cookie
.env
.env.*
*.pem
*.key
*.p12
*.pfx
id_rsa
id_rsa.*
id_ed25519
id_ed25519.*

# ---------- P0：登录态、浏览器抓包、页面截图 ----------
# practice2/practice3_network.json 含明文 SSH 密码 + 手机号 + 密码MD5
runs/browser/
runs/login_redirect.json

# ---------- P0：含他人数据 / 竞赛策略的运行产物 ----------
runs/queue*.json
runs/leaderboard_full.json
runs/leaderboard/
runs/official/
runs/*.jsonl
runs/evals/*.log
runs/configs/

# ---------- P0：原始情报与个人隐私（手机号/姓名/学号/邮箱）----------
# page_account.html、expt_detail.json、registration_success.png 等
intel/raw/

# ---------- P1：体积与非必要材料 ----------
docs/*.zip
docs/*.tar*
docs/题目1附件/
env/*.tar*
env/*.zip
report/figures/_fonttest.png

# ---------- Python / 工具链 ----------
__pycache__/
*.pyc
.venv/
venv/
.idea/
.vscode/
.DS_Store
Thumbs.db
```

**如果只想要最小改动**（不想连 `runs/evals/`、`runs/configs/` 一起忽略），至少必须加这 6 条：

```gitignore
runs/trit_*.json
runs/browser/
runs/queue*.json
runs/leaderboard*
runs/official/
intel/raw/
```
加上原有 `client/secrets.json`、`runs/.session.pkl`、`runs/*.jsonl`，即可消除全部 P0 中的"文件入库"类风险（P0-2/P0-8 是源码问题，gitignore 无效）。

---

## 七、必须改代码的硬编码凭据位置（gitignore 无法覆盖）

| # | 文件:行 | 现状 | 改法 |
|---|---|---|---|
| 1 | `client/vmssh.py:38` | `VM_PASS = os.environ.get("IDSN_VM_PASS", "nu**@******")` | 去掉默认值，缺失即 `raise SystemExit` |
| 2 | `client/vmssh.py:36-37` | `VM_HOST`/`VM_USER` 硬编码内网 IP + `openlab` | 移入 `client/secrets.json` 或环境变量 |
| 3 | `client/vmssh.py:39` / `client/trit.py:34` | 平台 IP+端口硬编码 | 保留为**非敏感**默认值可接受（地址不算凭据），但建议统一走 `IDSN_TRIT_BASE` |
| 4 | `client/trit.py:154` | 手机号作为 username 兜底默认值 | 删除 `or "1**********"` 分支 |
| 5 | `client/trit.py:12` | docstring 里写真实手机号 | 改为 `--username <手机号>` |
| 6 | `PLAN.md:145` | 真实姓名 | 改为 `金**` 或团队代号 |
| 7 | `client/submit_vm.py:56-88` | `guid` 来自 secrets.json（正确做法，保留） | 无需改 |

---

## 八、操作步骤（给 Lead，按顺序执行）

```powershell
cd E:\Download\iDSN

# 1. 用第六节内容替换 .gitignore（UTF-8 无 BOM）
# 2. 改掉第七节的 7 处硬编码（至少第 1、2、4 处）
# 3. 验证：不应再有敏感文件处于待提交状态
git status --porcelain --ignored=no | Measure-Object -Line
git check-ignore -v -- runs/trit_token.json runs/browser/practice2_network.json intel/raw/auth/page_account.html runs/queue1.json
#    ↑ 这四条必须全部输出 "IGNORED"（exit code 0）

# 4. 再确认源码里没有明文密码残留
#    在 client/ scripts/ 里搜 "os.environ.get(...<默认值>)" 形式的硬编码密码（应无输出）
git grep -n -I -E "(PASS|PASSWORD|PWD)[A-Z_]*\s*=\s*os\.environ\.get\([^,]+,\s*[\x22']" -- client scripts harness tools
#    手机号应只剩脱敏占位（应无输出）
git grep -n -I -E "(?<![0-9])1[3-9][0-9]{9}(?![0-9])" -- client scripts harness tools

# 5. 确认无 >100MB 文件（GitHub 硬限制）
git ls-files -z | ForEach-Object { Get-Item -LiteralPath $_ } |
  Where-Object { $_.Length -gt 100MB } | Select-Object FullName, Length
# 6. 最后才 add / commit / push
```

> 目前仓库 **0 commit / `git ls-files` 为空**，所以**不需要 `git filter-repo` 类清理**。一旦带着 `runs/trit_token.json` 提交并 push，就必须 rewrite history + 通知 GitHub 支持 + **立刻重置平台密码并在平台侧吊销 token**。

---

## 九、审计局限（如实声明）

1. **未做 OCR**：`intel/raw/registration_success.png`、`runs/browser/*.png` 共 30+ 张截图未逐张识别，按"页面含账号信息"最坏情况判定为高/中风险。
2. **未解压二进制**：`docs/*.docx` 与 `.tar.gz` 仅抽查（tar 已确认只含 `pacer.txt`）；docx 未做 `unzip` 文本检索。
3. **未做熵检测**：未用 gitleaks/trufflehog 类工具做高熵字符串扫描，改用明文字典 + 结构模式（JWT `eyJ`、32 位 MD5、11 位手机号、`Authorization: Bearer`）。JWT 全仓库只命中 3 个 `trit_*.json`，覆盖完整。
4. **未验证凭据有效性**：按约束不登录、不联网，因此"token 是否已过期"未验证，一律按**有效**处置。
5. **并发写入**：审计期间其他成员新增了 `.gitattributes`/`README.md`/`CONTRIBUTING.md`、并对 `intel/raw/trit/topo_detail.json` 做了脱敏。本报告以**审计时刻快照**为准，提交前请重跑第八节验证命令。
6. **误报已剔除**：`intel/raw/wechat_article.html` 的 3 处"身份证号"命中经核实为 JS nonce 与 `appmsg_listen_id`，非真实证件号。

---

## 十、风险汇总表

| 等级 | 数量 | 代表文件 | 一句话 |
|---|---|---|---|
| 🔴 P0 凭据 | 4 | `runs/trit_token.json`、`runs/trit_login.json`、`runs/trit_login.backup.json` | JWT 可直登平台，含 refresh token |
| 🔴 P0 凭据（源码） | 1 | `client/vmssh.py:38` | 云主机 SSH 明文密码写死在代码里 |
| 🔴 P0 凭据（抓包） | 2 | `runs/browser/practice2_network.json`、`practice3_network.json` | 明文 SSH 密码 + 手机号 + 密码 MD5 |
| 🟠 P0 PII | 9 | `intel/raw/auth/page_account.html`、`intel/raw/trit/expt_detail.json`、`registration_success.png` | 手机号 / 姓名 / 学号 / 邮箱 |
| 🟡 P1 卫生 | 5 | `docs/题目1附件/*乱码*.docx`、`runs/queue*.json` | 3.76 MB 重复文件 + 运行产物噪音 |
| ⚪ 无风险 | — | `docs/*.zip`、`client/secrets.json`、`runs/.session.pkl`、`*.pyc` | 已被现有 `.gitignore` 正确忽略 |

**最终建议：先按第六节替换 `.gitignore` + 按第七节改 3 处硬编码，重跑第八节验证，全部 `IGNORED` 后即可推送。**

---

## 十一、处置记录（2026-11-05，Lead 执行，推送前复核）

| 审计项 | 处置 | 结果 |
|---|---|---|
| P0-1 JWT 登录态 `runs/trit_*.json` | `.gitignore` 增加 `runs/trit_*.json`、`*.pkl` | `git check-ignore` IGNORED ✅ |
| P0-2 `client/vmssh.py:38` 明文 SSH 密码 | 删除默认值，改读 `IDSN_VM_PASS` 环境变量 → 回退 `client/secrets.json` 的 `vm_password`；缺失时连接阶段报错 | 源码无明文 ✅ |
| P0-2 `scripts/vm_test_eval.sh:4` 明文 SSH 密码 | 改为 `IDSN_VM_PASS` 或 `~/.idsn_vm_pass` | 源码无明文 ✅ |
| P0-3 `runs/browser/`（抓包+截图） | 整目录 ignore | IGNORED ✅ |
| P0-4/5/6 `intel/raw/auth/`、`intel/raw/trit/`、`registration_success.png` | 分类 ignore（保留公开榜单快照与公众号原文） | IGNORED ✅ |
| P0-7 `runs/queue*.json`、`runs/leaderboard/`、`runs/official/` 等 | ignore；`runs/configs/*/` 与生成 tarball ignore，仅保留 `submit-*.tar.gz` | IGNORED / 5 个提交包保留 ✅ |
| P0-8 `client/trit.py` 手机号 | docstring 与 username 兜底改占位，用户名只从 `--username`/`IDSN_TRIT_USERNAME`/secrets 读取 | 源码无手机号 ✅ |
| P1-1 乱码重名 docx | SHA256 校验后删除 3 组重复副本（保留可读名） | docs 由 7.5MB → 3.7MB ✅ |
| P1-3 `report/figures/_fonttest.png` | ignore | 未入库 ✅ |

**推送前最终校验（本机实测）**：暂存 119 文件 / 8.9 MB；`git grep --cached` 对 `nudt@`/`wlxlab`/账号密码/手机号/JWT 均无真实命中（仅本报告中的打码示例与公众号 HTML 的浮点数误报）；无单文件 >4 MB，无需 LFS。

> 剩余建议（未执行，需人工决定）：① 推送后若此仓库曾以任何形式外流，应在云主机与平台侧更换 SSH / 登录密码；② 若日后改为公开仓库，建议先 `git filter-repo` 清除历史中的 `intel/` 第三方材料。
