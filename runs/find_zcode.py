import json
from pathlib import Path

transcript_path = Path(r"C:\Users\Tadej\.gemini\antigravity\brain\7d78a0e4-e710-4cbc-9f6f-58477f5a7579\.system_generated\logs\transcript.jsonl")
if transcript_path.exists():
    with open(transcript_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if "0106" in line:
                try:
                    obj = json.loads(line)
                    print(f"Step {obj.get('step_index')}: type={obj.get('type')} tools={[t['name'] for t in obj.get('tool_calls', [])]}")
                except Exception as e:
                    print(f"Error line {idx}: {e}")
