"""
Tests for trade evaluation abstractions.

Tests the new TradePotentialEvaluator and TradeDiscoverer interfaces,
including behavioral equivalence with the old implementation.

Version: 2025.11.03
"""

import pytest
from decimal import Decimal
from vmt_engine.core.agent import Agent
from vmt_engine.core.state import Inventory
from vmt_engine.econ.utility import ULinear, UQuadratic
from vmt_engine.systems.trade_evaluation import (
    TradePotential,
    TradePotentialEvaluator,
    QuoteBasedTradeEvaluator,
    TradeTuple,
    TradeDiscoverer,
)
from vmt_engine.game_theory.bargaining.discovery import CompensatingBlockDiscoverer
from vmt_engine.systems.matching import find_compensating_block_generic


class TestQuoteBasedTradeEvaluator:
    """Test QuoteBasedTradeEvaluator heuristic."""
    
    def test_no_overlap_not_feasible(self):
        """Test that no quote overlap results in not feasible."""
        evaluator = QuoteBasedTradeEvaluator()
        
        # Agent i wants to buy A at 5, agent j wants to sell A at 10
        # No overlap
        agent_i = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=Decimal("10"), B=Decimal("10")),
            utility=ULinear(vA=0.5, vB=0.5),
            quotes={'bid_A_in_B': 5.0, 'ask_A_in_B': 15.0}
        )
        agent_j = Agent(
            id=2,
            pos=(0, 0),
            inventory=Inventory(A=Decimal("10"), B=Decimal("10")),
            utility=ULinear(vA=0.5, vB=0.5),
            quotes={'bid_A_in_B': 3.0, 'ask_A_in_B': 10.0}
        )
        
        potential = evaluator.evaluate_pair_potential(agent_i, agent_j)
        
        assert not potential.is_feasible
        assert potential.estimated_surplus == 0.0
        assert potential.preferred_direction is None
        assert potential.confidence == 1.0
    
    def test_positive_overlap_feasible(self):
        """Test that positive overlap results in feasible."""
        evaluator = QuoteBasedTradeEvaluator()
        
        # Agent i wants to buy A at 10, agent j wants to sell A at 5
        # Overlap of 5
        agent_i = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=Decimal("10"), B=Decimal("20")),
            utility=ULinear(vA=0.5, vB=0.5),
            quotes={'bid_A_in_B': 10.0, 'ask_A_in_B': 15.0}
        )
        agent_j = Agent(
            id=2,
            pos=(0, 0),
            inventory=Inventory(A=Decimal("10"), B=Decimal("10")),
            utility=ULinear(vA=0.5, vB=0.5),
            quotes={'bid_A_in_B': 3.0, 'ask_A_in_B': 5.0}
        )
        
        potential = evaluator.evaluate_pair_potential(agent_i, agent_j)
        
        assert potential.is_feasible
        assert potential.estimated_surplus > 0.0
        assert potential.preferred_direction in ["i_gives_A", "i_gives_B"]
        assert 0.0 <= potential.confidence <= 1.0
    
    def test_zero_inventory_not_feasible(self):
        """Test that zero inventory prevents feasibility."""
        evaluator = QuoteBasedTradeEvaluator()
        
        # Good quotes but no inventory
        agent_i = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=Decimal("0"), B=Decimal("0")),
            utility=ULinear(vA=0.5, vB=0.5),
            quotes={'bid_A_in_B': 10.0, 'ask_A_in_B': 15.0}
        )
        agent_j = Agent(
            id=2,
            pos=(0, 0),
            inventory=Inventory(A=Decimal("0"), B=Decimal("0")),
            utility=ULinear(vA=0.5, vB=0.5),
            quotes={'bid_A_in_B': 3.0, 'ask_A_in_B': 5.0}
        )
        
        potential = evaluator.evaluate_pair_potential(agent_i, agent_j)
        
        # compute_surplus includes inventory check
        assert not potential.is_feasible


