# k-norm 投影 Python release 0.1

NumPy projection onto matrix Ky Fan k-norm dual balls, with separate general-k and k=2 implementations.

[下载 v0.1 完整安装包](https://github.com/chaoding81/knorm-projection/releases/download/v0.1/knorm_projection-0.1.zip) · [Release 与校验码](https://github.com/chaoding81/knorm-projection/releases/tag/v0.1)

完整源代码、可安装 wheel、Windows 离线依赖、配置、实例、测试与基准结果均在本包中。核心投影算法与已经验证的 Python 0.1 源码逐字节相同。

程序计算矩阵 Ky Fan k-范数的**对偶球投影**：

`min 0.5 * ||P-X||_F^2, subject to ||P||_2 <= radius, ||P||_* <= k*radius`。

一般 k 与 k=2 的专用优化可以分别选择；另提供近端映射和显式 Hermitian/eigh 路径。详细推导见 [算法说明](docs/ALGORITHM_0.1.md)。

## 1. Windows 快速开始（离线）

准备 **CPython 3.12、64 位 x86-64**，然后完整解压 ZIP。解释器本身不在 ZIP 中；可从 [Python 官方网站](https://www.python.org/downloads/windows/)安装。NumPy 2.3.5 和本程序的 wheel 已随包提供，无需 MATLAB、SciPy、编译器或联网下载依赖。

在解压后的 `knorm_projection-0.1` 目录打开 PowerShell：

```powershell
py -3.12 install.py
.\.venv\Scripts\python.exe examples\demo.py
.\.venv\Scripts\python.exe examples\run_config.py --config configs\k2.json
.\.venv\Scripts\python.exe -I tools\validate.py
```

安装器只在当前 release 中建立 `.venv`，不会全局安装包或持久修改 PATH。安装前验证文件哈希，安装时强制核对依赖哈希，安装后运行依赖检查及投影冒烟测试。无需激活虚拟环境。

也可用 PowerShell 包装脚本，显式指定自己的 Python 路径：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1 -Python "C:\Path\To\Python312\python.exe"
```

该 `ExecutionPolicy` 参数只对这次 PowerShell 进程生效。若使用直接的 `py -3.12 install.py`，不需要运行任何 PowerShell 脚本。

## 2. 其他平台或 Python 版本（在线）

固定依赖 NumPy 2.3.5 要求 Python 3.11+，见 [NumPy 版本元数据](https://pypi.org/project/numpy/2.3.5/)。在线方式适用于 PyPI 有对应二进制 wheel 的解释器与平台；本 release 的实际安装验证范围为 Windows x86-64 / CPython 3.12。

```text
python install.py --online
```

Linux/macOS 也可运行：

```sh
sh setup.sh
.venv/bin/python examples/demo.py
.venv/bin/python examples/run_config.py --config configs/general_k.json
.venv/bin/python -I tools/validate.py
```

在线方式仍安装同一份本地 `knorm-projection==0.1` wheel，仅从官方 PyPI 下载适配平台的 NumPy 2.3.5 wheel；依赖文件记录了该版本发布的 wheel 哈希。它不接受源代码回退编译。安装器使用标准 [venv](https://docs.python.org/3/library/venv.html) 与 pip 的[哈希校验安装](https://pip.pypa.io/en/stable/topics/secure-installs/)。

## 3. 配置与实例

| 配置 | 内容 | 运行 |
|---|---|---|
| `configs/general_k.json` | 12×8 矩阵，k=3，强制一般路径 | `python examples/run_config.py --config configs/general_k.json` |
| `configs/k2.json` | 相同随机实例，k=2 专用路径 | `python examples/run_config.py --config configs/k2.json` |
| `configs/hermitian.json` | 实对称矩阵，eigh 路径 | `python examples/run_config.py --config configs/hermitian.json` |
| `configs/from_file.json` | 读取随包 `data/diagonal.npy` | `python examples/run_config.py --config configs/from_file.json` |

上表中的 `python` 指安装后的 `.venv` 解释器。若要修改参数，建议复制配置为新文件，保留原配置信息和供货哈希。全部字段、路径规则和自己的数据如何接入，见 [配置说明](docs/CONFIGURATION.md)。

每次运行新建 `outputs/<配置名>_<UTC时间>/`，包含：

- `input.npy`、`projection.npy`、`prox.npy`：实际输入及两种结果。
- `requested_config.json`：用户提交的配置，包括随机种子。
- `config.json`：固定读取已保存 `input.npy` 的可重放配置。
- `report.json`：方法、版本、输入哈希、耗时、可行性和 Moreau 核验结果。

例如重放某次运行：

```text
python examples/run_config.py --config outputs/<某次运行>/config.json
```

新结果写入该次运行下的 `replays/` 新子目录，不覆盖原结果。

## 4. 在自己的程序中调用

```python
import numpy as np
from knorm_projection import project_dual_ball, project_singular_values, prox_ky_fan

X = np.array([[4., 0., 0.], [0., 2., 0.], [0., 0., 1.]])
P = project_dual_ball(X, radius=1.0, k=2, method="k2")
P_general = project_dual_ball(X, radius=1.0, k=2, method="general")
Z = prox_ky_fan(X, weight=1.0, k=2)
assert np.allclose(P, P_general)
assert np.allclose(P + Z, X)

# 一般 k；默认 auto 仅在 k=2 时选择专用路径。
p, info = project_singular_values([4., 2., 1.], 1.0, 3,
                                 method="general", return_info=True)
```

非空输入要求整数 `1 <= k <= min(X.shape)`。`radius >= 0`；零半径、空矩阵及标量均有明确处理。一般矩阵可为实数或复数，计算精度为 float64/complex128。`hermitian=True` 要求输入精确满足 X=X*；不自动把任意数据对称化。k=2 不意味着投影矩阵秩为 2，本版没有数值秩截断。

## 5. 验证、原代码保护与基准

```text
python tools/verify_release.py
python tools/verify_sources.py
python -I tools/validate.py
python benchmarks/benchmark.py --repeats 7
```

`verify_release.py` 校验随包文件；新建 `.venv`、`outputs` 等不会影响它。`verify_sources.py` 默认只校验随包四个 MATLAB 投影快照，完全不依赖原工作区。需要核对原目录全部 46 个 `.m` 时，可额外指定：

```text
python tools/verify_sources.py --original-root "<原来的k-norm目录>"
```

`tools/validate.py` 必须使用已安装的 `.venv` Python，它会检查实际导入位置、已安装源码与随包源码一致性，执行 20 项算法测试及 release 配置/便携性测试，并在 `outputs/validation_<时间>/` 留下记录。

历史数学检查与正式基准保存在 `reports/`；它们针对同一核心算法，包含所有实例和未提速的情况。它们不是 MATLAB 计时，也不是 FMMC 外层求解器的加速报告。新的 release 安装验证另见 [release 检查记录](reports/RELEASE_VERIFICATION.json)。

## 6. 包内目录

```text
knorm_projection/      算法源码：一般 k、k=2、矩阵投影、近端及基线
wheelhouse/            本程序 wheel、Windows CPython 3.12 NumPy wheel、来源哈希
configs/              四套实例配置
data/                 小型 .npy 示例矩阵
examples/             最小示例、配置式运行入口
tests/                数学与 release 回归测试
tools/                安装后验证、文件校验、原始快照校验
benchmarks/           可重复的 Python 性能基准
original_matlab/       四个原始 MATLAB 文件，逐字节保留
docs/                 算法、配置、故障排查及维护说明
reports/              历史基准和本次 release 安装验证
install.py            跨平台虚拟环境安装器
setup.ps1 / setup.sh  安装包装脚本
requirements*.txt     精确版本与依赖哈希
RELEASE_MANIFEST.json  随包文件 SHA-256 清单
SOURCE_MANIFEST.json   原 MATLAB 源码 SHA-256
```

常见安装问题见 [故障排查](docs/TROUBLESHOOTING.md)。本项目通过 GitHub Release 分发，未发布到 PyPI。原 MATLAB 文件和先前的 Python 0.1 开发目录保持原样。

公开报告中的本机绝对路径已替换为占位符；数值测量、测试结果及算法源码未改变。详见 [发布记录](docs/PUBLICATION.md)。
