"""Frobenius projection onto the dual ball of the matrix Ky Fan k-norm."""
from .projection import project_dual_ball, project_singular_values, prox_ky_fan

__version__ = "0.1"
__all__ = ["project_dual_ball", "project_singular_values", "prox_ky_fan"]
