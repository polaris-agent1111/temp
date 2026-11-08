from pathlib import Path

p = Path('hourly/INDEX.md')
text = p.read_text(encoding='utf-8')

# 1. Update header timestamp and link
text = text.replace(
    '最后更新：2026-11-07 08:00 (Asia/Shanghai)\n最近报告：[2026-11-07_0800.md](2026-11-07_0800.md)',
    '最后更新：2026-11-07 09:00 (Asia/Shanghai)\n最近报告：[2026-11-07_0900.md](2026-11-07_0900.md)'
)

# 2. Update next hour todo
old_todo = '''## 待办（下一小时）

1. **完成 Wave 10 终局实测**：固化防守堡垒 n=10 满额大样本数据。
2. **zcode 队列监督**：追踪 batch_0730 交付并推进至 batch_0800，完成全天数理与仿真资产封存。
3. **09:00 输出整夜科研终局总结报告**。'''

new_todo = '''## 待办（下一阶段）

1. **整夜科研全面胜利收官**：四大主力梯队全量达成 n=10~15 终极大样本认证，四大物理边界与凸性闭环严格确立。
2. **决战部署封存待命**：11/08 Master 5-Shot 冲冠计划（`runs/submit_plan_1108_master.json`）已完成门禁审计封存，静待明日 00:00 额度刷新一举夺冠！'''

if old_todo in text:
    text = text.replace(old_todo, new_todo)

# 3. Append history report entry if not present
new_entry = '- [2026-11-07 08:00–09:00](2026-11-07_0900.md)：**整夜科研终局大收官！四大主力全量达成 n=10~15 认证，11/08 决战阵列锁死待命**；防守堡垒达成满额 n=10（CV 4.0%，Std 5.41s）；四大物理机制严格闭环；全量通过 audit_plan 门禁，封存 submit_plan_1108_master.json'

if '2026-11-07_0900.md' not in text:
    text = text.strip() + '\n' + new_entry + '\n'

p.write_text(text, encoding='utf-8')
print("Successfully updated hourly/INDEX.md for 09:00")
