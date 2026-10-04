"""NumPy implementation, version 0.1; no spectral rank truncation.

The general-k kernel solves sum(clip(s - theta, 0, radius)) = k*radius
when the sum constraint is active. The k=2 kernel instead uses at most
two sorted simplex projections. Both retain the same convex projection.
"""
from numbers import Integral, Real

import numpy as np

_EPS = np.finfo(np.float64).eps


def _parameters(radius, k, size, method):
    if not isinstance(radius, Real) or not np.isfinite(radius) or radius < 0:
        raise ValueError("radius must be a finite nonnegative real scalar")
    if isinstance(k, (bool, np.bool_)) or not isinstance(k, Integral):
        raise ValueError("k must be an integer")
    if k < 1 or (size and k > size):
        raise ValueError("k must satisfy 1 <= k <= min(matrix.shape)")
    if method not in ("auto", "general", "k2"):
        raise ValueError("method must be 'auto', 'general', or 'k2'")
    if method == "k2" and k != 2:
        raise ValueError("the k2 method requires k=2")
    return float(radius), int(k), ("k2" if k == 2 else "general") if method == "auto" else method


def _spectrum(s, assume_sorted):
    raw = np.asarray(s)
    if raw.ndim != 1 or raw.dtype.kind not in "biuf":
        raise ValueError("s must be a one-dimensional real nonnegative spectrum")
    s = np.asarray(raw, dtype=np.float64)
    if not np.all(np.isfinite(s)) or np.any(s < 0):
        raise ValueError("s must contain finite nonnegative entries")
    if assume_sorted and np.any(s[1:] > s[:-1]):
        raise ValueError("assume_sorted=True requires descending input")
    return s


def _matrix(x, hermitian):
    raw = np.asarray(x)
    if raw.ndim != 2 or raw.dtype.kind not in "biufc":
        raise ValueError("x must be a two-dimensional numeric array")
    x = np.asarray(raw, dtype=np.complex128 if np.iscomplexobj(raw) else np.float64)
    if not np.all(np.isfinite(x)):
        raise ValueError("x must contain finite entries")
    if hermitian and (x.shape[0] != x.shape[1] or not np.array_equal(x, x.conj().T)):
        raise ValueError("hermitian=True requires an exactly Hermitian input; symmetrize explicitly if intended")
    return x


def _bounded_gaps(s, anchor, radius):
    # theta = anchor + radius*t, -1 <= t <= 0. Gaps outside [-r,r]
    # are permanently saturated/inactive throughout this bracket.
    return np.clip(s - anchor, -radius, radius) / radius


def _polish_active_set(s, radius, k, approximate):
    """Solve the affine KKT equation on a proposed active set, or reject it.

Center at the smallest free s, not at a huge absolute threshold. This
avoids cancellation when the budget is small or many free values cluster.
The cap/zero checks are exact floating-point comparisons, not rank cutoffs.
"""
    free = (approximate > 0) & (approximate < 1)
    capped = approximate == 1
    count = np.count_nonzero(free)
    if count == 0:
        if np.count_nonzero(capped) == k:
            return approximate.copy()
        return None
    anchor = float(np.min(s[free]))
    gaps = (s[free] - anchor) / radius
    remaining = (k - np.count_nonzero(capped)) - float(np.sum(gaps))
    correction = remaining / count
    values = gaps + correction
    if correction < 0 or np.any(values < 0) or np.any(values > 1):
        return None
    z = _bounded_gaps(s, anchor, radius)
    if np.any(z[~(free | capped)] + correction > 0):
        return None
    if np.any(z[capped] + correction < 1):
        return None
    p = capped.astype(np.float64)
    p[free] = values
    if abs(float(p.sum()) - k) > 32 * _EPS * max(1, k):
        return None
    return p


