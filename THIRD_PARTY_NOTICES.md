# 来源与第三方依赖

- `original_matlab/` 保留原项目四个投影文件的原始内容及原有论文引用；完整哈希记录见 `SOURCE_MANIFEST.json`。本 release 不为原 MATLAB 代码附加或推断新的授权条款。
- Python 投影源码来自本项目的 0.1 版本；基线和优化版分开保存，供研究与复现。本仓库及 GitHub Release 保留原有来源和版权信息。
- 唯一运行时第三方依赖是 NumPy 2.3.5。随包 Windows wheel 直接取自官方 PyPI，并核对其发布的 SHA-256。来源 URL、文件信息和各平台 wheel 哈希见 `wheelhouse/NUMPY_PROVENANCE.json`。
- NumPy wheel 自带 `.dist-info` 中的许可证及所含 OpenBLAS 等组件的许可文本，wheel 保持原样，未删除这些文件。[NumPy 发布页](https://pypi.org/project/numpy/2.3.5/)
- pip/venv 使用用户 Python 安装自带的工具；release 不改动用户的全局 Python 环境。
