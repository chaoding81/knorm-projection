"""Verify every shipped payload file against RELEASE_MANIFEST.json."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify_release():
    manifest = json.loads((ROOT / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    failures = []
    for name, expected in manifest["files_sha256"].items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            failures.append(name)
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            failures.append(name)
    if failures:
        raise RuntimeError("Release integrity check failed: " + "; ".join(failures))
    return {"version": manifest["version"], "files_checked": len(manifest["files_sha256"]),
            "integrity_ok": True}


if __name__ == "__main__":
    print(json.dumps(verify_release(), indent=2))
