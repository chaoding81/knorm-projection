"""Run a JSON-configured projection with the installed Python package."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import knorm_projection
from knorm_projection import project_dual_ball, prox_ky_fan


def validate_config(config):
    def check_keys(value, allowed, required, label):
        if not isinstance(value, dict) or set(value) - set(allowed) or set(required) - set(value):
            raise ValueError(f"Invalid or missing keys in {label}; allowed: {', '.join(allowed)}")
    check_keys(config, ("format_version", "input", "projection", "output_dir"),
               ("format_version", "input", "projection", "output_dir"), "configuration")
    if config["format_version"] != 1:
        raise ValueError("format_version must be 1")
    source = config["input"]
    if not isinstance(source, dict):
        raise ValueError("input must be an object")
    if source.get("kind") in ("random", "random_hermitian"):
        check_keys(source, ("kind", "shape", "seed"), ("kind", "shape", "seed"), "input")
        shape = source["shape"]
        if not isinstance(shape, list) or len(shape) != 2 or any(type(n) is not int or n <= 0 for n in shape):
            raise ValueError("shape must contain two positive integers")
        if source["kind"] == "random_hermitian" and shape[0] != shape[1]:
            raise ValueError("random_hermitian requires a square shape")
        if type(source["seed"]) is not int or source["seed"] < 0:
            raise ValueError("seed must be a nonnegative integer")
    elif source.get("kind") == "npy":
        check_keys(source, ("kind", "path"), ("kind", "path"), "input")
        if not isinstance(source["path"], str) or not source["path"]:
            raise ValueError("input.path must be a nonempty string")
    else:
        raise ValueError("input.kind must be random, random_hermitian, or npy")
    projection = config["projection"]
    check_keys(projection, ("radius", "k", "method", "hermitian"),
               ("radius", "k", "method", "hermitian"), "projection")
    if isinstance(projection["radius"], bool) or not isinstance(projection["radius"], (int, float)) or not np.isfinite(projection["radius"]) or projection["radius"] < 0:
        raise ValueError("radius must be finite and nonnegative")
    if type(projection["k"]) is not int or projection["k"] < 1:
        raise ValueError("k must be a positive integer")
    if projection["method"] not in ("auto", "general", "k2"):
        raise ValueError("method must be auto, general, or k2")
    if projection["method"] == "k2" and projection["k"] != 2:
        raise ValueError("method=k2 requires k=2")
    if type(projection["hermitian"]) is not bool:
        raise ValueError("hermitian must be true or false")
    if not isinstance(config["output_dir"], str) or not config["output_dir"]:
        raise ValueError("output_dir must be a nonempty string")
    return config


def load_config(path):
    return validate_config(json.loads(Path(path).read_text(encoding="utf-8-sig")))


def run(path, output_root=None):
    path = Path(path).resolve()
    config = load_config(path)
    source = config["input"]
    if source["kind"] == "npy":
        data_path = (path.parent / source["path"]).resolve()
        x = np.load(data_path, allow_pickle=False)
    else:
        rng = np.random.default_rng(source["seed"])
        x = rng.standard_normal(source["shape"])
        if source["kind"] == "random_hermitian":
            x = (x + x.T) / 2
    options = config["projection"]
    t0 = time.perf_counter()
    p, info = project_dual_ball(x, return_info=True, **options)
    elapsed = time.perf_counter() - t0
    z = prox_ky_fan(x, weight=options["radius"], k=options["k"],
                    method=options["method"], hermitian=options["hermitian"])
    sigma = np.linalg.svd(p, compute_uv=False)
    radius, k = options["radius"], options["k"]
    feasibility = max(0.0, (float(sigma[0]) - radius) / max(1, radius),
                      (float(sigma.sum()) - k * radius) / max(1, k * radius)) if sigma.size else 0.0
    scale = max(1.0, float(np.max(np.abs(x), initial=0)))
    moreau = float(np.linalg.norm((p / scale + z / scale) - x / scale, "fro") /
                   max(1 / scale, np.linalg.norm(x / scale, "fro")))
    if not np.isfinite(feasibility + moreau) or max(feasibility, moreau) > 1e-10:
        raise ArithmeticError("Example output failed feasibility or Moreau validation")
    root = Path(output_root).resolve() if output_root else (path.parent / config["output_dir"]).resolve()
    out = root / (path.stem + "_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    out.mkdir(parents=True, exist_ok=False)
    np.save(out / "input.npy", x, allow_pickle=False)
    np.save(out / "projection.npy", p, allow_pickle=False)
    np.save(out / "prox.npy", z, allow_pickle=False)
    (out / "requested_config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    replay = {**config, "input": {"kind": "npy", "path": "input.npy"}, "output_dir": "replays"}
    (out / "config.json").write_text(json.dumps(replay, indent=2) + "\n", encoding="utf-8")
    report = {"version": knorm_projection.__version__, "numpy": np.__version__,
              "package_file": knorm_projection.__file__, "python": sys.version,
              "shape": list(x.shape), "input_dtype": str(x.dtype), "projection_seconds": elapsed,
              "projection_info": info, "feasibility_residual": feasibility,
              "moreau_relative_residual": moreau, "input_sha256": hashlib.sha256(x.tobytes()).hexdigest(),
              "output_directory": str(out), "checks_passed": True}
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.config, args.output_root), indent=2))
