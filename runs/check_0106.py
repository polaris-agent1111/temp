import json
with open(r'C:\Users\Tadej\.gemini\antigravity\brain\7d78a0e4-e710-4cbc-9f6f-58477f5a7579\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if '0106-analysis.md' in line:
            o = json.loads(line)
            print('Step:', o.get('step_index'), 'Source:', o.get('source'), 'Type:', o.get('type'))