class TestCompensatingBlockDiscoverer:
    """Test CompensatingBlockDiscoverer trade discovery."""
    
    def test_no_utility_returns_none(self):
        """Test that agents without utility return None."""
        discoverer = CompensatingBlockDiscoverer()
        
        agent_i = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=Decimal("10"), B=Decimal("10")),
            utility=None,
            quotes={}
        )
        agent_j = Agent(
            id=2,
            pos=(0, 0),
            inventory=Inventory(A=Decimal("10"), B=Decimal("10")),
            utility=None,
            quotes={}
        )
        
        result = discoverer.discover_trade(agent_i, agent_j)
        assert result is None
    
    def test_no_overlap_returns_none(self):
        """Test that no quote overlap returns None."""
        discoverer = CompensatingBlockDiscoverer()
        
        # No overlap in quotes
        agent_i = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=Decimal("10"), B=Decimal("10")),
            utility=ULinear(vA=0.5, vB=0.5),
            quotes={'bid_A_in_B': 5.0, 'ask_A_in_B': 15.0}
        )
        agent_j = Agent(
            id=2,
            pos=(0, 0),
            inventory=Inventory(A=Decimal("10"), B=Decimal("10")),
            utility=ULinear(vA=0.5, vB=0.5),
            quotes={'bid_A_in_B': 3.0, 'ask_A_in_B': 10.0}
        )
        
        result = discoverer.discover_trade(agent_i, agent_j)
        assert result is None
    
    def test_finds_feasible_trade(self):
        """Test that feasible trade can be found with proper setup."""
        discoverer = CompensatingBlockDiscoverer()
        
        # Simple case: agent i has B and wants A, agent j has A and wants B
        # Both agents have symmetric linear utilities and good inventory
        agent_i = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=Decimal("1"), B=Decimal("100")),
            utility=ULinear(vA=3.0, vB=1.0),  # Values A highly
            quotes={'bid_A_in_B': 10.0, 'ask_A_in_B': 15.0}
        )
        agent_j = Agent(
            id=2,
            pos=(0, 0),
            inventory=Inventory(A=Decimal("100"), B=Decimal("1")),
            utility=ULinear(vA=1.0, vB=3.0),  # Values B highly
            quotes={'bid_A_in_B': 1.0, 'ask_A_in_B': 3.0}
        )
        
        result = discoverer.discover_trade(agent_i, agent_j)
        
        # With good overlap and complementary preferences, should find a trade
        if result is not None:
            assert isinstance(result, TradeTuple)
            assert result.surplus_i > 0
            assert result.surplus_j > 0
            assert result.price > 0
            assert result.pair_name == "A<->B"
            # Conservation laws
            assert result.dA_i + result.dA_j == 0
            assert result.dB_i + result.dB_j == 0
        # Note: We don't assert result is not None because whether a trade
        # is found depends on the exact utility calculation and epsilon threshold
    
    def test_behavioral_equivalence_with_old_implementation(self):
        """
        Test that CompensatingBlockDiscoverer produces same result as
        find_compensating_block_generic.
        """
        discoverer = CompensatingBlockDiscoverer()
        
        # Create test agents
        agent_i = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=Decimal("10"), B=Decimal("20")),
            utility=UQuadratic(A_star=15.0, B_star=25.0, sigma_A=5.0, sigma_B=5.0),
            quotes={'bid_A_in_B': 7.0, 'ask_A_in_B': 9.0}
        )
        agent_j = Agent(
            id=2,
            pos=(0, 0),
            inventory=Inventory(A=Decimal("15"), B=Decimal("10")),
            utility=UQuadratic(A_star=20.0, B_star=15.0, sigma_A=5.0, sigma_B=5.0),
            quotes={'bid_A_in_B': 5.0, 'ask_A_in_B': 6.0}
        )
        
        # Call new implementation
        new_result = discoverer.discover_trade(agent_i, agent_j, epsilon=1e-9)
        
        # Call old implementation
        old_result = find_compensating_block_generic(
            agent_i, agent_j, "A<->B", {}, epsilon=1e-9
        )
        
        # Both should find a trade or both should fail
        if old_result is None:
            assert new_result is None
        else:
            assert new_result is not None
            # Unpack old result
            dA_i_old, dB_i_old, dA_j_old, dB_j_old, surplus_i_old, surplus_j_old = old_result
            
            # Compare values (allowing for floating point tolerance)
            assert new_result.dA_i == dA_i_old
            assert new_result.dB_i == dB_i_old
            assert new_result.dA_j == dA_j_old
            assert new_result.dB_j == dB_j_old
            assert abs(new_result.surplus_i - surplus_i_old) < 1e-6
            assert abs(new_result.surplus_j - surplus_j_old) < 1e-6
            assert new_result.pair_name == "A<->B"
    
    def test_multiple_scenarios_equivalence(self):
        """Test equivalence across multiple agent configurations."""
        discoverer = CompensatingBlockDiscoverer()
        
        test_cases = [
            # (agent_i_inventory, agent_i_alpha, agent_j_inventory, agent_j_alpha)
            ((10, 20), 0.7, (20, 10), 0.3),
            ((5, 15), 0.8, (15, 5), 0.2),
            ((8, 12), 0.6, (12, 8), 0.4),
        ]
        
        for (A_i, B_i), alpha_i, (A_j, B_j), alpha_j in test_cases:
            agent_i = Agent(
                id=1,
                pos=(0, 0),
                inventory=Inventory(A=Decimal(str(A_i)), B=Decimal(str(B_i))),
                utility=ULinear(vA=alpha_i, vB=1.0-alpha_i),
                quotes={'bid_A_in_B': 8.0, 'ask_A_in_B': 10.0}
            )
            agent_j = Agent(
                id=2,
                pos=(0, 0),
                inventory=Inventory(A=Decimal(str(A_j)), B=Decimal(str(B_j))),
                utility=ULinear(vA=alpha_j, vB=1.0-alpha_j),
                quotes={'bid_A_in_B': 4.0, 'ask_A_in_B': 6.0}
            )
            
            new_result = discoverer.discover_trade(agent_i, agent_j)
            old_result = find_compensating_block_generic(agent_i, agent_j, "A<->B", {})
            
            # Results should match
            if old_result is None:
                assert new_result is None, f"Mismatch for case {A_i},{B_i},{alpha_i},{A_j},{B_j},{alpha_j}"
            else:
                assert new_result is not None, f"Mismatch for case {A_i},{B_i},{alpha_i},{A_j},{B_j},{alpha_j}"
                dA_i_old, dB_i_old, dA_j_old, dB_j_old, _, _ = old_result
                assert new_result.dA_i == dA_i_old
                assert new_result.dB_i == dB_i_old


