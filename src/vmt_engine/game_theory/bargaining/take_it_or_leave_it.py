"""
Take-It-Or-Leave-It Bargaining Protocol

NOT YET IMPLEMENTED - Stub for future development.

Intended Behavior:
- Select proposer based on power/randomness
- Proposer searches for optimal offer
- Subject to responder IR constraint: ΔU_responder ≥ ε
- Maximize proposer surplus
- Responder accepts (trade) or rejects (unpair)

Economic Properties:
- Asymmetric surplus distribution
- Models bargaining power
- Rubinstein bargaining limiting case
- Demonstrates hold-up problems

Parameters (Future):
- proposer_power: How much surplus proposer captures
- proposer_selection: "random" | "higher_id" | etc.

References:
- Rubinstein (1982) "Perfect Equilibrium in a Bargaining Model"
- Hold-up problem (Williamson 1985)

Version: 2025.11.04.stub
"""

from typing import TYPE_CHECKING
from ...protocols.registry import register_protocol
from .base import BargainingProtocol
from ...protocols.base import Effect, Unpair
from ...protocols.context import WorldView

if TYPE_CHECKING:
    from ...core import Agent


@register_protocol(
    category="bargaining",
    name="take_it_or_leave_it",
    description="Asymmetric power bargaining (NOT IMPLEMENTED - stub)",
    properties=["stub", "not_implemented"],
    complexity="O(K·P) proposer-optimal",
    references=["Rubinstein (1982)"],
)
class TakeItOrLeaveIt(BargainingProtocol):
    """
    Asymmetric bargaining - NOT IMPLEMENTED.
    
    This is a stub protocol. Returns Unpair(reason="not_implemented").
    
    TODO: Implement proposer-optimal search with responder IR constraint.
    """
    
    @property
    def name(self) -> str:
        return "take_it_or_leave_it"
    
    @property
    def version(self) -> str:
        return "2025.11.04.stub"
    
    VERSION = "2025.11.04.stub"
    
    def negotiate(
        self,
        pair: tuple[int, int],
        agents: tuple["Agent", "Agent"],
        world: WorldView
    ) -> list[Effect]:
        """NOT IMPLEMENTED - Returns Unpair."""
        return [Unpair(
            protocol_name=self.name,
            tick=world.tick,
            agent_a=pair[0],
            agent_b=pair[1],
            reason="not_implemented"
        )]
