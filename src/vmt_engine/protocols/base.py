"""
Protocol Base Classes and Effect Types

This module defines:
1. Effect types - declarative intents returned by protocols
2. ProtocolBase - abstract base class for all protocols

All protocols follow the pattern:
    Protocol receives: WorldView (frozen, read-only)
    Protocol returns: list[Effect] (declarative intents)
    Core applies: validates, executes, logs effects

Protocol ABCs (SearchProtocol, MatchingProtocol, BargainingProtocol) are now
defined in their respective domain modules:
- SearchProtocol: agent_based/search/base.py
- MatchingProtocol: game_theory/matching/base.py
- BargainingProtocol: game_theory/bargaining/base.py

Version: 2025.10.26 (Phase 0 - Infrastructure)
Post-restructure: 2025.11.02
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional, Union
from decimal import Decimal

# Type aliases for clarity
Position = tuple[int, int]
Target = Union[Position, int, str]  # Position, agent_id, or ResourceID


# =============================================================================
# Effect Types - Declarative Intents
# =============================================================================


@dataclass
class Effect:
    """
    Base class for all protocol effects.
    
    Effects are declarative intents returned by protocols. The simulation core
    validates and applies effects in deterministic order.
    
    All effects include:
    - protocol_name: Which protocol generated this effect
    - tick: When the effect was generated
    """
    
    protocol_name: str
    tick: int


# -----------------------------------------------------------------------------
# Target Selection Effects
# -----------------------------------------------------------------------------


@dataclass
class SetTarget(Effect):
    """
    Set an agent's target for movement.
    
    Target can be:
    - Position (x, y): Move toward specific location
    - int (agent_id): Move toward another agent
    - str (resource_id): Move toward resource type
    """
    
    agent_id: int
    target: Target


# -----------------------------------------------------------------------------
# Resource Management Effects
# -----------------------------------------------------------------------------


@dataclass
class ClaimResource(Effect):
    """
    Claim a resource cell for exclusive harvesting.
    
    Once claimed, other agents cannot harvest from this cell until released.
    """
    
    agent_id: int
    pos: Position


@dataclass
class ReleaseClaim(Effect):
    """
    Release a resource claim, making it available to other agents.
    """
    
    pos: Position


# -----------------------------------------------------------------------------
# Pairing Effects
# -----------------------------------------------------------------------------


@dataclass
class Pair(Effect):
    """
    Establish a bilateral pairing between two agents.
    
    Reasons:
    - "mutual_consent": Both agents ranked each other highly
    - "greedy_fallback": Best available match (three-pass algorithm)
    """
    
    agent_a: int
    agent_b: int
    reason: str  # "mutual_consent" | "greedy_fallback"


@dataclass
class Unpair(Effect):
    """
    Dissolve an existing pairing.
    
    Reasons:
    - "trade_failed": Negotiation did not reach agreement
    - "timeout": Negotiation exceeded max ticks
    - "mode_change": Simulation mode changed (trade/forage)
    """
    
    agent_a: int
    agent_b: int
    reason: str  # "trade_failed" | "timeout" | "mode_change"


# -----------------------------------------------------------------------------
# Movement Effects
# -----------------------------------------------------------------------------


@dataclass
class Move(Effect):
    """
    Move an agent by a displacement vector.
    
    The simulation core handles:
    - Grid boundary clamping
    - Move budget enforcement
    - Position updates
    """
    
    agent_id: int
    dx: int
    dy: int


# -----------------------------------------------------------------------------
# Trading Effects
# -----------------------------------------------------------------------------


@dataclass
class Trade(Effect):
    """
    Execute a bilateral barter trade between two agents.
    
    Trade type: A<->B barter only
    
    The simulation core validates:
    - Inventory feasibility (non-negative inventories)
    - Surplus positivity (both agents benefit)
    - Conservation laws (goods conserved)
    """
    
    buyer_id: int
    seller_id: int
    pair_type: str  # Always "A<->B" for barter-only economy
    dA: Decimal  # Change in good A (negative for seller, positive for buyer)
    dB: Decimal  # Change in good B
    price: float  # Price of the transaction
    metadata: dict[str, Any]  # Additional info (e.g., surplus, rounds)


# -----------------------------------------------------------------------------
# Foraging Effects
# -----------------------------------------------------------------------------


@dataclass
class Harvest(Effect):
    """
    Harvest resources from a cell.
    
    The simulation core validates:
    - Cell is claimed by this agent
    - Sufficient resources available
    - Agent is within interaction_radius
    """
    
    agent_id: int
    pos: Position
    amount: Decimal


# -----------------------------------------------------------------------------
# Housekeeping Effects
# -----------------------------------------------------------------------------


@dataclass
class RefreshQuotes(Effect):
    """
    Recompute an agent's reservation prices (quotes).
    
    Triggered when:
    - Inventory changes (after trade/forage)
    """
    
    agent_id: int


@dataclass
class SetCooldown(Effect):
    """
    Set a trade cooldown between two agents.
    
    Prevents repeated trading between the same pair for a specified
    number of ticks (prevents infinite trading loops).
    """
    
    agent_a: int
    agent_b: int
    ticks: int


# -----------------------------------------------------------------------------
# Multi-tick State Effects
# -----------------------------------------------------------------------------


@dataclass
class InternalStateUpdate(Effect):
    """
    Store protocol-specific state across multiple ticks.
    
    Used by multi-tick protocols (e.g., Rubinstein bargaining) to maintain:
    - Round numbers
    - Offer history
    - Learning/memory state
    
    Stored in telemetry for full audit trail and reproducibility.
    """
    
    agent_id: int
    key: str
    value: Any


# =============================================================================
# Protocol Base Classes
# =============================================================================


class ProtocolBase(ABC):
    """
    Abstract base class for all protocols.
    
    All protocols must provide:
    - name: Unique identifier (e.g., "three_pass_matching")
    - version: Date-based version (YYYY.MM.DD format)
    
    Protocols are pure functions: same WorldView → same Effects.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Protocol identifier for telemetry and configuration."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """
        Protocol version in YYYY.MM.DD format.
        
        Used for:
        - Telemetry tracking
        - Reproducibility
        - Research documentation
        """
        pass




# =============================================================================
# Type Hints for Import by Other Modules
# =============================================================================

# WorldView is defined in context.py but type-hinted here for circular import resolution
# The actual implementation is in src/vmt_engine/protocols/context.py