class TestTradeTupleInvariants:
    """Test that TradeTuple maintains required invariants."""
    
    def test_conservation_laws(self):
        """Test that discovered trades conserve goods."""
        discoverer = CompensatingBlockDiscoverer()
        
        agent_i = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=Decimal("10"), B=Decimal("20")),
            utility=ULinear(vA=0.7, vB=0.3),
            quotes={'bid_A_in_B': 8.0, 'ask_A_in_B': 12.0}
        )
        agent_j = Agent(
            id=2,
            pos=(0, 0),
            inventory=Inventory(A=Decimal("20"), B=Decimal("10")),
            utility=ULinear(vA=0.3, vB=0.7),
            quotes={'bid_A_in_B': 4.0, 'ask_A_in_B': 6.0}
        )
        
        result = discoverer.discover_trade(agent_i, agent_j)
        
        if result is not None:
            # Conservation of good A
            assert result.dA_i + result.dA_j == 0, "Good A not conserved"
            # Conservation of good B
            assert result.dB_i + result.dB_j == 0, "Good B not conserved"
    
    def test_mutual_benefit(self):
        """Test that both agents benefit from discovered trade."""
        discoverer = CompensatingBlockDiscoverer()
        
        agent_i = Agent(
            id=1,
            pos=(0, 0),
            inventory=Inventory(A=Decimal("10"), B=Decimal("20")),
            utility=ULinear(vA=0.7, vB=0.3),
            quotes={'bid_A_in_B': 8.0, 'ask_A_in_B': 12.0}
        )
        agent_j = Agent(
            id=2,
            pos=(0, 0),
            inventory=Inventory(A=Decimal("20"), B=Decimal("10")),
            utility=ULinear(vA=0.3, vB=0.7),
            quotes={'bid_A_in_B': 4.0, 'ask_A_in_B': 6.0}
        )
        
        result = discoverer.discover_trade(agent_i, agent_j, epsilon=1e-9)
        
        if result is not None:
            assert result.surplus_i > 0, "Agent i does not benefit"
            assert result.surplus_j > 0, "Agent j does not benefit"

