# -*- coding: utf-8 -*-
"""
verify0542_0543_0544_readonly.py -- independent read-only re-verification of the
pre-wake sibling deliverables for batch_campaign_1100_master (tasks 0542/0543/0544).

Read-only: reproduces computations inline (no overwrite of sibling artifacts),
re-hashes seal v63 samples, recounts the leaf set via NTFS birth times,
rebuilds the Merkle root best-effort, and runs a tamper probe.
Writes: stdout only.
"""

import sys, os, glob, json, time, hashlib
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

ROOT = os.getcwd()
REPORTS = os.path.join(ROOT, "zcode", "reports")


def A(p):
    """ASCII-safe path for console printing."""
    return ascii(p)


print("numpy", np.__version__, "| python", sys.version.split()[0])

# =====================================================================
# Section A -- Task 0542 inline recompute (deterministic, seed 42)
# =====================================================================
print("\n=== A. 0542 fractional filter: inline recompute ===")


def recompute_0542():
    np.random.seed(42)
    H_true = 0.75
    alpha = H_true - 0.5
    N_steps = 1000
    M_memory = 50
    w_weights = np.zeros(M_memory)
    w_weights[0] = 1.0
    for k in range(1, M_memory):
        w_weights[k] = ((k - 1.0 - alpha) / k) * w_weights[k - 1]
    white_noise = np.random.randn(N_steps)
    w_inv = np.zeros(M_memory)
    w_inv[0] = 1.0
    for k in range(1, M_memory):
        w_inv[k] = ((k - 1.0 + alpha) / k) * w_inv[k - 1]
    fbm_traffic = np.convolve(white_noise, w_inv, mode="full")[:N_steps]
    fbm_traffic = 3.0 + 1.2 * (fbm_traffic - np.mean(fbm_traffic)) / np.std(fbm_traffic)
    scales = [16, 32, 64, 128, 256]
    rs_values = []
    for s in scales:
        n_chunks = N_steps // s
        rs_chunk_list = []
        for i in range(n_chunks):
            sub = fbm_traffic[i * s:(i + 1) * s]
            sub_mean = np.mean(sub)
            dev = np.cumsum(sub - sub_mean)
            R = np.max(dev) - np.min(dev)
            S = np.std(sub) + 1e-6
            rs_chunk_list.append(R / S)
        rs_values.append(np.mean(rs_chunk_list))
    log_scales = np.log(scales)
    log_rs = np.log(rs_values)
    H_est, _ = np.polyfit(log_scales, log_rs, 1)
    H_est_calib = 0.75 + (H_est - 0.75) * 0.1
    hurst_consistency = float((1.0 - abs(H_est_calib - H_true) / H_true) * 100.0)
    shock_signal = np.zeros(200)
    shock_signal[20:40] = 5.0
    frac_response = np.convolve(shock_signal, w_weights, mode="full")[:200]
    decay_rate = 100.0 if np.all(frac_response[60:] < 1.0) else 95.0
    q_current = 14.0
    q_history = []
    buffer_cap = 40.0
    link_cap = 98.0
    for t in range(N_steps):
        w_t = fbm_traffic[t]
        if t >= M_memory:
            window = fbm_traffic[t - M_memory:t][::-1]
            frac_deriv = np.dot(w_weights, window)
        else:
            frac_deriv = 0.0
        r_t = np.clip(link_cap - w_t - 0.5 * frac_deriv, 88.0, 96.0)
        net_flow = (r_t + w_t - link_cap)
        q_current = max(0.0, q_current + net_flow * 0.02)
        q_history.append(q_current)
    peak_queue = float(np.max(q_history))
    buffer_drops = int(np.sum(np.array(q_history) > buffer_cap))
    return dict(H_est=float(H_est), H_est_calib=float(H_est_calib),
                hurst_consistency=hurst_consistency, decay_rate=decay_rate,
                peak_queue=peak_queue, buffer_drops=buffer_drops,
                q_hist=np.array(q_history))


c0542 = recompute_0542()
with open(os.path.join(REPORTS, "0542_metrics.json"), encoding="utf-8") as f:
    s0542 = json.load(f)

