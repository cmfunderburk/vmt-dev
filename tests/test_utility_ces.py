"""
Tests for CES utility function.
"""

import pytest
from vmt_engine.econ.utility import UCES


def test_ces_initialization():
    """Test CES utility initialization."""
    u = UCES(rho=-0.5, wA=1.0, wB=1.0)
    assert u.rho == -0.5
    assert u.wA == 1.0
    assert u.wB == 1.0


def test_ces_invalid_rho():
    """Test that rho=1.0 is rejected."""
    with pytest.raises(ValueError):
        UCES(rho=1.0, wA=1.0, wB=1.0)


def test_ces_invalid_weights():
    """Test that non-positive weights are rejected."""
    with pytest.raises(ValueError):
        UCES(rho=-0.5, wA=0, wB=1.0)
    
    with pytest.raises(ValueError):
        UCES(rho=-0.5, wA=1.0, wB=-1.0)


def test_ces_utility_positive_inventory():
    """Test CES utility with positive inventory."""
    u = UCES(rho=-0.5, wA=1.0, wB=1.0)
    
    # Both goods positive
    utility = u.u(10, 10)
    assert utility > 0
    
    # Different amounts
    u1 = u.u(10, 5)
    u2 = u.u(5, 10)
    assert u1 > 0
    assert u2 > 0


def test_ces_utility_zero_inventory():
    """Test CES utility with zero inventory."""
    u = UCES(rho=-0.5, wA=1.0, wB=1.0)
    
    # Both zero
    assert u.u(0, 0) == 0.0
    
    # One zero (with negative rho, utility should be 0)
    assert u.u(10, 0) == 0.0
    assert u.u(0, 10) == 0.0


def test_ces_mrs():
    """Test CES MRS calculation."""
    u = UCES(rho=-0.5, wA=1.0, wB=1.0)
    
    # Equal amounts
    mrs = u.mrs_A_in_B(10, 10)
    assert mrs > 0
    
    # Different amounts
    mrs1 = u.mrs_A_in_B(10, 5)
    mrs2 = u.mrs_A_in_B(5, 10)
    assert mrs1 > 0
    assert mrs2 > 0


def test_ces_reservation_bounds():
    """Test CES reservation bounds."""
    u = UCES(rho=-0.5, wA=1.0, wB=1.0)
    
    # Positive inventory
    p_min, p_max = u.reservation_bounds_A_in_B(10, 10)
    assert p_min > 0
    assert p_max > 0
    assert p_min == pytest.approx(p_max)  # Should be equal for analytic MRS
    
    # Zero inventory (should use epsilon shift)
    p_min, p_max = u.reservation_bounds_A_in_B(0, 0, eps=1e-12)
    assert p_min > 0
    assert p_max > 0
    assert p_min == pytest.approx(p_max)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

