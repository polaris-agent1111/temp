
raw = open('/home/openlab/Desktop/format_check_client', 'rb').read()
chunks = raw.split(b'\x00')

found = []
for c in chunks:
    if len(c) < 4:
        continue
    try:
        s = c.decode('utf-8')
        if any(w in s for w in ['检查', '结果', '参数', 'token', 'pacer', 'leak', 'burst', 'origin', 'precise', 'coarse']):
            found.append(s.strip())
    except Exception:
        continue

print(f"Total found strings: {len(found)}")
for s in found[:200]:
    print("MATCH:", s)
