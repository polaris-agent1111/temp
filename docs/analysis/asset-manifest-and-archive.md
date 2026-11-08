# 全仓库数字资产指纹清册与答辩材料包归档索引

- **生成时刻**：2026-11-07 02:12 (Asia/Shanghai)
- **执行者**：zcode（任务单 0064）
- **算法**：SHA-256（64 位十六进制，全量非截断）
- **权威数据文件**：`runs/asset_manifest.json`（机器可读，含全部字段；本文档为其人读版与索引）

---

## 一、覆盖范围与豁免说明

| 范围 | 状态 | 说明 |
|---|---|---|
| `configs/` | ✅ 已封存 | 13 个文件（参数 schema + 12 个候选构型 JSON） |
| `tools/` | ✅ 已封存 | 53 个文件（40 个源码/脚本 + 13 个 `__pycache__` 派生缓存） |
| `harness/` | ✅ 已封存 | 7 个文件（6 个源码 + 1 个 `__pycache__` 派生缓存） |
| `question/` | ⚠️ 本地不存在 | 评测配置树位于云端评测机（`/home/openlab/Desktop/question`），按合规红线不触碰云端资产；本地无该目录。答辩涉及该目录时以官方提交回执（`runs/submissions.jsonl` 内 tar.gz 字节数与时间戳）为佐证 |
| `client/`、`runs/.session.pkl`、凭据类文件 | 🚫 有意豁免 | 含 GUID/会话凭据/个人信息，按任务单「不封存个人隐私或密码」与 AGENTS.md 红线排除；敏感文件名扫描（secret/token/session/pkl/password/credential/.env）确认目标三目录内无此类文件 |
| 根目录 `dsh-session-*.zip` | 🚫 有意豁免 | 会话归档，疑似含会话数据，不纳入指纹清册 |
| `docs/`、`runs/` 其余文件 | 📇 精选封存 | 分析文档数量庞大，指纹仅覆盖答辩直接引用的核心材料（§三）；全量盘点见 11/06 版《`docs/资产清单.md`》 |

核心封存合计：**73 个文件，883,489 字节**。`__pycache__/*.pyc` 为派生缓存，指纹仅作完整性参考，答辩一致性以同名 `.py` 源码指纹为准。

---

## 二、核心代码与配置指纹清册（configs / tools / harness）

### 2.1 configs/（13 个）

| 路径 | 大小 (B) | 修改时间 | SHA-256 |
|---|---:|---|---|
| `configs/params_schema.json` | 4066 | 2026-11-05 16:14:37 | `961c0a78d740f747d98f81bfd0dc7493ff41473434c22a56567509d4eb0a2b1f` |
| `configs/test-hybrid-tb-asym40-50-champ.json` | 783 | 2026-11-06 19:17:36 | `e29357d171dca3e839d407e45186da3138c1ed7c762886ba74e8e02066bbf87b` |
| `configs/test-hybrid-tb-asym40-60-champ.json` | 783 | 2026-11-06 19:17:19 | `bfc0953fdd1c8d5cde6d0305dbc8309750391f013cc31db088a7c9d97419b8b6` |
| `configs/test-hybrid-tb3-precise3-champ.json` | 759 | 2026-11-06 16:53:48 | `e321ad05f0f710fb558f7761724ce78240ae730927509820bc5c28a7834613c1` |
| `configs/test-hybrid-tb4-2k-champ.json` | 783 | 2026-11-06 16:37:56 | `ecc1ef8b2e04968372691d2c44be72673730f408a3b88371ecb4cd4a01eaf802` |
| `configs/test-hybrid-tb4-2k-p98M-champ.json` | 783 | 2026-11-06 16:38:08 | `84d24e3876ab23b1b2d2ef85233ecf5989d5aa8ec842908cd4228446fde5b216` |
| `configs/test-hybrid-tb4-fast14-champ.json` | 783 | 2026-11-06 16:57:45 | `0379affea944e9dce4a9068f8e9d8db02c92f576f853316fe4f27a0315bd918f` |
| `configs/test-hybrid-tb4-p100M-p95M-champ.json` | 783 | 2026-11-06 17:03:22 | `1263ef1314d257dfebb7256afa900b2d9190bc606d64a166fa3342f91fb2b820` |
| `configs/test-hybrid-tb4-p100M-p96M-g1200.json` | 783 | 2026-11-06 16:44:47 | `8fe4a123fad19733673d8d4e1f2b2f29bde692377047f063a6700c6ec562e01e` |
| `configs/test-hybrid-tb4-p100M-p96M-g800.json` | 781 | 2026-11-06 16:44:40 | `4902ac961d42c0efa09a02d6a6ff5b762c0e2bf202770920465d24f5f22f9d07` |
| `configs/test-hybrid-tb4-p100M-p97M-champ.json` | 783 | 2026-11-06 17:03:38 | `333b1ac09ca8b5ee7d35d15255886428896f8a54b6ff3a3f5e41c1096967db0f` |
| `configs/test-hybrid-tb4-p98M-champ.json` | 783 | 2026-11-06 16:38:02 | `339b5a1f257c84d19ee8a40e9ffe355fad655677203ac8cc9d82515eee09f98d` |
| `configs/test-origin4-precise2-champ.json` | 619 | 2026-11-06 16:50:23 | `5bce5e5299fa8e18e913c4762426cdd63bafe4c3555206adc99c23b38481456b` |

