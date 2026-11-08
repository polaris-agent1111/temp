# -*- coding: utf-8 -*-
"""Task 0286: CERT-1H — 11/08 first-shot 1-hour war-readiness countersign.

Seven gates, all measured live (no hardcoded declarations):
  G1  five sealed config trees exist, SHA-256 tree digests, name<->content match
  G2  validate_pacer.py offline pass on all five trees (rc=0)
  G3  daily quota ledger from runs/submissions.jsonl (date field only)
  G4  +/-1 neighbourhood plateau from runs/pert0267_discrete_neighborhood.json
  G5  closed-loop pipeline file present + ast.parse syntax ok
  G6  secrets not tracked (git check-ignore + git ls-files)
  G7  local sample support per shot (honest n, mean, CV disclosure)

Certificate = content-addressed SHA-256 of the canonical gate payload,
written to zcode/reports/0286-certificate.json (zcode/ only; no runs/ writes).
"""
import json
import hashlib
import ast
import subprocess
import statistics as st
from pathlib import Path
from datetime import datetime, timedelta, timezone

import sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"
OUT_CERT = ROOT / "zcode" / "reports" / "0286-certificate.json"
OUT_RES = ROOT / "zcode" / "scripts" / "cert0286_results.json"

TZ = timezone(timedelta(hours=8))
now = datetime.now(TZ)
FIRST_SHOT = datetime(2026, 11, 8, 0, 5, 0, tzinfo=TZ)
t_minus_min = (FIRST_SHOT - now).total_seconds() / 60.0

# ---- sealed five-shot list: read from the master certificate (SSOT) ----
master = json.loads((RUNS / "master_battle_ready_certificate.json").read_text(encoding="utf-8"))
FIVE = master["sealed_configurations"]
assert len(FIVE) == 5, FIVE

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()

def parse_pacer(p: Path):
    lines = p.read_text(encoding="utf-8").split("\n")
    mode = lines[1].split(":", 1)[1]
    cfg = lines[2].split(":", 1)[1]
    return lines[0], mode, cfg

def expected_rates(name: str):
    """name -> expected leak_rate list or precise rates, for name<->content check."""
    if "41x2-40-37-36x2" in name:
        return ("leak_rates", [41, 41, 40, 37, 36, 36])
    if "40x3-37-37-36" in name:
        return ("leak_rates", [40, 40, 40, 37, 37, 36])
    if name.startswith("leakc-"):
        parts = name.split("-")
        return ("leak_cap_interval", [int(parts[1]), int(parts[2]), int(parts[3])])
    rates = []
    if "90M" in name:
        rates.append(11250000)
    if "96M" in name:
        rates.append(12000000)
    if "both" in name and rates:
        # "96M-both": every precise_rate_based stage uses the same rate
        return ("precise_rates_both", rates * 2)
    return ("precise_rates", rates)

g1 = []
for name in FIVE:
    tree = RUNS / "configs" / name
    entry = {"name": name, "tree_exists": tree.is_dir()}
    digests = {}
    parsed = []
    if entry["tree_exists"]:
        for k in range(1, 7):
            d = tree / str(k)
            f = d / "pacer.txt"
            digests[f"{k}/pacer.txt"] = sha256_file(f)
            ts, mode, cfg = parse_pacer(f)
            assert ts == f"[timestamp:{k}]", (name, k, ts)
            parsed.append((mode, cfg))
        entry["tree_digest"] = hashlib.sha256(
            json.dumps(digests, sort_keys=True).encode()).hexdigest()
        entry["modes"] = [m for m, _ in parsed]
        # name<->content consistency
        kind, exp = expected_rates(name)
        okc = False
        if kind == "leak_rates":
            got = [int(c.split("leak_rate=")[1].split(",")[0]) for _, c in parsed]
            okc = got == exp
            entry["parsed_leak_rates"] = got
        elif kind == "leak_cap_interval":
            c1 = parsed[0][1]
            lr = int(c1.split("leak_rate=")[1].split(",")[0])
            bc = int(c1.split("bucket_cap=")[1].split(",")[0])
            iv = int(c1.split("leak_interval_us=")[1].split(",")[0])
            okc = [lr, bc, iv] == exp
            entry["parsed_leak_cap_interval"] = [lr, bc, iv]
        elif kind == "precise_rates_both":
            got = [int(c.split("max_pacing_rate=")[1].split(",")[0])
                   for m, c in parsed if "max_pacing_rate" in c]
            okc = got == exp
        elif kind == "precise_rates":
            got = [int(c.split("max_pacing_rate=")[1].split(",")[0])
                   for m, c in parsed if "max_pacing_rate" in c]
            okc = all(r in got for r in exp) and len(got) == len(exp)
            entry["parsed_precise_rates"] = got
            entry["tb_stages"] = [c for m, c in parsed if m == "token_bucket"]
        entry["name_content_match"] = okc
    g1.append(entry)

# G2: offline validator
g2 = []
for name in FIVE:
    r = subprocess.run([sys.executable, "-I", "tools/validate_pacer.py",
                        str(RUNS / "configs" / name)],
                       capture_output=True, text=True, cwd=str(ROOT), timeout=120)
    g2.append({"name": name, "rc": r.returncode,
               "tail": (r.stdout.strip().splitlines() or [""])[-1][:120]})

# G3: quota ledger (date field only)
cnt = {}
with (RUNS / "submissions.jsonl").open(encoding="utf-8") as f:
    for line in f:
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        cnt[d.get("date", "?")] = cnt.get(d.get("date", "?"), 0) + 1
recent = {k: cnt[k] for k in sorted(cnt)[-3:]}
g3 = {"recent_daily_counts": recent, "today_1107": cnt.get("2026-11-07", 0),
      "quota_1108_fresh": cnt.get("2026-11-08", 0) == 0}

