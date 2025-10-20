"""
Tests for money-aware quote system (Phase 2a).

Verifies:
- compute_quotes() returns dict with all 8+ keys
- filter_quotes_by_regime() visibility control
- Arithmetic correctness of monetary quotes
- Backward compatibility with barter_only mode
"""

import pytest
from src.vmt_engine.core.agent import Agent
from src.vmt_engine.core.state import Inventory, Position
from src.vmt_engine.econ.utility import UCES, ULinear
from src.vmt_engine.systems.quotes import compute_quotes, filter_quotes_by_regime, refresh_quotes_if_needed


class TestComputeQuotesStructure:
    """Test that compute_quotes() returns the correct dictionary structure."""
    
    def test_returns_dict(self):
        """compute_quotes() should return a dictionary."""
        agent = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=10, B=10, M=0),
            utility=UCES(rho=0.5, wA=0.6, wB=0.4)
        )
        
        quotes = compute_quotes(agent, spread=0.1, epsilon=1e-9)
        assert isinstance(quotes, dict)
    
    def test_contains_barter_keys(self):
        """Quotes dict should contain all barter pair keys."""
        agent = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=10, B=10, M=0),
            utility=UCES(rho=0.5, wA=0.6, wB=0.4)
        )
        
        quotes = compute_quotes(agent, spread=0.1, epsilon=1e-9)
        
        # A<->B pair
        assert 'ask_A_in_B' in quotes
        assert 'bid_A_in_B' in quotes
        assert 'p_min_A_in_B' in quotes
        assert 'p_max_A_in_B' in quotes
        
        # B<->A pair (reciprocal)
        assert 'ask_B_in_A' in quotes
        assert 'bid_B_in_A' in quotes
        assert 'p_min_B_in_A' in quotes
        assert 'p_max_B_in_A' in quotes
    
    def test_contains_monetary_keys(self):
        """Quotes dict should contain all monetary pair keys."""
        agent = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=10, B=10, M=0),
            utility=UCES(rho=0.5, wA=0.6, wB=0.4)
        )
        
        quotes = compute_quotes(agent, spread=0.1, epsilon=1e-9)
        
        # A<->M pair
        assert 'ask_A_in_M' in quotes
        assert 'bid_A_in_M' in quotes
        
        # B<->M pair
        assert 'ask_B_in_M' in quotes
        assert 'bid_B_in_M' in quotes
    
    def test_all_values_nonnegative(self):
        """All quote values should be non-negative."""
        agent = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=10, B=10, M=0),
            utility=UCES(rho=0.5, wA=0.6, wB=0.4)
        )
        
        quotes = compute_quotes(agent, spread=0.1, epsilon=1e-9)
        
        for key, value in quotes.items():
            assert value >= 0, f"Quote {key} is negative: {value}"


class TestBarterQuotesArithmetic:
    """Test arithmetic correctness of barter quotes."""
    
    def test_ask_greater_than_p_min(self):
        """Ask price should be greater than reservation minimum."""
        agent = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=10, B=10, M=0),
            utility=UCES(rho=0.5, wA=0.6, wB=0.4)
        )
        
        quotes = compute_quotes(agent, spread=0.1, epsilon=1e-9)
        
        assert quotes['ask_A_in_B'] >= quotes['p_min_A_in_B']
        assert quotes['ask_B_in_A'] >= quotes['p_min_B_in_A']
    
    def test_bid_less_than_p_max(self):
        """Bid price should be less than reservation maximum."""
        agent = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=10, B=10, M=0),
            utility=UCES(rho=0.5, wA=0.6, wB=0.4)
        )
        
        quotes = compute_quotes(agent, spread=0.1, epsilon=1e-9)
        
        assert quotes['bid_A_in_B'] <= quotes['p_max_A_in_B']
        assert quotes['bid_B_in_A'] <= quotes['p_max_B_in_A']
    
    def test_spread_applied_correctly(self):
        """Spread should be applied correctly to asks and bids."""
        agent = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=10, B=10, M=0),
            utility=UCES(rho=0.5, wA=0.6, wB=0.4)
        )
        
        spread = 0.1
        quotes = compute_quotes(agent, spread=spread, epsilon=1e-9)
        
        # Ask = p_min * (1 + spread)
        expected_ask = quotes['p_min_A_in_B'] * (1 + spread)
        assert abs(quotes['ask_A_in_B'] - expected_ask) < 1e-6
        
        # Bid = p_max * (1 - spread)
        expected_bid = quotes['p_max_A_in_B'] * (1 - spread)
        assert abs(quotes['bid_A_in_B'] - expected_bid) < 1e-6
    
    def test_reciprocal_relationship(self):
        """B-in-A quotes should be reciprocal of A-in-B."""
        agent = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=10, B=10, M=0),
            utility=UCES(rho=0.5, wA=0.6, wB=0.4)
        )
        
        quotes = compute_quotes(agent, spread=0.1, epsilon=1e-9)
        
        # p_min_B_in_A ≈ 1 / p_max_A_in_B
        expected_p_min_B = 1.0 / quotes['p_max_A_in_B']
        assert abs(quotes['p_min_B_in_A'] - expected_p_min_B) < 1e-6
        
        # p_max_B_in_A ≈ 1 / p_min_A_in_B
        expected_p_max_B = 1.0 / quotes['p_min_A_in_B']
        assert abs(quotes['p_max_B_in_A'] - expected_p_max_B) < 1e-6


