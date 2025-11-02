"""
Protocol Base Classes and Effect Types

This module defines:
1. Effect types - declarative intents returned by protocols
2. ProtocolBase - abstract base class for all protocols
3. Protocol interfaces - SearchProtocol, MatchingProtocol, BargainingProtocol

All protocols follow the pattern:
    Protocol receives: WorldView (frozen, read-only)
    Protocol returns: list[Effect] (declarative intents)
    Core applies: validates, executes, logs effects

Version: 2025.10.26 (Phase 0 - Infrastructure)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional, Union

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
    dA: int  # Change in good A (negative for seller, positive for buyer)
    dB: int  # Change in good B
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
    amount: int


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
    - name: Unique identifier (e.g., "legacy_three_pass")
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


class SearchProtocol(ProtocolBase):
    """
    Protocol for agent search and target selection.
    
    Search protocols determine:
    - Which opportunities agents perceive
    - How agents rank potential targets
    - Which target an agent commits to
    
    Examples:
    - Distance-discounted search (legacy)
    - Random walk exploration
    - Memory-based search
    """
    
    # Class-level version to avoid instantiation during registration
    VERSION = "unknown"

    @property
    def version(self) -> str:
        return getattr(self.__class__, "VERSION", "unknown")

    @abstractmethod
    def build_preferences(
        self, world: "WorldView"
    ) -> list[tuple[Target, float, dict[str, Any]]]:
        """
        Build ranked list of targets with scores.
        
        Args:
            world: Immutable snapshot of agent's perception
        
        Returns:
            List of (target, score, metadata) tuples, sorted by descending score
        
        The metadata dict can include:
        - 'distance': Distance to target
        - 'expected_surplus': Estimated value
        - 'memory': Past experience with target
        """
        pass
    
    @abstractmethod
    def select_target(self, world: "WorldView") -> list[Effect]:
        """
        Select target and emit effects.
        
        Args:
            world: Immutable snapshot of agent's perception
        
        Returns:
            List of effects, typically:
            - [SetTarget(...)] if target selected
            - [] if no suitable target found
        """
        pass


class MatchingProtocol(ProtocolBase):
    """
    Protocol for agent pairing.
    
    Matching protocols determine:
    - Which agents form bilateral pairs
    - How conflicts are resolved (multiple agents want same partner)
    - Stability properties of resulting matches
    
    Examples:
    - Three-pass algorithm (legacy: mutual consent + greedy fallback)
    - Greedy surplus maximization
    - Stable matching (Gale-Shapley)
    """
    
    # Class-level version to avoid instantiation during registration
    VERSION = "unknown"

    @property
    def version(self) -> str:
        return getattr(self.__class__, "VERSION", "unknown")

    @abstractmethod
    def find_matches(
        self,
        preferences: dict[int, list[tuple[Target, float, dict[str, Any]]]],
        world: "WorldView",
    ) -> list[Effect]:
        """
        Establish pairings from agent preferences.
        
        Args:
            preferences: Per-agent preference rankings from SearchProtocol
            world: Global simulation state
        
        Returns:
            List of Pair effects
        
        Invariants (enforced by simulation core):
        - No agent in multiple pairs
        - Pairs are bidirectional (if A→B then B→A)
        - Deterministic with same input
        """
        pass


class BargainingProtocol(ProtocolBase):
    """
    Protocol for trade negotiation.
    
    Bargaining protocols determine:
    - How paired agents negotiate trade terms
    - Price and quantity determination
    - Single-tick vs multi-tick resolution
    
    Examples:
    - Compensating blocks (legacy: search for feasible trade)
    - Take-it-or-leave-it (monopoly offer)
    - Rubinstein alternating offers
    - Nash bargaining solution
    """
    
    # Class-level version to avoid instantiation during registration
    VERSION = "unknown"

    @property
    def version(self) -> str:
        return getattr(self.__class__, "VERSION", "unknown")

    @abstractmethod
    def negotiate(
        self, pair: tuple[int, int], world: "WorldView"
    ) -> list[Effect]:
        """
        One negotiation step (may be single-tick or multi-tick).
        
        Args:
            pair: (agent_a, agent_b) tuple
            world: Immutable snapshot including both agents' states
        
        Returns:
            List of effects:
            - [Trade(...)] if agreement reached
            - [Unpair(..., reason="trade_failed")] if negotiation fails
            - [] if multi-tick protocol still negotiating
            - [InternalStateUpdate(...)] for multi-tick state
        
        Multi-tick protocols maintain state via InternalStateUpdate effects.
        """
        pass
    
    def on_timeout(self, pair: tuple[int, int], world: "WorldView") -> list[Effect]:
        """
        Called when negotiation exceeds max ticks.
        
        Default behavior: dissolve pairing.
        Override for custom timeout handling.
        """
        return [Unpair(*pair, reason="timeout", protocol_name=self.name, tick=world.tick)]


# =============================================================================
# Type Hints for Import by Other Modules
# =============================================================================

# WorldView is defined in context.py but type-hinted here for circular import resolution
# The actual implementation is in src/vmt_engine/protocols/context.py

