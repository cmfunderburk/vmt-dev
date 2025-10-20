"""
Tests for generic matching primitives (Phase 2b).

Tests money-aware matching logic with mock agents in isolation.
Verifies:
- find_compensating_block_generic() for all three pairs (A<->B, A<->M, B<->M)
- find_best_trade() regime-based selection
- execute_trade_generic() conservation and invariants
"""

import pytest
from src.vmt_engine.core.agent import Agent
from src.vmt_engine.core.state import Inventory
from src.vmt_engine.econ.utility import UCES, ULinear
from src.vmt_engine.systems.matching import (
    find_compensating_block_generic,
    find_best_trade,
    execute_trade_generic
)


class TestFindCompensatingBlockGenericBarter:
    """Test generic matching for barter pair (A<->B)."""
    
    def test_barter_trade_found(self):
        """Should find mutually beneficial barter trade."""
        # Agent 1 has lots of A, wants B
        agent1 = Agent(
            id=1, pos=(0, 0),
            inventory=Inventory(A=10, B=2, M=0),
            utility=UCES(rho=0.5, wA=0.3, wB=0.7)
        )
        
        # Agent 2 has lots of B, wants A
        agent2 = Agent(
            id=2, pos=(0, 1),
            inventory=Inventory(A=2, B=10, M=0),
            utility=UCES(rho=0.5, wA=0.7, wB=0.3)
        )
        
        # Set up quotes (barter-only)
        agent1.quotes = {'ask_A_in_B': 1.5, 'bid_A_in_B': 2.0}
        agent2.quotes = {'ask_A_in_B': 1.0, 'bid_A_in_B': 1.8}
        
        params = {'dA_max': 5}
        
        trade = find_compensating_block_generic(agent1, agent2, "A<->B", params)
        
        assert trade is not None, "Should find a trade"
        dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j = trade
        
        # Conservation
        assert dA_i + dA_j == 0
        assert dB_i + dB_j == 0
        assert dM_i == 0 and dM_j == 0
        
        # Surplus positive
        assert surplus_i > 0
        assert surplus_j > 0
    
    def test_barter_no_trade_when_no_overlap(self):
        """Should return None when quotes don't overlap."""
        agent1 = Agent(
            id=1, pos=(0, 0),
            inventory=Inventory(A=5, B=5, M=0),
            utility=UCES(rho=0.5, wA=0.5, wB=0.5)
        )
        
        agent2 = Agent(
            id=2, pos=(0, 1),
            inventory=Inventory(A=5, B=5, M=0),
            utility=UCES(rho=0.5, wA=0.5, wB=0.5)
        )
        
        # No overlap: both ask too high
        agent1.quotes = {'ask_A_in_B': 3.0, 'bid_A_in_B': 2.5}
        agent2.quotes = {'ask_A_in_B': 3.0, 'bid_A_in_B': 2.5}
        
        params = {'dA_max': 5}
        
        trade = find_compensating_block_generic(agent1, agent2, "A<->B", params)
        
        assert trade is None