class TestMonetaryQuotesArithmetic:
    """Test arithmetic correctness of monetary quotes."""
    
    def test_monetary_quotes_use_marginal_utilities(self):
        """Monetary quotes should be based on MU / lambda_money."""
        agent = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=10, B=10, M=0),
            utility=UCES(rho=0.5, wA=0.6, wB=0.4),
            lambda_money=2.0
        )
        
        spread = 0.1
        money_scale = 100
        quotes = compute_quotes(agent, spread=spread, epsilon=1e-9, money_scale=money_scale)
        
        # Get marginal utilities
        mu_A = agent.utility.mu_A(10, 10)
        mu_B = agent.utility.mu_B(10, 10)
        
        # Expected prices
        expected_price_A = (mu_A / agent.lambda_money) * money_scale
        expected_price_B = (mu_B / agent.lambda_money) * money_scale
        
        # Check ask/bid are around expected price
        assert abs(quotes['ask_A_in_M'] - expected_price_A * (1 + spread)) < 1e-3
        assert abs(quotes['bid_A_in_M'] - expected_price_A * (1 - spread)) < 1e-3
        assert abs(quotes['ask_B_in_M'] - expected_price_B * (1 + spread)) < 1e-3
        assert abs(quotes['bid_B_in_M'] - expected_price_B * (1 - spread)) < 1e-3
    
    def test_money_scale_affects_monetary_quotes(self):
        """money_scale should proportionally affect monetary quotes."""
        agent = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=10, B=10, M=0),
            utility=UCES(rho=0.5, wA=0.6, wB=0.4)
        )
        
        quotes1 = compute_quotes(agent, spread=0.1, epsilon=1e-9, money_scale=1)
        quotes100 = compute_quotes(agent, spread=0.1, epsilon=1e-9, money_scale=100)
        
        # Quotes with money_scale=100 should be 100× larger
        assert abs(quotes100['ask_A_in_M'] / quotes1['ask_A_in_M'] - 100) < 1e-3
        assert abs(quotes100['bid_A_in_M'] / quotes1['bid_A_in_M'] - 100) < 1e-3


class TestFilterQuotesByRegime:
    """Test filter_quotes_by_regime() visibility control."""
    
    def test_barter_only_hides_monetary(self):
        """barter_only regime should only show barter keys."""
        full_quotes = {
            'ask_A_in_B': 1.0,
            'bid_A_in_B': 0.9,
            'ask_B_in_A': 1.1,
            'bid_B_in_A': 0.95,
            'ask_A_in_M': 100.0,
            'bid_A_in_M': 90.0,
            'ask_B_in_M': 150.0,
            'bid_B_in_M': 140.0,
        }
        
        filtered = filter_quotes_by_regime(full_quotes, "barter_only")
        
        # Should have barter keys
        assert 'ask_A_in_B' in filtered
        assert 'bid_A_in_B' in filtered
        assert 'ask_B_in_A' in filtered
        assert 'bid_B_in_A' in filtered
        
        # Should NOT have monetary keys
        assert 'ask_A_in_M' not in filtered
        assert 'bid_A_in_M' not in filtered
        assert 'ask_B_in_M' not in filtered
        assert 'bid_B_in_M' not in filtered
    
    def test_money_only_hides_barter(self):
        """money_only regime should only show monetary keys."""
        full_quotes = {
            'ask_A_in_B': 1.0,
            'bid_A_in_B': 0.9,
            'ask_B_in_A': 1.1,
            'bid_B_in_A': 0.95,
            'ask_A_in_M': 100.0,
            'bid_A_in_M': 90.0,
            'ask_B_in_M': 150.0,
            'bid_B_in_M': 140.0,
        }
        
        filtered = filter_quotes_by_regime(full_quotes, "money_only")
        
        # Should NOT have barter keys
        assert 'ask_A_in_B' not in filtered
        assert 'bid_A_in_B' not in filtered
        
        # Should have monetary keys
        assert 'ask_A_in_M' in filtered
        assert 'bid_A_in_M' in filtered
        assert 'ask_B_in_M' in filtered
        assert 'bid_B_in_M' in filtered
    
    def test_mixed_shows_all(self):
        """mixed regime should show all keys."""
        full_quotes = {
            'ask_A_in_B': 1.0,
            'bid_A_in_B': 0.9,
            'ask_A_in_M': 100.0,
            'bid_A_in_M': 90.0,
        }
        
        filtered = filter_quotes_by_regime(full_quotes, "mixed")
        
        # Should have all keys
        assert len(filtered) == len(full_quotes)
        assert all(k in filtered for k in full_quotes.keys())
    
    def test_unknown_regime_defaults_to_barter(self):
        """Unknown regime should default to barter_only with warning."""
        full_quotes = {
            'ask_A_in_B': 1.0,
            'ask_A_in_M': 100.0,
        }
        
        with pytest.warns(UserWarning, match="Unknown exchange_regime"):
            filtered = filter_quotes_by_regime(full_quotes, "invalid_regime")
        
        # Should default to barter_only
        assert 'ask_A_in_B' in filtered
        assert 'ask_A_in_M' not in filtered


