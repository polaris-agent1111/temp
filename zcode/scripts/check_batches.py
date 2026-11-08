import re

with open('tools/zcode_continuous_dispatcher.py', 'r', encoding='utf-8') as f:
    text = f.read()

batches = re.findall(r'"batch_id":\s*"([^"]+)"', text)
print("Total batches:", len(batches))
print("Batches tail:", batches[-10:])
