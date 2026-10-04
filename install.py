"""Install this release into a project-local virtual environment.

Default: offline CPython 3.12 / Windows x86-64. Use --online for another
supported Python/platform. No administrator rights or global pip install.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from verify_release import verify_release


def call(args, cwd=ROOT):
    subprocess.run([str(a) for a in args], cwd=cwd, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online", action="store_true", help="download compatible pinned NumPy wheel from PyPI")
    parser.add_argument("--venv", type=Path, default=ROOT / ".venv")
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        parser.error("Pinned NumPy 2.3.5 requires Python 3.11+. Offline bundle requires CPython 3.12 x64 on Windows.")
    if not args.online and not (sys.platform == "win32" and sys.implementation.name == "cpython" and
                               sys.version_info[:2] == (3, 12) and platform.machine().lower() in ("amd64", "x86_64")):
        parser.error("Offline mode requires CPython 3.12 x64 on Windows; otherwise use --online.")
    print(json.dumps(verify_release(), indent=2))
    environment = args.venv.resolve()
    if environment.exists() and not (environment / "pyvenv.cfg").is_file():
        parser.error("Refusing to overwrite an existing directory that is not a virtual environment.")
    if not environment.exists():
        venv.EnvBuilder(with_pip=True, system_site_packages=False).create(environment)
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.is_file():
        parser.error("Virtual environment has no Python executable. Choose another --venv path.")
    version = subprocess.check_output([str(python), "-I", "-c", "import sys; print(str(sys.version_info.major)+'.'+str(sys.version_info.minor))"], text=True).strip()
    if version != f"{sys.version_info.major}.{sys.version_info.minor}":
        parser.error("Existing virtual environment uses a different Python version. Choose another --venv path.")
    command = [python, "-I", "-m", "pip", "--isolated", "install", "--disable-pip-version-check",
               "--no-cache-dir", "--require-hashes", "--only-binary=:all:"]
    if args.online:
        command += ["--index-url", "https://pypi.org/simple", "-r", ROOT / "requirements-online.txt"]
    else:
        command += ["--no-index", "--find-links", ROOT / "wheelhouse", "-r", ROOT / "requirements-offline-win-py312.txt"]
    call(command)
    call([python, "-I", "-m", "pip", "--isolated", "check"])
    call([python, "-I", "-c", "import importlib.metadata as m, numpy as np, knorm_projection as k; assert m.version('knorm-projection')=='0.1'; assert np.__version__=='2.3.5'; np.testing.assert_allclose(k.project_dual_ball(np.eye(3),1,2),np.eye(3)*2/3); print('Installed package smoke test passed:',k.__file__)"])
    print("Installation complete. Python: " + str(python))
    print("Next: " + str(python) + " examples/demo.py")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode)
