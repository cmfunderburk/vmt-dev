"""
Tests for resource regeneration system.
"""

import pytest
from vmt_engine.core import Grid
from vmt_engine.systems.foraging import regenerate_resources


def test_resource_regeneration_requires_cooldown():
    """Test that regeneration doesn't start until cooldown period completes after last harvest."""
    grid = Grid(5)
    grid.set_resource(0, 0, "A", 3)  # Sets original_amount = 3
    cell = grid.get_cell(0, 0)
    
    # Simulate harvest at tick 10 (reduces to 2)
    cell.resource.amount = 2
    cell.resource.last_harvested_tick = 10
    
    # Try to regenerate before cooldown (5 ticks)
    regenerate_resources(grid, growth_rate=1, max_amount=5, cooldown_ticks=5, current_tick=12)
    assert cell.resource.amount == 2, "Should not regenerate before cooldown (2 ticks < 5)"
    
    regenerate_resources(grid, growth_rate=1, max_amount=5, cooldown_ticks=5, current_tick=14)
    assert cell.resource.amount == 2, "Should not regenerate before cooldown (4 ticks < 5)"
    
    # After cooldown completes (5 ticks since last harvest)
    regenerate_resources(grid, growth_rate=1, max_amount=5, cooldown_ticks=5, current_tick=15)
    assert cell.resource.amount == 3, "Should regenerate after cooldown (5 ticks >= 5)"


def test_resource_regeneration_continues_after_cooldown():
    """Test that once regeneration starts, it continues growing to original amount."""
    grid = Grid(5)
    grid.set_resource(0, 0, "A", 3)  # Original amount = 3
    cell = grid.get_cell(0, 0)
    
    # Simulate harvest to 0 at tick 10
    cell.resource.amount = 0
    cell.resource.last_harvested_tick = 10
    
    # After cooldown, regenerate
    regenerate_resources(grid, growth_rate=1, max_amount=5, cooldown_ticks=5, current_tick=15)
    assert cell.resource.amount == 1
    
    # Continue regenerating (no new harvests, so cooldown stays satisfied)
    regenerate_resources(grid, growth_rate=1, max_amount=5, cooldown_ticks=5, current_tick=16)
    assert cell.resource.amount == 2
    
    regenerate_resources(grid, growth_rate=1, max_amount=5, cooldown_ticks=5, current_tick=17)
    assert cell.resource.amount == 3, "Should reach original amount"


def test_resource_regeneration_capped():
    """Test that regeneration stops at original_amount."""
    grid = Grid(5)
    grid.set_resource(0, 0, "A", 3)  # Original amount = 3
    cell = grid.get_cell(0, 0)
    
    # Simulate harvest to 0 at tick 0
    cell.resource.amount = 0
    cell.resource.last_harvested_tick = 0
    
    # After cooldown, regenerate
    regenerate_resources(grid, growth_rate=2, max_amount=5, cooldown_ticks=5, current_tick=5)
    assert cell.resource.amount == 2, "Should regenerate 2 units"
    
    regenerate_resources(grid, growth_rate=2, max_amount=5, cooldown_ticks=5, current_tick=6)
    assert cell.resource.amount == 3, "Should cap at original amount (3), not max_amount (5)"
    
    # Try to regenerate more - should not grow beyond original
    regenerate_resources(grid, growth_rate=2, max_amount=5, cooldown_ticks=5, current_tick=7)
    assert cell.resource.amount == 3, "Should not exceed original_amount"


def test_resource_regeneration_disabled():
    """Test that growth_rate=0 disables regeneration."""
    grid = Grid(5)
    grid.set_resource(0, 0, "A", 3)
    cell = grid.get_cell(0, 0)
    
    cell.resource.amount = 0
    cell.resource.last_harvested_tick = 0
    
    regenerate_resources(grid, growth_rate=0, max_amount=5, cooldown_ticks=5, current_tick=10)
    assert cell.resource.amount == 0, "growth_rate=0 should disable regeneration"


