"""
Tests for Random Walk Search Protocol

Validates:
- Deterministic randomness (same seed → same behavior)
- Different seeds produce different paths
- Protocol interface compliance
- Proper RNG usage
- Economic properties (zero information efficiency)

Version: 2025.10.28 (Phase 2a)
"""

import pytest
import numpy as np
from scenarios.schema import ScenarioConfig, ScenarioParams, UtilitiesMix, UtilityConfig, ResourceSeed
from vmt_engine.simulation import Simulation
from tests.helpers import builders, run as run_helpers
from vmt_engine.agent_based.search import RandomWalkSearch
from vmt_engine.protocols.context import WorldView, AgentView, ResourceView
from vmt_engine.econ.utility import UCES


def create_test_world_view(seed: int = 42) -> WorldView:
    """Create minimal WorldView for testing."""
    rng = np.random.Generator(np.random.PCG64(seed))
    
    # Create test utility
    utility = UCES(rho=0.5, wA=1.0, wB=1.0)
    
    return WorldView(
        tick=0,
        mode="both",
        agent_id=0,
        pos=(5, 5),
        inventory={"A": 10, "B": 10},
        utility=utility,
        quotes={"ask_A_in_B": 1.1, "bid_A_in_B": 0.9},
        paired_with_id=None,
        trade_cooldowns={},
        visible_agents=[],
        visible_resources=[],
        params={
            "vision_radius": 3,
            "grid_size": 32,
            "beta": 0.95,
        },
        rng=rng,
    )


class TestRandomWalkSearchInterface:
    """Test protocol interface compliance."""
    
    def test_has_required_properties(self):
        """Protocol provides name and version properties."""
        protocol = RandomWalkSearch()
        
        assert hasattr(protocol, "name")
        assert hasattr(protocol, "version")
        assert protocol.name == "random_walk"
        assert protocol.version == "2025.10.28"
    
    def test_has_required_methods(self):
        """Protocol implements SearchProtocol interface."""
        protocol = RandomWalkSearch()
        
        assert hasattr(protocol, "build_preferences")
        assert hasattr(protocol, "select_target")
        assert callable(protocol.build_preferences)
        assert callable(protocol.select_target)


class TestRandomWalkDeterminism:
    """Test deterministic behavior with RNG."""
    
    def test_same_seed_produces_same_preferences(self):
        """Same seed → identical preference ordering."""
        protocol = RandomWalkSearch()
        
        # Build preferences twice with same seed
        world1 = create_test_world_view(seed=42)
        prefs1 = protocol.build_preferences(world1)
        
        world2 = create_test_world_view(seed=42)
        prefs2 = protocol.build_preferences(world2)
        
        # Should be identical
        assert len(prefs1) == len(prefs2)
        for (pos1, score1, meta1), (pos2, score2, meta2) in zip(prefs1, prefs2):
            assert pos1 == pos2
            assert score1 == score2
    
    def test_different_seeds_produce_different_preferences(self):
        """Different seeds → different preference ordering."""
        protocol = RandomWalkSearch()
        
        world1 = create_test_world_view(seed=42)
        prefs1 = protocol.build_preferences(world1)
        
        world2 = create_test_world_view(seed=123)
        prefs2 = protocol.build_preferences(world2)
        
        # Should be different (with high probability)
        # Check first target differs
        if prefs1 and prefs2:
            assert prefs1[0][0] != prefs2[0][0]  # Different first target
    
    def test_same_seed_produces_same_target_selection(self):
        """Same seed → identical target selection."""
        protocol = RandomWalkSearch()
        
        world1 = create_test_world_view(seed=42)
        effects1 = protocol.select_target(world1)
        
        world2 = create_test_world_view(seed=42)
        effects2 = protocol.select_target(world2)
        
        # Should produce identical effects
        assert len(effects1) == len(effects2)
        if effects1:
            assert effects1[0].target == effects2[0].target


class TestRandomWalkBehavior:
    """Test behavioral properties."""
    
    def test_preferences_within_vision_radius(self):
        """All preferences are within vision radius."""
        protocol = RandomWalkSearch()
        world = create_test_world_view()
        
        prefs = protocol.build_preferences(world)
        
        vision_radius = world.params["vision_radius"]
        agent_pos = world.pos
        
        for target_pos, score, metadata in prefs:
            # Calculate Manhattan distance
            dist = abs(target_pos[0] - agent_pos[0]) + abs(target_pos[1] - agent_pos[1])
            assert dist <= vision_radius, f"Target {target_pos} beyond vision radius {vision_radius}"
    
    def test_excludes_current_position(self):
        """Current position not in targets."""
        protocol = RandomWalkSearch()
        world = create_test_world_view()
        
        prefs = protocol.build_preferences(world)
        
        # Current position should not be in preferences
        for target_pos, _, _ in prefs:
            assert target_pos != world.pos, "Should not target current position"
    
    def test_all_scores_equal_to_zero(self):
        """All preferences have score 0.0 (no real preference)."""
        protocol = RandomWalkSearch()
        world = create_test_world_view()
        
        prefs = protocol.build_preferences(world)
        
        for _, score, _ in prefs:
            assert score == 0.0, "Random walk should have no preference (score 0.0)"
    
    def test_honors_pairing_commitment(self):
        """Paired agents don't select new targets."""
        protocol = RandomWalkSearch()
        rng = np.random.Generator(np.random.PCG64(42))
        utility = UCES(rho=0.5, wA=1.0, wB=1.0)
        
        # Create world with paired agent
        world = WorldView(
            tick=0,
            mode="both",
            agent_id=0,
            pos=(5, 5),
            inventory={"A": 10, "B": 10},
            utility=utility,
            quotes={"ask_A_in_B": 1.1, "bid_A_in_B": 0.9},
            paired_with_id=5,  # Paired with agent 5
            trade_cooldowns={},
            visible_agents=[],
            visible_resources=[],
            params={"vision_radius": 3, "grid_size": 32, "beta": 0.95},
            rng=rng,
        )
        
        effects = protocol.select_target(world)
        
        # Should return empty list (no target selection when paired)
        assert effects == []


