"""
Grid and cell management for the simulation.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal, Optional
import numpy as np
from .state import Position
from .decimal_config import decimal_from_numeric, quantize_quantity


@dataclass
class Resource:
    """Resource on a cell."""
    type: Literal["A", "B"] | None = None
    amount: Decimal = field(default_factory=lambda: Decimal('0'))
    original_amount: Decimal = field(default_factory=lambda: Decimal('0'))  # Initial seeded amount (cap for regeneration)
    last_harvested_tick: int | None = None  # Tick when resource was last harvested (for regeneration cooldown)
    
    def __post_init__(self):
        # Convert to Decimal if needed and quantize
        if isinstance(self.amount, (int, float)):
            self.amount = decimal_from_numeric(self.amount)
        else:
            self.amount = quantize_quantity(self.amount)
        
        if isinstance(self.original_amount, (int, float)):
            self.original_amount = decimal_from_numeric(self.original_amount)
        else:
            self.original_amount = quantize_quantity(self.original_amount)


@dataclass
class Cell:
    """A cell in the grid."""
    position: Position
    resource: Resource = field(default_factory=Resource)


class Grid:
    """NxN grid of cells with resources."""
    
    def __init__(self, N: int):
        """
        Initialize an NxN grid.
        
        Args:
            N: Grid dimension (creates NxN grid)
        """
        if N <= 0:
            raise ValueError(f"Grid size must be positive, got {N}")
        
        self.N = N
        self.cells: dict[Position, Cell] = {}
        
        # Track cells that have been harvested and need regeneration
        # Reduces regeneration from O(N²) to O(harvested_cells)
        self.harvested_cells: set[Position] = set()
        
        # Initialize all cells
        for x in range(N):
            for y in range(N):
                pos = (x, y)
                self.cells[pos] = Cell(position=pos)
    
    def get_cell(self, x: int, y: int) -> Cell:
        """Get cell at position (x, y)."""
        pos = (x, y)
        if pos not in self.cells:
            raise ValueError(f"Position {pos} out of grid bounds (0, 0) to ({self.N-1}, {self.N-1})")
        return self.cells[pos]
    
    def set_resource(self, x: int, y: int, good_type: Literal["A", "B"], amount: int | Decimal):
        """Set resource on cell at (x, y)."""
        from .decimal_config import decimal_from_numeric
        
        cell = self.get_cell(x, y)
        cell.resource.type = good_type
        cell.resource.amount = decimal_from_numeric(amount) if isinstance(amount, (int, float)) else amount
        cell.resource.original_amount = cell.resource.amount  # Track original for regeneration cap
    
    def manhattan_distance(self, pos1: Position, pos2: Position) -> int:
        """Calculate Manhattan distance between two positions."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def cells_within_radius(self, pos: Position, radius: int) -> list[Cell]:
        """
        Get all cells within Manhattan distance radius from pos.
        
        Args:
            pos: Center position
            radius: Maximum Manhattan distance
            
        Returns:
            List of cells within radius (including center)
        """
        result = []
        x0, y0 = pos
        
        for x in range(max(0, x0 - radius), min(self.N, x0 + radius + 1)):
            for y in range(max(0, y0 - radius), min(self.N, y0 + radius + 1)):
                if self.manhattan_distance(pos, (x, y)) <= radius:
                    result.append(self.cells[(x, y)])
        
        return result
    
    def seed_resources(self, rng: np.random.Generator, density: float, amount: int | Decimal):
        """
        Randomly seed resources on the grid.
        
        Args:
            rng: Random number generator
            density: Probability of a cell having a resource (0-1)
            amount: Amount of resource per cell
        """
        from .decimal_config import decimal_from_numeric
        
        amount_decimal = decimal_from_numeric(amount) if isinstance(amount, (int, float)) else amount
        
        for cell in self.cells.values():
            if rng.random() < density:
                # Randomly choose A or B
                resource_type = "A" if rng.random() < 0.5 else "B"
                cell.resource.type = resource_type
                cell.resource.amount = amount_decimal
                cell.resource.original_amount = amount_decimal  # Track for regeneration cap

