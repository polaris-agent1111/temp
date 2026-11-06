status: done
priority: 4
assignee: zcode
created: 2026-11-05 22:55

# 0033 — 杂活：全量配置快照格式校验

## 为什么

`pacer.txt` 一旦有 CRLF 或末尾换行，官方解析就会失败（我们踩过这个坑，白扔了两次提交）。历史上 `runs/configs/` 里已经有几百份快照，需要一次全量体检，确保「今天还能用的配置」都是干净的。

## 任务

产出 `tools/check_all_configs.py` + `report/配置全量校验.md`：

1. 遍历 `runs/configs/**/pacer.txt`（可能几百个文件），逐个检查：
   - 是否 UTF-8 无 BOM
   - 是否含 `\r`（CRLF）
   - 是否以换行结尾（应为**无**末尾换行）
   - 字节数是否合理（约 90–120 字节）
   - 三行结构：`[timestamp:N]` / `pacer_mode:<模块>` / `pacer_config:k=v,...`
   - `timestamp` 是否等于所在目录号（1–6）
   - 六个目录的 `pacer_config` 是否一致（同一 tag 内）
   - `bucket_cap >= leak_rate`、`leak_interval_us >= 4000`
2. **输出**：合格/不合格统计 + 不合格清单（路径 + 具体问题）。
3. **修复建议**：对不合格的，给出「是否可以直接用 `harness/run_experiment.py` 重新生成」的判断（不要实际改文件）。
4. 脚本要能一条命令重跑。

## 禁止

不修改任何 `pacer.txt`；不上传；不提交；不碰云主机。

## 交付

`tools/check_all_configs.py` + `report/配置全量校验.md` + `zcode/reports/0033-configcheck.md`。
