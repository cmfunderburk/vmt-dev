"""
Tests for Linear utility function.
"""

import pytest
from vmt_engine.econ.utility import ULinear


def test_linear_initialization():
    """Test linear utility initialization."""
    u = ULinear(vA=1.0, vB=1.2)
    assert u.vA == 1.0
    assert u.vB == 1.2


def test_linear_invalid_values():
    """Test that non-positive values are rejected."""
    with pytest.raises(ValueError):
        ULinear(vA=0, vB=1.0)
    
    with pytest.raises(ValueError):
        ULinear(vA=1.0, vB=-1.0)


def test_linear_utility():
    """Test linear utility calculation."""
    u = ULinear(vA=2.0, vB=3.0)
    
    # Zero inventory
    assert u.u(0, 0) == 0.0
    
    # Positive inventory
    assert u.u(10, 0) == 20.0
    assert u.u(0, 10) == 30.0
    assert u.u(10, 10) == 50.0


def test_linear_mrs():
    """Test that linear MRS is constant."""
    u = ULinear(vA=2.0, vB=3.0)
    
    mrs1 = u.mrs_A_in_B(10, 10)
    mrs2 = u.mrs_A_in_B(5, 20)
    mrs3 = u.mrs_A_in_B(100, 5)
    
    # All should equal vA / vB
    expected = 2.0 / 3.0
    assert mrs1 == pytest.approx(expected)
    assert mrs2 == pytest.approx(expected)
    assert mrs3 == pytest.approx(expected)


def test_linear_reservation_bounds():
    """Test linear reservation bounds."""
    u = ULinear(vA=2.0, vB=3.0)
    
    p_min, p_max = u.reservation_bounds_A_in_B(10, 10)
    
    # Should be constant (MRS)
    expected = 2.0 / 3.0
    assert p_min == pytest.approx(expected)
    assert p_max == pytest.approx(expected)
    
    # Should be same for any inventory
    p_min2, p_max2 = u.reservation_bounds_A_in_B(0, 0)
    assert p_min2 == pytest.approx(expected)
    assert p_max2 == pytest.approx(expected)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

