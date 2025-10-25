"""
Tests for logarithmic money utility functionality.

Tests cover:
- mu_money() function with linear and log forms
- u_total() with both money utility forms
- Quote system integration with log money
- Trade execution with log money
- Agent initialization with M_0
- Schema validation
"""

import pytest
import math
from src.vmt_engine.econ.utility import mu_money, u_total, UCES, ULinear
from src.vmt_engine.core.state import Inventory
from src.vmt_engine.core.agent import Agent
from src.vmt_engine.systems.quotes import compute_quotes
from src.scenarios.schema import ScenarioParams


class TestMuMoney:
    """Test mu_money() function for marginal utility of money."""
    
    def test_mu_money_linear_constant(self):
        """Linear form returns constant λ regardless of M."""
        lambda_money = 2.0
        
        mu_0 = mu_money(0, lambda_money, money_utility_form="linear")
        mu_100 = mu_money(100, lambda_money, money_utility_form="linear")
        mu_1000 = mu_money(1000, lambda_money, money_utility_form="linear")
        
        assert mu_0 == lambda_money
        assert mu_100 == lambda_money
        assert mu_1000 == lambda_money
    
    def test_mu_money_log_diminishing(self):
        """Log form shows diminishing marginal utility as M increases."""
        lambda_money = 1.0
        M_0 = 10.0
        
        mu_10 = mu_money(10, lambda_money, money_utility_form="log", M_0=M_0)
        mu_50 = mu_money(50, lambda_money, money_utility_form="log", M_0=M_0)
        mu_100 = mu_money(100, lambda_money, money_utility_form="log", M_0=M_0)
        
        # Should be diminishing: mu_10 > mu_50 > mu_100
        assert mu_10 > mu_50 > mu_100
        
        # Verify exact values: mu = λ/(M + M_0)
        assert abs(mu_10 - lambda_money / (10 + M_0)) < 1e-9
        assert abs(mu_50 - lambda_money / (50 + M_0)) < 1e-9
        assert abs(mu_100 - lambda_money / (100 + M_0)) < 1e-9
    
    def test_mu_money_log_zero_M_with_M_0(self):
        """Log form handles M=0 correctly when M_0 > 0."""
        lambda_money = 1.0
        M_0 = 10.0
        
        mu = mu_money(0, lambda_money, money_utility_form="log", M_0=M_0)
        
        # Should be λ/M_0
        assert abs(mu - lambda_money / M_0) < 1e-9
    
    def test_mu_money_log_zero_M_zero_M_0_epsilon_guard(self):
        """Log form uses epsilon guard when both M=0 and M_0=0."""
        lambda_money = 1.0
        epsilon = 1e-12
        
        mu = mu_money(0, lambda_money, money_utility_form="log", M_0=0.0, epsilon=epsilon)
        
        # Should be λ/epsilon (very large but not infinite)
        assert abs(mu - lambda_money / epsilon) < 1e-6
        assert mu > 0
        assert math.isfinite(mu)
    
    def test_mu_money_invalid_form_raises(self):
        """Invalid money_utility_form raises ValueError."""
        with pytest.raises(ValueError, match="Unknown money_utility_form"):
            mu_money(100, 1.0, money_utility_form="invalid")