def test_resource_regeneration_only_existing_types():
    """Test that only cells with resource type regenerate."""
    grid = Grid(5)
    grid.set_resource(0, 0, "A", 3)
    cell_00 = grid.get_cell(0, 0)
    
    # Simulate harvest to 0
    cell_00.resource.amount = 0
    cell_00.resource.last_harvested_tick = 0
    
    # Cell (1, 1) has no resource type set
    
    regenerate_resources(grid, growth_rate=1, max_amount=5, cooldown_ticks=5, current_tick=10)
    
    assert cell_00.resource.amount == 1, "Should regenerate existing type"
    assert grid.get_cell(1, 1).resource.amount == 0, "Should not create new resources"
    assert grid.get_cell(1, 1).resource.type is None, "Should not create new types"


def test_resource_never_depleted_does_not_regenerate():
    """Test that resources that were never depleted do NOT regenerate."""
    grid = Grid(5)
    grid.set_resource(0, 0, "A", 2)
    cell = grid.get_cell(0, 0)
    # depleted_at_tick is None because it was never depleted
    
    # Should NOT regenerate (never went through depletion cycle)
    regenerate_resources(grid, growth_rate=1, max_amount=5, cooldown_ticks=5, current_tick=100)
    assert cell.resource.amount == 2, "Should stay at original amount (never depleted)"
    
    regenerate_resources(grid, growth_rate=1, max_amount=5, cooldown_ticks=5, current_tick=101)
    assert cell.resource.amount == 2, "Should still not regenerate"


def test_resource_depleted_and_harvested_again():
    """Test that resources can be harvested multiple times with cooldown each time."""
    grid = Grid(5)
    grid.set_resource(0, 0, "A", 3)  # Original amount = 3
    cell = grid.get_cell(0, 0)
    
    # First harvest cycle: deplete to 0
    cell.resource.amount = 0
    cell.resource.last_harvested_tick = 0
    
    # Regenerate after cooldown
    regenerate_resources(grid, growth_rate=2, max_amount=5, cooldown_ticks=5, current_tick=5)
    assert cell.resource.amount == 2
    
    # Grow to original
    regenerate_resources(grid, growth_rate=2, max_amount=5, cooldown_ticks=5, current_tick=6)
    assert cell.resource.amount == 3, "Should reach original amount"
    
    # Second harvest cycle: harvest again at tick 10
    cell.resource.amount = 0
    cell.resource.last_harvested_tick = 10
    
    # Should need another cooldown
    regenerate_resources(grid, growth_rate=2, max_amount=5, cooldown_ticks=5, current_tick=14)
    assert cell.resource.amount == 0, "Still in cooldown (4 ticks < 5)"
    
    regenerate_resources(grid, growth_rate=2, max_amount=5, cooldown_ticks=5, current_tick=15)
    assert cell.resource.amount == 2, "Cooldown complete, should regenerate"


def test_harvest_during_regeneration_resets_cooldown():
    """Test that harvesting during regeneration resets the cooldown timer."""
    grid = Grid(5)
    grid.set_resource(0, 0, "A", 5)  # Original = 5
    cell = grid.get_cell(0, 0)
    
    # Harvest to 2 at tick 0
    cell.resource.amount = 2
    cell.resource.last_harvested_tick = 0
    
    # After cooldown, start regenerating
    regenerate_resources(grid, growth_rate=1, max_amount=5, cooldown_ticks=5, current_tick=5)
    assert cell.resource.amount == 3, "Should regenerate from 2 to 3"
    
    # Continue regenerating
    regenerate_resources(grid, growth_rate=1, max_amount=5, cooldown_ticks=5, current_tick=6)
    assert cell.resource.amount == 4, "Should grow to 4"
    
    # Now harvest again at tick 7 (simulating agent returning)
    cell.resource.amount = 3  # Harvested 1
    cell.resource.last_harvested_tick = 7
    
    # Try to regenerate immediately - should NOT work (cooldown reset)
    regenerate_resources(grid, growth_rate=1, max_amount=5, cooldown_ticks=5, current_tick=8)
    assert cell.resource.amount == 3, "Should not regenerate (only 1 tick since harvest)"
    
    # Wait full cooldown from new harvest
    regenerate_resources(grid, growth_rate=1, max_amount=5, cooldown_ticks=5, current_tick=12)
    assert cell.resource.amount == 4, "Should regenerate after new cooldown (5 ticks since tick 7)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

