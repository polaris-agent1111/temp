# 0244 理论审计 — 决选方案配置哈希硬编码签名与全量校验

- **作者**：zcode（任务 0244）
- **完成时间**：2026-11-07 17:40（本版本覆盖 17:01 的陈旧转录——那是本任务脚本首版输出的粘贴件，缺自校验段与参数序发现）
- **对象**：11/08 决选 5 发真实提交清单 `runs/seq_1108_shot_{1..5}.json` 及其渲染配置树（提交通路：`tools/submit_batch.py --plan` → `harness/upload_config.py --configs-file` → `build_tree`/`render_pacer` 字节落盘）
- **审计工具**：`zcode/scripts/audit0244_config_fingerprint.py`（只读；输出 `zcode/scripts/_0244_out.md`；退出码 0=PASS）
- **数据源**：`configs/params_schema.json`（格式规则 SSOT，只读加载）、`runs/configs/` 磁盘真实渲染树（自校验基准）
- **合规声明**：不联网、不提交、不触碰评测系统；指纹计算纯本地。
- **一句话结论**：**5 个决选清单 + 3 棵 distinct 配置树 × 6 目录 + 3 组家族一致性 + 3 项磁盘真树逐字节自校验共 29 项校验全部通过（100% 格式合规且一致）；复刻渲染器对真实管线输出逐字节验证；每发提交前重跑工具比对指纹即可检测任何篡改。**

---

## 一、决选配置树复合指纹（核心交付）

复合指纹配方：`SHA-256( ⊕_{n=1..6} b"{n}/pacer.txt" ⊕ NUL ⊕ pacer_bytes ⊕ NUL )`，pacer 字节按 seq_1108 管线语义渲染（UTF-8 无 BOM、纯 LF、恰好 3 行、末尾无换行、参数序 = 清单 JSON 键序 `bucket_cap,leak_interval_us,leak_rate`）。

| 决选树 | 树级复合指纹 (SHA-256) | 使用发次 |
|---|---|---|
| steady-40x3-37-36-36 | `6556f6b727e2ffcdda678137ba6af1588ff67ca1c49d18207ad5d2096cdd1f12` | Shot 1 |
| crown-41x2-40-37-36x2 | `6f995d6b9ed39381ba8b455a37be706715061e28229f4c56b1dba8cbac73261b` | Shot 2 / 4 / 5 |
| crown-pert-40on2 | `f96a6f7f1d27dea498aa2a93723fe0da02c4d9333cca5025925ab4e0c50e3f66` | Shot 3 |

## 二、提交清单文件签名（原始字节）

| 清单文件 | 字节 | SHA-256 |
|---|---|---|
| `runs/seq_1108_shot_1.json` | 1188 | `33b37f4ea9bd6a76e296154ed57a1490bc49a34c40d4ea5970353fc6e094a029` |
| `runs/seq_1108_shot_2.json` | 1223 | `7f4e442c16c474f402a06af8e0bbfc58ba3c1c29179e0586906657ac41208017` |
| `runs/seq_1108_shot_3.json` | 1202 | `7aeb124244dbb43c284b139c49f7ee5a25df00c937493742484a622dc17ff5d7` |
| `runs/seq_1108_shot_4.json` | 1223 | `fba7c50929297d06bd5b9f808ccaa8d48fded203c51748528dd164ff8eb706ac` |
| `runs/seq_1108_shot_5.json` | 1223 | `a1657e476a8fa054a1df9dba5c892b7c4c660034a4a3fd9a67b744cc326f9fac` |

逐目录 pacer 指纹（18 条）见 `zcode/scripts/_0244_out.md` §2。

## 三、字节-语义差异的重要发现（参数序）

审计中发现仓库存在**两种语义等价但字节不同**的 pacer 参数序：

1. **磁盘历史树**（早期实验管线）：`leak_rate,bucket_cap,leak_interval_us`
2. **seq_1108 决选管线**（submit_batch → upload_config JSON 键序保真链）：`bucket_cap,leak_interval_us,leak_rate`

官方解析器读 key=value 对，二者语义等价（历史成绩均为 leak_rate-first 字节所获）；但 SHA-256 只认字节。**本清单签署的是 seq_1108 管线将实际渲染的字节**——该管线由 `submit_batch.py`（`json.dumps` 保序）→ `upload_config.py`（`json.loads` 保序）→ `render_pacer`（按 dict 序拼接）逐环验证。

**自校验**：工具复刻早期管线的 leak_rate-first 渲染，与磁盘三棵真实树逐字节比对——全部一致（如 `test-anchor-shot2-pert-40x3-37-36-36-r1/1/pacer.txt` sha256 `5ca2a8e6602b4b8a…`）✓。复刻渲染器本身被证明字节精确。

## 四、全量校验矩阵（29 项，全部通过）

| 校验类 | 项数 | 结果 |
|---|---|---|
| 清单文件签名存在性 | 5 | ✓ |
| distinct 树 × 6 目录格式（无 BOM/纯 LF/3 行/无尾换行/timestamp 匹配/参数名+类型+约束如 bucket_cap≥leak_rate） | 18 | ✓ |
| 家族一致性（同名家族各发复合指纹逐位相同，crown 3 发） | 3 | ✓ |
| 复刻渲染器 vs 磁盘真树 | 3 | ✓ |
| **总体** | **29** | **100% PASS** |

## 五、使用协议（给 Lead）

1. **每发提交前**：`python zcode/scripts/audit0244_config_fingerprint.py`，要求退出码 0 且 §1/§3 指纹与本清单逐位一致。
2. 任何指纹漂移 = 清单被改动：**中止提交**，先 `git diff runs/seq_1108_shot_*.json` 定位变更，再重新走 0243 遗憾评估确认新构型仍为预期候选。
3. 注意：`sequential_adaptive_1108.py` 每次运行会**重写** `seq_1108_shot_N.json`（`write_text(json.dumps(...))`）。Python dict 字面量序稳定，正常重写不改变字节；但若该工具被改动，指纹必然漂移——这正是本协议要拦截的场景。
4. 边界：本清单签的是提交清单与渲染树字节；云端落盘最终形态以官方 `format_check_client` 为准（本工具不替代、不触碰）。

## 六、局限

- 指纹清单的「不可篡改」依赖**本审计文档作为可信基准**（本文档由 git 跟踪，任何改动可见）；工具本身不引入第三方签名/HSM，威胁模型是「意外改动/管线漂移」，不是对抗性攻击者。
- 若 Lead 在临场手动改参（例如换 fallback 构型），必须重跑本工具并把新指纹补录到本文档，否则协议失效。
