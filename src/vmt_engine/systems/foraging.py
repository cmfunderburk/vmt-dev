"""
Foraging system for resource harvesting.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core import Agent, Grid
    from ..simulation import Simulation


class ForageSystem:
    """Phase 5: Agents harvest resources."""

    def execute(self, sim: "Simulation") -> None:
        # Track which resources have been harvested this tick
        harvested_this_tick = set()
        
        # Process agents in ID order (deterministic)
        for agent in sorted(sim.agents, key=lambda a: a.id):
            # Skip paired agents (exclusive commitment to trading)
            if agent.paired_with_id is not None:
                continue
            
            pos = agent.pos
            
            # Skip if this resource was already harvested this tick
            if sim.params.get("enforce_single_harvester", False):
                if pos in harvested_this_tick:
                    continue  # Another agent already harvested here
            
            # Attempt to forage
            did_harvest = forage(agent, sim.grid, sim.params["forage_rate"], sim.tick)
            
            if did_harvest and sim.params.get("enforce_single_harvester", False):
                harvested_this_tick.add(pos)


class ResourceRegenerationSystem:
    """Phase 6: Resources regenerate after cooldown period."""

    def execute(self, sim: "Simulation") -> None:
        from .foraging import regenerate_resources

        regenerate_resources(
            sim.grid,
            sim.params["resource_growth_rate"],
            sim.params["resource_max_amount"],
            sim.params["resource_regen_cooldown"],
            sim.tick,
        )


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
    
    # Add to harvested cells set for efficient regeneration tracking
    grid.harvested_cells.add(agent.pos)
    
    # Mark that inventory changed (for quote refresh)
    agent.inventory_changed = True
    
    return True


def regenerate_resources(grid: 'Grid', growth_rate: int, max_amount: int,
                        cooldown_ticks: int, current_tick: int) -> int:
    """
    Regenerate resources on the grid at a fixed rate after cooldown period.
    
    Uses active set tracking to only check harvested cells, reducing complexity
    from O(N_grid²) to O(harvested_cells).
    
    Regeneration occurs on cells that:
    1. Have a resource type (from initial seeding)
    2. Are below their original amount
    3. Have not been harvested for at least cooldown_ticks
    
    Any harvest from a cell resets the cooldown timer. Regeneration only
    begins after cooldown_ticks have passed with no harvesting activity.
    
    Note: For backward compatibility with tests that manually deplete cells,
    this function will scan all cells on first call if harvested_cells is empty
    but there are depleted cells with last_harvested_tick set.
    
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
    
    # Bootstrap: If harvested_cells is empty but there are depleted cells,
    # scan once to build the active set (for backward compatibility with tests)
    if not grid.harvested_cells:
        for pos, cell in grid.cells.items():
            if (cell.resource.type is not None and 
                cell.resource.last_harvested_tick is not None and
                cell.resource.amount < cell.resource.original_amount):
                grid.harvested_cells.add(pos)
    
    total_regenerated = 0
    cells_to_remove = []
    
    # Only iterate over harvested cells (O(harvested) instead of O(N²))
    for pos in grid.harvested_cells:
        cell = grid.cells[pos]
        
        # Only process cells with a resource type
        if cell.resource.type is None:
            cells_to_remove.append(pos)
            continue
        
        # Check if fully regenerated - remove from active set
        if cell.resource.amount >= cell.resource.original_amount:
            cells_to_remove.append(pos)
            continue
        
        # Check if cell has been harvested
        if cell.resource.last_harvested_tick is None:
            # Never harvested, don't regenerate (stays at original seed amount)
            cells_to_remove.append(pos)
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
            
            # If fully regenerated, remove from active set
            if cell.resource.amount >= cell.resource.original_amount:
                cells_to_remove.append(pos)
    
    # Remove fully regenerated cells from active set
    for pos in cells_to_remove:
        grid.harvested_cells.discard(pos)
    
    return total_regenerated

