# Changelog

## 0.1 - 2026-10-04

- Added separate NumPy baseline and optimized implementations, four byte-preserved MATLAB projection snapshots, and hashes of all 46 original MATLAB source files.
- Implemented a general-k threshold solver with translation, scaling, bracket protection, and active-set verification.
- Added a specialized k=2 method using at most two sorted simplex projections, with an option to force the general method for comparison.
- Added an explicit Hermitian/eigh path, column-scaled reconstruction, omission of zero spectral directions, and direct spectral reconstruction of the proximal mapping.
- Handled zero radii, empty input, scalar cases, clipping boundaries, and invalid parameters without numerical rank truncation.
- Added independent high-precision references, 20 algorithm tests, source-preservation checks, reproducible benchmarks, and records of cases that did not improve.
- Packaged offline Windows dependencies, four configurations, replayable examples, and three release tests, for 23 tests in total.
- Revised public documentation, documentation examples, wheel metadata, and Release notes to English. The version remains 0.1; algorithms, tolerances, and original MATLAB snapshots are unchanged.

The Python baseline includes necessary boundary fixes and does not reproduce the original boundary failures. Its timings do not establish MATLAB speedups. Earlier local packages and verification records are preserved.
