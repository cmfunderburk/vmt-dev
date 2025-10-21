"""
Tests for Translog utility function.
"""

import pytest
import math
from vmt_engine.econ.utility import UTranslog


def test_translog_initialization():
    """Test translog utility initialization."""
    u = UTranslog(alpha_0=0.0, alpha_A=0.5, alpha_B=0.5, 
                  beta_AA=-0.1, beta_BB=-0.1, beta_AB=0.05)
    assert u.alpha_0 == 0.0
    assert u.alpha_A == 0.5
    assert u.alpha_B == 0.5
    assert u.beta_AA == -0.1
    assert u.beta_BB == -0.1
    assert u.beta_AB == 0.05


def test_translog_invalid_alpha():
    """Test that non-positive alpha coefficients are rejected."""
    with pytest.raises(ValueError, match="First-order coefficients must be positive"):
        UTranslog(alpha_0=0.0, alpha_A=0, alpha_B=0.5, 
                  beta_AA=0.0, beta_BB=0.0, beta_AB=0.0)
    
    with pytest.raises(ValueError, match="First-order coefficients must be positive"):
        UTranslog(alpha_0=0.0, alpha_A=0.5, alpha_B=-0.1, 
                  beta_AA=0.0, beta_BB=0.0, beta_AB=0.0)


def test_translog_monotonicity():
    """Test that utility increases with A and B."""
    u = UTranslog(alpha_0=0.0, alpha_A=0.5, alpha_B=0.5, 
                  beta_AA=-0.05, beta_BB=-0.05, beta_AB=0.0)
    
    # Utility should increase with A
    u1 = u.u(10, 10)
    u2 = u.u(20, 10)
    assert u2 > u1
    
    # Utility should increase with B
    u3 = u.u(10, 20)
    assert u3 > u1


def test_translog_overflow_protection():
    """Test overflow protection for large ln(U)."""
    # Create utility with parameters that will actually cause overflow
    # ln(U) = 100 + 50*ln(1000) + 50*ln(1000) = 100 + 50*6.9 + 50*6.9 = 790 > 700
    u = UTranslog(alpha_0=100.0, alpha_A=50.0, alpha_B=50.0, 
                  beta_AA=0.0, beta_BB=0.0, beta_AB=0.0)
    
    # Should warn and cap at exp(700)
    with pytest.warns(UserWarning, match="exceeds safe exp"):
        utility = u.u(1000, 1000)
        assert utility == pytest.approx(math.exp(700))


def test_translog_marginal_utilities_positive():
    """Test that marginal utilities are always positive."""
    u = UTranslog(alpha_0=0.0, alpha_A=0.5, alpha_B=0.5, 
                  beta_AA=-0.05, beta_BB=-0.05, beta_AB=0.02)
    
    # Test at various inventory levels
    for A, B in [(1, 1), (10, 10), (50, 50), (100, 100)]:
        mu_A = u.mu_A(A, B)
        mu_B = u.mu_B(A, B)
        assert mu_A > 0, f"MU_A should be positive at ({A}, {B})"
        assert mu_B > 0, f"MU_B should be positive at ({A}, {B})"


def test_translog_mrs_always_defined():
    """Test that MRS is always well-defined."""
    u = UTranslog(alpha_0=0.0, alpha_A=0.5, alpha_B=0.5, 
                  beta_AA=-0.05, beta_BB=-0.05, beta_AB=0.02)
    
    # Test at various inventory levels
    for A, B in [(1, 1), (10, 10), (50, 50), (100, 100)]:
        mrs = u.mrs_A_in_B(A, B)
        assert mrs is not None
        assert mrs > 0
        assert not math.isnan(mrs)
        assert not math.isinf(mrs)


def test_translog_zero_handling():
    """Test epsilon-shift for zero inventories."""
    u = UTranslog(alpha_0=0.0, alpha_A=0.5, alpha_B=0.5, 
                  beta_AA=0.0, beta_BB=0.0, beta_AB=0.0)
    
    # Should handle A=0 gracefully
    utility = u.u(0, 10)
    assert not math.isnan(utility)
    assert not math.isinf(utility)
    
    # Should handle B=0 gracefully
    utility = u.u(10, 0)
    assert not math.isnan(utility)
    assert not math.isinf(utility)
    
    # Should handle both=0 gracefully
    utility = u.u(0, 0)
    assert not math.isnan(utility)
    assert not math.isinf(utility)


def test_translog_cobb_douglas_nesting():
    """Test that translog reduces to Cobb-Douglas when beta terms are zero."""
    u_translog = UTranslog(alpha_0=0.0, alpha_A=0.6, alpha_B=0.4, 
                           beta_AA=0.0, beta_BB=0.0, beta_AB=0.0)
    
    # For Cobb-Douglas U = A^0.6 * B^0.4
    # ln(U) = 0.6*ln(A) + 0.4*ln(B)
    A, B = 10, 20
    expected_ln_u = 0.6 * math.log(A) + 0.4 * math.log(B)
    expected_u = math.exp(expected_ln_u)
    
    assert u_translog.u(A, B) == pytest.approx(expected_u)


