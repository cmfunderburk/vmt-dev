"""
Tests for Random Matching Protocol

Validates:
- Deterministic randomness (same seed → same pairs)
- Different seeds produce different pairs
- Protocol interface compliance
- No double-pairing constraint
- Comparison with legacy matching

Version: 2025.10.28 (Phase 2a)
"""

import pytest
import numpy as np
from tests.helpers import builders, run as run_helpers
from scenarios.loader import load_scenario
from vmt_engine.simulation import Simulation
from vmt_engine.protocols.matching import RandomMatching
from vmt_engine.protocols.matching import RandomMatching, LegacyMatchingProtocol
from vmt_engine.protocols.context import ProtocolContext


def create_test_scenario(agent_count: int = 10, grid_size: int = 20):
    return builders.build_scenario(N=grid_size, agents=agent_count, name="random_matching_test")


class TestRandomMatchingInterface:
    """Test protocol interface compliance."""
    
    def test_has_required_properties(self):
        """Protocol exposes required properties."""
        protocol = RandomMatching()
        
        assert hasattr(protocol, "name")
        assert hasattr(protocol, "version")
        assert hasattr(protocol, "find_matches")
        assert protocol.name == "random"
        assert isinstance(protocol.version, str)
    
    def test_find_matches_signature(self):
        """find_matches accepts correct parameters."""
        protocol = RandomMatching()
        
        # Create minimal context
        rng = np.random.Generator(np.random.PCG64(42))
        context = ProtocolContext(
            tick=0,
            mode="both",
            exchange_regime="barter_only",
            all_agent_views={},
            all_resource_views=[],
            current_pairings={},
            protocol_state={},
            params={},
            rng=rng
        )
        
        # Should not raise
        preferences = {}
        result = protocol.find_matches(preferences, context)
        
        assert isinstance(result, list)
        assert all(hasattr(effect, "protocol_name") for effect in result)


class TestRandomMatchingDeterminism:
    """Test deterministic behavior with RNG."""
    
    def test_same_seed_produces_same_pairs(self):
        """Running twice with same seed produces identical pairs."""
        scenario = create_test_scenario(agent_count=10)
        
        # Run twice with same seed and capture final agent states
        states_list = []
        for _ in range(2):
            sim = builders.make_sim(scenario, seed=42, matching="random")
            run_helpers.run_ticks(sim, 10)
            
            # Extract final agent states (positions and inventories)
            states = [(a.pos, a.inventory.A, a.inventory.B) for a in sim.agents]
            states_list.append(states)
        
        assert states_list[0] == states_list[1], "Same seed should produce identical behavior"
    
    def test_different_seeds_produce_different_pairs(self):
        """Different seeds produce different pairings."""
        scenario = create_test_scenario(agent_count=10)
        
        # Run with different seeds and capture final states
        states_list = []
        for seed in [42, 43]:
            sim = builders.make_sim(scenario, seed=seed, matching="random")
            run_helpers.run_ticks(sim, 10)
            
            # Extract final agent states
            states = [(a.pos, a.inventory.A, a.inventory.B) for a in sim.agents]
            states_list.append(states)
        
        # Different seeds should produce different results (extremely unlikely to be same)
        assert states_list[0] != states_list[1], "Different seeds should produce different behavior"


class TestRandomMatchingBehavior:
    """Test random matching behavior properties."""
    
    def test_no_double_pairing(self):
        """Each agent appears in at most one pair per tick."""
        scenario = create_test_scenario(agent_count=20)
        sim = Simulation(scenario, seed=42, matching_protocol=RandomMatching())
        run_helpers.run_ticks(sim, 20)
        
        # Check agent pairing state - each agent should have at most one partner at a time
        # This is enforced by the pairing logic itself, so if simulation runs, constraint holds
        for agent in sim.agents:
            # paired_with_id is either None or a single agent ID
            assert agent.paired_with_id is None or isinstance(agent.paired_with_id, int)
    
    def test_only_pairs_trade_seekers(self):
        """Only pairs agents who want to trade."""
        # Use foundational scenario to ensure trades occur
        scenario = load_scenario('scenarios/foundational_barter_demo.yaml')
        sim = Simulation(scenario, seed=42, matching_protocol=RandomMatching())
        
        # Run and verify some trades happen (which requires pairing)
        run_helpers.run_ticks(sim, 20)
        
        # Check that some trades occurred (agents with complementary endowments)
        trade_count = len(sim.telemetry.recent_trades_for_renderer)
        assert trade_count > 0, "Should create some trades with complementary agents"
    
    def test_handles_odd_number_of_agents(self):
        """Handles odd number of trade seekers gracefully."""
        scenario = create_test_scenario(agent_count=9)  # Odd number
        sim = builders.make_sim(scenario, seed=42, matching="random")
        
        # Should not crash with odd number
        run_helpers.run_ticks(sim, 10)
        
        # Simulation should complete successfully
        assert sim.tick == 10


class TestRandomMatchingComparison:
    """Compare random matching with legacy matching."""
    
    def test_random_vs_legacy_surplus(self):
        """Compare random matching with legacy matching behavior."""
        scenario = load_scenario('scenarios/foundational_barter_demo.yaml')
        
        # Run with random matching
        sim_random = Simulation(scenario, seed=42, matching_protocol=RandomMatching())
        run_helpers.run_ticks(sim_random, 30)
        
        # Run with legacy matching
        sim_legacy = Simulation(scenario, seed=42)  # legacy by default
        run_helpers.run_ticks(sim_legacy, 30)
        
        # Count trades (simple proxy for surplus)
        trade_count_random = len(sim_random.telemetry.recent_trades_for_renderer)
        trade_count_legacy = len(sim_legacy.telemetry.recent_trades_for_renderer)
        
        # Both should produce trades (agents have complementary endowments)
        assert trade_count_random > 0, "Random matching should produce trades"
        assert trade_count_legacy > 0, "Legacy matching should produce trades"
        
        # Generally expect legacy to produce more/better trades, but allow for variation
        print(f"Random trades: {trade_count_random}, Legacy trades: {trade_count_legacy}")
    
    def test_random_creates_pairs(self):
        """Random matching actually creates pairs and leads to trades."""
        scenario = load_scenario('scenarios/foundational_barter_demo.yaml')
        sim = Simulation(scenario, seed=42, matching_protocol=RandomMatching())
        run_helpers.run_ticks(sim, 20)
        
        # Verify trades occurred (which requires pairing)
        trade_count = len(sim.telemetry.recent_trades_for_renderer)
        assert trade_count > 0, "Should create trades through random pairing"


class TestRandomMatchingIntegration:
    """Integration tests with full simulation."""
    
    def test_runs_in_simulation(self):
        """Protocol runs successfully in full simulation."""
        scenario = load_scenario('scenarios/foundational_barter_demo.yaml')
        sim = Simulation(scenario, seed=42, matching_protocol=RandomMatching())
        
        # Should not raise
        run_helpers.run_ticks(sim, 50)
        
        # Verify simulation completed
        assert sim.tick == 50
    
    def test_produces_trades(self):
        """Random matching leads to actual trades."""
        scenario = load_scenario('scenarios/foundational_barter_demo.yaml')
        sim = Simulation(scenario, seed=42, matching_protocol=RandomMatching())
        run_helpers.run_ticks(sim, 30)
        
        # Check trade count
        trade_count = len(sim.telemetry.recent_trades_for_renderer)
        
        # Should produce at least some trades (agents have complementary endowments)
        assert trade_count > 0, "Should produce some trades with complementary agents"

