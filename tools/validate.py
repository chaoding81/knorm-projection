"""Verify the installed wheel, all tests, release hashes, and source snapshots."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from verify_sources import verify
from verify_release import verify_release
import numpy as np
import knorm_projection


def main():
    start = datetime.now(timezone.utc)
    clock0 = time.perf_counter()
    package_path = Path(knorm_projection.__file__).resolve()
    if not package_path.is_relative_to(Path(sys.prefix).resolve()) or package_path.is_relative_to(ROOT / "knorm_projection"):
        raise RuntimeError("Run with the installed virtual-environment Python; do not validate a source-tree import.")
    integrity = verify_release()
    preservation = verify()
    for name in ("__init__.py", "projection.py", "baseline.py"):
        if (package_path.parent / name).read_bytes() != (ROOT / "knorm_projection" / name).read_bytes():
            raise RuntimeError("Installed package differs from the bundled source: " + name)
    log = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    text = log.getvalue()
    print(text, end="")
    out = ROOT / "outputs" / ("validation_" + start.strftime("%Y%m%dT%H%M%S%fZ"))
    out.mkdir(parents=True, exist_ok=False)
    log_path = out / "tests.log"
    log_path.write_text(text, encoding="utf-8")
    report = {"version": knorm_projection.__version__, "passed": result.wasSuccessful(),
              "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
              "package_file": str(package_path), "python": sys.version, "numpy": np.__version__,
              "release_integrity": integrity, "source_snapshots": preservation,
              "installed_source_bytes_match": True, "matlab_executed": False}
    result_path = out / "validation.json"
    result_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    manifest = {"schema_version": 1, "claim_id": "knorm-projection-0.1-portable-installed-release",
                "repository": {"commit": None, "dirty": True}, "command": [sys.executable, str(Path(__file__).resolve())],
                "environment": {"software": [sys.version, "NumPy " + np.__version__], "hardware": platform.platform()},
                "mathematics": {"assertion_tested": "The installed release reproduces the finite mathematical tests and portable packaging checks.",
                                "coefficient_domain": "float64/complex128 with independent Decimal references", "conventions": "Frobenius projection onto the matrix Ky Fan k-norm dual ball.",
                                "inputs": ["Bundled tests/test_projection.py", "Bundled tests/test_release_tools.py"], "bounds": {"test_methods": result.testsRun, "decimal_precision": 500},
                                "non_claims": ["No MATLAB execution", "No universal numerical proof", "No cross-platform execution claim"]},
                "randomness": {"used": True, "generator": "NumPy default_rng/PCG64", "seed": [20261004,83,4,21,37]},
                "run": {"started_at": start.isoformat(), "runtime_seconds": time.perf_counter() - clock0, "exit_status": 0 if result.wasSuccessful() else 1},
                "outputs": [{"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in (result_path, log_path)],
                "checks": ["Installed package location and source equality", "Release file hashes", "MATLAB snapshot hashes", "Entire bundled unittest suite"],
                "result": "All tests passed." if result.wasSuccessful() else "Tests failed; inspect tests.log.",
                "residual_risks": ["Only the current Python/NumPy/platform combination was executed"]}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("Results: " + str(out))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
