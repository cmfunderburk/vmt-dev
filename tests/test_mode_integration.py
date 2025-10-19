import pytest
from vmt_engine.simulation import Simulation
from scenarios.loader import load_scenario
from scenarios.schema import ScenarioConfig, ScenarioParams, ModeSchedule, UtilitiesMix, UtilityConfig, ResourceSeed
from telemetry.config import LogConfig


def create_mode_test_scenario(forage_ticks=10, trade_ticks=5):
    """Helper to create a test scenario with mode schedule."""
    return ScenarioConfig(
        schema_version=1,
        name="Mode Test",
        N=10,
        agents=3,
        initial_inventories={'A': 5, 'B': 5},
        utilities=UtilitiesMix(mix=[
            UtilityConfig(type="ces", weight=1.0, params={"rho": 0.5, "wA": 0.5, "wB": 0.5})
        ]),
        params=ScenarioParams(
            vision_radius=5, interaction_radius=1, move_budget_per_tick=1,
            dA_max=3, forage_rate=1, resource_growth_rate=1
        ),
        resource_seed=ResourceSeed(density=0.2, amount=3),
        mode_schedule=ModeSchedule(
            type="global_cycle", forage_ticks=forage_ticks, 
            trade_ticks=trade_ticks, start_mode="forage"
        )
    )


def test_mode_transitions_logged(tmp_path):
    """Test that mode changes are properly logged to telemetry."""
    scenario = create_mode_test_scenario(forage_ticks=5, trade_ticks=3)
    log_config = LogConfig.standard()
    log_config.db_path = str(tmp_path / "test.db")
    
    sim = Simulation(scenario, seed=42, log_config=log_config)
    sim.run(max_ticks=20)
    
    # Query mode_changes table
    cursor = sim.telemetry.db.execute("""
        SELECT tick, old_mode, new_mode FROM mode_changes 
        WHERE run_id = ? ORDER BY tick
    """, (sim.telemetry.run_id,))
    transitions = cursor.fetchall()
    
    assert len(transitions) >= 2  # At least 2 transitions in 20 ticks
    assert transitions[0]['tick'] == 5  # First transition at tick 5
    assert transitions[0]['new_mode'] == "trade"
    
    sim.close()


def test_forage_system_skips_in_trade_mode():
    """Test that ForageSystem skips execution in trade mode."""
    scenario = create_mode_test_scenario(forage_ticks=5, trade_ticks=5)
    sim = Simulation(scenario, seed=42, log_config=LogConfig.minimal())
    
    # Run to tick 5 (start of trade mode) - need to step through ticks 0-4, then one more to execute at tick 5
    for _ in range(6):
        sim.step()
    
    assert sim.current_mode == "trade"
    
    # Place agent on resource cell
    agent = sim.agents[0]
    for pos, cell in sim.grid.cells.items():
        if cell.resource.amount > 0:
            agent.pos = pos
            break
    
    initial_inventory = agent.inventory.A + agent.inventory.B
    sim.step()  # Should not forage
    final_inventory = agent.inventory.A + agent.inventory.B
    
    assert final_inventory == initial_inventory  # No foraging occurred
    sim.close()


def test_trade_system_skips_in_forage_mode():
    """Test that TradeSystem skips execution in forage mode."""
    scenario = create_mode_test_scenario(forage_ticks=5, trade_ticks=5)
    sim = Simulation(scenario, seed=42, log_config=LogConfig.minimal())
    
    # Ensure we're in forage mode
    assert sim.current_mode == "forage"
    
    # Place two agents adjacent
    sim.agents[0].pos = (0, 0)
    sim.agents[1].pos = (0, 1)
    sim.spatial_index.update_position(sim.agents[0].id, (0, 0))
    sim.spatial_index.update_position(sim.agents[1].id, (0, 1))
    
    # Set up favorable trade conditions
    sim.agents[0].inventory.A = 10
    sim.agents[0].inventory.B = 1
    sim.agents[1].inventory.A = 1
    sim.agents[1].inventory.B = 10
    
    initial_A_0 = sim.agents[0].inventory.A
    sim.step()
    final_A_0 = sim.agents[0].inventory.A
    
    assert final_A_0 == initial_A_0  # No trade occurred
    sim.close()


def test_resource_regeneration_in_all_modes():
    """Test that resources regenerate during all modes."""
    scenario = create_mode_test_scenario(forage_ticks=5, trade_ticks=5)
    scenario.params.resource_growth_rate = 1
    scenario.params.resource_regen_cooldown = 0
    
    sim = Simulation(scenario, seed=42, log_config=LogConfig.minimal())
    
    # Deplete a resource cell
    resource_cell = None
    for pos, cell in sim.grid.cells.items():
        if cell.resource.amount > 0:
            original_amount = cell.resource.amount
            cell.resource.amount = 0
            cell.resource.last_harvested_tick = 0
            sim.grid.harvested_cells.add(pos)
            resource_cell = cell
            break
    
    # Run through trade mode
    for _ in range(6):
        sim.step()
    
    assert sim.current_mode == "trade"
    assert resource_cell.resource.amount > 0  # Regenerated during trade mode
    sim.close()


def test_full_cycle_integration():
    """Test simulation through multiple complete forage→trade cycles."""
    scenario = create_mode_test_scenario(forage_ticks=10, trade_ticks=5)
    sim = Simulation(scenario, seed=42, log_config=LogConfig.minimal())
    
    modes_seen = []
    for i in range(35):
        sim.step()
        modes_seen.append(sim.current_mode)  # Capture after step so mode reflects what was executed
    
    # Verify cycle pattern
    # After stepping through ticks 0-9 (forage), we execute at those ticks in forage mode
    # After stepping through ticks 10-14 (trade), we execute at those ticks in trade mode
    assert modes_seen[:10] == ["forage"] * 10
    assert modes_seen[10:15] == ["trade"] * 5
    assert modes_seen[15:25] == ["forage"] * 10
    assert modes_seen[25:30] == ["trade"] * 5
    assert modes_seen[30:35] == ["forage"] * 5
    
    sim.close()

