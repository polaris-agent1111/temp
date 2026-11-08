import sys
sys.path.insert(0, ".")
from tools.zcode_continuous_dispatcher import TASK_BATCHES

for i, b in enumerate(TASK_BATCHES):
    for j, t in enumerate(b.get("tasks", [])):
        if "id" not in t:
            print(f"Batch {i} ({b.get('batch_id')}) task {j} missing id: {t}")
print("Check completed.")
