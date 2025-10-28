"""
Context Builder Helpers

Factory functions for creating WorldView and ProtocolContext objects from
simulation state. These are used by the decision and trade systems to build
immutable protocol contexts.

Version: 2025.10.26 (Phase 1 - Legacy Adapter)
"""

from typing import TYPE_CHECKING
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
            A=cell.resource.amount if cell.resource.type == "A" else 0,
            B=cell.resource.amount if cell.resource.type == "B" else 0,
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
        "dA_max": sim.params.get("dA_max", 50),
        "epsilon": sim.params.get("epsilon", 1e-9),
        
        # Resource claiming
        "enable_resource_claiming": sim.params.get("enable_resource_claiming", False),
        "resource_claims": sim.resource_claims.copy(),  # Pass global claims
        
        # Money parameters
        "money_scale": sim.params.get("money_scale", 1),
        "trade_cooldown_ticks": sim.params.get("trade_cooldown_ticks", 10),
        
        # Agent-specific
        "home_pos": agent.home_pos,
    }
    
    # Create WorldView
    return WorldView(
        tick=sim.tick,
        mode=sim.current_mode,
        exchange_regime=sim.params.get("exchange_regime", "barter_only"),
        agent_id=agent.id,
        pos=agent.pos,
        inventory={
            "A": agent.inventory.A,
            "B": agent.inventory.B,
            "M": agent.inventory.M,
        },
        utility=agent.utility,
        quotes=agent.quotes.copy(),
        lambda_money=agent.lambda_money,
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
                    A=cell.resource.amount if cell.resource.type == "A" else 0,
                    B=cell.resource.amount if cell.resource.type == "B" else 0,
                    claimed_by_id=sim.resource_claims.get((x, y))
                ))
    
    # Build current pairings dict
    current_pairings = {}
    for agent in sim.agents:
        if agent.paired_with_id is not None:
            current_pairings[agent.id] = agent.paired_with_id
    
    # Protocol-specific state (empty for now - will be populated by InternalStateUpdate effects)
    protocol_state = {}
    
    # Build params dict
    params = {
        "beta": sim.params.get("beta", 0.95),
        "vision_radius": sim.params.get("vision_radius", 5),
        "interaction_radius": sim.params.get("interaction_radius", 1),
        "epsilon": sim.params.get("epsilon", 1e-9),
        "exchange_regime": sim.params.get("exchange_regime", "barter_only"),
    }
    
    return ProtocolContext(
        tick=sim.tick,
        mode=sim.current_mode,
        exchange_regime=sim.params.get("exchange_regime", "barter_only"),
        all_agent_views=all_agent_views,
        all_resource_views=all_resource_views,
        current_pairings=current_pairings,
        protocol_state=protocol_state,
        params=params,
        rng=sim.rng,  # Pass simulation's deterministic RNG
    )


def build_trade_world_view(
    agent_a: "Agent",
    agent_b: "Agent", 
    sim: "Simulation"
) -> WorldView:
    """
    Build WorldView for trade negotiation between two paired agents.
    
    This is specialized for bargaining protocols - includes both agents' full states.
    
    Args:
        agent_a: First agent in pair
        agent_b: Second agent in pair
        sim: Current simulation state
    
    Returns:
        WorldView from agent_a's perspective with agent_b's info in visible_agents
    """
    # Build base WorldView for agent_a
    world = build_world_view_for_agent(agent_a, sim)
    
    # Add partner's inventory to params (needed by bargaining protocol)
    # This is a workaround until we extend AgentView or refactor matching functions
    params_with_partner = world.params.copy()
    params_with_partner[f"partner_{agent_b.id}_inv_A"] = agent_b.inventory.A
    params_with_partner[f"partner_{agent_b.id}_inv_B"] = agent_b.inventory.B
    params_with_partner[f"partner_{agent_b.id}_inv_M"] = agent_b.inventory.M
    params_with_partner[f"partner_{agent_b.id}_lambda"] = agent_b.lambda_money
    params_with_partner[f"partner_{agent_b.id}_utility"] = agent_b.utility
    params_with_partner[f"partner_{agent_b.id}_money_utility_form"] = agent_b.money_utility_form
    params_with_partner[f"partner_{agent_b.id}_M_0"] = agent_b.M_0
    
    # Rebuild WorldView with extended params
    # Using dataclasses.replace would be cleaner but WorldView is frozen
    # So we'll create a new one
    return WorldView(
        tick=world.tick,
        mode=world.mode,
        exchange_regime=world.exchange_regime,
        agent_id=world.agent_id,
        pos=world.pos,
        inventory=world.inventory,
        utility=world.utility,
        quotes=world.quotes,
        lambda_money=world.lambda_money,
        paired_with_id=world.paired_with_id,
        trade_cooldowns=world.trade_cooldowns,
        visible_agents=world.visible_agents,
        visible_resources=world.visible_resources,
        params=params_with_partner,
        rng=world.rng,  # Preserve RNG from original WorldView
    )

