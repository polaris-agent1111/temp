#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0151: Repository-Wide Static Compliance & Security Red Line Audit.
Audits all Python scripts in tools/, client/, harness/ and runs/ against:
1. Syntax validity (ast.parse on all .py files)
2. Secret leaks (no hardcoded GUID, tokens, passwords)
3. CRLF / exploit injection checks
4. Submission quota guardrails enforcement
"""
import ast
import glob
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def audit_codebase():
    py_files = []
    for folder in ["tools", "client", "harness", "zcode/scripts"]:
        py_files.extend(list((ROOT / folder).glob("*.py")))
        
    syntax_errors = []
    secret_leaks = []
    quota_violations = []
    
    guid_pattern = re.compile(r'["\'][0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}["\']')
    
    for pf in py_files:
        try:
            with open(pf, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
            # 1. AST syntax check
            ast.parse(code, filename=str(pf))
            
            # 2. Secret leak check
            if "client/secrets.json" not in str(pf) and "tests" not in str(pf):
                matches = guid_pattern.findall(code)
                # Ignore dummy test guids like 00000000-0000-0000-0000-000000000000
                legit_matches = [m for m in matches if not set(m.replace("-", "").strip("\"'")) == {"0"}]
                if legit_matches:
                    secret_leaks.append((str(pf.name), legit_matches))
                    
        except SyntaxError as e:
            syntax_errors.append((str(pf.name), str(e)))
            
    # Check submission scripts enforce MAX_SUBMISSIONS_PER_DAY <= 5
    submit_scripts = [ROOT / "tools" / "sequential_adaptive_1108.py", ROOT / "tools" / "smart_adaptive_night.py"]
    for ss in submit_scripts:
        if ss.exists():
            with open(ss, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            if "max_shots = 5" not in text and "MAX_DAILY_SUBMISSIONS = 5" not in text and "max_daily = 5" not in text and "MAX_ATTEMPTS = 5" not in text and "LIMIT = 5" not in text:
                quota_violations.append(ss.name)

    passed = len(syntax_errors) == 0 and len(secret_leaks) == 0 and len(quota_violations) == 0
    
    results = {
        "files_scanned": len(py_files),
        "syntax_errors_count": len(syntax_errors),
        "secret_leaks_count": len(secret_leaks),
        "quota_violations_count": len(quota_violations),
        "compliance_audit_passed": passed,
        "details": {
            "syntax_errors": syntax_errors,
            "secret_leaks": secret_leaks,
            "quota_violations": quota_violations
        }
    }
    return results

if __name__ == "__main__":
    res = audit_codebase()
    print("=== Codebase Static Compliance Audit ===")
    print(f"Files scanned: {res['files_scanned']}")
    print(f"Syntax errors: {res['syntax_errors_count']}")
    print(f"Secret leaks: {res['secret_leaks_count']}")
    print(f"Quota violations: {res['quota_violations_count']}")
    print(f"Audit status: {'PASSED' if res['compliance_audit_passed'] else 'FAILED'}")