def _general(s, radius, k, sorted_input):
    # kth largest sk provides the radius-wide bracket
    # max(0, sk-r) <= theta <= sk, even with repeated singular values.
    anchor = float(s[k - 1] if sorted_input else np.partition(s, s.size - k)[s.size - k])
    z = _bounded_gaps(s, anchor, radius)
    lo, hi = -min(anchor, radius) / radius, 0.0
    t = lo + (hi - lo) / 2
    previous_counts = None
    for iteration in range(1, 97):
        shifted = z - t
        p = np.clip(shifted, 0.0, 1.0)
        f = float(p.sum()) - k
        free_count = np.count_nonzero((shifted > 0) & (shifted < 1))
        counts = (np.count_nonzero(shifted >= 1), free_count)
        # With a common scalar threshold, equal cap/free counts identify the
        # same sets. Avoid a full certification scan while those sets move.
        if counts == previous_counts or abs(f) <= 32 * _EPS * max(1, k):
            polished = _polish_active_set(s, radius, k, p)
            if polished is not None:
                return polished * radius, iteration
        previous_counts = counts
        if f > 0:
            lo = t
        else:
            hi = t
        proposal = t + f / free_count if free_count else np.nan
        # Periodic bisection gives finite bracket contraction even when a
        # Newton step hugs an endpoint or the derivative vanishes.
        if (iteration % 3 == 0 or not lo < proposal < hi or proposal == t):
            proposal = lo + (hi - lo) / 2
        if proposal == lo or proposal == hi:
            # At a rounding boundary, try both adjacent active sets. Do not
            # return an unverified iterate simply because progress is small.
            for endpoint in (lo, hi):
                polished = _polish_active_set(s, radius, k, np.clip(z - endpoint, 0, 1))
                if polished is not None:
                    return polished * radius, iteration
            break
        t = proposal
    raise FloatingPointError("general-k projection could not certify a floating-point active set")


def _simplex_sorted(s, radius, mass):
    """Sorted simplex projection in units of radius; mass is 1 or 2."""
    # Far negative gaps may overflow to -inf when r is tiny. They are
    # provably inactive (gap <= -mass), and are excluded before summation.
    with np.errstate(over="ignore"):
        gaps = (s - s[0]) / radius
    candidates = int(np.count_nonzero(gaps > -mass))
    gaps = gaps[:candidates]
    prefix = np.cumsum(gaps)
    counts = np.arange(1, candidates + 1)
    support = int(np.flatnonzero(gaps > (prefix - mass) / counts)[-1]) + 1
    # Recenter at the smallest supported value for an accurate mass sum.
    p = np.zeros_like(s)
    while support:
        relative = (s[:support] - s[support - 1]) / radius
        correction = (mass - float(relative.sum())) / support
        if correction >= 0:
            p[:support] = relative + correction
            return p
        support -= 1
    raise FloatingPointError("simplex support could not be determined")


def _k2(s, radius, sorted_input):
    order = None if sorted_input else np.argsort(-s, kind="stable")
    ordered = s if order is None else s[order]
    p = _simplex_sorted(ordered, radius, 2)
    steps = 1
    if p[0] > 1:
        p[0] = 1
        p[1:] = _simplex_sorted(ordered[1:], radius, 1)
        steps = 2
    if np.any(p > 1 + 8 * _EPS) or abs(float(p.sum()) - 2) > 32 * _EPS:
        raise FloatingPointError("k=2 projection failed its scalar feasibility check")
    # Clamp only possible rounding above the cap, never small positive rank.
    p = np.minimum(p, 1) * radius
    if order is not None:
        restored = np.empty_like(p)
        restored[order] = p
        p = restored
    return p, steps


def _weights(s, radius, k, method, sorted_input):
    if not s.size or radius == 0:
        return np.zeros_like(s), 0, False
    clipped = np.minimum(s, radius)
    if float(np.sum(clipped / radius)) <= k:
        return clipped, 0, False
    if method == "k2":
        p, iterations = _k2(s, radius, sorted_input)
    else:
        p, iterations = _general(s, radius, k, sorted_input)
    return p, iterations, True


