"""Behavioral checks; expectations use geometry or independent root solves."""
from decimal import Decimal, localcontext
from itertools import combinations_with_replacement
import importlib
import unittest

import numpy as np

try:
    api = importlib.import_module("knorm_projection")
except ModuleNotFoundError:
    api = None


def oracle(s, radius, k):
    """Independent high-precision monotone root (small test vectors only)."""
    with localcontext() as context:
        context.prec = 500
        a = [Decimal.from_float(float(v)) for v in s]
        r = Decimal.from_float(float(radius))
        mass = k * r
        clip = lambda theta: [min(r, max(Decimal(0), v - theta)) for v in a]
        if r == 0 or not a:
            return np.zeros(len(a))
        if sum(clip(Decimal(0))) <= mass:
            return np.array([float(v) for v in clip(Decimal(0))])
        lo, hi = Decimal(0), max(a)
        for _ in range(1800):
            mid = (lo + hi) / 2
            values = clip(mid)
            if abs(sum(values) - mass) <= r * Decimal("1e-40"):
                break
            if sum(values) > mass:
                lo = mid
            else:
                hi = mid
        return np.array([float(v) for v in values])


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(api, "Python projection package has not been implemented")

    def close(self, actual, expected, scale=1.0, tolerance=5e-12):
        actual, expected = np.asarray(actual), np.asarray(expected)
        np.testing.assert_allclose(actual / scale, expected / scale,
                                   rtol=tolerance, atol=tolerance)

    def test_scalar_and_zero_radius(self):
        self.close(api.project_dual_ball([[2.0]], 1.0, 1), [[1.0]])
        self.close(api.project_dual_ball([[2.0]], 0.0, 1), [[0.0]])
        self.close(api.prox_ky_fan([[2.0]], 0.0, 1), [[2.0]])

    def test_empty_matrices_keep_shape(self):
        for shape in ((0, 0), (0, 4), (3, 0)):
            self.assertEqual(api.project_dual_ball(np.empty(shape), 1, 2).shape, shape)

    def test_hand_computed_general_k(self):
        fixtures = [([4, 2, 1], 1, 1, [1, 0, 0]),
                    ([4, 2, 1], 1, 2, [1, 1, 0]),
                    ([4, 2, 1], 1, 3, [1, 1, 1]),
                    ([3, 3, 3, 3], 1, 3, [0.75] * 4),
                    ([0.2, 0.1, 0], 1, 2, [0.2, 0.1, 0])]
        for s, r, k, expected in fixtures:
            with self.subTest(s=s, k=k):
                self.close(api.project_singular_values(s, r, k, method="general"), expected)

    def test_k2_both_special_branches(self):
        fixtures = [([3, 3, 3, 3], [0.5] * 4),
                    ([10, 1, 1, 1], [1, 1/3, 1/3, 1/3]),
                    ([2, 1, 0, 0], [1, 1, 0, 0])]
        for s, expected in fixtures:
            self.close(api.project_singular_values(s, 1, 2, method="k2"), expected)

    def test_general_small_exhaustive_spectra(self):
        for n in range(1, 6):
            for vals in combinations_with_replacement((0.0, 0.5, 1.5, 3.0), n):
                for k in range(1, n + 1):
                    expected = oracle(vals, 1.0, k)
                    self.close(api.project_singular_values(vals, 1, k, method="general"), expected)
                    if k == 2:
                        self.close(api.project_singular_values(vals, 1, k, method="k2"), expected)

    def test_random_general_k_and_k2_against_oracle(self):
        rng = np.random.default_rng(20261004)
        for n in (2, 3, 7, 16):
            for scale in (1e-100, 1.0, 1e100):
                for _ in range(4):
                    s = np.abs(rng.normal(size=n)) * 4 * scale
                    r = scale * rng.uniform(0.1, 1.5)
                    for k in sorted({1, 2, max(1, n // 2), n}):
                        p = api.project_singular_values(s, r, k, method="general")
                        self.close(p, oracle(s, r, k), scale=r)
                        if k == 2:
                            self.close(api.project_singular_values(s, r, k, method="k2"), p, scale=r)

    def test_large_common_offset_and_tiny_radius(self):
        for s, r, k in [([1e200] * 5, 1e-100, 2),
                        ([1e200] * 5, 1e-100, 3),
                        ([1e16, 1e16, 1e16, 0], 1, 2),
                        ([5, 5, 5, 5], 1e-200, 1)]:
            p = api.project_singular_values(s, r, k, method="general")
            self.close(p, oracle(s, r, k), scale=r)
            if k == 2:
                self.close(api.project_singular_values(s, r, k, method="k2"), p, scale=r)

    def test_dense_free_cluster_keeps_mass_accuracy(self):
        s = np.r_[1.0, 1.0, np.full(10000, 0.5)]
        expected = np.r_[0.5 + 1/10002, 0.5 + 1/10002,
                         np.full(10000, 1/10002)]
        for method in ("general", "k2"):
            p = api.project_singular_values(s, 1, 2, method=method)
            self.close(p, expected)
            self.assertLess(abs(p.sum() - 2), 2e-13)

    def test_permutation_equivariance_and_no_input_mutation(self):
        s = np.array([1.0, 7.0, 2.0, 7.0, 0.0])
        before = s.copy()
        perm = np.array([3, 4, 0, 1, 2])
        for method in ("general", "k2"):
            p = api.project_singular_values(s, 1, 2, method=method)
            pp = api.project_singular_values(s[perm], 1, 2, method=method)
            self.close(pp, p[perm])
        np.testing.assert_array_equal(s, before)

    def test_neighbors_of_zero_and_cap_breakpoints(self):
        base = np.array([4., 3., 2.5, 2.5, 2., 1., 0.])
        for index in (1, 2, 4):
            for direction in (-np.inf, np.inf):
                s = base.copy()
                s[index] = np.nextafter(s[index], direction)
                for k in (2, 3, 4):
                    self.close(api.project_singular_values(s, 1, k, method="general"),
                               oracle(s, 1, k))
                    if k == 2:
                        self.close(api.project_singular_values(s, 1, k, method="k2"),
                                   oracle(s, 1, k))

    def test_projection_variational_inequality(self):
        rng = np.random.default_rng(83)
        for n, k in ((6, 2), (9, 4), (12, 1)):
            for _ in range(20):
                s = np.abs(rng.normal(size=n)) * 3
                p = api.project_singular_values(s, 1, k)
                for _ in range(10):
                    y = rng.random(n)
                    y *= min(1, k / y.sum())
                    self.assertLessEqual(float((s - p) @ (y - p)), 1e-11)

    def test_k2_projection_can_be_full_rank(self):
        x = np.eye(9)
        self.close(api.project_dual_ball(x, 1, 2), np.eye(9) * (2/9))

    def test_matrix_shapes_complex_values_and_moreau_optimality(self):
        rng = np.random.default_rng(4)
        for shape in ((3, 7), (7, 3), (5, 5)):
            for is_complex in (False, True):
                x = rng.normal(size=shape)
                if is_complex:
                    x = x + 1j * rng.normal(size=shape)
                before = x.copy()
                for k in (1, 2, min(shape)):
                    p = api.project_dual_ball(x, 0.7, k)
                    z = api.prox_ky_fan(x, 0.7, k)
                    self.close(p + z, x)
                    sigma = np.linalg.svd(p, compute_uv=False)
                    self.assertLessEqual(sigma[0], 0.7 + 1e-12)
                    self.assertLessEqual(sigma.sum(), 0.7 * k + 1e-12)
                    rhs = 0.7 * np.linalg.svd(z, compute_uv=False)[:k].sum()
                    self.assertLess(abs(np.vdot(p, z).real - rhs), 1e-10)
                np.testing.assert_array_equal(x, before)

    def test_hermitian_eigh_matches_svd_with_negative_and_repeated_eigenvalues(self):
        rng = np.random.default_rng(21)
        for is_complex in (False, True):
            a = rng.normal(size=(8, 8))
            if is_complex:
                a = a + 1j * rng.normal(size=(8, 8))
            q, _ = np.linalg.qr(a)
            x = (q * np.array([-3, -3, -1, 0, 0, 1, 3, 3])) @ q.conj().T
            x = (x + x.conj().T) / 2
            for k in (1, 2, 5, 8):
                p = api.project_dual_ball(x, 1, k, hermitian=True)
                self.close(p, api.project_dual_ball(x, 1, k))
                self.close(api.project_dual_ball(p, 1, k), p)

    def test_hermitian_flag_does_not_silently_symmetrize(self):
        with self.assertRaises(ValueError):
            api.project_dual_ball([[1, 2], [0, 1]], 1, 2, hermitian=True)

    def test_small_positive_components_are_not_rank_truncated(self):
        x = np.diag([0.5, 1e-16, 0.0])
        p = api.project_dual_ball(x, 1, 2)
        np.testing.assert_array_equal(p, x)

    def test_large_finite_hermitian_result_does_not_overflow_when_symmetrizing(self):
        x = np.diag([1.7e308, 0.0])
        p = api.project_dual_ball(x, 1.6e308, 1, hermitian=True)
        self.assertTrue(np.all(np.isfinite(p)))
        self.close(p / 1.6e308, np.diag([1.0, 0.0]))

    def test_baseline_matches_regular_domain(self):
        baseline = importlib.import_module("knorm_projection.baseline")
        rng = np.random.default_rng(37)
        for n in (1, 3, 9, 50):
            s = np.sort(np.abs(rng.normal(size=n)) * 3)[::-1]
            for k in sorted({1, min(2, n), n}):
                self.close(baseline.project_singular_values(s, 1, k),
                           api.project_singular_values(s, 1, k))
        x = rng.normal(size=(9, 6))
        self.close(baseline.project_dual_ball(x, 1, 3), api.project_dual_ball(x, 1, 3))

    def test_diagnostics_and_forced_dispatch(self):
        for method, expected_method in (("auto", "k2"), ("k2", "k2"), ("general", "general")):
            p, info = api.project_singular_values([3, 3, 3], 1, 2, method=method, return_info=True)
            self.close(p, [2/3] * 3)
            self.assertEqual(info["method"], expected_method)
            self.assertLessEqual(info["feasibility_residual"], 1e-12)
        with self.assertRaises(ValueError):
            api.project_singular_values([1, 2, 3], 1, 3, method="k2")

    def test_invalid_parameters_fail_explicitly(self):
        for k in (0, -1, 4, 1.5, True):
            with self.subTest(k=k), self.assertRaises((TypeError, ValueError)):
                api.project_singular_values([1, 2, 3], 1, k)
        for radius in (-1, np.nan, np.inf):
            with self.assertRaises(ValueError):
                api.project_singular_values([1, 2, 3], radius, 2)
        for s in ([1, np.inf], [1, np.nan], [-1, 2], [[1, 2]]):
            with self.assertRaises(ValueError):
                api.project_singular_values(s, 1, 2)
        with self.assertRaises(ValueError):
            api.project_dual_ball([1, 2], 1, 2)
        with self.assertRaises(ValueError):
            api.project_singular_values([1, 2], 1, 2, assume_sorted=True)


if __name__ == "__main__":
    unittest.main()
