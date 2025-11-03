"""
Compensating Block Bargaining Protocol

Implements the foundational VMT compensating block algorithm for bilateral
barter trade negotiation. This protocol searches for the first mutually
beneficial trade using discrete quantity steps and price candidate generation.

This is the default bargaining protocol in VMT.

Version: 2025.11.03 (Restructured)
"""

from typing import Optional, TYPE_CHECKING
from ...protocols.registry import register_protocol
from .base import BargainingProtocol
from .discovery import CompensatingBlockDiscoverer
from ...systems.trade_evaluation import TradeDiscoverer, TradeTuple
from ...protocols.base import Effect, Trade, Unpair
from ...protocols.context import WorldView

if TYPE_CHECKING:
    from ...core import Agent


@register_protocol(
    category="bargaining",
    name="compensating_block",
    description="First feasible trade using compensating block algorithm (default)",
    properties=["deterministic", "first_feasible"],
    complexity="O(K·P)",  # K = quantities tried, P = prices per quantity
    references=["VMT foundational algorithm"],
    phase="4",
)
class CompensatingBlockBargaining(BargainingProtocol):
    """
    Compensating block bargaining - the foundational VMT algorithm.
    
    Searches over discrete quantities (1, 2, 3, ...) and price candidates
    to find the first mutually beneficial barter trade. Returns Trade effect
    if successful, Unpair effect if no feasible trade exists.
    
    This is the default bargaining protocol and implements the core VMT
    trade discovery logic.
    """
    
    def __init__(self, discoverer: TradeDiscoverer | None = None):
        """
        Initialize compensating block bargaining.
        
        Args:
            discoverer: Trade discovery algorithm (default: CompensatingBlockDiscoverer)
        """
        self.discoverer = discoverer or CompensatingBlockDiscoverer()
    
    @property
    def name(self) -> str:
        return "compensating_block"
    
    @property
    def version(self) -> str:
        return "2025.11.03"
    
    VERSION = "2025.11.03"
    
    def negotiate(
        self,
        pair: tuple[int, int],
        agents: tuple["Agent", "Agent"],
        world: WorldView
    ) -> list[Effect]:
        """
        Negotiate trade between paired agents.
        
        Args:
            pair: (agent_a_id, agent_b_id) tuple
            agents: (agent_a, agent_b) - direct access to agent states
            world: Context (tick, params, rng)
        
        Returns:
            [Trade(...)] if successful
            [Unpair(...)] if no mutually beneficial trade found
        """
        agent_a, agent_b = agents
        epsilon = world.params.get("epsilon", 1e-9)
        
        # Discover trade using injected discovery algorithm
        # Note: discoverer must not mutate agents
        trade_tuple = self.discoverer.discover_trade(agent_a, agent_b, world.params, epsilon)
        
        if trade_tuple is None:
            # No mutually beneficial trade - unpair
            return [Unpair(
                protocol_name=self.name,
                tick=world.tick,
                agent_a=pair[0],
                agent_b=pair[1],
                reason="trade_failed"
            )]
        
        # Convert TradeTuple to Trade effect
        return [self._trade_tuple_to_effect(pair, trade_tuple, world)]
    
    def _trade_tuple_to_effect(
        self,
        pair: tuple[int, int],
        trade_tuple: TradeTuple,
        world: WorldView
    ) -> Trade:
        """
        Convert TradeTuple to Trade effect.
        
        Args:
            pair: (agent_a_id, agent_b_id)
            trade_tuple: Trade specification from discovery
            world: Context for tick
            
        Returns:
            Trade effect
        """
        agent_a_id, agent_b_id = pair
        
        # Determine buyer/seller from trade direction
        if trade_tuple.dA_i > 0:  # agent_a receives A (buyer)
            buyer_id, seller_id = agent_a_id, agent_b_id
            dA = trade_tuple.dA_i
            dB = -trade_tuple.dB_i
            surplus_buyer = trade_tuple.surplus_i
            surplus_seller = trade_tuple.surplus_j
        else:  # agent_b receives A (buyer)
            buyer_id, seller_id = agent_b_id, agent_a_id
            dA = -trade_tuple.dA_i
            dB = -trade_tuple.dB_i
            surplus_buyer = trade_tuple.surplus_j
            surplus_seller = trade_tuple.surplus_i
        
        return Trade(
            protocol_name=self.name,
            tick=world.tick,
            buyer_id=buyer_id,
            seller_id=seller_id,
            pair_type="A<->B",
            dA=abs(dA),
            dB=abs(dB),
            price=float(trade_tuple.price),
            metadata={
                "surplus_buyer": surplus_buyer,
                "surplus_seller": surplus_seller,
                "total_surplus": trade_tuple.surplus_i + trade_tuple.surplus_j,
            }
        )

