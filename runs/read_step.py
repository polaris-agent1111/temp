import json
with open(r'C:\Users\Tadej\.gemini\antigravity\brain\7d78a0e4-e710-4cbc-9f6f-58477f5a7579\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        o = json.loads(line)
        if o.get('step_index') == 3466:
            print('Source:', o.get('source'), 'Type:', o.get('type'))
            print('Content:', o.get('content')[:200])
