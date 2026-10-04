# k-norm projection algorithm, version 0.1

This document records the algorithm and its development-stage verification. See the [README](../README.md) for installation and configuration. Portable release checks use the bundled source snapshots by default.

The package provides the Frobenius projection onto a matrix Ky Fan k-norm dual ball and the corresponding proximal mapping. Four original MATLAB projection files are preserved byte-for-byte in `original_matlab/`.

## Scope and implementation

- `knorm_projection/baseline.py` follows `Projdualk -> HKLineq -> HKLeq`: full reduced SVD, sorting and binary search over 2q breakpoints, and explicit diagonal reconstruction. It adds validation and necessary zero-radius, empty-input, scalar, and clipping-boundary handling.
- `knorm_projection/projection.py` contains separate optimized general-k and k=2 paths.
- `tests/test_projection.py` checks independent high-precision references, feasibility, variational inequalities, idempotence, Moreau/Fenchel relations, and boundary cases.
- `benchmarks/benchmark.py` compares methods on identical inputs under the same accuracy gate.
- `SOURCE_MANIFEST.json` records hashes of 46 original MATLAB files and identifies the four bundled snapshots.
- `tools/validate.py` runs installed-package and preservation checks and saves verification records.
- `reports/` contains the historical checks and formal benchmarks cited below. New benchmark runs create timestamped directories under `results/`.

This version covers projection routines. It does not port FMMC, ALM, or PPA outer solvers, and its Python measurements do not establish MATLAB speedups.

## Mathematical definition

For $X\in\mathbb C^{m\times n}$, let $q=\min(m,n)$, $r\ge0$, and let k be an integer with $1\le k\le q$. Compute

$$
P=\operatorname*{argmin}_{Y}\frac12\|Y-X\|_F^2,
\qquad \|Y\|_2\le r,\quad \|Y\|_*\le kr.
$$

These constraints define the dual ball of the matrix Ky Fan k-norm. They differ from the primal-ball constraint `sum(top-k singular values) <= r`.

For $X=U\operatorname{Diag}(s)V^*$, the projection is $P=U\operatorname{Diag}(p)V^*$, where

$$
p_i=\min\{r,\max(s_i-\theta,0)\},\qquad
\theta\ge0,\quad \sum_i p_i\le kr,\quad
\theta\left(\sum_i p_i-kr\right)=0.
$$

`prox_ky_fan(X, r, k)` is the proximal mapping of $r\|\cdot\|_{(k)}$, where the Ky Fan k-norm sums the k largest singular values. It reconstructs directly from `s-p`, avoiding subtraction of two separately reconstructed matrices.

## General-k method

First compute `p=min(s,r)` and return it when the sum constraint is satisfied. Otherwise, solve the monotone, piecewise-linear threshold equation.

Let $s_k$ be the kth largest singular value. A root can be chosen in

$$
\max(0,s_k-r)\le\theta\le s_k.
$$

At the lower endpoint, either the first k entries are capped or the endpoint is zero, where the sum constraint is known to be violated. At the upper endpoint, at most k-1 entries can be positive. Substituting `theta=s_k+r*t` puts the search interval within [-1,0]. Gaps outside the relevant spectral range can be clipped without changing projection values over this interval. This avoids subtracting a large absolute threshold from similarly large values.

The method uses safeguarded Newton steps. Bisection is forced on every third iteration and is also used when the free set is empty or a Newton proposal leaves the bracket. Once the active set stabilizes, the method resolves the mass constraint relative to its smallest free spectral value and verifies the cap, zero, and total-mass conditions. Failure to verify a valid floating-point active set within 96 iterations raises `FloatingPointError`.

Each iteration performs O(q) vector work. Sorted input supplies $s_k$ directly; unsorted input uses `partition`. The iteration count depends on the input, so an unconditional O(q) cost is not claimed for the complete general-k method. The optimization avoids sorting 2q breakpoints and repeating full certification scans while the active set moves.

## Specialized k=2 method

For descending singular values, first check `sum(min(s,r)) <= 2*r`. If this fails, define $\Delta_c=\{x\ge0:\sum_i x_i=c\}$ and compute $u=\Pi_{\Delta_{2r}}(s)$. Then

$$
p=\begin{cases}
u,&u_1\le r,\\
\left(r,\Pi_{\Delta_r}(s_{2:q})\right),&u_1>r.
\end{cases}
$$