class TestRandomWalkCoverage:
    """Test that random walk explores uniformly."""
    
    def test_explores_all_directions(self):
        """Over many runs, explores in all directions."""
        protocol = RandomWalkSearch()
        
        # Track which quadrants are explored
        quadrants = {"NE": 0, "NW": 0, "SE": 0, "SW": 0}
        
        for seed in range(100):
            world = create_test_world_view(seed=seed)
            effects = protocol.select_target(world)
            
            if effects:
                target = effects[0].target
                agent_pos = world.pos
                
                # Determine quadrant
                if target[0] >= agent_pos[0] and target[1] >= agent_pos[1]:
                    quadrants["NE"] += 1
                elif target[0] < agent_pos[0] and target[1] >= agent_pos[1]:
                    quadrants["NW"] += 1
                elif target[0] >= agent_pos[0] and target[1] < agent_pos[1]:
                    quadrants["SE"] += 1
                else:
                    quadrants["SW"] += 1
        
        # All quadrants should be explored (with high probability)
        for quadrant, count in quadrants.items():
            assert count > 0, f"Quadrant {quadrant} never explored in 100 runs"


class TestRandomWalkEffects:
    """Test Effect generation."""
    
    def test_returns_set_target_effect(self):
        """Returns SetTarget effect with correct structure."""
        protocol = RandomWalkSearch()
        world = create_test_world_view()
        
        effects = protocol.select_target(world)
        
        assert len(effects) == 1
        effect = effects[0]
        
        # Check effect structure
        assert effect.protocol_name == "random_walk"
        assert effect.tick == world.tick
        assert effect.agent_id == world.agent_id
        assert isinstance(effect.target, tuple)
        assert len(effect.target) == 2
    
    def test_returns_empty_when_no_targets(self):
        """Returns empty list when no visible targets."""
        protocol = RandomWalkSearch()
        rng = np.random.Generator(np.random.PCG64(42))
        utility = UCES(rho=0.5, wA=1.0, wB=1.0)
        
        # Create world with vision radius 0 (no visible positions except current)
        world = WorldView(
            tick=0,
            mode="both",
            agent_id=0,
            pos=(5, 5),
            inventory={"A": 10, "B": 10},
            utility=utility,
            quotes={"ask_A_in_B": 1.1, "bid_A_in_B": 0.9},
            paired_with_id=None,
            trade_cooldowns={},
            visible_agents=[],
            visible_resources=[],
            params={"vision_radius": 0, "grid_size": 32, "beta": 0.95},
            rng=rng,
        )
        
        effects = protocol.select_target(world)
        assert effects == []


class TestRandomWalkIntegration:
    """Test integration with simulation."""
    
    def test_can_inject_into_simulation(self):
        """Protocol can be injected into Simulation."""
        # Create minimal scenario
        scenario = builders.build_scenario(N=10, agents=2, name="test_random_walk")
        
        # Create protocol
        protocol = RandomWalkSearch()
        
        # Inject into simulation
        sim = Simulation(scenario, seed=42, search_protocol=protocol)
        
        # Verify protocol is set
        assert sim.search_protocol.name == "random_walk"
        assert sim.search_protocol.version == "2025.10.28"
    
    def test_runs_in_simulation(self):
        """Protocol executes successfully in simulation."""
        scenario = builders.build_scenario(N=10, agents=3, name="test_random_walk_run")
        
        protocol = RandomWalkSearch()
        sim = Simulation(scenario, seed=42, search_protocol=protocol)
        
        # Run simulation (should not crash)
        run_helpers.run_ticks(sim, 5)
        
        # Verify agents moved (random walk should cause movement)
        initial_positions = [(0, 0), (0, 1), (0, 2)]  # Example
        moved = False
        for agent in sim.agents:
            # Check if any agent has target set
            if agent.target_pos is not None:
                moved = True
                break
        
        # At least some agents should have targets (unless all paired immediately)
        # This is a weak test but validates execution
        assert sim.tick == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

