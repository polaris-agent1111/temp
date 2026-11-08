import sys
from pathlib import Path
sys.path.insert(0, ".")
from tools.zcode_continuous_dispatcher import TASK_BATCHES, dispatch_batch

b = TASK_BATCHES[22]
print(f"Dispatching batch: {b['batch_id']}...")
dispatch_batch(b)
print("Dispatched successfully!")
