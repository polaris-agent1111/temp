import urllib.request, json

url = "http://47.120.64.152:5000/api/leaderboard"
try:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print("Leaderboard fetch success!")
        for p in (data.get('leaderboard') or {}).get('problems') or []:
            for s in (p.get('submissions') or [])[:10]:
                print(f"Rank {s.get('rank')}: {s.get('team')} - {s.get('min_download_seconds')}s ({s.get('attempts_count')} submissions)")
except Exception as e:
    print("Leaderboard fetch error:", e)