class TestUTotal:
    """Test u_total() with different money utility forms."""
    
    def test_u_total_linear_matches_legacy(self):
        """Linear money utility matches legacy behavior (λ·M)."""
        utility = UCES(rho=0.5, wA=0.6, wB=0.4)
        params = {
            'utility': utility,
            'lambda_money': 1.0,
            'money_utility_form': 'linear'
        }
        
        inv = Inventory(A=10, B=15, M=100)
        
        u_goods = utility.u_goods(10, 15)
        u_expected = u_goods + 1.0 * 100  # λ·M
        
        u_actual = u_total(inv, params)
        
        assert abs(u_actual - u_expected) < 1e-9
    
    def test_u_total_log_basic(self):
        """Log money utility computed correctly."""
        utility = ULinear(vA=2.0, vB=3.0)
        lambda_money = 1.0
        M_0 = 10.0
        
        params = {
            'utility': utility,
            'lambda_money': lambda_money,
            'money_utility_form': 'log',
            'M_0': M_0
        }
        
        inv = Inventory(A=5, B=10, M=50)
        
        u_goods = utility.u_goods(5, 10)  # 2*5 + 3*10 = 40
        u_money = lambda_money * math.log(50 + M_0)  # log(60)
        u_expected = u_goods + u_money
        
        u_actual = u_total(inv, params)
        
        assert abs(u_actual - u_expected) < 1e-9
    
    def test_u_total_log_with_different_M_0(self):
        """Different M_0 values produce different utilities."""
        utility = ULinear(vA=1.0, vB=1.0)
        lambda_money = 1.0
        
        inv = Inventory(A=5, B=5, M=50)
        
        # M_0 = 0
        params_0 = {
            'utility': utility,
            'lambda_money': lambda_money,
            'money_utility_form': 'log',
            'M_0': 0.0
        }
        u_0 = u_total(inv, params_0)
        
        # M_0 = 10
        params_10 = {
            'utility': utility,
            'lambda_money': lambda_money,
            'money_utility_form': 'log',
            'M_0': 10.0
        }
        u_10 = u_total(inv, params_10)
        
        # M_0 = 50
        params_50 = {
            'utility': utility,
            'lambda_money': lambda_money,
            'money_utility_form': 'log',
            'M_0': 50.0
        }
        u_50 = u_total(inv, params_50)
        
        # All should be different (goods utility is same, money utility differs)
        assert u_0 != u_10 != u_50
        # Higher M_0 → higher log argument (M + M_0) → higher log value → higher total utility (for fixed M)
        assert u_0 < u_10 < u_50
    
    def test_u_total_log_zero_money_with_M_0(self):
        """Log utility handles M=0 correctly when M_0 > 0."""
        utility = ULinear(vA=1.0, vB=1.0)
        lambda_money = 1.0
        M_0 = 10.0
        
        params = {
            'utility': utility,
            'lambda_money': lambda_money,
            'money_utility_form': 'log',
            'M_0': M_0
        }
        
        inv = Inventory(A=5, B=5, M=0)
        
        u_goods = 5 + 5  # 10
        u_money = lambda_money * math.log(M_0)  # log(10)
        u_expected = u_goods + u_money
        
        u_actual = u_total(inv, params)
        
        assert abs(u_actual - u_expected) < 1e-9
    
    def test_u_total_log_zero_money_zero_M_0_epsilon_guard(self):
        """Log utility uses epsilon guard when M=0 and M_0=0."""
        utility = ULinear(vA=1.0, vB=1.0)
        lambda_money = 1.0
        epsilon = 1e-12
        
        params = {
            'utility': utility,
            'lambda_money': lambda_money,
            'money_utility_form': 'log',
            'M_0': 0.0,
            'epsilon': epsilon
        }
        
        inv = Inventory(A=5, B=5, M=0)
        
        u_actual = u_total(inv, params)
        
        # Should use log(epsilon), which is very negative
        u_goods = 10
        u_money = lambda_money * math.log(epsilon)  # ~ -27.6
        u_expected = u_goods + u_money
        
        assert abs(u_actual - u_expected) < 1e-6
        assert math.isfinite(u_actual)
    
    def test_u_total_income_effect(self):
        """Agents with more money have higher total utility (income effect)."""
        utility = UCES(rho=0.5, wA=0.6, wB=0.4)
        lambda_money = 1.0
        M_0 = 10.0
        
        params = {
            'utility': utility,
            'lambda_money': lambda_money,
            'money_utility_form': 'log',
            'M_0': M_0
        }
        
        # Same goods, different money
        inv_poor = Inventory(A=10, B=10, M=10)
        inv_middle = Inventory(A=10, B=10, M=50)
        inv_rich = Inventory(A=10, B=10, M=200)
        
        u_poor = u_total(inv_poor, params)
        u_middle = u_total(inv_middle, params)
        u_rich = u_total(inv_rich, params)
        
        # Rich should have higher utility
        assert u_poor < u_middle < u_rich
    
    def test_u_total_invalid_form_raises(self):
        """Invalid money_utility_form raises ValueError."""
        utility = ULinear(vA=1.0, vB=1.0)
        params = {
            'utility': utility,
            'lambda_money': 1.0,
            'money_utility_form': 'invalid'
        }
        
        inv = Inventory(A=5, B=5, M=100)
        
        with pytest.raises(ValueError, match="Unknown money_utility_form"):
            u_total(inv, params)
    
    def test_u_total_missing_utility_raises(self):
        """Missing 'utility' key raises KeyError."""
        params = {'lambda_money': 1.0}
        inv = Inventory(A=5, B=5, M=100)
        
        with pytest.raises(KeyError, match="params must contain 'utility' key"):
            u_total(inv, params)


