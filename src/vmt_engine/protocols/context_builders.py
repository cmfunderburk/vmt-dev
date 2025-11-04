"""
Context Builder Helpers

Factory functions for creating WorldView and ProtocolContext objects from
simulation state. These are used by the decision and trade systems to build
immutable protocol contexts.

Version: 2025.10.26 (Phase 1 - Context Builder Infrastructure)
"""

from typing import TYPE_CHECKING
from decimal import Decimal
from .context import WorldView, ProtocolContext, AgentView, ResourceView
from ..core.state import Position

if TYPE_CHECKING:
    from ..simulation import Simulation
    from ..core.agent import Agent


def build_world_view_for_agent(agent: "Agent", sim: "Simulation") -> WorldView:
    """
    Build WorldView from agent's perception cache and current simulation state.
    
    Args:
        agent: The agent whose perspective to build
        sim: Current simulation state
    
    Returns:
        Frozen WorldView for this agent
    """
    # Extract from perception cache
    view = agent.perception_cache
    
    # Build visible agents list
    visible_agents = []
    for neighbor_id, neighbor_pos in view.get("neighbors", []):
        if neighbor_id not in sim.agent_by_id:
            continue
        
        neighbor = sim.agent_by_id[neighbor_id]
        visible_agents.append(AgentView(
            agent_id=neighbor.id,
            pos=neighbor.pos,
            quotes=neighbor.quotes.copy(),
            paired_with_id=neighbor.paired_with_id
        ))
    
    # Build visible resources list
    visible_resources = []
    for cell in view.get("resource_cells", []):
        visible_resources.append(ResourceView(
            pos=cell.position,
            A=cell.resource.amount if cell.resource.type == "A" else Decimal('0'),
            B=cell.resource.amount if cell.resource.type == "B" else Decimal('0'),
            claimed_by_id=sim.resource_claims.get(cell.position)
        ))
    
    # Build params dict with essential simulation parameters
    params = {
        # Core parameters
        "grid_size": sim.grid.N,  # Grid dimension for bounds checking
        "beta": sim.params.get("beta", 0.95),
        "forage_rate": sim.params.get("forage_rate", 1),
        "vision_radius": sim.params.get("vision_radius", 5),
        "interaction_radius": sim.params.get("interaction_radius", 1),
        "move_budget_per_tick": sim.params.get("move_budget_per_tick", 1),
        "epsilon": sim.params.get("epsilon", 1e-9),
        
        # Resource claiming
        "enable_resource_claiming": sim.params.get("enable_resource_claiming", False),
        "resource_claims": sim.resource_claims.copy(),  # Pass global claims
        
        # Trade parameters
        "trade_cooldown_ticks": sim.params.get("trade_cooldown_ticks", 10),
        
        # Agent-specific
        "home_pos": agent.home_pos,
    }
    
    # Create WorldView
    return WorldView(
        tick=sim.tick,
        mode=sim.current_mode,
        agent_id=agent.id,
        pos=agent.pos,
        inventory={
            "A": agent.inventory.A,
            "B": agent.inventory.B,
        },
        utility=agent.utility,
        quotes=agent.quotes.copy(),
        paired_with_id=agent.paired_with_id,
        trade_cooldowns=agent.trade_cooldowns.copy(),
        visible_agents=visible_agents,
        visible_resources=visible_resources,
        params=params,
        rng=sim.rng,  # Pass simulation's deterministic RNG to protocols
    )


def build_protocol_context(sim: "Simulation") -> ProtocolContext:
    """
    Build ProtocolContext with global simulation state.
    
    Args:
        sim: Current simulation state
    
    Returns:
        Frozen ProtocolContext for matching protocols
    """
    # Build all agent views
    all_agent_views = {}
    for agent in sim.agents:
        all_agent_views[agent.id] = AgentView(
            agent_id=agent.id,
            pos=agent.pos,
            quotes=agent.quotes.copy(),
            paired_with_id=agent.paired_with_id
        )
    
    # Build all resource views
    all_resource_views = []
    for x in range(sim.grid.N):
        for y in range(sim.grid.N):
            cell = sim.grid.get_cell(x, y)
            if cell.resource.type is not None and cell.resource.amount > 0:
                all_resource_views.append(ResourceView(
                    pos=(x, y),
                    A=cell.resource.amount if cell.resource.type == "A" else Decimal('0'),
                    B=cell.resource.amount if cell.resource.type == "B" else Decimal('0'),
                    claimed_by_id=sim.resource_claims.get((x, y))
                ))
    
    # Build current pairings dict
    current_pairings = {}
    for agent in sim.agents:
        if agent.paired_with_id is not None:
            current_pairings[agent.id] = agent.paired_with_id
    
    # Protocol-specific state (empty for now - will be populated by InternalStateUpdate effects)
    protocol_state = {}
    
    # Build params dict (no longer includes agent state - use agents dict instead)
    params = {
        "beta": sim.params.get("beta", 0.95),
        "vision_radius": sim.params.get("vision_radius", 5),
        "interaction_radius": sim.params.get("interaction_radius", 1),
        "epsilon": sim.params.get("epsilon", 1e-9),
    }
    
    # Build agents dict for direct access (eliminates params hack)
    agents = {agent.id: agent for agent in sim.agents}
    
    return ProtocolContext(
        tick=sim.tick,
        mode=sim.current_mode,
        all_agent_views=all_agent_views,
        all_resource_views=all_resource_views,
        agents=agents,
        current_pairings=current_pairings,
        protocol_state=protocol_state,
        params=params,
        rng=sim.rng,  # Pass simulation's deterministic RNG
    )


