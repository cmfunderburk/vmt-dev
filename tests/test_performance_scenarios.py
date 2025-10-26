"""
Tests for performance benchmark scenarios.

Ensures the performance scenarios load correctly and run without errors.
Does NOT enforce performance targets (use scripts/benchmark_performance.py for that).
"""

import pytest
from scenarios.loader import load_scenario
from vmt_engine.simulation import Simulation
from telemetry.config import LogConfig


@pytest.mark.parametrize("scenario_name,expected_agents,expected_grid_size", [
    ("perf_forage_only", 400, 50),
    ("perf_exchange_only", 400, 50),
    ("perf_both_modes", 400, 50),
])
def test_performance_scenario_loads(scenario_name, expected_agents, expected_grid_size):
    """Verify performance scenarios load and have correct configuration."""
    config = load_scenario(f"scenarios/{scenario_name}.yaml")
    
    assert config.agents == expected_agents
    assert config.N == expected_grid_size
    assert len(config.utilities.mix) > 0  # Has utility mix
    
    # Verify utility weights sum to 1.0
    total_weight = sum(u.weight for u in config.utilities.mix)
    assert abs(total_weight - 1.0) < 1e-6


@pytest.mark.parametrize("scenario_name", [
    "perf_forage_only",
    "perf_exchange_only",
    "perf_both_modes",
])
def test_performance_scenario_runs(scenario_name):
    """Verify performance scenarios can run for a few ticks without errors."""
    config = load_scenario(f"scenarios/{scenario_name}.yaml")
    
    # Run for just 5 ticks with no logging
    sim = Simulation(config, seed=42, log_config=LogConfig(use_database=False))
    sim.run(max_ticks=5)
    
    # Basic sanity checks
    assert sim.tick == 5
    assert len(sim.agents) == 400
    
    # Verify all agents still exist and have valid state
    for agent in sim.agents:
        assert agent.inventory.A >= 0
        assert agent.inventory.B >= 0
        assert agent.inventory.M >= 0


def test_performance_scenarios_are_deterministic():
    """Verify performance scenarios produce deterministic results."""
    scenario = "perf_both_modes"
    
    # Run 1
    config1 = load_scenario(f"scenarios/{scenario}.yaml")
    sim1 = Simulation(config1, seed=42, log_config=LogConfig(use_database=False))
    sim1.run(max_ticks=10)
    inv1 = [(a.inventory.A, a.inventory.B) for a in sim1.agents]
    
    # Run 2 (same seed)
    config2 = load_scenario(f"scenarios/{scenario}.yaml")
    sim2 = Simulation(config2, seed=42, log_config=LogConfig(use_database=False))
    sim2.run(max_ticks=10)
    inv2 = [(a.inventory.A, a.inventory.B) for a in sim2.agents]
    
    # Identical results
    assert inv1 == inv2

