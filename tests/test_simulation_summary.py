"""Tests for post-simulation summary counters and output."""

from scenarios.loader import load_scenario
from vmt_engine.simulation import Simulation


def test_post_sim_summary_reports_foraging(capfd):
    """Single-agent forage scenario increments gathered counters and prints summary."""
    scenario = load_scenario("scenarios/single_agent_forage.yaml")
    sim = Simulation(scenario, seed=42)

    sim.run(max_ticks=50)

    gathered = sim._gathered_resources[0]
    assert gathered["A"] > 0 or gathered["B"] > 0

    utility_label = sim.agents[0].utility.__class__.__name__ if sim.agents[0].utility else "None"

    sim.close()

    captured_out = capfd.readouterr().out
    assert "Post-sim summary" in captured_out
    assert f"Agent 0 ({utility_label})" in captured_out
    assert "gathered" in captured_out


def test_post_sim_summary_trade_counts(capfd):
    """Trade scenario increments per-agent trade counters and prints summary."""
    scenario = load_scenario("scenarios/three_agent_barter.yaml")
    sim = Simulation(scenario, seed=42)

    sim.run(max_ticks=30)

    trade_records = list(sim.telemetry.recent_trades_for_renderer)
    assert trade_records, "Simulation should record at least one trade"

    total_trade_events = len(trade_records)
    total_trade_counts = sum(sim._trades_made.values())
    assert total_trade_counts == total_trade_events * 2
    assert any(count > 0 for count in sim._trades_made.values())

    utility_labels = {
        agent.id: (agent.utility.__class__.__name__ if agent.utility else "None")
        for agent in sim.agents
    }

    sim.close()

    captured_out = capfd.readouterr().out
    assert "Post-sim summary" in captured_out
    for agent_id, label in utility_labels.items():
        assert f"Agent {agent_id} ({label})" in captured_out


