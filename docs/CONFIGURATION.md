# Configuration and input/output

Configurations use UTF-8 JSON. Unknown fields are rejected so a misspelled option cannot silently select an unintended default.

```json
{
  "format_version": 1,
  "input": {"kind": "random", "shape": [12, 8], "seed": 20261004},
  "projection": {"radius": 1.0, "k": 3, "method": "general", "hermitian": false},
  "output_dir": "../outputs"
}
```

| Field | Meaning and constraints |
|---|---|
| `format_version` | Must be 1. This is the configuration format version; the algorithm version is 0.1. |
| `input.kind` | `random`, `random_hermitian`, or `npy`. |
| `input.shape` | Two positive integers for generated input. Hermitian input must be square. |
| `input.seed` | A nonnegative integer for NumPy default_rng/PCG64. |
| `input.path` | File used in `npy` mode, loaded with `np.load(..., allow_pickle=False)`. |
| `projection.radius` | A finite nonnegative spectral-norm bound. The nuclear-norm bound is k times this radius. |
| `projection.k` | A positive integer, at most the smaller matrix dimension for nonempty input. |
| `projection.method` | `auto` selects k2 when k=2; `general` forces the general method; `k2` requires k=2. |
| `projection.hermitian` | Explicitly selects the Hermitian/eigh path; input is not automatically symmetrized. |
| `output_dir` | Parent output directory. Each run creates a unique timestamped subdirectory. |

Relative paths are resolved against **the directory containing the configuration**, regardless of the working directory. Absolute paths are also accepted.

## Use your own data

Save a matrix in the installed environment:

```python
import numpy as np
X = np.array([[2., -1.], [-1., 2.]])
np.save("my_matrix.npy", X, allow_pickle=False)
```

Save this configuration beside `my_matrix.npy`:

```json
{
  "format_version": 1,
  "input": {"kind": "npy", "path": "my_matrix.npy"},
  "projection": {"radius": 1.0, "k": 2, "method": "k2", "hermitian": true},
  "output_dir": "results"
}
```

Run `python examples/run_config.py --config <configuration_path>`. The `.npy` file can contain real or complex matrices, including rectangular input. Set `hermitian` to false for general matrices.

The runner computes the projection and proximal mapping, then checks spectral/nuclear feasibility and the Moreau identity. The reported projection time excludes the subsequent proximal call, verification, and file output. Use the dedicated benchmark script for performance comparisons.

## Read saved results

```python
from pathlib import Path
import json
import numpy as np

run = Path("outputs/<run_directory>")
P = np.load(run / "projection.npy", allow_pickle=False)
Z = np.load(run / "prox.npy", allow_pickle=False)
report = json.loads((run / "report.json").read_text(encoding="utf-8"))
print(report["projection_info"])
```

Each run saves the submitted configuration as `requested_config.json` and a replayable `config.json` that reads the adjacent fixed `input.npy`. The entire run directory can be moved and replayed without the original random state or data path.
