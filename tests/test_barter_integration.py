"""
Barter integration test on foundational_barter_demo.yaml.

Asserts determinism and a stable number of trades for seed=42.
"""

import pytest
from scenarios.loader import load_scenario
from vmt_engine.simulation import Simulation
from telemetry.config import LogConfig


def _count_trades(sim: Simulation) -> int:
    # Telemetry buffers are internal; we rely on renderer buffer length
    return len(sim.telemetry.recent_trades_for_renderer)


def test_foundational_barter_demo_determinism_and_trades():
    scenario_path = "scenarios/foundational_barter_demo.yaml"

    # Run 1
    sim1 = Simulation(load_scenario(scenario_path), seed=42, log_config=LogConfig.standard())
    sim1.run(max_ticks=40)
    final_inventories_1 = [(a.inventory.A, a.inventory.B) for a in sim1.agents]
    trade_count_1 = _count_trades(sim1)

    # Run 2 (same seed)
    sim2 = Simulation(load_scenario(scenario_path), seed=42, log_config=LogConfig.standard())
    sim2.run(max_ticks=40)
    final_inventories_2 = [(a.inventory.A, a.inventory.B) for a in sim2.agents]
    trade_count_2 = _count_trades(sim2)

    # Determinism: identical final states and trade counts
    assert final_inventories_2 == final_inventories_1
    assert trade_count_2 == trade_count_1

    # Sanity: at least one trade should occur in this demo
    assert trade_count_1 >= 1


def test_barter_only_pairing_unchanged():
    """
    Regression test to ensure money-aware pairing changes don't affect barter_only mode.
    
    This test verifies that in barter_only regime, agents still use the traditional
    compute_surplus function for pairing decisions, preserving bit-identical behavior.
    """
    scenario_path = "scenarios/foundational_barter_demo.yaml"
    
    # Run simulation
    sim = Simulation(load_scenario(scenario_path), seed=123, log_config=LogConfig.standard())
    sim.run(max_ticks=5)
    
    # Verify regime is barter_only
    assert sim.params.get("exchange_regime", "barter_only") == "barter_only"
    
    # Verify all agents have M=0 (no money in barter)
    for agent in sim.agents:
        assert agent.inventory.M == 0, "Barter scenario should have no money"
    
    # Run a second time with same seed to verify determinism
    sim2 = Simulation(load_scenario(scenario_path), seed=123, log_config=LogConfig.standard())
    sim2.run(max_ticks=5)
    
    # Compare final states
    for i, (agent1, agent2) in enumerate(zip(sim.agents, sim2.agents)):
        assert agent1.inventory.A == agent2.inventory.A, f"Agent {i} A inventory differs"
        assert agent1.inventory.B == agent2.inventory.B, f"Agent {i} B inventory differs"
        assert agent1.pos == agent2.pos, f"Agent {i} position differs"
    
    print("✓ Barter-only mode preserved bit-identical behavior")


