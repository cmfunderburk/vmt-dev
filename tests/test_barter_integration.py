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
    sim1 = Simulation(load_scenario(scenario_path), seed=42, log_config=LogConfig.summary())
    sim1.run(max_ticks=40)
    final_inventories_1 = [(a.inventory.A, a.inventory.B) for a in sim1.agents]
    trade_count_1 = _count_trades(sim1)

    # Run 2 (same seed)
    sim2 = Simulation(load_scenario(scenario_path), seed=42, log_config=LogConfig.summary())
    sim2.run(max_ticks=40)
    final_inventories_2 = [(a.inventory.A, a.inventory.B) for a in sim2.agents]
    trade_count_2 = _count_trades(sim2)

    # Determinism: identical final states and trade counts
    assert final_inventories_2 == final_inventories_1
    assert trade_count_2 == trade_count_1

    # Sanity: at least one trade should occur in this demo
    assert trade_count_1 >= 1


