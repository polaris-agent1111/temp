import sys
from pathlib import Path
sys.path.insert(0, ".")
from tools.zcode_continuous_dispatcher import TASK_BATCHES, is_batch_completed

for idx, b in enumerate(TASK_BATCHES):
    comp = is_batch_completed(b)
    print(f"{idx}: {b['batch_id']} ({b['target_time']}) - completed={comp}")
