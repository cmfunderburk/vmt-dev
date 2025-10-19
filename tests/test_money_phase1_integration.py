"""
Integration tests for Phase 1 money system infrastructure.

Verifies that legacy scenarios are completely unaffected by the changes.
"""

import tempfile
import sqlite3
from vmt_engine.simulation import Simulation
from scenarios.loader import load_scenario
from telemetry.config import LogConfig


def test_legacy_scenario_unchanged():
    """Verify that a legacy scenario runs and produces identical agent states."""
    # Load a legacy scenario that does not have any money parameters
    config = load_scenario("scenarios/three_agent_barter.yaml")

    # The loader should have applied the default 'barter_only' regime
    assert config.params.exchange_regime == "barter_only"

    # Run the simulation without logging for speed
    sim = Simulation(config, seed=42, log_config=LogConfig(use_database=False))
    sim.run(max_ticks=10)

    # Verify that all agents have M=0 and default lambda, as no money was specified
    for agent in sim.agents:
        assert agent.inventory.M == 0
        assert agent.lambda_money == 1.0  # Default value from ScenarioParams via loader

    # Note: A deeper comparison is done with a snapshot diff test


def test_telemetry_logs_barter_only_regime_for_legacy_scenario():
    """Verify that telemetry correctly logs the default 'barter_only' regime."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = f"{tmpdir}/test_phase1_telemetry.db"
        config = load_scenario("scenarios/three_agent_barter.yaml")
        log_cfg = LogConfig(use_database=True, db_path=db_path)

        # Run the simulation
        sim = Simulation(config, seed=42, log_config=log_cfg)
        sim.run(max_ticks=5)
        sim.close()

        # Query the tick_states table to verify the logged regime
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT DISTINCT exchange_regime FROM tick_states WHERE run_id = ?", (sim.telemetry.run_id,))
        regimes = {row[0] for row in cursor.fetchall()}
        conn.close()

        assert regimes == {"barter_only"}
