# 2026 iDSN 决选现场 10 分钟突发排障与备用节点快速接管 SOP

> **生效日期**：2026-11-08 00:00:00 决战日  
> **适用场景**：评测客户端断连、云主机不可达、调度脚本异常中断或网络分区突发故障。

---

## 一、故障等级与处置响应时效

| 故障等级 | 现象描述 | 自动响应机制 | 人工干预时限 |
|:---:|---|---|:---:|
| **P0 致命** | 主节点宿主机失联 / 崩溃 / 网络黑洞 | 触发备用节点冷启动接管 | $\le 15\text{ 秒}$ |
| **P1 严重** | 提交客户端卡死 / 无任何回包超时 | 自动 kill 卡死进程并重置套接字 | $\le 60\text{ 秒}$ |
| **P2 告警** | 出分延迟超 60 分钟 / 平台排队积压 | 启动自适应降级 fallback 策略 | 自动处置 |

---

## 二、三步极速故障转移流程 (Failover in 15s)

### 步骤 1：状态快照秒级确认
备用节点执行快速状态读取，核实已完成提交：
```bash
python tools/sequential_adaptive_1108.py --status
```
检查 `runs/adaptive_night_state.json` 中的 `completed_shots` 计数，杜绝重复提交。

### 步骤 2：配置树与签名一致性验证
```bash
python tools/validate_pacer.py question
python zcode/scripts/audit0244_config_fingerprint.py
```
若出现任何格式或哈希漂移，立即执行一键原子重置：
```bash
python tools/revert_question_backup.py
```

### 步骤 3：自适应流水线无缝续跑
```bash
python tools/sequential_adaptive_1108.py --resume
```
调度器将自动跳过已完成批次，精准从下一发断点继续推进。
