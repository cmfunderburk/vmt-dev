"""
Tests for Stone-Geary utility function.
"""

import pytest
import math
from vmt_engine.econ.utility import UStoneGeary


def test_stone_geary_initialization():
    """Test Stone-Geary utility initialization."""
    u = UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=5.0, gamma_B=3.0)
    assert u.alpha_A == 0.6
    assert u.alpha_B == 0.4
    assert u.gamma_A == 5.0
    assert u.gamma_B == 3.0
    assert u.epsilon == 1e-12


def test_stone_geary_invalid_alpha():
    """Test that non-positive preference weights are rejected."""
    with pytest.raises(ValueError, match="Preference weights must be positive"):
        UStoneGeary(alpha_A=0, alpha_B=0.4, gamma_A=5.0, gamma_B=3.0)
    
    with pytest.raises(ValueError, match="Preference weights must be positive"):
        UStoneGeary(alpha_A=0.6, alpha_B=-0.1, gamma_A=5.0, gamma_B=3.0)


def test_stone_geary_invalid_gamma():
    """Test that negative subsistence levels are rejected."""
    with pytest.raises(ValueError, match="Subsistence levels must be non-negative"):
        UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=-1.0, gamma_B=3.0)
    
    with pytest.raises(ValueError, match="Subsistence levels must be non-negative"):
        UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=5.0, gamma_B=-1.0)


def test_stone_geary_utility_above_subsistence():
    """Test Stone-Geary utility with inventories above subsistence."""
    u = UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=5.0, gamma_B=3.0)
    
    # Above subsistence: should be well-behaved
    utility = u.u(10, 10)
    assert not math.isnan(utility)
    assert not math.isinf(utility)
    
    # More inventory = higher utility
    u1 = u.u(10, 10)
    u2 = u.u(20, 10)
    assert u2 > u1


def test_stone_geary_utility_at_subsistence():
    """Test Stone-Geary utility at subsistence boundary."""
    u = UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=5.0, gamma_B=3.0)
    
    # At subsistence: epsilon-shift gives finite (very negative) utility
    utility = u.u(5, 3)
    assert not math.isnan(utility)
    assert not math.isinf(utility)
    assert utility < -20  # Should be very negative


def test_stone_geary_utility_below_subsistence():
    """Test Stone-Geary utility below subsistence."""
    u = UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=5.0, gamma_B=3.0)
    
    # Below subsistence: epsilon-shift prevents -inf
    utility = u.u(3, 1)
    assert not math.isnan(utility)
    assert not math.isinf(utility)
    assert utility < -20  # Should be very negative


def test_stone_geary_cobb_douglas_nesting():
    """Test that Stone-Geary reduces to Cobb-Douglas when gamma=0."""
    u_sg = UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=0.0, gamma_B=0.0)
    
    # For Cobb-Douglas: ln(U) = 0.6*ln(A) + 0.4*ln(B)
    A, B = 10, 20
    expected = 0.6 * math.log(A) + 0.4 * math.log(B)
    
    assert u_sg.u(A, B) == pytest.approx(expected)


def test_stone_geary_mu_infinity_near_subsistence():
    """Test that marginal utility approaches infinity near subsistence."""
    u = UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=5.0, gamma_B=3.0)
    
    # Very close to subsistence: MU should be very large
    mu_A_close = u.mu_A(6, 10)  # A - gamma_A = 1
    mu_A_far = u.mu_A(50, 10)   # A - gamma_A = 45
    
    assert mu_A_close > mu_A_far
    assert mu_A_close > 0.5  # Should be quite large


def test_stone_geary_mu_zero_as_inventory_grows():
    """Test that marginal utility approaches zero as inventory grows."""
    u = UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=5.0, gamma_B=3.0)
    
    # Far from subsistence: MU should be small
    mu_A_far = u.mu_A(1000, 100)
    assert mu_A_far < 0.001  # Should be very small


