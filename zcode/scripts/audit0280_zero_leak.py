#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0280: pre-launch full-chain security audit & zero-leak verification.

READ-ONLY audit: nothing in the repo is modified, nothing is submitted, no
credential material is ever printed (matches are masked to file:line:pattern).

Checks:
  G1  credential files untracked by git (client/secrets.json, runs/.session.pkl,
      plus any tracked *.pkl / *.session / *.key / *.pem)
  G2  .gitignore actually ignores those paths (git check-ignore)
  G3  tracked-file content scan for credential-shaped strings
      (git grep on the published surface only; pacing-module vocabulary such
      as token_bucket / token_refill / burst_tokens is whitelisted as
      non-credential)
  G4  working-tree scan of publishable dirs (zcode/, docs/, report/, hourly/,
      tools/, harness/, configs/) for the same patterns, including untracked
      files; runs/ and client/secrets.json are never read
  G5  daily submission quota: entries in runs/submissions.jsonl dated today
      must be <= 5 (only date/at fields are read)
  G6  zcode task channel hygiene: reports/requests/inbox contain no GUID-
      shaped strings (the channel is the most likely accidental publish path)

Certificate: sha256 over the canonical JSON of all check results
(content-addressed, 0268 style).  The certificate signs the CHECK RESULTS,
not wall-clock duration.
"""
import sys
import os
import re
import json
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
TODAY = "2026-11-07"

GUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                     r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
HEX32_RE = re.compile(r"\b[0-9a-f]{32}\b")
ASSIGN_RE = re.compile(
    r"(?i)\b(password|passwd|api[_-]?key|secret|bearer)\b\s*[:=]")
# pacing-module vocabulary that merely contains "token"/"secret"-like words
PACING_WHITELIST = re.compile(
    r"(?i)token_bucket|token_refill|burst_tokens|\"tokens\"|'tokens'|"
    r"\btokens\s*[:=]|leak_bucket|pacer|pacing")

RESULTS = {}


def run(cmd):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def g1_untracked_secrets():
    tracked = run(["git", "ls-files"]).stdout.splitlines()
    bad = [f for f in tracked
           if f in ("client/secrets.json", "runs/.session.pkl")
           or re.search(r"\.(pkl|session|key|pem)$", f, re.I)]
    return {"tracked_violations": bad, "pass": not bad}


def g2_gitignore():
    # runs/ is PARTIALLY tracked by design (configs/plans tracked; credentials,
    # logs, jsonl, browser/ ignored) -> only the two credential paths are
    # pass/fail criteria; runs/ whole-dir is reported informationally.
    checks = {}
    for p in ("client/secrets.json", "runs/.session.pkl",
              "runs/browser/", "runs/trit_token.json"):
        r = run(["git", "check-ignore", "-q", p])
        checks[p] = (r.returncode == 0)
    info_runs = run(["git", "check-ignore", "-q", "runs/"]).returncode == 0
    return {"ignored": checks, "runs_whole_dir_ignored": info_runs,
            "pass": all(checks.values())}


def scan_lines(lines, source):
    hits = []
    for i, line in enumerate(lines, 1):
        if PACING_WHITELIST.search(line):
            continue
        for name, rx in (("GUID", GUID_RE), ("HEX32", HEX32_RE),
                         ("CRED_ASSIGN", ASSIGN_RE)):
            m = rx.search(line)
            if m:
                # repo precedent (audit0151): all-zero dummy GUID is not a leak
                if name == "GUID" and set(
                        m.group(0).replace("-", "")) == {"0"}:
                    continue
                hits.append({"file": source, "line": i, "pattern": name})
    return hits


def g3_tracked_content():
    files = [f for f in run(["git", "ls-files"]).stdout.splitlines()
             if re.search(r"\.(md|py|json|txt|jsonl|csv|sh|yml|yaml|toml|cfg|ini)$",
                          f, re.I)]
    hits = []
    for f in files:
        r = run(["git", "show", f"HEAD:{f}"])
        if r.returncode != 0:
            r = run(["git", "show", f":{f}"])
            if r.returncode != 0:
                continue
        hits.extend(scan_lines(r.stdout.splitlines(), f))
    return {"files_scanned": len(files), "hits": hits, "pass": not hits}


def g4_working_tree():
    hits = []
    scanned = 0
    for d in ("zcode", "docs", "report", "hourly", "tools", "harness",
              "configs"):
        base = ROOT / d
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.stat().st_size > 5_000_000:
                continue
            if p.suffix.lower() not in (".md", ".py", ".json", ".txt",
                                        ".jsonl", ".csv", ".sh", ".yml",
                                        ".yaml", ".toml", ".cfg", ".ini"):
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            scanned += 1
            hits.extend(scan_lines(
                text.splitlines(), str(p.relative_to(ROOT)).replace("\\", "/")))
    return {"files_scanned": scanned, "hits": hits, "pass": not hits}


def g5_quota():
    p = ROOT / "runs" / "submissions.jsonl"
    if not p.exists():
        return {"pass": True, "today_count": 0, "note": "file missing"}
    today = 0
    total = 0
    with p.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            total += 1
            if str(rec.get("date", "")).startswith(TODAY):
                today += 1
    return {"today_count": today, "total_records": total,
            "pass": today <= 5}


def g6_zcode_channel():
    hits = []
    scanned = 0
    for d in ("zcode/reports", "zcode/requests", "zcode/inbox"):
        base = ROOT / d
        if not base.exists():
            continue
        for p in base.glob("*.md"):
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            scanned += 1
            hits.extend(scan_lines(
                text.splitlines(), str(p.relative_to(ROOT)).replace("\\", "/")))
    return {"files_scanned": scanned, "hits": hits, "pass": not hits}


def main():
    print("=== Task 0280: pre-launch zero-leak audit (READ-ONLY) ===")
    print(f"workspace: {ROOT.name}  utc-now: "
          f"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")

    RESULTS["G1_secrets_untracked"] = g1_untracked_secrets()
    RESULTS["G2_gitignore_covers"] = g2_gitignore()
    RESULTS["G3_tracked_content_clean"] = g3_tracked_content()
    RESULTS["G4_worktree_content_clean"] = g4_working_tree()
    RESULTS["G5_daily_quota_within_5"] = g5_quota()
    RESULTS["G6_zcode_channel_clean"] = g6_zcode_channel()

    for k, v in RESULTS.items():
        extra = ""
        if "hits" in v:
            extra = f", hits={len(v['hits'])}"
            if v["hits"]:
                # masked listing: file:line:pattern only, never content
                for h in v["hits"][:12]:
                    extra += f"\n      {h['file']}:{h['line']}:{h['pattern']}"
                if len(v["hits"]) > 12:
                    extra += f"\n      ... +{len(v['hits'])-12} more"
        if "ignored" in v:
            extra = f", {v['ignored']}"
        if "today_count" in v:
            extra = f", today={v['today_count']}"
        if "tracked_violations" in v:
            extra = f", violations={v['tracked_violations']}"
        print(f"  {k}: {'PASS' if v['pass'] else 'FAIL'}{extra}")

    all_pass = all(v["pass"] for v in RESULTS.values())
    payload = {
        "task": "0280",
        "generated_utc": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"),
        "all_pass": all_pass,
        "results": RESULTS,
    }
    digest = hashlib.sha256(json.dumps(
        payload, sort_keys=True, ensure_ascii=False,
        default=str).encode("utf-8")).hexdigest()
    cert_id = "ZERO-LEAK-" + digest[:16].upper()
    print(f"\nALL-CHECKS: {'PASS (6/6)' if all_pass else 'FAIL'}")
    print(f"certificate id: {cert_id}")
    print(f"sha256: {digest}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
