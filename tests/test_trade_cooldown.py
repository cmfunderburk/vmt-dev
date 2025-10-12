"""
Tests for trade cooldown system.
"""

import pytest
from vmt_engine.core import Agent, Inventory, Quote
from vmt_engine.econ.utility import UCES
from vmt_engine.systems.matching import choose_partner


def test_trade_cooldown_prevents_retargeting():
    """Test that cooldown prevents immediate re-targeting of failed partner."""
    # Create agents with different quotes (so surplus exists)
    agent1 = Agent(
        id=1, pos=(0, 0), inventory=Inventory(A=8, B=4),
        utility=UCES(rho=-0.5, wA=1.0, wB=1.0),
        quotes=Quote(ask_A_in_B=0.5, bid_A_in_B=0.5, p_min=0.5, p_max=0.5)
    )
    
    agent2 = Agent(
        id=2, pos=(0, 1), inventory=Inventory(A=4, B=8),
        utility=UCES(rho=-0.5, wA=1.0, wB=1.0),
        quotes=Quote(ask_A_in_B=2.0, bid_A_in_B=2.0, p_min=2.0, p_max=2.0)
    )
    
    # Simulate failed trade at tick 10, cooldown until tick 15
    agent1.trade_cooldowns[2] = 15
    
    # Before cooldown expires (tick 14)
    neighbors = [(2, (0, 1))]
    partner, _, _ = choose_partner(agent1, neighbors, {2: agent2}, current_tick=14)
    assert partner is None, "Should skip partner in cooldown"
    assert 2 in agent1.trade_cooldowns, "Cooldown should still be active"
    
    # After cooldown expires (tick 15)
    partner, surplus, _ = choose_partner(agent1, neighbors, {2: agent2}, current_tick=15)
    assert partner == 2, "Cooldown expired, should consider partner again"
    assert surplus > 0, "Should detect positive surplus"
    assert 2 not in agent1.trade_cooldowns, "Cooldown should be removed"


def test_cooldown_allows_other_partners():
    """Test that cooldown only affects specific partner, not all trading."""
    agent1 = Agent(
        id=1, pos=(0, 0), inventory=Inventory(A=5, B=5),
        utility=UCES(rho=-0.5, wA=1.0, wB=1.0),
        quotes=Quote(ask_A_in_B=1.0, bid_A_in_B=1.0, p_min=1.0, p_max=1.0)
    )
    
    agent2 = Agent(
        id=2, pos=(0, 1), inventory=Inventory(A=3, B=7),
        utility=UCES(rho=-0.5, wA=1.0, wB=1.0),
        quotes=Quote(ask_A_in_B=2.0, bid_A_in_B=2.0, p_min=2.0, p_max=2.0)
    )
    
    agent3 = Agent(
        id=3, pos=(1, 0), inventory=Inventory(A=7, B=3),
        utility=UCES(rho=-0.5, wA=1.0, wB=1.0),
        quotes=Quote(ask_A_in_B=0.5, bid_A_in_B=0.5, p_min=0.5, p_max=0.5)
    )
    
    # Agent 1 has cooldown with agent 2
    agent1.trade_cooldowns[2] = 20
    
    # But can still trade with agent 3
    neighbors = [(2, (0, 1)), (3, (1, 0))]
    partner, surplus, _ = choose_partner(agent1, neighbors, {2: agent2, 3: agent3}, current_tick=10)
    
    # Should choose agent 3 (not in cooldown) even if agent 2 has higher surplus
    assert partner == 3, "Should choose non-cooldown partner"


def test_cooldown_with_no_surplus():
    """Test that cooldown doesn't cause issues when no surplus exists."""
    agent1 = Agent(
        id=1, pos=(0, 0), inventory=Inventory(A=5, B=5),
        utility=UCES(rho=-0.5, wA=1.0, wB=1.0),
        quotes=Quote(ask_A_in_B=1.0, bid_A_in_B=1.0, p_min=1.0, p_max=1.0)
    )
    
    agent2 = Agent(
        id=2, pos=(0, 1), inventory=Inventory(A=5, B=5),
        utility=UCES(rho=-0.5, wA=1.0, wB=1.0),
        quotes=Quote(ask_A_in_B=1.0, bid_A_in_B=1.0, p_min=1.0, p_max=1.0)
    )
    
    # Set cooldown
    agent1.trade_cooldowns[2] = 15
    
    # No surplus anyway (ask=bid=1.0 for both)
    neighbors = [(2, (0, 1))]
    partner, _, _ = choose_partner(agent1, neighbors, {2: agent2}, current_tick=10)
    
    assert partner is None, "No partner chosen (no surplus)"


def test_cooldown_zero_disables():
    """Test that cooldown_ticks=0 results in immediate cooldown expiry."""
    agent1 = Agent(
        id=1, pos=(0, 0), inventory=Inventory(A=5, B=5),
        utility=UCES(rho=-0.5, wA=1.0, wB=1.0),
        quotes=Quote(ask_A_in_B=1.0, bid_A_in_B=1.0, p_min=1.0, p_max=1.0)
    )
    
    # Cooldown until same tick (cooldown_ticks=0)
    agent1.trade_cooldowns[2] = 10  # Set at tick 10 with 0-tick cooldown
    
    # Same tick should already expire
    neighbors = [(2, (0, 1))]
    agent2 = Agent(id=2, pos=(0,1), inventory=Inventory(A=3, B=7),
                   quotes=Quote(ask_A_in_B=2.0, bid_A_in_B=2.0, p_min=2.0, p_max=2.0))
    
    partner, _, _ = choose_partner(agent1, neighbors, {2: agent2}, current_tick=10)
    assert partner == 2, "With cooldown_ticks=0, should immediately be available"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

