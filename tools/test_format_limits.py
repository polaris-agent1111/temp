import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "client"))
from vmssh import VmShell

def main():
    vm = VmShell()
    vm.connect()
    
    def check_cfg(cfg_text):
        cmd = (
            "mkdir -p /home/openlab/evals/test_fmt/1 /home/openlab/evals/test_fmt/2 "
            "/home/openlab/evals/test_fmt/3 /home/openlab/evals/test_fmt/4 "
            "/home/openlab/evals/test_fmt/5 /home/openlab/evals/test_fmt/6 && "
            "for i in 1 2 3 4 5 6; do "
            "echo \"[timestamp:$i]\" > /home/openlab/evals/test_fmt/$i/pacer.txt; "
            "echo \"pacer_mode:token_bucket\" >> /home/openlab/evals/test_fmt/$i/pacer.txt; "
            f"echo \"pacer_config:{cfg_text}\" >> /home/openlab/evals/test_fmt/$i/pacer.txt; "
            "done && "
            "cp -r /home/openlab/evals/test_fmt/* /home/openlab/Desktop/question/ && "
            "cd /home/openlab/Desktop && ./format_check_client 2>&1 | tail -5"
        )
        code, out = vm.run(cmd, timeout=30)
        lines = [line.strip() for line in out.strip().splitlines() if line.strip()]
        last_line = lines[-1] if lines else ""
        return "通过" in out, last_line

    print("Testing token_bucket limits:")
    for b in [40, 50, 60, 80, 100, 200]:
        ok, last = check_cfg(f"tokens={b},burst={b},token_refill_rate=40,token_refill_interval_us=4000,enable_n_in_flight=1")
        print(f"burst={b}: ok={ok} -> {last}")

    vm.close()

if __name__ == "__main__":
    main()
