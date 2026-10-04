"""Refresh release checksums and create a new ZIP without build/cache files.

The output ZIP and its checksum must not already exist. The wheel must be
built before packaging; this utility never downloads or changes algorithms.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = {"knorm_projection", "wheelhouse", "configs", "data", "examples", "tests",
               "tools", "benchmarks", "original_matlab", "docs", "reports"}
ROOT_FILES = {"README.md", "CHANGELOG.md", "pyproject.toml", "SOURCE_MANIFEST.json",
              "install.py", "setup.ps1", "setup.sh", "requirements.txt",
              "requirements-online.txt", "requirements-offline-win-py312.txt",
              "THIRD_PARTY_NOTICES.md"}


def payload_files():
    files = [ROOT / name for name in sorted(ROOT_FILES) if (ROOT / name).is_file()]
    for directory in sorted(DIRECTORIES):
        for base, dirs, names in os.walk(ROOT / directory):
            dirs[:] = sorted(name for name in dirs if not name.startswith(".") and name != "__pycache__")
            for name in sorted(names):
                if not name.startswith(".") and not name.endswith((".pyc", ".pyo")):
                    files.append(Path(base) / name)
    return sorted(files)


def pack(output):
    output = Path(output).resolve()
    checksum = output.with_suffix(output.suffix + ".sha256")
    if output.exists() or checksum.exists():
        raise FileExistsError("Choose a new output filename; existing releases are not overwritten.")
    files = payload_files()
    for name in ROOT_FILES:
        if not (ROOT / name).is_file():
            raise FileNotFoundError(name)
    hashes = {str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    manifest = {"name": "knorm-projection", "version": "0.1",
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "offline_platform": "CPython 3.12 / Windows x86-64",
                "numpy_version": "2.3.5", "files_sha256": hashes}
    manifest_path = ROOT / "RELEASE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files + [manifest_path]:
            archive.write(path, "knorm_projection-0.1/" + str(path.relative_to(ROOT)).replace("\\", "/"))
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    checksum.write_text(digest + "  " + output.name + "\n", encoding="ascii")
    return {"zip": str(output), "bytes": output.stat().st_size, "sha256": digest,
            "files": len(files) + 1}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(pack(args.output), indent=2))