def test_stone_geary_mrs_high_near_subsistence():
    """Test that MRS is very high when close to subsistence in A."""
    u = UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=5.0, gamma_B=3.0)
    
    # Close to subsistence in A, far above in B
    mrs_desperate = u.mrs_A_in_B(6, 50)
    
    # Far above subsistence in both
    mrs_normal = u.mrs_A_in_B(50, 50)
    
    # Desperate MRS should be much higher
    assert mrs_desperate > mrs_normal * 10


def test_stone_geary_mrs_stable_far_above():
    """Test that MRS stabilizes far above subsistence (Cobb-Douglas-like)."""
    u = UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=5.0, gamma_B=3.0)
    
    # Far above subsistence, should behave like Cobb-Douglas
    # For large A, B: MRS ≈ (alpha_A / alpha_B) * (B / A)
    A, B = 100, 100
    mrs = u.mrs_A_in_B(A, B)
    
    # Approximate Cobb-Douglas MRS
    approx_mrs = (0.6 / 0.4) * ((B - 3.0) / (A - 5.0))
    
    assert mrs == pytest.approx(approx_mrs, rel=1e-6)


def test_stone_geary_reservation_bounds_normal():
    """Test reservation bounds when above subsistence."""
    u = UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=5.0, gamma_B=3.0)
    
    # Normal case: both above subsistence
    mrs = u.mrs_A_in_B(10, 10)
    p_min, p_max = u.reservation_bounds_A_in_B(10, 10)
    
    assert p_min == p_max
    assert p_min == pytest.approx(mrs)


def test_stone_geary_reservation_bounds_desperate_buyer():
    """Test reservation bounds when below subsistence in A."""
    u = UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=5.0, gamma_B=3.0)
    
    # Below subsistence in A only: desperate buyer
    p_min, p_max = u.reservation_bounds_A_in_B(5, 10)
    assert p_min == pytest.approx(1e6)
    assert p_max == pytest.approx(1e6)


def test_stone_geary_reservation_bounds_cannot_sell():
    """Test reservation bounds when below subsistence in B."""
    u = UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=5.0, gamma_B=3.0)
    
    # Below subsistence in B only: cannot spare B
    p_min, p_max = u.reservation_bounds_A_in_B(10, 3)
    assert p_min == pytest.approx(1e6)
    assert p_max == pytest.approx(1e6)


def test_stone_geary_reservation_bounds_both_below():
    """Test reservation bounds when below subsistence in both goods."""
    u = UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=5.0, gamma_B=3.0)
    
    # Below subsistence in both: neutral default
    p_min, p_max = u.reservation_bounds_A_in_B(4, 2)
    assert p_min == pytest.approx(1.0)
    assert p_max == pytest.approx(1.0)


def test_stone_geary_is_above_subsistence():
    """Test is_above_subsistence helper method."""
    u = UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=5.0, gamma_B=3.0)
    
    # Above subsistence
    assert u.is_above_subsistence(10, 10) is True
    
    # At subsistence
    assert u.is_above_subsistence(5, 3) is False
    
    # Below subsistence
    assert u.is_above_subsistence(3, 2) is False
    
    # Mixed
    assert u.is_above_subsistence(10, 3) is False
    assert u.is_above_subsistence(5, 10) is False


def test_stone_geary_boundary_exactly_at_subsistence():
    """Test behavior exactly at subsistence boundary."""
    u = UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=5.0, gamma_B=3.0)
    
    # Exactly at subsistence should use epsilon-shift
    utility = u.u(5, 3)
    mu_A = u.mu_A(5, 3)
    mu_B = u.mu_B(5, 3)
    
    assert not math.isnan(utility)
    assert not math.isinf(utility)
    assert not math.isnan(mu_A)
    assert not math.isinf(mu_A)
    assert mu_A > 0  # Should be very large but finite


def test_stone_geary_money_aware_api():
    """Test money-aware API methods."""
    u = UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=5.0, gamma_B=3.0)
    
    # u_goods should give same result as u
    assert u.u_goods(10, 10) == u.u(10, 10)
    
    # mu_A and mu_B should work
    mu_A = u.mu_A(10, 10)
    mu_B = u.mu_B(10, 10)
    assert mu_A > 0
    assert mu_B > 0