# G4: neighbourhood plateau (read 0267 artifact)
p267 = RUNS / "pert0267_discrete_neighborhood.json"
raw267 = json.loads(p267.read_text(encoding="utf-8"))
max_dev = raw267.get("single_dimension_evaluations", {}).get("max_abs_diff_sec")
g4 = {"pass_gate": raw267.get("pass_gate"),
      "plateau_certified": raw267.get("plateau_flatness_certified"),
      "max_abs_diff_sec": max_dev, "threshold_s": 0.8}

# G5: pipeline file + syntax
pipe = ROOT / "tools" / "sequential_adaptive_night.py"
g5 = {"exists": pipe.is_file()}
if g5["exists"]:
    try:
        ast.parse(pipe.read_text(encoding="utf-8"))
        g5["syntax_ok"] = True
    except SyntaxError:
        g5["syntax_ok"] = False

# G6: secrets hygiene (no content read)
gi = subprocess.run(["git", "check-ignore", "client/secrets.json"],
                    capture_output=True, text=True, cwd=str(ROOT))
ls = subprocess.run(["git", "ls-files", "client/"],
                    capture_output=True, text=True, cwd=str(ROOT))
g6 = {"check_ignore_rc": gi.returncode,
      "secrets_tracked": any("secrets" in l for l in ls.stdout.splitlines())}

# G7: local sample support per shot (honest disclosure)
rows = []
with (RUNS / "results.jsonl").open(encoding="utf-8") as f:
    for line in f:
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("valid") and not d.get("tag", "").startswith("load-"):
            rows.append(d)
FAM = {"1108-A1-hybrid-champ-90M-96M": "1108-A1-hybrid-champ-90M-96M",
       "1108-A2-hybrid-champ-96M-both": "1108-A2-hybrid-champ-96M-both",
       "test-leak-asym-41x2-40-37-36x2-r1": "41x2-40-37-36x2-",
       "test-leak-asym-40x3-37-37-36-r1": "40x3-37-37-36-",
       "leakc-36-40-4000": "leakc-36-40-4000"}
g7 = []
for name, frag in FAM.items():
    ts = [d["total_seconds"] for d in rows if frag in d.get("tag", "")]
    rec = {"name": name, "n_exact_tag": len(ts)}
    if len(ts) >= 2:
        rec.update(mean=round(st.mean(ts), 3), std=round(st.pstdev(ts), 3),
                   cv_pct=round(100 * st.pstdev(ts) / st.mean(ts), 2))
    elif len(ts) == 1:
        rec.update(mean=ts[0])
    g7.append(rec)

gates_pass = (all(e.get("tree_exists") and e.get("name_content_match", False) for e in g1)
              and all(r["rc"] == 0 for r in g2)
              and g3["today_1107"] == 5 and g3["quota_1108_fresh"]
              and g4["pass_gate"] is True and (g4["max_abs_diff_sec"] or 9) <= 0.8
              and g5["exists"] and g5.get("syntax_ok")
              and gi.returncode == 0 and not g6["secrets_tracked"])

payload = {
    "cert_type": "CERT-1H",
    "task": "0286",
    "issued_at": now.strftime("%Y-%m-%d %H:%M:%S %Z").replace("%Z", "Asia/Shanghai"),
    "t_minus_minutes_to_first_shot": round(t_minus_min, 1),
    "first_shot_window": "2026-11-08 00:05:00 Asia/Shanghai",
    "sealed_configurations": FIVE,
    "gates": {"G1_trees_digest_name_match": g1, "G2_validate_pacer": g2,
              "G3_quota_ledger": g3, "G4_neighbourhood": g4, "G5_pipeline": g5,
              "G6_secrets_hygiene": g6, "G7_local_support": g7},
    "verdict": "READY_FOR_FIRST_SHOT" if gates_pass else "NOT_READY",
    "scope_note": ("仅声明上述门禁在审计时点为真；不构成对出分水平的承诺；"
                   "官方口径为多次复测取均值。runs/countdown_*_certificate.json "
                   "为历史 v1 残留，未经本会话复核，不作为依据。"),
}
cert_hash = hashlib.sha256(
    json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
cert = {"certificate_id": f"CERT-0286-1H-{cert_hash[:16].upper()}",
        "payload_sha256": cert_hash, "payload": payload}
OUT_CERT.write_text(json.dumps(cert, ensure_ascii=False, indent=1), encoding="utf-8")
OUT_RES.write_text(json.dumps(cert, ensure_ascii=False, indent=1), encoding="utf-8")

print("T-minus:", round(t_minus_min, 1), "min to 11/08 00:05")
print("G1 trees:", all(e.get("tree_exists") for e in g1),
      "name-content:", all(e.get("name_content_match", False) for e in g1))
for e in g1:
    print("  ", e["name"], e.get("tree_digest", "MISSING")[:16], e.get("name_content_match"))
print("G2 validate rc:", [r["rc"] for r in g2])
print("G3 quota:", g3["recent_daily_counts"], "1108 fresh:", g3["quota_1108_fresh"])
print("G4:", g4)
print("G5:", g5, "G6 rc/track:", gi.returncode, g6["secrets_tracked"])
print("G7 local support:")
for r in g7:
    print("  ", r)
print("VERDICT:", payload["verdict"])
print("CERT:", cert["certificate_id"])
