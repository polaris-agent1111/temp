import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "client"))
from vmssh import VmShell

def main():
    vm = VmShell()
    vm.connect()
    try:
        remote_script = """import subprocess
configs = [
    'tokens=40,burst=60,token_refill_rate=40,token_refill_interval_us=4000,enable_n_in_flight=1',
    'tokens=40,burst=60,token_refill_rate=38,token_refill_interval_us=4000,enable_n_in_flight=1',
    'tokens=40,burst=50,token_refill_rate=40,token_refill_interval_us=4000,enable_n_in_flight=1',
]
for cfg in configs:
    with open('/home/openlab/Desktop/question/1/pacer.txt', 'wb') as f:
        f.write(f'[timestamp:1]\\npacer_mode:token_bucket\\npacer_config:{cfg}'.encode('utf-8'))
    out = subprocess.getoutput('cd /home/openlab/Desktop && ./format_check_client')
    passed = '通过' in out
    print(f'cfg: {cfg[:45]}... -> PASS={passed}')
"""
        vm.run("cat << 'EOF' > /tmp/test_asym.py\n" + remote_script + "\nEOF\n", timeout=20)
        code, out = vm.run("python3 /tmp/test_asym.py", timeout=30)
        print(out)
    finally:
        vm.close()

if __name__ == "__main__":
    main()
