import re
from pathlib import Path

p = Path('tools/zcode_continuous_dispatcher.py')
text = p.read_text(encoding='utf-8')

# 1. Update dispatch_batch
target1 = '''def dispatch_batch(batch: dict) -> None:
    """写入批次任务文件并更新 zcode/STATUS.md 看板。"""
    now_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M")'''

replacement1 = '''def dispatch_batch(batch: dict) -> None:
    """写入批次任务文件并更新 zcode/STATUS.md 看板。"""
    batch["dispatched_at"] = dt.datetime.now()
    now_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M")'''

# 2. Update time-based trigger
target2 = '''            # 如果到达下一个批次的时间窗口，且当前时间 >= 23:00
            if current_batch_idx + 1 < len(TASK_BATCHES):
                next_batch = TASK_BATCHES[current_batch_idx + 1]
                if should_activate_batch(next_batch, now):
                    log(f"时间触发：当前时间 {now:%H:%M} 已达下一批次 {next_batch['target_time']} 窗口，强制推进至 【{next_batch['batch_id']}】！")
                    current_batch_idx += 1
                    dispatch_batch(next_batch)'''

replacement2 = '''            # 如果到达下一个批次的时间窗口，且当前批次已运行至少 25 分钟
            if current_batch_idx + 1 < len(TASK_BATCHES):
                next_batch = TASK_BATCHES[current_batch_idx + 1]
                dispatched_at = cur_batch.get("dispatched_at")
                elapsed_min = (now - dispatched_at).total_seconds() / 60.0 if dispatched_at else 999.0
                if should_activate_batch(next_batch, now) and elapsed_min >= 25.0:
                    log(f"时间触发：当前时间 {now:%H:%M} 已达下一批次 {next_batch['target_time']} 窗口且已执行 {elapsed_min:.1f}m，强制推进至 【{next_batch['batch_id']}】！")
                    current_batch_idx += 1
                    dispatch_batch(next_batch)'''

assert target1 in text, "target1 not found"
assert target2 in text, "target2 not found"

text = text.replace(target1, replacement1).replace(target2, replacement2)
p.write_text(text, encoding='utf-8')
print("Successfully updated tools/zcode_continuous_dispatcher.py")
