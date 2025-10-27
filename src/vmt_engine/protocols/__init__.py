"""
VMT Protocol System

This package provides the modular protocol architecture for VMT's decision-making,
trading, and movement systems. Protocols define swappable economic mechanisms that
can be configured per-scenario.

Key Concepts:
- **Protocol**: A swappable economic mechanism (e.g., bargaining, matching, search)
- **Effect**: A declarative intent returned by protocols (e.g., Pair, Trade, Move)
- **WorldView**: Immutable read-only snapshot provided to protocols
- **Registry**: Central protocol registration and lookup system

Organization:
- base.py: Effect types and ProtocolBase abstract classes
- context.py: WorldView and ProtocolContext
- registry.py: Protocol registration and lookup
- search/: Search protocols (target selection)
- matching/: Matching protocols (agent pairing)
- bargaining/: Bargaining protocols (trade negotiation)
"""

from .base import (
    # Effect base class
    Effect,
    # Target selection effects
    SetTarget,
    # Resource management effects
    ClaimResource,
    ReleaseClaim,
    # Pairing effects
    Pair,
    Unpair,
    # Movement effects
    Move,
    # Trading effects
    Trade,
    # Foraging effects
    Harvest,
    # Housekeeping effects
    RefreshQuotes,
    SetCooldown,
    # Multi-tick state effects
    InternalStateUpdate,
    # Protocol base classes
    ProtocolBase,
    SearchProtocol,
    MatchingProtocol,
    BargainingProtocol,
)

from .context import (
    AgentView,
    ResourceView,
    WorldView,
    ProtocolContext,
    create_world_view,
    create_protocol_context,
)

from .registry import ProtocolRegistry
from .context_builders import (
    build_world_view_for_agent,
    build_protocol_context,
    build_trade_world_view,
)

__all__ = [
    # Effects
    "Effect",
    "SetTarget",
    "ClaimResource",
    "ReleaseClaim",
    "Pair",
    "Unpair",
    "Move",
    "Trade",
    "Harvest",
    "RefreshQuotes",
    "SetCooldown",
    "InternalStateUpdate",
    # Protocols
    "ProtocolBase",
    "SearchProtocol",
    "MatchingProtocol",
    "BargainingProtocol",
    # Context
    "AgentView",
    "ResourceView",
    "WorldView",
    "ProtocolContext",
    "create_world_view",
    "create_protocol_context",
    # Registry
    "ProtocolRegistry",
    # Context builders
    "build_world_view_for_agent",
    "build_protocol_context",
    "build_trade_world_view",
]

