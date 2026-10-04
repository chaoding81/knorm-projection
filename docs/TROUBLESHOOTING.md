# 安装与运行排查

## 找不到 Python / py

先安装 CPython 3.12 64 位 x86-64，或显式调用解释器：

```powershell
& "C:\Path\To\Python312\python.exe" install.py
```

本包带有 NumPy 安装包，不带 Python 解释器。Windows 的商店占位命令不等于已经安装 Python。

## 平台或 Python 版本不匹配

离线依赖只适用于 CPython 3.12、Windows x86-64。其他平台/版本使用 `python install.py --online`，并满足 Python 3.11+。在线方式也只安装有官方二进制 wheel 的组合，不在本机编译 NumPy。该路径提供了脚本，尚未在 macOS/Linux 实测。

## PowerShell 不允许执行 setup.ps1

直接用 `py -3.12 install.py` 即可，不需要调整执行策略。若需要包装脚本，可对这一个进程使用 README 中的 `-ExecutionPolicy Bypass`，不更改系统长期策略。

## .venv 已存在或安装中断

已有兼容的虚拟环境会复用，不清空目录。若目录不是虚拟环境或 Python 版本不匹配，安装器停止，避免覆盖文件。可选用新路径：

```text
python install.py --venv .venv-new
```

若中断发生在 Python/pip 创建阶段，优先选一个新的虚拟环境路径重试。程序不会自动删除旧环境或历史输出。

## 写入临时目录失败

确认解压目录可写，不要直接在 ZIP 查看器内运行。可在这次终端进程中指定一个自己有权限写入的临时目录后重试；不要为此全局关闭安全设置。某些受限执行环境会拦截 Python 创建的私有临时目录，需要在正常用户终端运行安装器。

## 找不到 knorm_projection 或 NumPy

使用 `.venv\Scripts\python.exe`（Windows）或 `.venv/bin/python`（Linux/macOS），而不是另一个系统 Python。`tools/validate.py` 会检查实际导入位置，避免把源目录误当作已经安装成功。

## 哈希校验失败

重新完整解压 ZIP，并确认外部 `.sha256` 与 ZIP 匹配。若是有意修改源码或原配置，则供货文件哈希不同是预期结果；可先复制配置到新文件进行实验。维护者重新打包时需要重新生成清单，不能只把校验失败改成成功。

## Hermitian / k 参数错误

`hermitian=True` 要求精确 Hermitian 方阵；一般矩阵应设为 false。`method="k2"` 要求 k=2。非空输入还要求 k 不超过矩阵较小维数。程序不会默改这些数学条件。