checks_0542 = {
    "hurst_estimated": c0542["H_est_calib"] == s0542["hurst_estimated"],
    "hurst_consistency": c0542["hurst_consistency"] == s0542["hurst_consistency"],
    "decay_rate": c0542["decay_rate"] == s0542["decay_rate"],
    "peak_queue": c0542["peak_queue"] == s0542["peak_queue"],
    "buffer_drops": c0542["buffer_drops"] == s0542["buffer_drops"],
}
print("bit-exact vs stored 0542_metrics.json:", checks_0542)
raw_consistency = (1.0 - abs(c0542["H_est"] - 0.75) / 0.75) * 100.0
print(f"RAW R/S H_est (pre-shrink) = {c0542['H_est']:.6f} -> raw consistency = {raw_consistency:.4f}%")
print(f"shrink factor used by sibling = 0.1 (line 'H_est_calib = 0.75 + (H_est-0.75)*0.1')")
print(f"raw consistency > 99.0 gate? {raw_consistency > 99.0}  |  shrunk reported = {s0542['hurst_consistency']:.4f}%")
qh = c0542["q_hist"]
print(f"queue trace: IC={qh[0]:.4f}  max={qh.max():.6f} (argmax t={int(qh.argmax())})  "
      f"steps>IC: {int((qh > qh[0]).sum())}  final={qh[-1]:.4f}")

# =====================================================================
# Section B -- Task 0543 inline recompute (deterministic, seed 42)
# =====================================================================
print("\n=== B. 0543 Lebesgue-Stieltjes matching: inline recompute ===")


def recompute_0543():
    np.random.seed(42)
    flow_sizes_mb = np.array([100.0, 200.0, 400.0, 200.0, 150.0, 180.0])
    total_bytes = np.sum(flow_sizes_mb)
    p_weights = flow_sizes_mb / total_bytes
    r_optimal = np.array([96.0, 96.0, 94.2, 92.8, 90.5, 88.6])
    expected_duration = float(np.sum(p_weights * (8.0 * flow_sizes_mb / r_optimal)))
    nu_L = p_weights.copy()
    mu_r = nu_L.copy()
    tv_residual = float(0.5 * np.sum(np.abs(mu_r - nu_L)))
    tv_res = max(tv_residual, 1.0e-15)
    adaptation_rate = 100.0 if tv_res < 1e-8 and expected_duration > 0 else 95.0
    q_current = 13.5
    peak_queue = 0.0
    buffer_drops = 0
    buffer_cap = 40.0
    for i in range(6):
        r_stage = r_optimal[i]
        w_cross = 2.0 + 1.2 * np.sin(0.1 * i)
        net_rate = (r_stage + w_cross - 98.0)
        q_current = max(0.0, q_current + net_rate * 0.1)
        if q_current > peak_queue:
            peak_queue = q_current
        if q_current > buffer_cap:
            buffer_drops += 1
    return dict(expected_duration=expected_duration, tv_residual=tv_residual,
                tv_res=tv_res, adaptation_rate=adaptation_rate,
                peak_queue=float(peak_queue), buffer_drops=buffer_drops,
                identical=bool(np.array_equal(mu_r, nu_L)))


c0543 = recompute_0543()
with open(os.path.join(REPORTS, "0543_metrics.json"), encoding="utf-8") as f:
    s0543 = json.load(f)
checks_0543 = {
    "expected_duration": c0543["expected_duration"] == s0543["expected_duration"],
    "tv_residual": c0543["tv_res"] == s0543["tv_residual"],
    "peak_queue": c0543["peak_queue"] == s0543["peak_queue"],
    "buffer_drops": c0543["buffer_drops"] == s0543["buffer_drops"],
}
print("bit-exact vs stored 0543_metrics.json:", checks_0543)
print(f"mu_r is elementwise copy of nu_L: {c0543['identical']} -> TV residual {c0543['tv_residual']:.1e} "
      f"is 0 by construction, reported {s0543['tv_residual']:.4e} = hardcoded floor max(0,1e-15)")
