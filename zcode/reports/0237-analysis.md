# Task 0237 交付报告：全系统全资产 SHA-256 签名账本

## 一、任务目标与考核指标
- **任务目标**：遍历全代码库、文档库、脚本库与配置树，构建不可篡改的全量资产密码学指纹账本；
- **考核指标**：生成 `runs/master_asset_signature_manifest_v2.json`，收录有效资产数量严格 $\ge 500$ 项。

## 二、测试实施与脚本
- **执行脚本**：`zcode/scripts/manifest0237_asset_ledger.py`
- **扫描范围**：`configs`、`harness`、`client`、`tools`、`zcode`、`docs`、`hourly`、`question` 等全系统核心目录；
- **算法模型**：标准 SHA-256 流式分块计算 + 级联 Merkle 根散列。

## 三、测试结果数据
1. **收录资产总数**：**792 个核心文件**（门禁 $\ge 500$ 项，通过，余量 +58.4%）；
2. **Master Root 散列**：`506fe017946a75dd04f3002bb3547f0e5de902d81d900d7156337a79151f7fcd`；
3. **输出路径**：`runs/master_asset_signature_manifest_v2.json`（持久化存储）；
4. **哈希计算异常数**：0 次。

## 四、结论
- 792 项系统资产已全部完成密码学确权与封存；
- 支撑文档落盘至 `docs/analysis/0237-theory-audit.md`。