class TestFindCompensatingBlockGenericMonetary:
    """Test generic matching for monetary pairs (A<->M, B<->M)."""
    
    def test_monetary_A_for_M_trade(self):
        """Should find trade where agent sells A for money."""
        # Agent 1 has A but desperately needs money (very high lambda)
        agent1 = Agent(
            id=1, pos=(0, 0),
            inventory=Inventory(A=20, B=10, M=0),
            utility=ULinear(vA=1.0, vB=1.0),  # Linear for simplicity
            lambda_money=10.0  # Money is VERY valuable
        )
        
        # Agent 2 has money and low lambda (money less valuable)
        agent2 = Agent(
            id=2, pos=(0, 1),
            inventory=Inventory(A=0, B=10, M=200),
            utility=ULinear(vA=5.0, vB=1.0),  # Values A highly
            lambda_money=0.5  # Money not very valuable
        )
        
        # With these settings:
        # Agent1: will happily sell A for money (since lambda=10 >> vA=1)
        # Agent2: will happily buy A with money (since vA=5 >> lambda=0.5)
        
        # Set up quotes reflecting this
        agent1.quotes = {'ask_A_in_M': 1.0, 'bid_A_in_M': 2.0}
        agent2.quotes = {'ask_A_in_M': 8.0, 'bid_A_in_M': 15.0}
        
        params = {'dA_max': 5}
        
        trade = find_compensating_block_generic(agent1, agent2, "A<->M", params)
        
        assert trade is not None, "Should find a monetary trade"
        dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j = trade
        
        # Conservation
        assert dA_i + dA_j == 0
        assert dB_i == 0 and dB_j == 0  # No B exchange
        assert dM_i + dM_j == 0
        
        # Surplus positive
        assert surplus_i > 0
        assert surplus_j > 0
        
        # Money changed hands
        assert dM_i != 0 or dM_j != 0
    
    def test_monetary_B_for_M_trade(self):
        """Should find trade where agent sells B for money."""
        # Agent 1 has B, high lambda (money very valuable)
        agent1 = Agent(
            id=1, pos=(0, 0),
            inventory=Inventory(A=10, B=20, M=0),
            utility=ULinear(vA=1.0, vB=1.0),
            lambda_money=10.0
        )
        
        # Agent 2 has M, wants B, low lambda (money less valuable)
        agent2 = Agent(
            id=2, pos=(0, 1),
            inventory=Inventory(A=10, B=0, M=200),
            utility=ULinear(vA=1.0, vB=5.0),  # Values B highly
            lambda_money=0.5
        )
        
        # Set up monetary quotes
        agent1.quotes = {'ask_B_in_M': 1.0, 'bid_B_in_M': 2.0}
        agent2.quotes = {'ask_B_in_M': 8.0, 'bid_B_in_M': 15.0}
        
        params = {'dA_max': 5}
        
        trade = find_compensating_block_generic(agent1, agent2, "B<->M", params)
        
        assert trade is not None, "Should find a monetary trade"
        dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j = trade
        
        # Conservation
        assert dA_i == 0 and dA_j == 0  # No A exchange
        assert dB_i + dB_j == 0
        assert dM_i + dM_j == 0
        
        # Surplus positive
        assert surplus_i > 0
        assert surplus_j > 0
    
    def test_no_trade_when_insufficient_money(self):
        """Should return None when buyer doesn't have enough money."""
        agent1 = Agent(
            id=1, pos=(0, 0),
            inventory=Inventory(A=10, B=5, M=0),
            utility=UCES(rho=0.5, wA=0.5, wB=0.5)
        )
        
        # Agent 2 wants A but has no money
        agent2 = Agent(
            id=2, pos=(0, 1),
            inventory=Inventory(A=0, B=5, M=0),  # No money!
            utility=UCES(rho=0.5, wA=0.5, wB=0.5)
        )
        
        agent1.quotes = {'ask_A_in_M': 5.0, 'bid_A_in_M': 10.0}
        agent2.quotes = {'ask_A_in_M': 3.0, 'bid_A_in_M': 8.0}
        
        params = {'dA_max': 5}
        
        trade = find_compensating_block_generic(agent1, agent2, "A<->M", params)
        
        assert trade is None


