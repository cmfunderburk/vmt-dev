"""
Minimal integration test to verify the foundational barter scenario produces trades
under pytest using default (legacy) protocols.
"""

from scenarios.loader import load_scenario
from vmt_engine.simulation import Simulation


def test_foundational_barter_demo_produces_trades_and_inventory_changes():
    s = load_scenario('scenarios/foundational_barter_demo.yaml')
    sim = Simulation(s, seed=42)

    # Capture initial inventories
    initial_inventories = [(a.inventory.A, a.inventory.B) for a in sim.agents]

    # Run a short simulation
    sim.run(20)

    # Trades should occur
    assert len(sim.telemetry.recent_trades_for_renderer) > 0

    # At least one agent's inventory should change
    final_inventories = [(a.inventory.A, a.inventory.B) for a in sim.agents]
    changed_count = sum(1 for i, f in zip(initial_inventories, final_inventories) if f != i)
    assert changed_count > 0


