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


def perceive(agent: 'Agent', grid: 'Grid', nearby_agent_ids: list[int], 
             agent_by_id: dict[int, 'Agent']) -> PerceptionView:
    """
    Compute what an agent can see within its vision_radius.
    
    Uses pre-filtered list of nearby agents from spatial index for efficiency.
    
    Args:
        agent: The perceiving agent
        grid: The simulation grid
        nearby_agent_ids: List of agent IDs within vision radius (pre-filtered by spatial index)
        agent_by_id: Dictionary mapping agent IDs to Agent objects
        
    Returns:
        PerceptionView containing visible neighbors and resources
    """
    neighbors = []
    neighbor_quotes = {}
    
    # Build neighbor list from pre-filtered IDs (already within vision radius)
    for other_id in nearby_agent_ids:
        other = agent_by_id[other_id]
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

