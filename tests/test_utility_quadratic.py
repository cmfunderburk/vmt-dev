"""
Tests for Quadratic utility function.
"""

import pytest
from vmt_engine.econ.utility import UQuadratic


def test_quadratic_initialization():
    """Test quadratic utility initialization."""
    u = UQuadratic(A_star=10.0, B_star=10.0, sigma_A=5.0, sigma_B=5.0, gamma=0.2)
    assert u.A_star == 10.0
    assert u.B_star == 10.0
    assert u.sigma_A == 5.0
    assert u.sigma_B == 5.0
    assert u.gamma == 0.2


def test_quadratic_invalid_bliss_points():
    """Test that non-positive bliss points are rejected."""
    with pytest.raises(ValueError, match="Bliss points must be positive"):
        UQuadratic(A_star=0, B_star=10.0, sigma_A=5.0, sigma_B=5.0)
    
    with pytest.raises(ValueError, match="Bliss points must be positive"):
        UQuadratic(A_star=10.0, B_star=-1.0, sigma_A=5.0, sigma_B=5.0)


def test_quadratic_invalid_curvature():
    """Test that non-positive curvature parameters are rejected."""
    with pytest.raises(ValueError, match="Curvature parameters must be positive"):
        UQuadratic(A_star=10.0, B_star=10.0, sigma_A=0, sigma_B=5.0)
    
    with pytest.raises(ValueError, match="Curvature parameters must be positive"):
        UQuadratic(A_star=10.0, B_star=10.0, sigma_A=5.0, sigma_B=-1.0)


def test_quadratic_invalid_gamma():
    """Test that negative gamma is rejected."""
    with pytest.raises(ValueError, match="gamma must be non-negative"):
        UQuadratic(A_star=10.0, B_star=10.0, sigma_A=5.0, sigma_B=5.0, gamma=-0.1)


def test_quadratic_utility_at_bliss():
    """Test quadratic utility at bliss point."""
    u = UQuadratic(A_star=10.0, B_star=10.0, sigma_A=5.0, sigma_B=5.0, gamma=0.0)
    
    # At bliss point, utility should be 0
    assert u.u(10, 10) == pytest.approx(0.0)


def test_quadratic_utility_below_bliss():
    """Test quadratic utility below bliss point (U < 0 but MU > 0)."""
    u = UQuadratic(A_star=10.0, B_star=10.0, sigma_A=5.0, sigma_B=5.0, gamma=0.0)
    
    # Below bliss point, utility is negative
    utility = u.u(5, 5)
    assert utility < 0
    
    # But marginal utilities should be positive (moving toward bliss)
    mu_A = u.mu_A(5, 5)
    mu_B = u.mu_B(5, 5)
    assert mu_A > 0
    assert mu_B > 0


def test_quadratic_utility_above_bliss():
    """Test quadratic utility above bliss point (U < 0 and MU < 0)."""
    u = UQuadratic(A_star=10.0, B_star=10.0, sigma_A=5.0, sigma_B=5.0, gamma=0.0)
    
    # Above bliss point, utility is negative
    utility = u.u(15, 15)
    assert utility < 0
    
    # Marginal utilities should be negative (satiation)
    mu_A = u.mu_A(15, 15)
    mu_B = u.mu_B(15, 15)
    assert mu_A < 0
    assert mu_B < 0


def test_quadratic_marginal_utilities_at_bliss():
    """Test that marginal utilities are zero at bliss point."""
    u = UQuadratic(A_star=10.0, B_star=10.0, sigma_A=5.0, sigma_B=5.0, gamma=0.0)
    
    mu_A = u.mu_A(10, 10)
    mu_B = u.mu_B(10, 10)
    
    assert mu_A == pytest.approx(0.0)
    assert mu_B == pytest.approx(0.0)


