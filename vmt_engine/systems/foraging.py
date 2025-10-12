"""
Foraging system for resource harvesting.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core import Agent, Grid


def forage(agent: 'Agent', grid: 'Grid', forage_rate: int, current_tick: int = 0) -> bool:
    """
    Harvest resources from agent's current cell.
    
    Args:
        agent: The foraging agent
        grid: The simulation grid
        forage_rate: Maximum amount to harvest per tick
        current_tick: Current simulation tick (for depletion tracking)
        
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
    
    # Track when resource was last harvested (for regeneration cooldown)
    # ANY harvest resets the cooldown timer
    cell.resource.last_harvested_tick = current_tick
    
    # Mark that inventory changed (for quote refresh)
    agent.inventory_changed = True
    
    return True


def regenerate_resources(grid: 'Grid', growth_rate: int, max_amount: int,
                        cooldown_ticks: int, current_tick: int) -> int:
    """
    Regenerate resources on the grid at a fixed rate after cooldown period.
    
    Regeneration occurs on cells that:
    1. Have a resource type (from initial seeding)
    2. Are below their original amount
    3. Have not been harvested for at least cooldown_ticks
    
    Any harvest from a cell resets the cooldown timer. Regeneration only
    begins after cooldown_ticks have passed with no harvesting activity.
    
    Args:
        grid: The simulation grid
        growth_rate: Units to regenerate per tick (0 = no regeneration)
        max_amount: Global maximum (unused, kept for backward compatibility)
        cooldown_ticks: Ticks to wait after last harvest before regeneration starts
        current_tick: Current simulation tick
        
    Returns:
        Total units regenerated this tick
    """
    if growth_rate <= 0:
        return 0
    
    total_regenerated = 0
    
    for cell in grid.cells.values():
        # Only process cells with a resource type
        if cell.resource.type is None:
            continue
        
        # Only regenerate if below original amount
        if cell.resource.amount >= cell.resource.original_amount:
            continue
        
        # Check if cell has been harvested
        if cell.resource.last_harvested_tick is None:
            # Never harvested, don't regenerate (stays at original seed amount)
            continue
        
        # Check if cooldown period has passed since last harvest
        ticks_since_harvest = current_tick - cell.resource.last_harvested_tick
        
        if ticks_since_harvest >= cooldown_ticks:
            # Cooldown complete, regenerate
            old_amount = cell.resource.amount
            new_amount = min(old_amount + growth_rate, cell.resource.original_amount)
            regenerated = new_amount - old_amount
            
            cell.resource.amount = new_amount
            total_regenerated += regenerated
    
    return total_regenerated

