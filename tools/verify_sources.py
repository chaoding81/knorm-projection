"""Verify bundled MATLAB snapshots; the original workspace is optional."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify(original_root=None):
    manifest = json.loads((ROOT / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    failures = []
    for name in manifest["snapshot_files"]:
        path = ROOT / "original_matlab" / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != manifest["original_matlab_sha256"][name]:
            failures.append(str(path))
    checked = 0
    if original_root is not None:
        original_root = Path(original_root).resolve()
        for name, expected in manifest["original_matlab_sha256"].items():
            path = original_root / name
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                failures.append(str(path))
            checked += 1
    if failures:
        raise RuntimeError("Source preservation check failed: " + "; ".join(failures))
    return {"preserved": True, "bundled_snapshots_checked": len(manifest["snapshot_files"]),
            "original_files_checked": checked,
            "original_tree_check": "passed" if original_root is not None else "not requested; portable snapshot check only"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-root", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.original_root), indent=2))