def test_quadratic_mrs_undefined_at_bliss():
    """Test that MRS returns None at bliss point."""
    u = UQuadratic(A_star=10.0, B_star=10.0, sigma_A=5.0, sigma_B=5.0, gamma=0.0)
    
    mrs = u.mrs_A_in_B(10, 10)
    assert mrs is None


def test_quadratic_mrs_defined_away_from_bliss():
    """Test that MRS is well-defined away from bliss point."""
    u = UQuadratic(A_star=10.0, B_star=10.0, sigma_A=5.0, sigma_B=5.0, gamma=0.0)
    
    # Below bliss
    mrs = u.mrs_A_in_B(5, 5)
    assert mrs is not None
    assert mrs > 0
    
    # Above bliss (both MU negative, so MRS positive)
    mrs = u.mrs_A_in_B(15, 15)
    assert mrs is not None


def test_quadratic_reservation_bounds_standard():
    """Test reservation bounds when both MU are positive."""
    u = UQuadratic(A_star=10.0, B_star=10.0, sigma_A=5.0, sigma_B=5.0, gamma=0.0)
    
    # Below bliss: both MU positive
    p_min, p_max = u.reservation_bounds_A_in_B(5, 5)
    assert p_min == p_max  # Should equal MRS
    assert p_min > 0


def test_quadratic_reservation_bounds_satiation():
    """Test reservation bounds when agent is saturated."""
    u = UQuadratic(A_star=10.0, B_star=10.0, sigma_A=5.0, sigma_B=5.0, gamma=0.0)
    
    # Both MU <= 0: no feasible trade
    p_min, p_max = u.reservation_bounds_A_in_B(15, 15)
    assert p_min > p_max  # Indicates no trade


def test_quadratic_reservation_bounds_give_away_A():
    """Test reservation bounds when agent wants to give away A (MU_A <= 0)."""
    u = UQuadratic(A_star=10.0, B_star=10.0, sigma_A=5.0, sigma_B=5.0, gamma=0.0)
    
    # A above bliss, B below bliss: MU_A < 0, MU_B > 0
    p_min, p_max = u.reservation_bounds_A_in_B(15, 5)
    assert p_min == pytest.approx(1e-12)  # Willing to sell at epsilon
    assert p_max == pytest.approx(1e-12)


def test_quadratic_reservation_bounds_give_away_B():
    """Test reservation bounds when agent wants to give away B (MU_B <= 0)."""
    u = UQuadratic(A_star=10.0, B_star=10.0, sigma_A=5.0, sigma_B=5.0, gamma=0.0)
    
    # A below bliss, B above bliss: MU_A > 0, MU_B < 0
    p_min, p_max = u.reservation_bounds_A_in_B(5, 15)
    assert p_min == pytest.approx(1e6)  # Willing to pay huge price
    assert p_max == pytest.approx(1e6)


def test_quadratic_money_aware_api():
    """Test that u_goods() routes correctly."""
    u = UQuadratic(A_star=10.0, B_star=10.0, sigma_A=5.0, sigma_B=5.0, gamma=0.0)
    
    # u_goods should give same result as u
    assert u.u_goods(5, 5) == u.u(5, 5)
    assert u.u_goods(10, 10) == u.u(10, 10)


def test_quadratic_with_cross_curvature():
    """Test quadratic utility with non-zero gamma."""
    u = UQuadratic(A_star=10.0, B_star=10.0, sigma_A=5.0, sigma_B=5.0, gamma=0.3)
    
    # Should still have zero utility at bliss
    assert u.u(10, 10) == pytest.approx(0.0)
    
    # Marginal utilities should differ from independent case
    mu_A_with_gamma = u.mu_A(5, 5)
    
    u_no_gamma = UQuadratic(A_star=10.0, B_star=10.0, sigma_A=5.0, sigma_B=5.0, gamma=0.0)
    mu_A_no_gamma = u_no_gamma.mu_A(5, 5)
    
    # They should differ due to cross-curvature term
    assert mu_A_with_gamma != mu_A_no_gamma

