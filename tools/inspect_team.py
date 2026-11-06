import argparse
import json
import sys
import urllib.request

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ap = argparse.ArgumentParser()
ap.add_argument("team", default="大肥鱼")
args = ap.parse_args()

req = urllib.request.Request("http://47.120.64.152:5000/api/leaderboard")
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read().decode("utf-8"))

for s in data['leaderboard']['problems'][0]['submissions']:
    if s['team'] == args.team:
        print(f"=== {s['team']} (Total {len(s['attempts'])} attempts) ===")
        for a in s['attempts']:
            print(f"  {a.get('submitted_at')}: {float(a.get('download_seconds')):8.4f}s")
        break