class TestFindBestTrade:
    """Test find_best_trade() regime-based selection."""
    
    def test_barter_only_regime(self):
        """Should only try barter pair in barter_only mode."""
        agent1 = Agent(
            id=1, pos=(0, 0),
            inventory=Inventory(A=10, B=5, M=50),
            utility=UCES(rho=0.5, wA=0.3, wB=0.7)
        )
        
        agent2 = Agent(
            id=2, pos=(0, 1),
            inventory=Inventory(A=5, B=10, M=50),
            utility=UCES(rho=0.5, wA=0.7, wB=0.3)
        )
        
        # Set up quotes for all pairs
        agent1.quotes = {
            'ask_A_in_B': 1.5, 'bid_A_in_B': 2.0,
            'ask_A_in_M': 8.0, 'bid_A_in_M': 12.0
        }
        agent2.quotes = {
            'ask_A_in_B': 1.0, 'bid_A_in_B': 1.8,
            'ask_A_in_M': 5.0, 'bid_A_in_M': 10.0
        }
        
        params = {'dA_max': 5}
        
        result = find_best_trade(agent1, agent2, "barter_only", params)
        
        assert result is not None
        pair, trade = result
        assert pair == "A<->B", "Should choose barter pair in barter_only mode"
    
    def test_money_only_regime(self):
        """Should only try monetary pairs in money_only mode."""
        agent1 = Agent(
            id=1, pos=(0, 0),
            inventory=Inventory(A=10, B=5, M=0),
            utility=ULinear(vA=1.0, vB=1.0),
            lambda_money=10.0  # High value on money
        )
        
        agent2 = Agent(
            id=2, pos=(0, 1),
            inventory=Inventory(A=0, B=5, M=100),
            utility=ULinear(vA=5.0, vB=1.0),  # High value on A
            lambda_money=0.5  # Low value on money
        )
        
        # Set up quotes for all pairs
        agent1.quotes = {
            'ask_A_in_B': 1.5, 'bid_A_in_B': 2.0,
            'ask_A_in_M': 1.0, 'bid_A_in_M': 2.0
        }
        agent2.quotes = {
            'ask_A_in_B': 1.0, 'bid_A_in_B': 1.8,
            'ask_A_in_M': 8.0, 'bid_A_in_M': 15.0
        }
        
        params = {'dA_max': 5}
        
        result = find_best_trade(agent1, agent2, "money_only", params)
        
        assert result is not None
        pair, trade = result
        assert pair in ["A<->M", "B<->M"], "Should choose monetary pair in money_only mode"
    
    def test_mixed_regime_chooses_best(self):
        """Should try all pairs and choose highest surplus in mixed mode."""
        agent1 = Agent(
            id=1, pos=(0, 0),
            inventory=Inventory(A=15, B=10, M=0),
            utility=ULinear(vA=1.0, vB=1.0),
            lambda_money=10.0
        )
        
        agent2 = Agent(
            id=2, pos=(0, 1),
            inventory=Inventory(A=5, B=15, M=100),
            utility=ULinear(vA=2.0, vB=0.5),
            lambda_money=0.5
        )
        
        # Set up quotes
        agent1.quotes = {
            'ask_A_in_B': 0.8, 'bid_A_in_B': 1.2,
            'ask_A_in_M': 1.0, 'bid_A_in_M': 2.0,
            'ask_B_in_M': 1.0, 'bid_B_in_M': 2.0
        }
        agent2.quotes = {
            'ask_A_in_B': 1.5, 'bid_A_in_B': 2.5,
            'ask_A_in_M': 5.0, 'bid_A_in_M': 10.0,
            'ask_B_in_M': 3.0, 'bid_B_in_M': 6.0
        }
        
        params = {'dA_max': 5}
        
        result = find_best_trade(agent1, agent2, "mixed", params)
        
        # Should find some trade (exact pair depends on surplus calculation)
        assert result is not None
        pair, trade = result
        assert pair in ["A<->B", "A<->M", "B<->M"]
    
    def test_no_trade_possible(self):
        """Should return None when no mutually beneficial trade exists."""
        # Agents with identical preferences and endowments
        agent1 = Agent(
            id=1, pos=(0, 0),
            inventory=Inventory(A=5, B=5, M=50),
            utility=UCES(rho=0.5, wA=0.5, wB=0.5)
        )
        
        agent2 = Agent(
            id=2, pos=(0, 1),
            inventory=Inventory(A=5, B=5, M=50),
            utility=UCES(rho=0.5, wA=0.5, wB=0.5)
        )
        
        # Identical quotes = no trade opportunity
        agent1.quotes = {
            'ask_A_in_B': 1.0, 'bid_A_in_B': 1.0,
            'ask_A_in_M': 10.0, 'bid_A_in_M': 10.0
        }
        agent2.quotes = {
            'ask_A_in_B': 1.0, 'bid_A_in_B': 1.0,
            'ask_A_in_M': 10.0, 'bid_A_in_M': 10.0
        }
        
        params = {'dA_max': 5}
        
        result = find_best_trade(agent1, agent2, "mixed", params)
        
        assert result is None


