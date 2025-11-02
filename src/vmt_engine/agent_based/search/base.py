"""
Search Protocol Base Class

Search protocols determine how agents select targets for interaction in spatial environments.
Part of the Agent-Based modeling paradigm - emergent behavior from decentralized decisions.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...protocols.context import WorldView

from ...protocols.base import Effect, ProtocolBase


class SearchProtocol(ProtocolBase):
    """
    Base class for search protocols.
    
    Search protocols implement target selection strategies in spatial environments.
    They answer: "Given what I can see, who should I approach?"
    
    Theoretical Context:
    - Agent-Based Modeling paradigm
    - Bounded rationality and local information
    - Emergent patterns from decentralized search
    
    Returns:
        List of SetTarget effects
    """
    
    # Class-level version to avoid instantiation during registration
    VERSION = "unknown"

    @property
    def version(self) -> str:
        return getattr(self.__class__, "VERSION", "unknown")
    
    @abstractmethod
    def build_preferences(
        self, world: "WorldView"
    ) -> list[tuple[Any, float, dict[str, Any]]]:
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

