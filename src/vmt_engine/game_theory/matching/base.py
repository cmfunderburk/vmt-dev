"""
Matching Protocol Base Class

Matching protocols determine how agents form bilateral pairs for negotiation.
Part of the Game Theory paradigm - strategic pairing mechanisms.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...protocols.context import WorldView

from ...protocols.base import Effect, ProtocolBase


class MatchingProtocol(ProtocolBase):
    """
    Base class for matching protocols.
    
    Matching protocols implement pairing mechanisms that determine which agents
    negotiate together. They answer: "Who negotiates with whom?"
    
    Theoretical Context:
    - Game Theory paradigm (matching theory, mechanism design)
    - Two-sided matching with preferences
    - Strategic considerations in pairing
    
    Returns:
        List of Pair/Unpair effects
    """
    
    # Class-level version to avoid instantiation during registration
    VERSION = "unknown"

    @property
    def version(self) -> str:
        return getattr(self.__class__, "VERSION", "unknown")
    
    @abstractmethod
    def find_matches(
        self,
        preferences: dict[int, list[tuple[Any, float, dict[str, Any]]]],
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

