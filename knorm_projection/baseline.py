"""Readable Python baseline of Projdualk/HKLineq/HKLeq, kept for comparison.

Retains full reduced SVD, a sorted 2q-breakpoint binary search, and explicit
diagonal reconstruction. Adds only input validation and zero/empty/scalar/
clipped-boundary handling. It is not a MATLAB timing baseline. Extreme scales
and large common offsets should use the optimized implementation.
"""
import numpy as np

from .projection import _matrix, _parameters, _spectrum


def project_singular_values(s, radius=1.0, k=2):
    s = _spectrum(s, False)
    radius, k, _ = _parameters(radius, k, s.size, "general")
    if not s.size or radius == 0:
        return np.zeros_like(s)
    p = np.minimum(s, radius)
    mass = k * radius
    if p.sum() <= mass:
        return p
    breaks = np.sort(np.r_[s - radius, s])
    lo, hi = 0, breaks.size - 1
    left_mass, right_mass = s.size * radius, 0.0
    while hi - lo > 1:
        middle = (lo + hi) // 2
        values = np.clip(s - breaks[middle], 0, radius)
        total = float(values.sum())
        if total == mass:
            return values
        if total > mass:
            lo, left_mass = middle, total
        else:
            hi, right_mass = middle, total
    theta = breaks[lo] + (breaks[hi] - breaks[lo]) * (mass - left_mass) / (right_mass - left_mass)
    return np.clip(s - theta, 0, radius)


def project_dual_ball(x, radius=1.0, k=2):
    x = _matrix(x, False)
    radius, k, _ = _parameters(radius, k, min(x.shape), "general")
    if not min(x.shape) or radius == 0:
        return np.zeros_like(x)
    u, s, vh = np.linalg.svd(x, full_matrices=False)
    if s[0] <= radius and s.sum() <= k * radius:
        return x.copy()
    p = project_singular_values(s, radius, k)
    return u @ np.diag(p) @ vh


def prox_ky_fan(x, weight=1.0, k=2):
    x = _matrix(x, False)
    return x - project_dual_ball(x, weight, k)
