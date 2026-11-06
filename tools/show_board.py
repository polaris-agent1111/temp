import argparse
import glob
import json
import sys
import urllib.request

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ap = argparse.ArgumentParser()
ap.add_argument("--live", action="store_true", help="Fetch live from API")
args = ap.parse_args()

data = None
if args.live:
    try:
        req = urllib.request.Request("http://47.120.64.152:5000/api/leaderboard")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        print("[live] Fetched latest snapshot from API")
    except Exception as exc:
        print(f"[warn] Live fetch failed ({exc}), falling back to cached snapshot")

if data is None:
    files = sorted(glob.glob('intel/raw/leaderboard_*.json'))
    if not files:
        print("No leaderboard snapshots found.")
        exit(0)
    latest = files[-1]
    print(f"Reading snapshot: {latest}")
    data = json.load(open(latest, encoding='utf-8'))

subs = data['leaderboard']['problems'][0]['submissions']

board = []
for s in subs:
    team = s['team']
    atts = s.get('attempts', [])
    if not atts:
        continue
    best = min(float(a['download_seconds']) for a in atts)
    last_sub = atts[-1].get('submitted_at', 'N/A')
    board.append((best, team, len(atts), last_sub, [float(a['download_seconds']) for a in atts]))

board.sort(key=lambda x: x[0])

print(f"{'Rank':4s} | {'Team':18s} | {'Best (s)':10s} | {'Attempts':8s} | {'Last Submitted':19s}")
print("-" * 70)
for i, (best, team, att_count, last_sub, scores) in enumerate(board[:15]):
    print(f"{i+1:4d} | {team:18s} | {best:10.4f} | {att_count:8d} | {last_sub:19s}")