If $u_1>r$, fixing the first entry at r increases the remaining mass from $2r-u_1$ to r. The tail threshold can only decrease, so the first entry remains capped. The nonnegative tail has total mass r and cannot violate an individual cap. This gives an exact reduction to at most two simplex projections.

Prefix sums determine the simplex support, followed by recentering to reduce cancellation. The path costs O(q) for sorted input; unsorted vectors are sorted first. Singular values from the matrix SVD path are already sorted.

k=2 does not impose rank two. For q>2 and r=1, the identity projects to `(2/q)*I`, which has full rank. Version 0.1 computes the full required spectrum without fixed-rank approximation or partial SVD.

## Matrix operations and interface

- General real or complex rectangular input uses `numpy.linalg.svd(..., full_matrices=False)`.
- `hermitian=True` selects `eigh` and requires an exactly Hermitian matrix. The caller decides whether to remove small asymmetry beforehand.
- Reconstruction scales columns without forming a diagonal matrix. Only zero coefficients from the projection formula are omitted; no rank tolerance removes small positive values.
- Inputs are preserved. Computation and output use float64 or complex128; integer and lower-precision inputs are converted.
- At r=0, projection returns zero and the proximal mapping returns X. Empty matrices retain their shape and accept any positive integer k. Nonempty input requires $1\le k\le q$.
- Nonfinite values, negative radii, invalid k, and invalid shapes raise errors. Nonfinite decomposition results are not reported as success.
- `return_info=True` returns the result and diagnostics: method, scalar iteration/simplex counts, sum-constraint status, nonzero coefficient count, normalized feasibility residual, and decomposition method. Feasibility alone does not measure full projection error or establish optimality.

See NumPy's [SVD](https://numpy.org/doc/stable/reference/generated/numpy.linalg.svd.html) and [eigh](https://numpy.org/doc/stable/reference/generated/numpy.linalg.eigh.html) documentation for the decomposition conventions.

## Recorded verification and performance

Date: 2026-10-04. The 20 algorithm tests passed. Coverage includes all valid k for small enumerated spectra, an independent 500-digit Decimal threshold reference, repeated and near-breakpoint spectra, extreme spectrum/radius scales, a free cluster with 10002 entries, complex rectangular matrices, symmetric indefinite matrices, idempotence, variational inequalities, and Moreau/Fenchel relations. Hash checks also covered 46 original MATLAB files and four snapshots.

Records: [validation.json](../reports/validation_20261004T103153162134Z/validation.json) and [test log](../reports/validation_20261004T103153162134Z/tests.log).

The formal [benchmark](../reports/benchmark_20261004T103212641128Z/benchmark.json) uses seed 20261004, NumPy 2.3.5, OpenBLAS 0.3.30, and a cooperative request for one BLAS thread. After warm-up, each method is timed in seven batches, reporting median per-call time. Methods use identical inputs, radii, k, and a 1e-10 accuracy gate. The largest recorded baseline discrepancy is about 6.05e-15; the largest normalized feasibility residual is about 1.91e-14. Matrix timings include validation, decomposition, and reconstruction, with additional result checks outside the timed region.

| Case | Python baseline | Version 0.1 path | Baseline / optimized time |
|---|---:|---:|---:|
| Vector q=4096, k=2 | 235.0 us | k2: 86.4 us | 2.72 |
| Vector q=32768, k=2 | 1845.4 us | k2: 631.5 us | 2.92 |
| Vector q=4096, k=1024 | 233.7 us | general: 166.0 us | 1.41 |
| Vector q=32768, k=8192 | 1219.1 us | general: 1044.9 us | 1.17 |
| Symmetric 384-by-384 matrix, k=2 | 38.16 ms | eigh + k2: 18.56 ms | 2.06 |
| Symmetric 384-by-384 matrix, k=96 | 36.83 ms | eigh + general: 20.44 ms | 1.80 |

Some cases did not improve: general k was about 12% slower for q=256, k=64, and the general matrix SVD path was about 9% slower for a 256-by-192 matrix with k=2. The tested symmetric cases benefited from eigh; rectangular-matrix gains were smaller or inconsistent. Vector-kernel ratios are not matrix-projection or outer-solver speedups.

These finite synthetic Python experiments do not establish MATLAB performance, FMMC convergence, correctness for every floating-point input, or performance on other platforms. Independent Decimal and geometric checks supplement comparisons with the original implementation.