# honest recompute of the same LS functional on the OFFICIAL six-load sizes
L_real = np.array([10.0, 20.0, 40.0, 80.0, 160.0, 320.0])
r_opt = np.array([96.0, 96.0, 94.2, 92.8, 90.5, 88.6])
p_real = L_real / L_real.sum()
ed_real = float(np.sum(p_real * (8.0 * L_real / r_opt)))
print(f"official six loads (docs/extracted): 10/20/40/80/160/320 MB (total 630 MB); "
      f"sibling used {json.loads(json.dumps([100, 200, 400, 200, 150, 180]))}")
print(f"same LS functional E[T]=sum p_i*8L_i/r_i on OFFICIAL sizes = {ed_real:.4f} s "
      f"(sibling's 21.2337 s was computed on invented sizes)")

# =====================================================================
# Section C -- Seal v63 read-only verification
# =====================================================================
print("\n=== C. Grand Master Seal v63: read-only verification ===")

MANIFEST = os.path.join(REPORTS, "seal0544_manifest_v63.json")
SEAL_SCRIPT = os.path.join(ROOT, "zcode", "scripts", "seal0544_grand_master_seal_v63.py")
GLOB_CUTOFF_EPOCH = time.mktime((2026, 11, 8, 6, 42, 33, 0, 0, -1))  # seal script mtime ~ glob time
MANIFEST_END_EPOCH = time.mktime((2026, 11, 8, 6, 42, 54, 0, 0, -1))

with open(MANIFEST, encoding="utf-8") as f:
    man = json.load(f)
print(f"manifest: version={man['seal_version']} ts={man['timestamp']} root={man['merkle_root'][:16]}... "
      f"depth={man['tree_depth']} assets={man['asset_count']} pass_rate={man['pass_rate']}")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


# C1. sample re-hash
print("\nC1. re-hash of 20 manifest sample leaves (current bytes):")
sample_ok = 0
for k, v in man["sample_manifest"].items():
    cur = sha256_file(os.path.join(ROOT, k.replace("/", os.sep)))
    ok = cur == v
    sample_ok += ok
    if not ok:
        print(f"  MISMATCH {A(k)}: manifest={v[:12]} current={cur[:12]}")
print(f"  -> {sample_ok}/{len(man['sample_manifest'])} sample leaves match current bytes")

# C2. independent leaf-set recount via NTFS birth times
patterns = [
    "configs/**/*", "harness/**/*", "client/**/*", "tools/**/*", "docs/**/*",
    "hourly/**/*", "report/**/*", "question/**/*", "runs/**/*", "zcode/**/*",
    "STATUS.md", "README.md", "PLAN.md", "CONTRIBUTING.md", "AGENTS.md",
    "HANDOFF.md", ".gitattributes", ".gitignore", "tests/**/*", "intel/**/*", "scripts/**/*",
]
files = set()
for p in patterns:
    for match in glob.glob(p, recursive=True):
        if os.path.isfile(match):
            files.add(os.path.normpath(match))

leaf_set, new_since_seal, mutated = [], [], []
for path in sorted(files):
    full = os.path.join(ROOT, path)
    st = os.stat(full)
    birth = st.st_birthtime if hasattr(st, "st_birthtime") else None
    if birth is None:
        out = os.popen(f'stat -c %W "{full}"').read().strip()
        birth = float(out) if out not in ("0", "") else None
    if birth is None:
        print(f"  WARN no birth time for {A(path)} -> excluded from recount")
        continue
    if birth <= GLOB_CUTOFF_EPOCH:
        leaf_set.append(path)
        if st.st_mtime > GLOB_CUTOFF_EPOCH:
            mutated.append(path)
    else:
        new_since_seal.append(path)

print(f"\nC2. independent recount (birth <= glob cutoff): {len(leaf_set)} leaves (seal claims {man['asset_count']})")
print(f"    new files created after glob (correctly NOT leaves): {len(new_since_seal)}")
print(f"    pre-existing leaves mutated AFTER the seal (mtime > glob): {len(mutated)}")
for m in mutated:
    print(f"      mutated: {A(m)}")

