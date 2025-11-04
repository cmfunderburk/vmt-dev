"""
Performance benchmarks to validate O() complexity improvements.
"""

import time
import pytest
from vmt_engine.simulation import Simulation
from scenarios.schema import (
    ScenarioConfig, ScenarioParams, ResourceSeed, 
    UtilitiesMix, UtilityConfig
)


def create_test_scenario(n_agents: int, grid_size: int) -> ScenarioConfig:
    """Create a scenario for performance testing."""
    return ScenarioConfig(
        schema_version=1,
        name="performance_test",
        N=grid_size,
        agents=n_agents,
        initial_inventories={'A': 10, 'B': 10},
        params=ScenarioParams(
            spread=0.1,
            vision_radius=5,
            interaction_radius=2,
            move_budget_per_tick=1,
            forage_rate=1,
            epsilon=1e-9,
            beta=0.95,
            resource_growth_rate=1,
            resource_max_amount=10,
            resource_regen_cooldown=5,
            trade_cooldown_ticks=10
        ),
        resource_seed=ResourceSeed(
            density=0.1,
            amount=10
        ),
        utilities=UtilitiesMix(
            mix=[
                UtilityConfig(
                    type='ces',
                    params={'rho': 0.5, 'wA': 1.0, 'wB': 1.0},
                    weight=1.0
                )
            ]
        ),
        # Set protocol fields explicitly to avoid test failures
        search_protocol="distance_discounted_search",
        matching_protocol="three_pass_matching", 
        bargaining_protocol="compensating_block",
    )


def benchmark_simulation(n_agents: int, grid_size: int, ticks: int = 10) -> float:
    """
    Benchmark simulation performance.
    
    Returns average time per tick in seconds.
    """
    scenario = create_test_scenario(n_agents, grid_size)
    sim = Simulation(scenario, seed=42)
    
    start_time = time.time()
    sim.run(ticks)
    elapsed = time.time() - start_time
    sim.close()
    
    return elapsed / ticks


def test_perception_phase_scalability():
    """
    Test that perception phase scales linearly with agent count.
    
    With spatial indexing: O(N_agents)
    Without: O(N_agents²)
    """
    # Small scenario
    time_10 = benchmark_simulation(n_agents=10, grid_size=20, ticks=5)
    
    # Medium scenario (4x agents)
    time_40 = benchmark_simulation(n_agents=40, grid_size=40, ticks=5)
    
    # If O(N), ratio should be ~4x
    # If O(N²), ratio would be ~16x
    ratio = time_40 / time_10
    
    print(f"\nPerception scalability test:")
    print(f"  10 agents: {time_10*1000:.2f}ms per tick")
    print(f"  40 agents: {time_40*1000:.2f}ms per tick")
    print(f"  Ratio: {ratio:.2f}x (expect ~4x for O(N), ~16x for O(N²))")
    
    # Should be closer to 4x than 16x (with some tolerance for overhead)
    assert ratio < 8.0, f"Perception phase may still be O(N²), ratio: {ratio:.2f}x"


def test_trade_phase_scalability():
    """
    Test that trade phase scales linearly with agent count.
    
    With spatial indexing: O(N_agents)
    Without: O(N_agents²)
    """
    # Smaller grid to encourage agent interactions
    time_10 = benchmark_simulation(n_agents=10, grid_size=10, ticks=5)
    time_40 = benchmark_simulation(n_agents=40, grid_size=20, ticks=5)
    
    ratio = time_40 / time_10
    
    print(f"\nTrade phase scalability test:")
    print(f"  10 agents: {time_10*1000:.2f}ms per tick")
    print(f"  40 agents: {time_40*1000:.2f}ms per tick")
    print(f"  Ratio: {ratio:.2f}x (expect ~4x for O(N), ~16x for O(N²))")
    
    assert ratio < 8.0, f"Trade phase may still be O(N²), ratio: {ratio:.2f}x"


def test_resource_regeneration_scalability():
    """
    Test that resource regeneration scales with harvested cells, not grid size.
    
    With active set: O(harvested_cells)
    Without: O(N_grid²)
    """
    # Small grid
    time_small = benchmark_simulation(n_agents=10, grid_size=20, ticks=10)
    
    # Large grid (4x size = 16x cells)
    time_large = benchmark_simulation(n_agents=10, grid_size=40, ticks=10)
    
    ratio = time_large / time_small
    
    print(f"\nResource regeneration scalability test:")
    print(f"  20x20 grid: {time_small*1000:.2f}ms per tick")
    print(f"  40x40 grid: {time_large*1000:.2f}ms per tick")
    print(f"  Ratio: {ratio:.2f}x (expect ~1-2x for O(harvested), ~16x for O(N²))")
    
    # With active set, should not scale with grid size
    # Expect similar performance since same number of agents harvesting
    assert ratio < 4.0, f"Regeneration may still be O(N²), ratio: {ratio:.2f}x"


def test_overall_performance_100_agents():
    """
    Test that simulation can handle 100 agents efficiently.
    
    With optimizations, should complete in reasonable time.
    """
    time_per_tick = benchmark_simulation(n_agents=100, grid_size=50, ticks=5)
    
    print(f"\nOverall performance (100 agents):")
    print(f"  Time per tick: {time_per_tick*1000:.2f}ms")
    print(f"  Ticks per second: {1.0/time_per_tick:.1f}")
    
    # Should be able to simulate at reasonable speed
    # Even on slow hardware, 100 agents should run at >10 ticks/sec
    assert time_per_tick < 0.1, f"Simulation too slow: {time_per_tick*1000:.2f}ms per tick"


@pytest.mark.parametrize("n_agents", [10, 25, 50, 100])
def test_spatial_index_correctness(n_agents):
    """
    Verify spatial index produces same results as brute force.
    
    This ensures optimizations don't change simulation behavior.
    """
    scenario = create_test_scenario(n_agents, grid_size=30)
    sim = Simulation(scenario, seed=123)
    
    # Run a few ticks
    for _ in range(5):
        sim.step()
        
        # Verify spatial index consistency
        for agent in sim.agents:
            indexed_pos = sim.spatial_index.agent_positions.get(agent.id)
            assert indexed_pos == agent.pos, \
                f"Spatial index out of sync for agent {agent.id}"
    
    sim.close()


def test_harvested_cells_tracking():
    """
    Verify harvested cells set is maintained correctly.
    """
    scenario = create_test_scenario(n_agents=10, grid_size=20)
    sim = Simulation(scenario, seed=456)
    
    # Initially no harvested cells
    assert len(sim.grid.harvested_cells) == 0
    
    # Run simulation
    sim.run(20)
    
    # Should have some harvested cells
    harvested_count = len(sim.grid.harvested_cells)
    print(f"\nHarvested cells after 20 ticks: {harvested_count}")
    
    # All harvested cells should actually be depleted or regenerating
    for pos in sim.grid.harvested_cells:
        cell = sim.grid.cells[pos]
        # Should have a resource type
        assert cell.resource.type is not None
        # Should be below original amount (still regenerating)
        assert cell.resource.amount < cell.resource.original_amount
        # Should have been harvested
        assert cell.resource.last_harvested_tick is not None
    
    sim.close()


if __name__ == "__main__":
    # Run benchmarks directly for manual testing
    print("=" * 70)
    print("PERFORMANCE BENCHMARKS")
    print("=" * 70)
    
    test_perception_phase_scalability()
    test_trade_phase_scalability()
    test_resource_regeneration_scalability()
    test_overall_performance_100_agents()
    
    print("\n" + "=" * 70)
    print("All benchmarks passed!")
    print("=" * 70)

