from pathlib import Path

p = Path('hourly/INDEX.md')
text = p.read_text(encoding='utf-8')

# 1. Update timestamp and latest report link
text = text.replace(
    '最后更新：2026-11-07 06:00 (Asia/Shanghai)\n最近报告：[2026-11-07_0600.md](2026-11-07_0600.md)',
    '最后更新：2026-11-07 07:00 (Asia/Shanghai)\n最近报告：[2026-11-07_0700.md](2026-11-07_0700.md)'
)

# 2. Update next hour todo
old_todo = '''## 待办（下一小时）

1. **推进云端漏桶网格扫描**：评估 42-41-40-38-37 极致梯级与邻域置信区间。
2. **zcode 队列监督**：追踪 `batch_0200`（0062/0063/0064）执行，02:30 自动切入 `batch_0230`。
3. **03:00 输出凌晨整点工作报告**。'''

new_todo = '''## 待办（下一小时）

1. **完成 Wave 8 收尾并评估 5.bin 微扰**：汇总 test-crown-pert-37on5 实测数据。
2. **zcode 队列监督**：追踪 batch_0630（0089/0090/0091）交付，07:30 自动推进至 batch_0700。
3. **08:00 输出整点工作报告**。'''

if old_todo in text:
    text = text.replace(old_todo, new_todo)

# 3. Append history report entry if not present
new_entry = '- [2026-11-07 06:00–07:00](2026-11-07_0700.md)：**第八波皇冠微扰 A 构型达成 n=10 大样本认证，严格证明宽阔平坦邻域**；test-crown-pert-40on2 达成 n=10（均值 135.85s，Std 8.63s，CV 6.4%，破除 n=3 小样本偏差，证明皇冠原点平坦邻域无断崖）；zcode 交付 batch_0530 并滚动至 batch_0630'

if '2026-11-07_0700.md' not in text:
    text = text.strip() + '\n' + new_entry + '\n'

p.write_text(text, encoding='utf-8')
print("Successfully updated hourly/INDEX.md")
