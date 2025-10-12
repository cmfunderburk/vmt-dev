"""
Foraging system for resource harvesting.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core import Agent, Grid


def forage(agent: 'Agent', grid: 'Grid', forage_rate: int) -> bool:
    """
    Harvest resources from agent's current cell.
    
    Args:
        agent: The foraging agent
        grid: The simulation grid
        forage_rate: Maximum amount to harvest per tick
        
    Returns:
        True if any resources were harvested, False otherwise
    """
    cell = grid.get_cell(agent.pos[0], agent.pos[1])
    
    if cell.resource.amount == 0 or cell.resource.type is None:
        return False
    
    # Determine harvest amount
    harvest = min(cell.resource.amount, forage_rate)
    good_type = cell.resource.type
    
    # Update agent inventory
    if good_type == "A":
        agent.inventory.A += harvest
    else:  # "B"
        agent.inventory.B += harvest
    
    # Update cell resource
    cell.resource.amount -= harvest
    
    # Mark that inventory changed (for quote refresh)
    agent.inventory_changed = True
    
    return True

