"""Reproducible, accuracy-gated baseline/general-k/k=2 timing comparison.

Run from the release directory: python benchmarks/benchmark.py
Only this child process requests one BLAS thread; no system settings change.
The thread limit is cooperative and is recorded, not asserted as a CPU cap.
"""
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import statistics
import sys
import time

RELEASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RELEASE))

import numpy as np
import knorm_projection as optimized
from knorm_projection import baseline


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes():
    return {str(p.relative_to(RELEASE)).replace("\\", "/"): file_hash(p)
            for folder in ("knorm_projection", "tests", "benchmarks", "tools")
            for p in sorted((RELEASE / folder).rglob("*.py"))}


def timing(function, repeats, target_seconds=0.025):
    function()  # common warm-up policy
    before = time.perf_counter()
    function()
    pilot = max(time.perf_counter() - before, 1e-7)
    loops = max(1, min(128, int(target_seconds / pilot)))
    samples = []
    for _ in range(repeats):
        before = time.perf_counter()
        for _ in range(loops):
            function()
        samples.append((time.perf_counter() - before) / loops)
    return {"median_seconds": statistics.median(samples), "samples_seconds": samples,
            "calls_per_sample": loops}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="use smaller sizes for an initial measurement")
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if args.repeats < 3:
        parser.error("at least three repeats are needed")
    start = datetime.now(timezone.utc)
    timer = time.perf_counter()
    inputs_before = source_hashes()
    rng = np.random.default_rng(20261004)
    records = []
    vector_sizes = (256, 4096) if args.quick else (256, 4096, 32768)
    for n in vector_sizes:
        s = np.sort(rng.uniform(0, 4, n))[::-1]
        for k in (2, n // 4):
            functions = {"baseline": lambda: baseline.project_singular_values(s, 1, k),
                         "general": lambda: optimized.project_singular_values(s, 1, k, method="general", assume_sorted=True)}
            if k == 2:
                functions["k2"] = lambda: optimized.project_singular_values(s, 1, k, method="k2", assume_sorted=True)
            expected = functions["baseline"]()
            record = {"kind": "vector", "n": n, "k": k, "radius": 1.0,
                      "input_sha256": hashlib.sha256(s.tobytes()).hexdigest(), "methods": {}}
            for name, function in functions.items():
                p = function()
                error = float(np.max(np.abs(p - expected)))
                feasibility = max(0.0, -float(p.min()), float(p.max()) - 1,
                                  (float(p.sum()) - k) / k)
                if max(error, feasibility) > 1e-10:
                    raise AssertionError((record, name, error, feasibility))
                record["methods"][name] = {**timing(function, args.repeats),
                                             "max_error_vs_baseline": error,
                                             "feasibility_residual": feasibility}
            records.append(record)
            print(f"vector n={n}, k={k}: " + ", ".join(f"{name}={values['median_seconds']*1e6:.1f} us" for name, values in record["methods"].items()), flush=True)

    orders = (64, 192) if args.quick else (64, 192, 384)
    cases = []
    for n in orders:
        a = rng.normal(size=(n, n)) / np.sqrt(n)
        cases.append(("symmetric", (a + a.T) / 2))
    for m, n in ((96, 64),) if args.quick else ((96, 64), (256, 192)):
        cases.append(("rectangular", rng.normal(size=(m, n)) / np.sqrt(n)))
    for kind, x in cases:
        for k in (2, min(x.shape) // 4):
            functions = {"baseline_svd": lambda: baseline.project_dual_ball(x, 1, k),
                         "optimized_svd": lambda: optimized.project_dual_ball(x, 1, k)}
            if kind == "symmetric":
                functions["optimized_eigh"] = lambda: optimized.project_dual_ball(x, 1, k, hermitian=True)
            expected = functions["baseline_svd"]()
            denom = max(1.0, float(np.linalg.norm(expected, "fro")))
            record = {"kind": kind, "shape": list(x.shape), "k": k, "radius": 1.0,
                      "input_sha256": hashlib.sha256(x.tobytes()).hexdigest(), "methods": {}}
            for name, function in functions.items():
                p = function()
                error = float(np.linalg.norm(p - expected, "fro") / denom)
                sigma = np.linalg.svd(p, compute_uv=False)
                feasibility = max(0.0, float(sigma[0]) - 1,
                                  (float(sigma.sum()) - k) / k)
                if max(error, feasibility) > 1e-10:
                    raise AssertionError((record, name, error, feasibility))
                record["methods"][name] = {**timing(function, args.repeats),
                                             "relative_error_vs_baseline": error,
                                             "feasibility_residual": feasibility}
            records.append(record)
            print(f"{kind} {x.shape}, k={k}: " + ", ".join(f"{name}={values['median_seconds']*1e3:.2f} ms" for name, values in record["methods"].items()), flush=True)
    if source_hashes() != inputs_before:
        raise RuntimeError("Source changed while benchmark was running")
    config_stream = io.StringIO()
    from contextlib import redirect_stdout
    with redirect_stdout(config_stream):
        # The dictionary form avoids the optional PyYAML dependency.
        config = np.show_config(mode="dicts")
    environment = {"python": sys.version, "numpy": np.__version__, "platform": platform.platform(),
                   "processor": platform.processor(), "logical_cpu_count": os.cpu_count(),
                   "thread_environment": {key: os.environ.get(key) for key in
                                          ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")},
                   "numpy_build": config}
    output = RELEASE / "results" / ("benchmark_" + start.strftime("%Y%m%dT%H%M%S%fZ"))
    output.mkdir(parents=True, exist_ok=False)
    results = {"version": optimized.__version__, "seed": 20261004, "repeats": args.repeats,
               "environment": environment, "source_sha256": inputs_before, "records": records,
               "accuracy_gate": 1e-10, "matlab_executed": False,
               "timing_scope": "One projection including API validation, decomposition (matrix cases), scalar solve, and reconstruction; accuracy checks outside the timer; same float64 precision and radius/k.",
               "limitations": ["Synthetic finite cases, not solver end-to-end experiments", "Single-process cooperative BLAS thread request", "Baseline is a Python port, not MATLAB"]}
    result_path = output / "benchmark.json"
    result_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    manifest = {"schema_version": 1, "claim_id": "knorm-projection-v0.1-python-performance",
                "repository": {"commit": None, "dirty": True},
                "command": [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
                "environment": {"software": [sys.version, "NumPy " + np.__version__], "hardware": environment["platform"] + "; " + environment["processor"]},
                "mathematics": {"assertion_tested": "Optimized general-k and k=2 projections meet the same accuracy gate as the Python baseline on identical inputs, with separately measured scalar and matrix timings.",
                                "coefficient_domain": "IEEE-754 float64", "conventions": "Dual Ky Fan ball: spectral norm <= radius and nuclear norm <= k*radius; Frobenius metric.",
                                "inputs": ["Seeded sorted uniform spectra", "Seeded real symmetric and rectangular matrices"],
                                "bounds": {"vector_sizes": list(vector_sizes), "matrix_orders": list(orders), "accuracy_gate": 1e-10, "timing_repeats": args.repeats, "max_calls_per_sample": 128},
                                "non_claims": results["limitations"]},
                "randomness": {"used": True, "generator": "NumPy default_rng/PCG64", "seed": 20261004},
                "run": {"started_at": start.isoformat(), "runtime_seconds": time.perf_counter() - timer, "exit_status": 0},
                "outputs": [{"path": str(result_path.relative_to(RELEASE)).replace("\\", "/"), "sha256": file_hash(result_path)}],
                "checks": ["Baseline agreement", "Spectral and nuclear feasibility", "Input code hashes unchanged"],
                "result": "Accuracy checks and repeated timing completed for every recorded case.",
                "residual_risks": results["limitations"]}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Results: " + str(result_path))


if __name__ == "__main__":
    main()