class TestExecuteTradeGeneric:
    """Test execute_trade_generic() conservation and invariants."""
    
    def test_conservation_barter(self):
        """Should conserve goods in barter trade."""
        agent1 = Agent(
            id=1, pos=(0, 0),
            inventory=Inventory(A=10, B=5, M=0),
            utility=UCES(rho=0.5, wA=0.5, wB=0.5)
        )
        
        agent2 = Agent(
            id=2, pos=(0, 1),
            inventory=Inventory(A=5, B=10, M=0),
            utility=UCES(rho=0.5, wA=0.5, wB=0.5)
        )
        
        # Trade: agent1 gives 3A, receives 4B
        trade = (-3, 4, 0, 3, -4, 0, 0.1, 0.1)
        
        execute_trade_generic(agent1, agent2, trade)
        
        # Check new inventories
        assert agent1.inventory.A == 7
        assert agent1.inventory.B == 9
        assert agent1.inventory.M == 0
        
        assert agent2.inventory.A == 8
        assert agent2.inventory.B == 6
        assert agent2.inventory.M == 0
        
        # Flags set
        assert agent1.inventory_changed
        assert agent2.inventory_changed
    
    def test_conservation_monetary(self):
        """Should conserve goods and money in monetary trade."""
        agent1 = Agent(
            id=1, pos=(0, 0),
            inventory=Inventory(A=10, B=5, M=0),
            utility=UCES(rho=0.5, wA=0.5, wB=0.5)
        )
        
        agent2 = Agent(
            id=2, pos=(0, 1),
            inventory=Inventory(A=5, B=5, M=100),
            utility=UCES(rho=0.5, wA=0.5, wB=0.5)
        )
        
        # Trade: agent1 sells 2A for 20M
        trade = (-2, 0, 20, 2, 0, -20, 0.1, 0.1)
        
        execute_trade_generic(agent1, agent2, trade)
        
        # Check inventories
        assert agent1.inventory.A == 8
        assert agent1.inventory.B == 5
        assert agent1.inventory.M == 20
        
        assert agent2.inventory.A == 7
        assert agent2.inventory.B == 5
        assert agent2.inventory.M == 80
        
        # Total money conserved
        assert agent1.inventory.M + agent2.inventory.M == 100
    
    def test_non_negativity_enforced(self):
        """Should fail assertion if trade would make inventory negative."""
        agent1 = Agent(
            id=1, pos=(0, 0),
            inventory=Inventory(A=2, B=5, M=0),
            utility=UCES(rho=0.5, wA=0.5, wB=0.5)
        )
        
        agent2 = Agent(
            id=2, pos=(0, 1),
            inventory=Inventory(A=5, B=10, M=0),
            utility=UCES(rho=0.5, wA=0.5, wB=0.5)
        )
        
        # Trade would make agent1.A negative
        trade = (-5, 0, 0, 5, 0, 0, 0.1, 0.1)
        
        with pytest.raises(AssertionError, match="inventory negative"):
            execute_trade_generic(agent1, agent2, trade)
    
    def test_conservation_violated_fails(self):
        """Should fail assertion if conservation is violated."""
        agent1 = Agent(
            id=1, pos=(0, 0),
            inventory=Inventory(A=10, B=5, M=0),
            utility=UCES(rho=0.5, wA=0.5, wB=0.5)
        )
        
        agent2 = Agent(
            id=2, pos=(0, 1),
            inventory=Inventory(A=5, B=10, M=0),
            utility=UCES(rho=0.5, wA=0.5, wB=0.5)
        )
        
        # Invalid trade: doesn't conserve A
        trade = (-3, 0, 0, 5, 0, 0, 0.1, 0.1)  # -3 + 5 != 0
        
        with pytest.raises(AssertionError, match="not conserved"):
            execute_trade_generic(agent1, agent2, trade)


class TestDeterminism:
    """Test that matching is deterministic."""
    
    def test_same_inputs_same_output(self):
        """Same inputs should always produce same output."""
        results = []
        
        for _ in range(3):
            agent1 = Agent(
                id=1, pos=(0, 0),
                inventory=Inventory(A=10, B=5, M=50),
                utility=UCES(rho=0.5, wA=0.4, wB=0.6)
            )
            
            agent2 = Agent(
                id=2, pos=(0, 1),
                inventory=Inventory(A=5, B=10, M=50),
                utility=UCES(rho=0.5, wA=0.6, wB=0.4)
            )
            
            agent1.quotes = {
                'ask_A_in_B': 1.5, 'bid_A_in_B': 2.0,
                'ask_A_in_M': 8.0, 'bid_A_in_M': 12.0
            }
            agent2.quotes = {
                'ask_A_in_B': 1.0, 'bid_A_in_B': 1.8,
                'ask_A_in_M': 5.0, 'bid_A_in_M': 10.0
            }
            
            params = {'dA_max': 5}
            
            result = find_best_trade(agent1, agent2, "mixed", params)
            results.append(result)
        
        # All results should be identical
        assert results[0] == results[1] == results[2]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