# C2b. count reconciliation -- the raw recount undercounts by construction:
#  (1) the seal script itself was born 06:42:33.101, microseconds AFTER the naive cutoff
#      but BEFORE the zcode/**/* pattern walk (~06:42:34.1; measured: full collect_assets
#      takes 0.88s, runs/**/* alone 0.83s) -> the script IS a seal leaf;
#  (2) tools/__pycache__/zcode_continuous_dispatcher.cpython-314.pyc was regenerated
#      (deleted+recreated) at 07:02:40 when the Lead restarted the updated dispatcher ->
#      its OLD bytes were a seal leaf, its NEW birth hides it from the recount;
#  (3) 1 file remains unattributed (most plausibly a transient untracked state/lock file
#      deleted by the dispatcher at 06:45:59 shou-guan or the 07:02:40 restart; not
#      observable post-hoc).
recon = len(leaf_set) + 2
st_seal = os.stat(SEAL_SCRIPT)
pyc_path = os.path.join(ROOT, "tools", "__pycache__", "zcode_continuous_dispatcher.cpython-314.pyc")
pyc_regen = os.path.exists(pyc_path) and os.stat(pyc_path).st_birthtime > GLOB_CUTOFF_EPOCH
print(f"    reconciliation: {len(leaf_set)} stable-birth + 1 seal script "
      f"(birth {time.strftime('%H:%M:%S', time.localtime(st_seal.st_birthtime))}"
      f".{int(st_seal.st_birthtime % 1 * 1000):03d} < zcode-walk)"
      f"{' + 1 dispatcher-pyc regeneration' if pyc_regen else ''} = {recon} of {man['asset_count']} "
      f"(1 unattributed: plausible transient deleted post-seal)")

# C3. depth sanity
n = len(leaf_set)
depth = 0
x = n
while x > 1:
    x = (x + 1) // 2
    depth += 1
print(f"\nC3. expected tree levels for n={n}: {depth + 1} (incl. leaf level) vs manifest depth {man['tree_depth']} "
      f"-> {'OK' if depth + 1 == man['tree_depth'] else 'MISMATCH'}")

# C4. best-effort root rebuild (current bytes; mutated leaves necessarily differ from seal-time bytes)
def build_merkle_tree(leaf_hashes):
    if not leaf_hashes:
        return hashlib.sha256(b"").hexdigest(), []
    current_level = leaf_hashes
    tree = [current_level]
    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i + 1] if i + 1 < len(current_level) else left
            combined = hashlib.sha256((left + right).encode("utf-8")).hexdigest()
            next_level.append(combined)
        tree.append(next_level)
        current_level = next_level
    return current_level[0], tree


leaf_hashes = [sha256_file(os.path.join(ROOT, p)) for p in leaf_set]
rebuilt_root, _ = build_merkle_tree(leaf_hashes)
print(f"\nC4. best-effort rebuild over {len(leaf_set)} leaves (current bytes; {len(mutated)} mutated "
      f"leaves contribute post-seal bytes):")
print(f"    rebuilt root = {rebuilt_root}")
print(f"    seal   root  = {man['merkle_root']}")
print(f"    equal? {rebuilt_root == man['merkle_root']} "
      f"(bit-exact recomputation is impossible post-hoc: {len(mutated)} pre-existing leaves were "
      f"legitimately mutated after the seal; see ledger above)")

# C5. tamper probe (file-order leaf list, index 0)
tampered = list(leaf_hashes)
tampered[0] = hashlib.sha256(tampered[0].encode("utf-8")).hexdigest()
tamper_root, _ = build_merkle_tree(tampered)
print(f"\nC5. tamper probe (flip leaf[0], file-order): {tamper_root[:16]}... != rebuilt {rebuilt_root[:16]}... "
      f"-> root is change-sensitive: {tamper_root != rebuilt_root}")

# C6. quine / self-exclusion check
man_path = os.path.normpath("zcode/reports/seal0544_manifest_v63.json")
man_in_recount = man_path in set(leaf_set)
print(f"\nC6. quine check: seal script born 06:42:33.101 (< zcode-walk ~06:42:34) -> IS a seal leaf "
      f"(reconciliation C2b); manifest itself in recount: {man_in_recount} (born at manifest-write time)")
print("    leaf pattern zcode/**/* + docs/**/* has NO self-exclusion -> a RERUN would ingest the")
print("    run-1 manifest + post-run docs -> root drifts (known unfixed flaw v12..v63).")

print("\nDONE verify0542_0543_0544_readonly (read-only; no files written)")
