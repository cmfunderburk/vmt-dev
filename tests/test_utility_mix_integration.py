"""
Integration tests for mixed utility populations.
"""

import pytest
import math
from vmt_engine.econ.utility import UCES, ULinear, UQuadratic, UTranslog, UStoneGeary
from scenarios.schema import ScenarioConfig, UtilityConfig, UtilitiesMix, ScenarioParams, ResourceSeed


def test_all_utilities_implement_interface():
    """Test that all utility classes implement the full Utility interface."""
    utilities = [
        UCES(rho=-0.5, wA=1.0, wB=1.0),
        ULinear(vA=2.0, vB=3.0),
        UQuadratic(A_star=10.0, B_star=10.0, sigma_A=5.0, sigma_B=5.0, gamma=0.0),
        UTranslog(alpha_0=0.0, alpha_A=0.5, alpha_B=0.5, beta_AA=0.0, beta_BB=0.0, beta_AB=0.0),
        UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=5.0, gamma_B=3.0)
    ]
    
    # Test inventory
    A, B = 20, 20
    
    for u in utilities:
        # All should implement u()
        utility = u.u(A, B)
        assert not math.isnan(utility)
        assert not math.isinf(utility)
        
        # All should implement u_goods()
        u_goods = u.u_goods(A, B)
        assert u_goods == utility
        
        # All should implement mu_A() and mu_B()
        mu_A = u.mu_A(A, B)
        mu_B = u.mu_B(A, B)
        assert not math.isnan(mu_A)
        assert not math.isnan(mu_B)
        
        # All should implement mrs_A_in_B() (may return None for some)
        mrs = u.mrs_A_in_B(A, B)
        if mrs is not None:
            assert not math.isnan(mrs)
        
        # All should implement reservation_bounds_A_in_B()
        p_min, p_max = u.reservation_bounds_A_in_B(A, B)
        assert not math.isnan(p_min)
        assert not math.isnan(p_max)


def test_mixed_population_quote_generation():
    """Test that agents with different utility types can generate quotes."""
    utilities = {
        'ces': UCES(rho=-0.5, wA=1.0, wB=1.0),
        'linear': ULinear(vA=2.0, vB=3.0),
        'quadratic': UQuadratic(A_star=15.0, B_star=15.0, sigma_A=5.0, sigma_B=5.0),
        'translog': UTranslog(alpha_0=0.0, alpha_A=0.5, alpha_B=0.5, 
                               beta_AA=-0.05, beta_BB=-0.05, beta_AB=0.02),
        'stone_geary': UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=5.0, gamma_B=3.0)
    }
    
    # All should be able to compute MRS at this inventory
    A, B = 20, 20
    
    for name, u in utilities.items():
        mrs = u.mrs_A_in_B(A, B)
        assert mrs is not None, f"{name} should have defined MRS at ({A}, {B})"
        assert mrs > 0, f"{name} MRS should be positive"


def test_quadratic_satiation_no_trade():
    """Test that quadratic agents at/beyond bliss refuse trades."""
    u = UQuadratic(A_star=10.0, B_star=10.0, sigma_A=5.0, sigma_B=5.0)
    
    # Beyond bliss in both dimensions: both MU negative
    p_min, p_max = u.reservation_bounds_A_in_B(15, 15)
    
    # Should indicate no feasible trade
    assert p_min > p_max


def test_stone_geary_desperate_trading():
    """Test that Stone-Geary agents near subsistence have high MRS."""
    u = UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=5.0, gamma_B=3.0)
    
    # Just above subsistence in A
    mrs_desperate = u.mrs_A_in_B(6, 20)
    
    # Far above subsistence
    mrs_normal = u.mrs_A_in_B(50, 20)
    
    # Desperate agent should have much higher MRS
    assert mrs_desperate > mrs_normal * 5


def test_translog_numerical_stability():
    """Test that translog handles edge cases numerically."""
    u = UTranslog(alpha_0=0.0, alpha_A=0.5, alpha_B=0.5, 
                  beta_AA=-0.1, beta_BB=-0.1, beta_AB=0.05)
    
    # Test with zero inventory
    utility = u.u(0, 10)
    assert not math.isnan(utility)
    assert not math.isinf(utility)
    
    # Test with very large inventory
    utility = u.u(1000, 1000)
    assert not math.isnan(utility)
    assert not math.isinf(utility)


def test_scenario_validation_stone_geary_subsistence():
    """Test that scenario loader validates Stone-Geary subsistence constraints."""
    # Valid configuration: initial inventories > subsistence
    valid_config = ScenarioConfig(
        schema_version=1,
        name="Test Stone-Geary Valid",
        N=10,
        agents=5,
        initial_inventories={'A': 10, 'B': 8},
        utilities=UtilitiesMix(mix=[
            UtilityConfig(
                type="stone_geary",
                weight=1.0,
                params={
                    'alpha_A': 0.6,
                    'alpha_B': 0.4,
                    'gamma_A': 5.0,
                    'gamma_B': 3.0
                }
            )
        ]),
        params=ScenarioParams(),
        resource_seed=ResourceSeed(density=0.3, amount=5)
    )
    
    # Should not raise
    valid_config.validate()


