import os

with open("tools/zcode_continuous_dispatcher.py", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find("current_batch_idx = 0")
if idx != -1:
    end_marker = 'log(f"'
    end_idx = text.find(end_marker, idx)
    replacement = """current_batch_idx = -1
    for idx, b in enumerate(TASK_BATCHES):
        if not is_batch_completed(b):
            current_batch_idx = idx
            break
            
    if current_batch_idx == -1:
        log("所有登记批次内部任务已全部 status: done！静候明日决战。")
        return 0
        
    cur_batch = TASK_BATCHES[current_batch_idx]
    """
    text = text[:idx] + replacement + text[end_idx:]
    with open("tools/zcode_continuous_dispatcher.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("Successfully patched dispatcher main() logic.")
else:
    print("Target current_batch_idx = 0 not found.")
