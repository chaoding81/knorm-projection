# Provenance and third-party dependencies

- `original_matlab/` preserves four original projection files and their existing references. Their hashes are recorded in `SOURCE_MANIFEST.json`. This release does not assign or infer new license terms for those files.
- The Python projection code is version 0.1 of this project. Baseline and optimized implementations are kept separately for research and reproducibility. Existing attribution and copyright information are retained.
- NumPy 2.3.5 is the only third-party runtime dependency. The bundled Windows wheel was downloaded from official PyPI and checked against its published SHA-256. The URL, file metadata, and hashes of published wheels are in `wheelhouse/NUMPY_PROVENANCE.json`.
- The unmodified NumPy wheel includes license texts in its `.dist-info` directory, including notices for components such as OpenBLAS. See the [NumPy release page](https://pypi.org/project/numpy/2.3.5/).
- Installation uses pip and venv from the user's Python installation and does not modify the global Python environment.
