# Installation and runtime troubleshooting

## Python or py is not found

Install 64-bit CPython 3.12 for Windows x86-64, or invoke an existing interpreter:

```powershell
& "C:\Path\To\Python312\python.exe" install.py
```

The bundle includes NumPy wheels; Python must be installed separately. A Windows Store command alias does not establish that an interpreter is installed.

## Platform or Python version mismatch

Offline installation requires CPython 3.12 on Windows x86-64. For another supported combination, use `python install.py --online` with Python 3.11+. Only compatible official binary wheels are accepted; NumPy is not compiled locally. The macOS/Linux wrappers have not been executed in the release verification environment.

## PowerShell blocks setup.ps1

Run `py -3.12 install.py` directly. To use the wrapper, the README shows a process-local `-ExecutionPolicy Bypass` option. No persistent policy change is required.

## An environment already exists, or installation was interrupted

A compatible environment is reused without clearing its directory. The installer stops if the target is not a virtual environment or uses a different Python version. Choose another path when needed:

```text
python install.py --venv .venv-new
```

If installation stopped during Python or pip initialization, retry with a new environment path. Old environments and historical outputs are not deleted automatically.

## Temporary-directory permission errors

Extract the ZIP into a writable directory. If necessary, select a writable temporary directory for the current terminal process. Some restricted environments cannot access Python's private temporary directories; use a normal user terminal in that case. A global security-policy change is not required.

## knorm_projection or NumPy cannot be imported

Use `.venv\Scripts\python.exe` on Windows or `.venv/bin/python` on Linux/macOS. `tools/validate.py` checks the import location so a source-tree import is not mistaken for an installed-wheel check.

## A checksum does not match

Check the ZIP against its accompanying `.sha256` file, then extract it again. Intentional edits to shipped files change their hashes; use a copied configuration for experiments. Maintainers must regenerate the manifest when rebuilding and must not suppress failed integrity checks.

## Invalid Hermitian or k options

`hermitian=True` requires an exactly Hermitian square matrix. Use false for general matrices. `method="k2"` requires k=2, and k must not exceed the smaller dimension of nonempty input. These mathematical conditions are not changed silently.
