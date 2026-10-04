# v0.1 publication record

Repository: <https://github.com/chaoding81/knorm-projection>.

The three files in `knorm_projection/` and four snapshots in `original_matlab/` are byte-identical to the previously validated local 0.1 implementation.

Publication preparation changed distribution and report metadata:

- Added repository, Release, and complete-ZIP links.
- Replaced local absolute paths with `${PYTHON}`, `${SOURCE_ROOT}`, `${VENV}`, `${OUTPUTS}`, or `${BUILD_ROOT}` placeholders, preserving numerical measurements and test outcomes.
- Updated public report locations and hashes while retaining original output hashes. Historical source hashes still identify the code tested at the time; those records are not presented as new executions.
- Rebuilt the wheel with current documentation and regenerated dependency hashes, the release manifest, and ZIP checksum.
- Added Git ignore and byte-preservation rules. Environments, caches, installation-test directories, and temporary builds are excluded from the repository.

## English revision

At the user's request, public documentation, documentation examples, wheel metadata, and Release notes are now in English. The Python source, comments, errors, and installer scripts were already in English and remain unchanged.

The existing `v0.1` source tag and Release attachments are updated together for this language correction. The software version remains 0.1. The model, algorithms, tolerances, and benchmark measurements are unchanged; earlier local archives and the previous Git commit are preserved.

Rebuilding changes the distribution checksum. Use the `.sha256` file supplied with the current Release assets.

The complete bundle provides offline dependencies for CPython 3.12 on Windows x86-64. Other supported combinations use online installation. The runtime dependency is pinned to NumPy 2.3.5.
