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
    from ...core import Agent

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
        self,
        pair: tuple[int, int],
        agents: tuple["Agent", "Agent"],
        world: "WorldView"
    ) -> list[Effect]:
        """
        One negotiation step (may be single-tick or multi-tick).
        
        Args:
            pair: (agent_a_id, agent_b_id) - agent IDs
            agents: (agent_a, agent_b) - READ-ONLY access to full agent state
                    Guaranteed: agents[0].id == pair[0], agents[1].id == pair[1]
                    WARNING: Agents are mutable but protocols MUST NOT mutate them.
                             Mutations are only allowed via Trade effects.
                             Debug assertions verify this in development.
            world: Immutable context (tick, mode, params, rng)
        
        Returns:
            List of effects:
            - [Trade(...)] if agreement reached
            - [Unpair(..., reason="trade_failed")] if negotiation fails
            - [] if multi-tick protocol still negotiating
            - [InternalStateUpdate(...)] for multi-tick state
        
        Multi-tick protocols maintain state via InternalStateUpdate effects.
        """
        pass
    
    def on_timeout(
        self,
        pair: tuple[int, int],
        agents: tuple["Agent", "Agent"],
        world: "WorldView"
    ) -> list[Effect]:
        """
        Called when negotiation exceeds max ticks.
        
        Default behavior: dissolve pairing.
        Override for custom timeout handling.
        """
        from ...protocols.base import Unpair
        return [Unpair(*pair, reason="timeout", protocol_name=self.name, tick=world.tick)]

