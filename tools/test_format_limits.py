import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "client"))
from vmssh import VmShell

def main():
    vm = VmShell()
    vm.connect()
    
    def check_cfg(mode, cfg_text):
        cmd = (
            "mkdir -p /home/openlab/evals/test_fmt/1 /home/openlab/evals/test_fmt/2 "
            "/home/openlab/evals/test_fmt/3 /home/openlab/evals/test_fmt/4 "
            "/home/openlab/evals/test_fmt/5 /home/openlab/evals/test_fmt/6 && "
            "for i in 1 2 3 4 5 6; do "
            "echo \"[timestamp:$i]\" > /home/openlab/evals/test_fmt/$i/pacer.txt; "
            f"echo \"pacer_mode:{mode}\" >> /home/openlab/evals/test_fmt/$i/pacer.txt; "
            f"echo \"pacer_config:{cfg_text}\" >> /home/openlab/evals/test_fmt/$i/pacer.txt; "
            "done && "
            "cp -r /home/openlab/evals/test_fmt/* /home/openlab/Desktop/question/ && "
            "cd /home/openlab/Desktop && ./format_check_client 2>&1 | tail -5"
        )
        code, out = vm.run(cmd, timeout=30)
        return "通过" in out

    print("Testing token_bucket refill & burst variations:")
    tests = [
        ("token_bucket", "tokens=50,burst=50,token_refill_rate=50,token_refill_interval_us=4000,enable_n_in_flight=1"),
        ("token_bucket", "tokens=60,burst=60,token_refill_rate=60,token_refill_interval_us=4000,enable_n_in_flight=1"),
        ("token_bucket", "tokens=40,burst=40,token_refill_rate=10,token_refill_interval_us=1000,enable_n_in_flight=1"),
        ("token_bucket", "tokens=100,burst=100,token_refill_rate=100,token_refill_interval_us=4000,enable_n_in_flight=1"),
        ("precise_rate_based", "max_pacing_rate=12500000,clock_granularity=2000,enable_n_in_flight=1"),
        ("precise_rate_based", "max_pacing_rate=12500000,clock_granularity=1000,enable_n_in_flight=0"),
        ("precise_rate_based", "max_pacing_rate=12000000,clock_granularity=1000,enable_n_in_flight=1"),
        ("precise_rate_based", "max_pacing_rate=11800000,clock_granularity=1000,enable_n_in_flight=1"),
        ("precise_rate_based", "max_pacing_rate=11600000,clock_granularity=1000,enable_n_in_flight=1"),
        ("precise_rate_based", "max_pacing_rate=13000000,clock_granularity=1000,enable_n_in_flight=1"),
        ("coarse_grained_rate_based", "max_pacing_rate=12500000,clock_granularity=1000,enable_n_in_flight=1"),
        ("origin", "burst_tokens=50,max_pacing_rate=12000000,clock_granularity=1000"),
    ]
    for mode, cfg in tests:
        ok = check_cfg(mode, cfg)
        print(f"[{'PASS' if ok else 'FAIL'}] {mode:25} -> {cfg}")

    vm.close()

if __name__ == "__main__":
    main()
