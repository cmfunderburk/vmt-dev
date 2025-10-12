"""
Tests for core state structures.
"""

import pytest
from vmt_engine.core import Grid, Agent, Inventory, Position


def test_grid_initialization():
    """Test grid initialization."""
    grid = Grid(8)
    
    assert grid.N == 8
    assert len(grid.cells) == 64
    
    # Check cell at (0, 0)
    cell = grid.get_cell(0, 0)
    assert cell.position == (0, 0)
    assert cell.resource.amount == 0


def test_grid_manhattan_distance():
    """Test Manhattan distance calculation."""
    grid = Grid(10)
    
    assert grid.manhattan_distance((0, 0), (0, 0)) == 0
    assert grid.manhattan_distance((0, 0), (3, 4)) == 7
    assert grid.manhattan_distance((5, 5), (2, 8)) == 6


def test_grid_cells_within_radius():
    """Test getting cells within radius."""
    grid = Grid(10)
    
    # Radius 0 should return only center cell
    cells = grid.cells_within_radius((5, 5), 0)
    assert len(cells) == 1
    
    # Radius 1 should return up to 5 cells (center + 4 neighbors)
    cells = grid.cells_within_radius((5, 5), 1)
    assert len(cells) == 5
    
    # Radius 2 should return up to 13 cells
    cells = grid.cells_within_radius((5, 5), 2)
    assert len(cells) == 13
    
    # Corner case: (0, 0) with radius 1
    cells = grid.cells_within_radius((0, 0), 1)
    assert len(cells) == 3  # (0,0), (1,0), (0,1)


def test_inventory_validation():
    """Test inventory validation."""
    # Valid inventory
    inv = Inventory(A=5, B=10)
    assert inv.A == 5
    assert inv.B == 10
    
    # Invalid inventory (negative)
    with pytest.raises(ValueError):
        Inventory(A=-1, B=5)


def test_agent_initialization():
    """Test agent initialization."""
    inv = Inventory(A=10, B=5)
    agent = Agent(id=0, pos=(5, 5), inventory=inv)
    
    assert agent.id == 0
    assert agent.pos == (5, 5)
    assert agent.inventory.A == 10
    assert agent.inventory.B == 5
    assert agent.vision_radius == 5  # Default


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

