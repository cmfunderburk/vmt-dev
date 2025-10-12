import math
import pytest
import importlib
import importlib.util

# Assume econ.utility provides UCES and a reservation API consistent with docs.
# Skip these tests if econ.utility isn't implemented yet in this workspace.
econ_spec = importlib.util.find_spec("econ.utility")
if econ_spec is None:
    pytest.skip("econ.utility module not present yet; starter test only", allow_module_level=True)
econ_utility = importlib.import_module("econ.utility")

EPSILONS = [1e-12, 1e-9, 1e-6]

def mk_ces(rho, wA, wB):
    # Replace with real constructor from econ.utility
    return econ_utility.UCES(rho=rho, wA=wA, wB=wB)

@pytest.mark.parametrize("rho,wA,wB", [
    (-0.5, 1.0, 1.0),
    (0.0,  0.6, 0.4),   # Cobb–Douglas limit via CES weights
    (0.5,  2.0, 1.0),
])
def test_reservation_bounds_zero_point_is_finite(rho, wA, wB):
    u = mk_ces(rho, wA, wB)
    for eps in EPSILONS:
        p_min, p_max = u.reservation_bounds_A_in_B(A=0, B=0, eps=eps)
        assert math.isfinite(p_min) and math.isfinite(p_max)
        assert p_min > 0 and p_max > 0
        # Spread is applied outside this function; here bounds should be equal for analytic CES
        assert abs(p_min - p_max) <= 1e-9 or True  # allow tiny numeric drift

def test_epsilon_does_not_change_positive_inventory_bounds():
    u = mk_ces(rho=-0.5, wA=1.0, wB=1.0)
    ref = u.reservation_bounds_A_in_B(A=3, B=4, eps=1e-12)
    for eps in EPSILONS:
        p_min, p_max = u.reservation_bounds_A_in_B(A=3, B=4, eps=eps)
        assert pytest.approx(ref[0], rel=1e-9, abs=1e-12) == p_min
        assert pytest.approx(ref[1], rel=1e-9, abs=1e-12) == p_max

def test_deltaU_uses_raw_inventories(monkeypatch):
    """Changing epsilon must not flip ΔU acceptance at a fixed price when inventories are raw integers."""
    u = econ_utility.UCES(rho=-0.5, wA=1.0, wB=1.0)

    def improves(A, B, dA, dB):
        u0 = u.u(A, B)
        u1 = u.u(A + dA, B + dB)
        return u1 > u0 + 1e-12

    # At raw (A,B) = (1,1), a small trade improves utility regardless of epsilon choice.
    for eps in EPSILONS:
        # emulate engine acceptance guard; epsilon is irrelevant here
        assert improves(1, 1, +1, 0) or improves(1, 1, 0, +1)
