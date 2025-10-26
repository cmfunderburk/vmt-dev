"""
Protocol Context and WorldView

This module defines immutable read-only context objects provided to protocols.
Protocols cannot mutate simulation state directly - they can only return Effects.

Key Classes:
- WorldView: Frozen snapshot of an agent's perspective
- AgentView: Simplified view of another agent
- ResourceView: Simplified view of a resource cell
- ProtocolContext: Additional context for protocol execution

Version: 2025.10.26 (Phase 0 - Infrastructure)
"""

from dataclasses import dataclass
from typing import Any, Optional

from ..econ.base import Utility

# Type aliases
Position = tuple[int, int]
Inventory = dict[str, int]


# =============================================================================
# Simplified Views for Visibility
# =============================================================================


@dataclass(frozen=True)
class AgentView:
    """
    Simplified view of another agent visible to the current agent.
    
    Includes only publicly observable information:
    - Position (visible)
    - Quotes (publicly posted prices)
    - Pairing status (observable)
    
    Does NOT include:
    - Exact inventory (private information)
    - Utility function (private preferences)
    - Internal state (private)
    """
    
    agent_id: int
    pos: Position
    quotes: dict[str, float]  # Posted reservation prices
    paired_with_id: Optional[int]  # None if unpaired


@dataclass(frozen=True)
class ResourceView:
    """
    Simplified view of a resource cell visible to the current agent.
    
    Includes:
    - Position
    - Available amounts (A and B resources)
    - Claiming status
    """
    
    pos: Position
    A: int  # Available A resources
    B: int  # Available B resources
    claimed_by_id: Optional[int]  # None if unclaimed


# =============================================================================
# WorldView - Agent's Perspective
# =============================================================================


@dataclass(frozen=True)
class WorldView:
    """
    Immutable snapshot provided to protocols.
    
    Represents everything an agent can perceive at a given tick, from their
    perspective. Frozen to prevent accidental mutation by protocols.
    
    Organization:
    1. Simulation state (tick, mode, regime)
    2. Agent perspective (own state)
    3. Local environment (visible agents/resources)
    4. Global parameters (read-only config)
    5. Deterministic RNG stream
    """
    
    # -------------------------------------------------------------------------
    # Simulation State
    # -------------------------------------------------------------------------
    
    tick: int
    mode: str  # "trade" | "forage" | "both"
    exchange_regime: str  # "barter_only" | "money_only" | "mixed"
    
    # -------------------------------------------------------------------------
    # Agent Perspective (Own State)
    # -------------------------------------------------------------------------
    
    agent_id: int
    pos: Position
    inventory: Inventory  # {"A": int, "B": int, "M": int}
    utility: Utility  # Agent's utility function
    quotes: dict[str, float]  # Own reservation prices
    lambda_money: float  # Money utility parameter
    paired_with_id: Optional[int]  # None if unpaired
    trade_cooldowns: dict[int, int]  # {partner_id: ticks_remaining}
    
    # -------------------------------------------------------------------------
    # Local Environment (Within Vision Radius)
    # -------------------------------------------------------------------------
    
    visible_agents: list[AgentView]
    visible_resources: list[ResourceView]
    
    # -------------------------------------------------------------------------
    # Global Parameters (Read-Only Configuration)
    # -------------------------------------------------------------------------
    
    params: dict[str, Any]  # Scenario parameters
    # Common params include:
    # - grid_size: int
    # - vision_radius: int
    # - interaction_radius: int
    # - move_budget: int
    # - trade_cooldown_ticks: int
    
    # -------------------------------------------------------------------------
    # Deterministic RNG Stream (Per-Agent)
    # -------------------------------------------------------------------------
    
    # Note: RNG stream implementation deferred to Phase 1
    # For now, protocols should be deterministic without randomness
    # or use global RNG from simulation (for legacy compatibility)


# =============================================================================
# ProtocolContext - Global Context
# =============================================================================


@dataclass(frozen=True)
class ProtocolContext:
    """
    Additional context for protocol execution beyond agent perspective.
    
    Used by MatchingProtocol and other protocols that need global state.
    
    Includes:
    - All agent states (for matching algorithms)
    - Grid state (for resource-aware decisions)
    - Protocol history (for multi-tick protocols)
    """
    
    tick: int
    mode: str
    exchange_regime: str
    
    # Global state
    all_agent_views: dict[int, AgentView]  # All agents in simulation
    all_resource_views: list[ResourceView]  # All resources on grid
    
    # Pairing state
    current_pairings: dict[int, int]  # {agent_id: partner_id}
    
    # Protocol-specific state (from InternalStateUpdate effects)
    protocol_state: dict[str, dict[int, dict[str, Any]]]
    # Structure: {protocol_name: {agent_id: {key: value}}}
    
    # Global parameters
    params: dict[str, Any]


# =============================================================================
# Helper Functions for Context Creation
# =============================================================================


def create_world_view(
    agent_id: int,
    tick: int,
    mode: str,
    exchange_regime: str,
    pos: Position,
    inventory: Inventory,
    utility: Utility,
    quotes: dict[str, float],
    lambda_money: float,
    paired_with_id: Optional[int],
    trade_cooldowns: dict[int, int],
    visible_agents: list[AgentView],
    visible_resources: list[ResourceView],
    params: dict[str, Any],
) -> WorldView:
    """
    Factory function for creating WorldView instances.
    
    This function will be called by the simulation core during the
    perception phase to create per-agent WorldView snapshots.
    """
    return WorldView(
        tick=tick,
        mode=mode,
        exchange_regime=exchange_regime,
        agent_id=agent_id,
        pos=pos,
        inventory=inventory,
        utility=utility,
        quotes=quotes,
        lambda_money=lambda_money,
        paired_with_id=paired_with_id,
        trade_cooldowns=trade_cooldowns,
        visible_agents=visible_agents,
        visible_resources=visible_resources,
        params=params,
    )


def create_protocol_context(
    tick: int,
    mode: str,
    exchange_regime: str,
    all_agent_views: dict[int, AgentView],
    all_resource_views: list[ResourceView],
    current_pairings: dict[int, int],
    protocol_state: dict[str, dict[int, dict[str, Any]]],
    params: dict[str, Any],
) -> ProtocolContext:
    """
    Factory function for creating ProtocolContext instances.
    
    This function will be called by the simulation core during phases
    that require global state (e.g., matching phase).
    """
    return ProtocolContext(
        tick=tick,
        mode=mode,
        exchange_regime=exchange_regime,
        all_agent_views=all_agent_views,
        all_resource_views=all_resource_views,
        current_pairings=current_pairings,
        protocol_state=protocol_state,
        params=params,
    )

