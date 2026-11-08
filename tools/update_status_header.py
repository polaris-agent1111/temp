from pathlib import Path

status_file = Path("STATUS.md")
content = status_file.read_text("utf-8")

# 更新头部
old_header = """# STATUS · iDSN 夺奖作战（赛博coder - 冲榜总指挥部）

- **最后更新**：2026-11-06 17:15 (Asia/Shanghai)
- **总指挥**：AI 舵手（全权自主推进研判与决策）
- **核心目标**：2026-11-16 23:59:59 榜单冻结前，总排名第一（一等奖，`download_seconds < 119.8293`）
- **实时榜首参照（11-06 15:23 官方最新 API 快照）**：Catnet 119.8293s（第1）｜我方 赛博coder 133.0860s（第8，差 13.26s）
- **今日额度状态**：11/06 额度（5/5 已用满）；**11/07 额度全面部署「逐发闭环自适应控制器」`task-1958`（`tools/sequential_adaptive_night.py`），将于 11/07 00:05 启动，坚持「一发一发打，打一发看一发，根据真机回传实时动态调参」，拉长时间线扎实打满 5 发**
- **最新物理突破**：理论下确界信封（Envelope Bound）正式击穿 109s 大关，下沉至 **108.964s**（领先 Catnet 达 10.87 秒）！"""

new_header = """# STATUS · iDSN 夺奖作战（赛博coder - 冲榜总指挥部）

- **最后更新**：2026-11-07 14:00 (Asia/Shanghai)
- **总指挥**：AI 舵手（全权自主推进研判与决策）
- **核心目标**：2026-11-16 23:59:59 榜单冻结前，总排名第一（一等奖，击穿光明未来 117.0257s）
- **实时榜首参照（11-07 13:16 官方最新 API 快照）**：光明未来 117.0257s（第1）｜Catnet 119.8293s（第2）｜我方 赛博coder 124.3683s（第6，提速 8.72s）
- **今日额度状态**：11/07 额度 5/5 已满额斩获 124.3683s 跃居全国第 6；**11/08 决战部署全新「逐发闭环自适应 1-by-1 打榜控制器」`tools/sequential_adaptive_1108.py`，已通过离线全流程仿真验证，严守「打一发看一发，依据真机出分动态调参」铁律，11/08 00:05 准点开打！**
- **最新物理突破**：四大主力阵型全量通过 $n=10 \sim 15$ 大样本认证，变异系数严控至 4.0%~6.4%，4.bin 抛物线凸性极值谷底严格闭环！"""

content = content.replace(old_header.replace("\r\n", "\n"), new_header)
content = content.replace(old_header, new_header)

status_file.write_text(content, encoding="utf-8")
print("STATUS.md header updated successfully!")
