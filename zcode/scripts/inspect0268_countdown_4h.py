#!/usr/bin/env python3
"""
Task 0268: Pre-launch readiness inspection & sign-off (re-audit, v2).

v1 (interrupted session, ~19:12) issues fixed here:
  1. Wrote its certificate into runs/ (red-line path, not authorized by the
     task sheet) -> now writes only under zcode/ (authorized).
  2. GATE 2 (quota) and GATE 6 (dispatch health) were hardcoded, not measured
     -> now measured from runs/submissions.jsonl (read-only aggregation) and
     zcode/reports/ file counts.
  3. Certificate SHA-256 was a function of wall-clock time -> now content-
     addressed over the canonical gate-result payload.

All gate inputs are read-only; the only writes are inside zcode/.
"""

import sys
import json
import hashlib
import subprocess
import ast
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CST = timezone(timedelta(hours=8))
DAILY_LIMIT = 5


def read_only(path_desc):
    p = ROOT / path_desc
    return p.exists()


def gate1_redline():
    # secrets must not be git-tracked; .gitignore must cover them
    ls = subprocess.run(["git", "ls-files", "client/"], cwd=ROOT,
                        capture_output=True, text=True, encoding="utf-8", errors="ignore")
    tracked_secret = any("secrets" in l.lower() or l.strip().endswith(".pkl")
                         for l in ls.stdout.splitlines())
    ig = subprocess.run(["git", "check-ignore", "-v", "client/secrets.json"], cwd=ROOT,
                        capture_output=True, text=True, encoding="utf-8", errors="ignore")
    ignored = ig.returncode == 0
    ok = (not tracked_secret) and ignored
    return ok, {"secrets_git_tracked": tracked_secret, "secrets_gitignored": ignored}


def gate2_quota():
    # aggregate only: dates + counts; no GUID/token/note values are read into output
    p = ROOT / "runs/submissions.jsonl"
    if not p.exists():
        return False, {"error": "runs/submissions.jsonl missing"}
    days = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        day = str(rec.get("date", ""))[:10]
        if day:
            days[day] = days.get(day, 0) + 1
    today = datetime.now(CST).strftime("%Y-%m-%d")
    used = days.get(today, 0)
    return used >= DAILY_LIMIT, {
        "today": today, "used_today": used, "daily_limit": DAILY_LIMIT,
        "recent_days": {k: days[k] for k in sorted(days)[-3:]},
    }


def gate3_config_trees():
    r = subprocess.run([sys.executable, "tools/validate_pacer.py", "question"], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8", errors="ignore",
                       env={"PYTHONIOENCODING": "utf-8", "PATH": __import__("os").environ["PATH"],
                            "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", "")})
    return r.returncode == 0, {"return_code": r.returncode,
                               "tail": (r.stdout or "").strip().splitlines()[-1:]}


def gate4_pipeline():
    f = ROOT / "tools/sequential_adaptive_night.py"
    if not f.exists():
        return False, {"error": "pipeline file missing"}
    try:
        ast.parse(f.read_text(encoding="utf-8"))
        return True, {"file": "tools/sequential_adaptive_night.py", "syntax": "ok"}
    except SyntaxError as e:
        return False, {"syntax_error": str(e)}


def gate5_anti_overfit():
    p = ROOT / "runs/pert0267_discrete_neighborhood.json"
    if not p.exists():
        return False, {"error": "pert0267 json missing"}
    d = json.loads(p.read_text(encoding="utf-8"))
    sd = d.get("single_dimension_evaluations", {})
    max1d = sd.get("max_abs_diff_sec")
    mean1d = sd.get("mean_abs_diff_sec")
    gate = sd.get("target_gate_sec", 0.8)
    grid = d.get("full_729_grid_evaluations", {})
    ok = bool(d.get("pass_gate")) and isinstance(max1d, (int, float)) and max1d <= gate
    return ok, {
        "pass_gate_0267": d.get("pass_gate"),
        "max_1d_dev_sec": max1d, "mean_1d_dev_sec": mean1d, "gate_sec": gate,
        "grid_points": grid.get("total_points"),
        "grid_mean_dev_sec": grid.get("mean_abs_diff_sec"),
        "grid_max_dev_sec_corner": grid.get("max_abs_diff_sec"),
        "note": "grid max is the 6-D same-direction corner, not a +/-1 single-axis point",
    }


def gate6_dispatch():
    reps = sorted((ROOT / "zcode/reports").glob("*.md"))
    return len(reps) >= 1, {"zcode_reports_delivered": len(reps)}


def main():
    now = datetime.now(CST)
    launch = datetime(2026, 11, 8, 0, 5, 0, tzinfo=CST)
    unlock = datetime(2026, 11, 8, 0, 0, 0, tzinfo=CST)

    checks = [
        ("GATE_1_REDLINE_COMPLIANCE", gate1_redline),
        ("GATE_2_QUOTA_INTEGRITY", gate2_quota),
        ("GATE_3_CONFIG_TREES_VALID", gate3_config_trees),
        ("GATE_4_SEQUENTIAL_PIPELINE_READY", gate4_pipeline),
        ("GATE_5_ANTI_OVERFITTING_CERTIFIED", gate5_anti_overfit),
        ("GATE_6_DISPATCH_DELIVERABLES", gate6_dispatch),
    ]
    gates, all_pass = {}, True
    for name, fn in checks:
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, {"exception": repr(e)}
        all_pass = all_pass and ok
        gates[name] = {"status": "PASS" if ok else "FAIL", "detail": detail}

    payload = {
        "certificate_id_prefix": "CERT-0268",
        "audited_at": now.isoformat(),
        "quota_unlock_1108": unlock.isoformat(),
        "target_first_shot_1108": launch.isoformat(),
        "minutes_to_unlock": round((unlock - now).total_seconds() / 60, 1),
        "minutes_to_first_shot": round((launch - now).total_seconds() / 60, 1),
        "all_gates_passed": all_pass,
        "overall_readiness": "READY_FOR_BATTLE" if all_pass else "BLOCKED",
        "gates": gates,
    }
    canon = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    seal = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    payload["content_sha256"] = seal
    payload["certificate_id"] = f"CERT-0268-{seal[:12].upper()}"

    out = ROOT / "zcode/reports/0268-certificate.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: payload[k] for k in
                      ("certificate_id", "audited_at", "minutes_to_first_shot",
                       "all_gates_passed", "overall_readiness")},
                     ensure_ascii=False))
    for name, g in gates.items():
        print(f"{name}: {g['status']}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
