# 配置与输入输出

配置是 UTF-8 JSON。未知字段会报错，避免把 `radius` 等参数拼错后悄悄使用默认值。

```json
{
  "format_version": 1,
  "input": {"kind": "random", "shape": [12, 8], "seed": 20261004},
  "projection": {"radius": 1.0, "k": 3, "method": "general", "hermitian": false},
  "output_dir": "../outputs"
}
```

| 字段 | 含义与限制 |
|---|---|
| `format_version` | 固定为 1，是配置格式版本；算法版本仍为 0.1 |
| `input.kind` | `random`、`random_hermitian` 或 `npy` |
| `input.shape` | 随机输入的两维正整数；Hermitian 输入必须方阵 |
| `input.seed` | 非负整数，使用 NumPy default_rng/PCG64 |
| `input.path` | `npy` 模式的数据文件；用 `np.load(..., allow_pickle=False)` 读取 |
| `projection.radius` | 非负有限数，谱范数上界；核范数上界为 k×radius |
| `projection.k` | 正整数；非空矩阵不超过较小维数 |
| `projection.method` | `auto`：k=2 选专用路径，否则一般路径；`general`：强制通用；`k2`：要求 k=2 |
| `projection.hermitian` | 显式启用 Hermitian/eigh 路径，不自动修正输入的非对称部分 |
| `output_dir` | 结果父目录；运行时再创建唯一时间戳子目录 |

所有相对文件路径都相对于**配置文件所在目录**，不依赖启动程序时的工作目录。也可以用绝对路径。

## 自己的数据

在已安装环境中保存矩阵：

```python
import numpy as np
X = np.array([[2., -1.], [-1., 2.]])
np.save("my_matrix.npy", X, allow_pickle=False)
```

把下面配置保存到与 `my_matrix.npy` 相同的目录：

```json
{
  "format_version": 1,
  "input": {"kind": "npy", "path": "my_matrix.npy"},
  "projection": {"radius": 1.0, "k": 2, "method": "k2", "hermitian": true},
  "output_dir": "results"
}
```

运行 `python examples/run_config.py --config <配置文件路径>`。实数、复数以及一般矩形矩阵都可通过 `.npy` 输入；若不是 Hermitian 矩阵，将 `hermitian` 设为 false。

示例入口会计算投影与近端映射，重新核对投影的谱/核范数可行性以及 Moreau 关系。报告中的单次耗时只涵盖投影调用，不包括随后近端计算、结果核验与文件保存；它不是正式性能基准。

## 读回结果

```python
from pathlib import Path
import json
import numpy as np

run = Path("outputs/<某次运行目录>")
P = np.load(run / "projection.npy", allow_pickle=False)
Z = np.load(run / "prox.npy", allow_pickle=False)
report = json.loads((run / "report.json").read_text(encoding="utf-8"))
print(report["projection_info"])
```

每次运行保存原配置 `requested_config.json`，并另存可重放的 `config.json`，后者读取同目录的固定 `input.npy`。因此整个运行目录复制到别处后仍可重放，不需要原随机状态或原数据路径。
