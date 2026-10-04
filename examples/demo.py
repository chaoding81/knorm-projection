"""Small executable example of both k paths and the Hermitian option."""
import numpy as np
from knorm_projection import __version__, project_dual_ball, prox_ky_fan


def main():
    rng = np.random.default_rng(7)
    x = rng.standard_normal((12, 8))
    general = project_dual_ball(x, 1, 3, method="general")
    p, info = project_dual_ball(x, 1, 2, method="k2", return_info=True)
    p_general = project_dual_ball(x, 1, 2, method="general")
    z = prox_ky_fan(x, 1, 2)
    np.testing.assert_allclose(p, p_general, atol=1e-12)
    np.testing.assert_allclose(p + z, x, atol=1e-12)
    a = rng.standard_normal((12, 12))
    h = (a + a.T) / 2
    symmetric = project_dual_ball(h, 1, 2, hermitian=True)
    np.testing.assert_allclose(symmetric, project_dual_ball(h, 1, 2), atol=1e-12)
    print("knorm_projection", __version__)
    print("general k=3 projection shape:", general.shape)
    print("k=2 diagnostics:", info)
    print("k=2/general agreement, Moreau identity, and Hermitian/SVD agreement passed.")


if __name__ == "__main__":
    main()
