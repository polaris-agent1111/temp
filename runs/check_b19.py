import sys
from pathlib import Path
sys.path.insert(0, ".")
from tools.zcode_continuous_dispatcher import TASK_BATCHES, check_task_status

b = TASK_BATCHES[19]
print("Batch 19:", b['batch_id'])
for t in b['tasks']:
    st = check_task_status(t['id'])
    print(f"Task {t['id']}: status = {st}")
