"""
Unit tests for trade evaluation abstractions.

Tests the lightweight evaluation interfaces for matching phase
and full discovery interfaces for bargaining phase.
"""

import pytest
from decimal import Decimal
from src.vmt_engine.systems.trade_evaluation import (
    TradePotential,
    TradePotentialEvaluator,
    QuoteBasedTradeEvaluator,
    TradeTuple,
)
from tests.helpers.builders import build_agent


class TestTradePotentialNamedTuple:
    """Test TradePotential as NamedTuple."""
    
    def test_trade_potential_creation(self):
        """Test basic NamedTuple creation and field access."""
        potential = TradePotential(
            is_feasible=True,
            estimated_surplus=5.0,
            preferred_direction="i_gives_A",
            confidence=0.8
        )
        
        assert potential.is_feasible is True
        assert potential.estimated_surplus == 5.0
        assert potential.preferred_direction == "i_gives_A"
        assert potential.confidence == 0.8
    
    def test_trade_potential_immutable(self):
        """Verify NamedTuple is immutable."""
        potential = TradePotential(True, 5.0, "i_gives_A", 0.8)
        
        with pytest.raises(AttributeError):
            potential.is_feasible = False
    
    def test_trade_potential_tuple_unpacking(self):
        """Test NamedTuple can be unpacked like regular tuple."""
        potential = TradePotential(True, 5.0, "i_gives_A", 0.8)
        
        is_feasible, surplus, direction, confidence = potential
        assert is_feasible is True
        assert surplus == 5.0


class TestQuoteBasedTradeEvaluator:
    """Test the lightweight evaluation interface for matching."""
    
    def test_no_quote_overlap_infeasible(self):
        """No quote overlap should return infeasible."""
        agent_i = build_agent(
            id=1, inv_A=10, inv_B=10,
            quotes={'bid_A_in_B': 1.0, 'ask_A_in_B': 2.0}
        )
        agent_j = build_agent(
            id=2, inv_A=10, inv_B=10,
            quotes={'bid_A_in_B': 1.0, 'ask_A_in_B': 2.0}
        )
        
        evaluator = QuoteBasedTradeEvaluator()
        potential = evaluator.evaluate_pair_potential(agent_i, agent_j)
        
        assert isinstance(potential, TradePotential)
        assert not potential.is_feasible
        assert potential.estimated_surplus == 0.0
        assert potential.preferred_direction is None
        assert potential.confidence == 1.0
    
    def test_quote_overlap_feasible(self):
        """Quote overlap should return feasible with estimated surplus."""
        agent_i = build_agent(
            id=1, inv_A=10, inv_B=10,
            quotes={'bid_A_in_B': 3.0, 'ask_A_in_B': 2.0}
        )
        agent_j = build_agent(
            id=2, inv_A=10, inv_B=10,
            quotes={'bid_A_in_B': 2.5, 'ask_A_in_B': 1.0}
        )
        
        evaluator = QuoteBasedTradeEvaluator()
        potential = evaluator.evaluate_pair_potential(agent_i, agent_j)
        
        assert potential.is_feasible
        assert potential.estimated_surplus > 0
        assert potential.preferred_direction in ["i_gives_A", "i_gives_B"]
        assert 0.0 <= potential.confidence <= 1.0
    
    def test_evaluator_lightweight(self):
        """Verify evaluator doesn't mutate agents."""
        agent_i = build_agent(id=1, inv_A=10, inv_B=10)
        agent_j = build_agent(id=2, inv_A=10, inv_B=10)
        
        inv_i_before = (agent_i.inventory.A, agent_i.inventory.B)
        inv_j_before = (agent_j.inventory.A, agent_j.inventory.B)
        
        evaluator = QuoteBasedTradeEvaluator()
        evaluator.evaluate_pair_potential(agent_i, agent_j)
        
        assert (agent_i.inventory.A, agent_i.inventory.B) == inv_i_before
        assert (agent_j.inventory.A, agent_j.inventory.B) == inv_j_before


class TestTradeTupleNamedTuple:
    """Test TradeTuple as NamedTuple."""
    
    def test_trade_tuple_creation(self):
        """Test basic NamedTuple creation and field access."""
        trade = TradeTuple(
            dA_i=Decimal("-5"),
            dB_i=Decimal("10"),
            dA_j=Decimal("5"),
            dB_j=Decimal("-10"),
            surplus_i=2.5,
            surplus_j=3.0,
            price=2.0,
            pair_name="A<->B"
        )
        
        assert trade.dA_i == Decimal("-5")
        assert trade.surplus_i == 2.5
        assert trade.pair_name == "A<->B"
    
    def test_trade_tuple_immutable(self):
        """Verify NamedTuple is immutable."""
        trade = TradeTuple(
            Decimal("5"), Decimal("-10"), Decimal("-5"), Decimal("10"),
            2.5, 3.0, 2.0, "A<->B"
        )
        
        with pytest.raises(AttributeError):
            trade.price = 3.0
    
    def test_trade_tuple_conservation(self):
        """Verify conservation laws in TradeTuple."""
        trade = TradeTuple(
            dA_i=Decimal("-5"),
            dB_i=Decimal("10"),
            dA_j=Decimal("5"),
            dB_j=Decimal("-10"),
            surplus_i=2.5,
            surplus_j=3.0,
            price=2.0,
            pair_name="A<->B"
        )
        
        # Conservation of A and B
        assert trade.dA_i + trade.dA_j == 0
        assert trade.dB_i + trade.dB_j == 0
        
        # Mutual benefit
        assert trade.surplus_i > 0
        assert trade.surplus_j > 0
