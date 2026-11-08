# -*- coding: utf-8 -*-
"""
Fix the bracket nesting in tools/zcode_continuous_dispatcher.py
"""

with open('tools/zcode_continuous_dispatcher.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Locate the insertion point after 0382
target = '"""\n            }\n        ,\n    # ---------------- 批次：batch_campaign_0530_dawn'
replacement = '"""\n            }\n        ]\n    },\n    # ---------------- 批次：batch_campaign_0530_dawn'

if target in text:
    text = text.replace(target, replacement, 1)
    with open('tools/zcode_continuous_dispatcher.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Successfully fixed nesting in tools/zcode_continuous_dispatcher.py!")
else:
    print("Target string not found! Looking for variants...")
    idx = text.find('batch_campaign_0530_dawn')
    print(repr(text[idx-60:idx+40]))
