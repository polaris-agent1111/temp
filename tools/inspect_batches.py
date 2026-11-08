import re
from pathlib import Path

text = Path('tools/zcode_continuous_dispatcher.py').read_text(encoding='utf-8')
for m in re.finditer(r'"batch_id":\s*"([^"]+)",\s*"target_time":\s*"([^"]+)"', text):
    print(m.groups())
