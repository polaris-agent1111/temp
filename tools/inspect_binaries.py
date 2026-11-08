import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "client"))
from vmssh import VmShell

def main():
    vm = VmShell()
    vm.connect()
    
    vm_script = r"""
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
"""
    tmp_local = ROOT / "runs" / "inspect_tmp.py"
    tmp_local.write_text(vm_script, encoding="utf-8")
    vm.push_file(tmp_local, "/home/openlab/inspect_bin.py")
    code, out = vm.run("python3 /home/openlab/inspect_bin.py", timeout=30)
    
    out_file = ROOT / "runs" / "format_check_analysis.txt"
    out_file.write_text(out, encoding="utf-8", errors="replace")
    print(f"Saved {len(out)} chars to {out_file}")
    vm.close()

if __name__ == "__main__":
    main()