### 2.2 tools/（53 个，含 13 个派生缓存）

| 路径 | 大小 (B) | 修改时间 | SHA-256 |
|---|---:|---|---|
| `tools/adaptive_submit.py` | 10429 | 2026-11-05 23:14:23 | `4465ec699bc12f1871f008b918352ab2a119e7aaa7bb96c71aaa32c69c730044` |
| `tools/analyze_adaptive.py` | 3251 | 2026-11-05 23:52:03 | `3e73e00bc4f6a8540d708edeed2c0118cfbf21fa7cabf174a9291088b358d4a8` |
| `tools/analyze_hybrid.py` | 1310 | 2026-11-06 15:18:39 | `82fe93b52e9108c69644feb72ad412cd9ee9453c42de9c3b7cc9595f6eba4b80` |
| `tools/asym_leak_researcher.py` | 9044 | 2026-11-07 01:32:38 | `e0af1d0422726fbef54be63f902bbd7ad08ee7ac4775062fa28803cc24be3d1e` |
| `tools/audit_plan.py` | 7083 | 2026-11-06 17:10:24 | `6253d294379923e9b64ac8b5d97be88aaa55a5ad4e492bc7f664f728c65cbf14` |
| `tools/auto_continuous_researcher.py` | 15299 | 2026-11-06 20:12:07 | `2e312fab59a701f822f8b0762a72aeb9b5b81ad5ad659e13aae5d4d3e8e3ebf3` |
| `tools/check_all_configs.py` | 11467 | 2026-11-05 23:22:55 | `c1c603dfa58c2471d09fab73478252087f33b7387a505116cb0d9f8135d615c8` |
| `tools/check_precise_lower_rates.py` | 879 | 2026-11-06 19:16:37 | `33516e57ee5fd9bd19b71e263e20f5977700cf385c80e6fd7ebc12eded6df10c` |
| `tools/config_stats.py` | 12646 | 2026-11-05 16:02:52 | `a44749b1bfda51f09341aa1a823e834843243f3fe52245a1cb1a1c40297feb04` |
| `tools/deep_analysis.py` | 1683 | 2026-11-06 16:35:59 | `7bcfac55ccd7ae8d1ffa31e3c389fde6f839fea25582f69d64223a5addb01e4b` |
| `tools/delta_model.py` | 20625 | 2026-11-06 08:04:50 | `da442ae8f780c8e20d985c85812e3b96728bea6381d673e5a205d0685fd55c76` |
| `tools/dump_docs_clean.py` | 2026 | 2026-11-06 15:33:30 | `035e4266d8e0956144d30692aa4f6042ac7fe4f6f8a6162621722ba52fd5a8d6` |
| `tools/dump_official_md.py` | 3436 | 2026-11-06 15:34:18 | `f00f687bc3c74e35d67ec13c1c75cd731aa4eed7c23f8fd6116ef1c3ceb9629b` |
| `tools/extend_zcode_batches.py` | 11372 | 2026-11-06 23:14:52 | `70ef3cb05cf53a7a59d5b238545ecf493c2852a554e01232650ebba95c4a147b` |
| `tools/extract_docx.py` | 2258 | 2026-11-06 15:33:09 | `2517035a036e2712ca2e6823b68ad1a5f7690c571252d268d6082ef8e6037693` |
| `tools/fit_official_surface.py` | 56924 | 2026-11-06 07:59:50 | `a4fc779ec2f06891ea6f1a242ab9cf1f06622d6e4bf691064e3d4c386e7fd197` |
| `tools/generate_review_manifest.py` | 1139 | 2026-11-06 14:47:25 | `15b9ab7c148ebe434480c0625a0fa1355ef7e77439f8609ca2ef3890964d5f34` |
| `tools/inspect_binaries.py` | 1193 | 2026-11-06 16:22:35 | `d7af061bc7b7d9f7cd34b3b1622dea9f4563447478edd68e4c25bb31322d775b` |
| `tools/inspect_team.py` | 730 | 2026-11-06 14:44:20 | `c350282c4495dd940f98d9c155b21e2071afc21d4863079276a896377b028a8a` |
| `tools/local_official_map.py` | 31442 | 2026-11-05 23:43:49 | `2c16e3673cd53399514641c3fc71953c255be63a54d8bb0fe425c63b63e992b4` |
| `tools/monte_carlo_websearch.py` | 6606 | 2026-11-06 19:36:32 | `e3e95087ca88e9e97e89ae6e42ea3d2ca4f7a9a4d8ba6096a219c105aa356487` |
| `tools/night_submit.py` | 3455 | 2026-11-06 17:10:24 | `24253dcf23e31cd6f334e6e29bdf096f6445dd49b8749e985237bad2e57e0cd7` |
| `tools/official_analysis.py` | 14634 | 2026-11-05 19:31:29 | `cadd202c0a5a9e6d917ce2fdcb79753a24d7783b5f8c5f72132d115dcd1919e2` |
| `tools/official_log.py` | 5478 | 2026-11-05 18:41:44 | `dc4c04bee95770a4bca9ebbf63b269b7d42b381d155f351ad2b7ef0267d5770f` |
| `tools/parse_word.py` | 603 | 2026-11-06 15:33:55 | `9e4ece5f3359f9d21edd27a5780e56f650a7eb7dc681df746b46bbb021f2394d` |
| `tools/probe_matrix.py` | 20788 | 2026-11-06 08:36:29 | `b67f524e7b1916e1dd1081dbc221454aae147c7d47a8f91126e6c19a14d5bab0` |
| `tools/sequential_adaptive_night.py` | 20420 | 2026-11-06 19:33:29 | `0e79a37e3ff441483eb18f36c890ac0087132f6067f3e33d05d6418e8da9a11d` |
| `tools/show_board.py` | 1666 | 2026-11-06 14:43:53 | `0dbfb96956b0984176fd312f6383f883088642e81b0b4dfb9a377651bc54b738` |
| `tools/smart_adaptive_night.py` | 13458 | 2026-11-06 17:10:24 | `76f4642d845ae1b2c0261b834270608dc53f6b89e6c00691007d1308f7b4b0c0` |
| `tools/submit_batch.py` | 3370 | 2026-11-05 21:25:35 | `5e28b3136f88b78bf6fd32c9d05bcbdc19a4e0167106282e97a12282f46b03a9` |
| `tools/summarize_hybrid_stats.py` | 9399 | 2026-11-06 17:12:01 | `0e7e830ec6da486f363ddff7dd3a015a4b8dfb33fc00cf46744798186e9d782b` |
| `tools/test_1core.py` | 3219 | 2026-11-06 09:11:07 | `bf3f11cf4cec6ced0eb4087087fa95deefdb30ab3a7a755d1a7d4ab7122d0a67` |
| `tools/test_asym_tb.py` | 1165 | 2026-11-06 19:17:01 | `f13ea4ec983ba808e9b3f3e879abff5d38e3d04b999c892c3669f5847256b96a` |
| `tools/test_format_limits.py` | 4704 | 2026-11-06 17:10:24 | `9241bd01ba57b1427da090605158e04b9071f421ce292b06c54d8acc1a2e3be1` |
| `tools/test_granularity_limits.py` | 1179 | 2026-11-06 16:41:24 | `8ab3377d089954306f9fa8b0e3d613817dad735061d61d486f1514d6ea2b8ce8` |
| `tools/test_tb_intervals.py` | 1343 | 2026-11-06 16:37:10 | `1fdd0c7f8750918873bf8fc42e02608cbd5d31d816491095b2596fb72fd6e660` |
| `tools/timer_model.py` | 6302 | 2026-11-05 16:37:45 | `f6167e1903103d585e50184dbc351b5f19fa9bdcb83505fbe77fd2546589b938` |
| `tools/validate_pacer.py` | 11806 | 2026-11-05 16:16:07 | `8681e580bfaa3d4f64f629a3094362ecd63d168313eb4b50cf34a2d503fe45e4` |
| `tools/vm_load.py` | 1537 | 2026-11-05 15:17:50 | `9a7bd34dcbf3378048d415ce8c8d167777a4151d5439bca037806687899b8e94` |
| `tools/watch_board.py` | 2678 | 2026-11-05 15:14:35 | `d511916f27fc39fe37e8bee0720713c24e6c4d661e4dab57d3e16fb934ff1f99` |
| `tools/zcode_continuous_dispatcher.py` | 94529 | 2026-11-06 23:17:35 | `91809a067ab852fc91f5b916e59a50bff3350c36bc95cc1d9ca6c75fb4ab3d1a` |
| `tools/__pycache__/adaptive_submit.cpython-314.pyc` | 16310 | 2026-11-05 23:14:23 | `8f26e9e89d3e2c47b74ce642ca55ee3c84f7f3907070406ab35ba6dfa22b7f24` |
| `tools/__pycache__/asym_leak_researcher.cpython-314.pyc` | 11531 | 2026-11-07 01:32:01 | `fe27662cdb4c7763a338ffc37839148994ea7d43323a0f76a54f4d7a8511f76c` |
| `tools/__pycache__/audit_plan.cpython-314.pyc` | 13964 | 2026-11-06 17:11:55 | `6ff7e1c4518e1fee4290a80aeefb591b81156c53ac1ec3f672eb92d027485e51` |
| `tools/__pycache__/delta_model.cpython-314.pyc` | 33918 | 2026-11-06 08:29:57 | `d3ded12a6a1e010bce53ad7543a0219bfd1d19369bf8809cc2304112e119b3fb` |
| `tools/__pycache__/fit_official_surface.cpython-314.pyc` | 95157 | 2026-11-06 07:58:20 | `07a182ca0099a2f923e8c0c47da54f9abfc8078489ce851cccb1191c8f196d79` |
| `tools/__pycache__/local_official_map.cpython-314.pyc` | 46994 | 2026-11-05 23:49:51 | `7f9d420fb504f2d2647e9093c950c652929501355bdb00d5568cac0e7d63f34d` |
| `tools/__pycache__/night_submit.cpython-314.pyc` | 6980 | 2026-11-06 17:11:55 | `1f8c1c3790ba9154e52a0465ee449425b290d6fa570352d1731b9305652770bf` |
| `tools/__pycache__/probe_matrix.cpython-314.pyc` | 34477 | 2026-11-06 08:33:51 | `06a92a79e14436ea38f9a71518e41462892592460d6d89c187c085a8f5d820a8` |
| `tools/__pycache__/smart_adaptive_night.cpython-314.pyc` | 24526 | 2026-11-06 17:11:55 | `8da8655b1ace0dfaf5da4f298b001869998472ca488c07dc7080035c778932c9` |
| `tools/__pycache__/summarize_hybrid_stats.cpython-314.pyc` | 17983 | 2026-11-06 17:12:06 | `84c7d6af0283e7952548d1e4d1872731972d35b20144bd5428a1856d62eb6317` |
| `tools/__pycache__/test_format_limits.cpython-314.pyc` | 7924 | 2026-11-06 17:11:55 | `8f87a6cef6a86b85ecd92a6f06bb92370511826bb6162532f78c58f596677635` |
| `tools/__pycache__/zcode_continuous_dispatcher.cpython-314.pyc` | 88145 | 2026-11-06 23:15:04 | `a00cd70c3c6390f0be49f0b23b4651f708821c314ad26cb614b0a26c514814b9` |

