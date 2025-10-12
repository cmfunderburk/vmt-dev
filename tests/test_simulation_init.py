"""
Tests for simulation initialization.
"""

import pytest
from scenarios.loader import load_scenario
from vmt_engine.simulation import Simulation


def test_simulation_initialization():
    """Test basic simulation initialization."""
    scenario = load_scenario("scenarios/single_agent_forage.yaml")
    sim = Simulation(scenario, seed=42)
    
    assert sim.tick == 0
    assert len(sim.agents) == 1
    assert sim.grid.N == 16


def test_simulation_determinism():
    """Test that same seed produces same initial state."""
    scenario = load_scenario("scenarios/three_agent_barter.yaml")
    
    sim1 = Simulation(scenario, seed=123)
    sim2 = Simulation(scenario, seed=123)
    
    # Check agents have same initial positions
    for a1, a2 in zip(sim1.agents, sim2.agents):
        assert a1.pos == a2.pos
        assert a1.inventory.A == a2.inventory.A
        assert a1.inventory.B == a2.inventory.B


def test_simulation_different_seeds():
    """Test that different seeds produce different states."""
    scenario = load_scenario("scenarios/three_agent_barter.yaml")
    
    sim1 = Simulation(scenario, seed=111)
    sim2 = Simulation(scenario, seed=222)
    
    # Check that at least one agent has different position
    positions_differ = False
    for a1, a2 in zip(sim1.agents, sim2.agents):
        if a1.pos != a2.pos:
            positions_differ = True
            break
    
    assert positions_differ, "Different seeds should produce different initial positions"


def test_agents_sorted_by_id():
    """Test that agents are sorted by id."""
    scenario = load_scenario("scenarios/three_agent_barter.yaml")
    sim = Simulation(scenario, seed=42)
    
    for i, agent in enumerate(sim.agents):
        assert agent.id == i


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

