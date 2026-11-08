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
    'max_pacing_rate=12000000,clock_granularity=800,enable_n_in_flight=1',
    'max_pacing_rate=12000000,clock_granularity=1200,enable_n_in_flight=1',
    'max_pacing_rate=12000000,clock_granularity=900,enable_n_in_flight=1',
    'max_pacing_rate=12000000,clock_granularity=1100,enable_n_in_flight=1',
]
for cfg in configs:
    with open('/home/openlab/Desktop/question/6/pacer.txt', 'wb') as f:
        f.write(f'[timestamp:6]\\npacer_mode:precise_rate_based\\npacer_config:{cfg}'.encode('utf-8'))
    out = subprocess.getoutput('cd /home/openlab/Desktop && ./format_check_client')
    passed = '通过' in out
    print(f'cfg: {cfg[:45]}... -> PASS={passed}')
"""
        vm.run("cat << 'EOF' > /tmp/test_gran.py\n" + remote_script + "\nEOF\n", timeout=20)
        code, out = vm.run("python3 /tmp/test_gran.py", timeout=30)
        print(out)
    finally:
        vm.close()

if __name__ == "__main__":
    main()