def _info(p, radius, k, method, iterations, active):
    if radius and p.size:
        normalized = p / radius
        residual = max(0.0, -float(normalized.min()), float(normalized.max()) - 1,
                       (float(normalized.sum()) - k) / max(1, k))
    else:
        residual = 0.0
    return {"version": "0.1", "method": method, "iterations": iterations,
            "mass_constraint_active": active, "nonzero_spectral_values": int(np.count_nonzero(p)),
            "feasibility_residual": residual}


def project_singular_values(s, radius=1.0, k=2, *, method="auto",
                            assume_sorted=False, return_info=False):
    """Project nonnegative s onto {0 <= p <= radius, sum(p) <= k*radius}.

    method='general' works for every integer k in [1,len(s)]. method='k2'
    requires k=2; 'auto' dispatches accordingly. Empty s accepts any positive
    integer k. Inputs are not mutated. Computation uses float64.
    """
    s = _spectrum(s, assume_sorted)
    radius, k, method = _parameters(radius, k, s.size, method)
    p, iterations, active = _weights(s, radius, k, method, assume_sorted)
    if return_info:
        return p, _info(p, radius, k, method, iterations, active)
    return p


def _reconstruct(left, weights, right):
    nonzero = np.flatnonzero(weights != 0)
    if not nonzero.size:
        return np.zeros((left.shape[0], right.shape[1]), dtype=left.dtype)
    if nonzero.size == weights.size:
        return (left * weights) @ right
    return (left[:, nonzero] * weights[nonzero]) @ right[nonzero, :]


def _spectral(x, radius, k, method, hermitian, return_info, proximal):
    x = _matrix(x, hermitian)
    size = min(x.shape)
    radius, k, method = _parameters(radius, k, size, method)
    if not size or radius == 0:
        result = x.copy() if proximal else np.zeros_like(x)
        info = _info(np.zeros(size), radius, k, method, 0, False)
        info["spectral_solver"] = "none"
        return (result, info) if return_info else result
    if hermitian:
        d, left = np.linalg.eigh(x)
        if not np.all(np.isfinite(d)):
            raise FloatingPointError("eigh produced non-finite eigenvalues")
        s = np.abs(d)
        right = left.conj().T
        p, iterations, active = _weights(s, radius, k, method, False)
        weights = (s - p if proximal else p) * np.sign(d)
    else:
        left, s, right = np.linalg.svd(x, full_matrices=False)
        if not np.all(np.isfinite(s)):
            raise FloatingPointError("SVD produced non-finite singular values")
        p, iterations, active = _weights(s, radius, k, method, True)
        weights = s - p if proximal else p
    if np.array_equal(s, p):
        result = np.zeros_like(x) if proximal else x.copy()
    else:
        result = _reconstruct(left, weights, right)
        if hermitian:
            # Restore exact Hermitian storage after roundoff in multiplication.
            result = result * 0.5 + result.conj().T * 0.5
    if return_info:
        info = _info(p, radius, k, method, iterations, active)
        info["spectral_solver"] = "eigh" if hermitian else "svd"
        return result, info
    return result


def project_dual_ball(x, radius=1.0, k=2, *, method="auto", hermitian=False,
                      return_info=False):
    """Frobenius projection onto ||P||_2 <= radius, ||P||_* <= k*radius.

    Real/complex rectangular inputs use reduced SVD. hermitian=True explicitly
    selects eigh for exactly symmetric/Hermitian square inputs. No tolerance
    is used to truncate positive projected singular values.
    """
    return _spectral(x, radius, k, method, hermitian, return_info, False)


def prox_ky_fan(x, weight=1.0, k=2, *, method="auto", hermitian=False,
                 return_info=False):
    """prox_{weight * sum(top-k singular values)}(x), from one decomposition."""
    return _spectral(x, weight, k, method, hermitian, return_info, True)
