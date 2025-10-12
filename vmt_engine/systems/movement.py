"""
Movement and pathfinding system.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core import Agent, Position, Cell
    from .perception import PerceptionView


def next_step_toward(current: 'Position', target: 'Position', budget: int) -> 'Position':
    """
    Return next position moving toward target by up to budget steps.
    
    Uses Manhattan distance movement with tie-breaking rules:
    - Prefer reducing |dx| before |dy|
    - Prefer negative direction when dx or dy are equal in magnitude
    
    Args:
        current: Current position (x, y)
        target: Target position (x, y)
        budget: Maximum number of steps to move
        
    Returns:
        New position after moving toward target
    """
    x, y = current
    tx, ty = target
    
    dx = tx - x
    dy = ty - y
    
    # Move up to budget steps
    for _ in range(budget):
        if dx == 0 and dy == 0:
            break  # Already at target
        
        # Prefer reducing |dx| before |dy|
        # If |dx| > |dy|, move in x direction
        # If tied, prefer x direction
        # Within direction, prefer negative over positive
        if abs(dx) >= abs(dy) and dx != 0:
            # Move in x direction
            if dx < 0:
                x -= 1
                dx += 1
            else:
                x += 1
                dx -= 1
        elif dy != 0:
            # Move in y direction
            if dy < 0:
                y -= 1
                dy += 1
            else:
                y += 1
                dy -= 1
    
    return (x, y)


def choose_forage_target(agent: 'Agent', resource_cells: list['Cell'], beta: float, 
                        forage_rate: int = 1) -> 'Position' | None:
    """
    Choose best foraging target using distance-discounted utility seeking.
    
    Evaluates all resource cells including current position (if on resource).
    Current position has distance=0, so score = ΔU * β^0 = ΔU (no discount).
    Other cells are discounted by β^distance.
    
    Utility gain is calculated based on forage_rate (amount agent will harvest),
    not the full amount on the cell.
    
    Strategy: maximize ΔU_from_one_harvest * β^distance
    Fallback: nearest resource (A before B, then lowest x, y)
    
    Args:
        agent: The deciding agent
        resource_cells: List of visible resource cells
        beta: Discount factor for distance (0 < β ≤ 1)
        forage_rate: Amount agent harvests per tick (default: 1)
        
    Returns:
        Target position or None if no resources visible
    """
    if not resource_cells:
        return None
    
    if not agent.utility:
        # No utility function, use fallback: nearest resource
        return _nearest_resource_fallback(agent, resource_cells)
    
    # Calculate current utility
    current_A = agent.inventory.A
    current_B = agent.inventory.B
    current_u = agent.utility.u(current_A, current_B)
    
    best_score = float('-inf')
    best_target = None
    
    # Evaluate each resource cell (including current position if it has resources)
    for cell in resource_cells:
        # Calculate distance from agent's current position
        distance = abs(cell.position[0] - agent.pos[0]) + abs(cell.position[1] - agent.pos[1])
        
        # Amount agent will actually harvest (limited by forage_rate)
        harvest_amount = min(cell.resource.amount, forage_rate)
        
        # Calculate utility after harvesting forage_rate units (not full cell amount)
        if cell.resource.type == "A":
            new_A = current_A + harvest_amount
            new_B = current_B
        else:  # "B"
            new_A = current_A
            new_B = current_B + harvest_amount
        
        new_u = agent.utility.u(new_A, new_B)
        delta_u = new_u - current_u
        
        # Distance-discounted score
        score = delta_u * (beta ** distance)
        
        # Track best score
        # Tie-breaking: first seen (deterministic given sorted resource_cells)
        if score > best_score:
            best_score = score
            best_target = cell.position
    
    if best_target:
        return best_target
    
    # Fallback if no positive utility gain
    return _nearest_resource_fallback(agent, resource_cells)


def _nearest_resource_fallback(agent: 'Agent', resource_cells: list['Cell']) -> 'Position':
    """
    Fallback: choose nearest resource cell.
    Tie-breaking: A before B, then lowest x, then lowest y.
    """
    if not resource_cells:
        return agent.pos  # Stay in place
    
    # Sort by: distance, type (A before B), x, y
    def sort_key(cell: 'Cell'):
        distance = abs(cell.position[0] - agent.pos[0]) + abs(cell.position[1] - agent.pos[1])
        type_priority = 0 if cell.resource.type == "A" else 1
        return (distance, type_priority, cell.position[0], cell.position[1])
    
    sorted_cells = sorted(resource_cells, key=sort_key)
    return sorted_cells[0].position