def test_translog_mrs_log_space():
    """Test that MRS computation in log-space matches manual calculation."""
    u = UTranslog(alpha_0=0.0, alpha_A=0.5, alpha_B=0.5, 
                  beta_AA=-0.05, beta_BB=-0.05, beta_AB=0.02)
    
    A, B = 10, 20
    
    # Compute MRS using the formula
    ln_A = math.log(A)
    ln_B = math.log(B)
    
    d_ln_u_dA = (0.5 + (-0.05) * ln_A + 0.02 * ln_B) / A
    d_ln_u_dB = (0.5 + (-0.05) * ln_B + 0.02 * ln_A) / B
    
    expected_mrs = d_ln_u_dA / d_ln_u_dB
    
    assert u.mrs_A_in_B(A, B) == pytest.approx(expected_mrs)


def test_translog_reservation_bounds():
    """Test that reservation bounds equal MRS."""
    u = UTranslog(alpha_0=0.0, alpha_A=0.5, alpha_B=0.5, 
                  beta_AA=-0.05, beta_BB=-0.05, beta_AB=0.02)
    
    mrs = u.mrs_A_in_B(10, 20)
    p_min, p_max = u.reservation_bounds_A_in_B(10, 20)
    
    assert p_min == p_max
    assert p_min == pytest.approx(mrs)


def test_translog_money_aware_api():
    """Test money-aware API methods."""
    u = UTranslog(alpha_0=0.0, alpha_A=0.5, alpha_B=0.5, 
                  beta_AA=-0.05, beta_BB=-0.05, beta_AB=0.02)
    
    # u_goods should give same result as u
    assert u.u_goods(10, 20) == u.u(10, 20)
    
    # mu_A and mu_B should work
    mu_A = u.mu_A(10, 20)
    mu_B = u.mu_B(10, 20)
    assert mu_A > 0
    assert mu_B > 0


def test_translog_variable_elasticity():
    """Test that elasticity varies with consumption levels (unlike CES)."""
    u = UTranslog(alpha_0=0.0, alpha_A=0.5, alpha_B=0.5, 
                  beta_AA=-0.1, beta_BB=-0.1, beta_AB=0.05)
    
    # Test at asymmetric points to see variation
    # MRS should change with inventory levels due to second-order terms
    mrs_low = u.mrs_A_in_B(10, 20)
    mrs_high = u.mrs_A_in_B(100, 200)
    
    # With non-zero beta terms, MRS should differ as ln(A) changes
    # Even though ratio is constant, the beta terms create variation
    assert mrs_low != pytest.approx(mrs_high, rel=0.01)


def test_translog_complementarity():
    """Test complementarity with positive beta_AB."""
    u_complements = UTranslog(alpha_0=0.0, alpha_A=0.5, alpha_B=0.5, 
                               beta_AA=-0.05, beta_BB=-0.05, beta_AB=0.1)
    
    u_substitutes = UTranslog(alpha_0=0.0, alpha_A=0.5, alpha_B=0.5, 
                               beta_AA=-0.05, beta_BB=-0.05, beta_AB=-0.05)
    
    # Positive beta_AB suggests complementarity
    # MRS behavior should differ between the two at asymmetric points
    A, B = 10, 20
    mrs_comp = u_complements.mrs_A_in_B(A, B)
    mrs_sub = u_substitutes.mrs_A_in_B(A, B)
    
    assert mrs_comp != pytest.approx(mrs_sub)


def test_translog_helper_methods():
    """Test internal helper methods."""
    u = UTranslog(alpha_0=1.0, alpha_A=0.5, alpha_B=0.5, 
                  beta_AA=-0.05, beta_BB=-0.05, beta_AB=0.02)
    
    A, B = 10, 20
    
    # Test _ln_u
    ln_u = u._ln_u(A, B)
    assert not math.isnan(ln_u)
    assert not math.isinf(ln_u)
    
    # Test _d_ln_u_dA
    d_ln_u_dA = u._d_ln_u_dA(A, B)
    assert not math.isnan(d_ln_u_dA)
    assert not math.isinf(d_ln_u_dA)
    assert d_ln_u_dA > 0  # Should be positive for monotonicity
    
    # Test _d_ln_u_dB
    d_ln_u_dB = u._d_ln_u_dB(A, B)
    assert not math.isnan(d_ln_u_dB)
    assert not math.isinf(d_ln_u_dB)
    assert d_ln_u_dB > 0  # Should be positive for monotonicity

