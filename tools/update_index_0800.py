from pathlib import Path

p = Path('hourly/INDEX.md')
text = p.read_text(encoding='utf-8')

# 1. Update header timestamp and link
text = text.replace(
    '最后更新：2026-11-07 07:00 (Asia/Shanghai)\n最近报告：[2026-11-07_0700.md](2026-11-07_0700.md)',
    '最后更新：2026-11-07 08:00 (Asia/Shanghai)\n最近报告：[2026-11-07_0800.md](2026-11-07_0800.md)'
)

# 2. Update next hour todo
old_todo = '''## 待办（下一小时）

1. **完成 Wave 8 收尾并评估 5.bin 微扰**：汇总 test-crown-pert-37on5 实测数据。
2. **zcode 队列监督**：追踪 batch_0630（0089/0090/0091）交付，07:30 自动推进至 batch_0700。
3. **08:00 输出整点工作报告**。'''

new_todo = '''## 待办（下一小时）

1. **完成 Wave 10 终局实测**：固化防守堡垒 n=10 满额大样本数据。
2. **zcode 队列监督**：追踪 batch_0730 交付并推进至 batch_0800，完成全天数理与仿真资产封存。
3. **09:00 输出整夜科研终局总结报告**。'''

if old_todo in text:
    text = text.replace(old_todo, new_todo)

# 3. Append history report entry if not present
new_entry = '- [2026-11-07 07:00–08:00](2026-11-07_0800.md)：**第九/十波双主力达成 n=15 终极认证，四大物理边界与凸性闭环确立**；稳健主力与皇冠原点齐头并进达成 n=15（SE 仅 2.16s/2.49s，极大值严控在 148s/152s）；严格闭环 4.bin 36 vs 37 vs 38 抛物线凸性极小值证据链与 1.bin 41 包线速天花板；zcode 滚动至 batch_0730'

if '2026-11-07_0800.md' not in text:
    text = text.strip() + '\n' + new_entry + '\n'

p.write_text(text, encoding='utf-8')
print("Successfully updated hourly/INDEX.md for 08:00")
