"""
Perception system for agents to observe their environment.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core import Agent, Grid, Cell, Quote, Position
    from ..simulation import Simulation


@dataclass
class PerceptionView:
    """What an agent perceives in its environment."""
    neighbors: list[tuple[int, 'Position']]  # (agent_id, pos)
    neighbor_quotes: dict[int, 'Quote']      # agent_id -> quotes
    resource_cells: list['Cell']              # visible resource cells
    recent_trade_prices: dict[str, list[float]]  # commodity -> [prices from recent trades]


class PerceptionSystem:
    """Phase 1: Agents perceive their environment."""
    def execute(self, sim: "Simulation") -> None:
        for agent in sim.agents:
            # Use spatial index to find nearby agents efficiently (O(N) instead of O(N²))
            nearby_agent_ids = sim.spatial_index.query_radius(
                agent.pos,
                agent.vision_radius,
                exclude_id=agent.id,
            )

            perception = perceive(agent, sim.grid, nearby_agent_ids, sim.agent_by_id, sim)
            agent.perception_cache = {
                "neighbors": perception.neighbors,
                "neighbor_quotes": perception.neighbor_quotes,
                "resource_cells": perception.resource_cells,
                "recent_trade_prices": perception.recent_trade_prices,
            }


def perceive(agent: 'Agent', grid: 'Grid', nearby_agent_ids: list[int], 
             agent_by_id: dict[int, 'Agent'], sim: 'Simulation') -> PerceptionView:
    """
    Compute what an agent can see within its vision_radius.
    
    Uses pre-filtered list of nearby agents from spatial index for efficiency.
    
    Args:
        agent: The perceiving agent
        grid: The simulation grid
        nearby_agent_ids: List of agent IDs within vision radius (pre-filtered by spatial index)
        agent_by_id: Dictionary mapping agent IDs to Agent objects
        sim: Simulation object for accessing trade history
        
    Returns:
        PerceptionView containing visible neighbors, resources, and recent trade prices
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
    
    # Extract recent trade prices from telemetry
    recent_trade_prices = _extract_recent_trade_prices(agent, sim)
    
    return PerceptionView(
        neighbors=neighbors,
        neighbor_quotes=neighbor_quotes,
        resource_cells=resource_cells,
        recent_trade_prices=recent_trade_prices
    )


def _extract_recent_trade_prices(agent: 'Agent', sim: 'Simulation') -> dict[str, list[float]]:
    """
    Extract recent trade prices from telemetry for price signal learning.
    
    Args:
        agent: The agent observing prices
        sim: Simulation object with access to telemetry
        
    Returns:
        Dictionary mapping commodity names to lists of recent prices
    """
    recent_prices = {'A': [], 'B': []}
    
    # Get recent trades from telemetry (last 5 ticks)
    recent_ticks = range(max(0, sim.tick - 5), sim.tick)
    
    for tick in recent_ticks:
        # Query telemetry for trades in this tick
        # This is a simplified implementation - in practice, you'd query the database
        # For now, we'll extract from the trade system's recent trades if available
        if hasattr(sim, 'trade_system') and hasattr(sim.trade_system, 'recent_trades'):
            for trade in sim.trade_system.recent_trades.get(tick, []):
                if hasattr(trade, 'price') and hasattr(trade, 'pair_type'):
                    # Extract commodity and price based on trade type
                    if trade.pair_type == "A<->B":
                        # For A<->B trades, record price of A in terms of B
                        if trade.dA > 0:  # Someone bought A
                            recent_prices['A'].append(trade.price)
                    elif trade.pair_type == "A<->M":
                        # For A<->M trades, record price of A in terms of money
                        if trade.dA > 0:  # Someone bought A
                            recent_prices['A'].append(trade.price)
                    elif trade.pair_type == "B<->M":
                        # For B<->M trades, record price of B in terms of money
                        if trade.dB > 0:  # Someone bought B
                            recent_prices['B'].append(trade.price)
    
    return recent_prices