def test_scenario_validation_stone_geary_fails_fixed_inventory():
    """Test that Stone-Geary validation rejects invalid fixed inventories."""
    invalid_config = ScenarioConfig(
        schema_version=1,
        name="Test Stone-Geary Invalid",
        N=10,
        agents=5,
        initial_inventories={'A': 3, 'B': 8},  # A <= gamma_A
        utilities=UtilitiesMix(mix=[
            UtilityConfig(
                type="stone_geary",
                weight=1.0,
                params={
                    'alpha_A': 0.6,
                    'alpha_B': 0.4,
                    'gamma_A': 5.0,
                    'gamma_B': 3.0
                }
            )
        ]),
        params=ScenarioParams(),
        resource_seed=ResourceSeed(density=0.3, amount=5)
    )
    
    with pytest.raises(ValueError, match="Stone-Geary requires initial_inventories\\['A'\\]=3 > gamma_A=5.0"):
        invalid_config.validate()


def test_scenario_validation_stone_geary_fails_uniform_inventory():
    """Test that Stone-Geary validation rejects invalid uniform_int inventories."""
    invalid_config = ScenarioConfig(
        schema_version=1,
        name="Test Stone-Geary Invalid Uniform",
        N=10,
        agents=5,
        initial_inventories={'A': {'uniform_int': [3, 15]}, 'B': {'uniform_int': [5, 20]}},  # min(A)=3 <= gamma_A=5
        utilities=UtilitiesMix(mix=[
            UtilityConfig(
                type="stone_geary",
                weight=1.0,
                params={
                    'alpha_A': 0.6,
                    'alpha_B': 0.4,
                    'gamma_A': 5.0,
                    'gamma_B': 3.0
                }
            )
        ]),
        params=ScenarioParams(),
        resource_seed=ResourceSeed(density=0.3, amount=5)
    )
    
    with pytest.raises(ValueError, match="Stone-Geary requires min\\(initial_inventories\\['A'\\]\\)=3 > gamma_A=5.0"):
        invalid_config.validate()


def test_mixed_utility_population_validation():
    """Test scenario with multiple utility types validates correctly."""
    mixed_config = ScenarioConfig(
        schema_version=1,
        name="Mixed Utilities",
        N=20,
        agents=12,
        initial_inventories={'A': {'uniform_int': [10, 50]}, 'B': {'uniform_int': [10, 50]}},
        utilities=UtilitiesMix(mix=[
            UtilityConfig(type="quadratic", weight=0.25, 
                         params={'A_star': 30.0, 'B_star': 30.0, 'sigma_A': 10.0, 'sigma_B': 10.0}),
            UtilityConfig(type="translog", weight=0.25,
                         params={'alpha_0': 0.0, 'alpha_A': 0.5, 'alpha_B': 0.5, 
                                'beta_AA': -0.05, 'beta_BB': -0.05, 'beta_AB': 0.02}),
            UtilityConfig(type="stone_geary", weight=0.25,
                         params={'alpha_A': 0.6, 'alpha_B': 0.4, 'gamma_A': 5.0, 'gamma_B': 5.0}),
            UtilityConfig(type="ces", weight=0.25,
                         params={'rho': -0.5, 'wA': 1.0, 'wB': 1.0})
        ]),
        params=ScenarioParams(),
        resource_seed=ResourceSeed(density=0.4, amount=5)
    )
    
    # Should validate successfully
    mixed_config.validate()


def test_quadratic_utility_decreases_beyond_bliss():
    """Test that quadratic utility decreases beyond bliss point."""
    u = UQuadratic(A_star=10.0, B_star=10.0, sigma_A=5.0, sigma_B=5.0)
    
    # At bliss
    u_bliss = u.u(10, 10)
    
    # Slightly above bliss
    u_above = u.u(11, 10)
    
    # Should be lower than at bliss
    assert u_above < u_bliss


def test_translog_vs_cobb_douglas():
    """Test that translog with beta=0 matches Cobb-Douglas behavior."""
    u_translog = UTranslog(alpha_0=0.0, alpha_A=0.6, alpha_B=0.4,
                           beta_AA=0.0, beta_BB=0.0, beta_AB=0.0)
    
    u_stone_geary = UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=0.0, gamma_B=0.0)
    
    # Both represent Cobb-Douglas but in different forms
    # Translog: U = exp(ln U), Stone-Geary: returns ln U directly
    # Compare ln(U) values instead
    A, B = 20, 30
    
    ln_u_translog = u_translog._ln_u(A, B)
    ln_u_stone_geary = u_stone_geary.u(A, B)  # Stone-Geary returns ln form
    
    assert ln_u_translog == pytest.approx(ln_u_stone_geary)
    
    # MRS should match exactly (same Cobb-Douglas formula)
    assert u_translog.mrs_A_in_B(A, B) == pytest.approx(u_stone_geary.mrs_A_in_B(A, B))