class TestRefreshQuotesIfNeeded:
    """Test refresh_quotes_if_needed() integration."""
    
    def test_refreshes_when_inventory_changed(self):
        """Should refresh quotes when inventory_changed is True."""
        agent = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=10, B=10, M=0),
            utility=UCES(rho=0.5, wA=0.6, wB=0.4),
            inventory_changed=True
        )
        
        refreshed = refresh_quotes_if_needed(agent, spread=0.1, epsilon=1e-9)
        
        assert refreshed
        assert not agent.inventory_changed
        assert len(agent.quotes) > 0
    
    def test_no_refresh_when_not_changed(self):
        """Should not refresh when inventory_changed is False."""
        agent = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=10, B=10, M=0),
            utility=UCES(rho=0.5, wA=0.6, wB=0.4),
            inventory_changed=False
        )
        agent.quotes = {'old_key': 999.0}  # Pre-existing quotes
        
        refreshed = refresh_quotes_if_needed(agent, spread=0.1, epsilon=1e-9)
        
        assert not refreshed
        assert agent.quotes == {'old_key': 999.0}  # Unchanged
    
    def test_applies_regime_filter(self):
        """Should apply regime filter when refreshing."""
        agent = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=10, B=10, M=0),
            utility=UCES(rho=0.5, wA=0.6, wB=0.4),
            inventory_changed=True
        )
        
        # Refresh with money_only regime
        refresh_quotes_if_needed(
            agent, spread=0.1, epsilon=1e-9,
            money_scale=100, exchange_regime="money_only"
        )
        
        # Should only have monetary keys
        assert 'ask_A_in_M' in agent.quotes
        assert 'ask_B_in_M' in agent.quotes
        assert 'ask_A_in_B' not in agent.quotes


class TestBackwardCompatibility:
    """Verify backward compatibility with barter_only mode."""
    
    def test_barter_only_quotes_match_legacy(self):
        """Barter quotes in barter_only mode should match legacy behavior."""
        agent = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=10, B=10, M=0),
            utility=UCES(rho=0.5, wA=0.6, wB=0.4)
        )
        
        spread = 0.1
        epsilon = 1e-9
        
        # Get filtered quotes (barter_only)
        all_quotes = compute_quotes(agent, spread, epsilon)
        barter_quotes = filter_quotes_by_regime(all_quotes, "barter_only")
        
        # Check that A<->B quotes are present and valid
        assert 'ask_A_in_B' in barter_quotes
        assert 'bid_A_in_B' in barter_quotes
        
        # Should match MRS-based calculation
        mrs = agent.utility.mrs_A_in_B(10, 10, epsilon)
        assert abs(barter_quotes['ask_A_in_B'] - mrs * (1 + spread)) < 1e-6
        assert abs(barter_quotes['bid_A_in_B'] - mrs * (1 - spread)) < 1e-6


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_zero_inventory_handled(self):
        """Should handle zero inventory without errors."""
        agent = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=0, B=10, M=0),
            utility=UCES(rho=0.5, wA=0.6, wB=0.4)
        )
        
        # Should not raise
        quotes = compute_quotes(agent, spread=0.1, epsilon=1e-9)
        assert quotes is not None
    
    def test_no_utility_function(self):
        """Should handle agents without utility function."""
        agent = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=10, B=10, M=0),
            utility=None
        )
        
        quotes = compute_quotes(agent, spread=0.1, epsilon=1e-9)
        
        # Should return some default quotes
        assert quotes is not None
        assert all(v >= 0 for v in quotes.values())

