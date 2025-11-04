"""
Split-the-Difference Bargaining Protocol

NOT YET IMPLEMENTED - Stub for future development.

Intended Behavior:
- Search ALL possible trades exhaustively
- Rank by surplus evenness: |surplus_i - surplus_j|
- Select trade with most equal surplus split
- If tied, use deterministic tie-breaker

Economic Properties:
- Nash bargaining solution approximation
- Fairness criterion: equal gains from trade
- Pareto efficient
- Computationally expensive (exhaustive search)

References:
- Nash (1950) "The Bargaining Problem"
- Kalai-Smorodinsky (1975)

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
    name="split_difference",
    description="Equal surplus division (NOT IMPLEMENTED - stub)",
    properties=["stub", "not_implemented"],
    complexity="O(K·P) exhaustive",
    references=["Nash (1950)"],
    phase="future",
)
class SplitDifference(BargainingProtocol):
    """
    Equal surplus division bargaining - NOT IMPLEMENTED.
    
    This is a stub protocol. Returns Unpair(reason="not_implemented").
    
    TODO: Implement exhaustive search for equal split trade.
    """
    
    @property
    def name(self) -> str:
        return "split_difference"
    
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