### 2.3 harness/（7 个，含 1 个派生缓存）

| 路径 | 大小 (B) | 修改时间 | SHA-256 |
|---|---:|---|---|
| `harness/analyze.py` | 3721 | 2026-11-05 11:53:40 | `050424a4aa6ecad3977e3a46d9b61befa69c3c4c9220d42dc29e1f43ad6b4843` |
| `harness/import_vm_result.py` | 1618 | 2026-11-05 10:52:39 | `49fc6259d3d054f4c28d0e159f324dedd78e710f2f8b001023c23a30f132c585` |
| `harness/make_report_data.py` | 3359 | 2026-11-05 14:53:17 | `2b6c8bd001c0f0a9e64f7d6e29440a38c8e1d60f946f138e87365b1b5ec7addd` |
| `harness/run_experiment.py` | 9496 | 2026-11-05 11:31:16 | `a00bfb34b92b364ed0c2dfb8748365b62cbbb1cb2d46e4309ab8c3efd01ffed3` |
| `harness/sweep.py` | 2166 | 2026-11-05 10:49:31 | `85b7c4f03b8b5ee5bf0d0d508167eac24c135c1c2c69b03004154e15c57f3674` |
| `harness/upload_config.py` | 2231 | 2026-11-05 12:48:01 | `8fda615a2299508d94c9d0b520caf70777b634fa30d0c0643ca41e1634ff1bf1` |
| `harness/__pycache__/run_experiment.cpython-314.pyc` | 17142 | 2026-11-05 11:31:17 | `d85f264a82cafb0a3387b6d279cfbf6723a3a71b98844d85e90e7cf452e9a55e` |

