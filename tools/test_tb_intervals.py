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
    ('origin', 'burst_tokens=40,max_pacing_rate=12500000,clock_granularity=1000'),
    ('origin', 'burst_tokens=40,max_pacing_rate=12000000,clock_granularity=1000'),
    ('origin', 'burst_tokens=40,max_pacing_rate=11500000,clock_granularity=1000'),
    ('precise_rate_based', 'max_pacing_rate=12250000,clock_granularity=1000,enable_n_in_flight=1'),
    ('precise_rate_based', 'max_pacing_rate=12125000,clock_granularity=1000,enable_n_in_flight=1'),
]
for mode, cfg in configs:
    with open('/home/openlab/Desktop/question/1/pacer.txt', 'wb') as f:
        f.write(f'[timestamp:1]\\npacer_mode:{mode}\\npacer_config:{cfg}'.encode('utf-8'))
    out = subprocess.getoutput('cd /home/openlab/Desktop && ./format_check_client')
    passed = '通过' in out
    print(f'{mode}: {cfg[:45]}... -> PASS={passed}')
"""
        vm.run("cat << 'EOF' > /tmp/test_origin_precise.py\n" + remote_script + "\nEOF\n", timeout=20)
        code, out = vm.run("python3 /tmp/test_origin_precise.py", timeout=30)
        print(out)
    finally:
        vm.close()

if __name__ == "__main__":
    main()
