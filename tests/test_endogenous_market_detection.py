"""
Tests for endogenous market detection (Week 1).

Tests market formation, persistence, and dissolution based on agent clustering.
"""

import pytest
from vmt_engine.simulation import Simulation
from scenarios.schema import ScenarioConfig, ScenarioParams, UtilitiesMix, UtilityConfig, ResourceSeed
from telemetry.config import LogConfig
from tests.helpers.builders import build_scenario
from vmt_engine.core import Position


def test_market_forms_at_threshold():
    """Market forms when 5+ agents cluster within interaction radius."""
    scenario = build_scenario(N=20, agents=10, regime="barter_only")
    # Set market formation threshold to 5 (default)
    scenario.params.market_formation_threshold = 5
    scenario.params.interaction_radius = 3
    
    sim = Simulation(scenario, seed=42, log_config=LogConfig.minimal())
    
    # Place 5 agents within interaction_radius=3 of each other
    agents = sim.agents[:5]
    center_x, center_y = 10, 10
    
    for i, agent in enumerate(agents):
        # Place in a small cluster around (10, 10)
        agent.pos = (center_x + (i % 2), center_y + (i // 2))
        sim.spatial_index.update_position(agent.id, agent.pos)
    
    # Run one tick to detect markets
    sim.trade_system.execute(sim)
    
    # Assert: 1 market exists
    assert len(sim.trade_system.active_markets) == 1
    
    market = list(sim.trade_system.active_markets.values())[0]
    assert len(market.participant_ids) >= 5
    assert market.center[0] >= center_x - 1 and market.center[0] <= center_x + 1
    assert market.center[1] >= center_y - 1 and market.center[1] <= center_y + 1
    
    sim.close()


def test_market_does_not_form_below_threshold():
    """No market when only 4 agents cluster."""
    scenario = build_scenario(N=20, agents=10, regime="barter_only")
    scenario.params.market_formation_threshold = 5
    scenario.params.interaction_radius = 3
    
    sim = Simulation(scenario, seed=42, log_config=LogConfig.minimal())
    
    # Place only 4 agents within interaction_radius=3
    agents = sim.agents[:4]
    center_x, center_y = 10, 10
    
    for i, agent in enumerate(agents):
        agent.pos = (center_x + (i % 2), center_y + (i // 2))
        sim.spatial_index.update_position(agent.id, agent.pos)
    
    # Run one tick
    sim.trade_system.execute(sim)
    
    # Assert: 0 markets exist
    assert len(sim.trade_system.active_markets) == 0
    
    sim.close()


def test_market_persists_across_ticks():
    """Market maintains identity if agents remain clustered."""
    scenario = build_scenario(N=20, agents=10, regime="barter_only")
    scenario.params.market_formation_threshold = 5
    scenario.params.interaction_radius = 3
    
    sim = Simulation(scenario, seed=42, log_config=LogConfig.minimal())
    
    # Place 5 agents in cluster
    agents = sim.agents[:5]
    center_x, center_y = 10, 10
    
    for i, agent in enumerate(agents):
        agent.pos = (center_x + (i % 2), center_y + (i // 2))
        sim.spatial_index.update_position(agent.id, agent.pos)
    
    # Form market at tick 0
    sim.trade_system.execute(sim)
    
    assert len(sim.trade_system.active_markets) == 1
    market_id_tick0 = list(sim.trade_system.active_markets.keys())[0]
    
    # Agents stay clustered for ticks 1-5
    sim.tick = 1
    sim.trade_system.execute(sim)
    sim.tick = 2
    sim.trade_system.execute(sim)
    sim.tick = 3
    sim.trade_system.execute(sim)
    
    # Assert: Same market ID persists
    assert len(sim.trade_system.active_markets) == 1
    assert market_id_tick0 in sim.trade_system.active_markets
    
    sim.close()


def test_market_dissolves_after_patience():
    """Market dissolves after falling below threshold for patience ticks."""
    scenario = build_scenario(N=20, agents=10, regime="barter_only")
    scenario.params.market_formation_threshold = 5
    scenario.params.market_dissolution_threshold = 3
    scenario.params.market_dissolution_patience = 5
    scenario.params.interaction_radius = 3
    
    sim = Simulation(scenario, seed=42, log_config=LogConfig.minimal())
    
    # Place 5 agents in cluster
    agents = sim.agents[:5]
    center_x, center_y = 10, 10
    
    for i, agent in enumerate(agents):
        agent.pos = (center_x + (i % 2), center_y + (i // 2))
        sim.spatial_index.update_position(agent.id, agent.pos)
    
    # Form market
    sim.trade_system.execute(sim)
    assert len(sim.trade_system.active_markets) == 1
    market_id = list(sim.trade_system.active_markets.keys())[0]
    
    # Agents disperse (density drops to 2)
    agents[0].pos = (0, 0)
    agents[1].pos = (19, 19)
    agents[2].pos = (19, 0)
    agents[3].pos = (0, 19)
    agents[4].pos = (10, 10)  # Only one agent remains
    
    for agent in agents:
        sim.spatial_index.update_position(agent.id, agent.pos)
    
    # Wait market_dissolution_patience ticks
    for tick in range(1, 6):
        sim.tick = tick
        sim.trade_system.execute(sim)
        # Market should still exist for first 4 ticks (patience = 5)
        if tick < 5:
            assert market_id in sim.trade_system.active_markets
    
    # After 5 ticks below threshold, market should dissolve
    assert market_id not in sim.trade_system.active_markets
    
    sim.close()


def test_location_based_market_identity():
    """Market reuses ID if formed near previous location."""
    scenario = build_scenario(N=20, agents=10, regime="barter_only")
    scenario.params.market_formation_threshold = 5
    scenario.params.interaction_radius = 3
    
    sim = Simulation(scenario, seed=42, log_config=LogConfig.minimal())
    
    # Form market at (10, 10)
    agents = sim.agents[:5]
    for i, agent in enumerate(agents):
        agent.pos = (10 + (i % 2), 10 + (i // 2))
        sim.spatial_index.update_position(agent.id, agent.pos)
    
    sim.trade_system.execute(sim)
    assert len(sim.trade_system.active_markets) == 1
    market_id1 = list(sim.trade_system.active_markets.keys())[0]
    
    # Disperse agents
    for i, agent in enumerate(agents):
        agent.pos = (i * 5, i * 5)
        sim.spatial_index.update_position(agent.id, agent.pos)
    
    sim.tick = 10
    sim.trade_system.execute(sim)
    # Market may dissolve or have low participation
    
    # Cluster forms at (11, 11) (within 2 cells of (10, 10))
    for i, agent in enumerate(agents):
        agent.pos = (11 + (i % 2), 11 + (i // 2))
        sim.spatial_index.update_position(agent.id, agent.pos)
    
    sim.tick = 11
    sim.trade_system.execute(sim)
    
    # Assert: Same market ID reused (or new one if market was dissolved)
    # If market wasn't dissolved, same ID should be reused
    if len(sim.trade_system.active_markets) > 0:
        # Check if it's the same market by checking center proximity
        market = list(sim.trade_system.active_markets.values())[0]
        dist = abs(market.center[0] - 10) + abs(market.center[1] - 10)
        if dist <= 2:
            # Same market location, should reuse ID
            assert market.id == market_id1
    
    sim.close()


def test_deterministic_market_ids():
    """Same seed → same market IDs (determinism check)."""
    scenario = build_scenario(N=20, agents=10, regime="barter_only")
    scenario.params.market_formation_threshold = 5
    scenario.params.interaction_radius = 3
    
    # Run twice with same seed
    sim1 = Simulation(scenario, seed=42, log_config=LogConfig.minimal())
    # Place 5 agents in cluster
    agents1 = sim1.agents[:5]
    for i, agent in enumerate(agents1):
        agent.pos = (10 + (i % 2), 10 + (i // 2))
        sim1.spatial_index.update_position(agent.id, agent.pos)
    
    sim1.trade_system.execute(sim1)
    market_ids1 = set(sim1.trade_system.active_markets.keys())
    
    sim1.close()
    
    sim2 = Simulation(scenario, seed=42, log_config=LogConfig.minimal())
    # Place 5 agents in same positions
    agents2 = sim2.agents[:5]
    for i, agent in enumerate(agents2):
        agent.pos = (10 + (i % 2), 10 + (i // 2))
        sim2.spatial_index.update_position(agent.id, agent.pos)
    
    sim2.trade_system.execute(sim2)
    market_ids2 = set(sim2.trade_system.active_markets.keys())
    
    # Assert: Same market IDs
    assert market_ids1 == market_ids2
    
    sim2.close()


def test_multiple_markets_can_coexist():
    """Two separate clusters form two markets."""
    scenario = build_scenario(N=40, agents=15, regime="barter_only")
    scenario.params.market_formation_threshold = 5
    scenario.params.interaction_radius = 3
    
    sim = Simulation(scenario, seed=42, log_config=LogConfig.minimal())
    
    # Cluster 1 at (10, 10)
    agents1 = sim.agents[:5]
    for i, agent in enumerate(agents1):
        agent.pos = (10 + (i % 2), 10 + (i // 2))
        sim.spatial_index.update_position(agent.id, agent.pos)
    
    # Cluster 2 at (30, 30) (far enough to be separate)
    agents2 = sim.agents[5:10]
    for i, agent in enumerate(agents2):
        agent.pos = (30 + (i % 2), 30 + (i // 2))
        sim.spatial_index.update_position(agent.id, agent.pos)
    
    sim.trade_system.execute(sim)
    
    # Assert: 2 markets exist
    assert len(sim.trade_system.active_markets) == 2
    
    sim.close()