---

## 三、答辩材料包指纹与引用索引（11 份精选）

| # | 材料 | 用途（答辩时回答什么） | SHA-256 |
|---|---|---|---|
| 1 | `docs/analysis/4plus2-phase-transition-theory.md` | 分段限速架构的相变动力学推导 | `2473e9d005b7d6c9cd0e30dc0981784d10c0224d75153a0563cf3deec2fb1b7d` |
| 2 | `docs/analysis/first-prize-defense-whitepaper.md` | 复测合规自查与四大技术支柱复盘（含前提纠偏） | `9e8d89d3d4954bcc8c5657cac929871d37261472ebec0f0e9a9d4958e076cab8` |
| 3 | `docs/analysis/5shot-battle-retrospective.md` | 11/07 五发实战全流程审计与决策偏差复盘 | `a89cdbfe1e5f493e90255fc690af17259645980a09b26bd57b4540c2e6713ff3` |
| 4 | `docs/analysis/11-07-five-shot-deep-review.md` | 官方五发数据横截面与机理解析（Lead 产出） | `0a5b0dfb3471075738f55f8ec9ec5db1fa8c44daedb21507eccaf5e27c8c1d9d` |
| 5 | `docs/analysis/hybrid-statistical-summary.md` | 37 构型 × 316 场统计总览与选型口径 | `4373a0bdef4cdc7b4afb1dfa3a911ed0d7829b2d4ef917276689254dcc74ebb2` |
| 6 | `docs/analysis/overfitting-and-selection.md` | 测量口径与反过拟合纪律（选型门槛） | `ebc9d18f75976736884fc5fd576b4c4038fa9ab5809c4b4b1292b8b07e331f30` |
| 7 | `docs/analysis/network-queuing-delay-theory.md` | 排队论推导（Drop-tail B=40、4% 余量律依据） | `d0670e43e6fc131a84e8634c6c7cbd6b19ecd8bb07f1b430f068010c26c53085` |
| 8 | `docs/analysis/monte-carlo-collision-simulation.md` | 背景流碰撞蒙特卡洛仿真 | `2667197f93ce6b698ff0ca25978c2d8b2abbb76d2e9a5e9498d43bb354ee0585` |
| 9 | `docs/analysis/variance-decomposition-and-bounds.md` | 方差分解与理论下界 | `5e45bf220ff1f976f5f5fe7aafb8098300de339da53b09472ae79c88fd715094` |
| 10 | `docs/资产清单.md` | 全仓库 3811 文件资产盘点（11/06 版） | `7632ea17126162bd72ce4e3b977d3da74d5dd45e8a5a701fab497c51c69b989d` |
| 11 | `runs/submissions.jsonl` | 官方提交回执原始记录（14 次提交全量） | `0a5ebe9b6220955c2b93a0d4a6e8f7766bc1c628bd7a593ed49434e14812a9e9` |

> 注：材料 2、3、5 的 mtime 在本次封存（02:12:42）之前，指纹有效。若后续文档更新，需重新计算指纹并更新 `runs/asset_manifest.json`。

---

## 四、校验方法

任意一种均可独立复核（在仓库根 `E:\Download\iDSN` 执行）：

```bash
# Git Bash / Linux
sha256sum configs/params_schema.json

# Windows PowerShell
Get-FileHash configs/params_schema.json -Algorithm SHA256

# Python（跨平台）
python -c "import hashlib;print(hashlib.sha256(open('configs/params_schema.json','rb').read()).hexdigest())"
```

比对基准：`runs/asset_manifest.json` 对应条目的 `sha256` 字段。

---

## 五、红线与合规说明

- 本次封存为**只读计算 + 授权路径写入**（`runs/asset_manifest.json`），未修改任何被指纹文件，未删除/移动文件，未做 git 操作；
- 凭据与会话类文件（`client/secrets.json`、`runs/.session.pkl`、根目录会话 zip 等）已按红线排除，清册中无任何密码、token、GUID、个人信息；
- `question/` 涉及云端评测环境，按红线不访问，已如实记录缺失原因（§一）。
