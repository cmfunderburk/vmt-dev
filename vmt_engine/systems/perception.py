"""
Perception system for agents to observe their environment.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core import Agent, Grid, Cell, Quote, Position


@dataclass
class PerceptionView:
    """What an agent perceives in its environment."""
    neighbors: list[tuple[int, 'Position']]  # (agent_id, pos)
    neighbor_quotes: dict[int, 'Quote']      # agent_id -> quotes
    resource_cells: list['Cell']              # visible resource cells


def perceive(agent: 'Agent', grid: 'Grid', all_agents: list['Agent']) -> PerceptionView:
    """
    Compute what an agent can see within its vision_radius.
    
    Args:
        agent: The perceiving agent
        grid: The simulation grid
        all_agents: List of all agents in simulation
        
    Returns:
        PerceptionView containing visible neighbors and resources
    """
    neighbors = []
    neighbor_quotes = {}
    
    # Find agents within vision radius
    for other in all_agents:
        if other.id == agent.id:
            continue  # Don't perceive self
        
        distance = grid.manhattan_distance(agent.pos, other.pos)
        if distance <= agent.vision_radius:
            neighbors.append((other.id, other.pos))
            # Snapshot quotes (read-only copy)
            neighbor_quotes[other.id] = other.quotes
    
    # Get resource cells within vision radius
    resource_cells = []
    visible_cells = grid.cells_within_radius(agent.pos, agent.vision_radius)
    
    for cell in visible_cells:
        if cell.resource.amount > 0 and cell.resource.type:
            resource_cells.append(cell)
    
    return PerceptionView(
        neighbors=neighbors,
        neighbor_quotes=neighbor_quotes,
        resource_cells=resource_cells
    )

