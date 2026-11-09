# bin · 官方二进制（可选）

这里放的是从竞赛云主机桌面复制来的官方程序，方便通过 GitHub 转到自己的 Linux 机器：

| 文件 | 大小 | 用途 | 注意 |
|---|---:|---|---|
| `competition_question1` | 17 MB | 官方本地仿真评测器 | 需要 Linux x86_64 + root + containernet + Docker + TrafficGenerator/http_server；**不是单文件可移植程序** |
| `format_check_client` | 11 MB | 官方格式检查器 | 硬编码检查 `/home/openlab/Desktop/question` |
| `local_send_client` | 16 MB | 官方提交客户端 | 需要 `--token <团队 GUID>`；**每次成功连上服务端都会消耗当天 5 次额度** |

校验和见 `SHA256SUMS`：

```bash
cd local-eval/bin
sha256sum -c SHA256SUMS
```

## 重要提醒

1. **不要把团队 GUID 写进仓库**。`local_send_client --token ...` 只在命令行临时传入。
2. `competition_question1` 的 `--help` 可以随便跑；真正评测需要 `sudo` 和完整 containernet 环境。先读 `../docs/background/bottleneck-and-40shot-plan.md` 和根目录 `LOCAL_EVAL_GUIDE.md` 第 4 节。
3. 如果你只想要一个轻量仓库，可以在 push 前把 `bin/` 从 git 索引里去掉：
   ```bash
   git rm --cached local-eval/bin/competition_question1 \
                  local-eval/bin/format_check_client \
                  local-eval/bin/local_send_client
   ```
   但这样新克隆的机器就没有二进制了；离线仿真不受影响。
4. 二进制是官方 v0.1.0（`--version` 输出 `V 0.1.0`），如果官方更新，以竞赛平台下载的为准。
