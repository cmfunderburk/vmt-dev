"""
Bargaining Protocol Base Class

Bargaining protocols determine how paired agents negotiate trade terms.
Part of the Game Theory paradigm - strategic negotiation mechanisms.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...protocols.context import WorldView

from ...protocols.base import Effect, ProtocolBase


class BargainingProtocol(ProtocolBase):
    """
    Base class for bargaining protocols.
    
    Bargaining protocols implement negotiation mechanisms between paired agents.
    They answer: "What terms do we agree to?"
    
    Theoretical Context:
    - Game Theory paradigm (bargaining theory, Nash program)
    - Axiomatic bargaining solutions (Nash, Kalai-Smorodinsky, etc.)
    - Strategic bargaining (Rubinstein, ultimatum games)
    
    Returns:
        List of Trade/Unpair effects
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
        from ...protocols.base import Unpair
        return [Unpair(*pair, reason="timeout", protocol_name=self.name, tick=world.tick)]

