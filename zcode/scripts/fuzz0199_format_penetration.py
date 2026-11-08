#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0199: Local format check penetration and malformed data immunity testing.
Runs boundary test cases against tools/validate_pacer.py and schema constraints.
Verifies rejection of CRLF, missing LF, trailing newlines, out-of-range rates, and invalid timestamps.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tools" / "validate_pacer.py"

def run_penetration_test():
    test_cases = [
        # Valid baseline
        {
            "name": "VALID_BASELINE",
            "content": "[timestamp:1]\npacer_mode:leak_bucket\npacer_config:leak_rate=37,bucket_cap=40,leak_interval_us=4000",
            "expected_valid": True
        },
        # CRLF injection (Red line 4 violation / bug exploit rejection)
        {
            "name": "CRLF_LINE_ENDING",
            "content": "[timestamp:1]\r\npacer_mode:leak_bucket\r\npacer_config:leak_rate=37,bucket_cap=40,leak_interval_us=4000",
            "expected_valid": False
        },
        # Trailing newline at end of file (Disallowed by specification)
        {
            "name": "TRAILING_NEWLINE",
            "content": "[timestamp:1]\npacer_mode:leak_bucket\npacer_config:leak_rate=37,bucket_cap=40,leak_interval_us=4000\n",
            "expected_valid": False
        },
        # Timestamp mismatch (Bin 1 has [timestamp:2])
        {
            "name": "TIMESTAMP_MISMATCH",
            "content": "[timestamp:2]\npacer_mode:leak_bucket\npacer_config:leak_rate=37,bucket_cap=40,leak_interval_us=4000",
            "expected_valid": False
        },
        # Schema constraint violation: bucket_cap < leak_rate
        {
            "name": "CAP_LESS_THAN_RATE",
            "content": "[timestamp:1]\npacer_mode:leak_bucket\npacer_config:leak_rate=41,bucket_cap=40,leak_interval_us=4000",
            "expected_valid": False
        },
        # Invalid mode
        {
            "name": "INVALID_MODE",
            "content": "[timestamp:1]\npacer_mode:hyper_pacer\npacer_config:leak_rate=37,bucket_cap=40,leak_interval_us=4000",
            "expected_valid": False
        },
        # Zero or negative leak rate (Must be positive integer >= 1)
        {
            "name": "ZERO_LEAK_RATE",
            "content": "[timestamp:1]\npacer_mode:leak_bucket\npacer_config:leak_rate=0,bucket_cap=40,leak_interval_us=4000",
            "expected_valid": False
        }
    ]
    
    results = []
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        for tc in test_cases:
            # Create a 6-bin directory structure with bin 1 containing test content
            tree_dir = tmp_path / tc["name"]
            tree_dir.mkdir(parents=True, exist_ok=True)
            for i in range(1, 7):
                bin_dir = tree_dir / str(i)
                bin_dir.mkdir(parents=True, exist_ok=True)
                pacer_file = bin_dir / "pacer.txt"
                if i == 1:
                    # Write exact binary bytes to preserve CRLF or trailing newlines
                    with open(pacer_file, "wb") as f:
                        f.write(tc["content"].encode("utf-8"))
                else:
                    # Normal valid content for other bins
                    content = f"[timestamp:{i}]\npacer_mode:leak_bucket\npacer_config:leak_rate=37,bucket_cap=40,leak_interval_us=4000"
                    with open(pacer_file, "wb") as f:
                        f.write(content.encode("utf-8"))
                        
            # Run validate_pacer.py
            cmd = [sys.executable, str(VALIDATOR), str(tree_dir)]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            is_valid = (proc.returncode == 0)
            
            passed = (is_valid == tc["expected_valid"])
            results.append({
                "case": tc["name"],
                "is_valid": is_valid,
                "expected": tc["expected_valid"],
                "passed": passed
            })
            
    print("=== Task 0199: Format Penetration & Immunity Testing ===")
    for r in results:
        status_str = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status_str}] Case: {r['case']:<25} | Valid: {r['is_valid']} | Expected: {r['expected']}")
        
    all_passed = all(r["passed"] for r in results)
    print(f"\nall_penetration_tests_passed: {all_passed}")
    return results

if __name__ == "__main__":
    run_penetration_test()
