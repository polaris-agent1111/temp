import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.zcode_continuous_dispatcher import TASK_BATCHES, is_batch_completed, check_task_status

for idx, b in enumerate(TASK_BATCHES):
    comp = is_batch_completed(b)
    statuses = [f"{t['id']}:{check_task_status(t['id'])}" for t in b['tasks']]
    print(f"{b['batch_id']}: completed={comp}, tasks={statuses}")