class TestQuotesWithLogMoney:
    """Test monetary quote generation with log money utility."""
    
    def test_quotes_log_money_reflect_wealth(self):
        """Monetary quotes reflect agent wealth (income effects) with log money."""
        utility = UCES(rho=0.5, wA=0.6, wB=0.4)
        
        # Poor agent (M=10)
        agent_poor = Agent(
            id=0,
            pos=(0, 0),
            inventory=Inventory(A=10, B=10, M=10),
            utility=utility,
            lambda_money=1.0,
            money_utility_form="log",
            M_0=5.0
        )
        
        # Rich agent (M=200)
        agent_rich = Agent(
            id=1,
            pos=(1, 1),
            inventory=Inventory(A=10, B=10, M=200),
            utility=utility,
            lambda_money=1.0,
            money_utility_form="log",
            M_0=5.0
        )
        
        quotes_poor = compute_quotes(agent_poor, spread=0.0, epsilon=1e-12)
        quotes_rich = compute_quotes(agent_rich, spread=0.0, epsilon=1e-12)
        
        # Rich agent values goods more in money terms (higher MU_good / lower MU_money)
        # So rich agent willing to pay more money for goods
        assert quotes_rich['bid_A_in_M'] > quotes_poor['bid_A_in_M']
        assert quotes_rich['bid_B_in_M'] > quotes_poor['bid_B_in_M']
        
        # Rich agent asks for more money when selling goods
        assert quotes_rich['ask_A_in_M'] > quotes_poor['ask_A_in_M']
        assert quotes_rich['ask_B_in_M'] > quotes_poor['ask_B_in_M']
    
    def test_quotes_linear_no_wealth_effect(self):
        """Linear money utility shows no wealth effects on quotes."""
        utility = UCES(rho=0.5, wA=0.6, wB=0.4)
        
        # Poor agent (M=10)
        agent_poor = Agent(
            id=0,
            pos=(0, 0),
            inventory=Inventory(A=10, B=10, M=10),
            utility=utility,
            lambda_money=1.0,
            money_utility_form="linear",
            M_0=0.0
        )
        
        # Rich agent (M=200)
        agent_rich = Agent(
            id=1,
            pos=(1, 1),
            inventory=Inventory(A=10, B=10, M=200),
            utility=utility,
            lambda_money=1.0,
            money_utility_form="linear",
            M_0=0.0
        )
        
        quotes_poor = compute_quotes(agent_poor, spread=0.0, epsilon=1e-12)
        quotes_rich = compute_quotes(agent_rich, spread=0.0, epsilon=1e-12)
        
        # With linear money, same goods inventory → same quotes (no wealth effect)
        assert abs(quotes_poor['bid_A_in_M'] - quotes_rich['bid_A_in_M']) < 1e-9
        assert abs(quotes_poor['bid_B_in_M'] - quotes_rich['bid_B_in_M']) < 1e-9
        assert abs(quotes_poor['ask_A_in_M'] - quotes_rich['ask_A_in_M']) < 1e-9
        assert abs(quotes_poor['ask_B_in_M'] - quotes_rich['ask_B_in_M']) < 1e-9


class TestSchemaValidation:
    """Test schema validation for new parameters."""
    
    def test_schema_validates_M_0_nonnegative(self):
        """Schema validation requires M_0 >= 0."""
        params = ScenarioParams(M_0=-1.0)
        
        with pytest.raises(ValueError, match="M_0 must be non-negative"):
            params.validate()
    
    def test_schema_accepts_M_0_zero(self):
        """M_0 = 0 is valid (backward compatibility)."""
        params = ScenarioParams(M_0=0.0)
        params.validate()  # Should not raise
    
    def test_schema_accepts_M_0_positive(self):
        """M_0 > 0 is valid."""
        params = ScenarioParams(M_0=10.0)
        params.validate()  # Should not raise
    
    def test_schema_validates_money_utility_form(self):
        """Schema validation requires valid money_utility_form."""
        params = ScenarioParams(money_utility_form="invalid")
        
        with pytest.raises(ValueError, match="money_utility_form must be 'linear' or 'log'"):
            params.validate()
    
    def test_schema_accepts_linear_form(self):
        """money_utility_form='linear' is valid."""
        params = ScenarioParams(money_utility_form="linear")
        params.validate()  # Should not raise
    
    def test_schema_accepts_log_form(self):
        """money_utility_form='log' is valid."""
        params = ScenarioParams(money_utility_form="log")
        params.validate()  # Should not raise
    
    def test_schema_defaults(self):
        """Schema has correct defaults for new parameters."""
        params = ScenarioParams()
        
        assert params.money_utility_form == "linear"
        assert params.M_0 == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

