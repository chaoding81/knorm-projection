# k-norm Projection: Python Release 0.1

NumPy projection onto matrix Ky Fan k-norm dual balls, with separate implementations for general k and k=2.

[Download the complete v0.1 bundle](https://github.com/chaoding81/knorm-projection/releases/download/v0.1/knorm_projection-0.1.zip) · [Release and checksums](https://github.com/chaoding81/knorm-projection/releases/tag/v0.1)

The bundle includes source code, an installable wheel, offline Windows dependencies, configurations, examples, tests, and benchmark records. The numerical implementation is byte-identical to the previously validated Python 0.1 code.

The program computes the **Frobenius projection onto the dual ball** of the matrix Ky Fan k-norm:

```text
minimize  0.5 * ||P - X||_F^2
subject to ||P||_2 <= radius,  ||P||_* <= k * radius
```

The general-k and specialized k=2 methods can be selected explicitly. The package also provides the corresponding proximal mapping and an optional Hermitian/eigh path. See the [algorithm description](docs/ALGORITHM_0.1.md).

## 1. Windows quick start: offline installation

Install **64-bit CPython 3.12 for Windows x86-64**, then extract the complete ZIP. The Python interpreter is a prerequisite, available from the [official Python website](https://www.python.org/downloads/windows/). NumPy 2.3.5 and the projection package wheels are bundled. No MATLAB, SciPy, compiler, or dependency download is required for offline installation.

Open PowerShell in the extracted `knorm_projection-0.1` directory:

```powershell
py -3.12 install.py
.\.venv\Scripts\python.exe examples\demo.py
.\.venv\Scripts\python.exe examples\run_config.py --config configs\k2.json
.\.venv\Scripts\python.exe -I tools\validate.py
```

The installer creates a local `.venv`, verifies release and dependency hashes, installs the wheels, and runs dependency and projection smoke checks. It does not install packages globally or persistently change PATH. Environment activation is optional.

To select an interpreter through the PowerShell wrapper:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1 -Python "C:\Path\To\Python312\python.exe"
```

The execution-policy option applies only to that process. Running `py -3.12 install.py` directly needs no PowerShell script or execution-policy change.

## 2. Other platforms or Python versions: online installation

The pinned NumPy 2.3.5 dependency requires Python 3.11+, as stated in its [release metadata](https://pypi.org/project/numpy/2.3.5/). Online installation supports combinations for which PyPI provides a compatible binary wheel. Installation was tested on Windows x86-64 with CPython 3.12.

```text
python install.py --online
```

On Linux or macOS:

```sh
sh setup.sh
.venv/bin/python examples/demo.py
.venv/bin/python examples/run_config.py --config configs/general_k.json
.venv/bin/python -I tools/validate.py
```

Online installation uses the same local `knorm-projection==0.1` wheel and downloads the compatible NumPy 2.3.5 wheel from official PyPI. Published wheel hashes are pinned in the dependency file. Source-build fallback is disabled. The installer uses standard [venv](https://docs.python.org/3/library/venv.html) and pip [hash checking](https://pip.pypa.io/en/stable/topics/secure-installs/).

## 3. Configurations and examples

| Configuration | Purpose | Command |
|---|---|---|
| `configs/general_k.json` | A 12-by-8 matrix, k=3, general method | `python examples/run_config.py --config configs/general_k.json` |
| `configs/k2.json` | The same random instance, specialized k=2 method | `python examples/run_config.py --config configs/k2.json` |
| `configs/hermitian.json` | A real symmetric matrix using eigh | `python examples/run_config.py --config configs/hermitian.json` |
| `configs/from_file.json` | Load `data/diagonal.npy` | `python examples/run_config.py --config configs/from_file.json` |

Here, `python` means the installed `.venv` interpreter. Copy a supplied configuration before editing it so the shipped files retain their hashes. See the [configuration guide](docs/CONFIGURATION.md) for fields, path resolution, and custom data.

Each run creates `outputs/<configuration>_<UTC timestamp>/` with:

- `input.npy`, `projection.npy`, and `prox.npy`: the actual input and both outputs.
- `requested_config.json`: the submitted configuration, including the seed.
- `config.json`: a replay configuration using the saved `input.npy`.
- `report.json`: the method, versions, input hash, timing, feasibility, and Moreau checks.

Replay a saved run with:

```text
python examples/run_config.py --config outputs/<run_directory>/config.json
```

Results go into a new subdirectory under that run's `replays/` folder. Existing outputs are preserved.

## 4. Python API

```python
import numpy as np
from knorm_projection import project_dual_ball, project_singular_values, prox_ky_fan

X = np.array([[4., 0., 0.], [0., 2., 0.], [0., 0., 1.]])
P = project_dual_ball(X, radius=1.0, k=2, method="k2")
P_general = project_dual_ball(X, radius=1.0, k=2, method="general")
Z = prox_ky_fan(X, weight=1.0, k=2)
assert np.allclose(P, P_general)
assert np.allclose(P + Z, X)

# The default "auto" method selects the specialized path only when k=2.
p, info = project_singular_values([4., 2., 1.], 1.0, 3,
                                 method="general", return_info=True)
```

For nonempty input, k must be an integer with `1 <= k <= min(X.shape)`. The radius must be finite and nonnegative. Zero radii, empty matrices, and scalar cases are handled explicitly. General matrices may be real or complex; computation uses float64 or complex128. `hermitian=True` requires an exactly Hermitian input, X=X*. The caller must decide whether symmetrization is appropriate. The parameter k=2 does not imply rank two, and small positive spectral values are not truncated.

## 5. Verification and benchmarks

```text
python tools/verify_release.py
python tools/verify_sources.py
python -I tools/validate.py
python benchmarks/benchmark.py --repeats 7
```

`verify_release.py` checks shipped files; new `.venv` and `outputs` directories do not affect it. `verify_sources.py` checks the four bundled MATLAB snapshots without requiring the original workspace. To check all 46 original `.m` files:

```text
python tools/verify_sources.py --original-root "<original_k-norm_directory>"
```

Run `tools/validate.py` with the installed `.venv` interpreter. It checks import locations and installed source bytes, runs the 20 algorithm tests and three release tests, and writes records under `outputs/validation_<timestamp>/`.

Historical mathematical checks and complete benchmarks are in `reports/`, including cases that did not improve. They measure Python projection routines, not MATLAB or complete FMMC solvers. See the [release installation record](reports/RELEASE_VERIFICATION.json) for clean-install verification.

## 6. Bundle contents

```text
knorm_projection/      General-k, k=2, matrix projection, proximal mapping, baseline
wheelhouse/            Package wheel, Windows NumPy wheel, provenance
configs/              Four example configurations
data/                 Small .npy fixture
examples/             Minimal and configuration-driven examples
tests/                Algorithm and release regression tests
tools/                Installed-package, release-file, and snapshot verification
benchmarks/           Reproducible Python performance measurements
original_matlab/       Four byte-preserved MATLAB source snapshots
docs/                 Algorithm, configuration, troubleshooting, publication notes
reports/              Benchmarks and verification records
install.py            Virtual-environment installer
setup.ps1 / setup.sh  Installer wrappers
requirements*.txt     Pinned dependencies and hashes
RELEASE_MANIFEST.json  SHA-256 hashes of shipped files
SOURCE_MANIFEST.json   Original MATLAB source hashes
```

See [troubleshooting](docs/TROUBLESHOOTING.md) for installation issues. Distribution is through GitHub Releases; the project has not been published to PyPI. Original MATLAB files and earlier local Python 0.1 artifacts are preserved.

Public reports replace local absolute paths with placeholders. Numerical measurements, test outcomes, and the algorithm source are unchanged. The [publication record](docs/PUBLICATION.md) describes the English revision and packaging history.
