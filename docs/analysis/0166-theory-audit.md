# 0166 理论审计：11/08 决战全量配置参数 SHA-256 校验与防篡改白盒封存

## 1. 封存架构与白盒规范
为保证明日（11/08）打靶全流程的确定性与不可篡改性，对决战四大候选方案进行白盒构建并计算密码学哈希清单：
1. **Steady Champion** (`1108-shot-steady-40x3-37-36-36`)：首发锚定；
2. **Crown Fusion** (`1108-shot-crown-41x2-40-37-36x2`)：主攻破局；
3. **Crown Plateau A** (`1108-shot-crown-pert-40on2`)：中度扰动稳定；
4. **Defense Fortress** (`1108-shot-fortress-40x4-37x2`)：恶劣拥塞兜底。

## 2. 格式规范与哈希清单
每个方案包含完整 1~6 级目录树，每级目录下的 `pacer.txt` 严格满足：
- 无 BOM UTF-8 编码，LF 换行，末尾无换行；
- 恰好 3 行，第一行为 `[timestamp:N]`，第二行为 `pacer_mode:leak_bucket`，第三行为 `pacer_config:...`；
- 严格遵循 `configs/params_schema.json` 约束：当 `leak_rate=41` 时 `bucket_cap=41`，满足 `bucket_cap >= leak_rate`。

## 3. 校验与封存结果
运行 `zcode/scripts/seal0166_sha256_tree_verification.py`：
- 四大方案 24 个 `pacer.txt` 全部通过 `tools/validate_pacer.py` 严格校验（**通过率 100%**）；
- 全量指纹固化写入 `runs/sealed_1108_manifest.json`；
- 确保在 11/08 决战前零篡改、零漂移。
